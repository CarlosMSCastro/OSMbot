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


def doctor_candidates(injured: list[int], cases: list[dict], games_out: dict[int, int] | None = None,
                      listed: set[int] | frozenset = frozenset()) -> list[int]:
    """Every injured player not with the doctor right now (the doctor may be used again and again, owner 2026-10-09),
    in the order to send them (owner, 2026-11-03; OSMPro Outros point 4): first the fewest games out (one treatment
    takes off 1, sometimes 2: it may be enough for him to play), the ones on the transfer list last. Someone the game
    refuses waits for the running case, so the order picks who gets the one place."""
    busy = {c["playerId"] for c in open_cases(cases)}
    out = games_out or {}
    wanted = [pid for pid in injured if pid not in busy]
    return sorted(wanted, key=lambda pid: (pid in listed, out.get(pid) or 99))


def lawyer_candidates(suspended: list[int], cases: list[dict], week: int) -> list[int]:
    """Every suspended player without a lawyer case this week (once per week, owner 2026-10-09)."""
    used = {c["playerId"] for c in cases if c.get("weekNr") == week} | {c["playerId"] for c in open_cases(cases)}
    return [pid for pid in suspended if pid not in used]
