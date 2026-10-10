"""The window's timeline (D-030): what comes next (above "now") and what the bot already did (below). Pure.

The past is built from the bot's own log lines: only the ones that are an action (a video watched, a training
collected or started, the doctor, a friendly...), with runs of the same thing merged into one entry
("Vídeos da loja ×9", "Treinos recolhidos: A, B"). The future comes from the same snapshot as the cards.
"""
from __future__ import annotations

import re
from datetime import datetime

from osmbot.game.dashboard import span

MERGE_WITHIN = 15 * 60  # s: the same kind of action this close to the last one joins it
KEEP = 40  # past entries kept
PREP_BEFORE = 4 * 3600  # the friendly and the analysis are done 4 h before the match (THEORY.md section 6)
SIDES = {"H": "casa", "A": "fora"}

_ACTIONS = (  # (pattern, kind, text): kinds in MERGED join the previous entry of the same kind
    (re.compile(r"^Loja: vídeo \d+$"), "shop", "Vídeos da loja"),
    (re.compile(r"^Treino: vídeo \d+ \((?P<club>.+), (?P<pos>\w+)\)$"), "training_video", "Vídeo de treino −2h"),
    (re.compile(r"^Dinheiro: vídeo \d+ \((?P<club>.+)\)$"), "money", "Vídeo de dinheiro"),
    (re.compile(r"^(?P<name>[^:(]+): recolhido \("), "collect", "Treinos recolhidos"),
    (re.compile(r"^(?P<name>[^:(]+) \(\w+, \d+ anos, rating \d+\): a treinar"), "train", "A treinar"),
    (re.compile(r"^(?P<club>.+): (?P<part>[^:]+): melhoria iniciada$"), "stadium", "Estádio"),
    (re.compile(r"^Patrocinador: (?P<what>.+)$"), "sponsor", "Patrocinador"),
    (re.compile(r"^(?P<what>(Amigável|Análise|Médico|Advogado): .+)$"), "match", ""),
    (re.compile(r"^(?P<what>(Missões|Início de sessão|Vídeos acumulados): .*reclamad.+)$"), "reward", ""),
)
_FAILED = re.compile(r"\b(falh|recus|erro)\w*|à espera|\bnão\b")
MERGED = {"shop", "collect", "train", "money", "training_video"}


def action(message: str) -> dict | None:
    """The log line as a past action, or None when it is not one (counts, waits, warnings, failures)."""
    text = message.lstrip(chr(7)).strip()
    if text.startswith("!") or _FAILED.search(text):
        return None
    for pattern, kind, title in _ACTIONS:
        found = pattern.match(text)
        if not found:
            continue
        parts = found.groupdict()
        if kind in ("collect", "train"):
            return {"kind": kind, "title": title, "names": [parts["name"].strip()]}
        if kind == "training_video":
            return {"kind": kind, "title": title, "names": [f"{parts['club']} {parts['pos']}"]}
        if kind == "money":
            return {"kind": kind, "title": title, "names": [parts["club"]]}
        if kind == "stadium":
            return {"kind": kind, "title": f"Estádio: {parts['part']} a subir", "sub": parts["club"]}
        if kind == "sponsor":
            return {"kind": kind, "title": "Patrocinador assinado", "sub": parts["what"]}
        if kind in ("match", "reward"):
            head, _, rest = parts["what"].partition(": ")
            return {"kind": kind, "title": head, "sub": rest}
        return {"kind": kind, "title": title}
    return None


def add(history: list[dict], when: float, message: str) -> None:
    """Add the log line to the past if it is an action, merging it with the last entry when it is more of the same."""
    found = action(message)
    if not found:
        return
    last = history[-1] if history else None
    if last and found["kind"] in MERGED and last["kind"] == found["kind"] and when - last["ts"] <= MERGE_WITHIN:
        last["ts"] = when
        last["count"] = last.get("count", 1) + 1
        for name in found.get("names", []):
            if name not in last.setdefault("names", []):
                last["names"].append(name)
        return
    history.append({**found, "ts": when, "count": 1})
    del history[:-KEEP]


def past_view(history: list[dict]) -> list[dict]:
    """The past for the window, newest first: {"time": "21:05", "title", "sub"}."""
    rows = []
    for entry in reversed(history):
        title = entry["title"]
        if entry["kind"] == "shop" and entry.get("count", 1) > 1:
            title = f"{title} ×{entry['count']}"
        elif entry["kind"] in ("training_video", "money") and entry.get("count", 1) > 1:
            title = f"{title} ×{entry['count']}"
        sub = entry.get("sub") or ", ".join(entry.get("names") or [])
        rows.append({"time": f"{datetime.fromtimestamp(entry['ts']):%H:%M}", "title": title, "sub": sub,
                     "icon": icon_of(entry)})
    return rows


