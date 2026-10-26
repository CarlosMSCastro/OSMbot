"""Which stadium part to upgrade next (THEORY.md section 15). Pure: no network, no I/O."""
from __future__ import annotations

# stadiumPartType values (DISCOVERY.md section 3): 0 Capacity, 1 Pitch, 2 Training.
# Owner's order (2026-10-25): training ground to level 1, pitch to level 1 (one 18 h cycle each), then training ground
# to the top, pitch to the top, capacity. None: the part's top level.
STEPS = ((2, 1), (1, 1), (2, None), (1, None), (0, None))
PART_NAMES = {0: "capacidade", 1: "campo", 2: "campo de treinos"}


def max_level(part: dict) -> int:
    return max((lvl["level"] for lvl in part.get("stadiumPartLevels") or []), default=0)


def running_until(parts: list[dict], now: float) -> float | None:
    """When the upgrade in progress ends, or None if no part is being upgraded (one at a time)."""
    ends = [p["countdownTimer"]["finishedTimestamp"] for p in parts
            if p.get("countdownTimer") and p["countdownTimer"]["finishedTimestamp"] > now]
    return max(ends) if ends else None


def to_claim(parts: list[dict], now: float) -> list[dict]:
    """Finished upgrades still to collect: they only count once collected (DISCOVERY.md section 3, 2026-10-24)."""
    return [p for p in parts if p.get("countdownTimer") and p["countdownTimer"]["finishedTimestamp"] <= now
            and not p["countdownTimer"].get("isClaimed")]


def next_part(parts: list[dict], now: float) -> int | None:
    """The part type to start upgrading now, or None (one is already running, or everything is at the top)."""
    if running_until(parts, now) is not None:
        return None
    by_type = {p["stadiumPartType"]: p for p in parts}
    for part_type, level in STEPS:
        part = by_type.get(part_type)
        if part is not None and part["level"] < min(level or max_level(part), max_level(part)):
            return part_type
    return None
