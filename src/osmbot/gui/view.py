"""What the window shows, as plain data: texts with a colour name and bar fractions (D-024, card layout D-026).

Pure functions over the same snapshot as the console board (``dashboard.collect``), so both always agree.
Colours mean the same as on the console: green = done/good, blue = time still to run (and, in a bar, the part
a video skipped), yellow = needs attention, grey = labels / nothing going on, red = errors.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

from osmbot.board.timeline import future_view, past_view
from osmbot.events.calendar import effect_text, span_of
from osmbot.game.ads import MAX_PER_BURST, MAX_TRAINING_VIDEOS, VIDEO_SAVES
from osmbot.game.dashboard import BAR_SECONDS, SPONSOR_SLOTS, coin_jump, money, span, wake_events
from osmbot.inventory.policy import WARN_BEFORE
from osmbot.rewards.texts import amount, mission_text, prize_text

GREEN, BLUE, YELLOW, GREY, RED, ORANGE = "green", "blue", "yellow", "grey", "red", "orange"


def _say(lang: str, pt: str, en: str) -> str:
    """The hover texts made here from the game's own words (the window's ``tr`` only knows fixed Portuguese texts)."""
    return pt if lang == "pt" else en


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


CASE_SECONDS = 8 * 3600  # doctor and lawyer: 480 min (DISCOVERY.md section 3); when the case has no length


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
    count = first["games"]  # games out: shown as the number by the cross / the red card (owner, 2026-10-10)
    if first.get("ready"):
        return {"label": label, "state": "ready", "centre": "pronto", "name": name, "sub": "a levantar", "done": 1.0,
                "games": count}
    if first.get("until") and first["until"] > now:
        return {"label": label, "state": "working", "centre": span(first["until"] - now), "name": name, "sub": games,
                "done": _done(first["until"] - now, first.get("length") or CASE_SECONDS), "games": count}
    if lawyer and count < 2:
        return {"label": label, "state": "blocked", "centre": "não dá", "name": name, "sub": "1 jogo · não dá", "done": 0.0,
                "games": count}
    return {"label": label, "state": "waiting", "centre": "à espera", "name": name, "sub": f"{games} · à espera",
            "done": 0.0, "games": count}


UNIVERSAL_SESSION = 6 * 3600  # TrainingUniversalSession: 360 min


def universal_ring(universal: dict | None, now: float) -> dict:
    """The universal trainer beside the doctor and the lawyer (owner, 2026-10-12), only while it is active: who it
    trains and the time left (green when the session is ready to collect), or nobody yet."""
    until = (universal or {}).get("until")
    if not until or until <= now:
        return {"label": "Treinador universal", "state": "none", "centre": "—", "name": "", "sub": "", "done": 0.0}
    active = f"ativo até {datetime.fromtimestamp(until):%H:%M}"
    session = (universal or {}).get("session")
    if not session:
        return {"label": "Treinador universal", "state": "waiting", "centre": "livre", "name": "ninguém", "sub": active, "done": 0.0}
    if session["claimed"] or session["finish"] <= now:
        return {"label": "Treinador universal", "state": "ready", "centre": "pronto", "name": session["name"], "sub": active,
                "done": 1.0}
    return {"label": "Treinador universal", "state": "working", "centre": span(session["finish"] - now), "name": session["name"],
            "sub": active, "done": _done(session["finish"] - now, session.get("length") or UNIVERSAL_SESSION)}


def time_left(seconds: float, lang: str = "pt") -> str:
    """Days and hours, as the owner reads it (2026-10-12): "1 dia e 13 horas", "13 horas", "40 min"."""
    seconds = max(0, int(seconds))
    days, hours, minutes = seconds // 86400, seconds % 86400 // 3600, seconds % 3600 // 60

    def unit(n: int, pt: str, en: str) -> str:
        return f"{n} {_say(lang, pt, en)}{'' if n == 1 else 's'}"

    if days:
        text = unit(days, "dia", "day")
        return text + (_say(lang, " e ", " and ") + unit(hours, "hora", "hour") if hours else "")
    if hours:
        return unit(hours, "hora", "hour")
    return f"{minutes} min"


def inventory_view(items: list[dict] | None, now: float, lang: str = "pt") -> dict | None:
    """The top bar's inventory (owner, 2026-10-12): a yellow dot when an item expires within 24 h; on hover only the
    items that expire, each with the time left in days and hours. None when it could not be read."""
    if items is None:
        return None
    rows, warn = [], False
    for item in sorted((i for i in items if i.get("expires") and i["expires"] > now), key=lambda i: i["expires"]):
        name = prize_text({"type": item["type"], "value": item["value"], "action": item["action"]}, lang)
        if item["type"] == 12:  # universal trainer: its hours, not the bare value
            name = _say(lang, f"treinador universal {round(item['value'] / 60)} h", f"universal trainer {round(item['value'] / 60)} h")
        left = item["expires"] - now
        soon = left <= WARN_BEFORE
        warn = warn or soon
        rows.append((prize_icon(item), f"{name} · {_say(lang, 'expira em', 'expires in')} {time_left(left, lang)}",
                     YELLOW if soon else None))
    if not rows:
        rows = [(None, _say(lang, "Nada a expirar", "Nothing expiring"), GREY)]
    return {"warn": warn, "rows": rows}


TOP_PLACES, BOTTOM_PLACES = 2, 3  # squad value: 1st-2nd green, the last 3 red, yellow in between (owner, 2026-10-10)


def squad_view(value: tuple | None, table: list | None = None) -> dict:
    """The squad value: the place by value in colour, the total in white; players and average on hover, and the
    league's table by value around the club when known (owner, 2026-10-15)."""
    if not value:
        return {"place": "", "colour": GREY, "total": "—", "tip": "", "table_tip": None}
    place, total, average, *more = value  # (place, total, average, players, teams); older readings had only 3
    players, teams = more if more else (round(total / average) if average else 0, 0)
    colour = GREEN if place <= TOP_PLACES else RED if teams and place > teams - BOTTOM_PLACES else YELLOW
    tip = f"{players} jogadores · média {money(round(average))}"
    rows = [([str(at), name, money(sum_), str(count), money(round(avg))], mine) for at, name, sum_, count, avg, mine in table or []]
    grid = {"columns": [("#", "r"), ("Clube", "l"), ("Valor", "r"), ("Jogadores", "r"), ("Média", "r")], "rows": rows,
            "foot": ""} if rows else None  # as the game's table by value (owner, 2026-10-15)
    return {"place": f"{place}.º", "colour": colour, "total": money(total), "tip": tip, "table_tip": grid}


