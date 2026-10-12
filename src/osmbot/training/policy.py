"""Who to train in each free trainer slot.

Owner's policy: train the best player of each position, except players aged
``max_age`` or more (then the best of the rest). Because the owner rotates the
whole squad through transfers, "the best player" is almost always the right one.
Goalkeepers are exempt from the age limit (owner, 2026-10-04).

Rotation (owner, 2026-10-12): training the same player again in the same round gains less, and it resets
with each match. Given how many sessions each player already had this round, the trainer goes to the
starter (onze) with the fewest, the best first; with no eligible starter, to the rest the same way.

Trainers 1-4 are position-bound (ATT, MID, DEF, GK), matching the API's
``trainer`` field as reported by third parties. The universal trainer (5) is not
handled yet: the owner has not said how to use it.
"""
from __future__ import annotations

from typing import Iterable, Mapping, Optional, Sequence

from osmbot.models import Player, Position

TRAINER_POSITION: dict[int, Position] = {
    1: Position.ATT,
    2: Position.MID,
    3: Position.DEF,
    4: Position.GK,
}


def pick_trainee(
    players: Iterable[Player],
    position: Position,
    *,
    unavailable_ids: frozenset[int] = frozenset(),
    max_age: int = 30,
    forecasts: Optional[Mapping[int, int]] = None,
    sessions: Optional[Mapping[int, int]] = None,
) -> Optional[Player]:
    """Best eligible player of ``position``, or ``None``.

    Excluded: injured, in ``unavailable_ids`` (already training / listed for
    sale), aged ``max_age`` or more, and - when ``forecasts`` is given - players
    whose server forecast is not positive (nothing left to gain).
    Best = highest rating; ties go to the higher forecast, then the lower id.
    With ``sessions`` (player id -> sessions this round): the rotation above.
    """
    candidates = []
    for p in players:
        if p.position is not position or p.injured or p.id in unavailable_ids:
            continue
        if p.age >= max_age and position is not Position.GK:  # owner: goalkeepers train regardless of age
            continue
        forecast = forecasts.get(p.id, 0) if forecasts is not None else 0
        if forecasts is not None and forecast <= 0:
            continue
        candidates.append((p.rating, forecast, -p.id, p))
    if not candidates:
        return None
    if sessions is None:
        return max(candidates, key=lambda c: c[:3])[3]
    starters = [c for c in candidates if c[3].starter]
    return max(starters or candidates, key=lambda c: (-sessions.get(c[3].id, 0), *c[:3]))[3]


def plan_training(
    players: Iterable[Player],
    free_trainers: Iterable[int],
    *,
    unavailable_ids: Iterable[int] = (),
    max_age: int = 30,
    forecasts: Optional[Mapping[int, int]] = None,
    sessions: Optional[Mapping[int, int]] = None,
) -> dict[int, Player]:
    """Map each free position-bound trainer to the player it should train.

    A player is assigned at most once. Trainers with no eligible player are
    left out of the result.
    """
    squad = list(players)
    taken = set(unavailable_ids)
    plan: dict[int, Player] = {}
    for trainer in sorted(free_trainers):
        position = TRAINER_POSITION.get(trainer)
        if position is None:
            continue
        chosen = pick_trainee(
            squad,
            position,
            unavailable_ids=frozenset(taken),
            max_age=max_age,
            forecasts=forecasts,
            sessions=sessions,
        )
        if chosen is not None:
            plan[trainer] = chosen
            taken.add(chosen.id)
    return plan


def round_sessions(ongoing: Sequence[Mapping], recorded: Mapping[str, int], week: int) -> dict[int, int]:
    """How many sessions each player had in round ``week``: the ones the bot recorded (session id -> player id)
    plus the ongoing ones of that round (the owner's included), each session counted once."""
    seen = {str(k): int(v) for k, v in recorded.items()}
    for s in ongoing:
        if s.get("weekNr") == week:
            seen.setdefault(str(s["id"]), int(s["playerId"]))
    counts: dict[int, int] = {}
    for player_id in seen.values():
        counts[player_id] = counts.get(player_id, 0) + 1
    return counts
