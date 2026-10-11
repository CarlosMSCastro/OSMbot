"""Players sold, per club, kept in ~/.osmbot/sales.json so a restart does not forget them (D-026)."""
from __future__ import annotations

import json
import threading
import time
from datetime import datetime
from pathlib import Path

from osmbot.board.info import track_sales
from osmbot.game.dashboard import money, span

SALES_FILE = Path.home() / ".osmbot" / "sales.json"
_LOCK = threading.Lock()  # clubs are read side by side, by the bot and the window: one read-and-write at a time


def _load() -> dict:
    try:
        return json.loads(SALES_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


MAX_PRICE = 2.5  # the game's maximum asking price is ~2.5 × the player's value (THEORY.md 7.5)


def _clock(ts: float | None) -> str:
    return f"{datetime.fromtimestamp(ts):%d/%m %H:%M}" if ts else "antes de o bot começar a seguir"


def _of_max(item: dict) -> str:
    value = item.get("value") or 0
    return f" ({item['price'] / (MAX_PRICE * value):.0%} do máximo ≈ {money(round(MAX_PRICE * value))})" if value else ""


def describe(club: str, state: dict) -> list[str]:
    """The log lines for what changed on the list (owner, 2026-10-10: the times in the log too)."""
    lines = [f"Lista de transferências: {item['name']} ({club}) à venda por {money(item['price'])}{_of_max(item)}"
             for item in state["new_listings"]]
    for sale in state["new_sales"]:
        took = f", demorou {span(sale['sold'] - sale['since'])}" if sale.get("since") else ""
        lines.append(f"Venda: {sale['name']} ({club}) vendido por {money(sale['price'])}{_of_max(sale)}; "
                     f"à venda desde {_clock(sale.get('since'))}, vendido até {_clock(sale['sold'])}{took}")
    return lines


def update(club_key: str, listed: dict[int, dict], squad: set[int], club: str = "", log=None) -> list[dict]:
    """Follow one club's transfer list and return its sales still to show; ``log`` gets the listings and sales."""
    with _LOCK:
        data = _load()
        state = track_sales(data.get(club_key) or {}, listed, squad, time.time())
        data[club_key] = {"listed": {str(k): v for k, v in state["listed"].items()}, "sales": state["sales"]}
        try:
            SALES_FILE.parent.mkdir(parents=True, exist_ok=True)
            SALES_FILE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass
    if log is None:
        from osmbot.game.loop import _log as log  # the bot's log: ~/.osmbot/bot.log and the repo (D-022)
    for line in describe(club, state):
        log(line)
    return state["sales"]
