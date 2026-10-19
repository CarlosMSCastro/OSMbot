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
from osmbot.events.calendar import active_changes, claim_bonus_end, months_needed, parse_schedule, upcoming

FILE = Path.home() / ".osmbot" / "eventos.json"
TOPIC = 67089
FORUM = "https://forum.onlinesoccermanager.com"
CHECK_EVERY = 3600.0  # s: the game's settings and eventnotifications, per league
EARLY, EARLY_EVERY = (5 * 60 + 30, 7 * 60), 600.0  # 05:30-07:00 (local): read every 10 min, to learn when events begin
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


def check_every(now: float) -> float:
    """How often the settings are read: every 10 min from 05:30 to 07:00 (the events seem to begin at ~06:00 in
    Portugal, DISCOVERY.md; owner, 2026-10-14), every hour otherwise."""
    moment = datetime.fromtimestamp(now)
    return EARLY_EVERY if EARLY[0] <= moment.hour * 60 + moment.minute < EARLY[1] else CHECK_EVERY


def training_event_wake(events: list[dict], active: list[list[str]], now: float) -> float | None:
    """When the bot should look again for a training event that the forum's schedule puts today (owner,
    2026-10-16: finish the trainings put before it as soon as it begins): at 05:30, then every 10 min until 07:00
    or until some league shows it (``active``: each league's changes, e.g. ["treinos 120 min"]). Pure."""
    if any(change.startswith("treinos ") for changes in active for change in changes):
        return None
    for event in events:
        if "treinos" not in (event.get("tags") or []):
            continue
        day = datetime.fromtimestamp(event["start"]).replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
        opens, closes = day + EARLY[0] * 60, day + EARLY[1] * 60
        if now < opens <= now + 86400:
            return opens
        if opens <= now < closes:
            return now + EARLY_EVERY
    return None


def event_end_wake(events: list[dict], now: float) -> float | None:
    """When the bot should wake for the last half hour of an event that gives its bonus when a training is
    collected (22:30 of its last day; owner, 2026-10-19). Pure."""
    window = claim_bonus_end(events, now)
    return window[0] if window and now < window[0] <= now + 86400 else None


def training_wake(now: float | None = None) -> float | None:
    """``training_event_wake`` and ``event_end_wake`` with the schedule the bot keeps and what the leagues show now."""
    now = time.time() if now is None else now
    events = calendar_events(now, days=2)
    times = [t for t in (training_event_wake(events, list(_active.values()), now), event_end_wake(events, now)) if t]
    return min(times, default=None)


def check_league(client, league_id: int, name: str = "", settings: list[dict] | None = None, log=None,
                 now: float | None = None) -> list[str]:
    """What an event changed in this league's settings (read at most once an hour); logged when it changes.
    Also reads ``eventnotifications`` and keeps any answer, to learn what the game says during an event."""
    now = time.time() if now is None else now
    before = _last_check.get(league_id)
    if before is not None and now - before < check_every(now):
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
        since = f" (mudou entre {datetime.fromtimestamp(before):%H:%M} e {datetime.fromtimestamp(now):%H:%M})" if before else ""
        log(f"Evento no jogo ({where}): {', '.join(changes)}{since}" if changes else f"Evento no jogo ({where}): acabou, tudo normal{since}")
        logs.record("eventos", {"evento": "definições", "liga": league_id, "mudancas": changes, "leitura_anterior": before})
    _active[league_id] = changes
    status, body = client.get(f"leagues/{league_id}/eventnotifications")
    if status == 200 and body:
        logs.record("eventos", {"evento": "eventnotifications", "liga": league_id, "resposta": body})
    return changes
