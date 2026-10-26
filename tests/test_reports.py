from osmbot.game.reports import RETRY, comments, key, pending, record, save_reports, verdict

EVENTS = [  # as the game answered for a 3-0 at home (2026-10-25), shortened
    {"id": 3, "teamId": 7, "commentatorPhase": 4, "commentatorType": 1, "text": "All Specialists were doing their job"},
    {"id": 1, "teamId": 7, "commentatorPhase": 0, "commentatorType": 0, "text": "What a fixture!"},
    {"id": 2, "teamId": 0, "commentatorPhase": 1, "commentatorType": 1, "text": "Great game so far!"},
    {"id": 4, "teamId": 7, "commentatorPhase": 4, "commentatorType": 1, "text": "I would spice up the Tackling"},
    {"id": 5, "teamId": 7, "commentatorPhase": 4, "commentatorType": 0, "text": "3 - 0! What did you think?"},
    {"id": 6, "teamId": 9, "commentatorPhase": 4, "commentatorType": 1, "text": "the other club's"},
]


def test_the_verdict_is_the_pundits_post_match_lines_highlight_first_and_tip_last():
    assert verdict(EVENTS, 7) == ["All Specialists were doing their job", "I would spice up the Tackling"]


def test_every_comment_of_the_club_and_the_generic_ones_in_the_order_of_the_match():
    assert [(c["fase"], c["quem"], c["texto"]) for c in comments(EVENTS, 7)] == [
        ("antes", "apresentador", "What a fixture!"), ("intervalo", "comentador", "Great game so far!"),
        ("fim", "comentador", "All Specialists were doing their job"), ("fim", "comentador", "I would spice up the Tackling"),
        ("fim", "apresentador", "3 - 0! What did you think?")]


def test_only_played_matches_of_the_club_not_kept_and_not_asked_lately():
    played = {"homeTeamId": 7, "awayTeamId": 2, "weekNr": 6, "matchId": 6, "matchData": {"homeOvr": 669}}
    friendly = {**played, "matchId": 14, "matchType": 2}
    future = {**played, "weekNr": 7, "matchData": None}
    others = {**played, "homeTeamId": 3, "matchId": 9}
    matches = [played, friendly, future, others]
    assert pending(matches, 1, 7, set(), {}, 1000.0) == [played, friendly]
    assert pending(matches, 1, 7, {key(1, 7, played)}, {}, 1000.0) == [friendly]
    assert pending(matches, 1, 7, set(), {key(1, 7, friendly): 1000.0 - RETRY + 1}, 1000.0) == [played]


def test_the_record_is_from_the_clubs_side():
    match = {"homeTeamId": 2, "awayTeamId": 7, "homeGoals": 1, "awayGoals": 3, "weekNr": 6, "matchId": 6, "matchType": 0}
    line = record(match, {"id": 7, "name": "Clube", "leagueId": 1}, {2: "Rival"}, EVENTS)
    assert (line["resultado"], line["casa"], line["adversario"], line["tipo"]) == ("3-1", False, "Rival", "liga")
    assert line["veredito"][-1] == "I would spice up the Tackling" and len(line["comentarios"]) == 5


class FakeClient:
    def __init__(self, reports):
        self.reports, self.asked = reports, []

    def get(self, path):
        self.asked.append(path)
        if path == "user/accounts":
            return 200, {"teamSlots": {"0": {"team": {"id": 7, "name": "Clube", "leagueId": 1}}}}
        if path.endswith("/matches/filter"):
            return 200, [{"homeTeamId": 7, "awayTeamId": 2, "homeGoals": 3, "awayGoals": 0, "weekNr": 6, "matchId": 6,
                          "matchType": 0, "matchData": {"homeOvr": 669}}]
        if path.endswith("/teams"):
            return 200, [{"id": 2, "name": "Rival"}]
        if path.endswith("/commentatorevents"):
            return (200, self.reports) if self.reports else (404, "")
        raise AssertionError(path)


def test_a_report_is_kept_once_and_a_missing_one_asked_again_later(monkeypatch):
    from osmbot.game import clubinfo

    monkeypatch.setattr(clubinfo, "_cache", {})
    lines = []
    late = FakeClient([])
    assert save_reports(late, lines.append, now=1000.0) == 0
    assert save_reports(late, lines.append, now=1000.0 + 60) == 0
    assert sum(p.endswith("commentatorevents") for p in late.asked) == 1  # not again within RETRY
    out = FakeClient(EVENTS)
    assert save_reports(out, lines.append, now=1000.0 + RETRY) == 1
    assert lines == ["Relatório: Clube 3-0 Rival (liga): All Specialists were doing their job · I would spice up the Tackling"]
    assert save_reports(out, lines.append, now=1000.0 + 2 * RETRY) == 0  # kept: never read again
