"""Doctor and lawyer (THEORY.md section 18): who to send and which cases to collect. Pure: no network."""
from __future__ import annotations

LAWYER_MIN_GAMES = 2  # the lawyer brings a suspension down to 1 game: with 1 game the game refuses it (owner, 2026-10-09)


def _timer(case: dict) -> dict | None:
    timer = case.get("countdownTimer")
    return timer if timer and not timer.get("isClaimed") else None


def open_cases(cases: list[dict]) -> list[dict]:
    """Cases still running or finished but not collected yet."""
    return [c for c in cases if _timer(c)]


def to_collect(cases: list[dict], now: float) -> list[dict]:
    return [c for c in open_cases(cases) if _timer(c)["finishedTimestamp"] <= now]


def running_until(cases: list[dict], now: float) -> list[float]:
    return [_timer(c)["finishedTimestamp"] for c in open_cases(cases) if _timer(c)["finishedTimestamp"] > now]


def doctor_candidates(injured: list[int], cases: list[dict]) -> list[int]:
    """Every injured player not with the doctor right now (the doctor may be used again and again, owner 2026-10-09)."""
    busy = {c["playerId"] for c in open_cases(cases)}
    return [pid for pid in injured if pid not in busy]


def lawyer_candidates(suspended: list[int], cases: list[dict], week: int) -> list[int]:
    """Every suspended player without a lawyer case this week (once per week, owner 2026-10-09)."""
    used = {c["playerId"] for c in cases if c.get("weekNr") == week} | {c["playerId"] for c in open_cases(cases)}
    return [pid for pid in suspended if pid not in used]