CLOSE_STRENGTH = 2  # the opponent's circle: yellow when the strengths are less than 2 apart [S] (THEORY.md section 19)


def opponent_tip(name: str, value: tuple | None) -> dict | None:
    """The hover on the opponent's name: its squad value, players and average, one per line under its name (no
    strength: the circle shows it; owner 2026-10-15: "mais esclarecedor e não 1 linha tudo seguido")."""
    if not value:
        return None
    place, total, average, *more = value
    players = more[0] if more else (round(total / average) if average else 0)
    return {"title": name, "pairs": [("Valor do plantel", money(total)), ("Jogadores", str(players)),
                                     ("Média", money(round(average)))]}


def rating_badge(strength: int | None, ours: int | None = None) -> dict | None:
    """The team's strength in a circle, the number the game shows (owner, 2026-10-13). The club's own is blue; the
    opponent's (``ours`` given) is green when weaker, red when stronger, yellow when close. None when unknown: the
    opponent's only once analysed, as in the game. No hover on either (owner, 2026-10-15: redundant)."""
    if not strength:
        return None
    colour = BLUE
    if ours:
        colour = GREEN if strength <= ours - CLOSE_STRENGTH else RED if strength >= ours + CLOSE_STRENGTH else YELLOW
    return {"text": str(strength), "colour": colour, "tip": ""}


