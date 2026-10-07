"""Which sponsor goes into which free slot (THEORY.md section 15). Pure: no network, no I/O."""
from __future__ import annotations

SIDES = (1, 2, 3, 4)  # the four sponsor slots


def active(current: list[dict]) -> list[dict]:
    return [s for s in current if s.get("weeksLeft", 0) > 0]


def free_sides(current: list[dict]) -> list[int]:
    taken = {s["side"] for s in active(current)}
    return [side for side in SIDES if side not in taken]


def ranked_offers(offers: list[dict]) -> list[dict]:
    """Best first: most revenue per round, a shorter contract wins a tie."""
    return sorted(offers, key=lambda o: (-o["sponsorRevenueForTeam"], o["weeks"], o["id"]))


def next_choice(offers: list[dict], current: list[dict], refused: set[tuple[int, int]] = frozenset()) -> tuple[int, dict] | None:
    """(side, offer) for the first free slot: the best offer the game has not refused for that slot.

    The owner's rule is "the best for each slot": the same sponsor may repeat; if the game refuses a
    repeat (or an offer that slot does not have), ``refused`` holds (side, offer id) and the next best is used."""
    ranked = ranked_offers(offers)
    for side in free_sides(current):
        for offer in ranked:
            if (side, offer["id"]) not in refused:
                return side, offer
    return None
