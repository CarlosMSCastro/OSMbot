"""What the window shows, as plain data: texts with a colour name and bar fractions (D-024).

Pure functions over the same snapshot as the console board (``dashboard.collect``), so both always agree.
Colours mean the same as on the console: green = done/good, blue = time still to run (and, in a bar, the part
a video skipped), yellow = needs attention, grey = labels / nothing going on, red = errors.
"""
from __future__ import annotations

from osmbot.game.dashboard import (BAR_SECONDS, SHOP_BAR_SECONDS, SPONSOR_SLOTS, STADIUM_BAR_SECONDS, coin_jump, money,
                                   span, summary_lines, wake_events)

GREEN, BLUE, YELLOW, GREY, RED = "green", "blue", "yellow", "grey", "red"


def _money(amount: int | None) -> str:
    return "?" if amount is None else "0" if amount == 0 else money(amount)


def _done(left: float, total: float) -> float:
    """Share of a timer already gone by (0 to 1)."""
    return 1 - min(max(left, 0), total) / total


def club_view(club: dict, now: float, shortened: dict | None = None) -> dict:
    """One club's panel: title, the five fields, the stadium rows, the training rows and the tired starters."""
    shortened = shortened or {}
    fields = []
    fields.append(("Próximo jogo", span(club["match"] - now) if club.get("match") else "—", BLUE if club.get("match") else GREY))
    if club.get("slots"):
        listed, top = club["slots"]
        fields.append(("Lista de transf.", f"{listed}/{top}", YELLOW if top > listed else None))
    else:
        fields.append(("Lista de transf.", "?", GREY))
    funds, savings = club.get("money") or (None, None)
    fields.append(("Fundos", _money(funds), None if funds else GREY))
    fields.append(("Poupança", _money(savings), None if savings else GREY))
    sponsors = club.get("sponsors")
    if sponsors:
        full = sponsors["slots"] >= SPONSOR_SLOTS
        fields.append(("Patrocinadores", f"{sponsors['slots']}/{SPONSOR_SLOTS}  ·  {money(sponsors['revenue'])}/ronda",
                       GREEN if full else YELLOW))

    stadium = []
    for name, level, top, ends in (club.get("stadium") or {}).get("parts", []):
        if ends and ends > now:
            stadium.append((name, f"{level}/{top}", f"a subir · {span(ends - now)}", BLUE, _done(ends - now, STADIUM_BAR_SECONDS)))
        elif level >= top:
            stadium.append((name, f"{level}/{top}", "máximo", GREEN, None))
        else:
            stadium.append((name, f"{level}/{top}", "—", GREY, None))

    trainings = []
    for t in club.get("trainings", []):
        left = t["finish"] - now
        ready = left <= 0 and not t["claimed"]
        done = _done(left, BAR_SECONDS)
        skipped = min(done, max(shortened.get(t.get("id"), 0), 0) / BAR_SECONDS)
        trainings.append((t["name"], t["pos"], "pronto" if ready else span(left), GREEN if ready else BLUE, done, skipped))

    tired = " · ".join(f"{p['name']} {p['fitness']}%" for p in club.get("tired") or [])
    title = f"{club['name']}  —  {club.get('ranking') or '?'}.º · {club.get('league') or '?'}"
    return {"name": club["name"], "title": title, "fields": fields, "stadium": stadium, "trainings": trainings, "tired": tired}


def daily_view(daily: dict | None, now: float) -> tuple[list[tuple[str, str]], dict | None]:
    """The daily rewards as (text, colour) pieces, and the accumulated-videos row (or None)."""
    daily = daily or {}
    parts: list[tuple[str, str]] = []
    login = daily.get("login")
    if login:
        parts.append(("início de sessão por reclamar", YELLOW) if login["claimable"]
                     else (f"início de sessão ✓ (dia {login['day']})", GREEN))
    missions = daily.get("missions")
    if missions and missions["total"]:
        finished = missions["claimed"] >= missions["total"]
        parts.append((f"missões {missions['claimed']}/{missions['total']}" + (" ✓" if finished else ""), GREEN if finished else YELLOW))
        if missions["day_pending"]:
            parts.append(("prémio do dia por reclamar", YELLOW))
        else:
            parts.append(("prémio do dia ✓", GREEN) if finished else ("prémio do dia —", GREY))
    renews = (login or {}).get("renews")
    if renews and renews > now:
        parts.append((f"novo dia em {span(renews - now)}", BLUE))
    videos = daily.get("videos")
    row = None
    if videos:
        total = max(1, videos["threshold"])
        if videos["claimable"]:
            row = {"text": "por reclamar", "colour": YELLOW, "done": 1.0}
        else:
            reopen = videos.get("reopen")
            row = {"text": f"{videos['count']}/{videos['threshold']}" + (f" · reabre em {span(reopen - now)}" if reopen and reopen > now else ""),
                   "colour": None, "done": min(1.0, videos["count"] / total)}
    return parts, row


def account_view(snapshot: dict, stats: dict | None, now: float) -> dict:
    """The "Conta" box: boss coins (and what changed since the start), the shop, the daily rewards, the summary."""
    jump = coin_jump(snapshot, stats)
    coins = f"{snapshot['coins']:,}".replace(",", " ") if snapshot.get("coins") is not None else "?"
    if jump is not None:
        coins += f"  ({jump:+d} desde o arranque)"
    shop = (snapshot.get("ads") or {}).get("shop") or {}
    reopen = shop.get("reopen")
    if shop.get("open"):
        shop_row = {"text": "vídeos disponíveis", "colour": GREEN, "done": 1.0}
    elif reopen and reopen > now:
        shop_row = {"text": f"reabre em {span(reopen - now)}", "colour": BLUE, "done": _done(reopen - now, SHOP_BAR_SECONDS)}
    else:
        shop_row = {"text": "—", "colour": GREY, "done": None}
    daily, videos = daily_view(snapshot.get("daily"), now)
    summary = _summary(snapshot, stats, now)
    return {"coins": coins, "shop": shop_row, "daily": daily, "videos": videos, "summary": summary or "—"}


def _summary(snapshot: dict, stats: dict | None, now: float) -> str:
    """The run's totals in one line: "0h38 · vídeos: loja 9 · ... · recompensas: ..." (the coins have their own field)."""
    lines = summary_lines(snapshot, stats, now, full=True)
    if not lines:
        return ""
    head = lines[0]
    run_time = head[head.find("(") + 1:head.find(")")] if "(" in head else ""
    return " · ".join(part for part in (run_time, *(line.strip() for line in lines[1:])) if part)


def next_check(snapshot: dict | None, now: float) -> str:
    """The status-bar line: what the bot is waiting for, soonest first."""
    events = wake_events(snapshot, now)
    if not events:
        return ""
    return "Próxima verificação: " + " · ".join(f"{label} em {span(ts - now)}" for label, ts in events)


def board_view(snapshot: dict | None, stats: dict | None, now: float) -> dict | None:
    """Everything the window shows for one moment (None while there is nothing read yet)."""
    if not snapshot:
        return None
    shortened = (stats or {}).get("shortened") or {}
    return {"clubs": [club_view(c, now, shortened) for c in snapshot["clubs"]],
            "account": account_view(snapshot, stats, now), "next": next_check(snapshot, now)}
