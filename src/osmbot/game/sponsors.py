"""Sponsors (writes, owner's rule in THEORY.md section 15; request observed 2026-10-07).

Every free slot gets the offer that pays most per round. Contracts are counted in rounds, so there is
no time to wake at: the check simply happens on every pass (two reads per club).
"""
from __future__ import annotations

import time

from osmbot.game import refusals

PAUSE_BETWEEN_WRITES = 1.5  # seconds
COUNTS = {"signed": 0}
MAX_TRIES = 12  # writes per club per pass, refusals included


def _money(amount: int) -> str:
    return f"{amount / 1000:.0f}k" if amount < 1_000_000 else f"{amount / 1_000_000:.2f}M"


def sign_club(client, team: dict, base: str, confirm: bool, log=print) -> int:
    """Fill the club's free slots, best offer first. A refusal moves on to the next best. Returns the failures."""
    from osmbot.sponsors.policy import free_sides, next_choice

    refused: set[tuple[int, int]] = set()
    signed: set[int] = set()
    for _ in range(MAX_TRIES):
        _, current = client.get(f"{base}/sponsors")
        _, offers = client.get(f"{base}/sponsors/offers")
        refused |= {(side, offer["id"]) for side in free_sides(current) for offer in offers
                    if refusals.blocked(f"patrocinador:{base}:{side}:{offer['id']}")}  # refused earlier today (D-032)
        choice = next_choice(offers, current, refused)
        if choice is None:
            return 0
        side, offer = choice
        if side in signed:  # the game said yes but the slot still shows empty: do not sign it again
            log(f"{team['name']}: espaço {side} continua vazio depois de assinar; paro por agora")
            return 0
        label = (f"{team['name']}: {offer['name']} ({offer['weeks']} rondas, "
                 f"{_money(offer['sponsorRevenueForTeam'])}/ronda) no espaço {side}")
        if not confirm:
            log(f"{team['name']}: assinaria {offer['name']} ({offer['weeks']} rondas, "
                f"{_money(offer['sponsorRevenueForTeam'])}/ronda) no espaço {side}"
                f" (espaços livres: {', '.join(map(str, free_sides(current)))})")
            return 0
        status, _ = client.post(f"{base}/sponsors", {"sponsorId": offer["id"], "sponsorSide": side})
        time.sleep(PAUSE_BETWEEN_WRITES)
        if status == 200:
            COUNTS["signed"] += 1
            signed.add(side)
            log(f"Patrocinador: {label}")
        elif refusals.is_refusal(status):
            refused.add((side, offer["id"]))
            refusals.refuse(f"patrocinador:{base}:{side}:{offer['id']}", log,
                            f"Patrocinador: {label} recusado ({status}); tento o seguinte (este fica para amanhã)", day=refusals.game_day())
        else:
            log(f"Patrocinador: {label} falhou ({status})")
            return 1
    return 0


def run_sponsors(confirm: bool) -> tuple[int, list[float]]:
    """Every club. Returns (failures, times to wake at: none). Without ``confirm`` only shows the plan."""
    from osmbot.game.client import NeedsBrowserLogin, OsmClient
    from osmbot.game.trainings import _teams

    failures = 0
    try:
        client = OsmClient()
        for _, team, base in _teams(client):
            failures += sign_club(client, team, base, confirm)
    except NeedsBrowserLogin as error:
        raise SystemExit(str(error))
    return failures, []