def table_view(club: dict) -> tuple[str, dict | None]:
    """The club's place ("2.º Campeonato", or "Campeões" once the title is mathematically won) and its hover: the
    top 3 (the top 2 and the club when below 3rd) as the game's table, # · Clube · J · DG · Pts (owner, 2026-10-15),
    and the season's goal under it (THEORY.md section 19), with the green tick when the club is at or above it and the
    yellow mark when below; no mark before the league's first round (owner, 2026-10-15)."""
    table = club.get("table") or {}
    header = "Campeões" if table.get("champion") else f"{club.get('ranking') or '?'}.º Campeonato"
    rows = [([str(place), name, str(rest[0]) if rest else "", (f"{rest[1]:+d}" if rest[1] else "0") if len(rest) > 1 else "", str(points)], mine)
            for place, name, points, mine, *rest in table.get("rows") or []]
    if not rows:
        return header, None
    goal = table.get("goal")
    foot = f"Objetivo: {goal}.º" + (" ou acima" if goal > 1 else "") if goal else ""
    started = (club.get("week") or 0) >= 1  # weekNr < 1: the pre-season, the table means nothing yet
    mark = ("done" if club["ranking"] <= goal else "collect") if goal and started and club.get("ranking") else None
    return header, {"columns": [("#", "r"), ("Clube", "l"), ("J", "r"), ("DG", "r"), ("Pts", "r")], "rows": rows, "foot": foot,
                    "mark": mark}


def tired_view(club: dict) -> tuple[str, str]:
    """The tired starters' line and, when one has no cover, the "SALE" players that fit the money (THEORY.md 16)."""
    cover = club.get("cover") or {}
    text = " · ".join(f"{p['name']} {p['fitness']}%" + (f" (sem suplente {p['pos']})" if p["pos"] in cover else "")
                      for p in club.get("tired") or [])
    tips = []
    for pos, options in cover.items():
        if options:
            tips.append(f"SALE {pos} que cabem no dinheiro:\n" + "\n".join(
                f"{o['rating']} · {o['nome']} ({o['idade']} anos) · {money(o['preco'])}" for o in options))
        else:
            tips.append(f"Nenhum SALE {pos} cabe no dinheiro")
    return text, "\n\n".join(tips)


def sale_view(club: dict) -> dict | None:
    """The "SALE" worth a look (THEORY.md 7.7), for a blue stripe as the game's (owner, 2026-10-15): the best one, its
    price and estimated resale profit ("?" when the league does not sell at the maximum), its marks and how many more;
    on hover the 3 as a table, with "reforço" (better than the weakest starter) and "pechincha". None: no stripe."""
    sale = club.get("sale") or {}
    picks = sale.get("picks") or []
    if not picks:
        return None
    unsure = "" if sale.get("certo") else "?"

    def tags(p: dict) -> list[str]:
        return (["reforço"] if p["reforco"] else []) + (["pechincha"] if p["pechincha"] else [])

    best = picks[0]
    rows = [([p["pos"], str(p["rating"]), p["nome"], str(p["idade"]), money(p["preco"]), f"{p['razao']}×",
              f"~{money(p['lucro'])}{unsure}", " · ".join(f"{tag} (> {p['fraco']})" if tag == "reforço" and p["fraco"] else tag
                                                          for tag in tags(p))],
             False) for p in picks]
    grid = {"columns": [("Pos", "l"), ("Força", "r"), ("Jogador", "l"), ("Idade", "r"), ("Preço", "r"), ("Valor", "r"),
                        ("Lucro", "r"), ("", "l")], "rows": rows,
            "foot": "? = esta liga não vendeu ao máximo nos últimos 3 dias" if unsure else ""}
    return {"player": f"{best['pos']} {best['rating']} · {best['nome']}", "price": money(best["preco"]),
            "profit": f"lucro ~{money(best['lucro'])}{unsure}", "tags": tags(best), "more": len(picks) - 1, "tip": grid}


