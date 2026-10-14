"""Specialist selection (captain, penalties, free kicks, corners). See THEORY.md §4.

All functions take the **starters only** and return ``None`` when no eligible
player exists; deciding what to do then is the caller's job.

Equal attack: the better rest of the stats wins (overall + defence; owner, 2026-10-14).
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


def _attack(p: Player) -> tuple:
    """Attack first; on equal attack, the better rest of the stats (owner, 2026-10-14)."""
    return (p.stat_att, p.stat_ovr + p.stat_def, p.rating, -p.id)


def pick_penalty_taker(starters: Iterable[Player]) -> Optional[Player]:
    """Forward with the highest attack stat."""
    forwards = (p for p in starters if p.position is Position.ATT)
    return _best(forwards, _attack)


def pick_free_kick_taker(starters: Iterable[Player]) -> Optional[Player]:
    """Any starter with the highest attack stat."""
    return _best(starters, _attack)


def pick_corner_taker(starters: Iterable[Player]) -> Optional[Player]:
    """Midfielder with the highest attack stat."""
    mids = (p for p in starters if p.position is Position.MID)
    return _best(mids, _attack)


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


ROLES = {"captain": "captain", "penalty": "penalty_taker", "freekick": "free_kick_taker", "corners": "corner_taker"}  # game -> ours
ROLE_NAMES = {"captain": "capitão", "penalty": "penáltis", "freekick": "livres", "corners": "cantos"}


def wanted_slots(players: Iterable[Player]) -> dict[str, Optional[int]]:
    """The lineup place (1-11) the owner's rule gives each role, as the game stores it (``specialists``: a place in
    the eleven, not a player). A player out of the eleven is out of the specialists too (owner, 2026-10-12)."""
    chosen = pick_specialists(p for p in players if p.starter)
    return {role: (getattr(chosen, ours).lineup if getattr(chosen, ours) else None) for role, ours in ROLES.items()}


def wrong_roles(current: dict, wanted: dict[str, Optional[int]]) -> list[str]:
    """The roles whose place differs from the rule (a role the rule cannot fill is left as it is)."""
    return [role for role, place in wanted.items() if place is not None and current.get(role) != place]
