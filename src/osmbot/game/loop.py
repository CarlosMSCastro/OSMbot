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

from osmbot.game.ads import (TRAINING_ACTION, AdsError, is_claimable, run_shop_ads, run_training_ads, watch_shop_video,
                             watch_training_video)
from osmbot.game.dashboard import Screen, collect, machine_name, render, span, summary_text, wake_events
from osmbot.game.slots import describe, newly_free, read_slots
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
    return {**_stats, "claimed": COUNTS["claimed"], "started": COUNTS["started"]}


def _check_slots(read, previous: dict[str, int]) -> None:
    """Warn (console + log) when a club has more free transfer-list slots than at the last check."""
    try:
        for status in newly_free(read(), previous):
            _log("*** AVISO: " + describe(status))
    except Exception as error:  # read-only extra: never stop the training loop because of it
        _log(f"Nao consegui verificar os slots de venda ({error}).")


MAX_ADS_FAILURES = 2  # in a row; then ads are switched off for this run (trainings go on)


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


def _all_ads(dry_run: bool) -> int:
    """Shop videos, then training videos; one failing does not stop the other (the failure is reported after)."""
    watched, errors = 0, []
    for step in (_shop_ads, _training_ads):
        try:
            watched += step(dry_run)
        except Exception as error:
            errors.append(f"{step.__name__.strip('_')}: {error}")
    if errors:
        raise AdsError("; ".join(errors))
    return watched


def run_active(dry_run: bool = False, *, claim=run_claim, train=run_train, finish_times=None, slots=None,
               ads=lambda dry_run: _all_ads(dry_run), snapshot=None, use_screen: bool | None = None,
               sleep=time.sleep, clock=time.time, rng=random) -> None:
    """Loop until Ctrl+C or the first failure. With ``dry_run`` do one simulated pass and show the board once.

    ``use_screen``: None = draw the board when the output is a terminal (and not a dry run)."""
    global _screen_on, _redraw
    from osmbot.game.client import OsmClient

    finish_times = finish_times or (lambda: pending_finish_times(OsmClient()))
    slots = slots or (lambda: read_slots(OsmClient()))
    snapshot = snapshot or (lambda: collect(OsmClient()))
    free_before: dict[str, int] = {}
    ads_failures = 0
    last_snapshot = None
    _stats.clear()
    _stats["start"] = clock()
    COUNTS.update(claimed=0, started=0)
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
        _log("Modo ativo " + ("(simulacao, uma passagem)" if dry_run else "ligado. Ctrl+C para parar."))
        if screen:  # something to show right away, before the first pass (which can take minutes)
            try:
                last_snapshot = snapshot()
                _stats["coins0"] = last_snapshot["coins"]
            except Exception as error:
                _log(f"Nao consegui ler o estado inicial ({error}).")
        retries = 0
        while True:
            try:
                draw("A TRABALHAR")
                failed = _quiet(claim, not dry_run) + _quiet(train, not dry_run)
                if failed:
                    _log(f"PAROU: {failed} acao(oes) falharam. Nao repito sozinho; vê o registo e corre 'osmbot treinos'.")
                    raise SystemExit(1)
                _check_slots(slots, free_before)
                if ads:
                    try:
                        _quiet(ads, dry_run)
                        ads_failures = 0
                    except Exception as error:  # ads are an extra: they never stop the trainings
                        ads_failures += 1
                        _log(f"Anuncios: falhou ({error}) [{ads_failures}/{MAX_ADS_FAILURES}].")
                        if ads_failures >= MAX_ADS_FAILURES:
                            _log("Anuncios desligados ate ao proximo arranque; os treinos continuam.")
                            ads = None
                try:
                    last_snapshot = snapshot()
                except Exception as error:  # the board is an extra too
                    _log(f"Nao consegui atualizar o quadro ({error}).")
                if last_snapshot and "coins0" not in _stats:
                    _stats["coins0"] = last_snapshot["coins"]
                events = wake_events(last_snapshot, clock())
                times = [ts for _, ts in events] or finish_times()
                wait = next_wait(times, clock(), rng.uniform(*JITTER))
                retries = 0
            except SystemExit as error:  # NeedsBrowserLogin is turned into SystemExit by the commands
                if error.code in (0, None, 1):
                    raise
                _log(f"PAROU: {error.code}")
                raise
            except KeyboardInterrupt:
                _log("Parado pelo dono.")
                return
            except OSError as error:  # network trouble: a few patient retries, then stop
                retries += 1
                if retries > MAX_NETWORK_RETRIES:
                    _log(f"PAROU: sem rede/servidor depois de {MAX_NETWORK_RETRIES} tentativas ({error}).")
                    raise SystemExit(1)
                _log(f"Erro de rede ({error}); tento outra vez daqui a {RETRY_PAUSE:.0f}s ({retries}/{MAX_NETWORK_RETRIES}).")
                events, wait = [], RETRY_PAUSE
            if dry_run:
                if last_snapshot:
                    print(render(last_snapshot, clock(), "SIMULACAO", list(_recent), machine, colour=sys.stdout.isatty()))
                _log(f"Simulacao: acordaria daqui a {span(wait)}.")
                return
            _log("A espera " + (" · ".join(f"{label} em {span(ts - clock())}" for label, ts in events) or f"{span(wait)}") + ".")
            try:
                deadline = clock() + wait
                if not screen:
                    sleep(wait)
                while screen and clock() < deadline:
                    draw("ATIVO")
                    sleep(min(1.0, max(0.0, deadline - clock())))
            except KeyboardInterrupt:
                _log("Parado pelo dono.")
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