PAST_ICONS = {"shop": "coins", "training_video": "training", "money": "funds", "collect": "training",
              "train": "training", "stadium": "stadium", "sponsor": "funds", "reward": "missions"}
MATCH_ICONS = {"Médico": "cross", "Advogado": "card"}  # the friendly and the analysis keep the dot


def icon_of(entry: dict) -> str:
    """The icon of a past entry in the timeline ("" = the plain dot)."""
    if entry["kind"] == "match":
        return MATCH_ICONS.get(entry["title"], "")
    return PAST_ICONS.get(entry["kind"], "")


def _event(ts: float, title: str, sub: str = "", club: int | None = None, icon: str = "") -> dict:
    return {"ts": ts, "title": title, "sub": sub, "club": club, "icon": icon}


def _clock(ts: float) -> str:
    return f"{datetime.fromtimestamp(ts):%H:%M}"


def future_events(snapshot: dict | None, now: float) -> list[dict]:
    """What comes next, soonest first: {"ts", "title", "sub", "club"} (club = its index, None for the account).
    Things already due (a video open, a training to collect) get ``now``."""
    if not snapshot:
        return []
    events = []
    ads = snapshot.get("ads") or {}
    for key, title, plural, icon in (("shop", "Vídeos da loja", True, "coins"), ("training", "Acelerar treinos", False, "training"),
                                     ("money", "Vídeos de dinheiro", True, "funds")):
        info = ads.get(key) or {}
        if info.get("open"):
            events.append(_event(now, title, "disponíveis" if plural else "disponível", icon=icon))
        elif info.get("reopen") and info["reopen"] > now:
            events.append(_event(info["reopen"], title, f"reabre às {_clock(info['reopen'])}", icon=icon))
    daily = snapshot.get("daily") or {}
    videos = daily.get("videos") or {}
    if videos.get("claimable"):
        events.append(_event(now, "Reward cumulativo", "por reclamar", icon="missions"))
    elif videos.get("reopen") and videos["reopen"] > now:
        events.append(_event(videos["reopen"], "Reward cumulativo", f"{videos.get('count', 0)}/{videos.get('threshold', '?')}",
                             icon="missions"))
    renews = (daily.get("login") or {}).get("renews")
    if renews and renews > now:
        events.append(_event(renews, "Novo dia (diárias)", icon="missions"))

    for index, club in enumerate(snapshot.get("clubs") or []):
        name = club["name"]
        groups: list[tuple[float, list[str]]] = []  # trainings ending within a minute of each other: one line
        for t in sorted((t for t in club.get("trainings") or [] if not t.get("claimed")), key=lambda t: t["finish"]):
            ends = max(t["finish"], now)
            if groups and ends - groups[-1][0] <= 60:
                groups[-1][1].append(t["name"])
            else:
                groups.append((ends, [t["name"]]))
        for ts, names in groups:
            title = ("Recolher treino " if ts <= now else "Treino ") + ", ".join(names)
            events.append(_event(max(ts, now), title, name, index, "training"))
        match, nxt = club.get("match"), club.get("next") or {}
        if match and match > now:
            opponent = nxt.get("opponent")
            sub = "jogo · " + SIDES.get(nxt.get("side"), "?") + (" · taça" if nxt.get("cup") else "")
            events.append(_event(match, f"{name} vs {opponent}" if opponent else f"Jogo {name}", sub, index, "ball"))
            missing = [step for step, done, _ in (club.get("prep") or {}).get("steps") or []
                       if step in ("Amigável", "Análise") and not done]
            if missing and match - PREP_BEFORE > now:
                events.append(_event(match - PREP_BEFORE, " e ".join(missing), name, index))
        for part, level, top, ends in (club.get("stadium") or {}).get("parts") or []:
            if ends and ends > now:
                events.append(_event(ends, f"{part} {name}", f"{level}/{top} → {level + 1}/{top}", index, "stadium"))
        for people, place in ((club.get("injured") or [], "Médico"), (club.get("suspended") or [], "Advogado")):
            for p in people:
                if p.get("ready"):
                    events.append(_event(now, f"{place}: levantar {p['name']}", name, index, MATCH_ICONS[place]))
                elif p.get("until") and p["until"] > now:
                    events.append(_event(p["until"], f"{place}: {p['name']}", name, index, MATCH_ICONS[place]))
    return sorted(events, key=lambda e: (e["ts"], e["title"]))


def future_view(snapshot: dict | None, now: float) -> list[dict]:
    """The future for the window, soonest first, with the time left as text ("já" when due)."""
    return [{**e, "left": "já" if e["ts"] <= now else span(e["ts"] - now)} for e in future_events(snapshot, now)]
