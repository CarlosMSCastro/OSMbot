"""What the window shows, as plain data: texts with a colour name and bar fractions (D-024, card layout D-026).

Pure functions over the same snapshot as the console board (``dashboard.collect``), so both always agree.
Colours mean the same as on the console: green = done/good, blue = time still to run (and, in a bar, the part
a video skipped), yellow = needs attention, grey = labels / nothing going on, red = errors.
"""
from __future__ import annotations

from datetime import datetime

from osmbot.board.timeline import future_view, past_view
from osmbot.game.ads import MAX_PER_BURST, MAX_TRAINING_VIDEOS, VIDEO_SAVES
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


CASE_SECONDS = 8 * 3600  # doctor and lawyer: 480 min (DISCOVERY.md section 3)


def stadium_rings(stadium: dict | None, now: float) -> list[dict]:
    """The stadium as small rings (D-030, owner 2026-10-09): the part going up fills in the accent colour with the
    time left; the others stand still in grey with their level (green when at the top)."""
    rings = []
    lengths = (stadium or {}).get("lengths") or {}
    for name, level, top, ends in (stadium or {}).get("parts", []):
        if ends and ends > now:
            length = lengths.get(name)
            rings.append({"name": name, "level": f"{level}/{top}", "state": "moving", "left": span(ends - now),
                          "done": _done(ends - now, length) if length else 0.0})
        else:
            rings.append({"name": name, "level": f"{level}/{top}", "state": "top" if level >= top else "still",
                          "left": "no máximo" if level >= top else "parado", "done": level / top if top else 0.0})
    return rings


def care_ring(label: str, people: list[dict], now: float, lawyer: bool = False) -> dict:
    """The doctor or the lawyer as one ring: nobody · working on someone (time left) · done, to collect · someone
    waiting · (lawyer) a 1-game suspension, which the lawyer cannot take (owner, 2026-10-09)."""
    if not people:
        return {"label": label, "state": "none", "centre": "—", "name": "ninguém", "sub": "", "done": 0.0}
    first = next((p for p in people if p.get("until") or p.get("ready")), people[0])
    name = first["name"] + (f" +{len(people) - 1}" if len(people) > 1 else "")
    games = f"{first['games']} jogo{'s' if first['games'] != 1 else ''}"
    if first.get("ready"):
        return {"label": label, "state": "ready", "centre": "pronto", "name": name, "sub": "a levantar", "done": 1.0}
    if first.get("until") and first["until"] > now:
        return {"label": label, "state": "working", "centre": span(first["until"] - now), "name": name, "sub": games,
                "done": _done(first["until"] - now, CASE_SECONDS)}
    if lawyer and first["games"] < 2:
        return {"label": label, "state": "blocked", "centre": "1 j", "name": name, "sub": "1 jogo · não dá", "done": 0.0}
    return {"label": label, "state": "waiting", "centre": f"{first['games']} j", "name": name, "sub": f"{games} · à espera",
            "done": 0.0}


TOP_PLACES, BOTTOM_PLACES = 2, 3  # squad value: 1st-2nd green, the last 3 red, yellow in between (owner, 2026-10-10)


def squad_view(value: tuple | None) -> dict:
    """The squad value: the place by value in colour, the total in white; players and average on hover."""
    if not value:
        return {"place": "", "colour": GREY, "total": "—", "tip": ""}
    place, total, average, *more = value  # (place, total, average, players, teams); older readings had only 3
    players, teams = more if more else (round(total / average) if average else 0, 0)
    colour = GREEN if place <= TOP_PLACES else RED if teams and place > teams - BOTTOM_PLACES else YELLOW
    return {"place": f"{place}.º", "colour": colour, "total": money(total),
            "tip": f"{players} jogadores · média {money(round(average))}"}


def sponsor_view(sponsors: dict | None) -> dict:
    """Only the money per round; with an empty slot, ⚠ and the empty slots said on hover (owner, 2026-10-10)."""
    if not sponsors:
        return {"text": "—", "colour": GREY, "tip": ""}
    empty = SPONSOR_SLOTS - sponsors["slots"]
    text = f"{money(sponsors['revenue'])}/ronda"
    if empty <= 0:
        return {"text": text, "colour": GREEN, "tip": ""}
    plural = "s" if empty > 1 else ""
    return {"text": f"⚠ {text}", "colour": YELLOW, "tip": f"{empty} vaga{plural} vazia{plural} nos patrocinadores"}


