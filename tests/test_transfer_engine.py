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
    assert describe_sales(appeared, "Liga", lambda m: f"{m} €") == "SALE novos (Liga): 1 · DEF 84 J4 (25 anos) 120 €"
