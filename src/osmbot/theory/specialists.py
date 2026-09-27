"""Specialist selection (captain, penalties, free kicks, corners). See THEORY.md §4.

All functions take the **starters only** and return ``None`` when no eligible
player exists; deciding what to do then is the caller's job.

Ties that the theory does not cover are broken deterministically by higher
rating, then lower player id, so the same squad always gives the same answer.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from osmbot.models import Player, Position


def _best(players: Iterable[Player], key) -> Optional[Player]:
    return max(players, key=key, default=None)


def pick_captain(starters: Iterable[Player]) -> Optional[Player]:
    """Oldest player, regardless of rating; on equal age, higher rating."""
    return _best(starters, lambda p: (p.age, p.rating, -p.id))


def pick_penalty_taker(starters: Iterable[Player]) -> Optional[Player]:
    """Forward with the highest attack stat."""
    forwards = (p for p in starters if p.position is Position.ATT)
    return _best(forwards, lambda p: (p.stat_att, p.rating, -p.id))


def pick_free_kick_taker(starters: Iterable[Player]) -> Optional[Player]:
    """Any starter with the highest attack stat."""
    return _best(starters, lambda p: (p.stat_att, p.rating, -p.id))


def pick_corner_taker(starters: Iterable[Player]) -> Optional[Player]:
    """Midfielder with the highest attack stat."""
    mids = (p for p in starters if p.position is Position.MID)
    return _best(mids, lambda p: (p.stat_att, p.rating, -p.id))


@dataclass(frozen=True)
class Specialists:
    captain: Optional[Player]
    penalty_taker: Optional[Player]
    free_kick_taker: Optional[Player]
    corner_taker: Optional[Player]


def pick_specialists(starters: Iterable[Player]) -> Specialists:
    squad = list(starters)
    return Specialists(
        captain=pick_captain(squad),
        penalty_taker=pick_penalty_taker(squad),
        free_kick_taker=pick_free_kick_taker(squad),
        corner_taker=pick_corner_taker(squad),
    )
