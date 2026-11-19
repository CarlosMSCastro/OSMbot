from datetime import datetime

from osmbot import logs
from osmbot.game import wallet


def test_the_change_is_split_into_the_bot_s_kinds_and_what_is_left():
    assert wallet.split(-20, {"amigáveis": -8, "vídeos da loja": 3}) == {"amigáveis": -8, "vídeos da loja": 3, "fora do bot": -15}
    assert wallet.split(-8, {"amigáveis": -8}) == {"amigáveis": -8}
    assert wallet.split(5, {}) == {"fora do bot": 5}


def test_the_summary_line_follows_the_order_and_shows_the_balance():
    line = wallet.summary_line("2026-10-28", {"fora do bot": -15, "amigáveis": -56, "vídeos da loja": 80}, 3275)
    assert line == "Boss coins (2026-10-28): +80 vídeos da loja · -56 amigáveis · -15 fora do bot · saldo 3 275"


def test_check_records_each_change_and_writes_the_day_before_s_summary(monkeypatch):
    recorded, said = [], []
    monkeypatch.setattr(logs, "record", lambda kind, data: recorded.append((kind, data)))
    day = datetime(2026, 10, 28, 12)
    wallet.check(100, said.append, day)  # first reading: only the balance
    assert recorded == []
    wallet.note("amigáveis", -4)
    wallet.check(90, said.append, day)
    assert recorded == [("carteira", {"saldo": 90, "antes": 100, "diferenca": -10, "partes": {"amigáveis": -4, "fora do bot": -6}})]
    wallet.check(90, said.append, day)  # no change: nothing
    assert len(recorded) == 1 and said == []
    wallet.check(95, said.append, datetime(2026, 10, 29, 9))
    assert said == ["Boss coins (2026-10-28): -4 amigáveis · -6 fora do bot · saldo 90"]


def test_a_drop_with_a_purchase_seen_is_transfers_not_outside():
    from osmbot.game import wallet

    assert wallet.split(-5, {}, 1) == {"transferências": -5}
    assert wallet.split(-5, {}, 0) == {"fora do bot": -5}
    assert wallet.split(3, {}, 1) == {"fora do bot": 3}  # a gain is never a transfer's


def test_a_purchase_seen_after_the_drop_moves_it_to_transfers(tmp_path, monkeypatch):
    from datetime import datetime, timedelta

    from osmbot.game import wallet

    monkeypatch.setattr(wallet, "FILE", tmp_path / "carteira.json")
    monkeypatch.setattr(wallet.logs, "record", lambda *a, **k: None)
    monkeypatch.setattr(wallet, "_history", [])
    monkeypatch.setattr(wallet, "_purchases", [])
    t0 = datetime(2026, 11, 19, 12, 0)
    wallet.check(100, now=t0)
    wallet.check(99, now=t0 + timedelta(minutes=1))  # the drop first: "fora do bot"
    assert wallet._history[-1]["parts"] == {"fora do bot": -1}
    wallet.note_purchases(["Torres"], now=t0 + timedelta(minutes=4))  # the squad is read later
    assert wallet._history[-1]["parts"] == {"transferências": -1} and wallet._history[-1]["players"] == ["Torres"]
    assert wallet._load()["totais"] == {"transferências": -1, "fora do bot": 0}
    wallet.note_purchases(["Konan"], now=t0 + timedelta(minutes=10))  # the purchase first, the drop after
    wallet.check(98, now=t0 + timedelta(minutes=11))
    assert wallet._history[-1]["parts"] == {"transferências": -1} and wallet._history[-1]["players"] == ["Konan"]
