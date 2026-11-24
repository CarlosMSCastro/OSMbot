"""Friendlies spread over the day and opponent analysis at the last hours before a match (THEORY.md section 6). Pure: no network, no I/O."""
from __future__ import annotations

LEAD = 4 * 3600  # act only when the match is this close: before that the owner may still do it himself (owner, 2026-10-08)
ANALYSIS_LEAD = 2 * 3600  # the bot analyses the opponent only this close, when the owner has not (owner, 2026-10-29)
FRIENDLY_STEP = 7  # matchpreparation step "Play 1 Friendly"
FRIENDLIES_PER_MATCH = 4  # owner, 2026-10-11: 4 friendlies before each match (THEORY.md section 6)
FRIENDLY_TIMES = (16 * 3600, 12 * 3600, 8 * 3600, 4 * 3600)  # spread over the day (owner, 2026-10-12): the k-th is due this long before the match [S]
EVENT_FRIENDLY_TIMES = tuple(h * 3600 for h in (16, 14, 12, 10, 8, 6, 4, 2))  # 8 in an Intense Friendlies [S]
# The events that bring 8 friendlies, recognised by name without spaces [S]: the Intense Friendlies (owner, 2026-10-12)
# and the Trainingcamp Terror, where each friendly gives more than the one before (forum; OSMPro series point 1: owner,
# 2026-10-28, "o dobro dos amigáveis, e claro medir": every friendly is recorded with its event in logs/*/amigaveis)
EVENT_NAMES = ("intensefriendlies", "trainingcampterror")
EVENT_MARGIN = 3600  # a friendly that would only fit after the event is played this long before it ends [S]
ANALYSIS_STEP = 5  # matchpreparation step "Analyse your opponent"
LEAGUE_MATCH, CUP_MATCH, FRIENDLY_MATCH = 0, 1, 2  # matchType in matches/filter (1 = cup: hypothesis)
DAY = 24 * 3600


def preseason(week: int | None) -> bool:
    """The 4 days before the first league match: ``weekNr`` -3 to 0 (seen -3 and -2, 2026-10-14/15)."""
    return week is not None and week < 1


