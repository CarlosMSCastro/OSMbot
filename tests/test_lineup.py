from osmbot.theory.lineup import bench_warnings, formation_name, tactic_warnings


def p(name, position, lineup, stat, fitness=100, unavailable=0):
    return {"name": name, "position": position, "lineup": lineup, "statAtt": stat, "statDef": stat, "statOvr": stat,
            "fitness": fitness, "unavailable": unavailable}


ELEVEN = [p("GR", 4, 1, 105), *[p(f"D{i}", 3, i + 1, 104 + i) for i in range(4)], *[p(f"M{i}", 2, i + 5, 107) for i in range(3)],
          p("Trossard", 1, 9, 111), p("Zirkzee", 1, 10, 105), p("Diomande", 1, 11, 102)]


def test_a_worse_substitute_ahead_of_a_better_one_is_warned_even_when_the_better_one_is_tired():
    players = ELEVEN + [p("Akanni", 3, 13, 51), p("Ndicka", 3, 16, 107, fitness=60)]
    assert bench_warnings(players) == ["Akanni 51 entra antes de Ndicka 107"]


def test_a_fit_substitute_better_than_a_starter_is_warned_but_not_a_tired_one():
    assert bench_warnings(ELEVEN + [p("Marmoush", 1, 15, 110)]) == ["Marmoush 110 no banco, Diomande 102 a jogar"]
    assert bench_warnings(ELEVEN + [p("Marmoush", 1, 15, 110, fitness=79)]) == []


def test_injured_players_and_a_good_bench_give_no_warning():
    players = ELEVEN + [p("Ndicka", 3, 13, 100), p("Akanni", 3, 16, 51), p("Hurt", 3, 14, 120, unavailable=2)]
    assert bench_warnings(players) == []


def test_formation_names():
    assert formation_name({"formation": 433, "formationDetail": "B"}) == "4-3-3 B"
    assert formation_name({"formation": 532, "formationDetail": ""}) == "5-3-2"


def test_the_tackling_must_match_the_next_referee():
    tactic = {"formation": 433, "formationDetail": "A", "style": 1}
    assert tactic_warnings(tactic, 3, 108, None) == ["Desarme Normal com árbitro normal: devia ser Agressivo"]
    assert tactic_warnings({**tactic, "style": 1}, 1, 108, None) == []  # very strict: Normal
    assert tactic_warnings({**tactic, "style": 3}, 4, 108, None) == []  # lenient: Aggressive or Extreme
    assert tactic_warnings({**tactic, "style": 2}, 5, 108, None) == ["Desarme Agressivo com árbitro muito brando: devia ser Extremo"]
    assert tactic_warnings({**tactic, "style": 2}, None, 108, None) == []  # referee unknown


def test_the_formation_is_4_3_3_a_and_5_3_2_only_against_a_clearly_stronger_analysed_opponent():
    b = {"formation": 433, "formationDetail": "B", "style": 2}
    assert tactic_warnings(b, 3, 108, None) == ["Formação 4-3-3 B: devia ser 4-3-3 A"]
    five = {"formation": 532, "formationDetail": "A", "style": 2}
    assert tactic_warnings(five, 3, 100, None) == ["Formação 5-3-2: devia ser 4-3-3 A"]  # before the analysis
    assert tactic_warnings(five, 3, 100, 110) == []
    assert tactic_warnings({**five, "formation": 433}, 3, 100, 110) == [
        "Formação 4-3-3 A: devia ser 5-3-2 (adversário mais de 5 % mais forte)"]


def test_the_warnings_are_translated():
    from osmbot.i18n import set_language, tr

    set_language("en", save=False)
    try:
        assert tr("Akanni 51 entra antes de Ndicka 107") == "Akanni 51 comes on before Ndicka 107"
        assert tr("Desarme Normal com árbitro normal: devia ser Agressivo") == \
            "Tackling Normal with an average referee: should be Aggressive"
        assert tr("Cantos: A, pela regra B") == "Corners: A, your rule says B"
    finally:
        set_language("pt", save=False)
