"""The console board of ``osmbot ativo`` (D-015): a fixed screen that redraws itself.

``collect`` reads the game (GET only); ``render`` is a pure function from that snapshot to text,
so the countdowns can be redrawn every second without touching the game.
"""
from __future__ import annotations

import os
import platform
import sys
import time
from datetime import datetime

from osmbot.game.ads import SHOP_ACTION, TRAINING_ACTION, money_state
from osmbot.game.slots import read_slots
from osmbot.theory.fitness import YELLOW_BELOW, tired_starters

POSITIONS = {1: "ATA", 2: "MED", 3: "DEF", 4: "GR"}
NEXT_MATCH_TIMER = 14
BAR_SECONDS = 8 * 3600  # the bar is drawn against a normal 8h training
BAR_WIDTH = 18
WIDTH = 66
GREEN, YELLOW, GREY, RESET = "\x1b[32m", "\x1b[33m", "\x1b[90m", "\x1b[0m"
RED, CYAN, BOLD = "[31m", "[36m", "[1m"
SPONSOR_SLOTS = 4
STADIUM_NAMES = {2: "campo de treinos", 1: "campo", 0: "capacidade"}


def span(seconds: float) -> str:
    minutes = int(max(0, seconds) // 60)
    return f"{minutes // 60}h{minutes % 60:02d}"


def money(amount: int) -> str:
    """12 345 678 -> "12,35 M"; 450 000 -> "450 k"."""
    if abs(amount) >= 1_000_000:
        return f"{amount / 1_000_000:.2f} M".replace(".", ",")
    return f"{amount / 1000:.0f} k"


def bar(left: float) -> str:
    done = 1 - min(max(left, 0), BAR_SECONDS) / BAR_SECONDS
    filled = round(done * BAR_WIDTH)
    return "█" * filled + "░" * (BAR_WIDTH - filled)


def collect(client) -> dict:
    """One snapshot of everything the board shows (a handful of GET requests)."""
    from osmbot.game.trainings import _teams

    _, account = client.get("user/accounts")
    _, wallet = client.get("user/bosscoinwallet")
    leagues = {c["team"]["name"]: c.get("league") or {} for c in (account.get("teamSlots") or {}).values() if c and c.get("team")}
    slots = {s.team: s for s in read_slots(client)}
    clubs = []
    for _, team, base in _teams(client):
        _, sessions = client.get(f"{base}/trainingsessions/ongoing")
        _, timers = client.get(f"{base}/timers")
        match = next((t["finishedTimestamp"] for t in timers if t["type"] == NEXT_MATCH_TIMER), None)
        slot = slots.get(team["name"])
        _, players = client.get(f"{base}/players")
        _, funds = client.get(f"{base}/finances/balanceandsavings")
        _, stadium = client.get(f"{base}/stadium")
        _, contracts = client.get(f"{base}/sponsors")
        running = [p["countdownTimer"]["finishedTimestamp"] for p in stadium["stadiumParts"]
                   if p.get("countdownTimer") and p["countdownTimer"]["finishedTimestamp"] > time.time()]
        live = [c for c in contracts if c.get("weeksLeft", 0) > 0]
        clubs.append({
            "name": team["name"], "ranking": team.get("ranking"), "league": leagues.get(team["name"], {}).get("name", "?"),
            "tired": tired_starters(players), "match": match,
            "money": (funds["balance"], funds["savings"]),
            "stadium": {"parts": [(STADIUM_NAMES.get(p["stadiumPartType"], "?"), p["level"],
                                   max((lv["level"] for lv in p["stadiumPartLevels"]), default=0),
                                   (p.get("countdownTimer") or {}).get("finishedTimestamp"))
                                  for p in sorted(stadium["stadiumParts"], key=lambda p: -p["stadiumPartType"])],
                        "until": max(running) if running else None},
            "sponsors": {"slots": len(live), "revenue": sum(c["sponsorRevenueForTeam"] for c in live)}, "slots": (slot.listed, slot.maximum) if slot else None,
            "trainings": [
                {"name": s["player"]["name"], "pos": POSITIONS.get(s["player"]["position"], "?"),
                 "finish": s["countdownTimer"]["finishedTimestamp"], "claimed": s["countdownTimer"]["isClaimed"]}
                for s in sorted(sessions, key=lambda s: s["trainer"])
            ],
        })
    ads = {}
    for key, action in (("shop", SHOP_ACTION), ("training", TRAINING_ACTION)):
        _, cap = client.get(f"user/caps/actions/{action}/0")
        ads[key] = {"open": bool(cap.get("isClaimable")) and not cap.get("isCapReached"),
                    "reopen": cap.get("timestampUntilUnreached") if cap.get("isCapReached") else None}
    ads["money"] = money_state(client)
    return {"coins": wallet.get("amount"), "clubs": clubs, "ads": ads}


def wake_events(snapshot: dict | None, now: float) -> list[tuple[str, float]]:
    """What the bot is waiting for, soonest first: (label, timestamp)."""
    if not snapshot:
        return []
    events = []
    finishes = [t["finish"] for c in snapshot["clubs"] for t in c["trainings"] if not t["claimed"] and t["finish"] > now]
    if finishes:
        events.append(("treino acaba", min(finishes)))
    ends = [c["stadium"]["until"] for c in snapshot["clubs"] if (c.get("stadium") or {}).get("until")]
    if ends and min(ends) > now:
        events.append(("estádio acaba", min(ends)))
    for key, label in (("shop", "loja reabre"), ("training", "vídeo de treino reabre"), ("money", "dinheiro reabre")):
        reopen = (snapshot["ads"].get(key) or {}).get("reopen")
        if reopen and reopen > now:
            events.append((label, reopen))
    return sorted(events, key=lambda e: e[1])


def _clock(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp).strftime("%H:%M")


def summary_lines(snapshot: dict | None, stats: dict | None, now: float) -> list[str]:
    """What the bot did since it started, on two short lines: balance change and what it did."""
    if not stats or stats.get("start") is None:
        return []
    first = f"Desde o arranque ({span(now - stats['start'])})"
    if snapshot and stats.get("coins0") is not None:
        first += f": saldo {snapshot['coins'] - stats['coins0']:+d} boss coins"
    second = (f"  vídeos: loja {stats.get('shop', 0)}, treino {stats.get('training', 0)}, dinheiro {stats.get('money', 0)}"
              f" · treinos: {stats.get('claimed', 0)} recolhidos, {stats.get('started', 0)} postos"
              f" · estádio {stats.get('upgrades', 0)} · patrocinadores {stats.get('signed', 0)}")
    return [first, second]


def summary_text(snapshot: dict | None, stats: dict | None, now: float) -> str:
    return " · ".join(line.strip() for line in summary_lines(snapshot, stats, now))


def render(snapshot: dict | None, now: float, status: str, recent: list[str], machine: str, colour: bool = True,
           stats: dict | None = None) -> str:
    def paint(text: str, code: str) -> str:
        return f"{code}{text}{RESET}" if colour else text

    rule = "─" * WIDTH
    lines = [f" OSMbot · {status} · {machine}".ljust(WIDTH - 8) + datetime.fromtimestamp(now).strftime("%H:%M:%S"), " " + rule]
    if snapshot is None:
        lines.append(" (a carregar…)")
    else:
        events = wake_events(snapshot, now)
        if events:
            lines.append(" A seguir  " + " · ".join(f"{label} {_clock(ts)} (em {span(ts - now)})" for label, ts in events))
        for club in snapshot["clubs"]:
            used = f"slots {club['slots'][0]}/{club['slots'][1]}" if club["slots"] else "slots ?"
            free = club["slots"][1] - club["slots"][0] if club["slots"] else 0
            head = f" {club['name'].upper()}   {club['ranking']}.º {club['league']}"
            if club["match"]:
                head += f"   jogo em {span(club['match'] - now)}"
            head += f"   {used}"
            lines += ["", paint(head, BOLD + (GREEN if not free else YELLOW)) + (paint(f"  ← LIVRE: {free}", YELLOW) if free else "")]
            if club.get("money"):
                funds, savings = club["money"]
                lines.append(f"   {paint('dinheiro', CYAN)}   fundos {paint(money(funds), GREEN if funds else GREY)}"
                             f" · poupança {paint(money(savings), GREEN if savings else GREY)}")
            stadium = club.get("stadium")
            if stadium:
                bits = []
                for name, level, top, ends in stadium["parts"]:
                    if ends and ends > now:
                        bits.append(paint(f"{name} {level}/{top} ▶ {span(ends - now)}", CYAN))
                    else:
                        bits.append(paint(f"{name} {level}/{top} ✓", GREY) if level >= top else f"{name} {level}/{top}")
                lines.append(f"   {paint('estádio', CYAN)}    " + " · ".join(bits))
            sponsors = club.get("sponsors")
            if sponsors:
                full = sponsors["slots"] >= SPONSOR_SLOTS
                lines.append(f"   {paint('patroc.', CYAN)}    "
                             + paint(f"{sponsors['slots']}/{SPONSOR_SLOTS} espaços", GREEN if full else YELLOW)
                             + f" · {paint(money(sponsors['revenue']), GREEN)}/ronda")
            for t in club["trainings"]:
                left = t["finish"] - now
                ready = left <= 0 and not t["claimed"]
                state = paint("pronto", BOLD + GREEN) if ready else paint(span(left), CYAN)
                drawn = bar(left)
                filled = drawn.count("█")
                lines.append(f"   {t['name'][:14]:<14} {t['pos']:<4} {state}{' ' * (6 - len('pronto' if ready else span(left)))}  "
                             + paint(drawn[:filled], GREEN) + paint(drawn[filled:], GREY))
            tired = club.get("tired") or []
            for p in tired[:5]:
                lines.append(paint(f"   ⚠ {p['name'][:14]:<14} {p['pos']:<4} cond. {p['fitness']}%  convém descansar 1 jogo", YELLOW))
            if len(tired) > 5:
                lines.append(paint(f"   ⚠ +{len(tired) - 5} titulares abaixo de {YELLOW_BELOW}%", YELLOW))
        shop, train = snapshot["ads"]["shop"], snapshot["ads"]["training"]
        money_ads = snapshot["ads"].get("money") or {}
        def flag(open_now: bool) -> str:
            return paint("✓", GREEN) if open_now else paint("-", GREY)

        lines += ["", f" Boss coins {paint(str(snapshot['coins']), BOLD + YELLOW)}    Vídeos: loja {flag(shop['open'])}"
                  f"  treino {flag(train['open'])}  dinheiro {flag(money_ads.get('open'))}"]
    summary = summary_lines(snapshot, stats, now)
    if summary:
        lines += ["", *[" " + line for line in summary]]
    lines.append(" " + rule)
    def log_colour(line: str) -> str:
        body = line[9:].lstrip()
        if body.startswith(("Parou", "Vídeos:", "Estádio:", "Patrocinadores:")) and "erro" in body or body.startswith("Parou"):
            return paint(line, RED)
        return paint(line, YELLOW if body.startswith(("!", "AVISO")) else GREY)

    lines += [" " + log_colour(line) for line in recent[-5:]] or [" (sem eventos)"]
    lines.append(" " * (WIDTH - 20) + "Ctrl+C para parar")
    return "\n".join(lines)


class Screen:
    """Redraws the board in place (ANSI). Only used when the output is a real terminal."""

    def __init__(self) -> None:
        if platform.system() == "Windows":
            os.system("")  # switches on ANSI escape codes in the Windows console
        self._out = sys.stdout  # the real terminal: stdout is redirected to the log while the bot works
        self._out.write("\x1b[?25l")  # hide the cursor

    def draw(self, text: str) -> None:
        self._out.write("\x1b[H\x1b[J" + text + "\n")
        self._out.flush()

    def close(self) -> None:
        self._out.write("\x1b[?25h")
        self._out.flush()


def machine_name() -> str:
    return {"Windows": "Windows", "Darwin": "macOS"}.get(platform.system(), platform.system())
