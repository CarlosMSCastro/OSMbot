"""Relisting a player whose right price rose on the list (D-085)."""
from osmbot.transfers.relist import right_price, to_relist


def test_the_right_price_is_the_sites_maximum_or_75_percent_of_it_above_150_m():
    assert right_price(17_050_775) == 42_626_938  # the test of 2026-11-03: round(value × 250 / 100)
    assert right_price(80e6) == 150_000_000  # 200 M maximum → 75 %
    assert right_price(60e6) == 150_000_000  # exactly 150 M stays at 100 %
    assert right_price(10e6, max_percentage=300) == 30_000_000  # the game setting, when it differs


def test_relists_only_a_rise_of_2_percent_or_more():
    listings = [
        {"listing": 1, "player": 11, "name": "Evoluiu", "price": 38_355_880, "value": 17_050_775},  # 90 % → relist
        {"listing": 2, "player": 12, "name": "Ruído", "price": 190_041_738, "value": 101_891_651},  # 74,6 % of 75 %
        {"listing": 3, "player": 13, "name": "Passou os 150", "price": 140e6, "value": 64e6},  # 160 M → 120 M: down
        {"listing": 4, "player": 14, "name": "Grande", "price": 150e6, "value": 85e6},  # 75 % of 212,5 M = 159 M
        {"listing": 5, "player": 15, "name": "Sem valor", "price": 1e6, "value": 0},
    ]
    due = to_relist(listings)
    assert [(d["name"], d["new_price"]) for d in due] == [("Grande", 159_375_000), ("Evoluiu", 42_626_938)]


class FakeClient:
    def __init__(self, sell_status=200, delete_status=200):
        self.writes, self.sell_status, self.delete_status = [], sell_status, delete_status

    def get(self, path):
        if path.endswith("/players"):
            return 200, [{"id": 11, "fullName": "Evoluiu", "value": 17_050_775}, {"id": 12, "fullName": "Igual", "value": 10e6}]
        if path.endswith("/transferplayers/0"):
            return 200, [{"id": 901, "player": {"id": 11}, "price": 38_355_880, "timeStampForSale": 0},
                         {"id": 902, "player": {"id": 12}, "price": 25e6, "timeStampForSale": 0},
                         {"id": 903, "player": {"id": 99}, "price": 1e6}]  # someone else's
        if path.endswith("/gamesettings"):
            return 200, [{"name": "MaxSalePercentage", "value": 250}]
        raise AssertionError(path)

    def request(self, method, path, form=None):
        self.writes.append((method, path, form))
        return (self.delete_status if method == "DELETE" else self.sell_status), ""


def _run(client, confirm=True, now=200_000.0):
    from osmbot.game import relist

    relist._checked.clear()
    lines = []
    relist.PAUSE_BETWEEN_WRITES = 0
    failed = relist.relist_club(client, {"name": "Clube"}, "leagues/1/teams/2", confirm, now, log=lines.append)
    return failed, lines


def test_takes_the_player_off_and_lists_him_again_at_the_new_maximum(monkeypatch, tmp_path):
    from osmbot.game import refusals

    monkeypatch.setattr(refusals, "FILE", tmp_path / "recusas.json")
    client = FakeClient()
    failed, lines = _run(client)
    assert failed == 0
    assert client.writes == [("DELETE", "leagues/1/teams/2/transferplayers/901", None),
                             ("PUT", "leagues/1/teams/2/players/sell", {"playerId": 11, "price": 42_626_938})]
    assert lines[0].startswith("Relistado: Evoluiu (Clube) de ") and "(+11%)" in lines[0]


def test_a_dry_run_only_says_it_and_a_club_is_checked_every_30_minutes(monkeypatch, tmp_path):
    from osmbot.game import refusals, relist

    monkeypatch.setattr(refusals, "FILE", tmp_path / "recusas.json")
    client = FakeClient()
    _, lines = _run(client, confirm=False)
    assert client.writes == [] and lines[0].startswith("Relistaria Evoluiu")
    assert relist.relist_club(client, {"name": "Clube"}, "leagues/1/teams/2", False, 200_000.0 + 60, log=lines.append) == 0
    assert len(lines) == 1  # 1 minute later: not read again


def test_a_player_taken_off_whom_the_game_does_not_let_back_is_said_loudly(monkeypatch, tmp_path):
    from osmbot.game import refusals

    monkeypatch.setattr(refusals, "FILE", tmp_path / "recusas.json")
    client = FakeClient(sell_status=400)
    failed, lines = _run(client)
    assert failed == 1
    assert [w[0] for w in client.writes] == ["DELETE", "PUT", "PUT"]  # tried twice
    assert lines[-1].startswith("! Relistar: Evoluiu (Clube) saiu da lista") and "à mão" in lines[-1]


def test_a_refused_take_off_is_not_tried_again_that_day(monkeypatch, tmp_path):
    from osmbot.game import refusals

    monkeypatch.setattr(refusals, "FILE", tmp_path / "recusas.json")
    client = FakeClient(delete_status=404)  # sold meanwhile
    failed, _ = _run(client)
    assert failed == 0 and [w[0] for w in client.writes] == ["DELETE"]
    client.writes.clear()
    _run(client, now=200_000.0 + 3600)  # same game day (it changes at 04:00 UTC)
    assert client.writes == []


def test_the_relist_lines_have_an_english_version():
    from osmbot import i18n

    i18n.set_language("en", save=False)
    try:
        assert i18n.tr("Relistado: X (C) de 38,4 M para 42,6 M (+11%), estava à venda há 1 dia e 18h27") == \
            "Relisted: X (C) from 38,4 M to 42,6 M (+11%), listed for 1 day and 18h27"
        assert i18n.tr("relistar") == "relisting"
    finally:
        i18n.set_language("pt", save=False)
