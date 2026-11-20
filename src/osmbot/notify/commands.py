"""What the owner writes to the bot on Telegram (D-116): ``/estado`` and ``/parar <PC>``. The bot reads only messages
from the saved ``chat_id`` (the code is public: that check is the lock) and never anything else. One bot can run on
several PCs, so a command carries the PC's name and a PC acts only on its own; a command for another PC is left unread
for it (Telegram keeps it 24 h). Commands older than ``STALE`` seconds, or sent before this run began, are ignored and
only then marked as read. Everything here is pure or injected (tested without a network); ``default`` wires it up.
"""
from __future__ import annotations

import re
import time
from typing import Callable, NamedTuple

from osmbot.notify import telegram

POLL_EVERY = 10  # seconds between two looks at Telegram
STALE = 120  # seconds: an older command is ignored (the PC may have been off) and then marked as read
MIN_NAME = 3  # letters of the PC's name that make it unambiguous enough
KEEP = 200  # update ids remembered in memory


class Command(NamedTuple):
    update_id: int
    kind: str  # "stop" | "status"
    target: str  # the PC's name (or part of it) as written; "" when none


def _words(message: dict) -> tuple[str, str] | None:
    parts = (message.get("text") or "").strip().split()
    if not parts or not parts[0].startswith("/"):
        return None
    return re.sub(r"@\w+$", "", parts[0]).casefold(), " ".join(parts[1:]).strip()


def parse(updates: list[dict], chat_id: int | str, now: float, since: float = 0.0) -> list[Command]:
    """The fresh ``/parar`` and ``/estado`` from the owner's own chat, oldest first."""
    found = []
    for update in updates or []:
        message = update.get("message") or {}
        chat = message.get("chat") or {}
        if str(chat.get("id")) != str(chat_id) or chat.get("type") != "private":
            continue  # anybody else: ignored without an answer
        sent = message.get("date") or 0
        if sent < since or now - sent > STALE:
            continue
        words = _words(message)
        if words and words[0] in ("/parar", "/estado"):
            found.append(Command(update.get("update_id", 0), "stop" if words[0] == "/parar" else "status", words[1]))
    return found


def pc_name(saved: str | None = None, fallback: str | None = None) -> str:
    """How this PC is called in the messages and in ``/parar <name>`` (owner, 2026-11-20: PCTrabalho, PCCasa): the
    name kept in ``config.json`` (``nome_pc``, set in Definições → Telegram…), else the network name."""
    from osmbot.i18n import get_pref
    from osmbot.logs import machine

    name = re.sub(r"\s+", "", saved if saved is not None else str(get_pref("nome_pc", "") or ""))
    return name or fallback or machine()


def addressed(target: str, machine: str) -> bool:
    """Whether ``/parar <target>`` is for this PC: the name, or part of it (at least ``MIN_NAME`` letters)."""
    target = (target or "").strip().casefold()
    return len(target) >= MIN_NAME and target in machine.casefold()


def stale_offset(updates: list[dict], now: float) -> int | None:
    """The newest update id old enough to be marked as read (Telegram forgets all up to it); None when none is."""
    old = [u.get("update_id", 0) for u in updates or []
           if now - ((u.get("message") or {}).get("date") or 0) > STALE]
    return max(old) if old else None


def _span(seconds: float | None) -> str:
    if seconds is None:
        return "parado"
    minutes = int(seconds // 60)
    return f"a trabalhar há {minutes // 60} h {minutes % 60:02d} min"


class Commander:
    def __init__(self, config: Callable[[], dict], fetch, ack, send, machine: str, uptime: Callable[[], float | None],
                 stop: Callable[[], None], now=time.time, since: float = 0.0):
        self.config, self.fetch, self.ack, self.send = config, fetch, ack, send
        self.machine, self.uptime, self.stop, self.now, self.since = machine, uptime, stop, now, since
        self.seen: list[int] = []

    def poll_once(self) -> None:
        config = self.config()
        if not telegram.connected(config):
            return
        token, chat = config["token"], config["chat_id"]
        updates = self.fetch(token)
        now = self.now()
        for command in parse(updates, chat, now, self.since):
            if command.update_id in self.seen:
                continue
            self.seen = (self.seen + [command.update_id])[-KEEP:]
            if command.kind == "status":
                self.send(token, chat, f"💻 {self.machine}: {_span(self.uptime())}\nPara fechar: /parar {self.machine}")
            elif not command.target:
                self.send(token, chat, f"Diz qual o PC: /parar {self.machine}")
            elif addressed(command.target, self.machine):
                self.send(token, chat, f"🔴 {self.machine}: a fechar (acaba o passo em curso)")
                self.stop()
        old = stale_offset(updates, now)
        if old is not None:
            self.ack(token, old)


def default(machine: str, uptime, stop, since: float | None = None) -> Commander:
    """The commander of this PC: the real Telegram calls (short polls: they never collide with another PC's)."""
    def fetch(token: str) -> list[dict]:
        return telegram._call(token, "getUpdates", {"timeout": 0, "allowed_updates": ["message"]}) or []

    def ack(token: str, update_id: int) -> None:
        telegram._call(token, "getUpdates", {"offset": update_id + 1, "timeout": 0})

    return Commander(telegram.load, fetch, ack, telegram.send, machine, uptime, stop,
                     since=time.time() if since is None else since)
