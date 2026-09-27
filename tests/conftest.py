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
