"""Formation, instructions, sliders and tackling. See THEORY.md §1-3.

Slider values follow the owner's rule of never leaving the band that defines a
style; inside the band the value is a free parameter ("perto de 75").
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Formation(str, Enum):
    F433_A = "4-3-3 A"  # with an attacking midfielder (MCO)
    F433_B = "4-3-3 B"  # with a defensive midfielder (MCD)
    F532 = "5-3-2"


class PlayStyle(str, Enum):
    PASSING = "passing"
    WINGS = "wings"
    COUNTER_ATTACK = "counter-attack"


class ForwardsRole(str, Enum):
    SUPPORT_MIDFIELD = "support midfield"
    ATTACK_ONLY = "attack only"


class MidfieldRole(str, Enum):
    HOLD_POSITIONS = "hold positions"
    HELP_DEFENCE = "help defence"


class DefenceRole(str, Enum):
    DEFEND_DEEP = "defend deep"


class Referee(str, Enum):
    VERY_STRICT = "very strict"
    STRICT = "strict"
    NORMAL = "normal"
    LENIENT = "lenient"
    VERY_LENIENT = "very lenient"


class Tackling(str, Enum):
    CAREFUL = "careful"
    NORMAL = "normal"
    AGGRESSIVE = "aggressive"
    EXTREME = "extreme"


@dataclass(frozen=True)
class Slider:
    """A 0-100 slider that must stay inside ``[low, high]``."""

    value: int
    low: int
    high: int

    def __post_init__(self) -> None:
        if not self.low <= self.value <= self.high:
            raise ValueError(
                f"slider value {self.value} outside its band [{self.low}, {self.high}]"
            )


@dataclass(frozen=True)
class TacticSetup:
    formation: Formation
    offside_trap: bool
    zonal_marking: bool
    play_style: PlayStyle
    pressure: Slider
    style: Slider
    timing: Slider
    forwards: ForwardsRole
    midfield: MidfieldRole
    defence: DefenceRole


HOME_PCT = 5  # [S] home advantage measured in 272 matches (THEORY.md section 1); the pitch's own share is unknown


def match_strength(rating: float, *, boost_pct: float = 0, home: bool = False, home_pct: float = HOME_PCT) -> float:
    """The strength that counts for the formation (THEORY.md section 1, owner 2026-10-14): the team rating plus the
    game's match boosts (daily logins, camp, secret training; added up as the game shows them), times the home
    advantage for the home side."""
    return rating * (1 + boost_pct / 100) * (1 + home_pct / 100 if home else 1)


def choose_formation(my_rating: float, opp_rating: float, *, stronger_pct: float = 0) -> Formation:
    """Pick the formation from the team-rating matchup (THEORY.md section 1, owner 2026-10-14).

    - opponent stronger (by more than ``stronger_pct`` percent; 0 = any margin) -> 5 defenders (5-3-2, 5-2-3,
      5-4-1: the owner picks the one that fits the players)
    - otherwise (equal or weaker opponent)                                    -> 4-3-3 A (attacking midfielder)

    4-3-3 B is no longer a default (the owner may still try it).
    """
    if stronger_pct < 0:
        raise ValueError("stronger_pct must be >= 0")
    if opp_rating > my_rating * (1 + stronger_pct / 100):
        return Formation.F532
    return Formation.F433_A


def build_setup(formation: Formation, *, prefer_wings: bool = False) -> TacticSetup:
    """Instructions and sliders for a formation.

    ``prefer_wings`` only affects 4-3-3 (owner: wingers clearly better than the
    striker -> play down the wings, otherwise it is indifferent).
    """
    if formation is Formation.F532:
        return TacticSetup(
            formation=formation,
            offside_trap=False,
            zonal_marking=True,
            play_style=PlayStyle.COUNTER_ATTACK,
            pressure=Slider(30, 20, 40),
            style=Slider(30, 20, 40),  # "defensive" band; exact value is our assumption
            timing=Slider(75, 60, 80),
            forwards=ForwardsRole.ATTACK_ONLY,
            midfield=MidfieldRole.HELP_DEFENCE,
            defence=DefenceRole.DEFEND_DEEP,
        )
    return TacticSetup(
        formation=formation,
        offside_trap=False,
        zonal_marking=False,
        play_style=PlayStyle.WINGS if prefer_wings else PlayStyle.PASSING,
        pressure=Slider(75, 60, 80),
        style=Slider(75, 60, 80),
        timing=Slider(75, 60, 80),
        forwards=ForwardsRole.SUPPORT_MIDFIELD,
        midfield=MidfieldRole.HOLD_POSITIONS,
        defence=DefenceRole.DEFEND_DEEP,
    )


def choose_tackling(referee: Referee, *, risk_extreme: bool = False) -> Tackling:
    """Highest tackling the referee tolerates.

    Very strict -> Normal; anything looser -> Aggressive; very lenient -> Extreme.
    ``risk_extreme`` is the owner's occasional gamble: with a merely lenient
    referee, go Extreme when he needs the win against a similar squad.
    Careful is never used.
    """
    if referee is Referee.VERY_STRICT:
        return Tackling.NORMAL
    if referee is Referee.VERY_LENIENT:
        return Tackling.EXTREME
    if referee is Referee.LENIENT and risk_extreme:
        return Tackling.EXTREME
    return Tackling.AGGRESSIVE
