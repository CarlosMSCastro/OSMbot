"""Players sold, per club, kept in ~/.osmbot/sales.json so a restart does not forget them (D-026)."""
from __future__ import annotations

import json
from pathlib import Path

from osmbot.board.info import track_sales

SALES_FILE = Path.home() / ".osmbot" / "sales.json"


def _load() -> dict:
    try:
        return json.loads(SALES_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def update(club_key: str, listed: dict[int, dict], squad: set[int]) -> list[dict]:
    """Follow one club's transfer list and return its sales still to show."""
    data = _load()
    state = track_sales(data.get(club_key) or {}, listed, squad)
    data[club_key] = {"listed": {str(k): v for k, v in state["listed"].items()}, "sales": state["sales"]}
    try:
        SALES_FILE.parent.mkdir(parents=True, exist_ok=True)
        SALES_FILE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass
    return state["sales"]
