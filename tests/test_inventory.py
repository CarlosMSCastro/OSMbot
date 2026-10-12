import pytest

from osmbot.game import inventory
from osmbot.inventory.policy import USE_BEFORE, active_until, due, pick_club, universal_trainee, wake_times

NOW = 1_800_000_000.0
HOUR = 3600


def item(iid, kind, expires_in=None, value=1440, action="X"):
    return {"id": iid, "reward": {"type": kind, "value": value}, "action": {"id": action},
            "expiredTimestamp": NOW + expires_in if expires_in is not None else 9223372036854775807}


def player(pid, lineup=1, age=25, position=3, unavailable=0, value=10):
    return {"id": pid, "name": f"P{pid}", "lineup": lineup, "age": age, "position": position, "unavailable": unavailable,
            "value": value}


def test_only_universal_trainers_and_bags_are_used_and_only_4_hours_before_they_expire():
    items = [item("ut", 12, 3 * HOUR), item("bag", 13, 2 * HOUR), item("later", 12, 30 * HOUR), item("swap", 7),
             item("gone", 12, -HOUR), item("tp", 9, HOUR)]
    assert [i["id"] for i in due(items, NOW)] == ["bag", "ut"]  # soonest first; swaps and progression never
    assert wake_times(items, NOW) == [NOW + 30 * HOUR - USE_BEFORE]


def test_the_universal_trainer_trains_the_starter_with_fewest_sessions_then_most_to_gain():
    players = [player(1), player(2), player(3, lineup=14), player(4, age=31), player(5, age=33, position=4),
               player(6), player(7, unavailable=2), player(8)]
    forecasts = {1: 20, 2: 50, 3: 90, 4: 80, 5: 30, 6: 70, 7: 99, 8: 60}
    sessions = [{"playerId": 6}]
    chosen = universal_trainee(players, sessions, listed={8}, rounds={2: 1}, forecasts=forecasts)
    assert chosen["id"] == 5  # 2 trained this round, 6 training, 8 listed, 7 out, 4 is 30+; a 33-year-old GK may
    assert universal_trainee([player(3, lineup=14), player(9, lineup=0)], [], set(), {}, {3: 10, 9: 40})["id"] == 9  # no starter: the rest
    assert universal_trainee([player(4, age=31)], [], set(), {}, {}) is None


def test_the_club_with_most_to_gain_gets_it_a_tie_goes_to_the_weaker_squad():
    assert pick_club([{"n": "a", "gain": 36, "value": 900}, {"n": "b", "gain": 67, "value": 700}])["n"] == "b"
    assert pick_club([{"n": "a", "gain": 40, "value": 900}, {"n": "b", "gain": 40, "value": 700}])["n"] == "b"
    assert pick_club([{"n": "a", "gain": None, "value": 1}]) is None
    assert active_until([{"type": 17, "finishedTimestamp": NOW + 60}, {"type": 18, "finishedTimestamp": NOW + 999}], NOW) == NOW + 60
    assert active_until([{"type": 17, "finishedTimestamp": NOW - 60}], NOW) is None


