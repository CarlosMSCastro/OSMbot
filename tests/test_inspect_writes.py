import json

from osmbot.game import browser


def test_view_shows_short_values_but_never_secret_looking_ones():
    body = {"missionId": 7, "actionId": "DailyLoginEnergy_1", "access_token": "abc", "email": "a@b.c",
            "note": "x" * 50, "nested": {"reward": {"type": 2, "value": 10}, "sessionId": "zzz"}}
    view = browser._view(body)
    assert view["missionId"] == 7 and view["actionId"] == "DailyLoginEnergy_1"
    assert view["access_token"] == "str" and view["email"] == "str" and view["note"] == "str"
    assert view["nested"]["reward"] == {"type": 2, "value": 10} and view["nested"]["sessionId"] == "str"


def test_form_bodies_follow_the_same_rule():
    view = browser._body_view("rewardId=12&refresh_token=secret&playerId=9", "application/x-www-form-urlencoded")
    assert view == {"rewardId": "12", "refresh_token": "str", "playerId": "9"}
    assert browser._body_view("not json {", "application/json") is None


class FakeRequest:
    def __init__(self, method, body=""):
        self.method, self.post_data, self.headers = method, body, {"content-type": "application/x-www-form-urlencoded", "x-a": "1"}


class FakeResponse:
    def __init__(self, method, url, body, status=200, post=""):
        self.request, self.url, self.status = FakeRequest(method, post), url, status
        self.headers, self._body = {"content-type": "application/json"}, body

    def text(self):
        return json.dumps(self._body)


def test_inspect_writes_logs_each_request_as_it_happens(monkeypatch, tmp_path, capsys):
    state = tmp_path / "session.json"
    state.write_text("{}")
    log = tmp_path / "inspect-writes.log"
    api = "https://web-api.onlinesoccermanager.com/api/v1/"
    events = [
        FakeResponse("GET", api + "user/dailylogin", {"isClaimable": True, "consecutiveLoginCount": 15}),
        FakeResponse("GET", api + "user/dailylogin", {"isClaimable": True}),  # repeated read: noted once
        FakeResponse("GET", api + "leagues/1/teams/2/players", [{"name": "Someone"}]),
        FakeResponse("POST", api + "user/dailylogin/claim", {"reward": {"id": 3}}, post="actionId=DailyLoginEnergy_1"),
        FakeResponse("POST", "https://web-api.onlinesoccermanager.com/api/tokenRefresh", {"x": 1}),  # never logged
        FakeResponse("POST", "https://elsewhere.example.com/collect", {"x": 1}),  # not the game
    ]

    class Context:
        def on(self, name, handler):
            for event in events:
                handler(event)

    seen_during = {}

    def fake_session(state_file, url, message, on_context=None, **kwargs):
        on_context(Context())
        seen_during["log"] = log.read_text(encoding="utf-8")  # already on disk before the window is closed

    monkeypatch.setattr(browser, "_run_session", fake_session)
    browser.inspect_writes(state, "http://x", log)
    text = log.read_text(encoding="utf-8")
    assert seen_during["log"] == text
    assert text.count("(leitura) GET") == 2 and "consecutiveLoginCount': 15" in text  # state endpoint shown with values
    assert "players" in text and "Someone" not in text  # other reads: address only
    assert "ESCRITA POST " + api + "user/dailylogin/claim -> 200" in text and "'actionId': 'DailyLoginEnergy_1'" in text
    assert "tokenRefresh" not in text and "elsewhere" not in text
    assert "Gravado em" in capsys.readouterr().out


def test_short_lists_are_shown_in_full_and_long_ones_by_their_first_item():
    eight = [{"missionId": i, "isClaimed": False} for i in range(8)]
    assert browser._view(eight) == eight
    long = [{"id": i} for i in range(30)]
    assert browser._view(long) == ["30 items", {"id": 0}]
