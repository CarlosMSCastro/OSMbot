from pathlib import Path

from osmbot.game import ads


class FakePage:
    def __init__(self):
        self.handlers = {}

    def on(self, event, handler):
        self.handlers[event] = handler

    def screenshot(self, path):
        Path(path).write_bytes(b"png")


class Message:
    def __init__(self, kind, text):
        self.type, self.text = kind, text


class Request:
    method, url, failure = "GET", "https://ads.example.com/x.js?token=SECRET", "net::ERR_BLOCKED_BY_CLIENT"


class Answer:
    status, request = 403, Request()
    url = "https://api.example.com/v1/videos/start?key=SECRET#frag"


def test_a_failure_keeps_a_screenshot_and_what_the_page_and_the_network_did(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    page = FakePage()
    ads.track(page)
    page.handlers["console"](Message("error", "boom"))
    page.handlers["console"](Message("log", "ignored"))
    page.handlers["requestfailed"](Request())
    page.handlers["response"](Answer())
    page.handlers["response"](type("Ok", (), {"status": 200, "request": Request(), "url": "https://x/y"})())
    ads.save_failure(page, "loja")
    notes = next((tmp_path / ".osmbot" / "failures").glob("*-loja.txt")).read_text(encoding="utf-8")
    lines = [line.split(" ", 1)[1] for line in notes.splitlines()]
    assert lines == ["console.error: boom", "falhou GET https://ads.example.com/x.js: net::ERR_BLOCKED_BY_CLIENT",
                     "403 GET https://api.example.com/v1/videos/start"]
    assert "SECRET" not in notes  # query strings never reach the file
    assert next((tmp_path / ".osmbot" / "failures").glob("*-loja.png")).read_bytes() == b"png"
