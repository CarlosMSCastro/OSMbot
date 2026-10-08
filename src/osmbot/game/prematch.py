"""Friendly and opponent analysis, 4 hours before each match, only if the owner has not done them
(writes, owner's rule in THEORY.md section 6; requests observed 2026-10-08, DISCOVERY.md section 3).

The game's own pre-match checklist (``matchpreparation``) says what is done. A friendly is played at once
(4 boss coins); the analyst takes an hour, so one sent this week also counts while it is still working, and when
the hour is over it has to be collected for the checklist to count it (observed 2026-10-09).
"""
from __future__ import annotations

import random
import time

from osmbot.prematch.policy import LEAD, friendly_choices, in_window, needs_analysis, needs_friendly, next_opponent

FRIENDLY_PRODUCT = 62  # bosscoinproducts: "Friendly"
FRIENDLY_PRICE = 4  # boss coins
SPY_TIMER_SETTING = 60  # gamesettings: "SpyInstructionTimer"
ANALYST_SECONDS = 3600  # SpyInstructionTimer: 60 min
NEXT_MATCH_TIMER = 14  # timers: "Your next match"
PAUSE_BETWEEN_WRITES = 1.5  # seconds
MAX_TRIES = 3  # friendly attempts per club per pass (a refused opponent moves on to another)
API_V11 = "https://web-api.onlinesoccermanager.com/api/v1.1"
COUNTS = {"friendlies": 0, "analyses": 0, "collected": 0}


def _match_time(client, base: str) -> float | None:
    _, timers = client.get(f"{base}/timers")
    return next((t["finishedTimestamp"] for t in timers if t["type"] == NEXT_MATCH_TIMER), None)


def _play_friendly(client, team: dict, base: str, league: str, week: int, confirm: bool, log, rng) -> int:
    _, wallet = client.get("user/bosscoinwallet")
    if wallet["amount"] < FRIENDLY_PRICE:
        log(f"! {team['name']}: sem boss coins para o amigável ({wallet['amount']}); fica por fazer")
        return 0
    _, teams = client.get(f"{league}/teams")
    _, matches = client.get(f"{league}/matches/filter")
    names = {t["id"]: t["name"] for t in teams}
    choices = friendly_choices(teams, matches, team["id"], week)
    rng.shuffle(choices)
    for opponent in choices[:MAX_TRIES]:
        if not confirm:
            log(f"{team['name']}: faria 1 amigável contra {names[opponent]}")
            return 0
        status, body = client.post(f"{base}/matches", {"opponentId": opponent, "productId": FRIENDLY_PRODUCT})
        time.sleep(PAUSE_BETWEEN_WRITES)
        if status == 200 and isinstance(body, dict):
            COUNTS["friendlies"] += 1
            mine_home = body.get("homeTeamId") == team["id"]
            score = (f"{body.get('homeGoals')}-{body.get('awayGoals')}" if mine_home
                     else f"{body.get('awayGoals')}-{body.get('homeGoals')}")
            log(f"Amigável: {team['name']} {score} {names[opponent]}")
            return 0
        if not 400 <= status < 500:
            log(f"Amigável: {team['name']} contra {names[opponent]} falhou ({status})")
            return 1
        log(f"Amigável: {team['name']} contra {names[opponent]} recusado ({status}); tento outro")
    if not choices:
        log(f"! {team['name']}: nenhum clube disponível para amigável nesta jornada")
    return 0


def _send_analyst(client, team: dict, base: str, league: str, week: int, confirm: bool, log) -> int:
    _, matches = client.get(f"{league}/matches/filter")
    opponent = next_opponent(matches, team["id"], week)
    if opponent is None:
        log(f"! {team['name']}: não sei quem é o próximo adversário; análise fica por fazer")
        return 0
    _, teams = client.get(f"{league}/teams")
    name = next((t["name"] for t in teams if t["id"] == opponent), str(opponent))
    if not confirm:
        log(f"{team['name']}: enviaria o analista a {name}")
        return 0
    status, _ = client.post(f"{base}/spyinstructions", {"instructionTeamId": opponent, "timerGameSettingId": SPY_TIMER_SETTING})
    time.sleep(PAUSE_BETWEEN_WRITES)
    if status == 200:
        COUNTS["analyses"] += 1
        log(f"Análise: {team['name']} enviou o analista a {name} (1 h)")
        return 0
    log(f"Análise: {team['name']} → {name} falhou ({status})")
    return 1


def _collect_analyst(client, team: dict, base: str, sent: list[dict], week: int, now: float, confirm: bool, log) -> tuple[int, float | None]:
    """Collect this week's analyst once its hour is over. Returns (failures, when it ends if still working)."""
    for entry in sent:
        timer = entry.get("countdownTimer")
        if entry.get("weekNr") != week or not timer or timer.get("isClaimed"):
            continue
        if timer["finishedTimestamp"] > now:
            return 0, timer["finishedTimestamp"]
        if not confirm:
            log(f"{team['name']}: levantaria o analista")
            return 0, None
        status, _ = client.put(f"{API_V11}/{base}/spyinstructions/{entry['id']}/claim")
        time.sleep(PAUSE_BETWEEN_WRITES)
        if status == 200:
            COUNTS["collected"] += 1
            log(f"Análise: {team['name']} levantou o analista")
            return 0, None
        log(f"Análise: {team['name']} levantar o analista falhou ({status})")
        return 1, None
    return 0, None


def prepare_club(client, team: dict, base: str, confirm: bool, now: float, log=print, rng=random) -> tuple[int, float | None]:
    """Friendly and analysis for one club when its match is 4 hours away or less. Returns (failures, time to wake at)."""
    match = _match_time(client, base)
    if not in_window(match, now):
        return 0, (match - LEAD if match and match - LEAD > now else None)
    league = base.rsplit("/teams/", 1)[0]
    _, info = client.get(league)
    week = info["weekNr"]
    _, prep = client.get(f"{base}/matchpreparation")
    steps = prep.get("steps") or []
    failures = 0
    if needs_friendly(steps):
        failures += _play_friendly(client, team, base, league, week, confirm, log, rng)
    status, sent = client.get(f"{base}/spyinstructions")  # 404 when nothing was sent
    sent = sent if status == 200 and isinstance(sent, list) else []
    wake = None
    if needs_analysis(steps, sent, week):
        before = COUNTS["analyses"]
        failures += _send_analyst(client, team, base, league, week, confirm, log)
        if COUNTS["analyses"] > before:
            wake = now + ANALYST_SECONDS  # come back when the hour is over, to collect it
    else:
        failed, wake = _collect_analyst(client, team, base, sent, week, now, confirm, log)
        failures += failed
    return failures, wake


def run_prematch(confirm: bool) -> tuple[int, list[float]]:
    """Every club. Returns (failures, times to wake at: 4 hours before each match). Without ``confirm`` only shows the plan."""
    from osmbot.game.client import NeedsBrowserLogin, OsmClient
    from osmbot.game.trainings import _teams

    failures, wake = 0, []
    try:
        client = OsmClient()
        for _, team, base in _teams(client):
            failed, at = prepare_club(client, team, base, confirm, time.time())
            failures += failed
            if at:
                wake.append(at)
    except NeedsBrowserLogin as error:
        raise SystemExit(str(error))
    return failures, wake
