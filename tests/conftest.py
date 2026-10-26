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
    from osmbot.game import refusals

    monkeypatch.setattr(refusals, "FILE", tmp_path / "recusas.json")  # never the owner's notes of refused requests
    from osmbot.game import rewards

    monkeypatch.setattr(rewards, "LOGIN_FILE", tmp_path / "inicio_sessao.json")  # nor today's login prize
    monkeypatch.setattr(rewards, "TRACK_FILE", tmp_path / "inicio_sessao_dias.json")  # nor the prizes by day
    from osmbot.game import events

    monkeypatch.setattr(events, "FILE", tmp_path / "eventos.json")  # nor the owner's calendar of events
    from osmbot.game import matchlog

    monkeypatch.setattr(matchlog, "FILE", tmp_path / "jogos.json")  # nor the match log's state
    from osmbot.game import xplog

    monkeypatch.setattr(xplog, "FILE", tmp_path / "xp.json")  # nor the XP log's state
    from osmbot.game import reports

    monkeypatch.setattr(reports, "FILE", tmp_path / "relatorios.json")  # nor the match reports' state


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
        lineup=0,
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
            lineup=lineup,
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
    monkeypatch.setattr(loop, "run_savings", lambda confirm: (0, []))
    monkeypatch.setattr(loop, "run_inventory", lambda confirm, log=None: (0, []))
    monkeypatch.setattr(loop, "log_rounds", lambda client=None, log=None: 0)
    monkeypatch.setattr(loop, "collect", lambda client: None)

    from osmbot.game import rewards


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
    monkeypatch.setattr(sales, "SALES_FILE", tmp_path / "sales.json")
    from osmbot.game import market

    monkeypatch.setattr(market, "STATE_FILE", tmp_path / "mercado.json")
    from osmbot.game import savings, trainings

    monkeypatch.setattr(savings, "COUNTS", {"deposits": 0})
    monkeypatch.setattr(savings, "PAUSE_BETWEEN_WRITES", 0)
    monkeypatch.setattr(trainings, "ROUNDS_FILE", tmp_path / "treinos.json")
    from osmbot.game import events

    monkeypatch.setattr(events, "real", {"refresh": events.refresh, "check_league": events.check_league}, raising=False)
    monkeypatch.setattr(events, "FILE", tmp_path / "eventos.json")
    monkeypatch.setattr(events, "refresh", lambda log=None, read=None, now=None: None)  # never opens the forum
    monkeypatch.setattr(events, "check_league", lambda *args, **kwargs: [])
    monkeypatch.setattr(events, "_last_check", {})
    monkeypatch.setattr(events, "_active", {})

    class _NoClient:
        def __init__(self, *args, **kwargs):
            raise AssertionError("a test tried to open a real game client")

    import osmbot.game.client as client_module

    monkeypatch.setattr(client_module, "OsmClient", _NoClient)
