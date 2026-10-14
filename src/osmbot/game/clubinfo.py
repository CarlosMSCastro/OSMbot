"""The extra facts of the club card (D-026), read from the game (GET only).

Next match, cup, squad value, transfer list and sales, the pre-match checklist, injured and suspended players.
Slow-changing reads are kept for a while: the fixtures and cup rounds for 10 minutes, the squad values of the
whole league (one read per club) for an hour (the own club's always from its fresh squad). Ver → Atualizar
forgets them all (``forget``).
"""
from __future__ import annotations

import time

from osmbot.board.info import cup_phase, league_summary, next_match, squad_value, team_rating
from osmbot.game import market as market_watch, sales
from osmbot.game.specialists import check
from osmbot.theory.lineup import bench_warnings, position_warnings, tactic_warnings
from osmbot.medical.policy import open_cases
from osmbot.prematch.policy import friendlies_played

FIXTURES_FOR = 10 * 60.0
SPECIALISTS_STEP = 4  # matchpreparation step "Select specialists"
RULE = "fora da regra"  # a step the game ticks but the owner's rule does not
VALUES_FOR = 3600.0
BENCH_STEP, ELEVEN_STEP, POSITIONS_STEP = 1, 0, 2
CHECKLIST = [(7, "Amigável"), (5, "Análise"), (0, "Onze"), (2, "Posições"), (3, "Em forma"), (1, "Banco"),
             (4, "Especialistas"), (6, "4 treinos")]  # matchpreparation step types, in the card's order
BOOSTS = [(8, "secret", "Treino secreto"), (9, "camp", "Estágio")]  # matchpreparation steps bought with boss coins: shown under the checklist
ANALYSIS_STEP = 5
FRIENDLY_STEP = 7
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


def forget_fixtures(league: str) -> None:
    """Read the league's fixtures again next time (the bot just played a friendly)."""
    _cache.pop(("matches", league), None)


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


def _settings(client, league_id: int) -> list[dict]:
    """The league's game settings, kept for a while (an event changes them: DISCOVERY.md §6b)."""
    return _cached(("gamesettings", league_id), FIXTURES_FOR, lambda: _list(client, f"leagues/{league_id}/gamesettings"))


def max_listed(client, league_id: int) -> int:
    """The game's limit of players on the transfer list (4 normally, 6 in events), kept for a while."""
    from osmbot.game.slots import MAX_SLOTS_SETTING

    return next((g["value"] for g in _settings(client, league_id) if g["name"] == MAX_SLOTS_SETTING), 4)


def session_minutes(client, league_id: int) -> tuple[int, int]:
    """How long a training and a universal trainer's session last now in this league, in minutes (480 and 360
    normally, 120 and 90 in the Super Staff)."""
    from osmbot.events.calendar import NORMAL

    values = {g["name"]: g["value"] for g in _settings(client, league_id)}
    return (values.get("TrainingSession") or NORMAL["TrainingSession"],
            values.get("TrainingUniversalSession") or NORMAL["TrainingUniversalSession"])


