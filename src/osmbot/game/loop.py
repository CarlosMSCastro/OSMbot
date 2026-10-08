"""Active mode: keep claiming finished trainings and starting new ones, on its own (D-014), and
warn when a club has a free transfer-list slot, and watch the shop videos when the game allows.

Instead of a fixed interval, the bot wakes up when the next training finishes (plus a random
few seconds), so short-training periods (2h events) are handled as fast as the normal 8h ones.
A failure never makes it hammer the game: a failed training write is looked at again 10 min later (re-reading
the game) and stops the loop after 3 passes in a row; the network is retried with longer and longer pauses;
extras (stadium, sponsors, rewards, videos) just try again later. A lost session stops it, saying why.
"""
from __future__ import annotations

import contextlib
import shutil
import io
import random
import sys
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path

from osmbot import logs as repo_log
from osmbot.game.ads import (SHOP_ACTION, TRAINING_ACTION, VIDEO_SAVES, AdsError, is_claimable, money_state, pick_money_club, run_money_ads,
                             run_shop_ads, run_training_ads, watch_money_video, watch_shop_video, watch_training_video)
from osmbot.game.dashboard import Screen, collect, machine_name, render, span, summary_text, wake_events
from osmbot.game.slots import describe, newly_free, read_slots
from osmbot.game import medical as medical_module
from osmbot.game import prematch as prematch_module
from osmbot.game import sponsors as sponsors_module
from osmbot.game import rewards as rewards_module
from osmbot.game import stadium as stadium_module
from osmbot.game.medical import run_medical
from osmbot.game.prematch import run_prematch
from osmbot.game.rewards import run_rewards
from osmbot.game.sponsors import run_sponsors
from osmbot.game.stadium import run_stadium
from osmbot.game.trainings import COUNTS, pending_finish_times, run_claim, run_train

LOG_FILE = Path.home() / ".osmbot" / "bot.log"
JITTER = (5.0, 60.0)  # seconds added after a training finishes, so timing is never exact
MIN_WAIT = 30.0
MAX_WAIT = 30 * 60.0  # also re-check now and then, in case timers changed (e.g. a skip with boss coins)
MAX_WRITE_FAILURES = 3  # passes in a row with a failed training write before stopping (D-019)
WRITE_RETRY = 10 * 60.0  # after a failed training write, look again (re-reading the game) this far ahead
NETWORK_PAUSES = (60.0, 120.0, 300.0, 600.0, 900.0)  # waits between attempts while the network is down
MAX_NETWORK_DOWN = 6 * 3600.0  # stop only after this long without network (office Wi-Fi, PC asleep...)


def network_pause(attempt: int) -> float:
    """Seconds to wait before network attempt ``attempt`` (1, 2...): longer and longer, up to 15 min."""
    return NETWORK_PAUSES[min(attempt, len(NETWORK_PAUSES)) - 1]


def next_wait(finish_times: list[float], now: float, jitter: float = 0.0) -> float:
    """Seconds to sleep until the earliest unclaimed training finishes (plus ``jitter``), within the limits."""
    if not finish_times:
        return MAX_WAIT
    wait = min(finish_times) - now + jitter
    return max(MIN_WAIT, min(MAX_WAIT, wait))


_recent: deque[str] = deque(maxlen=8)  # last log lines (printed when the board closes)
_errors: deque[tuple[float, str]] = deque(maxlen=5)  # (when, line) of the last problems: the only log lines the board shows
ERRORS_SHOWN_FOR = 30 * 60.0  # a problem stays on the board this long
ERROR_WORDS = ("erro", "falha", "parou")
_stats: dict = {}  # this run: start time, first coin balance, videos watched
_live: dict = {}  # values fresher than the last snapshot (boss coins after a video)
_screen_on = False  # while the board is drawn, nothing else may print to the terminal
_redraw = None  # set by run_active while the board is on: redraws it after each new log line
_refresh = None  # set by run_active while the board is on: re-reads the game and redraws (after a change)
_notices: deque[tuple[str, str, str]] = deque(maxlen=200)  # (hh:mm:ss, "Erro"/"Aviso", text) of this run, for the window (D-024)
_stop = threading.Event()  # set by the window's "Parar": the loop stops at its next pause, as with Ctrl+C


