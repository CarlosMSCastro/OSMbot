from osmbot.game import specialists

BASE = "leagues/9/teams/1"
TEAM = {"name": "Club"}


def player(pid, lineup, position, age, att, ovr=80, unavailable=0):
    return {"id": pid, "name": f"P{pid}", "lineup": lineup, "position": position, "age": age, "statAtt": att,
            "statOvr": ovr, "statDef": 50, "unavailable": unavailable}


PLAYERS = [player(1, 11, 1, 39, 100), player(2, 10, 1, 29, 106), player(3, 7, 2, 23, 112), player(4, 3, 3, 28, 60),
           player(5, 1, 4, 30, 0), player(6, 14, 1, 40, 120)]  # 6 is on the bench: never a specialist


class FakeGame:
    def __init__(self, current, status=200):
        self.current, self.status, self.writes = current, status, []

    def get(self, path):
        return 200, {f"{BASE}/specialists": self.current, f"{BASE}/players": PLAYERS}[path]

    def request(self, method, path, form):
        self.writes.append((method, path, form))
        return self.status, {}


def test_only_the_roles_out_of_the_rule_are_put_right():
    game, lines = FakeGame({"captain": 11, "penalty": 10, "freekick": 10, "corners": 7}), []
    assert specialists.fix_specialists(game, TEAM, BASE, True, lines.append) == 0
    assert game.writes == [("PUT", f"{BASE}/specialists", {"captain": 11, "corners": 7, "freekick": 7, "penalty": 10})]
    assert lines == ["Especialistas (Club): livres P2 → P3"]


def test_nothing_is_written_when_they_follow_the_rule_or_in_a_simulation():
    right = FakeGame({"captain": 11, "penalty": 10, "freekick": 7, "corners": 7})
    specialists.fix_specialists(right, TEAM, BASE, True, print)
    assert right.writes == []
    simulated, lines = FakeGame({"captain": 1, "penalty": 10, "freekick": 7, "corners": 7}), []
    specialists.fix_specialists(simulated, TEAM, BASE, False, lines.append)
    assert simulated.writes == [] and lines == ["Simulação: especialistas de Club: capitão P5 → P1"]


def test_a_refusal_is_not_repeated_the_same_day():
    game = FakeGame({"captain": 1, "penalty": 10, "freekick": 7, "corners": 7}, status=400)
    specialists.fix_specialists(game, TEAM, BASE, True, print)
    specialists.fix_specialists(game, TEAM, BASE, True, print)
    assert len(game.writes) == 1


def test_the_checklist_says_which_roles_are_out_of_the_rule():
    assert specialists.check(PLAYERS, {"captain": 11, "penalty": 10, "freekick": 10, "corners": 7}) == ["Livres: P2, pela regra P3"]
    assert specialists.check(PLAYERS, {"captain": 11, "penalty": 10, "freekick": 7, "corners": 7}) == []
    assert specialists.check(PLAYERS, None) == []
