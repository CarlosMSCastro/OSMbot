from datetime import datetime

from osmbot.analysis import videos
from osmbot.game.loop import video_record

T = datetime(2026, 11, 19, 2, 7).timestamp()


def test_each_video_tried_becomes_one_line():
    session = {"id": 1, "player": {"name": "J1"}}
    assert video_record("training", ("Clube A", session)) == {"tipo": "treino", "ok": True, "clube": "Clube A", "jogador": "J1"}
    assert video_record("shop", (), 1) == {"tipo": "loja", "ok": True, "coins": 1}
    failed = video_record("money", ("Clube A",), error=RuntimeError("o cartão de dinheiro não passou a visto"))
    assert failed["ok"] is False and failed["erro"].startswith("o cartão") and failed["clube"] == "Clube A"


def test_a_day_of_videos_filtered_with_the_totals():
    records = [{"t": T, "tipo": "treino", "ok": True, "clube": "A", "jogador": "J1", "pc": "PC1"},
               {"t": T + 60, "tipo": "loja", "ok": False, "erro": "sem anúncio", "pc": "PC1"},
               {"t": T + 120, "tipo": "loja", "ok": True, "coins": 1, "pc": "PC2"},
               {"t": T - 86400, "tipo": "loja", "ok": True, "coins": 1}]
    day = datetime.fromtimestamp(T).date()
    assert videos.days(records)[0] == day and len(videos.days(records)) == 2
    assert videos.summary(records, day) == "Loja 1 de 2 · Treino 1 de 1"
    assert [r["hora"] for r in videos.rows(records, day)] == ["02:09", "02:08", "02:07"]
    assert [r["resultado"] for r in videos.rows(records, day, "Passaram")] == ["passou (+1 coins)", "passou"]
    assert [r["motivo"] for r in videos.rows(records, day, "Falharam")] == ["sem anúncio"]
    assert len(videos.rows(records, day, kind="treino")) == 1
