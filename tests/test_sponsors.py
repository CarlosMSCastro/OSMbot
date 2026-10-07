import pytest

from osmbot.game import sponsors
from osmbot.sponsors.policy import free_sides, next_choice, ranked_offers

TEAM = {"name": "Club"}
BASE = "leagues/1/teams/2"


def offer(id, weeks, revenue):
    return {"id": id, "name": f"S{id}", "weeks": weeks, "sponsorRevenueForTeam": revenue}


def own(id, side, weeks_left=1):
    return {"id": id, "side": side, "weeksLeft": weeks_left}


def test_best_revenue_per_round_wins_and_a_shorter_contract_breaks_ties():
    offers = [offer(1, 3, 284), offer(2, 2, 289), offer(3, 1, 287), offer(4, 1, 289)]
    assert [o["id"] for o in ranked_offers(offers)] == [4, 2, 3, 1]


def test_free_slots_are_the_ones_without_an_active_contract():
    assert free_sides([own(1, 1), own(9, 3, weeks_left=0)]) == [2, 3, 4]


def test_the_best_goes_to_the_first_free_slot_and_refusals_move_on():
    offers = [offer(1, 1, 300), offer(2, 1, 200)]
    assert next_choice(offers, [own(7, 1)]) == (2, offers[0])
    assert next_choice(offers, [own(7, 1)], {(2, 1)}) == (2, offers[1])
    assert next_choice(offers, [own(7, 1)], {(2, 1), (2, 2)}) == (3, offers[0])


class FakeClient:
    def __init__(self, offers, current, refuse=()):
        self.offers, self.current, self.refuse, self.posts = offers, current, set(refuse), []

    def get(self, path):
        return 200, (self.offers if path.endswith("offers") else self.current)

    def post(self, path, form):
        side, sid = int(form["sponsorSide"]), int(form["sponsorId"])
        self.posts.append((side, sid))
        if (side, sid) in self.refuse:
            return 400, "no"
        self.current.append(own(sid, side))
        return 200, {}


@pytest.fixture(autouse=True)
def _fast(monkeypatch):
    monkeypatch.setattr(sponsors, "PAUSE_BETWEEN_WRITES", 0)
    sponsors._refused.clear()


def sign(client, confirm=True):
    return sponsors.sign_club(client, TEAM, BASE, confirm, log=lambda m: None)


def test_the_best_sponsor_goes_into_every_free_slot():
    client = FakeClient([offer(1, 1, 100), offer(2, 1, 300)], [own(9, 1)])
    assert sign(client) == 0
    assert client.posts == [(2, 2), (3, 2), (4, 2)]


def test_a_refused_repeat_falls_back_to_the_next_best():
    client = FakeClient([offer(1, 1, 100), offer(2, 1, 300)], [own(9, 1)], refuse={(3, 2), (4, 2)})
    assert sign(client) == 0
    assert client.posts == [(2, 2), (3, 2), (3, 1), (4, 2), (4, 1)]


def test_dry_run_signs_nothing():
    client = FakeClient([offer(1, 1, 100)], [])
    sign(client, confirm=False)
    assert client.posts == []


def test_refusals_are_remembered_between_passes():
    client = FakeClient([offer(1, 1, 100), offer(2, 1, 90)], [], refuse={(1, 1)})
    sign(client)
    client.current.clear()
    client.posts.clear()
    sign(client)
    assert (1, 1) not in client.posts
