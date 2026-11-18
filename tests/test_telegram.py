import io
import json
import urllib.error

import pytest

from osmbot.notify import telegram as tg

TOKEN = "123456789:" + "A" * 35


class Answer(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def opener_for(*bodies):
    calls = []
    queue = list(bodies)

    def opener(request, timeout=None):
        calls.append((request.full_url, json.loads(request.data)))
        return Answer(json.dumps(queue.pop(0)).encode())

    opener.calls = calls
    return opener


def test_a_token_looks_like_botfathers_and_a_code_is_url_safe():
    assert tg.valid_token(TOKEN) and tg.valid_token(f"  {TOKEN} ")
    assert not tg.valid_token("") and not tg.valid_token("abc") and not tg.valid_token("123:short")
    assert tg.link("meu_bot", "abc-_9") == "https://t.me/meu_bot?start=abc-_9"
    assert tg.new_code() != tg.new_code() and all(c.isalnum() or c in "-_" for c in tg.new_code())


def test_the_chat_is_the_one_that_pressed_start_with_our_code():
    private = lambda text, chat=7, kind="private", uid=1: {"update_id": uid, "message": {"text": text, "chat": {"id": chat, "type": kind}}}
    assert tg.chat_from_updates([private("/start xyz", uid=5)], "xyz") == (7, 5)
    assert tg.chat_from_updates([private("/start other")], "xyz") is None
    assert tg.chat_from_updates([private("/start xyz", kind="group")], "xyz") is None
    assert tg.chat_from_updates([private("olá")], "xyz") is None and tg.chat_from_updates([], "xyz") is None


def test_bot_username_wait_for_start_and_send_use_the_api():
    opener = opener_for({"ok": True, "result": {"username": "meu_bot"}})
    assert tg.bot_username(TOKEN, opener) == "meu_bot"
    assert opener.calls[0][0].endswith(f"/bot{TOKEN}/getMe")
    opener = opener_for({"ok": True, "result": [{"update_id": 9, "message": {"text": "/start c1", "chat": {"id": 42, "type": "private"}}}]},
                        {"ok": True, "result": []})
    assert tg.wait_for_start(TOKEN, "c1", opener) == 42
    assert opener.calls[1][1]["offset"] == 10  # the update is marked as read
    assert tg.wait_for_start(TOKEN, "c1", opener_for({"ok": True, "result": []})) is None
    sent = opener_for({"ok": True, "result": {}})
    tg.send(TOKEN, 42, "olá", sent)
    assert sent.calls[0][1] == {"chat_id": 42, "text": "olá", "disable_web_page_preview": True}


def test_errors_never_carry_the_token():
    def refuses(request, timeout=None):
        raise urllib.error.HTTPError(request.full_url, 401, "Unauthorized", {}, None)

    def offline(request, timeout=None):
        raise urllib.error.URLError("no route")

    for opener in (refuses, offline, opener_for({"ok": False, "description": "Bad Request: chat not found"})):
        with pytest.raises(tg.TelegramError) as error:
            tg.send(TOKEN, 1, "x", opener)
        assert TOKEN not in str(error.value) and "bot" not in str(error.value).split(":")[0]


def test_connected_needs_the_token_and_the_chat(monkeypatch):
    assert not tg.connected({}) and not tg.connected({"token": TOKEN}) and tg.connected({"token": TOKEN, "chat_id": 1})


def test_the_qr_matrix_is_square_with_a_white_border():
    from osmbot.notify.qr import BORDER, matrix

    grid = matrix(tg.link("meu_bot", "abc-_9"))
    assert len(grid) == len(grid[0]) and len(grid) > 2 * BORDER
    assert not any(grid[0]) and not any(grid[-1]) and not any(row[0] or row[-1] for row in grid)
    assert any(any(row) for row in grid)
    assert matrix("a") != matrix("b")


def test_send_in_html_with_a_logo_and_falls_back_to_text_alone():
    both = opener_for({"ok": True, "result": {}})
    tg.send(TOKEN, 1, "<b>x</b>", both, html=True, photo="https://x/l.png")
    assert both.calls[0][0].endswith("/sendPhoto")
    assert both.calls[0][1] == {"chat_id": 1, "photo": "https://x/l.png", "caption": "<b>x</b>", "parse_mode": "HTML"}
    fallback = opener_for({"ok": False, "description": "wrong file"}, {"ok": True, "result": {}})
    tg.send(TOKEN, 1, "t", fallback, photo="https://x/l.png")
    assert [c[0].rsplit("/", 1)[1] for c in fallback.calls] == ["sendPhoto", "sendMessage"]
    long_text = opener_for({"ok": True, "result": {}})
    tg.send(TOKEN, 1, "x" * 1100, long_text, photo="https://x/l.png")  # too long for a caption: no photo
    assert long_text.calls[0][0].endswith("/sendMessage")
