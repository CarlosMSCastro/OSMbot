"""Everything into savings just before each match (THEORY.md section 13; owner, 2026-10-12). Pure: no network, no I/O.

Savings earn 2 % at the end of the day's match, so what came into the club's funds during the day (sponsors,
a sale) is deposited right before it. Not earlier: the owner may still take the money out to buy someone.
"""
from __future__ import annotations

LEAD = 5 * 60  # the bot wakes this long before the match and deposits first thing (owner asked 2 min; 5 for safety)
WINDOW = 15 * 60  # any pass this close to the match deposits too: a long run of videos may delay the wake above


def deposit_due(match_time: float | None, now: float) -> bool:
    """True from 15 minutes before the match until it starts."""
    return match_time is not None and match_time - WINDOW <= now < match_time


def wake_at(match_time: float | None, now: float) -> float | None:
    """When to wake for the deposit, if that is still ahead."""
    if match_time is None or match_time - LEAD <= now:
        return None
    return match_time - LEAD
