"""Friendlies spread over the day and opponent analysis at the last hours before a match (THEORY.md section 6). Pure: no network, no I/O."""
from __future__ import annotations

LEAD = 4 * 3600  # act only when the match is this close: before that the owner may still do it himself (owner, 2026-10-08)
FRIENDLY_STEP = 7  # matchpreparation step "Play 1 Friendly"
FRIENDLIES_PER_MATCH = 4  # owner, 2026-10-11: 4 friendlies before each match (THEORY.md section 6)
FRIENDLY_TIMES = (16 * 3600, 12 * 3600, 8 * 3600, 4 * 3600)  # spread over the day (owner, 2026-10-12): the k-th is due this long before the match [S]
EVENT_FRIENDLY_TIMES = tuple(h * 3600 for h in (16, 14, 12, 10, 8, 6, 4, 2))  # 8 in an Intense Friendlies [S]
EVENT_NAME = "intense friendlies"  # the event that brings 8 friendlies (owner, 2026-10-12); recognised by name [S]
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
    """The Intense Friendlies going on now (``events``: the forum's schedule with "start" and "end"), if any."""
    return next((e for e in events or [] if EVENT_NAME in e.get("nome", "").lower() and e["start"] <= now < e["end"]), None)


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
    """Friendlies the club already played this round (since its last match), the owner's included."""
    return sum(1 for m in matches if m["matchType"] == FRIENDLY_MATCH and m["weekNr"] == week and _involves(m, team_id))


def friendlies_missing(matches: list[dict], team_id: int, week: int, target: int = FRIENDLIES_PER_MATCH) -> int:
    """Friendlies to play now so that ``target`` are done this round (all 4 by default)."""
    return max(0, target - friendlies_played(matches, team_id, week))


def needs_analysis(steps: list[dict], sent: list[dict], week: int) -> bool:
    """The checklist counts the analysis only once the analyst is collected: one already sent this week counts too."""
    if step_done(steps, ANALYSIS_STEP):
        return False
    return not any(s.get("weekNr") == week for s in sent)


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
