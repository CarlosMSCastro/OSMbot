"""The boss coins' ledger (owner, 2026-10-28: "onde foram os boss coins"; THEORY.md section 17).

Every place where the bot earns or spends boss coins notes it here (``note``); at each reading of the wallet
(``check``, the board's, every 3 minutes) the change since the reading before is split into what the bot did and
what is left: **fora do bot** (the owner by hand in the game or the site, or something the bot does not note). A line
in ``logs/<PC>/carteira/`` whenever the balance moves, and once a day a summary in the day's log. State (the last
balance and the day's totals) in ``~/.osmbot/carteira.json``.

[S] Two PCs running the bot at once see each other's spending as "fora do bot". A reading that falls between a spend
and its note shows it as "fora do bot" and the next one takes it back: the day's totals are right.
"""
from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path

from osmbot import logs

FILE = Path.home() / ".osmbot" / "carteira.json"
OUTSIDE = "fora do bot"
ORDER = ("vídeos da loja", "recompensas", "amigáveis", "treinos acabados", "estádio", OUTSIDE)
_pending: dict[str, int] = {}
_lock = threading.Lock()


def note(kind: str, amount: int) -> None:
    """The bot earned (+) or spent (-) ``amount`` boss coins on ``kind`` (one of ``ORDER``)."""
    if amount:
        with _lock:
            _pending[kind] = _pending.get(kind, 0) + amount


def split(change: int, done: dict[str, int]) -> dict[str, int]:
    """The change of the balance as the bot's kinds plus what is left, "fora do bot" (pure)."""
    parts = {kind: amount for kind, amount in done.items() if amount}
    left = change - sum(parts.values())
    if left:
        parts[OUTSIDE] = left
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
    state = _load()
    if state.get("dia") and state["dia"] != today:
        if log and state.get("totais"):
            log(summary_line(state["dia"], state["totais"], state.get("saldo", balance)))
        state["totais"] = {}
    state["dia"] = today
    before = state.get("saldo")
    if before is not None and (balance != before or done):
        parts = split(balance - before, done)
        if parts:
            logs.record("carteira", {"saldo": balance, "antes": before, "diferenca": balance - before, "partes": parts})
            state["totais"] = add(state.get("totais") or {}, parts)
    state["saldo"] = balance
    FILE.parent.mkdir(parents=True, exist_ok=True)
    FILE.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