def club_view(club: dict, now: float, shortened: dict | None = None) -> dict:
    """One club's card (D-026): header, Liga · Taça · Valor do plantel, money and sales, sponsors, stadium,
    pre-match checklist, trainings, tired starters, injured and suspended players."""
    shortened = shortened or {}
    subtitle: list[tuple[str, str | None]] = []
    nxt = club.get("next")
    rank = f" ({nxt['rank']}.º)" if nxt and nxt.get("rank") else ""
    when = f" · em {span(club['match'] - now)}" if club.get("match") else ""
    if nxt:
        if nxt["danger"]:
            subtitle.append(("⚠ confronto direto · ", YELLOW))
        subtitle.append((f"vs {nxt['opponent']}{rank} ({nxt['side']})" + (" · taça" if nxt["cup"] else "") + when,
                         YELLOW if nxt["danger"] else None))
    else:
        subtitle.append((f"{club.get('league') or ''}{when}".strip(" ·"), GREY))

    cup, state = club.get("cup") or ("—", "none")
    facts = [("Liga", f"{club.get('ranking') or '?'}.º", None),
             ("Taça", cup, {"out": GREY, "won": GREEN, "none": GREY}.get(state))]

    free = club.get("free_slots") or 0
    alert = f"{free} vaga{'s' if free > 1 else ''} livre{'s' if free > 1 else ''} na lista de transferências" if free else ""
    funds, savings = club.get("money") or (None, None)
    total = None if funds is None else funds + (savings or 0)
    sales = [f"✓ {s['name']} vendido · +{money(s['price'])}" for s in club.get("sales") or []]

    sponsors = club.get("sponsors")
    sponsor_row = sponsor_view(sponsors)

    still, moving = [], []
    lengths = (club.get("stadium") or {}).get("lengths") or {}
    for name, level, top, ends in (club.get("stadium") or {}).get("parts", []):
        if ends and ends > now:
            length = lengths.get(name)
            moving.append({"text": f"{name} {level}/{top}", "left": span(ends - now),
                           "done": _done(ends - now, length) if length else None})
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

    trainings = []
    for t in club.get("trainings", []):
        left = t["finish"] - now
        ready = left <= 0 and not t["claimed"]
        done = _done(left, BAR_SECONDS)
        skipped = min(done, max(shortened.get(t.get("id"), 0), 0) / BAR_SECONDS)
        trainings.append((t["name"], t["pos"], "pronto" if ready else span(left), GREEN if ready else BLUE, done, skipped))

    match = None  # the stripe of the next match (D-030), in the club's colour
    if nxt:
        match = {"text": f"vs {nxt['opponent']}{rank}",
                 "tag": ("CASA" if nxt["side"] == "H" else "FORA") + (" · TAÇA" if nxt["cup"] else ""), "danger": nxt["danger"], "left": span(club["match"] - now) if club.get("match") else ""}
    header = f"{club.get('ranking') or '?'}.º Campeonato"  # and the cup on a line of its own (owner, 2026-10-09)
    cup_line = cup[:1].upper() + cup[1:]
    done_steps = sum(1 for _, done, _ in prep.get("steps") or [] if done)
    prep_title = f"PRÉ-JOGO · {done_steps}/{len(prep.get('steps') or [])}" if prep.get("steps") else "PRÉ-JOGO"

    return {"name": club["name"], "logo": club.get("logo"), "logo_key": club.get("logo_key") or club["name"],
            "subtitle": subtitle, "facts": facts, "alert": alert, "header": header, "cup_line": cup_line, "match": match, "prep_title": prep_title,
            "money": _money(total), "sales": sales, "sponsors": sponsor_row, "squad": squad_view(club.get("value")),
            "stadium": {"still": still, "moving": moving},
            "prep": {"steps": steps},
            "trainings": trainings,
            "tired": " · ".join(f"{p['name']} {p['fitness']}%" for p in club.get("tired") or []),
            "injured": _people(club.get("injured") or [], "no médico", now),
            "suspended": _people(club.get("suspended") or [], "no advogado", now),
            "stadium_rings": stadium_rings(club.get("stadium"), now),
            "care": [care_ring("Médico", club.get("injured") or [], now),
                     care_ring("Advogado", club.get("suspended") or [], now, lawyer=True)]}


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


