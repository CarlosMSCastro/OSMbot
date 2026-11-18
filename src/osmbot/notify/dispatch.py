"""Where the bot's lines and the board's readings become Telegram messages (D-110). ``Dispatcher`` is the whole logic
with the sending, the clock and the memory of what was sent injected, so it is tested without a network. The bot
uses one ``Dispatcher`` (``default()``); nothing here ever raises into the bot or blocks it (sending runs in a thread)."""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path

from osmbot.notify import rules, telegram

SENT_FILE = Path.home() / ".osmbot" / "notificacoes.json"
KEEP = 400  # keys remembered between runs (a restart does not repeat what was already sent)
ERROR_EVERY = 300  # seconds: at most one error message in this time (a failing pass repeats its lines)


class Dispatcher:
    def __init__(self, send, config, now=time.time, store: Path | None = SENT_FILE, background: bool = True):
        self.send, self.config, self.now, self.store, self.background = send, config, now, store, background
        self.lock = threading.Lock()
        self.last_error = 0.0
        self.failures: dict[str, list[float]] = {}  # category -> when it failed lately (the ones the bot retries)
        self.repeated_at: dict[str, float] = {}
        self.logos: dict[str, str] = {}  # club name -> its logo's URL, from the board's last reading
        self.sent: list[str] = self._load()

    def _load(self) -> list[str]:
        try:
            data = json.loads(self.store.read_text(encoding="utf-8")) if self.store else []
            return [k for k in data if isinstance(k, str)][-KEEP:]
        except (OSError, ValueError):
            return []

    def _remember(self) -> None:
        if self.store:
            try:
                self.store.parent.mkdir(parents=True, exist_ok=True)
                self.store.write_text(json.dumps(self.sent[-KEEP:]), encoding="utf-8")
            except OSError:
                pass

    def line(self, message: str, is_error: bool = False) -> None:
        text = message.lstrip(chr(7)).lstrip("! ").strip()
        alerts = [rules.from_log_line(message, is_error)]
        if is_error and not rules.is_critical(text):
            alerts.append(self._repeat(text))
        self._go(alerts)

    def _repeat(self, text: str) -> rules.Alert | None:
        """An error the bot retries by itself reaches the phone only when it keeps failing."""
        what, now = rules.category(text), self.now()
        times = [t for t in self.failures.get(what, []) if now - t < rules.REPEAT_WINDOW] + [now]
        self.failures[what] = times
        if len(times) < rules.REPEAT_COUNT or now - self.repeated_at.get(what, 0) < rules.REPEAT_COOLDOWN:
            return None
        self.repeated_at[what] = now
        return rules.repeated(what, len(times), text[:160], now)

    def snapshot(self, snapshot: dict | None) -> None:
        """Each club's pre-match warning (the last hour) and the opponent's camp or secret training."""
        alerts = []
        for club in (snapshot or {}).get("clubs") or []:
            if club.get("name") and club.get("logo"):
                self.logos[club["name"]] = club["logo"]
            alerts += [rules.pregame(club, self.now()), rules.opponent(club)]
        self._go(alerts)

    def _go(self, alerts: list) -> None:
        config = self.config()
        if not telegram.connected(config):
            return
        with self.lock:
            sent = set(self.sent)
            todo = [a for a in rules.due(alerts, config.get("avisos"), sent)]
            if any(a.kind == "erro" for a in todo):  # one error message every few minutes, not one per line
                if self.now() - self.last_error < ERROR_EVERY:
                    todo = [a for a in todo if a.kind != "erro"]
                    sent = {*self.sent, *(a.key for a in todo)}
                else:
                    self.last_error = self.now()
            self.sent += [a.key for a in todo]
            if todo:
                self._remember()
        if todo:
            self._deliver(config, todo)

    def _deliver(self, config: dict, alerts: list) -> None:
        def run() -> None:
            for alert in alerts:
                try:
                    self.send(config["token"], config["chat_id"], alert.html or alert.text, html=bool(alert.html),
                              photo=self.logos.get(alert.club or ""))
                except Exception:  # never into the bot; the next fact tries again
                    pass

        if self.background:
            threading.Thread(target=run, daemon=True).start()
        else:
            run()


_default: Dispatcher | None = None


def default() -> Dispatcher:
    global _default
    if _default is None:
        _default = Dispatcher(telegram.send, telegram.load)
    return _default