class FakeGame:
    """Two clubs; the second has the better player for the universal trainer."""

    def __init__(self, items, timers=None, sessions=None):
        self.items, self.writes = items, []
        self.timers = timers or {}
        self.sessions = sessions or {}

    def get(self, path):
        clubs = {"leagues/9/teams/1": ([player(10), player(11)], {10: 30, 11: 36}),
                 "leagues/8/teams/2": ([player(20), player(21)], {20: 67, 21: 10})}
        if path == "user/userrewards":
            return 200, self.items
        if path == "user/accounts":
            return 200, {"teamSlots": {"0": {"team": {"id": 1, "leagueId": 9, "name": "A"}},
                                       "1": {"team": {"id": 2, "leagueId": 8, "name": "B"}}}}
        if path.endswith("/gamesettings"):
            return 200, [{"id": 974, "name": "TrainingUniversalSession"}]
        if path in ("leagues/9", "leagues/8"):
            return 200, {"weekNr": 5}
        base = next(b for b in clubs if path.startswith(b + "/"))
        what = {"trainingsessions/ongoing": "ongoing", "transferplayers/0": "transferplayers"}.get(path[len(base) + 1:],
                                                                                                  path[len(base) + 1:])
        players, forecasts = clubs[base]
        return 200, {"timers": self.timers.get(base, []), "ongoing": self.sessions.get(base, []), "players": players,
                     "transferplayers": [], "trainingforecasts": [{"playerId": k, "forecast": 1, "forecastUniversal": v}
                                                                  for k, v in forecasts.items()]}[what]

    def put(self, path):
        self.writes.append(("PUT", path))
        if "randomrewards" in path:
            return 200, [{"id": "c1", "reward": {"type": 1, "value": 5}, "action": {"id": "BC_5"}},
                         {"id": "e1", "reward": {"type": 15, "value": 2}, "action": {"id": "Energy_2"}}]
        return 200, {"type": 17, "finishedTimestamp": NOW + 24 * HOUR}

    def post(self, path, form):
        self.writes.append(("POST", path, form))
        return 200, {"id": 77}


@pytest.fixture
def game(monkeypatch, tmp_path):
    from osmbot.game import client, trainings

    monkeypatch.setattr(trainings, "ROUNDS_FILE", tmp_path / "treinos.json")
    monkeypatch.setattr(inventory, "PAUSE_BETWEEN_WRITES", 0)
    holder = {}
    monkeypatch.setattr(client, "OsmClient", lambda: holder["game"])

    def run(fake, confirm=True):
        holder["game"], lines = fake, []
        result = inventory.run_inventory(confirm, log=lines.append, clock=lambda: NOW)
        return result, lines
    return run


def test_a_universal_trainer_about_to_expire_goes_to_the_club_with_most_to_gain_and_trains_at_once(game):
    fake = FakeGame([item("ut24", 12, 3 * HOUR, action="DailyMissionsRewardUT_24H"), item("swap", 7)])
    (failures, wake), lines = game(fake)
    assert failures == 0
    assert fake.writes == [("PUT", "leagues/8/teams/2/universaltrainer/ut24/claim"),
                           ("POST", "leagues/8/teams/2/trainingsessions", {"playerId": 20, "trainer": 5, "timerGameSettingId": 974})]
    assert "Treinador universal de 24 h ativado em B" in lines[0] and "P20 (B, previsão 67) a treinar" in lines[1]


def test_an_active_universal_trainer_with_nobody_gets_the_next_player_and_a_busy_one_is_left_alone(game):
    timers = {"leagues/9/teams/1": [{"type": 17, "finishedTimestamp": NOW + 10 * HOUR}]}
    fake = FakeGame([], timers=timers)
    (_, wake), _ = game(fake)
    assert fake.writes == [("POST", "leagues/9/teams/1/trainingsessions", {"playerId": 11, "trainer": 5, "timerGameSettingId": 974})]
    assert NOW + 10 * HOUR in wake
    busy = FakeGame([], timers=timers, sessions={"leagues/9/teams/1": [{"id": 5, "playerId": 10, "trainer": 5, "weekNr": 5}]})
    game(busy)
    assert busy.writes == []


def test_a_bag_about_to_expire_is_opened_and_its_boss_coins_go_to_the_wallet(game):
    fake = FakeGame([item("bag", 13, HOUR, value=7, action="DailyLoginStreakBag_X")])
    (failures, _), lines = game(fake)
    assert failures == 0
    assert fake.writes == [("PUT", "user/randomrewards/bag/claim"),
                           ("POST", "user/bosscoinwallet/consumereward", {"rewardId": "c1"})]
    assert lines == ["Saco aberto antes de expirar: 5 boss coins, 2 de energia"]