def _training_video(snapshot: dict, now: float, current: int | None = None) -> str | None:
    """The training the next -2h video goes to, as the bot picks it (``ads.pick_session``): the most time left,
    2 h at least. ``current``: the session getting a video right now (it will have 2 h less)."""
    best = None
    for club in snapshot["clubs"]:
        for t in club.get("trainings") or []:
            left = t["finish"] - now - (VIDEO_SAVES if current is not None and t.get("id") == current else 0)
            if not t["claimed"] and left >= VIDEO_SAVES and (best is None or left > best[0]):
                best = (left, t["name"], club["name"])
    return f"vídeo de treino {best[1]} ({best[2]})" if best else None


def _video(kind: str, snapshot: dict, now: float) -> str | None:
    if not ((snapshot.get("ads") or {}).get(kind) or {}).get("open"):
        return None
    if kind == "shop":
        return f"vídeo da loja 1/{MAX_PER_BURST}"
    if kind == "training":
        return _training_video(snapshot, now)
    savings = {c["name"]: (c.get("money") or (0, 0))[1] or 0 for c in snapshot["clubs"]}
    return f"vídeo de dinheiro ({max(savings, key=savings.get)})" if savings else None


def _waited_for(snapshot: dict, now: float) -> str:
    """The next thing the bot waits for, by name: "recolher treino Fulano (Clube) às 15:51"."""
    events = wake_events(snapshot, now)
    if not events:
        return ""
    label, ts = events[0]
    if label in ("treino acaba", "treino por recolher"):
        found = next(((t["name"], c["name"]) for c in snapshot["clubs"] for t in c.get("trainings") or []
                      if not t["claimed"] and (t["finish"] == ts or (label == "treino por recolher" and t["finish"] <= now))), None)
        if found:
            label = f"recolher treino {found[0]} ({found[1]})"
    return label if ts <= now else f"{label} às {datetime.fromtimestamp(ts):%H:%M}"


def doing_view(snapshot: dict | None, doing: dict | None, now: float) -> str:
    """The status bar while the bot works: "agora: vídeo da loja 8/9 · a seguir: vídeo de treino Fulano (Clube)"
    (owner, 2026-10-09: one thing each, in the singular). "A seguir" is the next step the bot will take, worked out
    from the last reading of the game: more of the same video, the next kind of video that is open (shop, training,
    money, in the bot's order), or, with nothing left, the next thing it waits for."""
    if not doing or not snapshot:
        return ""
    kind, count = doing.get("kind"), doing.get("count") or 0
    following = None
    if kind == "shop" and count < MAX_PER_BURST and ((snapshot.get("ads") or {}).get("shop") or {}).get("open"):
        following = f"vídeo da loja {count + 1}/{MAX_PER_BURST}"
    elif kind == "training" and count < MAX_TRAINING_VIDEOS and ((snapshot.get("ads") or {}).get("training") or {}).get("open"):
        following = _training_video(snapshot, now, doing.get("session"))
    if following is None and doing.get("text") != "à espera":
        order = ("shop", "training", "money")
        for later in order[order.index(kind) + 1:] if kind in order else order:
            following = _video(later, snapshot, now)
            if following:
                break
    following = following or _waited_for(snapshot, now)
    return f"agora: {doing['text']}" + (f" · a seguir: {following}" if following else "")


def board_view(snapshot: dict | None, stats: dict | None, now: float, doing: dict | None = None,
               history: list[dict] | None = None) -> dict | None:
    """Everything the window shows for one moment (None while there is nothing read yet)."""
    if not snapshot:
        return None
    shortened = (stats or {}).get("shortened") or {}
    daily, _ = daily_view(snapshot.get("daily"), now)
    return {"clubs": [club_view(c, now, shortened) for c in snapshot["clubs"]],
            "account": account_view(snapshot, stats, now), "next": next_check(snapshot, now),
            "doing": doing_view(snapshot, doing, now),
            "daily": [piece for piece in daily if not piece[0].startswith("novo dia")],  # the new day is on the timeline
            "timeline": {"future": future_view(snapshot, now), "past": past_view(history or []),
                         "now": (doing or {}).get("text") or ""}}
