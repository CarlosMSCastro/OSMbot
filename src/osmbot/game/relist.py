"""Relist the owner's players whose right price went up on the list (write, owner 2026-11-03, D-085; THEORY.md 7.5).

Both requests were read in the site's code and tested once with the owner's OK (DISCOVERY.md 2026-11-03):
take off = ``DELETE leagues/{L}/teams/{T}/transferplayers/{listing id}``, list = ``PUT .../players/sell`` with the
form ``playerId`` + ``price``. Free. The rule (2 % or more) is in ``osmbot.transfers.relist``.
"""
from __future__ import annotations

import time

from osmbot.game import refusals
from osmbot.game.dashboard import money, span
from osmbot.transfers.relist import MAX_SALE_PERCENTAGE, to_relist

PAUSE_BETWEEN_WRITES = 1.5  # seconds
CHECK_EVERY = 30 * 60  # a club's list is checked for relisting at most every 30 minutes
COUNTS = {"relisted": 0}
_checked: dict[str, float] = {}


def _listings(client, base: str) -> list[dict]:
    """The owner's listings of this club, with the player's value now."""
    _, players = client.get(f"{base}/players")
    _, market = client.get(f"{base}/transferplayers/0")
    own = {p["id"]: p for p in players or []}
    found = []
    for ad in market or []:
        pid = (ad.get("player") or {}).get("id")
        if pid in own:
            found.append({"listing": ad["id"], "player": pid, "name": own[pid].get("fullName", "?"),
                          "price": ad.get("price"), "value": own[pid].get("value"), "since": ad.get("timeStampForSale")})
    return found


def _max_percentage(client, base: str) -> float:
    _, settings = client.get(f"{base.rsplit('/teams/', 1)[0]}/gamesettings")
    return next((g["value"] for g in settings or [] if g.get("name") == "MaxSalePercentage"), MAX_SALE_PERCENTAGE)


def relist_club(client, team: dict, base: str, confirm: bool, now: float, log=print) -> int:
    """One club. Returns the failures."""
    if now - _checked.get(base, 0) < CHECK_EVERY:
        return 0
    _checked[base] = now
    due = to_relist(_listings(client, base), _max_percentage(client, base))
    failures = 0
    for item in due:
        key = f"relistar:{item['player']}"
        if refusals.blocked(key, day=refusals.game_day(now)):
            continue
        gain = item["new_price"] / item["price"] - 1
        on_list = f", estava à venda há {span(now - item['since'])}" if item.get("since") else ""
        what = f"{item['name']} ({team['name']}) de {money(item['price'])} para {money(item['new_price'])} (+{gain:.0%}){on_list}"
        if not confirm:
            log(f"Relistaria {what}")
            continue
        status, _ = client.request("DELETE", f"{base}/transferplayers/{item['listing']}")
        time.sleep(PAUSE_BETWEEN_WRITES)
        if status != 200:
            if refusals.is_refusal(status):  # sold or taken off meanwhile, or the game says no: not again today
                refusals.refuse(key, log, f"! Relistar: o jogo recusou tirar {item['name']} ({team['name']}, {status}); "
                                "volto a tentar amanhã", day=refusals.game_day(now))
            else:
                log(f"Relistar: {item['name']} ({team['name']}) não saiu da lista ({status}); volto a tentar")
                failures += 1
            continue
        for attempt in range(2):  # the player is off the list now: put him back, whatever happens
            status, _ = client.request("PUT", f"{base}/players/sell", {"playerId": item["player"], "price": item["new_price"]})
            time.sleep(PAUSE_BETWEEN_WRITES)
            if status == 200:
                COUNTS["relisted"] += 1
                log(f"Relistado: {what}")
                break
        else:
            log(f"! Relistar: {item['name']} ({team['name']}) saiu da lista e o jogo não o deixou voltar ({status}); "
                "pô-lo à venda à mão")
            failures += 1
    return failures


def run_relist(confirm: bool) -> int:
    """Every club. Returns the failures. Without ``confirm`` only shows."""
    from osmbot.game.client import NeedsBrowserLogin, OsmClient
    from osmbot.game.trainings import _teams

    failures = 0
    try:
        client = OsmClient()
        for _, team, base in _teams(client, "relistar", writing=True):
            failures += relist_club(client, team, base, confirm, time.time())
    except NeedsBrowserLogin as error:
        raise SystemExit(str(error))
    return failures
