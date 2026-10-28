import pytest

from osmbot.game import prematch
from osmbot.prematch.policy import LEAD, friendly_choices, friendlies_missing, in_window, needs_analysis, next_opponent


@pytest.fixture(autouse=True)
def _no_scouting(monkeypatch):
    """These tests are about the friendlies and the opponent's analysis; the analyst going round the league has its
    own tests (test_scouting.py)."""
    monkeypatch.setattr(prematch, "_scout", lambda *args, **kwargs: (0, None))

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


def test_four_friendlies_before_each_match_the_owners_included():
    assert friendlies_missing([], 1, 14) == 4
    played = [match(14, 1, 2, kind=2), match(14, 3, 1, kind=2), match(13, 1, 4, kind=2), match(14, 1, 5)]
    assert friendlies_missing(played, 1, 14) == 2  # last round's and the league match don't count
    assert friendlies_missing(played + [match(14, 1, 6, kind=2), match(14, 7, 1, kind=2)], 1, 14) == 0


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


def test_friendly_opponents_exclude_the_next_official_opponent():
    teams = [{"id": i} for i in range(1, 6)]
    assert friendly_choices(teams, [match(15, 5, 1)], 1, 14) == [2, 3, 4]  # the game refuses it (400)
    assert friendly_choices(teams, [match(15, 5, 1), match(15, 1, 3, kind=1)], 1, 14) == [2, 3, 4, 5]  # unclear: none left out


ANALYSED = [{"weekNr": 14, "instructionTeamId": 3}]  # the analyst already went to the opponent this round


class FakeClient:
    def __init__(self, steps, match_in=3600, coins=100, sent=None, post_status=200, clubs=6, friendlies=1,
                 settings=({"id": 60, "name": "SpyInstructionTimer", "value": 60},), week=14):
        self.steps, self.coins, self.sent, self.post_status, self.week = steps, coins, sent, post_status, week
        self.settings = list(settings)
        self.match = NOW + match_in
        self.clubs, self.friendlies = clubs, friendlies
        self.posts, self.puts = [], []

    def get(self, path):
        teams = [{"id": i, "name": f"T{i}"} for i in range(1, self.clubs + 1)]
        data = {
            f"{BASE}/timers": [{"type": 14, "finishedTimestamp": self.match}],
            LEAGUE: {"weekNr": self.week},
            f"{LEAGUE}/gamesettings": self.settings,
            f"{BASE}/matchpreparation": {"steps": self.steps},
            f"{BASE}/specialists": {"captain": 1, "penalty": 1, "freekick": 1, "corners": 1},
            "user/bosscoinwallet": {"amount": self.coins - 4 * sum(1 for p, _ in self.posts if p.endswith("/matches"))},
            f"{LEAGUE}/teams": teams,
            f"{LEAGUE}/matches/filter": [match(self.week, 1, 2 + i, kind=2) for i in range(self.friendlies)] + [match(15, 1, 3)],
            f"{BASE}/players": [{"id": 50, "name": "J", "position": 2, "statAtt": 1, "statDef": 1, "statOvr": 1,
                                 "trainingProgress": 10 * sum(1 for p, _ in self.posts if p.endswith("/matches"))}],
        }
        if path == f"{BASE}/spyinstructions":
            return (200, self.sent) if self.sent else (404, "")
        return 200, data[path]

    def put(self, path):
        self.puts.append(path)
        return 200, {}

    def post(self, path, form):
        self.posts.append((path, form))
        return self.post_status, {"homeTeamId": 1, "homeGoals": 2, "awayGoals": 0}


class FirstRng:
    def shuffle(self, items):
        pass

    def uniform(self, low, high):
        return low


def prepare(client, confirm=True):
    lines = []
    result = prematch.prepare_club(client, TEAM, BASE, confirm, NOW, log=lines.append, rng=FirstRng())
    return result, lines


def test_nothing_before_the_first_friendly_time_and_it_wakes_up_then():
    client = FakeClient([step(7, 0), step(5, 0)], match_in=16 * 3600 + 600, friendlies=0)
    assert prepare(client)[0] == (0, NOW + 600)
    assert client.posts == []


def test_friendlies_are_spread_over_the_day_and_the_analysis_waits_for_the_4_hours():
    client = FakeClient([step(7, 0), step(5, 0)], match_in=LEAD + 600, friendlies=1)  # 3 due by now, the owner played 1
    assert prepare(client)[0] == (0, NOW + 600)  # back at 4 h: the 4th friendly and the analyst
    assert [path for path, _ in client.posts] == [f"{BASE}/matches"] * 2


