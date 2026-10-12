"""Friendlies spread over the day and opponent analysis 4 hours before each match, only what the owner has not done
(writes, owner's rule in THEORY.md section 6; requests observed 2026-10-08, DISCOVERY.md section 3).

The game's own pre-match checklist (``matchpreparation``) says what is done. A friendly is played at once
(4 boss coins each, 4 before each match, owner 2026-10-11; one more due at 16, 12, 8 and 4 hours before it, owner
2026-10-12); the analyst takes an hour, so one sent this week also counts while it is still working, and when
the hour is over it has to be collected for the checklist to count it (observed 2026-10-09): at any hour, as soon
as it is ready (owner, 2026-10-12).
A refused request is noted and not repeated this round (D-032): a refused opponent is left out, the others are tried.
"""
from __future__ import annotations

import random
import time

from osmbot import logs
from osmbot.game import clubinfo, refusals
from osmbot.prematch.policy import (FRIENDLIES_PER_MATCH, LEAD, friendly_choices, friendlies_due, friendlies_missing,
                                    friendlies_played, in_window, needs_analysis, next_friendly_at, next_opponent)

FRIENDLY_PRODUCT = 62  # bosscoinproducts: "Friendly"
FRIENDLY_PRICE = 4  # boss coins
SPY_TIMER_SETTING = 60  # gamesettings: "SpyInstructionTimer"
ANALYST_SECONDS = 3600  # SpyInstructionTimer: 60 min
NEXT_MATCH_TIMER = 14  # timers: "Your next match"
PAUSE_BETWEEN_WRITES = 1.5  # seconds
MAX_REFUSALS = 3  # refused friendlies per club per pass before giving up until the next pass (each moves on to another club)
GAP_BETWEEN_FRIENDLIES = (3, 8)  # × PAUSE_BETWEEN_WRITES: a few seconds between friendlies, not a burst
API_V11 = "https://web-api.onlinesoccermanager.com/api/v1.1"
COUNTS = {"friendlies": 0, "analyses": 0, "collected": 0}


def _match_time(client, base: str) -> float | None:
    _, timers = client.get(f"{base}/timers")
    return next((t["finishedTimestamp"] for t in timers if t["type"] == NEXT_MATCH_TIMER), None)


def _progress(client, base: str) -> dict[int, dict]:
    """Each player's training progress and stats, to see what a friendly gave (owner, 2026-10-12)."""
    status, players = client.get(f"{base}/players")
    if status != 200 or not isinstance(players, list):
        return {}
    return {p["id"]: {"nome": p.get("name"), "pos": p.get("position"), "progresso": p.get("trainingProgress"),
                      "att": p.get("statAtt"), "def": p.get("statDef"), "ovr": p.get("statOvr")} for p in players}


def _changed(before: dict[int, dict], after: dict[int, dict]) -> list[dict]:
    keys = ("progresso", "att", "def", "ovr")
    return [{"id": pid, "nome": now["nome"], "pos": now["pos"], **{f"{k}_antes": before[pid][k] for k in keys},
             **{f"{k}_depois": now[k] for k in keys}}
            for pid, now in after.items() if pid in before and any(before[pid][k] != now[k] for k in keys)]


def _play_friendlies(client, team: dict, base: str, league: str, week: int, target: int, confirm: bool, log, rng) -> tuple[int, int]:
    """Play the friendlies missing for ``target`` to be done this round (the owner's included; THEORY.md section 6).
    Returns (failures, friendlies played this round now)."""
    _, matches = client.get(f"{league}/matches/filter")
    before = friendlies_played(matches, team["id"], week)
    missing = friendlies_missing(matches, team["id"], week, target)
    if not missing:
        return 0, before
    _, teams = client.get(f"{league}/teams")
    names = {t["id"]: t["name"] for t in teams}
    choices = friendly_choices(teams, matches, team["id"], week)
    every = len(choices)
    choices = [c for c in choices if not refusals.blocked(f"amigável:{base}:{c}", week=week)]
    rng.shuffle(choices)
    if not confirm:
        if choices:
            log(f"{team['name']}: faria {min(missing, len(choices))} amigável(eis) contra {', '.join(names[c] for c in choices[:missing])}")
        return 0, before
    played = refused = 0
    progress = _progress(client, base)
    for opponent in choices:
        if played == missing or refused == MAX_REFUSALS:
            break
        _, wallet = client.get("user/bosscoinwallet")
        if wallet["amount"] < FRIENDLY_PRICE:
            log(f"! {team['name']}: sem boss coins para o amigável ({wallet['amount']}); "
                f"{FRIENDLIES_PER_MATCH - before - played} de {FRIENDLIES_PER_MATCH} ficam por fazer")
            return 0, before + played
        if played:
            time.sleep(PAUSE_BETWEEN_WRITES * rng.uniform(*GAP_BETWEEN_FRIENDLIES))
        status, body = client.post(f"{base}/matches", {"opponentId": opponent, "productId": FRIENDLY_PRODUCT})
        time.sleep(PAUSE_BETWEEN_WRITES)
        if status == 200 and isinstance(body, dict):
            played += 1
            COUNTS["friendlies"] += 1
            clubinfo.forget_fixtures(league)  # the card counts them from the fixtures: show this one now
            mine_home = body.get("homeTeamId") == team["id"]
            score = (f"{body.get('homeGoals')}-{body.get('awayGoals')}" if mine_home
                     else f"{body.get('awayGoals')}-{body.get('homeGoals')}")
            log(f"Amigável: {team['name']} {score} {names[opponent]}")
            later = _progress(client, base)
            logs.record("amigaveis", {"clube": base, "semana": week, "n_na_jornada": before + played,
                                      "adversario": names[opponent], "resultado": score, "jogadores": _changed(progress, later)})
            progress = later or progress
            continue
        if not refusals.is_refusal(status):
            log(f"Amigável: {team['name']} contra {names[opponent]} falhou ({status})")
            return 1, before + played
        refused += 1
        refusals.refuse(f"amigável:{base}:{opponent}", log, f"Amigável: {team['name']} contra {names[opponent]} recusado ({status}); "
                        "não volto a tentar este clube nesta jornada", week=week)
    if not every:
        log(f"! {team['name']}: nenhum clube disponível para amigável nesta jornada")
    return 0, before + played


