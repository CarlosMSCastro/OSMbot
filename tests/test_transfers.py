import json

from osmbot import logs
from osmbot.game import transfers as game_transfers
from osmbot.transfers.history import due, merge


def row(tid, ts):
    return {"id": tid, "timestamp": ts, "value": 10, "price": 25}


def test_due_once_a_day():
    assert due(None, "2026-10-09")
    assert not due({"lido": "2026-10-09"}, "2026-10-09")
    assert due({"lido": "2026-10-08"}, "2026-10-09")


def test_merge_keeps_each_transfer_once_oldest_first():
    first, new = merge(None, {"id": 7, "name": "Liga"}, [row(2, 200), row(1, 100)], "2026-10-08")
    assert new == 2 and [r["id"] for r in first["transferencias"]] == [1, 2]
    second, new = merge(first, {"id": 7, "name": "Liga"}, [row(3, 300), row(2, 200)], "2026-10-09")
    assert new == 1
    assert [r["id"] for r in second["transferencias"]] == [1, 2, 3]
    assert second["lido"] == "2026-10-09" and second["liga"] == 7


class FakeClient:
    def __init__(self):
        self.gets = []

    def get(self, path):
        self.gets.append(path)
        if path == "user/accounts":
            return 200, {"teamSlots": {"0": {"team": {"leagueId": 5, "id": 1}}, "1": None}}
        if path == "leagues/5/transfers":
            return 200, [row(1, 100)]
        return 200, {"id": 5, "name": "Liga"}


def test_save_once_a_day_into_the_repo_logs(tmp_path, monkeypatch):
    monkeypatch.setattr(game_transfers, "repo_folder", lambda: tmp_path)
    monkeypatch.setattr(game_transfers, "machine", lambda: "PC")
    client = FakeClient()
    assert game_transfers.save_transfers(lambda: client, log=lambda m: None, today="2026-10-09") == 1
    saved = json.loads((tmp_path / "logs" / "PC" / "transferencias" / "5.json").read_text(encoding="utf-8"))
    assert saved["nome"] == "Liga" and len(saved["transferencias"]) == 1
    client.gets.clear()
    assert game_transfers.save_transfers(lambda: client, log=lambda m: None, today="2026-10-09") == 0
    assert "leagues/5/transfers" not in client.gets  # already read today


def test_no_repo_no_network():
    assert logs.repo_folder() is None  # conftest
    assert game_transfers.save_transfers(lambda: (_ for _ in ()).throw(AssertionError("network")), log=print) == 0
