"""The league transfers kept for the price study (D-029, PROJECT_BRIEF 13). Pure: no network, no files."""
from __future__ import annotations


def due(saved: dict | None, today: str) -> bool:
    """True when the league was not read yet today (one read per day is enough)."""
    return not saved or saved.get("lido") != today


def merge(saved: dict | None, league: dict, rows: list[dict], today: str) -> tuple[dict, int]:
    """The saved file plus the transfers just read, each one once (by id), oldest first. Returns (file, new ones)."""
    known = {row["id"]: row for row in (saved or {}).get("transferencias", [])}
    new = [row for row in rows if row["id"] not in known]
    known.update({row["id"]: row for row in rows})
    every = sorted(known.values(), key=lambda row: (row.get("timestamp", 0), row["id"]))
    return {"liga": league["id"], "nome": league.get("name", ""), "lido": today, "transferencias": every}, len(new)