def sponsor_view(sponsors: dict | None) -> dict:
    """Only the money per round; with an empty slot, ⚠ and the empty slots said on hover (owner, 2026-10-10)."""
    if not sponsors:
        return {"text": "—", "colour": GREY, "tip": ""}
    empty = SPONSOR_SLOTS - sponsors["slots"]
    text = f"{money(sponsors['revenue'])}/ronda"
    if empty <= 0:
        return {"text": text, "colour": None, "tip": ""}  # white, not green (owner, 2026-10-10)
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
    steps = []  # (kind, name, extra, why): one icon per kind, all the same size (owner, 2026-10-10)
    why = prep.get("why") or {}
    for name, done, analyst in prep.get("steps") or []:
        reasons = why.get(name) or []  # out of the owner's rule: said on hover (THEORY.md section 21)
        if done:  # a done step never has warnings (they make it yellow): its lines are notes, a small "ⓘ" (owner, 2026-10-14)
            steps.append(("done", name, "ⓘ" if reasons else "", reasons))
        elif analyst == "fora da regra":  # done in the game but not as the owner's rule: yellow (owner, 2026-10-12)
            steps.append(("progress", name, "", reasons))
        elif analyst and analyst > now:
            steps.append(("waiting", name, span(analyst - now), reasons))
        elif analyst:
            steps.append(("collect", name, "por levantar", reasons))
        else:
            steps.append(("open", name, "", reasons))

    boosts = []  # secret training and training camp: the game's icon, green when marked, grey otherwise (owner, 2026-10-14)
    for boost in prep.get("boosts") or []:
        blocked = "Sem jogo nesta jornada" if boost["blocked"].startswith("You don't have a match") else (
            f"Indisponível: {boost['blocked']}" if boost["blocked"] else "")  # the game says why in English
        tip = "Marcado para o próximo jogo" if boost["on"] else blocked or "Não marcado"
        boosts.append({"icon": boost["kind"], "name": boost["name"], "on": boost["on"], "tip": tip})

    trainings = []
    for t in club.get("trainings", []):
        left = t["finish"] - now
        ready = left <= 0 and not t["claimed"]
        length = t.get("length") or BAR_SECONDS  # the session's real length (2 h in some events)
        done = _done(left, length)
        skipped = min(done, max(shortened.get(t.get("id"), 0), 0) / length)
        trainings.append((t["name"], t["pos"], "pronto" if ready else span(left), GREEN if ready else BLUE, done, skipped))

    match = None  # the stripe of the next match (D-030), in the club's colour
    if nxt:
        match = {"text": f"vs {nxt['opponent']}{rank}", "value": rating_badge(nxt.get("strength"), club.get("strength")),
                 "tip": opponent_tip(nxt["opponent"], nxt.get("value")),
                 "tag": ("CASA" if nxt["side"] == "H" else "FORA") + (" · TAÇA" if nxt["cup"] else ""), "danger": nxt["danger"], "left": span(club["match"] - now) if club.get("match") else ""}
    header, table_tip = table_view(club)  # and the cup on a line of its own (owner, 2026-10-09)
    cup_line = cup[:1].upper() + cup[1:]
    done_steps = sum(1 for _, done, _ in prep.get("steps") or [] if done)
    prep_title = f"PRÉ-JOGO · {done_steps}/{len(prep.get('steps') or [])}" if prep.get("steps") else "PRÉ-JOGO"
    tired_text, tired_tip = tired_view(club)

    return {"name": club["name"], "logo": club.get("logo"), "logo_key": club.get("logo_key") or club["name"],
            "subtitle": subtitle, "facts": facts, "alert": alert, "header": header, "cup_line": cup_line, "match": match, "prep_title": prep_title,
            "money": _money(total), "sales": sales, "sponsors": sponsor_row, "squad": squad_view(club.get("value"), club.get("value_table")),
            "stadium": {"still": still, "moving": moving},
            "prep": {"steps": steps, "boosts": boosts},
            "trainings": trainings,
            "tired": tired_text, "tired_tip": tired_tip, "sale": sale_view(club), "value_badge": rating_badge(club.get("strength")), "table_tip": table_tip,
            "injured": _people(club.get("injured") or [], "no médico", now),
            "suspended": _people(club.get("suspended") or [], "no advogado", now),
            "stadium_rings": stadium_rings(club.get("stadium"), now),
            "care": [care_ring("Médico", club.get("injured") or [], now),
                     care_ring("Advogado", club.get("suspended") or [], now, lawyer=True)],
            "universal": universal_ring(club.get("universal"), now)}


