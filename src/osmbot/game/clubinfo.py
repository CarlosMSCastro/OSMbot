"""The extra facts of the club card (D-026), read from the game (GET only).

Next match, cup, squad value, transfer list and sales, the pre-match checklist, injured and suspended players.
Slow-changing reads are kept for a while: the fixtures and cup rounds for 10 minutes, the squad values of the
whole league (one read per club) for an hour (the own club's always from its fresh squad). Ver → Atualizar
forgets them all (``forget``).
"""
from __future__ import annotations

import time

from osmbot.board.info import cup_phase, next_match, squad_value
from osmbot.game import sales
from osmbot.medical.policy import open_cases

FIXTURES_FOR = 10 * 60.0
VALUES_FOR = 3600.0
CHECKLIST = [(7, "Amigável"), (5, "Análise"), (0, "Onze"), (2, "Posições"), (3, "Em forma"), (1, "Banco"),
             (4, "Especialistas"), (6, "4 treinos")]  # matchpreparation step types, in the card's order
ANALYSIS_STEP = 5
_cache: dict[tuple, tuple[float, object]] = {}


def _cached(key: tuple, seconds: float, read):
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < seconds:
        return hit[1]
    value = read()
    _cache[key] = (time.time(), value)
    return value


def forget() -> None:
    """Drop the kept reads, so the next board read asks the game again (Ver → Atualizar)."""
    _cache.clear()


def _list(client, path: str) -> list:
    status, body = client.get(path)  # several of these answer 404 when the list is empty
    return body if status == 200 and isinstance(body, list) else []


def _values(client, league: str, teams: list[dict]) -> dict[int, tuple[int, int]]:
    from osmbot.game.dashboard import get_many

    answers = get_many(client, [f"{league}/teams/{t['id']}/players" for t in teams])
    values = {}
    for t, (status, players) in zip(teams, answers):
        players = players if status == 200 and isinstance(players, list) else []
        values[t["id"]] = (sum(p.get("value") or 0 for p in players), len(players))
    return values


def _as_list(answer: tuple[int, object]) -> list:
    status, body = answer
    return body if status == 200 and isinstance(body, list) else []


def _timer(case: dict) -> dict | None:
    timer = case.get("countdownTimer")
    return timer if timer and not timer.get("isClaimed") else None


def _people(players: list[dict], cases: list[dict]) -> list[dict]:
    """[{name, games, until, ready}]: ``until`` = when the doctor/lawyer case ends, ``ready`` = ended, to collect."""
    by_player = {c["playerId"]: _timer(c) for c in open_cases(cases)}
    now = time.time()
    result = []
    for p in players:
        timer = by_player.get(p["id"])
        end = timer["finishedTimestamp"] if timer else None
        result.append({"name": p["name"], "games": p.get("unavailable") or 0, "until": end,
                       "ready": bool(end and end <= now)})
    return result


def max_listed(client, league_id: int) -> int:
    """The game's limit of players on the transfer list (4 normally, 6 in events), kept for a while."""
    from osmbot.game.slots import MAX_SLOTS_SETTING

    def read():
        settings = _list(client, f"leagues/{league_id}/gamesettings")
        return next((g["value"] for g in settings if g["name"] == MAX_SLOTS_SETTING), 4)

    return _cached(("max_listed", league_id), FIXTURES_FOR, read)


def club_extra(client, team: dict, base: str, players: list[dict], slot, market: list[dict]) -> dict:
    from osmbot.game.dashboard import get_many

    league = base.rsplit("/teams/", 1)[0]
    got = get_many(client, [league, f"{league}/teams", f"{base}/matchpreparation",
                            f"{base}/spyinstructions", f"{base}/players/injured", f"{base}/doctortreatments"])
    week = got[0][1]["weekNr"]
    teams = _as_list(got[1])
    matches = _cached(("matches", league), FIXTURES_FOR, lambda: _list(client, f"{league}/matches/filter"))
    rounds = _cached(("rounds", league), FIXTURES_FOR, lambda: _list(client, f"{league}/cuprounds"))
    values = _cached(("values", league), VALUES_FOR, lambda: _values(client, league, teams))
    values = {**values, team["id"]: (sum(p.get("value") or 0 for p in players), len(players))}  # own squad: fresh

    squad = {p["id"] for p in players}
    listed = {item["player"]["id"]: {"name": item["player"].get("name", "?"), "price": item.get("price") or 0}
              for item in market if item["player"]["id"] in squad}
    sold = sales.update(f"{league}/{team['id']}", listed, squad)
    free = max(0, slot.maximum - slot.listed) if slot else 0

    status, prep = got[2]
    prep = prep if status == 200 and isinstance(prep, dict) else {}
    done = {s["type"]: s.get("progressAmount", 0) >= s.get("completionAmount", 1) for s in prep.get("steps") or []}
    analyst = None
    for entry in _as_list(got[3]):
        timer = _timer(entry)
        if entry.get("weekNr") == week and timer:
            analyst = timer["finishedTimestamp"]
    steps = [(name, done.get(kind, False), analyst if kind == ANALYSIS_STEP and not done.get(kind) else None)
             for kind, name in CHECKLIST]

    by_id = {p["id"]: p for p in players}
    injured = [{**p, "unavailable": by_id.get(p["id"], p).get("unavailable")} for p in _as_list(got[4])]
    injured_ids = {p["id"] for p in injured}
    suspended = [p for p in players if p.get("unavailable") and p["id"] not in injured_ids]
    doctor = _as_list(got[5])
    lawyer = _list(client, f"{base}/lawyercases") if suspended else []
    logo = next((a.get("path") for a in team.get("assets") or [] if a.get("type") == 4), None)
    return {
        "team_id": team["id"], "logo": logo, "logo_key": team.get("baseId") or str(team["id"]),
        "next": next_match(matches, teams, team["id"], week),
        "cup": cup_phase(rounds, matches, team["id"], week),
        "value": squad_value(values, team["id"]),
        "free_slots": free, "sales": sold,
        "prep": {"pct": prep.get("completionPercentage"), "steps": steps},
        "injured": _people(injured, doctor), "suspended": _people(suspended, lawyer),
    }
