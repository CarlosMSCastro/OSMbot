"""Deposit the club's funds into savings just before each match (write, owner's rule in THEORY.md section 13;
the request was observed on 2026-10-07 and is the one the stadium already uses, DISCOVERY.md section 3).

The same empty PUT moves everything to the other side, so when money is split between funds and savings the
first PUT may bring savings out: then a second one puts it all in. The reply says where the money is.
"""
from __future__ import annotations

import time

from osmbot.game import refusals
from osmbot.game.prematch import _match_time
from osmbot.savings.policy import deposit_due, wake_at

PAUSE_BETWEEN_WRITES = 1.5  # seconds
COUNTS = {"deposits": 0}


def _millions(amount: int) -> str:
    return f"{amount / 1e6:.1f} M".replace(".", ",")


def deposit_club(client, team: dict, base: str, confirm: bool, now: float, log=print) -> tuple[int, float | None]:
    """One club: deposit if its match is 15 minutes away or less. Returns (failures, time to wake at)."""
    match = _match_time(client, base)
    if not deposit_due(match, now):
        return 0, wake_at(match, now)
    _, money = client.get(f"{base}/finances/balanceandsavings")
    balance = money["balance"]
    if balance <= 0:
        return 0, None
    key = f"poupança:{base}"
    if refusals.blocked(key, day=refusals.game_day(now)):
        return 0, None
    if not confirm:
        log(f"{team['name']}: depositaria {_millions(balance)} na poupança antes do jogo")
        return 0, None
    for attempt in range(2):
        status, reply = client.put(f"{base}/savings/transfer")
        time.sleep(PAUSE_BETWEEN_WRITES)
        if status != 200 or not isinstance(reply, dict):
            if refusals.is_refusal(status):
                refusals.refuse(key, log, f"! Poupança: o jogo recusou o depósito ({team['name']}, {status}); "
                                "volto a tentar no próximo dia de jogo", day=refusals.game_day(now))
                return 0, None
            warn = "! " if attempt else ""  # after a first PUT that brought savings out, the money may be in the funds now
            log(f"{warn}Poupança: {team['name']} depósito falhou ({status})")
            return 1, None
        if reply.get("balance") == 0:
            COUNTS["deposits"] += 1
            log(f"Poupança: {team['name']} depositou {_millions(balance)} antes do jogo (poupança {_millions(reply.get('savings', 0))})")
            return 0, None
    log(f"! Poupança: {team['name']} o dinheiro não ficou todo na poupança")
    return 1, None


def run_savings(confirm: bool) -> tuple[int, list[float]]:
    """Every club. Returns (failures, times to wake at: 5 minutes before each match). Without ``confirm`` only shows."""
    from osmbot.game.client import NeedsBrowserLogin, OsmClient
    from osmbot.game.trainings import _teams

    failures, wake = 0, []
    try:
        client = OsmClient()
        for _, team, base in _teams(client):
            failed, at = deposit_club(client, team, base, confirm, time.time())
            failures += failed
            if at:
                wake.append(at)
    except NeedsBrowserLogin as error:
        raise SystemExit(str(error))
    return failures, wake
