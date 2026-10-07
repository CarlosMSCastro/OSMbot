"""Active mode: keep claiming finished trainings and starting new ones, on its own (D-014), and
warn when a club has a free transfer-list slot, and watch the shop videos when the game allows.

Instead of a fixed interval, the bot wakes up when the next training finishes (plus a random
few seconds), so short-training periods (2h events) are handled as fast as the normal 8h ones.
Any failure stops the loop and says why: it never keeps hammering the game.
"""
from __future__ import annotations

import contextlib
import io
import random
import sys
import time
from collections import deque
from datetime import datetime
from pathlib import Path

from osmbot.game.ads import (TRAINING_ACTION, AdsError, is_claimable, money_state, pick_money_club, run_money_ads,
                             run_shop_ads, run_training_ads, watch_money_video, watch_shop_video, watch_training_video)
from osmbot.game.dashboard import Screen, collect, machine_name, render, span, summary_text, wake_events
from osmbot.game.slots import describe, newly_free, read_slots
from osmbot.game import sponsors as sponsors_module
from osmbot.game import stadium as stadium_module
from osmbot.game.sponsors import run_sponsors
from osmbot.game.stadium import run_stadium
from osmbot.game.trainings import COUNTS, pending_finish_times, run_claim, run_train

LOG_FILE = Path.home() / ".osmbot" / "bot.log"
JITTER = (5.0, 60.0)  # seconds added after a training finishes, so timing is never exact
MIN_WAIT = 30.0
MAX_WAIT = 30 * 60.0  # also re-check now and then, in case timers changed (e.g. a skip with boss coins)
MAX_NETWORK_RETRIES = 3
RETRY_PAUSE = 60.0


def next_wait(finish_times: list[float], now: float, jitter: float = 0.0) -> float:
    """Seconds to sleep until the earliest unclaimed training finishes (plus ``jitter``), within the limits."""
    if not finish_times:
        return MAX_WAIT
    wait = min(finish_times) - now + jitter
    return max(MIN_WAIT, min(MAX_WAIT, wait))


_recent: deque[str] = deque(maxlen=8)  # last log lines, for the board
_stats: dict = {}  # this run: start time, first coin balance, videos watched
_screen_on = False  # while the board is drawn, nothing else may print to the terminal
_redraw = None  # set by run_active while the board is on: redraws it after each new log line


def _log(message: str) -> None:
    now = datetime.now()
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(f"{now:%Y-%m-%d %H:%M:%S}  {message}" + chr(10))
    _recent.append(f"{now:%H:%M:%S} {message.lstrip(chr(7))}")
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


def _counted(key: str, function):
    """Wrap a "watch one video" call so it is counted the moment it succeeds (a stop mid-burst loses nothing)."""
    def wrapper(*args):
        result = function(*args)
        _stats[key] = _stats.get(key, 0) + 1
        if _redraw:
            _redraw()
        return result
    return wrapper


def _tick_sleep(seconds: float) -> None:
    """A pause that keeps the board alive (countdowns move) instead of freezing it."""
    if not (_screen_on and _redraw):
        time.sleep(seconds)
        return
    end = time.time() + seconds
    while time.time() < end:
        _redraw()
        time.sleep(min(1.0, max(0.0, end - time.time())))


def _summary_data() -> dict:
    return {**_stats, "claimed": COUNTS["claimed"], "started": COUNTS["started"],
            "upgrades": stadium_module.COUNTS["upgrades"], "signed": sponsors_module.COUNTS["signed"]}


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


