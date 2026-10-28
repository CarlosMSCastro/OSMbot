import pytest

from osmbot.game import stadium
from osmbot.stadium.policy import next_part, running_until, to_claim

NOW = 1000.0
BASE = "leagues/1/teams/2"
TEAM = {"name": "Club", "leagueId": 1, "id": 2}


def part(kind, level, top=3, ends=None):
    p = {"stadiumPartType": kind, "level": level, "stadiumPartLevels": [{"level": i} for i in range(top + 1)]}
    if ends:
        p["countdownTimer"] = {"finishedTimestamp": ends, "isClaimed": False}
    return p


def test_order_is_training_and_pitch_to_1_then_training_pitch_and_capacity_to_the_top():
    assert next_part([part(0, 0), part(1, 0), part(2, 0)], NOW) == 2
    assert next_part([part(0, 0), part(1, 0), part(2, 1)], NOW) == 1  # the pitch to 1 (owner, 2026-10-25)
    assert next_part([part(0, 0), part(1, 0), part(2, 2)], NOW) == 1  # a club already past it: the pitch to 1 too
    assert next_part([part(0, 0), part(1, 1), part(2, 1)], NOW) == 2  # then back to the training ground
    assert next_part([part(0, 0), part(1, 1), part(2, 3)], NOW) == 1
    assert next_part([part(0, 0), part(1, 0), part(2, 3)], NOW) == 1
    assert next_part([part(0, 0), part(1, 0, top=0), part(2, 1)], NOW) == 2  # a pitch with no levels: skipped
    assert next_part([part(0, 0), part(1, 3), part(2, 3)], NOW) == 0
    assert next_part([part(0, 3), part(1, 3), part(2, 3)], NOW) is None


def test_nothing_starts_while_one_is_running():
    parts = [part(0, 0), part(1, 0, ends=NOW + 500), part(2, 3)]
    assert next_part(parts, NOW) is None
    assert running_until(parts, NOW) == NOW + 500
    assert running_until([part(1, 0, ends=NOW - 5)], NOW) is None  # finished: the next one may start


class FakeClient:
    """balance/savings move as the game does: the empty PUT sends everything to the other side."""

    def __init__(self, balance, savings, price, parts=None):
        self.balance, self.savings, self.price = balance, savings, price
        self.parts = parts or [part(0, 0), part(1, 0), part(2, 0)]
        self.calls = []
        self.claim_status = 200

    def get(self, path):
        if path.endswith("/stadium"):
            return 200, {"stadiumParts": self.parts}
        if path.endswith("balanceandsavings"):
            return 200, {"balance": self.balance, "savings": self.savings}
        return 200, [{"id": 30, "name": "StadiumUpgrade"}]

    def put(self, path):
        if path.endswith("/claim"):
            part_id = int(path.split("/")[-2])
            self.calls.append(("claim", part_id))
            if self.claim_status == 200:
                done = next(p for p in self.parts if p.get("id") == part_id)
                done.pop("countdownTimer")
                done["level"] += 1
            return self.claim_status, {}
        self.calls.append("put")
        if self.balance == 0:
            self.balance, self.savings = self.savings, 0
        elif self.savings == 0:
            self.balance, self.savings = 0, self.balance
        else:  # split money: the first PUT deposits everything
            self.balance, self.savings = 0, self.balance + self.savings
        return 200, {"balance": self.balance, "savings": self.savings}

    def post(self, path, form):
        self.calls.append(("post", form["stadiumPartType"]))
        if self.balance < self.price:
            return 400, "no money"
        self.balance -= self.price
        return 200, {"countdownTimer": {"finishedTimestamp": NOW + 64800}}


@pytest.fixture(autouse=True)
def _fast(monkeypatch):
    monkeypatch.setattr(stadium, "PAUSE_BETWEEN_WRITES", 0)

    stadium.COUNTS["upgrades"] = 0


def run(client, confirm=True):
    return stadium.upgrade_club(client, TEAM, BASE, confirm, log=lambda m: None, now=NOW)


def test_pays_from_funds_without_touching_savings():
    client = FakeClient(balance=500, savings=900, price=300)
    assert run(client) == (0, [NOW + 64800])
    assert client.calls == [("post", 2)] and client.savings == 900


def test_uses_savings_and_puts_the_rest_back():
    client = FakeClient(balance=0, savings=1000, price=300)
    failed, wake = run(client)
    assert (failed, wake) == (0, [NOW + 64800])
    assert client.calls == ["put", ("post", 2), "put"]
    assert (client.balance, client.savings) == (0, 700)


def test_split_money_ends_up_paid_and_deposited():
    client = FakeClient(balance=100, savings=900, price=300)
    assert run(client)[0] == 0
    # post (refused), deposit-all, withdraw-all, post (accepted), deposit what is left
    assert client.calls == [("post", 2), "put", "put", ("post", 2), "put"]
    assert client.savings == 700 and client.balance == 0


def test_not_enough_even_with_savings_changes_nothing_and_waits_for_new_money():
    client = FakeClient(balance=0, savings=100, price=300)
    assert run(client) == (0, [])
    assert (client.balance, client.savings) == (0, 100)
    client.calls.clear()
    assert run(client) == (0, [])
    assert client.calls == []  # no new money: savings left alone
    client.savings = 500  # a player was sold
    assert run(client)[0] == 0 and ("post", 2) in client.calls