def _daily_parts(daily: dict, now: float) -> list[tuple[str, str, str, str]]:
    """(which, kind, text, colour) per piece; "which" says what its hover is about."""
    parts: list[tuple[str, str, str, str]] = []
    login = daily.get("login")
    if login:
        parts.append(("login", "collect", "Início de sessão por reclamar", YELLOW) if login["claimable"]
                     else ("login", "done", f"Início de sessão (dia {login['day']})", GREEN))
    missions = daily.get("missions")
    if missions and missions["total"]:
        finished = missions["claimed"] >= missions["total"]
        parts.append(("missions", "done", f"Missões {missions['claimed']}/{missions['total']}", GREEN) if finished
                     else ("missions", "progress", f"Missões {missions['claimed']}/{missions['total']}", YELLOW))
        if missions["day_pending"]:
            parts.append(("day", "collect", "Prémio diário por reclamar", YELLOW))
        else:
            parts.append(("day", "done", "Prémio diário", GREEN) if finished else ("day", "open", "Prémio diário", GREY))
    renews = (login or {}).get("renews")
    if renews and renews > now:
        parts.append(("renews", "waiting", f"Novo dia em {span(renews - now)}", BLUE))
    return parts


PRIZE_ICONS = {1: "coins", 8: "funds", 9: "training", 12: "universal", 13: "inventory"}  # the window's pictures; any other prize: the missions one


def prize_icon(prize: dict | None) -> str:
    return PRIZE_ICONS.get((prize or {}).get("type"), "missions")


def daily_tips(daily: dict | None, lang: str = "pt") -> dict[str, list[tuple[str | None, str, str | None]]]:
    """The hover of each daily piece (owner, 2026-10-12), as rows of (icon, text, colour); the icon is a picture
    of the window ("coins", "funds"...) or a step mark ("done", "progress"). Login: only today's prize. Missions:
    the three of today, done or not, with their progress. Day reward: today's, and tomorrow's."""
    daily = daily or {}
    tips = {}
    login = daily.get("login")
    if login:
        prize = login.get("today")
        if prize:
            claim = _say(lang, " (por reclamar)", " (to claim)") if login.get("claimable") else ""
            tips["login"] = [(prize_icon(prize), _say(lang, "Hoje: ", "Today: ") + prize_text(prize, lang) + claim, None)]
        else:  # claimed before this PC ever saw it (on another PC or on the site)
            tips["login"] = [(None, _say(lang, "Hoje: reclamado (prémio não visto)", "Today: claimed (prize not seen)"), GREY)]
        tomorrow = login.get("tomorrow")
        if tomorrow:
            tips["login"].append((prize_icon(tomorrow), _say(lang, "Amanhã: ", "Tomorrow: ") + prize_text(tomorrow, lang), GREY))
    missions = daily.get("missions")
    if missions:
        dailies = missions.get("dailies") or []
        if dailies:
            tips["missions"] = [("done" if m["claimed"] else "progress",
                                 f"{mission_text(m['text'], lang)} ({amount(m['progress'], m['goal'])})", None) for m in dailies]
        week = missions.get("week") or []
        today = missions.get("today")
        first = next((d for d in week if d["day"] == today), None)
        if first:
            state = (_say(lang, "reclamado", "claimed") if first["claimed"] else
                     _say(lang, "por reclamar", "to claim") if missions.get("day_pending") else
                     _say(lang, "depois das 3 missões", "after the 3 missions"))
            rows = [(prize_icon(first["prize"]), _say(lang, "Hoje: ", "Today: ") + f"{prize_text(first['prize'], lang)} ({state})", None)]
        else:
            rows = [(None, _say(lang, "Sem prémio do dia", "No daily prize today"), GREY)]
        tomorrow = next((d for d in week if today is not None and d["day"] == today + 1), None)
        if tomorrow:
            rows.append((prize_icon(tomorrow["prize"]), _say(lang, "Amanhã: ", "Tomorrow: ") + prize_text(tomorrow["prize"], lang), GREY))
        if week or dailies:
            tips["day"] = rows
    return tips


def daily_view(daily: dict | None, now: float) -> tuple[list[tuple[str, str, str]], dict | None]:
    """The daily rewards as (kind, text, colour) pieces, and the accumulated-videos row (or None). The kind is the
    icon the window draws, as in the pre-match list (owner, 2026-10-10)."""
    daily = daily or {}
    parts = [piece[1:] for piece in _daily_parts(daily, now)]
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


