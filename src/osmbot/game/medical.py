"""Doctor and lawyer (writes, owner's rules in THEORY.md section 18; DISCOVERY.md section 3).

Free, with an 8-hour timer, collected at the end like a training. Sending to the doctor and collecting it were
observed (2026-10-09; the collect is on api/v1, not v1.1 like the analyst); the lawyer flow follows the doctor's,
accepted by the owner. A refused request is noted and not repeated (D-032).
"""
from __future__ import annotations

import time

from osmbot.game import refusals
from osmbot.medical.policy import LAWYER_MIN_GAMES, doctor_candidates, lawyer_candidates, running_until, to_collect

PAUSE_BETWEEN_WRITES = 1.5  # seconds
CASE_SECONDS = 8 * 3600  # DoctorTreatmentTimer and LawyerCaseTimer: 480 min
COUNTS = {"doctor": 0, "lawyer": 0, "collected": 0}
KINDS = {  # kind -> (cases path, gamesettings timer id, label, "sent to" text)
    "doctor": ("doctortreatments", 48, "Médico", "no médico"),  # DoctorTreatmentTimer
    "lawyer": ("lawyercases", 45, "Advogado", "no advogado"),  # LawyerCaseTimer
}


def _list(client, path: str) -> list[dict]:
    status, body = client.get(path)  # 404 when there is nothing
    return body if status == 200 and isinstance(body, list) else []


def _names(players: list[dict]) -> dict[int, str]:
    return {p["id"]: p["name"] for p in players}


def _collect(client, team: dict, base: str, kind: str, cases: list[dict], names: dict, now: float, week: int,
             confirm: bool, log) -> tuple[int, int]:
    """Collect the finished cases. A refused collect is not asked again this round (D-032). Returns (failures, collected)."""
    path, _, label, _ = KINDS[kind]
    failures = collected = 0
    for case in to_collect(cases, now):
        name = names.get(case["playerId"], str(case["playerId"]))
        key = f"{kind}:levantar:{base}:{case['id']}"
        if refusals.blocked(key, week=week):
            continue
        if not confirm:
            log(f"{team['name']}: levantaria {name} ({label.lower()})")
            continue
        status, _ = client.put(f"{base}/{path}/{case['id']}/claim")
        time.sleep(PAUSE_BETWEEN_WRITES)
        if status == 200:
            COUNTS["collected"] += 1
            collected += 1
            log(f"{label}: {team['name']} levantou {name}")
        elif refusals.is_refusal(status):
            refusals.refuse(key, log, f"! {label} (levantar): o jogo recusou {name} ({status}); volto a tentar na próxima jornada",
                            week=week)
        else:
            log(f"{label}: {team['name']} levantar {name} falhou ({status})")
            failures += 1
    return failures, collected


def _send(client, team: dict, base: str, kind: str, candidates: list[int], names: dict, cases: list[dict], now: float,
          week: int, confirm: bool, log) -> tuple[int, int]:
    """Send each candidate. A refusal is not repeated (D-032): while another player is being treated the game may take
    only one, so it waits for that case to end; otherwise it waits for the next round. Returns (failures, sent)."""
    path, setting, label, place = KINDS[kind]
    sent = 0
    for pid in candidates:
        name = names.get(pid, str(pid))
        key = f"{kind}:pôr:{base}:{pid}"
        if refusals.blocked(key, week=week, now=now):
            continue
        if not confirm:
            log(f"{team['name']}: poria {name} {place}")
            continue
        status, _ = client.post(f"{base}/{path}", {"playerId": pid, "timerGameSettingId": setting})
        time.sleep(PAUSE_BETWEEN_WRITES)
        if status == 200:
            COUNTS[kind] += 1
            sent += 1
            log(f"{label}: {team['name']} pôs {name} {place} (8 h)")
        elif refusals.is_refusal(status):
            busy = running_until(cases, now)
            if busy:  # e.g. only one at a time: this one waits for the running case to end (THEORY.md section 18)
                refusals.refuse(key, log, f"{label}: {team['name']} {name} fica à espera que acabe o tratamento em curso ({status})",
                                until=min(busy))
            else:
                refusals.refuse(key, log, f"! {label}: o jogo recusou {name} ({team['name']}, {status}); volto a tentar na próxima jornada",
                                week=week)
            break
        else:
            log(f"{label}: {team['name']} {name} falhou ({status})")
            return 1, sent
    return 0, sent


def treat_club(client, team: dict, base: str, confirm: bool, now: float, log=print) -> tuple[int, list[float]]:
    """Collect finished cases, then send every injured player to the doctor and every suspended one to the lawyer.
    Returns (failures, times a case ends)."""
    league = base.rsplit("/teams/", 1)[0]
    _, info = client.get(league)
    week = info["weekNr"]
    injured_players = _list(client, f"{base}/players/injured")
    injured = [p["id"] for p in injured_players]
    _, players = client.get(f"{base}/players")
    names = {**_names(players), **_names(injured_players)}
    suspended = [p["id"] for p in players if p.get("unavailable", 0) >= LAWYER_MIN_GAMES and p["id"] not in injured]
    failures, wake = 0, []
    for kind, people in (("doctor", injured), ("lawyer", suspended)):
        path = KINDS[kind][0]
        if kind == "lawyer" and not people:
            continue  # nobody suspended: nothing to send, and a lawyer case only lasts while the player is out
        cases = _list(client, f"{base}/{path}")
        failed, collected = _collect(client, team, base, kind, cases, names, now, week, confirm, log)
        failures += failed
        if collected:  # read again: the player may be fit already, and the case is no longer open
            cases = _list(client, f"{base}/{path}")
            if kind == "doctor":
                people = [p["id"] for p in _list(client, f"{base}/players/injured")]
        wanted = doctor_candidates(people, cases) if kind == "doctor" else lawyer_candidates(people, cases, week)
        failed, sent = _send(client, team, base, kind, wanted, names, cases, now, week, confirm, log)
        failures += failed
        wake += running_until(cases, now) + [now + CASE_SECONDS] * sent
    return failures, wake


def run_medical(confirm: bool) -> tuple[int, list[float]]:
    """Every club. Returns (failures, times to wake at). Without ``confirm`` only shows the plan."""
    from osmbot.game.client import NeedsBrowserLogin, OsmClient
    from osmbot.game.trainings import _teams

    failures, wake = 0, []
    try:
        client = OsmClient()
        for _, team, base in _teams(client):
            failed, ends = treat_club(client, team, base, confirm, time.time())
            failures += failed
            wake += ends
    except NeedsBrowserLogin as error:
        raise SystemExit(str(error))
    return failures, wake
