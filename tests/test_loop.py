import pytest

from osmbot.game import loop
from osmbot.game.loop import MAX_WAIT, MIN_WAIT, next_wait, run_active


@pytest.fixture(autouse=True)
def _no_log_file(monkeypatch, tmp_path):
    monkeypatch.setattr(loop, "LOG_FILE", tmp_path / "bot.log")
    monkeypatch.setattr(loop, "read_slots", lambda client: [])
    monkeypatch.setattr(loop, "_shop_ads", lambda dry_run: 0)


class FixedRng:
    def uniform(self, a, b):
        return a


def test_next_wait_is_until_earliest_finish_plus_jitter():
    assert next_wait([1000 + 600, 1000 + 7200], now=1000, jitter=10) == 610


def test_short_trainings_wake_sooner_than_long_ones():
    assert next_wait([1000 + 2 * 3600], now=1000) == MAX_WAIT  # capped, re-check in between
    assert next_wait([1000 + 300], now=1000) == 300


def test_wait_has_a_floor_and_a_ceiling():
    assert next_wait([500], now=1000) == MIN_WAIT  # already ready
    assert next_wait([], now=1000) == MAX_WAIT


def test_a_failed_training_write_is_looked_at_again_and_stops_only_after_three_passes_in_a_row():
    sleeps = []
    with pytest.raises(SystemExit) as stop:
        run_active(claim=lambda c: 0, train=lambda c: 1, finish_times=lambda: [], sleep=sleeps.append, rng=FixedRng())
    assert stop.value.code == 1 and sleeps == [loop.WRITE_RETRY] * (loop.MAX_WRITE_FAILURES - 1)


def test_a_pass_without_failures_resets_the_count_of_failed_writes():
    results = iter([1, 1, 0, 1, 1, 1])
    calls = []

    def train(confirm):
        calls.append(1)
        return next(results)

    with pytest.raises(SystemExit):
        run_active(claim=lambda c: 0, train=train, finish_times=lambda: [], sleep=lambda s: None, rng=FixedRng())
    assert len(calls) == 6


def test_network_pauses_grow_and_the_loop_only_gives_up_after_hours():
    assert [loop.network_pause(n) for n in (1, 2, 3, 4, 5, 9)] == [60, 120, 300, 600, 900, 900]
    now = {"t": 0.0}
    sleeps = []

    def claim(confirm):
        raise OSError("sem rede")

    def sleep(seconds):
        sleeps.append(seconds)
        now["t"] += seconds

    with pytest.raises(SystemExit):
        run_active(claim=claim, train=lambda c: 0, finish_times=lambda: [], sleep=sleep, clock=lambda: now["t"],
                   rng=FixedRng())
    assert sleeps[:5] == [60, 120, 300, 600, 900] and sum(sleeps) >= loop.MAX_NETWORK_DOWN


def test_a_kind_of_video_that_keeps_failing_waits_longer_each_time(monkeypatch):
    now = {"t": 0.0}
    tries = []

    def broken(dry_run):
        tries.append(now["t"])
        raise RuntimeError("botão não encontrado")

    monkeypatch.setattr(loop, "_training_ads", broken)
    monkeypatch.setattr(loop, "_money_ads", lambda dry_run: 0)
    loop._ads_backoff.clear()
    for t in range(0, 4 * 3600, 60):  # a pass every minute for 4 hours
        now["t"] = float(t)
        try:
            loop._all_ads(False, clock=lambda: now["t"])
        except Exception:
            pass
    assert [loop.ads_retry(n) for n in (1, 2, 3, 4, 5)] == [600, 1200, 2400, 3600, 3600]
    assert tries[:4] == [0, 600, 1800, 4200] and len(tries) < 10


def test_loop_sleeps_then_repeats_and_stops_on_error():
    calls = []
    sleeps = []

    def train(confirm):
        calls.append(confirm)
        return 0 if len(calls) < 3 else 1

    with pytest.raises(SystemExit):
        run_active(claim=lambda c: 0, train=train, finish_times=lambda: [1000 + 600], sleep=sleeps.append,
                   clock=lambda: 1000, rng=FixedRng())
    assert calls == [True] * 5 and sleeps[:2] == [605, 605] and sleeps[2:] == [loop.WRITE_RETRY] * 2


def test_dry_run_does_one_pass_and_never_writes():
    seen = []
    run_active(True, claim=lambda c: seen.append(c) or 0, train=lambda c: seen.append(c) or 0,
               finish_times=lambda: [], sleep=lambda s: seen.append("slept"))
    assert seen == [False, False]


def test_session_loss_stops_with_message():
    def claim(confirm):
        raise SystemExit("Sessao expirada: faz osmbot login")

    with pytest.raises(SystemExit) as stop:
        run_active(claim=claim, train=lambda c: 0, finish_times=lambda: [])
    assert "Sessao expirada" in str(stop.value.code)