def club_extra(client, team: dict, base: str, players: list[dict], slot, market: list[dict]) -> dict:
    from osmbot.game.dashboard import get_many

    league = base.rsplit("/teams/", 1)[0]
    got = get_many(client, [league, f"{league}/teams", f"{base}/matchpreparation",
                            f"{base}/spyinstructions", f"{base}/players/injured", f"{base}/doctortreatments",
                            f"{base}/specialists", f"{base}/teamtactics"])
    week = got[0][1]["weekNr"]
    teams = _as_list(got[1])
    matches = _cached(("matches", league), FIXTURES_FOR, lambda: _list(client, f"{league}/matches/filter"))
    rounds = _cached(("rounds", league), FIXTURES_FOR, lambda: _list(client, f"{league}/cuprounds"))
    values = _cached(("values", league), VALUES_FOR, lambda: _values(client, league, teams))
    values = {**values, team["id"]: (sum(p.get("value") or 0 for p in players), len(players))}  # own squad: fresh

    squad = {p["id"] for p in players}
    values_now = {p["id"]: p.get("value") or 0 for p in players}
    listed = {item["player"]["id"]: {"name": item["player"].get("name", "?"), "price": item.get("price") or 0,
                                     "value": values_now[item["player"]["id"]], "since": item.get("timeStampForSale")}
              for item in market if item["player"]["id"] in squad}
    sold = sales.update(f"{league}/{team['id']}", listed, squad, team.get("name", "?"))
    owner = next((t.get("userId") for t in teams if t["id"] == team["id"]), None)
    try:  # the engine records (D-034): never in the way of the card
        market_watch.watch(client, got[0][1]["id"], got[0][1].get("name", ""), market, owner)
    except OSError:
        raise
    except Exception:
        pass
    free = max(0, slot.maximum - slot.listed) if slot else 0
    sold = sold if free else []  # the green arrows go once the slots are full again (owner, 2026-10-13)

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
    friendlies = friendlies_played(matches, team["id"], week)  # owner, 2026-10-11: "Amigáveis (1)" … "(4)", green from the 1st
    steps = [(f"Amigáveis ({friendlies})", friendlies >= 1, None) if kind == FRIENDLY_STEP else step
             for (kind, _), step in zip(CHECKLIST, steps)]
    status, tactic = got[7]
    tactic = tactic if status == 200 and isinstance(tactic, dict) else None
    strength = team_rating(players, (tactic or {}).get("formation"))
    upcoming = next_match(matches, teams, team["id"], week)
    if upcoming:  # the opponent's strength in a circle (only once analysed), its squad value on hover (owner, 2026-10-13)
        rival = upcoming["opponent_id"]
        upcoming["value"] = squad_value(values, rival)
        upcoming["strength"] = _cached(("strength", league, rival, week), FIXTURES_FOR,
                                       lambda: team_rating(_list(client, f"{league}/teams/{rival}/players")))
    referees = _cached(("referees", league), FIXTURES_FOR, lambda: _list(client, f"{league}/referees"))
    strictness = next((r.get("strictness") for r in referees if upcoming and r["id"] == upcoming.get("referee_id")), None)
    status, current = got[6]  # the game ticks any 4 specialists; yellow when they are not the owner's rule (D-042)
    why = {SPECIALISTS_STEP: check(players, current if status == 200 and isinstance(current, dict) else None),
           BENCH_STEP: bench_warnings(players),  # THEORY.md section 21: yellow with the reason on hover
           ELEVEN_STEP: tactic_warnings(tactic, strictness, strength, (upcoming or {}).get("strength")),
           POSITIONS_STEP: position_warnings(players, tactic)}  # who is out of position, on the hover
    steps = [(name, False, RULE) if why.get(kind) and done_ else (name, done_, extra)
             for (kind, _), (name, done_, extra) in zip(CHECKLIST, steps)]
    reasons = {name: why[kind] for (kind, _), (name, _, _) in zip(CHECKLIST, steps) if why.get(kind)}
    by_type = {s["type"]: s for s in prep.get("steps") or []}
    boosts = [{"kind": key, "name": name, "on": done.get(kind, False),  # marked for the next match (owner, 2026-10-14)
               "blocked": "" if (by_type.get(kind) or {}).get("enabled", True) else by_type[kind].get("disabledText") or "?"}
              for kind, key, name in BOOSTS]

    by_id = {p["id"]: p for p in players}
    injured = [{**p, "unavailable": by_id.get(p["id"], p).get("unavailable")} for p in _as_list(got[4])]
    injured_ids = {p["id"] for p in injured}
    suspended = [p for p in players if p.get("unavailable") and p["id"] not in injured_ids]
    doctor = _as_list(got[5])
    lawyer = _list(client, f"{base}/lawyercases") if suspended else []
    logo = next((a.get("path") for a in team.get("assets") or [] if a.get("type") == 4), None)
    standings = _cached(("standings", league), FIXTURES_FOR, lambda: _list(client, f"{league}/standings"))
    return {
        "team_id": team["id"], "logo": logo, "logo_key": team.get("baseId") or str(team["id"]),
        "next": upcoming,
        "cup": cup_phase(rounds, matches, team["id"], week),
        "value": squad_value(values, team["id"]), "strength": strength,
        "table": league_summary(standings, teams, matches, team["id"], week, team.get("goal")),
        "free_slots": free, "sales": sold,
        "prep": {"pct": prep.get("completionPercentage"), "steps": steps, "why": reasons, "boosts": boosts},
        "injured": _people(injured, doctor), "suspended": _people(suspended, lawyer),
    }
