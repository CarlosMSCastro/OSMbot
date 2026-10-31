import pytest

from osmbot.theory.tactics import (
    Formation,
    Referee,
    Tackling,
    choose_formation,
    choose_tackling,
    defensive,
    instructions,
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


@pytest.mark.parametrize("formation, detail", [(433, "A"), (433, "B"), (532, None), (523, "A"), (523, "B"),
                                              (541, "A"), (541, "B"), (442, "B"), (343, "A"), (352, "A")])
def test_every_formation_of_section_1_has_a_rule_with_its_aim_inside_the_band(formation, detail):
    rule = instructions(formation, detail)
    for band in (rule.pressing, rule.mentality, rule.tempo):
        assert band.aim in band and band.high - band.low == 20  # the owner's bands are 20 wide (THEORY.md 2)


def test_formations_with_no_rule():
    assert instructions(451, "A") is None and instructions(442, "A") is None


def test_the_433_as_the_author():  # D-073
    rule = instructions(433, "A")
    assert rule.attack == {2} and rule.midfield == {0} and rule.offside == {True, False} and rule.plan == {1, 2}
    assert instructions(433, "A", clearly_stronger=True).offside == {True}
    assert instructions(433, "A", forwards=1).midfield == {1}
    assert instructions(433, "A", defensive_forwards=True).attack == {1, 2}


def test_the_5_defenders_style_follows_the_strength():
    assert (instructions(532, None).mentality.low, instructions(532, None).mentality.high) == (20, 40)
    assert (instructions(523, "A", clearly_weaker=True).mentality.aim) == 15
    assert instructions(523, "B").attack == {1} and instructions(541, "B").plan == {4}


def test_the_442_b_takes_the_author_s_line_only_against_counter_attack():  # D-079
    rule = instructions(442, "B", counter=True)
    assert rule.plan == {1} and rule.midfield == {2} and rule.attack == {2} and rule.offside == {False}
    assert (rule.pressing.aim, rule.mentality.aim, rule.tempo.aim) == (61, 49, 72)
    for band in (rule.pressing, rule.mentality, rule.tempo):
        assert band.aim in band and band.high - band.low == 20
    assert instructions(442, "B").midfield == {1} and instructions(442, "B").mentality.aim == 65
    assert instructions(433, "A", counter=True) == instructions(433, "A")


def test_the_counter_attack_is_read_from_the_report_on_the_next_opponent():
    from osmbot.game.clubinfo import plays_counter

    class Client:
        def __init__(self, status, body):
            self.answer = status, body

        def get(self, path):
            assert path.endswith("/api/v1.1/leagues/1/teams/2/spyresults")
            return self.answer

    reports = [{"teamId": 7, "overallMatchTactics": 3}, {"teamId": 9, "overallMatchTactics": 1}]
    assert plays_counter(Client(200, reports), "leagues/1/teams/2", 7)
    assert not plays_counter(Client(200, reports), "leagues/1/teams/2", 9)  # another style
    assert not plays_counter(Client(200, reports), "leagues/1/teams/2", 8)  # the analyst went elsewhere
    assert not plays_counter(Client(404, None), "leagues/1/teams/2", 7)


def test_the_343_marks_man_to_man_against_3_forwards():
    assert instructions(343, "B").marking == {False} and instructions(343, "B", forwards=3).marking == {True}


def test_defensive_forwards():
    assert not defensive([])
    assert defensive([{"specificPosition": 8, "statDef": 40}, {"specificPosition": 4, "statDef": 20}])
    assert not defensive([{"specificPosition": 8, "statDef": 39}, {"specificPosition": 4, "statDef": 50}])


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
