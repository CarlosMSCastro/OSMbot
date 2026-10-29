"""The extra facts of the club card (D-026), read from the game (GET only).

Next match, cup, squad value, transfer list and sales, the pre-match checklist, injured and suspended players.
Slow-changing reads are kept for a while: the fixtures and cup rounds for 10 minutes, the squad values of the
whole league (one read per club) for an hour (the own club's always from its fresh squad). Ver → Atualizar
forgets them all (``forget``).
"""
from __future__ import annotations

import time

from osmbot.board.info import (cup_phase, eleven_seen, league_round, league_summary, next_match, next_matches,
                               opponent_rating, season_fixtures, squad_value, stale_listings, team_rating, value_table)
from osmbot.game import market as market_watch, sales
from osmbot.game.transfers import saved_transfers
from osmbot.game.specialists import captain_note, check
from osmbot.theory.lineup import age_warnings, bench_notes, centre_notes, listed_starters, bench_warnings, empty_places, places, position_warnings, tactic_check, tactic_notes, tactic_warnings
from osmbot.medical.policy import open_cases
from osmbot.prematch.policy import friendlies_played
from osmbot.theory.fitness import rest_warnings
from osmbot.theory.tactics import match_strength

GUESS_FORMATION = 433  # [S] another club's eleven is unknown before the analysis: his best 4-3-3 (THEORY.md 1, 16)

