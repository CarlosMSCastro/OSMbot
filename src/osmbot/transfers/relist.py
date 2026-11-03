"""Relist a player whose right price went up while on the list (owner, 2026-11-03, D-085; THEORY.md 7.5). Pure.

A player who rises a rating on the list is worth ~7 % more, but the game keeps the old asking price. The right
price now is what the owner asks when listing: the game's maximum (``MaxSalePercentage`` of the value, 250 %),
or 75 % of it above 150 M. When that is at least 2 % above the listed price, the bot takes the player off the list
and lists him again at it. Smaller differences are the value's daily drift (~0.5 %), not an evolution.
"""
from __future__ import annotations

from osmbot.transfers.engine import BIG_SALE, BIG_SALE_SHARE

RELIST_GAIN = 0.02  # relist when the right price is at least 2 % above the listed one (owner, 2026-11-03)
MAX_SALE_PERCENTAGE = 250  # the game setting MaxSalePercentage when it cannot be read (DISCOVERY.md 2026-11-03)


def right_price(value: float, max_percentage: float = MAX_SALE_PERCENTAGE) -> int:
    """What the owner asks for a player of this value now: the site's maximum, round(value × % / 100), or 75 % of it
    above 150 M."""
    top = round(value * max_percentage / 100)
    return round(BIG_SALE_SHARE * top) if top > BIG_SALE else top


def to_relist(listings: list[dict], max_percentage: float = MAX_SALE_PERCENTAGE) -> list[dict]:
    """``listings``: the owner's listings [{"listing", "player", "name", "price", "value", "since"}]. Returns those
    to relist, each with "new_price", biggest gain first. A price that would go down (a player who crossed 150 M
    and would now go at 75 %) is left alone."""
    due = []
    for item in listings:
        if not item.get("value") or not item.get("price"):
            continue
        new = right_price(item["value"], max_percentage)
        if new >= item["price"] * (1 + RELIST_GAIN):
            due.append({**item, "new_price": new})
    return sorted(due, key=lambda d: d["price"] - d["new_price"])
