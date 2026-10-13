"""Specialists set by the owner's rule before each match (writes; THEORY.md section 4, D-042).

The game keeps each specialist as a place in the eleven (1-11), not a player: ``GET .../specialists`` and
``PUT .../specialists`` with ``captain``, ``penalty``, ``freekick`` and ``corners`` (form; first done 2026-10-12,
with the owner's OK: 200). In the last 4 hours before a match the bot puts right only the roles that differ from the
rule, so a change of the eleven by the owner is followed. A refused request is not repeated that day (D-032).
"""
from __future__ import annotations

from osmbot.game import refusals
from osmbot.models import Player
from osmbot.theory.specialists import ROLE_NAMES, wanted_slots, wrong_roles

COUNTS = {"set": 0}


def check(players: list[dict], current: dict | None) -> list[str]:
    """The roles out of the rule, as the card's hover says them ("Cantos: X, pela regra Y"; THEORY.md section 21).
    Pure."""
    if not current:
        return []
    wanted = wanted_slots(Player.from_api(p) for p in players)
    names = {p["lineup"]: p.get("name") for p in players if 1 <= (p.get("lineup") or 0) <= 11}
    return [f"{ROLE_NAMES[r].capitalize()}: {names.get(current.get(r), '—')}, pela regra {names.get(wanted[r], '—')}"
            for r in wrong_roles(current, wanted)]


def fix_specialists(client, team: dict, base: str, confirm: bool, log) -> int:
    """Put right the specialists that differ from the owner's rule. Returns the failures."""
    status, current = client.get(f"{base}/specialists")
    if status != 200 or not isinstance(current, dict):
        return 0
    _, players = client.get(f"{base}/players")
    wanted = wanted_slots(Player.from_api(p) for p in players)
    wrong = wrong_roles(current, wanted)
    if not wrong:
        return 0
    key = f"especialistas:{base}"
    if refusals.blocked(key, day=refusals.game_day()):
        return 0
    names = {p["lineup"]: p.get("name") for p in players if 1 <= (p.get("lineup") or 0) <= 11}
    change = ", ".join(f"{ROLE_NAMES[r]} {names.get(current.get(r), '?')} → {names.get(wanted[r], '?')}" for r in wrong)
    if not confirm:
        log(f"Simulação: especialistas de {team['name']}: {change}")
        return 0
    form = {role: wanted[role] if role in wrong else current.get(role) for role in ("captain", "corners", "freekick", "penalty")}
    status, _ = client.request("PUT", f"{base}/specialists", form)
    if status == 200:
        COUNTS["set"] += 1
        log(f"Especialistas ({team['name']}): {change}")
        return 0
    if refusals.is_refusal(status):
        refusals.refuse(key, log, f"! Especialistas ({team['name']}): o jogo recusou ({status}); volto a tentar amanhã",
                        day=refusals.game_day())
        return 0
    log(f"Especialistas ({team['name']}): falhou ({status})")
    return 1
