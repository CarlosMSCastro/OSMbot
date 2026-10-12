"""The game's events: the forum's monthly schedule and what the game's settings show now (owner, 2026-10-12; D-038).

The schedule is a staff post on the forum (topic 67089). The forum sits behind a bot check (Anubis) that needs a
real browser, so the bot reads it with its own Firefox, hidden, and only when a month is missing: this month,
and the next one from the 25th, at most one try a day (the next month at a random hour of the day). The owner
chose this knowing it gets round that check (2026-10-12). The schedule is kept in ``~/.osmbot/eventos.json``
and a copy goes to ``logs/<machine>/eventos/`` (to read it from any PC).

The game's settings (``gamesettings``) say what an event changed once it has begun; ``eventnotifications`` is
read once an hour too (404 on a day without events; what it says during one is still to be seen).
"""
from __future__ import annotations

import json
import random
import time
from datetime import date, datetime
from pathlib import Path

from osmbot import logs
from osmbot.events.calendar import active_changes, months_needed, parse_schedule, upcoming

FILE = Path.home() / ".osmbot" / "eventos.json"
TOPIC = 67089
FORUM = "https://forum.onlinesoccermanager.com"
CHECK_EVERY = 3600.0  # s: the game's settings and eventnotifications, per league
_last_check: dict[int, float] = {}
_active: dict[int, list[str]] = {}


def _load() -> dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _save(data: dict) -> None:
    try:
        FILE.parent.mkdir(parents=True, exist_ok=True)
        FILE.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        pass


def read_forum_post(timeout: float = 90.0) -> list[str]:
    """Every post of the topic (the staff's schedule is one of them), read with the bot's Firefox, hidden."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.firefox.launch(headless=True)
        try:
            page = browser.new_page()
            page.goto(f"{FORUM}/topic/{TOPIC}", timeout=timeout * 1000)
            deadline = time.time() + timeout
            for _ in range(3):  # the bot check runs in the page and reloads it: ask again until the forum answers
                while "not a bot" in page.title().lower() and time.time() < deadline:
                    time.sleep(1)
                page.wait_for_load_state("networkidle", timeout=timeout * 1000)
                try:
                    topic = json.loads(page.evaluate(f"async () => (await fetch('/api/topic/{TOPIC}')).text()"))
                    return [post.get("content", "") for post in topic.get("posts") or []]
                except ValueError:
                    time.sleep(3)
            raise TimeoutError("o fórum não respondeu")
        finally:
            browser.close()


def _due(data: dict, today: date, now: datetime) -> list[str]:
    """The months to fetch now: missing ones, once a day; the next month only after today's random hour."""
    if data.get("tentativa") == today.isoformat():
        return []
    missing = [m for m in months_needed(today) if m not in (data.get("meses") or {})]
    this_month = f"{today.year:04d}-{today.month:02d}"
    hour = random.Random(today.isoformat()).randint(0, 23)  # a different hour each day, not a machine's pattern
    return [m for m in missing if m == this_month or now.hour >= hour]


def refresh(log=None, read=None, now: datetime | None = None) -> None:
    """Fetch the schedule if a month is missing (see the module). Never fails: a problem is logged and retried tomorrow."""
    now = now or datetime.now()
    data = _load()
    wanted = _due(data, now.date(), now)
    if not wanted:
        return
    if log is None:
        from osmbot.game.loop import _log as log
    data["tentativa"] = now.date().isoformat()
    _save(data)
    try:
        posts = (read or read_forum_post)()
        found = [c for c in map(parse_schedule, [posts] if isinstance(posts, str) else posts) if c]
        schedule = max(found, key=lambda c: c["mes"]) if found else None  # the newest schedule in the topic
    except Exception as error:
        log(f"Calendário de eventos: não consegui ler o fórum ({type(error).__name__}); tento amanhã")
        return
    if schedule is None:
        log("! Calendário de eventos: o post do fórum mudou de formato; não percebi as datas")
        return
    if schedule["mes"] not in wanted and schedule["mes"] in (data.get("meses") or {}):
        return  # still last month's post: the new one is not out yet
    data.setdefault("meses", {})[schedule["mes"]] = schedule
    _save(data)
    logs.record("eventos", {"evento": "calendário", **schedule})
    names = ", ".join(f"{e['nome']} ({e['inicio'][8:]}" + (f"–{e['fim'][8:]})" if e["fim"] != e["inicio"] else ")")
                      for e in schedule["eventos"])
    log(f"Calendário de eventos de {schedule['mes']}: {len(schedule['eventos'])} · {names}")


def calendar_events(now: float | None = None, days: int = 7) -> list[dict]:
    """The events going on now or within ``days`` (for the board's timeline)."""
    return upcoming(list((_load().get("meses") or {}).values()), time.time() if now is None else now, days)


def calendar_months() -> list[dict]:
    """Every month of the schedule the bot has, oldest first (for the window's calendar)."""
    months = _load().get("meses") or {}
    return [months[key] for key in sorted(months)]


def check_league(client, league_id: int, name: str = "", settings: list[dict] | None = None, log=None,
                 now: float | None = None) -> list[str]:
    """What an event changed in this league's settings (read at most once an hour); logged when it changes.
    Also reads ``eventnotifications`` and keeps any answer, to learn what the game says during an event."""
    now = time.time() if now is None else now
    if league_id in _last_check and now - _last_check[league_id] < CHECK_EVERY:
        return _active.get(league_id, [])
    _last_check[league_id] = now
    if settings is None:
        status, settings = client.get(f"leagues/{league_id}/gamesettings")
        settings = settings if status == 200 and isinstance(settings, list) else []
    changes = active_changes(settings)
    if changes != _active.get(league_id, []):
        if log is None:
            from osmbot.game.loop import _log as log
        where = name or str(league_id)
        log(f"Evento no jogo ({where}): {', '.join(changes)}" if changes else f"Evento no jogo ({where}): acabou, tudo normal")
        logs.record("eventos", {"evento": "definições", "liga": league_id, "mudancas": changes})
    _active[league_id] = changes
    status, body = client.get(f"leagues/{league_id}/eventnotifications")
    if status == 200 and body:
        logs.record("eventos", {"evento": "eventnotifications", "liga": league_id, "resposta": body})
    return changes