FIXTURES_FOR = 10 * 60.0
SPECIALISTS_STEP = 4  # matchpreparation step "Select specialists"
RULE = "fora da regra"  # a step the game ticks but the owner's rule does not
HIDDEN = "treino secreto"  # the analysis the game does not allow: the opponent is on a secret training
VALUES_FOR = 3600.0
BENCH_STEP, ELEVEN_STEP, POSITIONS_STEP = 1, 0, 2
TACTIC_STEP = "tactic"  # not a step of the game: the owner's rule for the tactics (D-073)
CHECKLIST = [(7, "Amigável"), (5, "Análise"), (0, "Onze"), (TACTIC_STEP, "Tática"), (2, "Posições"), (3, "Em forma"), (1, "Banco"),
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


def _people(players: list[dict], cases: list[dict], minutes: int) -> list[dict]:
    """[{name, games, until, ready, length}]: ``until`` = when the doctor/lawyer case ends, ``ready`` = ended, to
    collect, ``length`` = how long the case lasts in all (the game gives only its end; ``minutes`` = the timer now)."""
    from osmbot.game.dashboard import CASE_NORMAL, session_length

    by_player = {c["playerId"]: _timer(c) for c in open_cases(cases)}
    now = time.time()
    result = []
    for p in players:
        timer = by_player.get(p["id"])
        end = timer["finishedTimestamp"] if timer else None
        length = session_length(("case", timer.get("id") or p["id"]), end - now, minutes * 60, CASE_NORMAL) \
            if end and end > now else None
        result.append({"name": p["name"], "games": p.get("unavailable") or 0, "until": end,
                       "ready": bool(end and end <= now), "length": length})
    return result


def _settings(client, league_id: int) -> list[dict]:
    """The league's game settings, kept for a while (an event changes them: DISCOVERY.md §6b)."""
    return _cached(("gamesettings", league_id), FIXTURES_FOR, lambda: _list(client, f"leagues/{league_id}/gamesettings"))


def max_listed(client, league_id: int) -> int:
    """The game's limit of players on the transfer list (4 normally, 6 in events), kept for a while."""
    from osmbot.game.slots import MAX_SLOTS_SETTING

    return next((g["value"] for g in _settings(client, league_id) if g["name"] == MAX_SLOTS_SETTING), 4)


def timer_minutes(client, league_id: int, name: str) -> int:
    """How long the game's timer ``name`` lasts now in this league, in minutes (the doctor: 480 normally, 180 in the
    Super Staff), kept for a while."""
    from osmbot.events.calendar import NORMAL

    return next((g["value"] for g in _settings(client, league_id) if g["name"] == name and g.get("value")), NORMAL[name])


def league_sells_at_max(client, league_id: int) -> bool:
    """Whether a club of this league sold at the maximum lately (the league's transfers, kept for a while): without
    it, the resale profit of a "SALE" is uncertain (THEORY.md 7.7)."""
    from osmbot.transfers.engine import sells_at_max

    transfers = _cached(("transfers", league_id), FIXTURES_FOR, lambda: _list(client, f"leagues/{league_id}/transfers"))
    return sells_at_max(transfers, time.time())


def session_minutes(client, league_id: int) -> tuple[int, int]:
    """How long a training and a universal trainer's session last now in this league, in minutes (480 and 360
    normally, 120 and 90 in the Super Staff)."""
    return timer_minutes(client, league_id, "TrainingSession"), timer_minutes(client, league_id, "TrainingUniversalSession")


def _boost(client, path: str, key: tuple) -> int:
    """A manager's match boost from the daily logins (the game's "+3 %"), kept for a while; 0 when unreadable."""
    def read():
        status, answer = client.get(path)
        return (answer.get("matchBoost") or 0) if status == 200 and isinstance(answer, dict) else 0
    return _cached(key, FIXTURES_FOR, read)


def _match_strengths(client, team: dict, league: str, teams: list[dict], week: int, upcoming: dict | None,
                     strength: float | None, done: dict) -> tuple[float | None, float | None]:
    """Both sides' strength for the formation rule (THEORY.md section 1): team rating, match boosts (own daily logins,
    camp and secret training when marked; the opponent's daily logins once analysed and only with a human manager,
    as the site shows them) and the home advantage (not on neutral ground)."""
    from osmbot.theory.tactics import match_strength

    if not strength or not upcoming or not upcoming.get("strength"):
        return strength, None
    settings = {g["name"]: g["value"] for g in _settings(client, team["leagueId"])}
    own = _boost(client, "user/dailylogin", ("matchboost", "me"))
    own += sum(settings.get(name) or 0 for kind, name in ((9, "CampBoostPercentage"), (8, "SecretBoostPercentage"))
               if done.get(kind))
    rival = upcoming["opponent_id"]
    user = next((t.get("userId") for t in teams if t["id"] == rival), None)
    theirs = _boost(client, f"user/dailylogin/{user}/matchboost", ("matchboost", user, week)) \
        if user and done.get(ANALYSIS_STEP) else 0
    home = not upcoming.get("neutral")
    return (match_strength(strength, boost_pct=own, home=home and upcoming.get("side") == "H"),
            match_strength(upcoming["strength"], boost_pct=theirs, home=home and upcoming.get("side") == "A"))


def club_extra(client, team: dict, base: str, players: list[dict], slot, market: list[dict], match: float | None = None) -> dict:
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
    sold = sales.update(f"{league}/{team['id']}", listed, squad, team.get("name", "?"),
                        transfers=lambda: _list(client, f"{league}/transfers") + saved_transfers(team["leagueId"]),
                        team_id=team["id"])
    stale = stale_listings(listed, sales.sale_times(), time.time())  # "parado na lista" (THEORY.md 7.5)
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
    status, tactic = got[7]
    tactic = tactic if status == 200 and isinstance(tactic, dict) else None
    strength = team_rating(players, (tactic or {}).get("formation"))
    upcoming = next_match(matches, teams, team["id"], week)
    if upcoming:  # the opponent's strength in a circle, its squad value on hover (owner, 2026-10-13); before the
        rival = upcoming["opponent_id"]  # analysis an estimate, read again as soon as it is done (owner, 2026-10-25)
        upcoming["value"] = squad_value(values, rival)

        def rival_strength() -> tuple[int | None, bool, int | None]:
            squad_of = _list(client, f"{league}/teams/{rival}/players")
            seen = eleven_seen(squad_of)  # his forwards, once the analysis shows his eleven (THEORY.md 2)
            forwards = sum(1 for p in squad_of if 1 <= (p.get("lineup") or 0) <= 11 and p.get("position") == 1) if seen else None
            return opponent_rating(squad_of, GUESS_FORMATION), not seen, forwards

        upcoming["strength"], upcoming["estimate"], upcoming["forwards"] = _cached(
            ("strength", league, rival, week, bool(done.get(ANALYSIS_STEP))), FIXTURES_FOR, rival_strength)
    by_type = {s["type"]: s for s in prep.get("steps") or []}
    rival = (upcoming or {}).get("opponent_id")
    analyst = None  # only the analyst sent to the next opponent: one going round the league is not his analysis
    for entry in _as_list(got[3]):
        timer = _timer(entry)
        if entry.get("weekNr") == week and timer and entry.get("instructionTeamId") in (None, rival):
            analyst = timer["finishedTimestamp"]
    hidden = not (by_type.get(ANALYSIS_STEP) or {}).get("enabled", True)  # the opponent's secret training (2026-10-29)
    steps = [(name, done.get(kind, False), (HIDDEN if hidden else analyst) if kind == ANALYSIS_STEP and not done.get(kind) else None)
             for kind, name in CHECKLIST]
    friendlies = friendlies_played(matches, team["id"], week)  # owner, 2026-10-11: "Amigáveis (1)" … "(4)", green from the 1st
    steps = [(f"Amigáveis ({friendlies})", friendlies >= 1, None) if kind == FRIENDLY_STEP else step
             for (kind, _), step in zip(CHECKLIST, steps)]
    referees = _cached(("referees", league), FIXTURES_FOR, lambda: _list(client, f"{league}/referees"))
    strictness = next((r.get("strictness") for r in referees if upcoming and r["id"] == upcoming.get("referee_id")), None)
    mine, theirs = _match_strengths(client, team, league, teams, week, upcoming, strength, done)

    def important(match: dict) -> dict:  # stronger opponent or a direct rival (owner, 2026-10-22, THEORY.md 16)
        rival = match["opponent_id"]
        rating = _cached(("strength_guess", league, rival, week), FIXTURES_FOR,  # [S] his eleven unknown: best 4-3-3
                         lambda: team_rating(_list(client, f"{league}/teams/{rival}/players"), GUESS_FORMATION))
        home = not match.get("neutral")
        stronger = bool(rating and strength) and match_strength(rating, home=home and match["side"] == "A") \
            > match_strength(strength, home=home and match["side"] == "H")
        return {"opponent": match["opponent"], "important": match["danger"] or stronger}

    pair = [important(m) for m in next_matches(matches, teams, team["id"], week)]
    rest = rest_warnings(players, *(pair + [None, None])[:2])
    spare = len(pair) > 1 and not pair[0]["important"] and pair[1]["important"]  # rest them before it (THEORY.md 1, 16)
    away = bool(upcoming) and upcoming.get("side") == "A" and not upcoming.get("neutral")  # the 4-3-3 B away (THEORY.md 1)
    status, current = got[6]  # the game ticks any 4 specialists; yellow when they are not the owner's rule (D-042)
    current = current if status == 200 and isinstance(current, dict) else None
    why = {SPECIALISTS_STEP: check(players, current),
           BENCH_STEP: bench_warnings(players, spare),  # THEORY.md section 21: yellow with the reason on hover
           ELEVEN_STEP: empty_places(players, tactic) + listed_starters(players, listed, match, time.time())
           + tactic_warnings(tactic, mine, theirs, players, away, spare),
           POSITIONS_STEP: position_warnings(players, tactic)}  # who is out of position, on the hover
    why[TACTIC_STEP], tactic_tips, known = tactic_check(tactic, strictness, mine, theirs, players, away, spare,
                                                        (upcoming or {}).get("forwards"))
    steps = [(step[0], known, step[2]) if kind == TACTIC_STEP else step for (kind, _), step in zip(CHECKLIST, steps)]
    steps = [(name, False, RULE) if why.get(kind) and done_ else (name, done_, extra)
             for (kind, _), (name, done_, extra) in zip(CHECKLIST, steps)]
    reasons = {name: why[kind] for (kind, _), (name, _, _) in zip(CHECKLIST, steps) if why.get(kind)}
    notes = {ELEVEN_STEP: age_warnings(players) + centre_notes(players, tactic) + tactic_notes(tactic, players, mine, theirs, away, spare),  # within the
             BENCH_STEP: bench_notes(players, pair[1]["opponent"] if spare else None), TACTIC_STEP: tactic_tips,
             SPECIALISTS_STEP: captain_note(players, current)}  # rule: the step keeps its colour
    for (kind, _), (name, _, _) in zip(CHECKLIST, steps):
        if notes.get(kind):  # after any warning of the same step (the tackling may still be out of the rule)
            reasons[name] = reasons.get(name, []) + notes[kind]
    if hidden:  # the game does not let the analyst see him: say so, and what the estimate leaves out
        camp = {g["name"]: g["value"] for g in _settings(client, team["leagueId"])}.get("CampBoostPercentage")
        reasons[dict(CHECKLIST)[ANALYSIS_STEP]] = ["O adversário está em treino secreto: o jogo não deixa analisar",
                                    "A força dele é estimada (onze e tática não se veem)"] + (
            [f"Se fez estágio, tem mais {camp} % que não se vê"] if camp else [])
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
        "team_id": team["id"], "week": week, "logo": logo, "logo_key": team.get("baseId") or str(team["id"]),
        "next": upcoming, "places": places(tactic),  # the formation's places, for the buying card
        "cup": cup_phase(rounds, matches, team["id"], week), "round": league_round(matches, team["id"], week),
        "fixtures": season_fixtures(matches, teams, rounds, team["id"], week),
        "value": squad_value(values, team["id"]), "strength": strength,
        "value_table": value_table(values, {t["id"]: t["name"] for t in teams}, team["id"]),
        "table": league_summary(standings, teams, matches, team["id"], week, team.get("goal")),
        "free_slots": free, "sales": sold, "stale": stale, "rest": rest,
        "prep": {"pct": prep.get("completionPercentage"), "steps": steps, "why": reasons, "boosts": boosts},
        "injured": _people(injured, doctor, timer_minutes(client, team["leagueId"], "DoctorTreatmentTimer")),
        "suspended": _people(suspended, lawyer, timer_minutes(client, team["leagueId"], "LawyerCaseTimer")),
    }
