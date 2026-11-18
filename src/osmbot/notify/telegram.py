"""The Telegram side of the notifications (D-110): one bot per user, made with @BotFather. The token is the bot's
password: it lives only in this PC's ``~/.osmbot/config.json`` (block ``telegram``) and is never logged or put in an
error message. Everything that touches the network goes through ``_call`` (HTTPS to api.telegram.org, no extra
dependency); the rest is pure and tested.
"""
from __future__ import annotations

import json
import re
import secrets
import urllib.error
import urllib.request

API = "https://api.telegram.org/bot{token}/{method}"
TOKEN = re.compile(r"^\d{6,}:[A-Za-z0-9_-]{30,}$")  # 123456789:AAH... as @BotFather gives it
TIMEOUT = 10


class TelegramError(Exception):
    """A failed call; the text never carries the token."""


def valid_token(token: str) -> bool:
    return bool(TOKEN.match((token or "").strip()))


def new_code() -> str:
    """The one-time word the user's Start carries (``t.me/<bot>?start=<code>``): letters, digits, _ and - only."""
    return secrets.token_urlsafe(8)


def link(username: str, code: str) -> str:
    return f"https://t.me/{username}?start={code}"


def chat_from_updates(updates: list[dict], code: str) -> tuple[int, int] | None:
    """(chat_id, update_id) of the newest private ``/start <code>`` among ``updates``; None when it has not come."""
    found = None
    for update in updates or []:
        message = update.get("message") or {}
        chat = message.get("chat") or {}
        parts = (message.get("text") or "").split()
        if chat.get("type") == "private" and len(parts) == 2 and parts[0] == "/start" and parts[1] == code:
            found = (chat["id"], update.get("update_id", 0))
    return found


def _call(token: str, method: str, payload: dict | None = None, opener=urllib.request.urlopen) -> object:
    request = urllib.request.Request(API.format(token=token, method=method), method="POST",
                                     data=json.dumps(payload or {}).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
    try:
        with opener(request, timeout=TIMEOUT) as answer:
            body = json.loads(answer.read().decode("utf-8"))
    except urllib.error.HTTPError as error:  # 401 = wrong token, 404 = no such bot
        raise TelegramError(f"o Telegram respondeu {error.code}") from None
    except (urllib.error.URLError, OSError, ValueError):
        raise TelegramError("sem ligação ao Telegram") from None
    if not body.get("ok"):
        raise TelegramError(str(body.get("description") or "o Telegram recusou"))
    return body.get("result")


def bot_username(token: str, opener=urllib.request.urlopen) -> str:
    """The bot's @username (getMe): proves the token works."""
    return str(_call(token.strip(), "getMe", opener=opener).get("username") or "")


def wait_for_start(token: str, code: str, opener=urllib.request.urlopen) -> int | None:
    """The chat id of whoever pressed Start with ``code`` (None: not yet). Marks the updates as read once found."""
    updates = _call(token, "getUpdates", {"timeout": 0, "allowed_updates": ["message"]}, opener) or []
    found = chat_from_updates(updates, code)
    if found:
        _call(token, "getUpdates", {"offset": found[1] + 1, "timeout": 0}, opener)
        return found[0]
    return None


CAPTION = 1000  # a photo's caption holds 1024 characters


def send(token: str, chat_id: int | str, text: str, opener=urllib.request.urlopen, *, html: bool = False,
         photo: str | None = None) -> None:
    """A message; html: bold, code and links as Telegram's HTML. photo: a public image URL (the club's logo) shown
    with the text as its caption; if Telegram cannot take the picture, the text goes alone."""
    extra = {"parse_mode": "HTML"} if html else {}
    if photo and len(text) <= CAPTION:
        try:
            _call(token, "sendPhoto", {"chat_id": chat_id, "photo": photo, "caption": text, **extra}, opener)
            return
        except TelegramError:
            pass
    _call(token, "sendMessage", {"chat_id": chat_id, "text": text, "disable_web_page_preview": True, **extra}, opener)


# --- what this PC keeps (config.json, block "telegram") -----------------------------------------------------------
def load() -> dict:
    from osmbot.i18n import get_pref

    saved = get_pref("telegram", {})
    return saved if isinstance(saved, dict) else {}


def save(token: str | None, chat_id: int | None, alerts: dict | None = None) -> None:
    from osmbot.i18n import set_pref

    set_pref("telegram", {"token": token, "chat_id": chat_id, "avisos": alerts if alerts is not None else load().get("avisos", {})})


def connected(config: dict | None = None) -> bool:
    config = load() if config is None else config
    return bool(config.get("token") and config.get("chat_id"))