def request_stop() -> None:
    """Ask a running loop to stop (the window's "Parar"); it stops at the next pause and logs "Parado"."""
    _stop.set()


def _check_stop() -> None:
    if _stop.is_set():
        raise KeyboardInterrupt


def notice_kind(message: str) -> str | None:
    """"Erro" for a problem, "Aviso" for a warning (lines starting with "!"), None for the rest."""
    text = message.lstrip(chr(7)).strip()
    if any(word in text.lower() for word in ERROR_WORDS):
        return "Erro"
    return "Aviso" if text.startswith("!") else None


def _log(message: str) -> None:
    now = datetime.now()
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(f"{now:%Y-%m-%d %H:%M:%S}  {message}" + chr(10))
    repo_log.write(now, message)  # the same line in the repo, to read from any machine (D-022)
    line = f"{now:%H:%M:%S} {message.lstrip(chr(7))}"
    _recent.append(line)
    if any(word in message.lower() for word in ERROR_WORDS):
        _errors.append((time.time(), line))
    kind = notice_kind(message)
    if kind:
        _notices.append((f"{now:%H:%M:%S}", kind, message.lstrip(chr(7)).lstrip("! ").strip()))
    if not _screen_on:
        print(f"{now:%Y-%m-%d %H:%M:%S}  {message}", flush=True)
    elif _redraw:
        _redraw()


def _quiet(function, *args):
    """Call a function that prints (claim, train, ads); with the board on, its lines go to the log instead."""
    if not _screen_on:
        return function(*args)
    buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(buffer):
            return function(*args)
    finally:
        for line in buffer.getvalue().splitlines():
            if line.strip():
                _log(line.strip())


def _note_shortened(session_id: int) -> None:
    """A training video took 2h off this session: remember it for the blue part of the bar, and show the
    new finish time at once (``_live`` is cleared when a fresh snapshot, which already has it, arrives)."""
    for store in (_stats.setdefault("shortened", {}), _live.setdefault("shift", {})):
        store[session_id] = store.get(session_id, 0) + VIDEO_SAVES


def _shown(snapshot: dict | None) -> dict | None:
    """The last snapshot with the values read since then (coins after a video, trainings shortened by a video)."""
    if not snapshot or not _live:
        return snapshot
    shown = dict(snapshot)
    if "coins" in _live:
        shown["coins"] = _live["coins"]
    if "shop" in _live:
        shown["ads"] = {**snapshot["ads"], "shop": _live["shop"]}
    shift = _live.get("shift")
    if shift:
        shown["clubs"] = [{**club, "trainings": [{**t, "finish": t["finish"] - shift.get(t.get("id"), 0)} for t in club["trainings"]]}
                          for club in snapshot["clubs"]]
    return shown


def _counted(key: str, function, refresh=None):
    """Wrap a "watch one video" call so it is counted the moment it succeeds (a stop mid-burst loses nothing).
    ``refresh`` (optional) reads fresh values for the board, e.g. the boss coins; its failure is ignored."""
    def wrapper(*args):
        result = function(*args)
        _stats[key] = _stats.get(key, 0) + 1
        if refresh:
            try:
                refresh()
            except Exception:
                pass
        if _redraw:
            _redraw()
        return result
    return wrapper


def _tick_sleep(seconds: float) -> None:
    """A pause that keeps the board alive (countdowns move) instead of freezing it."""
    if not (_screen_on and _redraw):
        _check_stop()
        time.sleep(seconds)
        return
    end = time.time() + seconds
    while time.time() < end:
        _check_stop()
        _redraw()
        time.sleep(min(1.0, max(0.0, end - time.time())))
    _check_stop()


