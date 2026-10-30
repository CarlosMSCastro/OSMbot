"""Starters whose condition is "yellow": worth resting for a game (THEORY.md section 16). Pure."""
from __future__ import annotations

YELLOW_BELOW = 80  # fitness 79 shows yellow, 80 shows green (owner, 2026-10-07)
STARTING_ELEVEN = range(1, 12)  # `lineup` 1-11 = the eleven, 12-18 = the bench, 0 = not in the squad list
POSITIONS = {1: "ATA", 2: "MED", 3: "DEF", 4: "GR"}


def tired_starters(players: list[dict]) -> list[dict]:
    """Starters (not injured) below the yellow line, most tired first: [{id, name, pos, fitness}]."""
    tired = [{"id": p["id"], "name": p["name"], "pos": POSITIONS.get(p["position"], "?"), "fitness": p["fitness"]}
             for p in players
             if p["lineup"] in STARTING_ELEVEN and not p["unavailable"] and p["fitness"] < YELLOW_BELOW]
    return sorted(tired, key=lambda p: p["fitness"])


LOW_MORALE = 80  # [S] a starter's morale below this is a warning (owner, 2026-10-28; OSMPro series point 7)


def low_morale(players: list[dict]) -> list[dict]:
    """Starters (not injured) with low morale, lowest first: [{name, morale}] (owner, 2026-10-28: rare, the owner's
    starters were below 80 in 6 of 1 445 readings; THEORY.md section 16)."""
    low = [{"name": p["name"], "morale": p["morale"]} for p in players
           if p.get("lineup") in STARTING_ELEVEN and not p.get("unavailable") and (p.get("morale") or 100) < LOW_MORALE]
    return sorted(low, key=lambda p: p["morale"])


def uncovered(players: list[dict], tired: list[dict]) -> list[str]:
    """The positions of tired starters with nobody to replace them: no other player of that position outside the
    eleven and available, whatever his condition (owner, 2026-10-13; THEORY.md section 16)."""
    cover = {POSITIONS.get(p["position"]) for p in players if p["lineup"] not in STARTING_ELEVEN and not p["unavailable"]}
    return sorted({p["pos"] for p in tired} - cover)


MATCH_DROP = 4  # [S] condition lost from one match to the next when a starter plays both (THEORY.md 16, 208 cases)
RIVAL_SHARE = 0.95  # [S] a direct rival is an important match only with at least 95 % of our strength (owner, 2026-10-29)
HARDER_BY = 0.05  # the one after must be 5 % harder to rest for it: the home advantage, and the estimates' error (owner, 2026-10-29)


def important_match(theirs: float | None, ours: float | None, rival: bool) -> bool:
    """An important match (THEORY.md 16): a stronger opponent, or a direct rival (2 places or fewer in the table) with
    at least 95 % of our strength (owner, 2026-10-29: a much weaker rival is not). Strengths as the formation rule
    counts them (with home); with one unknown, a direct rival is important, as before."""
    if not theirs or not ours:
        return rival
    return theirs > ours or (rival and theirs >= ours * RIVAL_SHARE)


def spare_for(first: dict | None, second: dict | None) -> bool:
    """Rest starters in the next match for the one after (THEORY.md 16, owner 2026-10-29): only for the harder one,
    when the one after is important and at least 5 % harder than the next (``difficulty``: the opponent's strength over
    ours, with home). With a difficulty unknown, as before: the next one not important."""
    if not first or not second or not second.get("important"):
        return False
    if first.get("difficulty") is None or second.get("difficulty") is None:
        return not first.get("important")
    return second["difficulty"] >= first["difficulty"] * (1 + HARDER_BY)


def rest_warnings(players: list[dict], first: dict | None, second: dict | None) -> list[dict]:
    """Starters still green who would reach the next important match yellow if they play the one before (owner,
    2026-10-22, THEORY.md 16). ``first``/``second``: the next two matches as {"opponent", "important", "difficulty"};
    only when ``spare_for`` them. Returns [{name, fitness, then, first, second}], most tired first."""
    if not spare_for(first, second):
        return []
    warned = [{"name": p["name"], "fitness": p["fitness"], "then": p["fitness"] - MATCH_DROP,
               "first": first["opponent"], "second": second["opponent"]}
              for p in players if p["lineup"] in STARTING_ELEVEN and not p["unavailable"]
              and YELLOW_BELOW <= p["fitness"] < YELLOW_BELOW + MATCH_DROP]
    return sorted(warned, key=lambda p: p["fitness"])
