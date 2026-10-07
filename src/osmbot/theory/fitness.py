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