def day_end(match_time: float | None, now: float, week: int | None) -> float | None:
    """When the game's day ends: the match; on a day with no match (the pre-season, or a round the club does not play),
    the same hour as the next match (one match a day), where the savings' interest is paid too (owner, 2026-10-15
    for the pre-season; 2026-10-24, rest days, a test: D-067; THEORY.md sections 6 and 13) [S]. ``week`` is not
    needed any more: kept for the callers."""
    if match_time is None or now >= match_time:
        return match_time
    return match_time - DAY * int((match_time - now) // DAY)


def in_window(match_time: float | None, now: float) -> bool:
    """True from 4 hours before the match until it starts."""
    return match_time is not None and match_time - LEAD <= now < match_time


def friendly_event(events: list[dict] | None, now: float) -> dict | None:
    """The friendlies' event going on now (``events``: the forum's schedule with "start" and "end"), if any."""
    return next((e for e in events or [] if any(name in e.get("nome", "").lower().replace(" ", "") for name in EVENT_NAMES)
                 and e["start"] <= now < e["end"]), None)


def friendly_deadlines(match_time: float, now: float, events: list[dict] | None = None) -> list[float]:
    """When each friendly of the round becomes due: 4 at 16/12/8/4 h before the match; during an Intense Friendlies 8
    at 16/14/.../2 h, none later than an hour before the event ends (THEORY.md section 6)."""
    event = friendly_event(events, now)
    if event is None:
        return [match_time - before for before in FRIENDLY_TIMES]
    return [min(match_time - before, event["end"] - EVENT_MARGIN) for before in EVENT_FRIENDLY_TIMES]


def friendlies_due(match_time: float | None, now: float, events: list[dict] | None = None) -> int:
    """How many friendlies should be played by now (4, or 8 in an Intense Friendlies), counting the deadlines passed."""
    if match_time is None or now >= match_time:
        return 0
    return sum(1 for at in friendly_deadlines(match_time, now, events) if at <= now)


def next_friendly_at(match_time: float | None, now: float, played: int, events: list[dict] | None = None) -> float | None:
    """When the next friendly becomes due, if that is still ahead (None: all played, or one is due now)."""
    if match_time is None:
        return None
    deadlines = friendly_deadlines(match_time, now, events)
    if played >= len(deadlines):
        return None
    at = deadlines[played]
    return at if at > now else None


def step_done(steps: list[dict], step_type: int) -> bool:
    """The checklist point is complete (or the game does not offer it: then there is nothing to do)."""
    step = next((s for s in steps if s.get("type") == step_type), None)
    if step is None or not step.get("enabled", True):
        return True
    return step.get("progressAmount", 0) >= step.get("completionAmount", 1)


def friendlies_played(matches: list[dict], team_id: int, week: int) -> int:
    """Friendlies the club already played this round (since its last match), the owner's included. Only the ones the
    club played at home, i.e. that it asked for: a rival who plays a friendly against it does not count, as in the
    game's own checklist (D-119)."""
    return sum(1 for m in matches if m["matchType"] == FRIENDLY_MATCH and m["weekNr"] == week and m["homeTeamId"] == team_id)


def friendlies_missing(matches: list[dict], team_id: int, week: int, target: int = FRIENDLIES_PER_MATCH) -> int:
    """Friendlies to play now so that ``target`` are done this round (all 4 by default)."""
    return max(0, target - friendlies_played(matches, team_id, week))


def needs_analysis(steps: list[dict], sent: list[dict], week: int, opponent: int | None = None) -> bool:
    """Whether the analyst must still go to the ``opponent`` this round. Done = an analyst already sent this round to
    him (by the bot or by hand; one sent to another club does not count: the analyst also goes round the league,
    owner 2026-10-28). The checklist's tick is not trusted when the opponent is known: an analyst collected after
    the round changed ticks the next round's step (Real Betis and KV Mechelen, 2026-10-28: collected at 00:38 and
    00:39, no analysis of that day's opponents). Not when the game does not offer it (step disabled: e.g. the
    opponent's secret training)."""
    step = next((s for s in steps if s.get("type") == ANALYSIS_STEP), None)
    if step is not None and not step.get("enabled", True):
        return False
    if opponent is None and step_done(steps, ANALYSIS_STEP):
        return False
    return not any(s.get("weekNr") == week and (opponent is None or s.get("instructionTeamId") in (None, opponent))
                   for s in sent)  # an entry with no club (older records) counts, as it did


SCOUT_MARGIN = 10 * 60  # an analysis of another club must end this long before the opponent's window opens
SCOUT_EVERY = 3  # rounds: another club is analysed at most once every 3 rounds (owner, 2026-11-15) [S]
SCOUT_START_MAX = 6 * 3600  # the tour starts up to 6 h after the previous match, a different hour each round [S]


def tour_start(match_time: float | None, now: float, week: int, key: str) -> float | None:
    """When the tour of the league may start this round: the previous match (a day before the next day's end) plus
    a delay of 0 to 6 h that changes with the club and the round, the same on every PC (owner, 2026-11-15: always at
    the same hour right after the match looks like a bot). None without a match."""
    end = day_end(match_time, now, week)
    if end is None:
        return None
    seed = sum((i + 1) * ord(c) for i, c in enumerate(f"{key}:{week}"))
    return end - DAY + (seed * 7919) % SCOUT_START_MAX


def analysis_window(match_time: float | None, now: float) -> bool:
    """True from 2 hours before the match until it starts: the bot's analysis of the opponent (owner, 2026-10-29)."""
    return match_time is not None and match_time - ANALYSIS_LEAD <= now < match_time


def analyst_busy(sent: list[dict], now: float) -> bool:
    """The analyst works on one club at a time (the game: "AlreadySpying", 2026-10-28): busy while a timer runs or
    a finished one is not collected yet."""
    return any((s.get("countdownTimer") or {}).get("isClaimed") is False for s in sent)


def scout_target(teams: list[dict], matches: list[dict], team_id: int, week: int, sent: list[dict],
                 last_seen: dict[int, int] | None = None) -> int | None:
    """The next club for the analyst to go round the league (owner, 2026-10-28; OSMPro series point 5): the
    opponents of the coming rounds first (not the next one: his analysis is in the 2 h before the match, closest to
    it), then the rest by place in the table. Each club at most once every ``SCOUT_EVERY`` rounds (owner, 2026-11-15:
    a manager complained of being analysed 14 times in 16 days): ``last_seen`` is the last round each club was
    analysed by this club (the logs, any PC). None when no club is due."""
    done = {s.get("instructionTeamId") for s in sent if s.get("weekNr") == week}
    for club, seen in (last_seen or {}).items():
        if 0 <= week - seen < SCOUT_EVERY:  # a lower round than the last one is a new season: due again
            done.add(club)
    following = next_opponent(matches, team_id, week)
    ahead = [_other(m, team_id) for m in sorted((m for m in matches if _involves(m, team_id) and m["weekNr"] > week
                                                  and m["matchType"] in (LEAGUE_MATCH, CUP_MATCH)), key=lambda m: m["weekNr"])]
    rest = [t["id"] for t in sorted(teams, key=lambda t: t.get("ranking") or 99)]
    for club in ahead + rest:
        if club not in done and club not in (team_id, following):
            return club
    return None


def can_scout(match: float | None, now: float, seconds: float, opponent_done: bool) -> bool:
    """Another club may be analysed now when it ends well before the bot's analysis of the next opponent (the last
    2 h before the match), and never once the opponent is analysed (owner, 2026-10-29): his analysis stays the last
    one until the match; the round after it, the tour starts again."""
    return not opponent_done and (match is None or now + seconds + SCOUT_MARGIN <= match - ANALYSIS_LEAD)


def _involves(match: dict, team_id: int) -> bool:
    return team_id in (match["homeTeamId"], match["awayTeamId"])


def _other(match: dict, team_id: int) -> int:
    return match["awayTeamId"] if match["homeTeamId"] == team_id else match["homeTeamId"]


def next_opponent(matches: list[dict], team_id: int, week: int) -> int | None:
    """The opponent of the club's next official match (league or cup) after ``week``, the last one played.
    None if there is none or the next week has more than one (unclear which comes first)."""
    ahead = [m for m in matches if _involves(m, team_id) and m["matchType"] in (LEAGUE_MATCH, CUP_MATCH) and m["weekNr"] > week]
    if not ahead:
        return None
    first = min(m["weekNr"] for m in ahead)
    found = [m for m in ahead if m["weekNr"] == first]
    return _other(found[0], team_id) if len(found) == 1 else None


def friendly_choices(teams: list[dict], matches: list[dict], team_id: int, week: int) -> list[int]:
    """Clubs of the league the club can still play a friendly against this week (one per opponent per week).
    Any of them will do (owner, 2026-10-08), except the next official opponent: the game refuses it (400, 5 of 5
    times seen, 2026-10-13 to 17)."""
    played = {_other(m, team_id) for m in matches
              if m["matchType"] == FRIENDLY_MATCH and m["weekNr"] == week and _involves(m, team_id)}
    played.add(next_opponent(matches, team_id, week))
    return [t["id"] for t in teams if t["id"] != team_id and t["id"] not in played]


STEP_NAMES = {0: "onze", 1: "banco", 2: "posições", 3: "em forma", 4: "especialistas", 5: "análise", 6: "treinos",
              7: "amigável", 8: "treino secreto", 9: "estágio"}  # matchpreparation step types (DISCOVERY.md section 3)


def prep_record(prep: dict, base: str, week: int, match: float) -> dict:
    """The game's pre-match checklist as one log line (owner, 2026-11-19: measure what the checklist is worth):
    the total and each point as [done, needed], by name."""
    points = {}
    for step in prep.get("steps") or []:
        name = STEP_NAMES.get(step.get("type"), str(step.get("type")))
        points[name] = [step.get("progressAmount", 0), step.get("completionAmount", 1)]
    return {"clube": base, "semana": week, "jogo": round(match), "pct": prep.get("completionPercentage"), "pontos": points}
