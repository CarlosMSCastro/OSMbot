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
        (100, 110, Formation.F532),  # opponent 10 % stronger
        (100, 101, Formation.F532),  # stronger by any margin (owner, 2026-10-14)
        (100, 100, Formation.F433_A),  # equal still plays 4-3-3
        (109, 107, Formation.F433_A),  # weaker opponent
    ],
)
def test_choose_formation(mine, theirs, expected):
    assert choose_formation(mine, theirs) == expected


def test_the_margin_can_be_changed():
    assert choose_formation(100, 103, stronger_pct=2) == Formation.F532


def test_negative_margin_rejected():
    with pytest.raises(ValueError):
        choose_formation(80, 80, stronger_pct=-1)


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


def test_match_strength_adds_the_boosts_and_the_home_advantage():
    from osmbot.theory.tactics import match_strength

    assert match_strength(100) == 100
    assert match_strength(109, boost_pct=3) == pytest.approx(112.27)
    assert match_strength(107, boost_pct=3, home=True) == pytest.approx(115.72, abs=0.01)  # FC Van away, 2026-10-14
    assert match_strength(100, boost_pct=3 + 25, home=True, home_pct=0) == 128  # camp and logins add up
