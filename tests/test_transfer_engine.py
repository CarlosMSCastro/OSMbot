import json

from osmbot.transfers.engine import classify, describe, observe


def game(listing, price):
    return {"id": listing, "price": price, "teamId": 99, "team": {"isForeignTeam": True, "userId": 0},
            "player": {"id": 1000 + listing, "value": price}}


def person(listing, player, price, value, user=5, age=25):
    return {"id": listing, "price": price, "teamId": 3, "timeStampForSale": 100.0,
            "team": {"isForeignTeam": False, "userId": user},
            "player": {"id": player, "value": value, "age": age, "position": 2, "statOvr": 80, "statAtt": 90, "statDef": 40}}


def test_a_round_of_the_engine_and_what_left_the_list():
    state, record = observe(None, [game(1, 1000), person(2, 20, 250, 100, user=7)], now=1000.0, owner=7)
    assert record is None  # the first read only learns the list
    state, record = observe(state, [game(1, 1000), person(2, 20, 250, 100, user=7)], now=1180.0, owner=7)
    assert record is None  # nothing changed
    state = json.loads(json.dumps(state))  # kept in a file between reads
    state, record = observe(state, [game(1, 990), game(3, 500)], now=1360.0, owner=7)
    assert record["descidas"] == 1 and record["jogo_novos"] == 1 and record["antes"] == 1180.0 and not record["lacuna"]
    assert record["sairam"] == [20]
    row = record["a_venda"][0]
    assert row["dono"] and row["utilizador"] and row["do_maximo"] == 1.0 and row["idade"] == 25 and row["desde"] == 100.0


def test_sold_or_taken_off_and_the_log_line():
    state, _ = observe(None, [game(1, 1000), person(2, 20, 250, 100, user=7), person(4, 40, 100, 100)], 1000.0, owner=7)
    _, record = observe(state, [game(1, 990)], 1180.0, owner=7)
    record = classify(record, [{"player": {"id": 20}, "timestamp": 1100.0}, {"player": {"id": 40}, "timestamp": 50.0}])
    assert record["vendidos"] == [{"jogador": 20, "quando": 1100.0}] and record["retirados"] == [40]
    line = describe(record, "Liga", lambda ts: f"t{int(ts)}")
    assert line == "Motor de transferências (Liga): passou entre t1000 e t1180; vendidos 1 de 2 à venda (teus: 1 de 1)"


def test_reads_far_apart_are_marked():
    state, _ = observe(None, [game(1, 1000)], 0.0)
    _, record = observe(state, [game(1, 900)], 3600.0)
    assert record["lacuna"] and record["sairam"] == []