def test_dry_run_writes_nothing():
    client = FakeClient(balance=0, savings=1000, price=300)
    assert run(client, confirm=False) == (0, [])
    assert client.calls == []


def test_running_upgrade_only_gives_the_wake_time():
    client = FakeClient(1000, 1000, 1, parts=[part(0, 0), part(1, 0, ends=NOW + 99), part(2, 3)])
    assert run(client) == (0, [NOW + 99])
    assert client.calls == []


def finished(kind, level, part_id):
    p = part(kind, level, ends=NOW - 60)
    p["id"] = part_id
    return p


def test_a_finished_upgrade_is_to_collect_until_claimed():
    done = finished(2, 0, 7)
    assert to_claim([done, part(1, 0)], NOW) == [done]
    done["countdownTimer"]["isClaimed"] = True
    assert to_claim([done], NOW) == []
    assert to_claim([part(2, 0, ends=NOW + 5)], NOW) == []  # still running


def test_collects_the_finished_one_before_starting_the_next():
    client = FakeClient(balance=500, savings=0, price=300, parts=[part(0, 0), part(1, 1), finished(2, 0, 7)])
    assert run(client) == (0, [NOW + 64800])
    assert client.calls == [("claim", 7), ("post", 2)]  # same part again: it went 0 -> 1, the next level is still to do
    client = FakeClient(balance=500, savings=0, price=300, parts=[part(0, 0), part(1, 0), finished(2, 0, 7)])
    assert run(client) == (0, [NOW + 64800])
    assert client.calls == [("claim", 7), ("post", 1)]  # the pitch to 1 next (owner, 2026-10-25)


def test_never_starts_over_an_uncollected_one():
    client = FakeClient(balance=500, savings=0, price=300, parts=[part(0, 0), part(1, 0), finished(2, 0, 7)])
    client.claim_status = 400
    assert run(client) == (1, [])
    assert client.calls == [("claim", 7)]
    assert run(client) == (1, [])
    assert client.calls == [("claim", 7)]  # refused today: not asked again every round


def test_dry_run_only_says_it_would_collect():
    client = FakeClient(balance=500, savings=0, price=300, parts=[part(0, 0), part(1, 0), finished(2, 0, 7)])
    said = []
    stadium.upgrade_club(client, TEAM, BASE, False, log=said.append, now=NOW)
    assert client.calls == [] and any("recolheria" in line for line in said)


def test_logs_what_the_upgrade_cost():
    said = []
    client = FakeClient(balance=0, savings=1000, price=300)
    stadium.upgrade_club(client, TEAM, BASE, True, log=said.append, now=NOW)
    assert said[-1].endswith("melhoria iniciada · custou 300")


def test_a_stadium_event_is_an_upgrade_shorter_than_18_h_and_its_spending_is_kept_per_event():
    from osmbot.stadium.policy import event_key, stadium_event
    from osmbot.training.policy import boost_product

    assert stadium_event(240) and not stadium_event(1080) and not stadium_event(None)
    events = [{"nome": "Super Staff", "inicio": "2026-10-27", "tags": ["treinos"]},
              {"nome": "Top Facilities", "inicio": "2026-10-28", "tags": ["treinos", "estadio"]}]
    assert event_key(events, "2026-10-28") == "Top Facilities 2026-10-28"
    assert event_key(events[:1], "2026-10-28") == "2026-10-28"
    products = [{"id": 551, "name": "StadiumBoostCost", "increment": 4, "value": 4},
                {"id": 548, "name": "StadiumBoostCost", "increment": 1, "value": 1},
                {"id": 9, "name": "TrainingBoostCost", "increment": 4, "value": 8}]
    assert boost_product(products, 3.5 * 3600, "StadiumBoostCost")["value"] == 4
    assert boost_product(products, 20 * 60, "StadiumBoostCost")["value"] == 1


def test_the_running_upgrade_is_boosted_only_within_the_budget(monkeypatch):
    import time
    from osmbot.game import stadium

    monkeypatch.setattr(stadium, "PAUSE_BETWEEN_WRITES", 0)
    part = {"id": 7, "stadiumPartType": 2, "countdownTimer": {"finishedTimestamp": time.time() + 3.5 * 3600}}

    class Game:
        writes = []

        def get(self, path):
            return 200, {"leagues/1/teams/2/stadium": {"stadiumParts": [part]}, "user/bosscoinwallet": {"amount": 100}}[path]

        def request(self, method, path, form):
            self.writes.append((method, path, form))
            return 200, {}

    products = [{"id": 551, "name": "StadiumBoostCost", "increment": 4, "value": 4}]
    game, said = Game(), []
    assert stadium._boost_running(game, {"name": "C"}, "leagues/1/teams/2", products, 3, said.append) == 0
    assert stadium._boost_running(game, {"name": "C"}, "leagues/1/teams/2", products, 4, said.append) == 4
    assert game.writes == [("PUT", "leagues/1/teams/2/stadiumparts/7/boost", {"productId": 551})]
    assert "acelerada com 4 boss coins" in said[0]
