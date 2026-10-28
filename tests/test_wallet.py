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
