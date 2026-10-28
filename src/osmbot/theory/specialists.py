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

MIN_MATCHES = 3  # [S] an average grade counts from 3 matches (owner, 2026-10-28)
CLOSE_GRADES = 0.2  # [S] averages this close: the more defensive midfielder (owner, 2026-10-28)
PENALTY_MID_MARGIN = 10  # a midfielder this much more attack than the best forward takes the penalties (owner, 2026-10-28)


def _best(players: Iterable[Player], key) -> Optional[Player]:
    return max(players, key=key, default=None)


def pick_captain(starters: Iterable[Player]) -> Optional[Player]:
    """Oldest player, regardless of rating; on equal age, higher rating."""
    return _best(starters, lambda p: (p.age, p.rating, -p.id))


def _attack(p: Player) -> tuple:
    """Attack first; on equal attack, the better rest of the stats (owner, 2026-10-14)."""
    return (p.stat_att, p.stat_ovr + p.stat_def, p.rating, -p.id)


def pick_penalty_taker(starters: Iterable[Player]) -> Optional[Player]:
    """Forward with the highest attack stat; a midfielder instead when he has ``PENALTY_MID_MARGIN`` or more attack
    than him (OSMPro Táticas point 18, owner 2026-10-28)."""
    squad = list(starters)
    forward = _best((p for p in squad if p.position is Position.ATT), _attack)
    mid = _best((p for p in squad if p.position is Position.MID), _attack)
    if forward and mid and mid.stat_att >= forward.stat_att + PENALTY_MID_MARGIN:
        return mid
    return forward


def pick_free_kick_taker(starters: Iterable[Player]) -> Optional[Player]:
    """Any starter with the highest attack stat."""
    return _best(starters, _attack)


def pick_corner_taker(starters: Iterable[Player], free_kick: Optional[Player] = None) -> Optional[Player]:
    """Midfielder with the highest attack stat. When he also takes the free kicks (``free_kick``), another midfielder
    (OSMPro Táticas point 17, owner 2026-10-28): the best average grade among those with ``MIN_MATCHES``, and of
    averages within ``CLOSE_GRADES`` of it the more defensive; with none of them, the next by attack; with no other
    midfielder, the same one."""
    mids = [p for p in starters if p.position is Position.MID]
    first = _best(mids, _attack)
    others = [p for p in mids if free_kick is None or p.id != free_kick.id]
    if first is None or free_kick is None or first.id != free_kick.id or not others:
        return first
    graded = [p for p in others if p.matches >= MIN_MATCHES]
    if not graded:
        return _best(others, _attack)
    top = max(p.average_grade for p in graded)
    return _best((p for p in graded if p.average_grade >= top - CLOSE_GRADES - 1e-9),
                 lambda p: (p.stat_def, p.average_grade, _attack(p)))


@dataclass(frozen=True)
class Specialists:
    captain: Optional[Player]
    penalty_taker: Optional[Player]
    free_kick_taker: Optional[Player]
    corner_taker: Optional[Player]


def pick_specialists(starters: Iterable[Player]) -> Specialists:
    squad = list(starters)
    free_kick = pick_free_kick_taker(squad)
    return Specialists(
        captain=pick_captain(squad),
        penalty_taker=pick_penalty_taker(squad),
        free_kick_taker=free_kick,
        corner_taker=pick_corner_taker(squad, free_kick),
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
