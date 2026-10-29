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


# The tactics' codes as the game keeps them (`teamtactics`), with the game's own words: read in the owner's clubs
# while he turned each carousel (2026-10-28, DISCOVERY.md 3); the carousels follow the codes' order
PLANS = {0: "Bola longa", 1: "Jogo de passe", 2: "Jogar pelas alas", 3: "Contra-ataque", 4: "Remate à vista"}
ATTACK = {0: "Ajudar a defender", 1: "Apoiar meio-campo", 2: "Atacar apenas"}  # forwards
MIDFIELD = {0: "Ajudar a defesa", 1: "Manter posições", 2: "Pressionar na frente"}  # midfielders
DEFENSE = {0: "Defender atrás", 1: "Defesas atacantes", 2: "Apoiar meio-campo"}  # defenders
LONG_BALL, PASSING, WINGS, COUNTER, SHOOT = 0, 1, 2, 3, 4
SUPPORT, ATTACK_ONLY = 1, 2
HELP_DEFENCE, NEUTRAL = 0, 1
DEEP = 0


@dataclass(frozen=True)
class Band:
    """A slider's band (THEORY.md 2: never out of it) and the value the owner aims at inside it."""

    low: int
    high: int
    aim: int

    def __contains__(self, value: int) -> bool:
        return self.low <= value <= self.high


@dataclass(frozen=True)
class Instructions:
    """What THEORY.md section 2 takes for a formation: each field the codes that are right, the sliders their band."""

    plan: frozenset[int]
    defense: frozenset[int]
    midfield: frozenset[int]
    attack: frozenset[int]
    marking: frozenset[bool]  # True = man-to-man, False = zonal (the game's `marking`)
    offside: frozenset[bool]
    pressing: Band
    mentality: Band  # the slider the game calls style
    tempo: Band


ONE_FORWARD = 1  # [S] his eleven with one forward (4-5-1, 4-2-3-1, 5-4-1): the author's "neutral against the 4-5-1"
DEFENSIVE_FORWARD = {8: 40, 11: 40, 4: 20}  # wingers ~40 of defence, a striker >= 20 (OSMPro, 10 videos)


def instructions(formation: int, detail: str | None, *, away: bool = False, clearly_stronger: bool = False,
                 clearly_weaker: bool = False, forwards: int | None = None,
                 defensive_forwards: bool = False) -> Instructions | None:
    """The instructions and sliders of THEORY.md section 2 (owner, 2026-10-28, D-073: "tudo como o autor"), or None
    for a formation it has no rule for. ``clearly_stronger``/``clearly_weaker``: more than 12 % apart in match
    strength (section 1); ``forwards``: how many his eleven has, once the analysis shows it (None before);
    ``defensive_forwards``: all of ours defend well enough to support the midfield."""
    def of(*codes):
        return frozenset(codes)

    attack = of(ATTACK_ONLY, SUPPORT) if defensive_forwards else of(ATTACK_ONLY)
    midfield = of(NEUTRAL) if forwards == ONE_FORWARD else of(HELP_DEFENCE)  # against the 4-5-1: neutral
    high = Band(60, 80, 75)
    five = dict(defense=of(DEEP), midfield=of(HELP_DEFENCE), marking=of(False), offside=of(False),
                mentality=Band(0, 20, 15) if clearly_weaker else Band(20, 40, 35), tempo=Band(60, 80, 75))
    if formation == 433:
        return Instructions(of(PASSING, WINGS), of(DEEP), midfield, attack, of(False),
                            of(True) if clearly_stronger else of(True, False), high, high, high)
    if formation == 532:
        return Instructions(of(COUNTER), attack=of(ATTACK_ONLY), pressing=Band(20, 40, 30), **five)
    if formation == 523:
        return Instructions(of(COUNTER), attack=of(SUPPORT) if detail == "B" else of(ATTACK_ONLY),
                            pressing=Band(20, 40, 35), **five)
    if formation == 541:
        return Instructions(of(SHOOT) if detail == "B" else of(COUNTER), attack=attack, pressing=Band(20, 40, 30),
                            **{**five, "midfield": of(NEUTRAL) if detail == "B" else of(HELP_DEFENCE)})
    if formation == 442 and detail == "B":
        return Instructions(of(PASSING), of(DEEP), of(NEUTRAL), of(SUPPORT), of(False), of(False),
                            Band(40, 60, 58), Band(60, 80, 65), Band(60, 80, 70))
    if formation == 343:
        return Instructions(of(WINGS), of(DEEP), midfield, attack, of(True) if forwards == 3 else of(False),
                            of(True), high, high, high)
    if formation == 352 and away:  # [S] the author only says offside at home
        return Instructions(of(SHOOT), of(DEEP), of(HELP_DEFENCE), of(ATTACK_ONLY, SUPPORT), of(False),
                            of(True, False), Band(20, 40, 35), Band(20, 40, 30), Band(60, 80, 70))
    if formation == 352:
        return Instructions(of(PASSING), of(DEEP), of(NEUTRAL), of(ATTACK_ONLY, SUPPORT), of(False), of(True),
                            Band(60, 80, 62), Band(40, 60, 55), Band(60, 80, 70))
    if formation == 424:  # [S] the author's experimental 4-2-4 B, only with no MO nor MDC (owner, 2026-10-29)
        return Instructions(of(LONG_BALL), of(DEEP), of(HELP_DEFENCE), of(ATTACK_ONLY), of(True), of(False),
                            Band(80, 100, 85), high, high)
    return None


def defensive(starters: list[dict]) -> bool:
    """All our forwards defend enough to support the midfield (``DEFENSIVE_FORWARD``); False with none."""
    forwards = [p for p in starters if p.get("specificPosition") in DEFENSIVE_FORWARD]
    return bool(forwards) and all((p.get("statDef") or 0) >= DEFENSIVE_FORWARD[p["specificPosition"]] for p in forwards)


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
