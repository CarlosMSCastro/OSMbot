"""The game's monthly events (Transfer Madness, Intense Friendlies...), owner 2026-10-12. Pure: no network, no I/O.

Two sources: the schedule the staff posts on the forum each month (``parse_schedule``, read by ``game/events.py``)
and the game's own settings, which an event changes (``active_changes``: 6 places on the transfer list, 2-hour
trainings...). The settings only show an event once it has begun; the schedule says it in advance.
"""
from __future__ import annotations

import html
import re
from datetime import date, datetime, timedelta

MONTHS = {name: number for number, name in enumerate(
    ("january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november",
     "december"), start=1)}
_HEADER = re.compile(r"events schedule:\s*([a-z]+)\s+(\d{4})", re.I)
_EVENT = re.compile(r"^(\d{1,2})(?:\s+([a-z]+))?(?:\s*-\s*(\d{1,2}))?\s+([a-z]+)\s*:\s*(.+)$", re.I)
TAGS = (  # what an event is about, from its lines (to act on it later)
    ("transferencias", ("sale chance", "transfer round")),  # sells better (not "legends added on the list")
    ("amigaveis", ("friendly",)),
    ("treinos", ("training progression", "trainers", "training timers")),
    ("estadio", ("stadium",)),
    ("olheiro", ("scout",)),
    ("analista", ("analyst",)),
    ("medico", ("doctor", "lawyer")),
    ("lendas", ("legend",)),
)
# The game's settings outside events (read 2026-10-12, a day with no event; minutes, or places on the list)
NORMAL = {"TrainingSession": 480, "TrainingUniversalSession": 360, "StadiumUpgrade": 1080, "SpyInstructionTimer": 60,
          "DoctorTreatmentTimer": 480, "LawyerCaseTimer": 480, "ScoutInstructionTimer": 960, "MaxPlayersOnTransferlist": 4}
LABELS = {"TrainingSession": "treinos", "TrainingUniversalSession": "treinador universal", "StadiumUpgrade": "estádio",
          "SpyInstructionTimer": "analista", "DoctorTreatmentTimer": "médico", "LawyerCaseTimer": "advogado",
          "ScoutInstructionTimer": "olheiro", "MaxPlayersOnTransferlist": "vagas de venda"}


def text_of(content: str) -> str:
    """A forum post (HTML) as plain lines."""
    text = re.sub(r"<br\s*/?>", "\n", content)
    text = re.sub(r"</(p|li|div|h\d|tr)>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text)


def _tags(lines: list[str]) -> list[str]:
    joined = " ".join(lines).lower()
    return [tag for tag, words in TAGS if any(word in joined for word in words)]


def parse_schedule(content: str) -> dict | None:
    """{"mes": "AAAA-MM", "eventos": [{"inicio", "fim", "nome", "efeitos", "tags"}]} from the staff's post,
    or None when the post is not a schedule (the format changed: the bot says so)."""
    lines = [line.strip() for line in text_of(content).splitlines()]
    header = next((m for m in map(_HEADER.search, lines) if m), None)
    if not header or header[1].lower() not in MONTHS:
        return None
    month, year = MONTHS[header[1].lower()], int(header[2])
    events, current = [], None
    for line in lines:
        if not line:
            continue
        found = _EVENT.match(line)
        if found and found[4].lower() in MONTHS and (found[2] is None or found[2].lower() in MONTHS):
            end_month = MONTHS[found[4].lower()]
            start_month = MONTHS[found[2].lower()] if found[2] else end_month
            start_day, end_day = int(found[1]), int(found[3] or found[1])
            if found[3] is None and found[2] is None:
                start_month = end_month
            start_year = year + (1 if start_month < month and month == 12 else 0)
            end_year = start_year + (1 if end_month < start_month else 0)
            current = {"inicio": date(start_year, start_month, start_day).isoformat(),
                       "fim": date(end_year, end_month, end_day).isoformat(), "nome": found[5].strip(), "efeitos": []}
            events.append(current)
        elif line.lower().startswith("note"):
            current = None
        elif current is not None and not _HEADER.search(line):
            current["efeitos"].append(line)
    for event in events:
        event["tags"] = _tags(event["efeitos"])
    return {"mes": f"{year:04d}-{month:02d}", "eventos": events} if events else None


def span_of(event: dict) -> tuple[float, float]:
    """Start and end of an event as timestamps: from 00:00 of the first day to 24:00 of the last [S: local time]."""
    start = datetime.fromisoformat(event["inicio"])
    end = datetime.fromisoformat(event["fim"]) + timedelta(days=1)
    return start.timestamp(), end.timestamp()


def upcoming(calendars: list[dict], now: float, days: int = 7) -> list[dict]:
    """The events going on now or starting within ``days``, soonest first, each with "start" and "end"."""
    found = []
    for calendar in calendars:
        for event in calendar.get("eventos") or []:
            start, end = span_of(event)
            if end > now and start <= now + days * 86400:
                found.append({**event, "start": start, "end": end})
    return sorted(found, key=lambda e: e["start"])


def active_changes(settings: list[dict]) -> list[str]:
    """What an event changed in the game's settings right now, e.g. ["treinos 120 min", "vagas de venda 6"]."""
    values = {g.get("name"): g.get("value") for g in settings}
    changes = []
    for name, normal in NORMAL.items():
        value = values.get(name)
        if value is not None and value != normal:
            unit = "" if name == "MaxPlayersOnTransferlist" else " min"
            changes.append(f"{LABELS[name]} {value}{unit}")
    return changes


def months_needed(today: date) -> list[str]:
    """The months whose schedule the bot should have: this one, and the next from the 25th (the staff posts it
    around the 25th-30th, DISCOVERY.md section 6b)."""
    months = [f"{today.year:04d}-{today.month:02d}"]
    if today.day >= 25:
        nxt = (today.replace(day=1) + timedelta(days=32)).replace(day=1)
        months.append(f"{nxt.year:04d}-{nxt.month:02d}")
    return months
