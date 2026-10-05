import itertools

import pytest

from osmbot.models import Player, Position

_ids = itertools.count(1)


@pytest.fixture
def make_player():
    """Factory for synthetic players. Stats default to a flat 50."""

    def _make(
        position=Position.MID,
        age=25,
        att=50,
        ovr=50,
        deff=50,
        *,
        id=None,
        name=None,
        injured=False,
    ):
        pid = id if id is not None else next(_ids)
        return Player(
            id=pid,
            name=name or f"P{pid}",
            position=position,
            age=age,
            stat_att=att,
            stat_ovr=ovr,
            stat_def=deff,
            injured=injured,
        )

    return _make


@pytest.fixture(autouse=True)
def _isolated_from_the_game(monkeypatch, tmp_path):
    """No test may touch the real game, the real session or the real log."""
    from osmbot.game import loop

    monkeypatch.setattr(loop, "LOG_FILE", tmp_path / "bot.log")
    monkeypatch.setattr(loop, "read_slots", lambda client: [])
    monkeypatch.setattr(loop, "_shop_ads", lambda dry_run: 0)
    monkeypatch.setattr(loop, "_training_ads", lambda dry_run: 0)
    monkeypatch.setattr(loop, "collect", lambda client: None)

    class _NoClient:
        def __init__(self, *args, **kwargs):
            raise AssertionError("a test tried to open a real game client")

    import osmbot.game.client as client_module

    monkeypatch.setattr(client_module, "OsmClient", _NoClient)