def _summary_data() -> dict:
    return {**_stats, "claimed": COUNTS["claimed"], "started": COUNTS["started"],
            "upgrades": stadium_module.COUNTS["upgrades"], "signed": sponsors_module.COUNTS["signed"],
            "r_login": rewards_module.COUNTS["login"], "r_missions": rewards_module.COUNTS["missions"],
            "r_videos": rewards_module.COUNTS["videos"], "friendlies": prematch_module.COUNTS["friendlies"],
            "analyses": prematch_module.COUNTS["analyses"]}  # doctor/lawyer counts live in medical_module.COUNTS


def _check_fitness(snapshot: dict | None, previous: set[int]) -> set[int]:
    """Log each starter that has just dropped below the yellow line (once, until they recover)."""
    if not snapshot:
        return previous
    now_tired = {}
    for club in snapshot["clubs"]:
        for player in club.get("tired") or []:
            now_tired[player["id"]] = (club["name"], player)
    for pid, (club, player) in now_tired.items():
        if pid not in previous:
            _log(f"! {club}: {player['name']} ({player['pos']}) com {player['fitness']}% de condição; convém descansar 1 jogo")
    return set(now_tired)


def _check_slots(read, previous: dict[str, int]) -> None:
    """Warn (console + log) when a club has more free transfer-list slots than at the last check."""
    try:
        for status in newly_free(read(), previous):
            _log("! " + describe(status))
    except Exception as error:  # read-only extra: never stop the training loop because of it
        _log(f"Slots: erro ao ler ({error})")


ADS_RETRY = 10 * 60.0  # after a failed video attempt, try again at most this far ahead
ADS_RETRY_MAX = 60 * 60.0  # the same kind failing again and again: wait longer each time, up to this
_ads_backoff: dict[str, tuple[int, float]] = {}  # kind of video -> (failures in a row, not before this time)


def ads_retry(failures: int) -> float:
    """Wait after the ``failures``-th failure in a row of one kind of video: 10, 20, 40, then 60 min."""
    return min(ADS_RETRY_MAX, ADS_RETRY * 2 ** (failures - 1))


def _shop_ads(dry_run: bool) -> int:
    from osmbot.game.client import OsmClient

    client = OsmClient()

    def refresh_coins() -> None:
        _live["coins"] = client.get("user/bosscoinwallet")[1]["amount"]
        cap = client.get(f"user/caps/actions/{SHOP_ACTION}/0")[1]  # the shop window may have just closed
        _live["shop"] = {"open": bool(cap.get("isClaimable")) and not cap.get("isCapReached"),
                         "reopen": cap.get("timestampUntilUnreached") if cap.get("isCapReached") else None}

    return run_shop_ads(lambda: is_claimable(client), _counted("shop", lambda: watch_shop_video(client), refresh_coins),
                        dry_run=dry_run, log=_log, sleep=_tick_sleep)


def _training_ads(dry_run: bool) -> int:
    from osmbot.game.client import OsmClient
    from osmbot.game.trainings import _teams

    client = OsmClient()
    clubs = {team["name"]: base for _, team, base in _teams(client)}

    def load():
        found = []
        for club, base in clubs.items():
            _, sessions = client.get(f"{base}/trainingsessions/ongoing")
            found += [(club, s) for s in sessions]
        return found

    def watch(club, session):
        watch_training_video(client, club, session, clubs[club])
        _note_shortened(session["id"])

    return run_training_ads(lambda: is_claimable(client, TRAINING_ACTION), load,
                            _counted("training", watch),
                            dry_run=dry_run, log=_log, sleep=_tick_sleep)


