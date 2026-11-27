"""The boss coins' ledger (owner, 2026-10-28: "onde foram os boss coins"; THEORY.md section 17).

Every place where the bot earns or spends boss coins notes it here (``note``); at each reading of the wallet
(``check``, the board's, every 3 minutes) the change since the reading before is split into what the bot did and
what is left: **fora do bot** (the owner by hand in the game or the site, or something the bot does not note). A line
in ``logs/<PC>/carteira/`` whenever the balance moves, and once a day a summary in the day's log. State (the last
balance and the day's totals) in ``~/.osmbot/carteira.json``.

[S] Two PCs running the bot at once see each other's spending as "fora do bot". A reading that falls between a spend
and its note shows it as "fora do bot" and the next one takes it back: the day's totals are right.

The first reading of each run is the starting point (owner, 2026-11-24: "quando o bot liga devia mostrar o saldo";
D-121): what changed before it is not counted, neither as "fora do bot" nor as "transferências", only what the bot
noted itself. The players seen arriving before it are dropped too.
"""
from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path

from osmbot import logs

FILE = Path.home() / ".osmbot" / "carteira.json"
OUTSIDE = "fora do bot"
TRANSFERS = "transferências"  # players the owner signs by hand (1 token each, 5 for a black card in form; D-114)
ORDER = ("vídeos da loja", "recompensas", "amigáveis", "treinos acabados", "estádio", "estágio", TRANSFERS, OUTSIDE)
_pending: dict[str, int] = {}
_history: list[dict] = []  # this run's changes, for the window's "since the bot started" (D-114)
_purchases: list[tuple[float, str]] = []  # players seen arriving, waiting for the drop of the wallet (time, name)
_run = {"started": False}  # False until this run's first reading of the wallet
_lock = threading.Lock()


def note(kind: str, amount: int) -> None:
    """The bot earned (+) or spent (-) ``amount`` boss coins on ``kind`` (one of ``ORDER``)."""
    if amount:
        with _lock:
            _pending[kind] = _pending.get(kind, 0) + amount


def since(start: float | None) -> list[dict] | None:
    """The changes of the balance noted since ``start`` ({"t", "diff", "parts", "players"}); None when not started."""
    if start is None:
        return None
    with _lock:
        return [entry for entry in _history if entry["t"] >= start]


PURCHASE_WINDOW = 20 * 60  # a purchase and the drop of the wallet are seen in either order, minutes apart


def note_purchases(players: list[str], now: datetime | None = None) -> None:
    """Players seen arriving in a squad by a transfer (``sales.update``). The wallet drops when the owner signs,
    but the squad is read minutes later, so either order happens: a drop already noted as "fora do bot" in the last
    20 min is moved to "transferências" (and corrected in the log); otherwise the players wait for the next drop.
    [S] An owner's spend at the same moment is also put here."""
    if not players:
        return
    now = now or datetime.now()
    with _lock:
        for entry in reversed(_history):
            if now.timestamp() - entry["t"] > PURCHASE_WINDOW:
                break
            if entry["parts"].get(OUTSIDE, 0) < 0 and not entry.get("players"):
                amount = entry["parts"].pop(OUTSIDE)
                entry["parts"][TRANSFERS] = entry["parts"].get(TRANSFERS, 0) + amount
                entry["players"] = list(players)
                _correct(amount, list(players), now)
                return
        _purchases.extend((now.timestamp(), name) for name in players)


def _correct(amount: int, players: list[str], now: datetime) -> None:
    """The totals and the log say "transferências" for a drop first written as "fora do bot" (no change of balance)."""
    state = _load()
    if state.get("saldo") is None:
        return
    state["totais"] = add(state.get("totais") or {}, {TRANSFERS: amount, OUTSIDE: -amount})
    try:
        FILE.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass
    logs.record("carteira", {"saldo": state["saldo"], "antes": state["saldo"], "diferenca": 0,
                             "partes": {TRANSFERS: amount, OUTSIDE: -amount}, "jogadores": players}, now)


SPENDING = ("amigáveis", "treinos acabados", "estádio")  # where the bot spends boss coins (and what a ceiling stops)
_warned: dict = {}


