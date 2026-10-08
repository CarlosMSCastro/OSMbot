"""What the window shows, as plain data: texts with a colour name and bar fractions (D-024, card layout D-026).

Pure functions over the same snapshot as the console board (``dashboard.collect``), so both always agree.
Colours mean the same as on the console: green = done/good, blue = time still to run (and, in a bar, the part
a video skipped), yellow = needs attention, grey = labels / nothing going on, red = errors.
"""
from __future__ import annotations

from osmbot.game.dashboard import BAR_SECONDS, SPONSOR_SLOTS, coin_jump, money, span, wake_events

GREEN, BLUE, YELLOW, GREY, RED = "green", "blue", "yellow", "grey", "red"


def _money(amount: int | None) -> str:
    return "?" if amount is None else "0" if amount == 0 else money(amount)


def _done(left: float, total: float) -> float:
    """Share of a timer already gone by (0 to 1)."""
    return 1 - min(max(left, 0), total) / total


def _people(people: list[dict], place: str, now: float) -> list[tuple[str, str | None]]:
    """Injured or suspended players as coloured pieces: "Fulano (6 jogos)" and, if applicable, "-> no médico, 7h58"."""
    pieces: list[tuple[str, str | None]] = []
    for index, p in enumerate(people):
        if index:
            pieces.append((" · ", GREY))
        pieces.append((f"{p['name']} ({p['games']} jogos)", YELLOW))
        if p.get("ready"):
            pieces.append((f" → {place} acabou, a levantar", GREEN))
        elif p.get("until"):
            pieces.append((f" → {place} · acaba em {span(p['until'] - now)}", BLUE))
    return pieces or [("0", GREY)]


def club_view(club: dict, now: float, shortened: dict | None = None) -> dict:
    """One club's card (D-026): header, Liga · Taça · Valor do plantel, money and sales, sponsors, stadium,
    pre-match checklist, trainings, tired starters, injured and suspended players."""
    shortened = shortened or {}
    subtitle: list[tuple[str, str | None]] = []
    nxt = club.get("next")
    when = f" · em {span(club['match'] - now)}" if club.get("match") else ""
    if nxt:
        if nxt["danger"]:
            subtitle.append(("⚠ confronto direto · ", YELLOW))
        rank = f" ({nxt['rank']}.º)" if nxt.get("rank") else ""
        subtitle.append((f"vs {nxt['opponent']}{rank} ({nxt['side']})" + (" · taça" if nxt["cup"] else "") + when,
                         YELLOW if nxt["danger"] else None))
    else:
        subtitle.append((f"{club.get('league') or ''}{when}".strip(" ·"), GREY))

    cup, state = club.get("cup") or ("—", "none")
    value = club.get("value")
    facts = [("Liga", f"{club.get('ranking') or '?'}.º", None),
             ("Taça", cup, {"out": GREY, "won": GREEN, "none": GREY}.get(state)),
             ("Valor do plantel", f"{value[0]}.º · {money(value[1])} · média {money(round(value[2]))}" if value else "—",
              None if value else GREY)]

    free = club.get("free_slots") or 0
    alert = f"{free} vaga{'s' if free > 1 else ''} livre{'s' if free > 1 else ''} na lista de transferências" if free else ""
    funds, savings = club.get("money") or (None, None)
    total = None if funds is None else funds + (savings or 0)
    sales = [f"✓ {s['name']} vendido · +{money(s['price'])}" for s in club.get("sales") or []]

    sponsors = club.get("sponsors")
    sponsor_row = ((f"{sponsors['slots']}/{SPONSOR_SLOTS} · {money(sponsors['revenue'])}/ronda",
                    GREEN if sponsors["slots"] >= SPONSOR_SLOTS else YELLOW) if sponsors else ("—", GREY))

    still, moving = [], []
    for name, level, top, ends in (club.get("stadium") or {}).get("parts", []):
        if ends and ends > now:
            moving.append((f"{name} {level}/{top} · a subir, acaba em {span(ends - now)}", BLUE))
        else:
            still.append((f"{name} {level}/{top}", GREEN if level >= top else None))

    prep = club.get("prep") or {}
    steps = []
    for name, done, analyst in prep.get("steps") or []:
        if done:
            steps.append((f"✓ {name}", GREEN))
        elif analyst and analyst > now:
            steps.append((f"⏳ {name} {span(analyst - now)}", BLUE))
        elif analyst:
            steps.append((f"◉ {name} por levantar", YELLOW))
        else:
            steps.append((f"○ {name}", GREY))
    pct = prep.get("pct")

    trainings = []
    for t in club.get("trainings", []):
        left = t["finish"] - now
        ready = left <= 0 and not t["claimed"]
        done = _done(left, BAR_SECONDS)
        skipped = min(done, max(shortened.get(t.get("id"), 0), 0) / BAR_SECONDS)
        trainings.append((t["name"], t["pos"], "pronto" if ready else span(left), GREEN if ready else BLUE, done, skipped))

    return {"name": club["name"], "logo": club.get("logo"), "logo_key": club.get("logo_key") or club["name"],
            "subtitle": subtitle, "facts": facts, "alert": alert,
            "money": _money(total), "sales": sales, "sponsors": sponsor_row,
            "stadium": {"still": still, "moving": moving},
            "prep": {"pct": f"{pct}%" if pct is not None else "", "colour": GREEN if pct == 100 else YELLOW, "steps": steps},
            "trainings": trainings,
            "tired": " · ".join(f"{p['name']} {p['fitness']}%" for p in club.get("tired") or []),
            "injured": _people(club.get("injured") or [], "no médico", now),
            "suspended": _people(club.get("suspended") or [], "no advogado", now)}


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