MONTH_NAMES = {"pt": "Janeiro Fevereiro Março Abril Maio Junho Julho Agosto Setembro Outubro Novembro Dezembro".split(),
               "en": "January February March April May June July August September October November December".split()}


def _days(event: dict) -> str:
    start, end = date.fromisoformat(event["inicio"]), date.fromisoformat(event["fim"])
    if start == end:
        return f"{start:%d/%m}"
    return f"{start:%d}–{end:%d/%m}" if start.month == end.month else f"{start:%d/%m}–{end:%d/%m}"


def calendar_view(months: list[dict] | None, now: float, lang: str = "pt") -> dict | None:
    """The events' calendar (owner, 2026-10-12): in the top bar, the event going on or the next one; on hover,
    each whole month as a calendar (a row per week, Monday first), the event's name on its days (orange) and its
    effects on hover over the day. This month (or the last one the bot has, if older) and any later month it has.
    None without a schedule."""
    events = []
    for month in months or []:
        for event in month.get("eventos") or []:
            start, end = span_of(event)
            events.append({**event, "start": start, "end": end})
    if not events:
        return None
    events.sort(key=lambda e: e["start"])
    today = datetime.fromtimestamp(now).date()
    going = next((e for e in events if e["start"] <= now < e["end"]), None)
    coming = next((e for e in events if e["start"] > now), None)
    if going:
        label = [(_say(lang, "Evento agora: ", "Event now: "), GREY), (going["nome"], ORANGE),
                 (_say(lang, " · até ", " · until ") + f"{date.fromisoformat(going['fim']):%d/%m}", None)]
    elif coming:
        label = [(_say(lang, "Próximo evento: ", "Next event: "), GREY), (coming["nome"], ORANGE), (f" · {_days(coming)}", None)]
    else:
        label = [(_say(lang, "Sem eventos marcados", "No events scheduled"), GREY)]
    keys = sorted(m["mes"] for m in months if m.get("eventos"))
    shown = []
    for key in [k for k in keys if k >= f"{today:%Y-%m}"] or keys[-1:]:
        first = date.fromisoformat(key + "-01")
        last = (first + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        weeks, day = [], first - timedelta(days=first.weekday())
        while day <= last:
            week = []
            for _ in range(7):
                if first <= day <= last:
                    found = [e for e in events if e["inicio"] <= day.isoformat() <= e["fim"]]
                    week.append({"day": day.day, "today": day == today, "past": day < today,
                                 "events": [{"name": e["nome"], "when": _days(e),
                                             "effects": [effect_text(line, lang) for line in e.get("efeitos") or []]}
                                            for e in found]})
                else:
                    week.append(None)
                day += timedelta(days=1)
            weeks.append(week)
        shown.append({"title": f"{MONTH_NAMES[lang if lang in MONTH_NAMES else 'en'][first.month - 1]} {first.year}", "weeks": weeks})
    return {"label": label, "months": shown,
            "weekdays": _say(lang, "Seg Ter Qua Qui Sex Sáb Dom", "Mon Tue Wed Thu Fri Sat Sun").split()}


def board_view(snapshot: dict | None, stats: dict | None, now: float, doing: dict | None = None,
               history: list[dict] | None = None, lang: str = "pt") -> dict | None:
    """Everything the window shows for one moment (None while there is nothing read yet)."""
    if not snapshot:
        return None
    shortened = (stats or {}).get("shortened") or {}
    tips = daily_tips(snapshot.get("daily"), lang)
    daily = [(kind, text, colour, tips.get(which, []))
             for which, kind, text, colour in _daily_parts(snapshot.get("daily") or {}, now)]
    return {"clubs": [club_view(c, now, shortened) for c in snapshot["clubs"]],
            "account": account_view(snapshot, stats, now), "next": next_check(snapshot, now),
            "doing": doing_view(snapshot, doing, now),
            "daily": [piece for piece in daily if piece[0] != "waiting"],  # the new day is on the timeline
            "event": calendar_view(snapshot.get("calendar"), now, lang),
            "inventory": inventory_view(snapshot.get("inventory"), now, lang),
            "timeline": {"future": future_view(snapshot, now), "past": past_view(history or []),
                         "now": (doing or {}).get("text") or ""}}
