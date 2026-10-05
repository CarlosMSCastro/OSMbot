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

from osmbot.game.ads import SHOP_ACTION, TRAINING_ACTION
from osmbot.game.slots import read_slots

POSITIONS = {1: "ATA", 2: "MED", 3: "DEF", 4: "GR"}
NEXT_MATCH_TIMER = 14
BAR_SECONDS = 8 * 3600  # the bar is drawn against a normal 8h training
BAR_WIDTH = 18
WIDTH = 66
GREEN, YELLOW, GREY, RESET = "\x1b[32m", "\x1b[33m", "\x1b[90m", "\x1b[0m"


def span(seconds: float) -> str:
    minutes = int(max(0, seconds) // 60)
    return f"{minutes // 60}h{minutes % 60:02d}"


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
        clubs.append({
            "name": team["name"], "ranking": team.get("ranking"), "league": leagues.get(team["name"], {}).get("name", "?"),
            "match": match, "slots": (slot.listed, slot.maximum) if slot else None,
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
    return {"coins": wallet.get("amount"), "clubs": clubs, "ads": ads}


def wake_events(snapshot: dict | None, now: float) -> list[tuple[str, float]]:
    """What the bot is waiting for, soonest first: (label, timestamp)."""
    if not snapshot:
        return []
    events = []
    finishes = [t["finish"] for c in snapshot["clubs"] for t in c["trainings"] if not t["claimed"] and t["finish"] > now]
    if finishes:
        events.append(("treino acaba", min(finishes)))
    for key, label in (("shop", "loja reabre"), ("training", "video de treino reabre")):
        reopen = snapshot["ads"][key]["reopen"]
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
    second = (f"  vídeos: loja {stats.get('shop', 0)}, treino {stats.get('training', 0)}"
              f" · treinos: {stats.get('claimed', 0)} recolhidos, {stats.get('started', 0)} postos")
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
        lines.append(" (ainda sem dados do jogo)")
    else:
        events = wake_events(snapshot, now)
        if events:
            lines.append(" À espera  " + " · ".join(f"{label} {_clock(ts)} (em {span(ts - now)})" for label, ts in events))
        for club in snapshot["clubs"]:
            used = f"slots {club['slots'][0]}/{club['slots'][1]}" if club["slots"] else "slots ?"
            free = club["slots"][1] - club["slots"][0] if club["slots"] else 0
            head = f" {club['name'].upper()}   {club['ranking']}.º {club['league']}"
            if club["match"]:
                head += f"   jogo em {span(club['match'] - now)}"
            head += f"   {used}"
            lines += ["", paint(head, GREEN if not free else YELLOW) + (paint(f"  ← LIVRE: {free}", YELLOW) if free else "")]
            for t in club["trainings"]:
                left = t["finish"] - now
                state = "pronto" if left <= 0 and not t["claimed"] else span(left)
                drawn = bar(left)
                filled = drawn.count("█")
                lines.append(f"   {t['name'][:14]:<14} {t['pos']:<4} {state:>6}  "
                             + paint(drawn[:filled], GREEN) + paint(drawn[filled:], GREY))
        shop, train = snapshot["ads"]["shop"], snapshot["ads"]["training"]
        lines += ["", " Boss coins " + str(snapshot["coins"]) + "    Anúncios: loja " + ("✓" if shop["open"] else "esperar")
                  + "  treino " + ("✓" if train["open"] else "esperar")]
    summary = summary_lines(snapshot, stats, now)
    if summary:
        lines += ["", *[" " + line for line in summary]]
    lines.append(" " + rule)
    lines += [" " + paint(line, GREY) for line in recent[-5:]] or [" (sem registo ainda)"]
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