def test_the_watch_saves_one_record_per_change_and_skips_the_same_read(tmp_path, monkeypatch):
    from osmbot import logs
    from osmbot.game import market

    repo = tmp_path / "repo"
    (repo / "src" / "osmbot").mkdir(parents=True)
    (repo / "pyproject.toml").write_text("", encoding="utf-8")
    monkeypatch.setenv("OSMBOT_REPO", str(repo))

    class Client:
        def get(self, path):
            assert path == "leagues/9/transfers"
            return 200, [{"player": {"id": 20}, "timestamp": 1100.0}]

    lines = []
    market.watch(Client(), 9, "Liga", [game(1, 1000), person(2, 20, 250, 100)], owner=7, log=lines.append, now=1000.0)
    assert market.watch(Client(), 9, "Liga", [game(1, 990)], owner=7, log=lines.append, now=1030.0) is None  # same read
    market.watch(Client(), 9, "Liga", [game(1, 990)], owner=7, log=lines.append, now=1180.0)
    saved = (repo / "logs" / logs.machine() / "transferencias" / "motor" / "9.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(saved) == 1 and json.loads(saved[0])["vendidos"][0]["jogador"] == 20
    assert len(lines) == 1 and lines[0].startswith("Motor de transferências (Liga): passou entre ")
    assert lines[0].endswith("; vendidos 1 de 1 à venda (teus: 0 de 0)")


def test_sale_players_appear_and_leave():
    from osmbot.transfers.engine import describe_sales, sale_changes, sale_rows

    def item(lid, price, value, user=None, pos=3):
        return {"id": lid, "price": price, "team": {"userId": user, "isForeignTeam": True},
                "player": {"id": lid * 10, "name": f"J{lid}", "position": pos, "statDef": 80 + lid, "age": 25, "value": value}}

    market = [item(1, 140, 100), item(2, 160, 100), item(3, 100, 100, user=5)]
    rows = sale_rows(market)
    assert list(rows) == ["1"] and rows["1"]["razao"] == 1.4  # 1.6× is no SALE; a manager's never counts
    state, appeared, gone = sale_changes(None, rows, 1000)
    assert appeared == [] and state["1"]["visto"] == 1000  # the first read only learns
    state, appeared, gone = sale_changes(state, sale_rows([item(4, 120, 100)]), 1600)
    assert [r["anuncio"] for r in appeared] == [4] and gone[0]["anuncio"] == 1 and gone[0]["durou"] == 600
    state, _, _ = sale_changes(state, sale_rows([item(4, 110, 100)]), 2000)  # the game lowered the price
    _, _, gone = sale_changes(state, {}, 2600)
    assert (gone[0]["preco_inicial"], gone[0]["preco"], gone[0]["durou"]) == (120, 110, 1000)
    every = sale_rows(market, ratio=float("inf"))
    assert list(every) == ["1", "2"]  # all the game's listings, SALE or not; still never a manager's
    assert describe_sales(appeared, "Liga", lambda m: f"{m} €") == "SALE novos (Liga): 1 · DEF 84 J4 (25 anos) 120 €"


def test_sale_options_are_the_games_sale_players_of_that_position_the_club_can_pay_for_best_first():
    from osmbot.transfers.engine import sale_options

    def item(aid, pos, rating, price, user=None):
        return {"id": aid, "price": price, "team": {"userId": user},
                "player": {"id": aid, "name": f"Jogador {aid}", "position": pos, "age": 25, "value": price * 2,
                           "statDef": rating, "statAtt": rating, "statOvr": rating}}

    market = [item(1, 3, 80, 5_000_000), item(2, 3, 88, 9_000_000), item(3, 3, 90, 30_000_000),
              item(4, 1, 95, 1_000_000), item(5, 3, 99, 2_000_000, user=7)]
    options = sale_options(market, "DEF", budget=10_000_000)
    assert [o["nome"] for o in options] == ["Jogador 2", "Jogador 1"]  # too dear, other position and a manager's are out


def _sale(aid, pos, rating, price, value):
    return {"id": aid, "price": price, "team": {"userId": None, "isForeignTeam": True},
            "player": {"id": aid, "name": f"S{aid}", "position": pos, "age": 26, "value": value,
                       "statDef": rating, "statAtt": rating, "statOvr": rating}}


def _starter(pid, pos, rating, lineup=1):
    return {"id": pid, "name": f"T{pid}", "position": pos, "lineup": lineup, "statDef": rating, "statAtt": rating, "statOvr": rating}


def test_sale_picks_are_the_affordable_sale_players_by_resale_profit_with_reinforcements_and_bargains():
    from osmbot.transfers.engine import resale, sale_picks

    assert resale(10e6) == 25e6 and resale(50e6) == 0.75 * 125e6  # the maximum, 75 % of it above 100 M (THEORY.md 7)
    players = [_starter(1, 3, 79), _starter(2, 3, 90, lineup=2), _starter(3, 3, 95, lineup=14)]  # the bench does not count
    market = [_sale(1, 3, 85, 14.3e6, 11e6),  # beats the weakest DEF (79), at 1.3×
              _sale(2, 1, 70, 12e6, 10e6),  # to sell again, at 1.2×: a bargain, the best bet
              _sale(3, 3, 99, 30e6, 25e6),  # too dear
              _sale(4, 1, 60, 1.2e6, 1e6),  # worth too little to sell again (under 10 M)
              _sale(5, 1, 70, 17e6, 10e6),  # no "SALE" (1.7×): still counts
              _sale(6, 1, 75, 13e6, 10e6),  # 1.3× like S1, smaller profit: after it
              _sale(7, 2, 70, 19e6, 15e6)]
    picks = sale_picks(market, players, money=20e6, count=5)
    assert [(p["nome"], p["reforco"], p["pechincha"]) for p in picks] == [
        ("S2", False, True), ("S7", False, False), ("S1", True, False), ("S6", False, False), ("S5", False, False)]
    assert picks[2]["lucro"] == 27.5e6 - 14.3e6 and picks[2]["fraco"] == "T1 79"
    assert len(sale_picks(market, players, money=20e6)) == 3
    big = _sale(8, 3, 90, 19e6, 12e6)  # a reinforcement is shown whatever its value
    assert sale_picks([big], players, 20e6)[0]["reforco"] and not sale_picks([_sale(9, 1, 90, 75e6, 50e6)], players, 80e6)


def test_reinforcements_go_by_specific_position_below_the_average_and_a_listed_starter_counts_as_his_cover():
    from osmbot.transfers.engine import sale_picks, weak_spots

    def player(pid, spec, rating, lineup):
        return {**_starter(pid, 2, rating, lineup), "specificPosition": spec}

    def offer(aid, spec, rating):
        item = _sale(aid, 2, rating, 100e6, 80e6)  # valued 80 M: never a pick to sell again
        item["player"]["specificPosition"] = spec
        return item

    mc, mco, gr = 2, 1, 6
    players = [player(1, mc, 96, 6), player(2, mco, 115, 7), player(3, gr, 118, 1),
               player(4, mc, 111, 14), player(5, mco, 100, 15)]
    mine = {"id": 50, "price": 55e6, "team": {"userId": 7, "isForeignTeam": False}, "player": {"id": 1}}  # MC 96 listed
    assert weak_spots(players, set()) == {mc: (96, "T1 96")}  # MCO 115 and GR 118 are above the average (109.7)
    assert weak_spots(players, {1}) == {mc: (111, "T4 111")}  # the listed MC counts as the MC on the bench (average 114.7)
    market = [offer(10, mco, 118), offer(11, mc, 105), offer(12, mc, 112), mine]
    picks = sale_picks(market, players, money=200e6)
    assert [(p["nome"], p["fraco"]) for p in picks] == [("S12", "T4 111")]  # MCO 118: not an MC; MC 105 < 111
    alone = [player(1, mc, 96, 6), player(2, mco, 115, 7), player(3, gr, 118, 1)]
    assert weak_spots(alone, {1}) == {mc: (0, "T1 à venda")}  # nobody to take his place: the place is open


def test_a_league_sells_at_the_maximum_when_one_of_its_clubs_sold_at_2_4_times_the_value_lately():
    from osmbot.transfers.engine import sells_at_max

    now = 1_000_000

    def sale(price, value, foreign=False, ago=3600):
        return {"price": price, "value": value, "timestamp": now - ago, "sourceTeam": {"id": 4, "isForeignTeam": foreign}}

    assert sells_at_max([sale(25, 10)], now)
    assert not sells_at_max([sale(20, 10)], now)  # 2×: below the maximum
    assert not sells_at_max([sale(25, 10, foreign=True)], now)  # bought by the league from outside, not sold by it
    assert not sells_at_max([sale(25, 10, ago=4 * 86400)], now)  # too long ago
