"""Requests the game refused, remembered so they are not repeated (D-032).

When the game says "no" (a 4xx answer) the bot notes the request (what, for which player or club) and does not
send it again until it makes sense: the next round (week), the next game day, a moment (the doctor is free again)
or, for the stadium, more money. The notes live in ``~/.osmbot/recusas.json``, so a restart does not start the
retries over, and they are dropped when the bot's version changes (a fixed request must never stay blocked).
A missing network, a server error or "too many requests" is not a "no": those are tried again as before.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from osmbot import __version__

FILE = Path.home() / ".osmbot" / "recusas.json"
NOT_A_NO = {401, 408, 429}  # login expired, timeout, too many requests: try again later as before


def is_refusal(status: int) -> bool:
    """The game said "no" to this request (and not "wait" or "broken")."""
    return 400 <= status < 500 and status not in NOT_A_NO


def game_day(now: float | None = None) -> str:
    """The game's day: it changes at 04:00 UTC (THEORY.md section 17)."""
    moment = datetime.fromtimestamp(time.time() if now is None else now, timezone.utc) - timedelta(hours=4)
    return f"{moment:%Y-%m-%d}"


def still_blocked(note: dict, week: int | None = None, day: str | None = None, now: float | None = None,
                  money: int | None = None) -> bool:
    """Pure: is a refusal noted like ``note`` still in force? A note holds one condition: the round it was refused
    in, the game day, a moment it lasts until, or the money there was (more money means try again)."""
    if "week" in note:
        return week is not None and note["week"] == week
    if "day" in note:
        return note["day"] == (day or game_day(now))
    if "until" in note:
        return (time.time() if now is None else now) < note["until"]
    if "money" in note:
        return money is not None and money <= note["money"]
    return False


def _load() -> dict:
    try:
        data = json.loads(FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if data.get("version") != __version__:  # a new version: every request gets a fresh chance
        return {}
    return data.get("items") or {}


def _save(items: dict) -> None:
    try:
        FILE.parent.mkdir(parents=True, exist_ok=True)
        FILE.write_text(json.dumps({"version": __version__, "items": items}, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        pass  # the bot carries on; at worst it asks again after a restart


def blocked(key: str, **current) -> bool:
    """True while the request ``key`` was refused and its condition still holds (see ``still_blocked``)."""
    note = _load().get(key)
    return bool(note) and still_blocked(note, **current)


def refuse(key: str, log=None, text: str = "", **condition) -> None:
    """Note that the game refused ``key`` (one condition: week=, day=, until= or money=) and say it once."""
    items = _load()
    if items.get(key) == condition:
        return  # already noted: said already
    items[key] = condition
    _save(items)
    if log and text:
        log(text)


def forget(key: str) -> None:
    """The request worked: drop its note."""
    items = _load()
    if items.pop(key, None) is not None:
        _save(items)