def test_slot_warning_only_when_free_slots_increase(capsys):
    from osmbot.game.slots import SlotStatus

    previous = {}
    full, one_free = SlotStatus("Clube A", 4, 4), SlotStatus("Clube A", 3, 4)
    loop._check_slots(lambda: [full], previous)
    loop._check_slots(lambda: [one_free], previous)
    loop._check_slots(lambda: [one_free], previous)  # still 1 free: no repeat
    loop._check_slots(lambda: [full], previous)
    loop._check_slots(lambda: [one_free], previous)  # went full and free again: warn again
    assert capsys.readouterr().out.count("slot(s) de venda livre") == 2


def test_slot_check_failure_does_not_stop_the_loop(capsys):
    def broken():
        raise RuntimeError("boom")

    loop._check_slots(broken, {})
    assert "Slots: erro ao ler" in capsys.readouterr().out


def test_board_mode_shows_data_at_once_and_keeps_redrawing(capsys):
    clock_state = {"t": 1_000_000.0}
    passes = []

    def train(confirm):
        passes.append(1)
        return 0 if len(passes) < 2 else 1  # second pass fails: the loop ends

    snap = {"coins": 2452, "clubs": [{"name": "Clube A", "ranking": 1, "league": "Liga A", "match": None, "slots": (4, 4),
                                        "trainings": [{"name": "Jogador 1", "pos": "ATA", "finish": 1_000_000.0 + 3600, "claimed": False}]}],
            "ads": {"shop": {"open": False, "reopen": 1_000_000.0 + 1800}, "training": {"open": False, "reopen": None}}}

    def sleep(seconds):
        clock_state["t"] += seconds

    with pytest.raises(SystemExit):
        loop.run_active(claim=lambda c: 0, train=train, finish_times=lambda: [], ads=None, snapshot=lambda: snap,
                        use_screen=True, sleep=sleep, clock=lambda: clock_state["t"], rng=FixedRng())
    out = capsys.readouterr().out
    assert "CLUBE A" in out and "A seguir" not in out and "ATIVO" in out
    assert out.count("Jogador 1") > 5  # redrawn many times while waiting
    assert "Resumo" in out


def test_videos_are_counted_when_watched_even_if_the_burst_is_interrupted():
    loop._stats.clear()
    calls = []

    def watch(*args):
        calls.append(args)
        if len(calls) == 3:
            raise KeyboardInterrupt  # owner stops in the middle of the burst

    counted = loop._counted("shop", watch)
    counted()
    counted()
    with pytest.raises(KeyboardInterrupt):
        counted()
    assert loop._stats["shop"] == 2


def test_board_keeps_drawing_while_the_bot_works_and_the_log_stays_clean(capsys):
    state = {"t": 1_000_000.0, "passes": 0}

    def working_ads(dry_run):
        loop._log("Anuncios: video 1 visto.")
        loop._log("Anuncios: video 2 visto.")

    def train(confirm):
        state["passes"] += 1
        if state["passes"] >= 2:
            raise SystemExit(1)
        return 0

    snap = {"coins": 2452, "clubs": [], "ads": {"shop": {"open": True, "reopen": None}, "training": {"open": True, "reopen": None}}}
    with pytest.raises(SystemExit):
        loop.run_active(claim=lambda c: 0, train=train, finish_times=lambda: [], ads=working_ads, snapshot=lambda: snap,
                        use_screen=True, sleep=lambda s: state.__setitem__("t", state["t"] + s),
                        clock=lambda: state["t"], rng=FixedRng())
    out = capsys.readouterr().out
    assert "Anuncios: video 2 visto." in out  # appeared on the real screen while the ads were running
    assert "\x1b" not in loop.LOG_FILE.read_text(encoding="utf-8")  # drawing never leaked into the log file


def test_board_is_refreshed_as_soon_as_trainings_start_not_only_at_the_end_of_the_pass(capsys):
    state = {"t": 1_000_000.0, "passes": 0, "snapshots": 0, "at_ads": None}

    def train(confirm):
        state["passes"] += 1
        if state["passes"] == 1:
            loop.COUNTS["started"] += 1  # a training was started
            return 0
        raise SystemExit(1)  # second pass: stop the loop

    def ads(dry_run):
        state["at_ads"] = state["snapshots"]

    def snap():
        state["snapshots"] += 1
        return {"coins": 1, "clubs": [], "ads": {"shop": {"open": False, "reopen": None}, "training": {"open": False, "reopen": None}}}

    with pytest.raises(SystemExit):
        loop.run_active(claim=lambda c: 0, train=train, finish_times=lambda: [], ads=ads, snapshot=snap, stadium=None, sponsors=None,
                        use_screen=True, sleep=lambda s: state.__setitem__("t", state["t"] + s), clock=lambda: state["t"], rng=FixedRng())
    assert state["at_ads"] == 2  # the first look plus the refresh after the training, both before the videos


def test_a_training_video_shortens_the_shown_finish_time_at_once():
    loop._live.clear()
    loop._stats.clear()
    snapshot = {"coins": 5, "ads": {}, "clubs": [{"trainings": [{"id": 7, "finish": 50_000.0}, {"id": 8, "finish": 60_000.0}]}]}
    loop._note_shortened(7)
    shown = loop._shown(snapshot)
    assert [t["finish"] for t in shown["clubs"][0]["trainings"]] == [50_000.0 - 7200, 60_000.0]
    assert snapshot["clubs"][0]["trainings"][0]["finish"] == 50_000.0  # the snapshot itself is untouched
    assert loop._stats["shortened"] == {7: 7200}
    loop._live.clear()


