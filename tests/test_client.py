import base64
import json
import time

import pytest

from osmbot.game.client import NeedsBrowserLogin, OsmClient


def jwt(exp: float) -> str:
    seg = lambda d: base64.urlsafe_b64encode(json.dumps(d).encode()).decode().rstrip("=")
    return f"{seg({'alg': 'x'})}.{seg({'exp': exp})}.sig"


def make(tmp_path, access_exp, refresh_exp, with_codes=True):
    state = tmp_path / "session.json"
    state.write_text(json.dumps({"cookies": [
        {"name": "access_token", "value": jwt(access_exp)},
        {"name": "refresh_token", "value": jwt(refresh_exp)},
    ]}), encoding="utf-8")
    codes = tmp_path / "client.json"
    if with_codes:
        codes.write_text(json.dumps({"client_id": "id", "client_secret": "sec"}), encoding="utf-8")
    return state, codes


class Fake:
    def __init__(self, *answers):
        self.answers, self.requests = list(answers), []

    def __call__(self, request):
        self.requests.append(request)
        return self.answers.pop(0)


def renewal(tmp_path):
    new = {"access_token": jwt(time.time() + 1200), "refresh_token": jwt(time.time() + 7 * 86400)}
    return (200, json.dumps(new).encode()), new


def test_fresh_token_skips_refresh(tmp_path):
    state, codes = make(tmp_path, time.time() + 600, time.time() + 86400)
    fake = Fake((200, b'{"ok": 1}'))
    assert OsmClient(state, codes, fake).get("x") == (200, {"ok": 1})
    assert len(fake.requests) == 1
    assert fake.requests[0].get_header("Authorization").startswith("Bearer ")


def test_expired_token_refreshes_and_saves(tmp_path):
    state, codes = make(tmp_path, time.time() - 10, time.time() + 86400)
    answer, new = renewal(tmp_path)
    fake = Fake(answer, (200, b"{}"))
    OsmClient(state, codes, fake).get("x")
    assert fake.requests[0].full_url.endswith("/api/tokenRefresh")
    saved = {c["name"]: c["value"] for c in json.loads(state.read_text())["cookies"]}
    assert saved == new


def test_401_triggers_one_refresh_and_retry(tmp_path):
    state, codes = make(tmp_path, time.time() + 600, time.time() + 86400)
    answer, _ = renewal(tmp_path)
    fake = Fake((401, b""), answer, (200, b"{}"))
    assert OsmClient(state, codes, fake).get("x")[0] == 200


def test_dead_refresh_token_needs_browser(tmp_path):
    state, codes = make(tmp_path, time.time() - 10, time.time() - 10)
    with pytest.raises(NeedsBrowserLogin):
        OsmClient(state, codes, Fake()).get("x")


def test_missing_client_codes_needs_browser(tmp_path):
    state, codes = make(tmp_path, time.time() - 10, time.time() + 86400, with_codes=False)
    with pytest.raises(NeedsBrowserLogin):
        OsmClient(state, codes, Fake()).get("x")
