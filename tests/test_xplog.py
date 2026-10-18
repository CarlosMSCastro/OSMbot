import json

from osmbot import logs
from osmbot.game import xplog

TIERS = [{"level": 9, "startRange": 380000, "endRange": 449999}, {"level": 10, "startRange": 450000, "endRange": 500000}]


class FakeGame:
    def __init__(self, week=23, rating=397927, league=694):
        self.week, self.rating, self.league, self.reads = week, rating, league, []

    def get(self, path):
        self.reads.append(path)
        bodies = {
            "user/accounts": {"skillRating": self.rating,
                              "teamSlots": {"0": {"team": {"id": 1, "leagueId": 9}}, "3": {"team": None}}},
            "leagues/9": {"weekNr": self.week},
            "leagues/9/matches/filter": [
                {"id": f"9_1_{self.week}", "leagueId": 9, "weekNr": self.week, "matchType": 0, "homeTeamId": 4,
                 "awayTeamId": 1, "homeGoals": 2, "awayGoals": 1, "winnerTeamId": 4},
                {"id": "9_2_x", "leagueId": 9, "weekNr": self.week, "matchType": 0, "homeTeamId": 2, "awayTeamId": 3,
                 "homeGoals": 0, "awayGoals": 0},
                {"id": "9_f", "leagueId": 9, "weekNr": self.week, "matchType": 2, "homeTeamId": 1, "awayTeamId": 2,
                 "homeGoals": 5, "awayGoals": 0}],
            "leagues/9/managers": [{"teamId": 1, "skillRating": self.rating, "leagueSkillRating": self.league},
                                   {"teamId": 4, "skillRating": 419891, "leagueSkillRating": 930}],
            "leagues/9/teams": [{"id": t, "name": f"T{t}"} for t in (1, 2, 3, 4)],
            "user/skillratingbonuses": [{"leagueId": 9, "weekNr": self.week, "type": 0, "amount": 25, "teamSlotIndex": 0},
                                        {"leagueId": 8, "weekNr": self.week, "type": 0, "amount": 25}],
            "tiers": TIERS,
        }
        return (200, bodies[path]) if path in bodies else (404, None)


def test_result_from_the_owners_side():
    match = {"homeTeamId": 1, "awayTeamId": 2, "homeGoals": 1, "awayGoals": 1, "winnerTeamId": 0}
    assert xplog.result(match, 1) == "E"
    assert xplog.result({**match, "homeGoals": 0}, 2) == "V"
    assert xplog.result({**match, "isDecidedByPenalties": True, "winnerTeamId": 2}, 1) == "D"


def test_tier_and_whats_left():
    assert xplog.tier(397927, TIERS) == {"nivel": 9, "falta": 52073}
    assert xplog.tier(None, TIERS) is None


def test_logs_each_owners_match_once_with_the_change_in_the_league(tmp_path):
    lines, said = [], []
    game = FakeGame()
    logs_record = lambda kind, data: lines.append((kind, data))
    original = logs.record
    logs.record = logs_record
    try:
        assert xplog.log_xp(game, log=said.append) == 1
        assert xplog.log_xp(game, log=said.append) == 0  # same round: nothing new
        game.week, game.rating, game.league = 24, 397900, 667
        assert xplog.log_xp(game, log=said.append) == 1
    finally:
        logs.record = original
    first, second = lines[0][1], lines[1][1]
    assert lines[0][0] == "xp"
    assert first["resultado"] == "D" and first["adversario_humano"] and first["rating_adversario"] == 419891
    assert first["liga_variacao"] is None and first["bonus"] == [{"tipo": "jogo", "valor": 25}]
    assert second["liga_variacao"] == -27 and second["rating_variacao"] == -27 and second["jornadas"] == 1
    assert second["nivel"] == {"nivel": 9, "falta": 52100}
    assert "1.ª leitura" in said[0] and "-27 nesta liga" in said[1] and "treinador 419 891" in said[1]


def test_summary_averages_only_consecutive_rounds(tmp_path):
    repo = tmp_path / "repo"
    folder = repo / "logs" / "PC" / "xp"
    folder.mkdir(parents=True)
    rows = [{"t": 1, "jogo": "a", "semana": 1, "clube": "T1", "golos": "1-0", "resultado": "V", "adversario_humano": False,
             "liga_variacao": 25, "jornadas": 1, "rating": 10, "bonus": []},
            {"t": 2, "jogo": "b", "semana": 3, "clube": "T1", "golos": "0-1", "resultado": "D", "adversario_humano": True,
             "rating_adversario": 5, "liga_variacao": -40, "jornadas": 2, "rating": 9, "bonus": []}]
    (folder / "2026-10.jsonl").write_text("\n".join(json.dumps(r) for r in rows + rows[:1]), encoding="utf-8")
    lines = xplog.read_lines(repo)
    assert [line["jogo"] for line in lines] == ["a", "b"]
    out = "\n".join(xplog.summary(lines))
    assert "V vs CPU    +25 (1 jogos)" in out and "D vs humano" not in out
