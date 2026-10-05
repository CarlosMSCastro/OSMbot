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


def test_loop_stops_on_failed_action():
    sleeps = []
    with pytest.raises(SystemExit) as stop:
        run_active(claim=lambda c: 0, train=lambda c: 1, finish_times=lambda: [], sleep=sleeps.append, rng=FixedRng())
    assert stop.value.code == 1 and sleeps == []


def test_loop_sleeps_then_repeats_and_stops_on_error():
    calls = []
    sleeps = []

    def train(confirm):
        calls.append(confirm)
        return 0 if len(calls) < 3 else 1

    with pytest.raises(SystemExit):
        run_active(claim=lambda c: 0, train=train, finish_times=lambda: [1000 + 600], sleep=sleeps.append,
                   clock=lambda: 1000, rng=FixedRng())
    assert calls == [True, True, True] and sleeps == [605, 605]


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
    assert capsys.readouterr().out.count("AVISO") == 2


def test_slot_check_failure_does_not_stop_the_loop(capsys):
    def broken():
        raise RuntimeError("boom")

    loop._check_slots(broken, {})
    assert "Nao consegui verificar" in capsys.readouterr().out


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
    assert "CLUBE A" in out and "À espera" in out and "ATIVO" in out
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
        return 0 if state["passes"] < 2 else 1

    snap = {"coins": 2452, "clubs": [], "ads": {"shop": {"open": True, "reopen": None}, "training": {"open": True, "reopen": None}}}
    with pytest.raises(SystemExit):
        loop.run_active(claim=lambda c: 0, train=train, finish_times=lambda: [], ads=working_ads, snapshot=lambda: snap,
                        use_screen=True, sleep=lambda s: state.__setitem__("t", state["t"] + s),
                        clock=lambda: state["t"], rng=FixedRng())
    out = capsys.readouterr().out
    assert "Anuncios: video 2 visto." in out  # appeared on the real screen while the ads were running
    assert "\x1b" not in loop.LOG_FILE.read_text(encoding="utf-8")  # drawing never leaked into the log file
