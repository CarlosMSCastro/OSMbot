import itertools

import pytest

from osmbot.models import Player, Position

_ids = itertools.count(1)


@pytest.fixture(autouse=True)
def _no_repo_logs(monkeypatch, tmp_path):
    """Tests never write into the real repo's logs/ nor read the owner's ~/.osmbot/config.json."""
    from osmbot import logs

    monkeypatch.setattr(logs, "CONFIG_FILE", tmp_path / "config.json")
    monkeypatch.setattr(logs, "SOURCE_ROOT", tmp_path / "no-repo" / "app")
    monkeypatch.setattr(logs, "HOME", tmp_path / "no-repo")
    monkeypatch.setattr(logs, "OLD_LOG", tmp_path / "old-bot.log")
    monkeypatch.delenv("OSMBOT_REPO", raising=False)


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
    monkeypatch.setattr(loop, "_money_ads", lambda dry_run: 0)
    monkeypatch.setattr(loop, "run_stadium", lambda confirm: (0, []))
    monkeypatch.setattr(loop, "run_sponsors", lambda confirm: (0, []))
    monkeypatch.setattr(loop, "run_rewards", lambda confirm: (0, []))
    monkeypatch.setattr(loop, "run_prematch", lambda confirm: (0, []))
    monkeypatch.setattr(loop, "run_medical", lambda confirm: (0, []))
    monkeypatch.setattr(loop, "collect", lambda client: None)

    from osmbot.game import rewards

    monkeypatch.setattr(rewards, "_refused", set())
    monkeypatch.setattr(rewards, "_said", set())
    monkeypatch.setattr(rewards, "_day_done", set())
    monkeypatch.setattr(rewards, "COUNTS", {"login": 0, "missions": 0, "videos": 0})
    monkeypatch.setattr(rewards, "_catalogue", [])

    from osmbot.game import prematch

    monkeypatch.setattr(prematch, "COUNTS", {"friendlies": 0, "analyses": 0, "collected": 0})
    monkeypatch.setattr(prematch, "PAUSE_BETWEEN_WRITES", 0)

    from osmbot.game import medical, sales

    monkeypatch.setattr(medical, "COUNTS", {"doctor": 0, "lawyer": 0, "collected": 0})
    monkeypatch.setattr(medical, "PAUSE_BETWEEN_WRITES", 0)
    monkeypatch.setattr(medical, "_unconfirmed", set())
    monkeypatch.setattr(sales, "SALES_FILE", tmp_path / "sales.json")

    class _NoClient:
        def __init__(self, *args, **kwargs):
            raise AssertionError("a test tried to open a real game client")

    import osmbot.game.client as client_module

    monkeypatch.setattr(client_module, "OsmClient", _NoClient)
