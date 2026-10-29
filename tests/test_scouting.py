from osmbot.game import prematch
from osmbot.prematch.policy import ANALYSIS_LEAD, analyst_busy, can_scout, needs_analysis, scout_target

NOW = 1_000_000.0
TEAMS = [{"id": i, "name": f"C{i}", "ranking": i} for i in range(1, 7)]


def fixture(week, home, away):
    return {"weekNr": week, "homeTeamId": home, "awayTeamId": away, "matchType": 0}


MATCHES = [fixture(11, 1, 2), fixture(12, 5, 1), fixture(13, 1, 3)]


def sent(club, week=10, claimed=True):
    return {"id": club, "weekNr": week, "instructionTeamId": club, "countdownTimer": {"finishedTimestamp": NOW - 1, "isClaimed": claimed}}


def test_another_club_analysed_does_not_count_as_the_opponent_s_analysis():
    steps = [{"type": 5, "progressAmount": 0, "completionAmount": 1}]  # "Analyse your opponent", not done
    assert needs_analysis(steps, [sent(4)], 10, opponent=2)
    assert not needs_analysis(steps, [sent(2)], 10, opponent=2)


def test_the_analyst_goes_round_the_coming_opponents_first_never_the_next_one_and_once_a_round():
    assert scout_target(TEAMS, MATCHES, 1, 10, []) == 5  # 2 is next: his analysis is in the last 2 h
    assert scout_target(TEAMS, MATCHES, 1, 10, [sent(5)]) == 3
    assert scout_target(TEAMS, MATCHES, 1, 10, [sent(5), sent(3)]) == 4  # then by place in the table
    assert scout_target(TEAMS, MATCHES, 1, 10, [sent(c) for c in (3, 4, 5, 6)]) is None
    assert scout_target(TEAMS, MATCHES, 1, 10, [sent(5, week=9)]) == 5  # a new round: again


def test_the_analyst_works_on_one_club_at_a_time_and_keeps_out_of_the_opponent_s_window():
    assert analyst_busy([sent(4, claimed=False)], NOW) and not analyst_busy([sent(4)], NOW)
    hour = 3600
    assert can_scout(NOW + ANALYSIS_LEAD + 2 * hour, NOW, hour, False)
    assert not can_scout(NOW + ANALYSIS_LEAD + hour, NOW, hour, False)  # would end too close to the bot's analysis
    assert not can_scout(NOW + 10 * hour, NOW, hour, True)  # the opponent is analysed: no other club until the match
    assert can_scout(None, NOW, hour, False)


class Game:
    def __init__(self, sent_list):
        self.sent, self.posts = sent_list, []

    def get(self, path):
        if path.endswith("/spyinstructions"):
            return 200, self.sent
        if path.endswith("/gamesettings"):
            return 200, [{"id": 60, "name": "SpyInstructionTimer", "value": 60}]
        return 200, {"leagues/9/teams": TEAMS, "leagues/9/matches/filter": MATCHES}[path]

    def post(self, path, form):
        self.posts.append((path, form))
        return 200, {}


def test_scouting_sends_the_analyst_and_comes_back_when_it_ends(monkeypatch):
    monkeypatch.setattr(prematch, "PAUSE_BETWEEN_WRITES", 0)
    monkeypatch.setattr(prematch, "timer", lambda client, league, name, normal: (60, 60))
    game, said = Game([]), []
    team = {"id": 1, "name": "Club"}
    result = prematch._scout(game, team, "leagues/9/teams/1", "leagues/9", 10, NOW + 10 * 3600, NOW, 2, True, said.append)
    assert result == (0, NOW + 3600)
    assert game.posts == [("leagues/9/teams/1/spyinstructions", {"instructionTeamId": 5, "timerGameSettingId": 60})]
    busy = Game([sent(5, claimed=False)])
    assert prematch._scout(busy, team, "leagues/9/teams/1", "leagues/9", 10, NOW + 10 * 3600, NOW, 2, True, said.append) == (0, None)
    assert busy.posts == []
