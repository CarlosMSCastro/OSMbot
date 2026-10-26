from osmbot.game.predictions import PREDICTION, claim_seasons, run_prediction, step, to_collect

NOW = 1_000_000.0
OPEN = {"id": 277, "startTimestamp": NOW - 3600, "endTimestamp": NOW + 3600, "homeTeamName": "Casa",
        "awayTeamName": "Fora", "actionId": "MatchPrediction_5BC", "homeGoalsResult": None, "awayGoalsResult": None}
OVER = {**OPEN, "id": 276, "startTimestamp": NOW - 9000, "endTimestamp": NOW - 5000, "homeGoalsResult": 1, "awayGoalsResult": 1}
NEXT = {**OPEN, "id": 278, "startTimestamp": NOW + 7200, "endTimestamp": NOW + 9000}


def test_predicts_the_open_match_when_there_is_no_prediction():
    assert step(None, [OVER, OPEN, NEXT], NOW) == ("predict", OPEN)
    assert step(None, [OVER, NEXT], NOW) is None  # nothing open now


def test_a_prediction_is_left_alone_until_its_match_is_over_with_a_result_then_cleared():
    mine = {"id": 9, "matchPredictionId": 277, "homeGoals": 1, "awayGoals": 1}
    assert step(mine, [OPEN], NOW) is None
    assert step(mine, [{**OPEN, "endTimestamp": NOW - 1}], NOW) is None  # over, no result yet
    done = {**mine, "matchPredictionId": 276}
    assert step(done, [OVER, OPEN], NOW) == ("claim", done)
    assert step({**mine, "matchPredictionId": 1}, [OPEN], NOW) == ("claim", {**mine, "matchPredictionId": 1})  # gone


class FakeClient:
    def __init__(self, mine=None, history=None):
        self.mine, self.history, self.writes = mine, history or [], []

    def get(self, path):
        if path == "matchpredictions":
            return 200, [OVER, OPEN]
        if path == "user/usermatchprediction":
            return (200, self.mine) if self.mine else (404, "")
        if path == "user/history":
            return 200, [{"history": self.history}]
        raise AssertionError(path)

    def post(self, path, form):
        self.writes.append(("POST", path, form))
        return 200, {}

    def put(self, path):
        self.writes.append(("PUT", path))
        return 200, {}

    def request(self, method, path, form=None):
        self.writes.append((method, path))
        return 200, [{"reward": {"name": "Boss coins", "type": 1, "value": 5}}]


def test_the_prediction_is_sent_and_a_finished_one_cleared_with_its_prize():
    said = []
    client = FakeClient()
    assert run_prediction(client, True, said.append, NOW) == 0
    assert client.writes == [("POST", "user/usermatchpredictions",
                              {"matchPredictionId": 277, "homeGoals": PREDICTION[0], "awayGoals": PREDICTION[1]})]
    client = FakeClient({"id": 9, "matchPredictionId": 276, "homeGoals": 1, "awayGoals": 1})
    assert run_prediction(client, True, said.append, NOW) == 0
    assert client.writes == [("DELETE", "user/usermatchpredictions/9")]
    assert said[-1] == "Previsão: Casa 1-1 Fora, previsto 1-1 · certa, prémio: Boss coins 5"
    dry = FakeClient()
    run_prediction(dry, False, said.append, NOW)
    assert dry.writes == [] and said[-1].startswith("Simulação: previa Casa 1-1 Fora")


def test_only_the_seasons_not_collected_are_claimed():
    history = [{"id": 1, "claimed": True, "reward": 40}, {"id": 2, "claimed": False, "reward": 17, "team": "Clube"},
               {"id": 3, "claimed": False, "reward": 0}]
    assert [s["id"] for s in to_collect(history)] == [2]
    client = FakeClient(history=history)
    assert claim_seasons(client, True, lambda line: None) == 0
    assert client.writes == [("PUT", "user/history/2/claim")]