def _shop_ads(dry_run: bool) -> int:
    from osmbot.game.client import OsmClient

    client = OsmClient()
    return run_shop_ads(lambda: is_claimable(client), _counted("shop", lambda: watch_shop_video(client)),
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

    return run_training_ads(lambda: is_claimable(client, TRAINING_ACTION), load,
                            _counted("training", lambda club, session: watch_training_video(client, club, session, clubs[club])),
                            dry_run=dry_run, log=_log, sleep=_tick_sleep)


def _money_ads(dry_run: bool) -> int:
    from osmbot.game.client import OsmClient
    from osmbot.game.trainings import _teams

    client = OsmClient()

    def savings() -> dict[str, int]:
        return {team["name"]: client.get(f"{base}/finances")[1]["savings"] for _, team, base in _teams(client)}

    return run_money_ads(lambda: money_state(client)["open"], lambda: pick_money_club(savings()),
                         _counted("money", lambda club: watch_money_video(client, club)),
                         dry_run=dry_run, log=_log, sleep=_tick_sleep)


def _all_ads(dry_run: bool) -> int:
    """Shop, training and money videos. Each kind is independent: one failing does not stop the others
    (the failure is reported after). Nothing is ever switched off: the next pass simply tries again."""
    watched, errors = 0, []
    for step in (_shop_ads, _training_ads, _money_ads):
        try:
            watched += step(dry_run)
        except Exception as error:
            errors.append(f"{step.__name__.strip('_')}: {error}")
    if errors:
        raise AdsError("; ".join(errors))
    return watched


def run_active(dry_run: bool = False, *, claim=run_claim, train=run_train, finish_times=None, slots=None,
               ads=lambda dry_run: _all_ads(dry_run), stadium=lambda confirm: run_stadium(confirm),
               sponsors=lambda confirm: run_sponsors(confirm), snapshot=None, use_screen: bool | None = None,
               sleep=time.sleep, clock=time.time, rng=random) -> None:
    """Loop until Ctrl+C or the first failure. With ``dry_run`` do one simulated pass and show the board once.

    ``use_screen``: None = draw the board when the output is a terminal (and not a dry run)."""
    global _screen_on, _redraw
    from osmbot.game.client import OsmClient

    finish_times = finish_times or (lambda: pending_finish_times(OsmClient()))
    slots = slots or (lambda: read_slots(OsmClient()))
    snapshot = snapshot or (lambda: collect(OsmClient()))
    free_before: dict[str, int] = {}
    tired_before: set[int] = set()
    last_snapshot = None
    _stats.clear()
    _stats["start"] = clock()
    COUNTS.update(claimed=0, started=0)
    stadium_module.COUNTS["upgrades"] = sponsors_module.COUNTS["signed"] = 0
    machine = machine_name()
    screen = Screen() if (sys.stdout.isatty() and not dry_run if use_screen is None else use_screen) else None
    _screen_on = screen is not None

    current = {"status": "A TRABALHAR"}

    def draw(status: str) -> None:
        current["status"] = status
        if screen:
            screen.draw(render(last_snapshot, clock(), status, list(_recent), machine, stats=_summary_data()))

    _redraw = (lambda: draw(current["status"])) if screen else None

    try:
        _log("Simulação (uma passagem)" if dry_run else "Bot ligado")
        if screen:  # something to show right away, before the first pass (which can take minutes)
            try:
                last_snapshot = snapshot()
                _stats["coins0"] = last_snapshot["coins"]
            except Exception as error:
                _log(f"Estado inicial: erro ({error})")
        retries = 0
        while True:
            try:
                draw("A TRABALHAR")
                ads_failed = False
                failed = _quiet(claim, not dry_run) + _quiet(train, not dry_run)
                if failed:
                    _log(f"Parou: {failed} falha(s) ao escrever. Ver bot.log")
                    raise SystemExit(1)
                _check_slots(slots, free_before)
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
                if ads:
                    try:
                        _quiet(ads, dry_run)
                    except Exception as error:  # ads are an extra: they never stop the trainings, and are retried
                        ads_failed = True
                        _log(f"Vídeos: erro ({error}); volto a tentar")
                try:
                    last_snapshot = snapshot()
                except Exception as error:  # the board is an extra too
                    _log(f"Quadro: erro ao atualizar ({error})")
                tired_before = _check_fitness(last_snapshot, tired_before)
                if last_snapshot and "coins0" not in _stats:
                    _stats["coins0"] = last_snapshot["coins"]
                events = wake_events(last_snapshot, clock())
                times = [ts for _, ts in events] or finish_times()
                times = times + [t for t in stadium_times if t > clock()]
                wait = next_wait(times, clock(), rng.uniform(*JITTER))
                if ads_failed:
                    wait = min(wait, ADS_RETRY)
                retries = 0
            except SystemExit as error:  # NeedsBrowserLogin is turned into SystemExit by the commands
                if error.code in (0, None, 1):
                    raise
                _log(f"Parou: {error.code}")
                raise
            except KeyboardInterrupt:
                _log("Parado")
                return
            except OSError as error:  # network trouble: a few patient retries, then stop
                retries += 1
                if retries > MAX_NETWORK_RETRIES:
                    _log(f"Parou: sem rede depois de {MAX_NETWORK_RETRIES} tentativas ({error})")
                    raise SystemExit(1)
                _log(f"Rede: erro ({error}); nova tentativa em {RETRY_PAUSE:.0f}s ({retries}/{MAX_NETWORK_RETRIES})")
                events, wait = [], RETRY_PAUSE
            if dry_run:
                if last_snapshot:
                    print(render(last_snapshot, clock(), "SIMULAÇÃO", list(_recent), machine, colour=sys.stdout.isatty()))
                _log(f"Simulação: próxima verificação em {span(wait)}")
                return
            _log("Próxima verificação: " + (" · ".join(f"{label} em {span(ts - clock())}" for label, ts in events) or f"em {span(wait)}"))
            try:
                deadline = clock() + wait
                if not screen:
                    sleep(wait)
                while screen and clock() < deadline:
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
            _screen_on = False
            _redraw = None
            print(chr(10).join(_recent))
        _screen_on = False