def spent_today(now: datetime | None = None) -> int:
    """The boss coins the bot has spent today: the day's totals plus what is not in them yet (this PC only)."""
    today = f"{(now or datetime.now()):%Y-%m-%d}"
    state = _load()
    totals = (state.get("totais") or {}) if state.get("dia") == today else {}
    with _lock:
        totals = add(totals, dict(_pending))
    return -sum(min(0, amount) for kind, amount in totals.items() if kind in SPENDING)


def cap_reached(price: int, cap: int | None, log=print, now: datetime | None = None) -> bool:
    """True when spending ``price`` more would pass the owner's daily ceiling (D-104); says so once a day."""
    if not cap or spent_today(now) + price <= cap:
        return False
    today = f"{(now or datetime.now()):%Y-%m-%d}"
    if _warned.get("dia") != today:
        _warned["dia"] = today
        log(f"Teto de boss coins do dia ({cap}) atingido: o bot não gasta mais hoje")
    return True


def split(change: int, done: dict[str, int], purchases: int = 0) -> dict[str, int]:
    """The change of the balance as the bot's kinds plus what is left, "fora do bot" (pure). With ``purchases`` (players
    seen arriving), a drop that is left is "transferências"."""
    parts = {kind: amount for kind, amount in done.items() if amount}
    left = change - sum(parts.values())
    if left:
        parts[TRANSFERS if purchases and left < 0 else OUTSIDE] = left
    return parts


def add(totals: dict[str, int], parts: dict[str, int]) -> dict[str, int]:
    return {kind: totals.get(kind, 0) + parts.get(kind, 0) for kind in {*totals, *parts}}


def summary_line(day: str, totals: dict[str, int], balance: int) -> str:
    """ "Boss coins (2026-10-28): +80 vídeos da loja · -56 amigáveis · -15 fora do bot · saldo 3 275" (pure)."""
    kinds = [k for k in ORDER if totals.get(k)] + sorted(k for k in totals if k not in ORDER and totals[k])
    parts = " · ".join(f"{totals[k]:+d} {k}" for k in kinds) or "sem mudanças"
    return f"Boss coins ({day}): {parts} · saldo {balance:,}".replace(",", " ")


def _load() -> dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def check(balance: int | None, log=None, now: datetime | None = None) -> None:
    """Compare the wallet with the last reading: record the change (when there is one) and, on a new day, write the
    day before's summary with ``log``."""
    if balance is None:
        return
    now = now or datetime.now()
    today = f"{now:%Y-%m-%d}"
    with _lock:
        done = dict(_pending)
        _pending.clear()
        _purchases[:] = [p for p in _purchases if now.timestamp() - p[0] <= PURCHASE_WINDOW]
        bought = [name for _, name in _purchases]
    state = _load()
    if state.get("dia") and state["dia"] != today:
        if log and state.get("totais"):
            log(summary_line(state["dia"], state["totais"], state.get("saldo", balance)))
        state["totais"] = {}
    state["dia"] = today
    before = state.get("saldo")
    stale = before is not None and not _run["started"]
    _run["started"] = True
    if stale:
        with _lock:
            _purchases.clear()
        bought = []
        if log and balance - before - sum(done.values()):
            log(f"Boss coins: {balance - before - sum(done.values()):+d} antes de o bot ligar "
                f"(saldo {before:,} → {balance:,}); não contam".replace(",", " "))
    if before is not None and (balance != before or done):
        parts = {k: v for k, v in done.items() if v} if stale else split(balance - before, done, len(bought))
        if TRANSFERS in parts:
            with _lock:
                _purchases.clear()
        diff = sum(parts.values()) if stale else balance - before
        if parts:
            record = {"saldo": balance, "antes": balance - diff, "diferenca": diff, "partes": parts}
            if TRANSFERS in parts:
                record["jogadores"] = bought
            logs.record("carteira", record)
            with _lock:
                _history.append({"t": now.timestamp(), "diff": diff, "parts": parts, "players": bought})
            state["totais"] = add(state.get("totais") or {}, parts)
    state["saldo"] = balance
    FILE.parent.mkdir(parents=True, exist_ok=True)
    FILE.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
