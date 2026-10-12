from osmbot import logs
from osmbot.game import matchlog

L = "leagues/9"


def player(pid, ovr, grade, lineup=1, value=10):
    return {"id": pid, "name": f"P{pid}", "position": 3, "statOvr": ovr, "statAtt": 0, "statDef": ovr, "age": 25,
            "value": value, "lineup": lineup, "lastPlayerGrade": grade, "goalsLastMatch": 0, "fitness": 90, "morale": 80}


class FakeGame:
    def __init__(self, week=18):
        self.week, self.reads = week, []

    def get(self, path):
        self.reads.append(path)
        bodies = {
            L: {"weekNr": self.week},
            f"{L}/matches/filter": [
                {"id": "9_1_18", "weekNr": 18, "matchType": 0, "homeTeamId": 2, "awayTeamId": 1, "homeGoals": 0, "awayGoals": 3,
                 "refereeId": 7, "winnerTeamId": 1},
                {"id": "9_2_18", "weekNr": 18, "matchType": 0, "homeTeamId": 3, "awayTeamId": 4, "homeGoals": 1, "awayGoals": 1,
                 "refereeId": 8, "winnerTeamId": 0},
                {"id": "9_9_18", "weekNr": 18, "matchType": 2, "homeTeamId": 1, "awayTeamId": 3, "homeGoals": 2, "awayGoals": 0},
                {"id": "9_1_19", "weekNr": 19, "matchType": 0, "homeTeamId": 1, "awayTeamId": 3, "homeGoals": None, "awayGoals": None}],
            f"{L}/teams": [{"id": t, "name": f"T{t}", "ranking": t, "previousRanking": t + 1} for t in (1, 2, 3, 4)],
            f"{L}/referees": [{"id": 7, "name": "R7", "strictness": 3}, {"id": 8, "name": "R8", "strictness": 5}],
            f"{L}/teams/1/teamtactics": {"formation": 433, "style": 2},
        }
        if path in bodies:
            return 200, bodies[path]
        if path.endswith("/players"):
            team = int(path.split("/teams/")[1].split("/")[0])
            return 200, [player(team * 10 + i, 80 + i, 6 + i % 3) for i in range(12)]
        return 404, ""


def test_a_round_is_logged_once_with_the_owner_s_tactics_from_before_the_match(monkeypatch):
    rows, said = [], []
    monkeypatch.setattr(logs, "record", lambda kind, row: rows.append((kind, row)))
    game = FakeGame()
    matchlog._save({"antes": {f"{L}/teams/1": {"semana": 17, "tatica": {"formation": 442}, "analise": [{"formation": 352}]}}})
    assert matchlog.log_round(game, 9, {1: {"id": 1}}, said.append) == 2  # league matches only, the played round
    assert [k for k, _ in rows] == ["jogos", "jogos"]
    mine = rows[0][1]
    assert mine["resultado"] == "0-3" and mine["arbitro"] == {"id": 7, "nome": "R7", "rigor": 3}
    assert mine["tatica"] == {"formation": 442} and mine["tatica_lida"] == "antes do jogo" and mine["analise"] == [{"formation": 352}]
    assert mine["fora"]["meu"] and not mine["casa"]["meu"] and mine["fora"]["lugar_antes"] == 2
    assert "fitness" in mine["fora"]["jogadores"][0] and "fitness" not in mine["casa"]["jogadores"][0]
    assert mine["casa"]["media_11"] == round(sum(range(81, 92)) / 11, 1)
    assert "tatica" not in rows[1][1]  # nobody of the owner's: no tactics
    assert said == ["Jogo: T1 3-0 T2 (fora) · árbitro rigor 3 · melhor nota P12 8"]
    assert matchlog.log_round(game, 9, {1: {"id": 1}}, said.append) == 0  # once per round


def test_without_a_read_from_before_the_tactics_are_read_after_and_said_so(monkeypatch):
    rows = []
    monkeypatch.setattr(logs, "record", lambda kind, row: rows.append(row))
    matchlog.log_round(FakeGame(), 9, {1: {"id": 1}}, lambda line: None)
    assert rows[0]["tatica"] == {"formation": 433, "style": 2} and rows[0]["tatica_lida"] == "depois do jogo"


def test_the_tactics_read_before_the_match_keep_the_analyst_s_report():
    game = FakeGame(week=17)
    game.get = lambda path: (200, [{"formation": 352}]) if path.endswith("spyresults") else (200, {"formation": 433})
    matchlog.note_prematch(game, f"{L}/teams/1", 17, now=5.0)
    game.get = lambda path: (404, "") if path.endswith("spyresults") else (200, {"formation": 442})
    matchlog.note_prematch(game, f"{L}/teams/1", 17, now=6.0)  # the report gone: the earlier one stays
    kept = matchlog._load()["antes"][f"{L}/teams/1"]
    assert kept["tatica"] == {"formation": 442} and kept["analise"] == [{"formation": 352}]


def test_the_season_so_far_is_logged_once_with_results_and_referees(monkeypatch):
    rows, said = [], []
    monkeypatch.setattr(logs, "record", lambda kind, row: rows.append(row))
    game = FakeGame(week=19)
    assert matchlog.log_history(game, 9, {1: {"id": 1}}, said.append) == 2  # weeks before 19, no friendlies
    assert all(r["historico"] for r in rows) and rows[0]["arbitro"]["rigor"] == 3 and "jogadores" not in rows[0]["casa"]
    assert matchlog.log_history(game, 9, {1: {"id": 1}}, said.append) == 0
