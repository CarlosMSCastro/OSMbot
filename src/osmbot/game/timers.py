"""The game's timers for the bot's writes: which ``timerGameSettingId`` to send, and how long it lasts now.

An event puts its own entry in the league's ``gamesettings``, with another id and a shorter time, in place of the
normal one (2026-10-14, Super Staff: DoctorTreatmentTimer 48 -> 725, 480 -> 180 min). The game takes whatever id it
is sent, so a fixed id gave the normal 8 h doctor in the middle of the event (DISCOVERY.md). Looked up by name, as
the trainings always did; the normal id only when the name is not there.
"""
from __future__ import annotations

from osmbot.events.calendar import NORMAL


def timer(client, league: str, name: str, fallback: int) -> tuple[int, int]:
    """(id, minutes) of the timer ``name`` in this league now (``league`` = "leagues/{id}"). Not found or unreadable:
    the normal id ``fallback`` and the normal length."""
    status, settings = client.get(f"{league}/gamesettings")
    for g in settings if status == 200 and isinstance(settings, list) else []:
        if g.get("name") == name and isinstance(g.get("id"), int):
            return g["id"], g.get("value") or NORMAL[name]
    return fallback, NORMAL[name]


def minutes_text(value) -> str:
    """360 -> "6 h", 90 -> "1h30", 15 -> "15 min"; the time as the log says it."""
    if not isinstance(value, int) or value <= 0:
        return "?"
    hours, minutes = divmod(value, 60)
    return f"{hours} h" if not minutes else f"{hours}h{minutes:02d}" if hours else f"{minutes} min"