def _send_analyst(client, team: dict, base: str, league: str, week: int, confirm: bool, log) -> int:
    _, matches = client.get(f"{league}/matches/filter")
    opponent = next_opponent(matches, team["id"], week)
    if opponent is None:
        log(f"! {team['name']}: não sei quem é o próximo adversário; análise fica por fazer")
        return 0
    _, teams = client.get(f"{league}/teams")
    name = next((t["name"] for t in teams if t["id"] == opponent), str(opponent))
    key = f"analista:enviar:{base}"
    if refusals.blocked(key, week=week):
        return 0
    if not confirm:
        log(f"{team['name']}: enviaria o analista a {name}")
        return 0
    status, _ = client.post(f"{base}/spyinstructions", {"instructionTeamId": opponent, "timerGameSettingId": SPY_TIMER_SETTING})
    time.sleep(PAUSE_BETWEEN_WRITES)
    if status == 200:
        COUNTS["analyses"] += 1
        log(f"Análise: {team['name']} enviou o analista a {name} (1 h)")
        return 0
    if refusals.is_refusal(status):
        refusals.refuse(key, log, f"! Análise: o jogo recusou enviar o analista a {name} ({team['name']}, {status}); "
                        "volto a tentar na próxima jornada", week=week)
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
        key = f"analista:levantar:{base}:{entry['id']}"
        if refusals.blocked(key, week=week):
            return 0, None
        if not confirm:
            log(f"{team['name']}: levantaria o analista")
            return 0, None
        status, _ = client.put(f"{API_V11}/{base}/spyinstructions/{entry['id']}/claim")
        time.sleep(PAUSE_BETWEEN_WRITES)
        if status == 200:
            COUNTS["collected"] += 1
            log(f"Análise: {team['name']} levantou o analista")
            return 0, None
        if refusals.is_refusal(status):
            refusals.refuse(key, log, f"! Análise (levantar): o jogo recusou ({team['name']}, {status}); volto a tentar na próxima jornada",
                            week=week)
            return 0, None
        log(f"Análise: {team['name']} levantar o analista falhou ({status})")
        return 1, None
    return 0, None


def prepare_club(client, team: dict, base: str, confirm: bool, now: float, log=print, rng=random) -> tuple[int, float | None]:
    """One club: collect a finished analyst (any hour), the friendlies due by now, and the analysis when the match is
    4 hours away or less. Returns (failures, time to wake at)."""
    match = _match_time(client, base)
    league = base.rsplit("/teams/", 1)[0]
    _, info = client.get(league)
    week = info["weekNr"]
    status, sent = client.get(f"{base}/spyinstructions")  # 404 when nothing was sent
    sent = sent if status == 200 and isinstance(sent, list) else []
    failures, wake = _collect_analyst(client, team, base, sent, week, now, confirm, log)
    wakes = [wake]
    if match is None or now >= match:
        return failures, wake
    due = friendlies_due(match, now)
    played = 0
    if due:
        failed, played = _play_friendlies(client, team, base, league, week, due, confirm, log, rng)
        failures += failed
    wakes.append(next_friendly_at(match, now, played))
    if not in_window(match, now):
        wakes.append(match - LEAD)  # the analysis is sent only in the last 4 hours
    else:
        _, prep = client.get(f"{base}/matchpreparation")
        if needs_analysis(prep.get("steps") or [], sent, week):
            before = COUNTS["analyses"]
            failures += _send_analyst(client, team, base, league, week, confirm, log)
            if COUNTS["analyses"] > before:
                wakes.append(now + ANALYST_SECONDS)  # come back when the hour is over, to collect it
    ahead = [w for w in wakes if w and w > now]
    return failures, min(ahead) if ahead else None


def run_prematch(confirm: bool) -> tuple[int, list[float]]:
    """Every club. Returns (failures, times to wake at: next friendly, analysis window, analyst ready). Without ``confirm`` only shows the plan."""
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