def test_friendly_times_before_the_match():
    from osmbot.prematch.policy import friendlies_due, next_friendly_at

    match_time = NOW + 10 * 3600
    assert friendlies_due(match_time, NOW) == 2 and friendlies_due(match_time, match_time - 60) == 4
    assert friendlies_due(match_time, match_time) == 0 and friendlies_due(None, NOW) == 0
    assert next_friendly_at(match_time, NOW, 2) == match_time - 8 * 3600
    assert next_friendly_at(match_time, NOW, 1) is None  # the 2nd is due already
    assert next_friendly_at(match_time, NOW, 4) is None


def test_plays_the_missing_friendlies_and_sends_the_analyst_to_the_next_opponent():
    client = FakeClient([step(7, 1), step(5, 0)])  # the owner played 1: 3 to go
    (failures, _), lines = prepare(client)
    assert failures == 0
    assert client.posts == [(f"{BASE}/matches", {"opponentId": c, "productId": 62}) for c in (4, 5, 6)] +         [(f"{BASE}/spyinstructions", {"instructionTeamId": 3, "timerGameSettingId": 60})]
    assert prematch.COUNTS == {"friendlies": 3, "analyses": 1, "collected": 0}
    assert "Amigável: Club 2-0 T4" in lines  # not T3, the next opponent: the game refuses it


def test_coins_for_only_some_of_the_friendlies():
    client = FakeClient([step(7, 0), step(5, 1)], friendlies=0, coins=9, sent=ANALYSED)
    _, lines = prepare(client)
    assert [form["opponentId"] for _, form in client.posts] == [2, 4]
    assert "! Club: sem boss coins para o amigável (1); 2 de 4 ficam por fazer" in lines


def test_what_the_owner_already_did_is_left_alone():
    client = FakeClient([step(7, 1), step(5, 0)], sent=[{"weekNr": 14}], friendlies=4)
    assert prepare(client)[0] == (0, None)
    assert client.posts == []


def test_in_an_event_the_analyst_takes_the_event_timer_and_is_collected_when_it_ends():
    client = FakeClient([step(7, 4), step(5, 0)], friendlies=4,
                        settings=[{"id": 728, "name": "SpyInstructionTimer", "value": 15}])  # Super Staff, 2026-10-14
    (failures, wake), lines = prepare(client)
    assert client.posts == [(f"{BASE}/spyinstructions", {"instructionTeamId": 3, "timerGameSettingId": 728})]
    assert failures == 0 and wake == NOW + 15 * 60 and "Análise: Club enviou o analista a T3 (15 min)" in lines


def test_without_coins_no_friendly_but_the_analysis_still_goes():
    client = FakeClient([step(7, 0), step(5, 0)], coins=3)
    _, lines = prepare(client)
    assert [path for path, _ in client.posts] == [f"{BASE}/spyinstructions"]
    assert any("sem boss coins" in line for line in lines)


def test_simulation_writes_nothing():
    client = FakeClient([step(7, 0), step(5, 0)])
    _, lines = prepare(client, confirm=False)
    assert client.posts == []
    assert "Club: faria 3 amigável(eis) contra T4, T5, T6" in lines


def test_a_refused_friendly_tries_another_opponent_and_a_server_error_is_a_failure():
    client = FakeClient([step(7, 0), step(5, 1)], post_status=400, clubs=7, sent=ANALYSED)
    assert prepare(client)[0] == (0, None)
    assert [form["opponentId"] for _, form in client.posts] == [4, 5, 6]  # 3 refusals: wait for the next pass
    prepare(client)  # the next pass: the refused clubs are not asked again this round (D-032)
    assert [form["opponentId"] for _, form in client.posts] == [4, 5, 6, 7]
    from osmbot.game import refusals

    refusals.FILE.unlink()
    client = FakeClient([step(7, 0), step(5, 1)], post_status=500, sent=ANALYSED)
    assert prepare(client)[0] == (1, None)


def test_the_analyst_is_collected_when_its_hour_is_over_and_waited_for_before():
    running = [{"id": 5, "weekNr": 14, "countdownTimer": {"finishedTimestamp": NOW + 600, "isClaimed": False}}]
    client = FakeClient([step(7, 1), step(5, 0)], sent=running, friendlies=4)
    assert prepare(client)[0] == (0, NOW + 600) and client.posts == []
    over = [{"id": 5, "weekNr": 14, "countdownTimer": {"finishedTimestamp": NOW - 60, "isClaimed": False}}]
    client = FakeClient([step(7, 1), step(5, 0)], sent=over, friendlies=4)
    (failures, _), lines = prepare(client)
    assert client.puts == ["https://web-api.onlinesoccermanager.com/api/v1.1/leagues/9/teams/1/spyinstructions/5/claim"]
    assert failures == 0 and "Análise: Club levantou o analista" in lines


