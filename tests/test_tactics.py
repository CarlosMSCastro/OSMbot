import pytest

from osmbot.theory.tactics import (
    ForwardsRole,
    Formation,
    MidfieldRole,
    PlayStyle,
    Referee,
    Slider,
    Tackling,
    build_setup,
    choose_formation,
    choose_tackling,
)


@pytest.mark.parametrize(
    "mine, theirs, expected",
    [
        (80, 90, Formation.F532),  # much stronger opponent
        (80, 82, Formation.F433_B),  # similar
        (80, 78, Formation.F433_B),  # similar (slightly weaker)
        (80, 70, Formation.F433_A),  # clearly weaker
        (80, 85, Formation.F433_B),  # exactly at the margin still counts as similar
        (80, 75, Formation.F433_B),
    ],
)
def test_choose_formation(mine, theirs, expected):
    assert choose_formation(mine, theirs, similar_margin=5) == expected


def test_similar_margin_is_required():
    with pytest.raises(TypeError):
        choose_formation(80, 80)  # type: ignore[call-arg]


def test_negative_margin_rejected():
    with pytest.raises(ValueError):
        choose_formation(80, 80, similar_margin=-1)


@pytest.mark.parametrize("formation", [Formation.F433_A, Formation.F433_B])
def test_433_setup(formation):
    s = build_setup(formation)
    assert s.offside_trap is False
    assert s.zonal_marking is False
    assert s.play_style is PlayStyle.PASSING
    assert (s.pressure.value, s.style.value, s.timing.value) == (75, 75, 75)
    assert s.forwards is ForwardsRole.SUPPORT_MIDFIELD
    assert s.midfield is MidfieldRole.HOLD_POSITIONS


def test_433_can_play_wings():
    assert build_setup(Formation.F433_A, prefer_wings=True).play_style is PlayStyle.WINGS


def test_532_setup():
    s = build_setup(Formation.F532, prefer_wings=True)  # wings flag is irrelevant here
    assert s.offside_trap is False
    assert s.zonal_marking is True
    assert s.play_style is PlayStyle.COUNTER_ATTACK
    assert s.pressure.value == 30
    assert s.timing.value == 75
    assert s.forwards is ForwardsRole.ATTACK_ONLY
    assert s.midfield is MidfieldRole.HELP_DEFENCE


@pytest.mark.parametrize("formation", list(Formation))
def test_default_sliders_sit_inside_the_owners_bands(formation):
    s = build_setup(formation)
    if formation is Formation.F532:
        assert (s.pressure.low, s.pressure.high) == (20, 40)
    else:
        assert (s.pressure.low, s.pressure.high) == (60, 80)
    assert (s.timing.low, s.timing.high) == (60, 80)


def test_slider_rejects_value_outside_band():
    with pytest.raises(ValueError):
        Slider(85, 60, 80)


@pytest.mark.parametrize(
    "referee, expected",
    [
        (Referee.VERY_STRICT, Tackling.NORMAL),
        (Referee.STRICT, Tackling.AGGRESSIVE),
        (Referee.NORMAL, Tackling.AGGRESSIVE),
        (Referee.LENIENT, Tackling.AGGRESSIVE),
        (Referee.VERY_LENIENT, Tackling.EXTREME),
    ],
)
def test_tackling_by_referee(referee, expected):
    assert choose_tackling(referee) is expected


def test_risk_extreme_only_upgrades_a_lenient_referee():
    assert choose_tackling(Referee.LENIENT, risk_extreme=True) is Tackling.EXTREME
    assert choose_tackling(Referee.VERY_STRICT, risk_extreme=True) is Tackling.NORMAL
    assert choose_tackling(Referee.NORMAL, risk_extreme=True) is Tackling.AGGRESSIVE
