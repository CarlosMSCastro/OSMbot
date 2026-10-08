from osmbot.game import medical
from osmbot.medical.policy import doctor_candidates, lawyer_candidates, to_collect

LEAGUE = "leagues/9"
BASE = f"{LEAGUE}/teams/1"
TEAM = {"id": 1, "name": "Club"}
NOW = 1_000_000.0
V11 = "https://web-api.onlinesoccermanager.com/api/v1.1"


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

    def get(self, path):
        players = [{"id": pid, "name": f"P{pid}", "unavailable": 3} for pid in self.injured + self.suspended]
        lists = {f"{BASE}/players/injured": [p for p in players if p["id"] in self.injured],
                 f"{BASE}/doctortreatments": self.doctor, f"{BASE}/lawyercases": self.lawyer}
        if path in lists:
            return (200, lists[path]) if lists[path] else (404, "")
        return 200, {LEAGUE: {"weekNr": 14}, f"{BASE}/players": players}[path]

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
    assert ("PUT", f"{V11}/{BASE}/doctortreatments/7/claim") in client.writes
    assert NOW + 600 in wake and failures == 0


def test_a_refusal_makes_the_others_wait_and_an_unknown_lawyer_request_is_said_once():
    client = FakeClient(injured=[10, 11], status=400)
    (failures, _), lines = treat(client)
    assert failures == 0 and len(client.writes) == 1 and any("fica à espera" in line for line in lines)
    client = FakeClient(suspended=[20, 21], status=404)
    (failures, _), lines = treat(client)
    (failures2, _), lines2 = treat(client)
    assert failures == failures2 == 0 and len(client.writes) == 1  # never asked again this run
    assert sum("o jogo não aceitou" in line for line in lines + lines2) == 1


def test_simulation_writes_nothing():
    client = FakeClient(injured=[10], doctor=[case(7, 12, NOW - 5)])
    _, lines = treat(client, confirm=False)
    assert client.writes == [] and "Club: poria P10 no médico" in lines and "Club: levantaria 12 (médico)" in lines
