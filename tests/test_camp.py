"""Camp + secret training 10 min before the match, by the owner's lamp (D-103)."""
from osmbot.game import camp
from osmbot.prematch import camp as rules

MATCH = 1_000_000.0
WEEK = 12
BASE = "leagues/1/teams/2"
TEAM = {"name": "Clube A", "leagueId": 1, "id": 2}
KEY = "1_2"
PRODUCTS = ([{"id": 2 + n, "name": "Camp", "value": v} for n, v in enumerate((10, 20, 50, 100, 200, 500))]
            + [{"id": 8 + n, "name": "Secret", "value": 3} for n in range(6)])
MATCHES = [{"weekNr": w, "matchType": 0, "homeTeamId": 2, "awayTeamId": 3} for w in (5, 9, 13)]


def test_counts_the_seasons_camps_as_the_site():
    trainings = [{"type": 2, "week": 4}, {"type": 1, "week": 4}, {"type": 2, "week": 8}, {"type": 2, "week": 30}]
    assert rules.used(trainings, rules.CAMP) == 3  # without the matches: all of them [S]
    assert rules.used(trainings, rules.CAMP, MATCHES, 2) == 2  # week 30 + 1 is no match of this season
    item = rules.offer(trainings, PRODUCTS, WEEK, MATCHES, 2)
    assert item["camp"]["value"] == 50 and item["camp_nr"] == 3  # the 3rd camp of the season
    assert item["secret"]["value"] == 3 and item["total"] == 53
    assert rules.question("Clube A", "Rival", item, "20:41") == \
        "Clube A × Rival: estágio n.º 3 (50 BC) + treino secreto (3 BC) = 53 BC às 20:41. Ligar?"


def test_booked_for_the_next_match_and_none_left():
    booked = [{"type": 2, "week": WEEK}]
    item = rules.offer(booked, PRODUCTS, WEEK)
    assert item["camp_booked"] and item["camp"] is None and item["total"] == 3
    assert rules.why_not(item) is None and rules.to_book(item) == [(rules.SECRET, item["secret"])]
    full = [{"type": 2, "week": w} for w in range(6)]
    assert rules.why_not(rules.offer(full, PRODUCTS, WEEK)) == "Sem estágios nesta época (6 de 6)"
    both = rules.offer(booked + [{"type": 1, "week": WEEK}], PRODUCTS, WEEK)
    assert rules.why_not(both) == "Estágio e treino secreto já marcados"


def test_decide_by_the_clock_and_the_price():
    item = rules.offer([], PRODUCTS, WEEK)
    light = rules.lamp(item, WEEK, MATCH, MATCH - 3600)
    assert rules.decide(None, item, WEEK, MATCH, MATCH - 300) == "none"
    assert rules.decide(light, item, WEEK, MATCH, MATCH - rules.LEAD - 1) == "wait"
    assert rules.decide(light, item, WEEK, MATCH, MATCH - rules.LEAD) == "book"
    assert rules.decide(light, item, WEEK, MATCH, MATCH - 30) == "late"
    assert rules.decide(light, item, WEEK + 1, MATCH, MATCH - 300) == "none"  # another round: not this lamp
    dearer = rules.offer([{"type": 2, "week": 1}], PRODUCTS, WEEK)  # a camp done by hand meanwhile: 20, not 10
    assert rules.decide(light, dearer, WEEK, MATCH, MATCH - 300) == "dearer"
    assert [k for k, _ in rules.to_book(item)] == [rules.SECRET, rules.CAMP]  # the secret training first


class FakeClient:
    def __init__(self, trainings=None, coins=500, status=200):
        self.trainings, self.coins, self.status = list(trainings or []), coins, status
        self.posts = []

    def get(self, path):
        if path == "bosscoinproducts":
            return 200, PRODUCTS
        if path == "user/bosscoinwallet":
            return 200, {"amount": self.coins}
        if path.endswith("/teamtrainings"):
            return (200, self.trainings) if self.trainings else (404, "")
        raise AssertionError(path)

    def post(self, path, form):
        self.posts.append((path, form))
        if self.status != 200:
            return self.status, "no"
        price = next(p["value"] for p in PRODUCTS if p["id"] == form["productId"])
        self.coins -= price
        self.trainings.append({"type": form["type"], "week": WEEK})
        return 200, {}


def _book(client, now, lines):
    camp._products.clear()
    return camp.book_club(client, TEAM, BASE, KEY, WEEK, MATCH, now, True, lines.append)


def test_books_both_at_10_minutes_and_puts_the_lamp_out(monkeypatch):
    monkeypatch.setattr(camp.time, "sleep", lambda s: None)
    item = rules.offer([], PRODUCTS, WEEK)
    camp.set_lamp(KEY, rules.lamp(item, WEEK, MATCH, MATCH - 3600))
    client, lines = FakeClient(), []
    assert _book(client, MATCH - 3600, lines) == MATCH - rules.LEAD and not client.posts  # before: wait
    assert _book(client, MATCH - 500, lines) is None
    assert client.posts == [(f"{BASE}/teamtrainings", {"type": 1, "productId": 8}),
                            (f"{BASE}/teamtrainings", {"type": 2, "productId": 2})]
    assert client.coins == 487 and lines[-1].startswith("Estágio + secreto: Clube A,") and lines[-1].endswith("13 BC")
    assert camp.lamp(KEY) is None


def test_never_dearer_than_accepted_and_retries_a_failure(monkeypatch):
    monkeypatch.setattr(camp.time, "sleep", lambda s: None)
    camp.set_lamp(KEY, rules.lamp(rules.offer([], PRODUCTS, WEEK), WEEK, MATCH, MATCH - 3600))
    client, lines = FakeClient(status=500), []
    assert _book(client, MATCH - 500, lines) == MATCH - 500 + rules.RETRY and camp.lamp(KEY)  # again in 1 min
    client, lines = FakeClient(trainings=[{"type": 2, "week": 1}]), []  # a camp by hand: now 20 BC
    assert _book(client, MATCH - 400, lines) is None and not client.posts
    assert lines == ["! Estágio não ligado: Clube A (custa agora 23 BC, aceitaste 13 BC)"] and camp.lamp(KEY) is None


def test_a_lamp_for_a_match_gone_by_goes_out():
    camp.set_lamp(KEY, {"semana": WEEK - 1, "jogo": MATCH - 86400})
    assert _book(FakeClient(), MATCH - 300, []) is None and camp.lamp(KEY) is None


def test_the_cards_lamp_says_the_price_and_asks():
    from osmbot.gui.view import late_view

    item = rules.offer([{"type": 2, "week": 4}], PRODUCTS, WEEK)
    club = {"name": "Clube A", "key": KEY, "match": MATCH, "week": WEEK,
            "prep": {"late": {"on": False, "accepted": None, "offer": item, "why_not": None, "opponent": "Rival"}}}
    late = late_view(club, MATCH - 7200)
    assert late["can"] and not late["on"] and late["tip"].startswith("Estágio n.º 2 (20 BC) + treino secreto (3 BC) = 23 BC.")
    assert late["question"].startswith("Clube A × Rival: estágio n.º 2 (20 BC)") and late["lamp"]["total"] == 23
    club["prep"]["late"]["why_not"] = "Sem jogo nesta jornada"
    assert not late_view(club, MATCH - 7200)["can"]
    assert late_view(club, MATCH + 1) is None  # the match went by