def test_nothing_due_and_nothing_active_reads_no_squads_and_writes_nothing(game):
    fake = FakeGame([item("later", 12, 30 * HOUR)])
    reads = []
    original = fake.get
    fake.get = lambda path: (reads.append(path), original(path))[1]
    (failures, wake), _ = game(fake)
    assert failures == 0 and fake.writes == [] and wake == [NOW + 26 * HOUR]
    assert not any(path.endswith("/players") for path in reads)
    simulated = FakeGame([item("ut", 12, HOUR)])
    (_, _), lines = game(simulated, confirm=False)
    assert simulated.writes == [] and lines[0].startswith("Simulação: ativaria o treinador universal de 24 h em B")


def test_the_window_shows_the_inventory_and_the_universal_trainer():
    from osmbot.gui.view import GREY, YELLOW, inventory_view, universal_ring

    items = [{"type": 12, "value": 1440, "action": "UT_24H", "expires": NOW + 3 * HOUR},
             {"type": 7, "value": 1, "action": "Switch", "expires": None},
             {"type": 7, "value": 1, "action": "Switch", "expires": None},
             {"type": 13, "value": 7, "action": "Bag", "expires": NOW + 100 * HOUR}]
    view = inventory_view(items, NOW)
    assert view["warn"] and "count" not in view
    assert view["rows"] == [("universal", "treinador universal 24 h · expira em 3 horas", YELLOW),
                            ("inventory", "saco de prémios · expira em 4 dias e 4 horas", None)]  # only what expires
    assert not inventory_view(items[1:], NOW)["warn"] and inventory_view(None, NOW) is None
    assert inventory_view(items[1:3], NOW)["rows"] == [(None, "Nada a expirar", GREY)]
    assert universal_ring(None, NOW)["state"] == "none"
    ring = universal_ring({"until": NOW + 20 * HOUR, "session": {"name": "P1", "finish": NOW + 3 * HOUR, "claimed": False}}, NOW)
    assert (ring["state"], ring["centre"], ring["name"], ring["done"]) == ("working", "3h00", "P1", 0.5)
    assert universal_ring({"until": NOW + HOUR, "session": None}, NOW)["state"] == "waiting"


def test_training_videos_skip_the_universal_trainer_and_the_bot_wakes_to_collect_its_session():
    from osmbot.game.ads import pick_session
    from osmbot.game.dashboard import wake_events

    universal = {"trainer": 5, "countdownTimer": {"isClaimed": False, "finishedTimestamp": NOW + 6 * HOUR}}
    normal = {"trainer": 3, "countdownTimer": {"isClaimed": False, "finishedTimestamp": NOW + 3 * HOUR}}
    assert pick_session([("A", universal), ("A", normal)], NOW) == ("A", normal)
    assert pick_session([("A", universal)], NOW) is None
    snapshot = {"clubs": [{"trainings": [], "universal": {"until": NOW + 9 * HOUR,
                                                          "session": {"finish": NOW + HOUR, "claimed": False}}}], "ads": {}}
    assert ("treino acaba", NOW + HOUR) in wake_events(snapshot, NOW)


def test_the_universal_trainer_s_session_is_on_the_timeline():
    from osmbot.board.timeline import future_events

    snapshot = {"clubs": [{"name": "A", "trainings": [], "universal": {"until": NOW + 9 * HOUR,
                                                                      "session": {"name": "P1", "finish": NOW + HOUR, "claimed": False}}}],
                "ads": {}, "daily": {}}
    assert any(e["title"] == "Treino P1" for e in future_events(snapshot, NOW))


def test_time_left_in_days_and_hours():
    from osmbot.gui.view import time_left

    assert time_left(37 * HOUR) == "1 dia e 13 horas" and time_left(48 * HOUR) == "2 dias"
    assert time_left(HOUR + 5) == "1 hora" and time_left(40 * 60) == "40 min"
    assert time_left(25 * HOUR, "en") == "1 day and 1 hour"