def _money_ads(dry_run: bool) -> int:
    from osmbot.game.client import OsmClient
    from osmbot.game.trainings import _teams

    client = OsmClient()

    def savings() -> dict[str, int]:
        return {team["name"]: client.get(f"{base}/finances")[1]["savings"] for _, team, base in _teams(client)}

    return run_money_ads(lambda: money_state(client)["open"], lambda: pick_money_club(savings()),
                         _counted("money", lambda club: watch_money_video(client, club), lambda: _refresh and _refresh()),
                         dry_run=dry_run, log=_log, sleep=_tick_sleep)


def _all_ads(dry_run: bool, clock=time.time) -> int:
    """Shop, training and money videos. Each kind is independent: one failing does not stop the others
    (the failure is reported after). Nothing is ever switched off, but a kind that keeps failing is left
    alone for longer each time (10, 20, 40, 60 min), so a broken page does not hold up every pass."""
    watched, errors = 0, []
    for step in (_shop_ads, _training_ads, _money_ads):
        name = step.__name__.strip("_")
        failures, not_before = _ads_backoff.get(name, (0, 0.0))
        if clock() < not_before:
            continue
        try:
            watched += step(dry_run)
            _ads_backoff.pop(name, None)
        except Exception as error:
            _ads_backoff[name] = (failures + 1, clock() + ads_retry(failures + 1))
            errors.append(f"{name}: {error}")
    if errors:
        raise AdsError("; ".join(errors))
    return watched


def ads_wake(now: float) -> float | None:
    """The earliest time a kind of video that failed may be tried again (None if none failed)."""
    times = [t for _, t in _ads_backoff.values() if t > now]
    return min(times) if times else None