def _timer_row(label: str, info: dict | None, open_text: str, now: float) -> tuple[str, str, str]:
    info = info or {}
    reopen = info.get("reopen")
    if info.get("open"):
        return label, f"● {open_text}", GREEN
    if reopen and reopen > now:
        return label, f"◷ em {span(reopen - now)}", BLUE
    return label, "—", GREY


def account_view(snapshot: dict, stats: dict | None, now: float) -> dict:
    """The bottom panel: boss coins (and the gain since the bot started) and the timers of the account."""
    jump = coin_jump(snapshot, stats)
    coins = f"{snapshot['coins']:,}".replace(",", " ") if snapshot.get("coins") is not None else "?"
    ads = snapshot.get("ads") or {}
    daily, videos = daily_view(snapshot.get("daily"), now)
    cumulative = (videos["text"], YELLOW if videos["colour"] == YELLOW else None) if videos else ("—", GREY)
    timers = [_timer_row("Vídeos da loja", ads.get("shop"), "disponíveis", now),
              _timer_row("Acelerar treinos", ads.get("training"), "disponível", now),
              _timer_row("Vídeos de dinheiro", ads.get("money"), "disponíveis", now),
              ("Reward cumulativo", *cumulative)]
    return {"coins": coins, "jump": f"{jump:+d}" if jump is not None else "", "timers": timers, "daily": daily,
            "since": f"desde que o bot foi ligado ({span(now - stats['start'])})" if stats and stats.get("start") else ""}


def next_check(snapshot: dict | None, now: float) -> str:
    """The status bar: only the next thing the bot waits for."""
    events = wake_events(snapshot, now)
    if not events:
        return ""
    label, ts = events[0]
    return f"próximo: {label} em {span(ts - now)}"


def board_view(snapshot: dict | None, stats: dict | None, now: float) -> dict | None:
    """Everything the window shows for one moment (None while there is nothing read yet)."""
    if not snapshot:
        return None
    shortened = (stats or {}).get("shortened") or {}
    return {"clubs": [club_view(c, now, shortened) for c in snapshot["clubs"]],
            "account": account_view(snapshot, stats, now), "next": next_check(snapshot, now)}
