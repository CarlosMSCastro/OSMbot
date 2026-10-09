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


def test_stale_app_version_is_reported_clearly(tmp_path):
    state, codes = make(tmp_path, time.time() - 10, time.time() + 86400)
    fake = Fake((400, b'{"modelState":{"AppVersion":["You must update the app"]}}'))
    with pytest.raises(NeedsBrowserLogin, match="atualizou"):
        OsmClient(state, codes, fake).get("x")


def test_refresh_sends_saved_site_headers(tmp_path):
    state, codes = make(tmp_path, time.time() - 10, time.time() + 86400)
    data = json.loads(codes.read_text())
    data["headers"] = {"appversion": "1.2.3"}
    codes.write_text(json.dumps(data))
    answer, _ = renewal(tmp_path)
    fake = Fake(answer, (200, b"{}"))
    OsmClient(state, codes, fake).get("x")
    assert fake.requests[0].get_header("Appversion") == "1.2.3"


def test_a_client_takes_the_tokens_another_client_already_renewed_instead_of_using_its_old_ones(tmp_path):
    state, codes = make(tmp_path, time.time() - 10, time.time() + 86400)
    old = OsmClient(state, codes, Fake())  # created before the renewal, holds the old tokens in memory
    answer, new = renewal(tmp_path)
    OsmClient(state, codes, Fake(answer)).refresh()  # someone else renews and saves
    fake = Fake((200, b"{}"))
    old._transport = fake
    old.get("x")
    assert len(fake.requests) == 1  # no second renewal with the stale refresh_token
    assert fake.requests[0].get_header("Authorization") == f"Bearer {new['access_token']}"


def test_a_rejected_token_is_renewed_even_if_it_looks_fresh(tmp_path):
    state, codes = make(tmp_path, time.time() + 600, time.time() + 86400)
    answer, new = renewal(tmp_path)
    fake = Fake((401, b""), answer, (200, b'{"ok": 1}'))
    assert OsmClient(state, codes, fake).get("x") == (200, {"ok": 1})
    assert fake.requests[2].get_header("Authorization") == f"Bearer {new['access_token']}"


def test_a_video_browser_never_overwrites_newer_tokens_with_older_ones(tmp_path):
    from osmbot.game.client import save_browser_session

    state, _ = make(tmp_path, time.time() + 1000, time.time() + 86400)
    older = [{"name": "access_token", "value": jwt(time.time() + 500)}, {"name": "refresh_token", "value": jwt(1)}]
    newer = [{"name": "access_token", "value": jwt(time.time() + 1200)}, {"name": "refresh_token", "value": jwt(2)}]
    assert not save_browser_session(older, state)
    assert save_browser_session(newer, state)
    assert json.loads(state.read_text(encoding="utf-8"))["cookies"] == newer


def test_two_clients_at_the_same_time_renew_only_once(tmp_path):
    """The window reads the board while the bot works: both find the token expired, only one renews."""
    import threading

    state, codes = make(tmp_path, time.time() - 10, time.time() + 86400)
    answer, new = renewal(tmp_path)
    renewals, started = [], threading.Event()

    def transport(request):
        if request.full_url.endswith("/api/tokenRefresh"):
            renewals.append(request)
            started.set()
            time.sleep(0.2)  # the other client arrives while this renewal is on its way
            return answer
        return 200, b"{}"

    clients = [OsmClient(state, codes, transport) for _ in range(2)]
    threads = [threading.Thread(target=client.get, args=("x",)) for client in clients]
    threads[0].start()
    started.wait(2)
    threads[1].start()
    for thread in threads:
        thread.join(5)
    assert len(renewals) == 1
    assert all(client._token("access_token") == new["access_token"] for client in clients)


def test_a_401_after_another_client_renewed_takes_its_tokens_instead_of_renewing_again(tmp_path):
    state, codes = make(tmp_path, time.time() + 600, time.time() + 86400)
    answer, new = renewal(tmp_path)
    late = OsmClient(state, codes, None)
    OsmClient(state, codes, Fake(answer)).refresh(force=True)  # the other one renewed: the old token stops working
    fake = Fake((401, b""), (200, b'{"ok": 1}'))
    late._transport = fake
    assert late.get("x") == (200, {"ok": 1})
    assert len(fake.requests) == 2 and fake.requests[1].get_header("Authorization") == f"Bearer {new['access_token']}"


def test_the_https_settings_are_built_once(monkeypatch):
    from osmbot.game import client

    built = []
    monkeypatch.setattr(client, "_ssl_context", None)
    monkeypatch.setattr(client.ssl, "create_default_context", lambda **_: built.append(1) or object())
    assert client._context() is client._context() and len(built) == 1
