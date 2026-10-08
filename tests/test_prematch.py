from osmbot.game import prematch
from osmbot.prematch.policy import LEAD, friendly_choices, in_window, needs_analysis, needs_friendly, next_opponent

TEAM = {"id": 1, "name": "Club"}
LEAGUE = "leagues/9"
BASE = f"{LEAGUE}/teams/1"
NOW = 1_000_000.0


def step(type_, progress, completion=1, enabled=True):
    return {"type": type_, "progressAmount": progress, "completionAmount": completion, "enabled": enabled}


def match(week, home, away, kind=0):
    return {"weekNr": week, "homeTeamId": home, "awayTeamId": away, "matchType": kind}


def test_only_in_the_last_4_hours_before_the_match():
    assert not in_window(NOW + LEAD + 60, NOW)
    assert in_window(NOW + LEAD, NOW)
    assert in_window(NOW + 60, NOW)
    assert not in_window(NOW - 60, NOW)
    assert not in_window(None, NOW)


def test_a_friendly_is_needed_only_while_the_checklist_point_is_open():
    assert needs_friendly([step(7, 0)])
    assert not needs_friendly([step(7, 1)])
    assert not needs_friendly([step(7, 2)])  # the owner played two
    assert not needs_friendly([step(7, 0, enabled=False)])
    assert not needs_friendly([])


def test_an_analyst_sent_this_week_counts_while_still_working():
    assert needs_analysis([step(5, 0)], [], 14)
    assert not needs_analysis([step(5, 0)], [{"weekNr": 14}], 14)
    assert needs_analysis([step(5, 0)], [{"weekNr": 13}], 14)
    assert not needs_analysis([step(5, 1)], [], 14)


def test_next_opponent_is_the_next_official_match_and_unclear_weeks_are_left_alone():
    matches = [match(14, 1, 19, kind=1), match(14, 1, 4, kind=2), match(15, 1, 6), match(16, 8, 1)]
    assert next_opponent(matches, 1, 14) == 6
    assert next_opponent(matches, 1, 15) == 8
    assert next_opponent(matches, 1, 16) is None
    assert next_opponent(matches + [match(15, 3, 1, kind=1)], 1, 14) is None


def test_friendly_opponents_exclude_the_club_and_this_weeks_friendlies():
    teams = [{"id": i} for i in range(1, 6)]
    matches = [match(14, 1, 4, kind=2), match(14, 2, 1, kind=2), match(13, 1, 3, kind=2), match(14, 3, 5, kind=2)]
    assert friendly_choices(teams, matches, 1, 14) == [3, 5]


class FakeClient:
    def __init__(self, steps, match_in=3600, coins=100, sent=None, post_status=200):
        self.steps, self.coins, self.sent, self.post_status = steps, coins, sent, post_status
        self.match = NOW + match_in
        self.posts = []

    def get(self, path):
        teams = [{"id": i, "name": f"T{i}"} for i in range(1, 5)]
        data = {
            f"{BASE}/timers": [{"type": 14, "finishedTimestamp": self.match}],
            LEAGUE: {"weekNr": 14},
            f"{BASE}/matchpreparation": {"steps": self.steps},
            "user/bosscoinwallet": {"amount": self.coins},
            f"{LEAGUE}/teams": teams,
            f"{LEAGUE}/matches/filter": [match(14, 1, 2, kind=2), match(15, 1, 3)],
        }
        if path == f"{BASE}/spyinstructions":
            return (200, self.sent) if self.sent else (404, "")
        return 200, data[path]

    def post(self, path, form):
        self.posts.append((path, form))
        return self.post_status, {"homeTeamId": 1, "homeGoals": 2, "awayGoals": 0}


class FirstRng:
    def shuffle(self, items):
        pass


def prepare(client, confirm=True):
    lines = []
    result = prematch.prepare_club(client, TEAM, BASE, confirm, NOW, log=lines.append, rng=FirstRng())
    return result, lines


def test_nothing_before_the_4_hours_and_it_wakes_up_then():
    client = FakeClient([step(7, 0), step(5, 0)], match_in=LEAD + 600)
    assert prepare(client)[0] == (0, NOW + 600)
    assert client.posts == []


def test_plays_one_friendly_and_sends_the_analyst_to_the_next_opponent():
    client = FakeClient([step(7, 0), step(5, 0)])
    (failures, _), lines = prepare(client)
    assert failures == 0
    assert client.posts == [(f"{BASE}/matches", {"opponentId": 3, "productId": 62}),
                            (f"{BASE}/spyinstructions", {"instructionTeamId": 3, "timerGameSettingId": 60})]
    assert prematch.COUNTS == {"friendlies": 1, "analyses": 1}
    assert "Amigável: Club 2-0 T3" in lines


def test_what_the_owner_already_did_is_left_alone():
    client = FakeClient([step(7, 1), step(5, 0)], sent=[{"weekNr": 14}])
    assert prepare(client)[0] == (0, None)
    assert client.posts == []


def test_without_coins_no_friendly_but_the_analysis_still_goes():
    client = FakeClient([step(7, 0), step(5, 0)], coins=3)
    _, lines = prepare(client)
    assert [path for path, _ in client.posts] == [f"{BASE}/spyinstructions"]
    assert any("sem boss coins" in line for line in lines)


def test_simulation_writes_nothing():
    client = FakeClient([step(7, 0), step(5, 0)])
    _, lines = prepare(client, confirm=False)
    assert client.posts == []
    assert "Club: faria 1 amigável contra T3" in lines


def test_a_refused_friendly_tries_another_opponent_and_a_server_error_is_a_failure():
    client = FakeClient([step(7, 0), step(5, 1)], post_status=400)
    assert prepare(client)[0] == (0, None)
    assert [form["opponentId"] for _, form in client.posts] == [3, 4]
    client = FakeClient([step(7, 0), step(5, 1)], post_status=500)
    assert prepare(client)[0] == (1, None)
