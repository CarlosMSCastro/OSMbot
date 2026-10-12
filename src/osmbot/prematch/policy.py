"""Friendlies spread over the day and opponent analysis at the last hours before a match (THEORY.md section 6). Pure: no network, no I/O."""
from __future__ import annotations

LEAD = 4 * 3600  # act only when the match is this close: before that the owner may still do it himself (owner, 2026-10-08)
FRIENDLY_STEP = 7  # matchpreparation step "Play 1 Friendly"
FRIENDLIES_PER_MATCH = 4  # owner, 2026-10-11: 4 friendlies before each match (THEORY.md section 6)
FRIENDLY_TIMES = (16 * 3600, 12 * 3600, 8 * 3600, 4 * 3600)  # spread over the day (owner, 2026-10-12): the k-th is due this long before the match [S]
ANALYSIS_STEP = 5  # matchpreparation step "Analyse your opponent"
LEAGUE_MATCH, CUP_MATCH, FRIENDLY_MATCH = 0, 1, 2  # matchType in matches/filter (1 = cup: hypothesis)


def in_window(match_time: float | None, now: float) -> bool:
    """True from 4 hours before the match until it starts."""
    return match_time is not None and match_time - LEAD <= now < match_time


def friendlies_due(match_time: float | None, now: float) -> int:
    """How many of the 4 friendlies should be played by now: one more at each of FRIENDLY_TIMES before the match."""
    if match_time is None or now >= match_time:
        return 0
    return sum(1 for before in FRIENDLY_TIMES if match_time - before <= now)


def next_friendly_at(match_time: float | None, now: float, played: int) -> float | None:
    """When the next friendly becomes due, if that is still ahead (None: all played, or one is due now)."""
    if match_time is None or played >= len(FRIENDLY_TIMES):
        return None
    at = match_time - FRIENDLY_TIMES[played]
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
    Any of them will do (owner, 2026-10-08)."""
    played = {_other(m, team_id) for m in matches
              if m["matchType"] == FRIENDLY_MATCH and m["weekNr"] == week and _involves(m, team_id)}
    return [t["id"] for t in teams if t["id"] != team_id and t["id"] not in played]
