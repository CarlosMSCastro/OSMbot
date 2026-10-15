from osmbot.game import refusals, savings
from osmbot.savings.policy import LEAD, WINDOW, deposit_due, wake_at

MATCH = 100_000.0
BASE = "leagues/1/teams/2"
TEAM = {"name": "Clube A", "leagueId": 1, "id": 2}


def test_deposit_only_in_the_last_minutes_before_the_match():
    assert not deposit_due(MATCH, MATCH - WINDOW - 1)
    assert deposit_due(MATCH, MATCH - WINDOW) and deposit_due(MATCH, MATCH - 1)
    assert not deposit_due(MATCH, MATCH) and not deposit_due(None, MATCH)
    assert wake_at(MATCH, MATCH - 3600) == MATCH - LEAD
    assert wake_at(MATCH, MATCH - LEAD) is None


class FakeClient:
    """The empty PUT moves everything to the other side; with money on both sides it brings savings out
    (``split_out``) or deposits all (the stadium's assumption): either way the bot must end with funds at 0."""

    def __init__(self, balance, saved, split_out=True, status=200):
        self.balance, self.saved, self.split_out, self.status = balance, saved, split_out, status
        self.puts = 0

    def get(self, path):
        if path.endswith("/timers"):
            return 200, [{"type": 14, "finishedTimestamp": MATCH}]
        return 200, {"balance": self.balance, "savings": self.saved}

    def put(self, path):
        self.puts += 1
        if self.status != 200:
            return self.status, "no"
        if self.balance and self.saved and self.split_out:
            self.balance, self.saved = self.balance + self.saved, 0
        elif self.balance:
            self.balance, self.saved = 0, self.balance + self.saved
        else:
            self.balance, self.saved = self.saved, 0
        return 200, {"balance": self.balance, "savings": self.saved}


def test_deposits_everything_even_when_money_is_split():
    for split_out in (True, False):
        client, lines = FakeClient(1_200_000, 5_000_000, split_out), []
        assert savings.deposit_club(client, TEAM, BASE, True, MATCH - 300, lines.append) == (0, None)
        assert (client.balance, client.saved) == (0, 6_200_000)
        assert lines == ["Poupança: Clube A depositou 1,2 M antes do jogo (poupança 6,2 M)"]


def test_nothing_to_do_with_empty_funds_or_too_early():
    client = FakeClient(0, 5_000_000)
    assert savings.deposit_club(client, TEAM, BASE, True, MATCH - 300) == (0, None) and client.puts == 0
    client = FakeClient(1_000_000, 0)
    assert savings.deposit_club(client, TEAM, BASE, True, MATCH - 7200) == (0, MATCH - LEAD) and client.puts == 0


def test_a_refused_deposit_is_not_repeated_that_day():
    client, lines = FakeClient(1_000_000, 0, status=400), []
    assert savings.deposit_club(client, TEAM, BASE, True, MATCH - 300, lines.append) == (0, None)
    savings.deposit_club(client, TEAM, BASE, True, MATCH - 200, lines.append)
    assert client.puts == 1 and len(lines) == 1 and lines[0].startswith("! Poupança")


def test_in_the_pre_season_it_deposits_before_each_day_ends():
    FIRST = MATCH + 2 * 86400  # the first league match; the day ends at the same hour
    class PreSeason(FakeClient):
        def get(self, path):
            return (200, {"weekNr": -2}) if path == "leagues/1" else super().get(path)

    client = PreSeason(1_000_000, 0)
    client.get = lambda path, get=client.get: (200, [{"type": 14, "finishedTimestamp": FIRST}]) if path.endswith("/timers") else get(path)
    assert savings.deposit_club(client, TEAM, BASE, True, MATCH - 300) == (0, None)  # 2 days before the first match
    assert client.saved == 1_000_000
    client = PreSeason(1_000_000, 0)
    client.get = lambda path, get=client.get: (200, [{"type": 14, "finishedTimestamp": FIRST}]) if path.endswith("/timers") else get(path)
    assert savings.deposit_club(client, TEAM, BASE, True, MATCH - 7200) == (0, MATCH - LEAD)
