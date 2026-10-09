import json

from osmbot.game import refusals


def test_only_a_real_no_counts():
    assert refusals.is_refusal(400) and refusals.is_refusal(404)
    for status in (200, 401, 408, 429, 500, 503):
        assert not refusals.is_refusal(status)


def test_each_kind_of_wait():
    assert refusals.still_blocked({"week": 14}, week=14) and not refusals.still_blocked({"week": 14}, week=15)
    assert refusals.still_blocked({"day": "2026-10-09"}, day="2026-10-09") and not refusals.still_blocked({"day": "2026-10-09"}, day="2026-10-10")
    assert refusals.still_blocked({"until": 100}, now=50) and not refusals.still_blocked({"until": 100}, now=100)
    assert refusals.still_blocked({"money": 10}, money=10) and not refusals.still_blocked({"money": 10}, money=11)


def test_the_game_day_changes_at_4_utc():
    from datetime import datetime, timezone

    assert refusals.game_day(datetime(2026, 10, 10, 3, 59, tzinfo=timezone.utc).timestamp()) == "2026-10-09"
    assert refusals.game_day(datetime(2026, 10, 10, 4, 0, tzinfo=timezone.utc).timestamp()) == "2026-10-10"


def test_noted_once_kept_on_disk_and_dropped_with_a_new_version():
    said = []
    refusals.refuse("médico:pôr:x:1", said.append, "recusado", week=14)
    refusals.refuse("médico:pôr:x:1", said.append, "recusado", week=14)
    assert said == ["recusado"] and refusals.blocked("médico:pôr:x:1", week=14)
    data = json.loads(refusals.FILE.read_text(encoding="utf-8"))
    refusals.FILE.write_text(json.dumps({**data, "version": "0.0.1"}), encoding="utf-8")
    assert not refusals.blocked("médico:pôr:x:1", week=14)  # another version wrote it: a fresh chance
    refusals.refuse("estádio:x", money=5)
    refusals.forget("estádio:x")
    assert not refusals.blocked("estádio:x", money=5)