def run_active(dry_run: bool = False, *, claim=run_claim, train=run_train, finish_times=None, slots=None,
               ads=lambda dry_run: _all_ads(dry_run), stadium=lambda confirm: run_stadium(confirm),
               sponsors=lambda confirm: run_sponsors(confirm), rewards=lambda confirm: run_rewards(confirm),
               prematch=lambda confirm: run_prematch(confirm), medical=lambda confirm: run_medical(confirm), snapshot=None, use_screen: bool | None = None,
               sleep=time.sleep, clock=time.time, rng=random, board=None) -> None:
    """Loop until Ctrl+C (or ``request_stop``) or the first failure. With ``dry_run`` do one simulated pass and show the board once.

    ``use_screen``: None = draw the board when the output is a terminal (and not a dry run).
    ``board``: the window (D-024) instead of the terminal: called with a dict (snapshot, status, stats, notices)
    whenever the board would be redrawn; nothing is printed then."""
    global _screen_on, _redraw, _refresh
    from osmbot.game.client import OsmClient

    finish_times = finish_times or (lambda: pending_finish_times(OsmClient()))
    slots = slots or (lambda: read_slots(OsmClient()))
    snapshot = snapshot or (lambda: collect(OsmClient()))
    free_before: dict[str, int] = {}
    tired_before: set[int] = set()
    last_snapshot = None
    _stats.clear()
    _live.clear()
    _errors.clear()
    _ads_backoff.clear()
    _notices.clear()
    _stop.clear()
    _stats["start"] = clock()
    COUNTS.update(claimed=0, started=0)
    stadium_module.COUNTS["upgrades"] = sponsors_module.COUNTS["signed"] = 0
    rewards_module.COUNTS.update(login=0, missions=0, videos=0)
    prematch_module.COUNTS.update(friendlies=0, analyses=0, collected=0)
    medical_module.COUNTS.update(doctor=0, lawyer=0, collected=0)
    machine = machine_name()
    if board:
        screen = None
    else:
        screen = Screen() if (sys.stdout.isatty() and not dry_run if use_screen is None else use_screen) else None
    shown = screen is not None or board is not None  # something draws the board: lines go to the log, not the terminal
    _screen_on = shown

    current = {"status": "A TRABALHAR"}

    def draw(status: str) -> None:
        current["status"] = status
        if screen:
            size = shutil.get_terminal_size((100, 40))
            problems = [line for when, line in _errors if time.time() - when < ERRORS_SHOWN_FOR]
            screen.draw(render(_shown(last_snapshot), clock(), status, problems, machine, stats=_summary_data(),
                               rows=size.lines, cols=size.columns))
        if board:
            board({"snapshot": _shown(last_snapshot), "status": status, "stats": _summary_data(), "notices": list(_notices)})

    _redraw = (lambda: draw(current["status"])) if shown else None

    def refresh_board() -> None:
        """Re-read the game and redraw now, so a change (trainings started, upgrade begun...) shows at once and
        not only when the whole pass, videos included, is over."""
        nonlocal last_snapshot
        try:
            last_snapshot = snapshot()
            _live.clear()
        except Exception:  # the snapshot at the end of the pass reports the problem
            pass
        draw(current["status"])

    _refresh = refresh_board if shown else None

    def changed(before: tuple) -> bool:
        return shown and counts() != before

    def counts() -> tuple:
        return (COUNTS["claimed"], COUNTS["started"], stadium_module.COUNTS["upgrades"], sponsors_module.COUNTS["signed"],
                *rewards_module.COUNTS.values(), *prematch_module.COUNTS.values(),
                *medical_module.COUNTS.values())

    try:
        _log("Simulação (uma passagem)" if dry_run else "Bot ligado")
        if shown:  # something to show right away, before the first pass (which can take minutes)
            try:
                last_snapshot = snapshot()
                _stats["coins0"] = last_snapshot["coins"]
                _live.clear()
            except Exception as error:
                _log(f"Estado inicial: erro ({error})")
        retries, offline_since, write_failures = 0, None, 0
        while True:
            try:
                _check_stop()
                draw("A TRABALHAR")
                ads_failed = False
                before = counts()
                failed = _quiet(claim, not dry_run) + _quiet(train, not dry_run)
                if changed(before):
                    refresh_board()
                if failed:  # e.g. the owner collected the same training by hand: the next pass re-reads the game
                    write_failures += 1
                    if write_failures >= MAX_WRITE_FAILURES:
                        _log(f"Parou: falhas ao escrever nos treinos em {write_failures} passagens seguidas. Ver bot.log")
                        raise SystemExit(1)
                    _log(f"Treinos: {failed} falha(s) ao escrever; volto a ver em {span(WRITE_RETRY)}"
                         f" ({write_failures}/{MAX_WRITE_FAILURES})")
                else:
                    write_failures = 0
                _check_slots(slots, free_before)
                before = counts()
                stadium_times: list[float] = []
                if stadium:
                    try:  # an extra too: a failure here never stops the trainings
                        stadium_failed, stadium_times = _quiet(stadium, not dry_run)
                        if stadium_failed:
                            _log(f"Estádio: {stadium_failed} falha(s); volto a tentar")
                    except OSError:
                        raise
                    except Exception as error:
                        _log(f"Estádio: erro ({error}); volto a tentar")
                if sponsors:
                    try:  # also an extra
                        sponsors_failed, _ = _quiet(sponsors, not dry_run)
                        if sponsors_failed:
                            _log(f"Patrocinadores: {sponsors_failed} falha(s); volto a tentar")
                    except OSError:
                        raise
                    except Exception as error:
                        _log(f"Patrocinadores: erro ({error}); volto a tentar")
                reward_times: list[float] = []
                if rewards:
                    try:  # an extra as well: the daily rewards never stop the trainings
                        rewards_failed, reward_times = _quiet(rewards, not dry_run)
                        if rewards_failed:
                            _log(f"Recompensas: {rewards_failed} falha(s); volto a tentar")
                    except OSError:
                        raise
                    except Exception as error:
                        _log(f"Recompensas: erro ({error}); volto a tentar")
                prematch_times: list[float] = []
                if prematch:
                    try:  # an extra: friendly and analysis 4 h before each match (THEORY.md section 6)
                        prematch_failed, prematch_times = _quiet(prematch, not dry_run)
                        if prematch_failed:
                            _log(f"Pré-jogo: {prematch_failed} falha(s); volto a tentar")
                    except OSError:
                        raise
                    except Exception as error:
                        _log(f"Pré-jogo: erro ({error}); volto a tentar")
                if changed(before):
                    refresh_board()
                medical_times: list[float] = []
                if medical:
                    before = counts()
                    try:  # an extra: doctor and lawyer (THEORY.md section 18)
                        medical_failed, medical_times = _quiet(medical, not dry_run)
                        if medical_failed:
                            _log(f"Médico/advogado: {medical_failed} falha(s); volto a tentar")
                    except OSError:
                        raise
                    except Exception as error:
                        _log(f"Médico/advogado: erro ({error}); volto a tentar")
                    if changed(before):
                        refresh_board()
                if ads:
                    try:
                        _quiet(ads, dry_run)
                    except Exception as error:  # ads are an extra: they never stop the trainings, and are retried
                        ads_failed = True
                        _log(f"Vídeos: erro ({error}); volto a tentar")
                try:
                    last_snapshot = snapshot()
                    _live.clear()  # the snapshot is fresher than anything read before it
                except Exception as error:  # the board is an extra too
                    _log(f"Quadro: erro ao atualizar ({error})")
                tired_before = _check_fitness(last_snapshot, tired_before)
                if last_snapshot and "coins0" not in _stats:
                    _stats["coins0"] = last_snapshot["coins"]
                events = wake_events(last_snapshot, clock())
                times = [ts for _, ts in events] or finish_times()
                times = times + [t for t in stadium_times + reward_times + prematch_times + medical_times if t > clock()]
                wait = next_wait(times, clock(), rng.uniform(*JITTER))
                if ads_failed:
                    again = ads_wake(clock())
                    wait = min(wait, max(MIN_WAIT, again - clock()) if again else ADS_RETRY)
                if failed:  # look again in 10 min, never sooner: a training left to collect would otherwise wake it every 30 s
                    wait = WRITE_RETRY
                retries, offline_since = 0, None
            except SystemExit as error:  # NeedsBrowserLogin is turned into SystemExit by the commands
                if error.code in (0, None, 1):
                    raise
                _log(f"Parou: {error.code}")
                raise
            except KeyboardInterrupt:
                _log("Parado")
                return
            except OSError as error:  # network trouble: patient retries, longer and longer, before giving up
                retries += 1
                offline_since = offline_since or clock()
                if clock() - offline_since > MAX_NETWORK_DOWN:
                    _log(f"Parou: sem rede há {span(clock() - offline_since)} ({error})")
                    raise SystemExit(1)
                wait = network_pause(retries)
                _log(f"Rede: erro ({error}); nova tentativa em {span(wait)} ({retries}.ª)")
                events = []
            if dry_run:
                if last_snapshot:
                    print(render(last_snapshot, clock(), "SIMULAÇÃO", list(_recent), machine, colour=sys.stdout.isatty()))
                _log(f"Simulação: próxima verificação em {span(wait)}")
                return
            _log("Próxima verificação: " + (" · ".join(f"{label} em {span(ts - clock())}" for label, ts in events) or f"em {span(wait)}"))
            try:
                deadline = clock() + wait
                if not shown:
                    sleep(wait)
                while shown and clock() < deadline:
                    _check_stop()
                    draw("ATIVO")
                    sleep(min(1.0, max(0.0, deadline - clock())))
            except KeyboardInterrupt:
                _log("Parado")
                return
    finally:
        if not dry_run and _stats.get("start") is not None:
            _log("Resumo: " + summary_text(last_snapshot, _summary_data(), clock()))
        if screen:
            screen.close()
            print(chr(10).join(_recent))
        if board:
            draw("PARADO")
        _screen_on = False
        _redraw = None
        _refresh = None
