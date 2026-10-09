from osmbot.game import medical
from osmbot.medical.policy import doctor_candidates, lawyer_candidates, to_collect

LEAGUE = "leagues/9"
BASE = f"{LEAGUE}/teams/1"
TEAM = {"id": 1, "name": "Club"}
NOW = 1_000_000.0


def case(cid, player, ends=None, claimed=False, week=14):
    item = {"id": cid, "playerId": player, "weekNr": week}
    if ends is not None:
        item["countdownTimer"] = {"finishedTimestamp": ends, "isClaimed": claimed}
    return item


def test_who_goes_to_the_doctor_and_the_lawyer():
    cases = [case(1, 10, NOW + 60), case(2, 11), case(3, 12, NOW - 60)]
    assert doctor_candidates([10, 11, 12, 13], cases) == [11, 13]  # 10 and 12 are with the doctor
    assert [c["id"] for c in to_collect(cases, NOW)] == [3]
    assert lawyer_candidates([20, 21], [case(5, 20)], 14) == [21]  # once per week
    assert lawyer_candidates([20], [case(5, 20, week=13)], 14) == [20]


class FakeClient:
    def __init__(self, injured=(), suspended=(), doctor=(), lawyer=(), status=200):
        self.injured, self.suspended = list(injured), list(suspended)
        self.doctor, self.lawyer, self.status = list(doctor), list(lawyer), status
        self.writes = []
        self.week = 14

    def get(self, path):
        players = [{"id": pid, "name": f"P{pid}", "unavailable": 3} for pid in self.injured + self.suspended]
        lists = {f"{BASE}/players/injured": [p for p in players if p["id"] in self.injured],
                 f"{BASE}/doctortreatments": self.doctor, f"{BASE}/lawyercases": self.lawyer}
        if path in lists:
            return (200, lists[path]) if lists[path] else (404, "")
        return 200, {LEAGUE: {"weekNr": self.week}, f"{BASE}/players": players}[path]

    def post(self, path, form):
        self.writes.append(("POST", path, form))
        return self.status, {}

    def put(self, path):
        self.writes.append(("PUT", path))
        return self.status, {}


def treat(client, confirm=True):
    lines = []
    result = medical.treat_club(client, TEAM, BASE, confirm, NOW, log=lines.append)
    return result, lines


def test_every_injured_player_goes_to_the_doctor_and_every_suspended_one_to_the_lawyer():
    client = FakeClient(injured=[10, 11], suspended=[20])
    (failures, wake), lines = treat(client)
    assert failures == 0 and wake == [NOW + 8 * 3600] * 3
    assert client.writes == [("POST", f"{BASE}/doctortreatments", {"playerId": 10, "timerGameSettingId": 48}),
                             ("POST", f"{BASE}/doctortreatments", {"playerId": 11, "timerGameSettingId": 48}),
                             ("POST", f"{BASE}/lawyercases", {"playerId": 20, "timerGameSettingId": 45})]
    assert "Médico: Club pôs P10 no médico (8 h)" in lines


def test_a_finished_case_is_collected_and_a_running_one_left_alone():
    client = FakeClient(injured=[10, 11], doctor=[case(7, 10, NOW - 5), case(8, 11, NOW + 600)])
    (failures, wake), _ = treat(client)
    assert ("PUT", f"{BASE}/doctortreatments/7/claim") in client.writes
    assert NOW + 600 in wake and failures == 0


def test_a_refused_player_is_not_asked_again_this_round_even_after_a_restart():
    client = FakeClient(injured=[10], status=400)
    _, lines = treat(client)
    _, again = treat(client)  # the next pass (or a restart: the note is kept on disk)
    assert len(client.writes) == 1 and sum("volto a tentar na próxima jornada" in line for line in lines + again) == 1
    client.week = 15
    treat(client)
    assert len(client.writes) == 2  # a new round: one more try


def test_while_someone_is_with_the_doctor_a_refused_one_waits_for_that_case_to_end():
    client = FakeClient(injured=[10, 11], doctor=[case(8, 10, NOW + 600)], status=400)
    _, lines = treat(client)
    assert [w[2]["playerId"] for w in client.writes] == [11] and any("fica à espera" in line for line in lines)
    treat(client)
    assert len(client.writes) == 1
    medical.treat_club(client, TEAM, BASE, True, NOW + 601, log=lambda m: None)
    posts = [w[2]["playerId"] for w in client.writes if w[0] == "POST"]
    assert posts == [11, 11]  # the running case ended (and is collected): try again


def test_a_refused_collect_is_not_repeated_this_round():
    client = FakeClient(injured=[10], doctor=[case(7, 10, NOW - 5)], status=404)
    treat(client)
    treat(client)
    assert sum(w[0] == "PUT" for w in client.writes) == 1


def test_a_server_error_is_not_a_refusal():
    client = FakeClient(injured=[10], status=500)
    (failures, _), _ = treat(client)
    treat(client)
    assert failures == 1 and len(client.writes) == 2  # tried again, as before


def test_simulation_writes_nothing():
    client = FakeClient(injured=[10], doctor=[case(7, 12, NOW - 5)])
    _, lines = treat(client, confirm=False)
    assert client.writes == [] and "Club: poria P10 no médico" in lines and "Club: levantaria 12 (médico)" in lines



def test_a_one_game_suspension_never_goes_to_the_lawyer():
    class OneGame(FakeClient):
        def get(self, path):
            if path == f"{BASE}/players":
                return 200, [{"id": 20, "name": "P20", "unavailable": 1}, {"id": 21, "name": "P21", "unavailable": 3}]
            return super().get(path)

    client = OneGame(suspended=[20, 21])
    treat(client)
    assert [w[2]["playerId"] for w in client.writes if w[1].endswith("lawyercases")] == [21]