def test_only_problems_are_kept_for_the_board():
    loop._errors.clear()
    for message in ("Loja: vídeo 1", "Treino: sem sessões com 2h ou mais", "Real Betis: 4 treino(s) a iniciar",
                    "Vídeos: erro (training_ads: x); volto a tentar", "Estádio: 2 falha(s); volto a tentar", "Parou: sem rede"):
        loop._log(message)
    kept = [line for _, line in loop._errors]
    assert len(kept) == 3 and "Vídeos: erro" in kept[0] and "falha" in kept[1] and "Parou" in kept[2]
    loop._errors.clear()


def _quick_loop(**kwargs):
    state = {"t": 1_000_000.0, "passes": 0}

    def train(confirm):
        state["passes"] += 1
        if state["passes"] >= 3:
            raise SystemExit(1)  # third pass: stop the loop
        return 0

    with pytest.raises(SystemExit):
        loop.run_active(claim=lambda c: 0, train=train, finish_times=lambda: [], ads=None, stadium=None, sponsors=None,
                        sleep=lambda s: state.__setitem__("t", state["t"] + s), clock=lambda: state["t"], rng=FixedRng(), **kwargs)


def test_the_daily_rewards_run_on_every_pass_and_their_failures_never_stop_the_trainings():
    seen = []

    def rewards(confirm):
        seen.append(confirm)
        return 2, []

    _quick_loop(rewards=rewards, snapshot=lambda: {"coins": 1, "clubs": [], "ads": {}}, use_screen=False)
    assert seen == [True, True]
    assert "Recompensas: 2 falha(s)" in loop.LOG_FILE.read_text(encoding="utf-8")


def test_a_crash_in_the_daily_rewards_is_logged_and_the_loop_goes_on():
    def rewards(confirm):
        raise ValueError("boom")

    _quick_loop(rewards=rewards, snapshot=lambda: {"coins": 1, "clubs": [], "ads": {}}, use_screen=False)
    assert "Recompensas: erro (boom)" in loop.LOG_FILE.read_text(encoding="utf-8")


def test_the_board_is_refreshed_right_after_a_reward_is_claimed():
    state = {"snapshots": 0, "at_ads": None}

    def rewards(confirm):
        loop.rewards_module.COUNTS["login"] += 1
        return 0, []

    def ads(dry_run):
        state["at_ads"] = state["snapshots"]

    def snap():
        state["snapshots"] += 1
        return {"coins": 1, "clubs": [], "ads": {}}

    clock = {"t": 1_000_000.0, "passes": 0}

    def train(confirm):
        clock["passes"] += 1
        if clock["passes"] >= 2:
            raise SystemExit(1)
        return 0

    with pytest.raises(SystemExit):
        loop.run_active(claim=lambda c: 0, train=train, finish_times=lambda: [], ads=ads, snapshot=snap, stadium=None, sponsors=None,
                        rewards=rewards, use_screen=True, sleep=lambda s: clock.__setitem__("t", clock["t"] + s),
                        clock=lambda: clock["t"], rng=FixedRng())
    assert state["at_ads"] == 2  # the first look plus the refresh after the claim, both before the videos


def test_the_window_gets_the_board_and_its_stop_button_ends_the_loop_like_ctrl_c():
    clock_state = {"t": 1_000_000.0}
    shown = []
    snap = {"coins": 2452, "clubs": [], "ads": {"shop": {"open": False, "reopen": None}, "training": {"open": False, "reopen": None}}}

    def sleep(seconds):
        clock_state["t"] += seconds
        if clock_state["t"] > 1_000_000.0 + 120:
            loop.request_stop()  # the owner presses "Parar" while the bot waits

    def board(payload):
        shown.append(payload)

    loop.run_active(claim=lambda c: 0, train=lambda c: 0, finish_times=lambda: [], ads=None, stadium=None, sponsors=None,
                    rewards=None, snapshot=lambda: snap, board=board, sleep=sleep, clock=lambda: clock_state["t"], rng=FixedRng())
    with_data = [p for p in shown if p["snapshot"]]
    assert with_data and with_data[0]["snapshot"] == snap and with_data[0]["stats"]["start"] == 1_000_000.0
    assert len(with_data) > 5  # redrawn while waiting, so the countdowns move
    assert shown[-1]["status"] == "PARADO"
    assert "Parado" in loop.LOG_FILE.read_text(encoding="utf-8")


def test_errors_and_warnings_are_kept_for_the_window():
    loop._notices.clear()
    loop._log("Vídeos: erro (shop_ads: os boss coins não subiram); volto a tentar")
    loop._log("! Clube A: Jogador 5 (DEF) com 68% de condição; convém descansar 1 jogo")
    loop._log("Loja: vídeo 1")
    kinds = [(kind, text[:9]) for _, kind, text in loop._notices]
    assert kinds == [("Erro", "Vídeos: e"), ("Aviso", "Clube A: ")]
