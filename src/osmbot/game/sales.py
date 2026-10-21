"""Players sold, per club, kept in ~/.osmbot/sales.json so a restart does not forget them (D-026)."""
from __future__ import annotations

import json
import threading
import time
from datetime import datetime
from pathlib import Path

from osmbot.board.info import purchases, sale_time, settle_sales, track_sales
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
    for buy in state.get("bought") or []:  # owner, 2026-10-22 (THEORY.md 7.5)
        times = f" ({buy['price'] / buy['value']:.2f} × o valor)".replace(".", ",") if buy.get("value") else ""
        lines.append(f"Compra: {buy['name']} ({club}) comprado por {money(buy['price'])}{times}"
                     + (f", de {buy['from']}" if buy.get("from") else ""))
    for sale in state["new_sales"]:
        took = f", demorou {span(sale['sold'] - sale['since'])}" if sale.get("since") else ""
        if sale.get("bought"):
            held = f" em {span(sale['sold'] - sale['bought_at'])}" if sale.get("bought_at") else ""
            gain = sale["price"] - sale["bought"]
            took += f"; lucro {'+' if gain >= 0 else '−'}{money(abs(gain))}{held}"
        sold = f"vendido às {_clock(sale['sold'])}" if sale.get("confirmada") else f"vendido até {_clock(sale['sold'])}"
        since = (f"à venda desde {_clock(sale.get('since'))}, " if sale.get("since") or not sale.get("confirmada")
                 else "listado de novo com o bot parado, ")  # the league's transfers had another price
        lines.append(f"Venda: {sale['name']} ({club}) vendido por {money(sale['price'])}{_of_max(sale)}; {since}{sold}{took}")
    return lines


def update(club_key: str, listed: dict[int, dict], squad: set[int], club: str = "", log=None,
           transfers=None, team_id: int | None = None) -> list[dict]:
    """Follow one club's transfer list and return its sales still to show; ``log`` gets the listings, purchases and
    sales. ``transfers``: a function that reads the league's transfers, called only when there is a sale or someone
    new in the squad (the price, time and purchase come from there, ``settle_sales`` and ``purchases``)."""
    with _LOCK:
        data = _load()
        state = track_sales(data.get(club_key) or {}, listed, squad, time.time())
        state["bought"] = []
        if (state["new_sales"] or state["new_members"]) and transfers is not None and team_id is not None:
            rows = transfers()
            settle_sales(state["new_sales"], rows, team_id)  # the same dicts as in state["sales"]
            state["bought"] = purchases(state["new_members"], rows, team_id)
        data[club_key] = {"listed": {str(k): v for k, v in state["listed"].items()}, "sales": state["sales"],
                          "squad": state["squad"]}
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


HISTORY_FOR = 3600  # seconds the sale times read from the logs are kept before reading them again
_history: dict = {}


def sale_times(now: float | None = None) -> list[tuple[float, float]]:
    """(price, seconds it took) of every sale in the repo's logs, all PCs, each sale once (THEORY.md 7.5: the
    "parado na lista" warning). Read again once an hour; empty without the repo."""
    from osmbot.logs import repo_folder

    now = now or time.time()
    if _history and now - _history["at"] < HISTORY_FOR:
        return _history["times"]
    found: dict = {}
    repo = repo_folder()
    for path in sorted((repo / "logs").glob("*/20*.log")) if repo else []:
        try:
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                if "Venda: " in line and (sale := sale_time(line)):
                    found.setdefault(sale[0], sale[1:])
        except OSError:
            continue
    _history.update(at=now, times=list(found.values()))
    return _history["times"]
