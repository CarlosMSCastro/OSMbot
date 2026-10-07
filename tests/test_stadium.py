import pytest

from osmbot.game import stadium
from osmbot.stadium.policy import next_part, running_until

NOW = 1000.0
BASE = "leagues/1/teams/2"
TEAM = {"name": "Club", "leagueId": 1, "id": 2}


def part(kind, level, top=3, ends=None):
    p = {"stadiumPartType": kind, "level": level, "stadiumPartLevels": [{"level": i} for i in range(top + 1)]}
    if ends:
        p["countdownTimer"] = {"finishedTimestamp": ends, "isClaimed": False}
    return p


def test_order_is_training_then_pitch_then_capacity():
    assert next_part([part(0, 0), part(1, 0), part(2, 0)], NOW) == 2
    assert next_part([part(0, 0), part(1, 0), part(2, 3)], NOW) == 1
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

    def get(self, path):
        if path.endswith("/stadium"):
            return 200, {"stadiumParts": self.parts}
        if path.endswith("balanceandsavings"):
            return 200, {"balance": self.balance, "savings": self.savings}
        return 200, [{"id": 30, "name": "StadiumUpgrade"}]

    def put(self, path):
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
    stadium._last_refused.clear()
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