def test_a_finished_analyst_is_collected_at_any_hour():
    over = [{"id": 5, "weekNr": 14, "countdownTimer": {"finishedTimestamp": NOW - 60, "isClaimed": False}}]
    client = FakeClient([step(7, 0), step(5, 0)], sent=over, match_in=10 * 3600, friendlies=2)
    (failures, wake), lines = prepare(client)
    assert client.puts == ["https://web-api.onlinesoccermanager.com/api/v1.1/leagues/9/teams/1/spyinstructions/5/claim"]
    assert failures == 0 and client.posts == [] and wake == NOW + 2 * 3600  # the 3rd friendly at 8 h before


def test_each_friendly_is_recorded_with_what_it_changed(monkeypatch, tmp_path):
    import json

    from osmbot import logs

    monkeypatch.setattr(logs, "repo_folder", lambda: tmp_path)
    prepare(FakeClient([step(7, 1), step(5, 1)], friendlies=3))  # 1 to go
    path = next((tmp_path / "logs" / logs.machine() / "amigaveis").glob("*.jsonl"))
    row = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    assert row["n_na_jornada"] == 4 and row["resultado"] == "2-0"
    assert row["jogadores"] == [{"id": 50, "nome": "J", "pos": 2, "progresso_antes": 0, "att_antes": 1, "def_antes": 1,
                                 "ovr_antes": 1, "progresso_depois": 10, "att_depois": 1, "def_depois": 1, "ovr_depois": 1}]


def test_eight_friendlies_during_an_intense_friendlies_and_never_after_it_ends():
    from osmbot.prematch.policy import friendlies_due, friendly_deadlines, next_friendly_at

    hour, match = 3600, 2_000_000_000.0
    event = {"nome": "Intense Friendlies", "start": match - 30 * hour, "end": match + 20 * hour}
    other = {"nome": "Training Camp Mania", "start": match - 30 * hour, "end": match + 20 * hour}
    now = match - 15 * hour
    assert friendlies_due(match, now) == 1 and friendlies_due(match, now, [other]) == 1  # 4 a day: 16 h passed
    assert friendlies_due(match, now, [event]) == 1 and friendlies_due(match, match - 9 * hour, [event]) == 4
    assert friendlies_due(match, match - 1, [event]) == 8
    assert next_friendly_at(match, now, 1, [event]) == match - 14 * hour
    ending = {**event, "end": match - 5 * hour}  # the event ends before the match: the rest by 1 h before its end
    assert max(friendly_deadlines(match, now, [ending])) == match - 6 * hour
    assert friendlies_due(match, match - 6 * hour, [ending]) == 8
    later = {**event, "start": match - 2 * hour}  # not started yet: still 4
    assert friendlies_due(match, now, [later]) == 1 and len(friendly_deadlines(match, now, [later])) == 4


def test_in_the_pre_season_the_day_ends_at_the_hour_of_the_first_match():
    from osmbot.prematch.policy import DAY, day_end

    first = NOW + 2 * DAY + 11 * 3600  # 59 h away, weekNr -2 (seen 2026-10-15)
    assert day_end(first, NOW, -2) == NOW + 11 * 3600
    assert day_end(first, NOW, 0) == NOW + 11 * 3600 and day_end(NOW + 3600, NOW, 0) == NOW + 3600
    assert day_end(first, NOW, 14) == NOW + 11 * 3600  # a round the club does not play: the same (D-067, test)
    assert day_end(NOW + 11 * 3600, NOW, 14) == NOW + 11 * 3600  # a match today: the day is the match
    assert day_end(None, NOW, -2) is None


def test_pre_season_friendlies_every_day_and_the_analysis_waits_for_the_match():
    client = FakeClient([step(7, 0), step(5, 0)], match_in=2 * 86400 + LEAD + 600, friendlies=0, week=-2)
    assert prepare(client)[0] == (0, NOW + 600)  # back at 4 h before the end of the day for the 4th
    assert [path for path, _ in client.posts] == [f"{BASE}/matches"] * 3


def test_the_trainingcamp_terror_brings_8_friendlies_too():
    from osmbot.prematch.policy import friendly_event

    now = 1000.0
    event = {"nome": "Trainingcamp Terror", "start": now - 10, "end": now + 10}
    assert friendly_event([event], now) is event
    assert friendly_event([{**event, "nome": "Training Camp Terror"}], now) is not None
    assert friendly_event([{**event, "nome": "Training Camp Mania"}], now) is None


def test_a_ticked_step_without_an_analyst_sent_to_this_opponent_still_sends_it():
    # 2026-10-28: an analyst collected after the round changed ticked the next round's step
    late = [{"weekNr": 13, "instructionTeamId": 9}]
    client = FakeClient([step(7, 4), step(5, 1)], friendlies=4, sent=late)
    prepare(client)
    assert client.posts == [(f"{BASE}/spyinstructions", {"instructionTeamId": 3, "timerGameSettingId": 60})]


def test_no_analyst_when_the_game_does_not_offer_it():
    client = FakeClient([step(7, 4), step(5, 0, enabled=False)], friendlies=4)  # e.g. his secret training
    prepare(client)
    assert client.posts == []
