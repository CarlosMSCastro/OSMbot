from osmbot.theory.lineup import bench_warnings, formation_name, places, position_warnings, tactic_warnings


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


def test_a_substitute_is_only_compared_with_starters_of_his_specific_position():
    eleven = [{**x, "specificPosition": {"Zirkzee": 4}.get(x["name"], 11)} for x in ELEVEN]
    assert bench_warnings(eleven + [{**p("Dembélé", 1, 15, 104), "specificPosition": 4}]) == []
    assert bench_warnings(eleven + [{**p("Dembélé", 1, 15, 106), "specificPosition": 4}]) == ["Dembélé 106 no banco, Zirkzee 105 a jogar"]


def test_injured_players_and_a_good_bench_give_no_warning():
    players = ELEVEN + [p("Ndicka", 3, 13, 100), p("Akanni", 3, 16, 51), p("Hurt", 3, 14, 120, unavailable=2)]
    assert bench_warnings(players) == []


def test_the_places_of_each_formation_follow_the_game():
    assert places({"formation": 433, "formationDetail": "A"}) == {1: 6, 2: 9, 3: 3, 4: 3, 5: 12, 6: 2, 7: 1, 8: 2,
                                                                  9: 8, 10: 4, 11: 11}
    assert [places({"formation": 433, "formationDetail": "B"})[i] for i in (6, 7, 8)] == [2, 5, 2]  # MDC in the middle
    assert [places({"formation": 532, "formationDetail": "A"})[i] for i in range(2, 12)] == [9, 3, 3, 3, 12, 2, 1, 2, 4, 4]
    assert places({"formation": 999}) == places(None) == {}


def test_starters_out_of_their_specific_position_are_warned():
    # the Betis eleven of 2026-10-14: the game's step "Position your players" said 9/11
    players = [{"name": n, "lineup": i, "specificPosition": s} for i, (n, s) in enumerate(
        [("GR", 6), ("DE", 9), ("DC1", 3), ("DC2", 3), ("DD", 12), ("MC1", 2), ("MO", 1), ("MC2", 2), ("Díaz", 8),
         ("Messi", 11), ("Haaland", 4)], start=1)] + [{"name": "Banco", "lineup": 14, "specificPosition": 5}]
    assert position_warnings(players, {"formation": 433, "formationDetail": "A"}) == \
        ["Messi (ED) a jogar a PL", "Haaland (PL) a jogar a ED"]
    assert position_warnings(players, None) == []


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


def test_the_formation_is_4_3_3_a_and_5_defenders_only_against_a_stronger_analysed_opponent():
    b = {"formation": 433, "formationDetail": "B", "style": 2}
    assert tactic_warnings(b, 3, 108, None) == ["Formação 4-3-3 B: devia ser 4-3-3 A"]
    five = {"formation": 532, "formationDetail": "A", "style": 2}
    assert tactic_warnings(five, 3, 100, None) == ["Formação 5-3-2: devia ser 4-3-3 A"]  # before the analysis
    assert tactic_warnings(five, 3, 100, 101) == []
    assert tactic_warnings({**five, "formation": 523}, 3, 100, 101) == []  # any 5 defenders (owner, 2026-10-14)
    assert tactic_warnings({**five, "formation": 541}, 3, 100, 101) == []
    assert tactic_warnings({**five, "formation": 523}, 3, 109, 107) == ["Formação 5-2-3: devia ser 4-3-3 A"]
    assert tactic_warnings({**five, "formation": 433}, 3, 100, 101) == [
        "Formação 4-3-3 A: devia ser de 5 defesas (adversário mais forte)"]


def test_the_warnings_are_translated():
    from osmbot.i18n import set_language, tr

    set_language("en", save=False)
    try:
        assert tr("Akanni 51 entra antes de Ndicka 107") == "Akanni 51 comes on before Ndicka 107"
        assert tr("Desarme Normal com árbitro normal: devia ser Agressivo") == \
            "Tackling Normal with an average referee: should be Aggressive"
        assert tr("Cantos: A, pela regra B") == "Corners: A, your rule says B"
        assert tr("Messi (ED) a jogar a PL") == "Messi (RW) playing as ST"
        assert tr("Formação 4-3-3 A: devia ser de 5 defesas (adversário mais forte)") == \
            "Formation 4-3-3 A: should have 5 defenders (stronger opponent)"
        assert tr("Formação 5-2-3: devia ser 4-3-3 A") == "Formation 5-2-3: should be 4-3-3 A"
    finally:
        set_language("pt", save=False)
