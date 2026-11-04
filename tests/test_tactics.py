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


def test_an_opponent_on_a_secret_training_is_taken_to_have_both_boosts():  # owner, 2026-11-02
    from osmbot.game.clubinfo import hidden_boost

    assert hidden_boost({"SecretBoostPercentage": 15, "CampBoostPercentage": 15}) == 30
    assert hidden_boost({}) == 0


@pytest.mark.parametrize(
    "referee, expected",
    [
        (Referee.VERY_STRICT, Tackling.NORMAL),
        (Referee.STRICT, Tackling.NORMAL),
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


def test_the_pitch_gives_the_home_advantage():
    from osmbot.theory.tactics import HOME_PCT, pitch_pct

    assert [pitch_pct(level) for level in range(4)] == [0, 2, 4, 6]  # DISCOVERY.md section 3
    assert pitch_pct(None) == HOME_PCT  # unknown: the measured average


def test_his_style_is_the_most_frequent_of_his_last_reports():
    from osmbot.theory.tactics import COUNTER, PASSING, WINGS, his_plan

    assert his_plan([]) is None
    assert his_plan([WINGS]) == WINGS
    assert his_plan([COUNTER, WINGS, WINGS]) == WINGS  # newest first: the most frequent wins
    assert his_plan([COUNTER, WINGS]) == COUNTER  # a tie: the newest
    assert his_plan([PASSING] + [WINGS] * 3 + [COUNTER] * 4) == WINGS  # only the last 5 count


def test_against_a_human_the_433_style_follows_his():
    from osmbot.theory.tactics import COUNTER, PASSING, WINGS, instructions

    assert instructions(433, "A").plan == {PASSING, WINGS}  # nothing known: either
    assert instructions(433, "A", human=True).plan == {PASSING, WINGS}
    assert instructions(433, "A", human=True, his=COUNTER).plan == {PASSING}  # his counter-attack
    assert instructions(433, "A", human=True, his=WINGS).plan == {WINGS}  # any other style
    assert instructions(433, "A", his=COUNTER).plan == {PASSING, WINGS}  # the computer: no change (D-092)


def test_the_tactic_step_says_his_style_and_where_it_was_read():
    from osmbot.theory.lineup import tactic_check
    from osmbot.theory.tactics import COUNTER, WINGS

    tactic = {"formation": 433, "formationDetail": "A", "overallMatchTactics": 1, "defense": 0, "midfield": 0,
              "attack": 2, "marking": False, "offsideTrap": True, "pressing": 72, "mentality": 70, "tempo": 79}
    warnings, notes, _ = tactic_check(tactic, 3, 100, 100, his=(WINGS, "últimos 3 relatórios"))
    assert "Estilo de jogo: Jogo de passe, devia ser Jogar pelas alas" in warnings
    assert notes[0] == "Estilo de jogo dele: Jogar pelas alas (últimos 3 relatórios)"
    warnings, notes, _ = tactic_check(tactic, 3, 100, 100, his=(COUNTER, "relatório desta jornada"))
    assert not any(w.startswith("Estilo de jogo") for w in warnings)  # passing against his counter-attack
    assert tactic_check(tactic, 3, 100, 100) == ([], [], True)  # nothing known: no note
    assert tactic_check(tactic, 3, 100, 100, cpu=True, his=(WINGS, "x")) == ([], [], True)  # the computer


def test_his_style_comes_from_this_rounds_report_or_his_last_ones(monkeypatch):
    from osmbot.game import clubinfo

    class Client:
        def __init__(self, body):
            self.body = body

        def get(self, path):
            return 200, self.body

    logged = [{"overallMatchTactics": 3}, {"overallMatchTactics": 2}, {"overallMatchTactics": 2}]
    monkeypatch.setattr(clubinfo, "logged_reports", lambda league, rival: logged if (league, rival) == ("1", 7) else [])
    assert clubinfo.his_style(Client([{"teamId": 7, "overallMatchTactics": 3}]), "leagues/1/teams/2", 7) == (3, "relatório desta jornada")
    assert clubinfo.his_style(Client([]), "leagues/1/teams/2", 7) == (2, "últimos 3 relatórios")
    assert clubinfo.his_style(Client([]), "leagues/1/teams/2", 8) is None


def test_the_logged_reports_are_one_per_round_newest_first(tmp_path, monkeypatch):
    import json
    from osmbot import logs
    from osmbot.game import clubinfo

    folder = tmp_path / "logs" / "PC" / "analista"
    folder.mkdir(parents=True)
    rows = [{"t": 1, "relatorio": {"leagueId": 1, "teamId": 7, "weekNr": 3, "overallMatchTactics": 3}},
            {"t": 2, "relatorio": {"leagueId": 1, "teamId": 7, "weekNr": 3, "overallMatchTactics": 2}},  # same round, later
            {"t": 3, "relatorio": {"leagueId": 1, "teamId": 7, "weekNr": 4, "overallMatchTactics": 1}},
            {"t": 4, "relatorio": {"leagueId": 2, "teamId": 7, "weekNr": 5, "overallMatchTactics": 0}}]  # another league
    (folder / "2026-11.jsonl").write_text("\n".join(json.dumps(r, separators=(",", ":")) for r in rows), encoding="utf-8")
    monkeypatch.setattr(logs, "repo_folder", lambda: tmp_path)
    assert [r["overallMatchTactics"] for r in clubinfo.logged_reports("1", 7)] == [1, 2]
