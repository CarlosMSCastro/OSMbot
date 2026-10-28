from osmbot.theory.lineup import bench_notes, bench_warnings, formation_name, places, position_warnings, tactic_check, tactic_notes, tactic_warnings


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


def test_before_an_important_match_a_substitute_who_would_reach_it_yellow_is_a_note_not_a_warning():
    for fitness, warned, noted in ((82, [], ["Marmoush a poupar para o Rival (82 % → 78 %)"]),
                                   (90, ["Marmoush 110 no banco, Diomande 102 a jogar"], [])):
        players = ELEVEN + [p("Marmoush", 1, 15, 110, fitness=fitness)]
        assert bench_warnings(players, spare=True) == warned
        assert bench_notes(players, "Rival") == noted
    assert bench_warnings(ELEVEN + [p("Marmoush", 1, 15, 110, fitness=82)]) == ["Marmoush 110 no banco, Diomande 102 a jogar"]
    assert bench_notes(ELEVEN + [p("Marmoush", 1, 15, 110, fitness=82)], None) == []


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


OWNERS_433 = {"formation": 433, "formationDetail": "A", "style": 2, "overallMatchTactics": 1, "defense": 0,
              "midfield": 0, "attack": 2, "marking": False, "offsideTrap": False, "mentality": 75, "pressing": 75,
              "tempo": 75}  # a 4-3-3 as THEORY.md 2 has it since 2026-10-28 (D-073)


def warnings_of(tactic, strictness=3, mine=104, opponent=None, **kw):
    return tactic_check(tactic, strictness, mine, opponent, **kw)[0]


def test_the_tackling_must_match_the_next_referee():  # in the "Tática" step since D-073
    tactic = {**OWNERS_433, "style": 1}
    assert warnings_of(tactic) == ["Desarme: Normal, devia ser Agressivo (árbitro normal)"]
    assert warnings_of(tactic, 1) == []  # very strict: Normal
    assert warnings_of({**tactic, "style": 3}, 4) == []  # lenient: Aggressive or Extreme
    assert warnings_of({**tactic, "style": 2}, 5) == []  # very lenient: Aggressive or Extreme (owner, 2026-10-14)
    assert warnings_of(tactic, 5) == ["Desarme: Normal, devia ser Agressivo ou Extremo (árbitro muito brando)"]
    assert warnings_of({**tactic, "style": 2}, None) == []  # referee unknown
    assert tactic_warnings(tactic, 108, None) == []  # no longer in the "Onze" step


def test_the_tactics_step_judges_the_formation_set():
    assert tactic_check(OWNERS_433, 3, 104, 100) == ([], [], True)
    old = {**OWNERS_433, "attack": 1, "midfield": 1, "pressing": 45}  # the 4-3-3 of THEORY.md 2 before D-073
    assert warnings_of(old, opponent=100) == ["Médios: Manter posições, devia ser Ajudar a defesa",
                                             "Avançados: Apoiar meio-campo, devia ser Atacar apenas", "Pressão: 45, devia ser 60–80 (~75)"]
    # clearly stronger: the offside trap on; against an equal one either
    assert warnings_of(OWNERS_433, mine=104, opponent=100) == []
    assert warnings_of(OWNERS_433, mine=113, opponent=100) == ["Fora de jogo: Não, devia ser Sim"]
    # his eleven with one forward (a 4-5-1): midfielders neutral
    assert warnings_of(OWNERS_433, opponent=100, forwards=1) == ["Médios: Ajudar a defesa, devia ser Manter posições"]
    # forwards who defend well may support the midfield
    wide = [{"name": "EE", "fitness": 100, "lineup": 9, "specificPosition": 8, "statDef": 41},
            {"name": "PL", "fitness": 100, "lineup": 10, "specificPosition": 4, "statDef": 22},
            {"name": "ED", "fitness": 100, "lineup": 11, "specificPosition": 11, "statDef": 40}]
    assert warnings_of({**OWNERS_433, "attack": 1}, opponent=100, players=wide) == []
    assert warnings_of({**OWNERS_433, "attack": 1}, opponent=100, players=wide[:2] + [{**wide[2], "statDef": 30}])


def test_five_defenders_drop_the_style_against_a_clearly_stronger_opponent():
    five = {**OWNERS_433, "formation": 523, "overallMatchTactics": 3, "midfield": 0, "attack": 2, "mentality": 31,
            "pressing": 27, "tempo": 71}  # the SV Ried's, 2026-10-28
    assert warnings_of(five, mine=100, opponent=103) == []
    assert warnings_of(five, mine=100, opponent=110) == []  # 10 %: not clearly (D-074)
    assert warnings_of(five, mine=100, opponent=113) == ["Estilo: 31, devia ser 0–20 (~15)"]


def test_a_formation_with_no_rule_is_grey_and_says_what_the_onze_asks_for():
    t451 = {**OWNERS_433, "formation": 451}
    warnings, notes, known = tactic_check(t451, 3, 108, 100)
    assert (warnings, known) == ([], False)
    assert notes[:2] == ["Sem regra para o 4-5-1", "Se mudares para 4-3-3 A:"]
    assert "Pressão: 60–80 (~75)" in notes and "Estilo de jogo: Jogo de passe ou jogar pelas alas" in notes
    # the "Onze" step happy: no "Se mudares"
    assert tactic_check(OWNERS_433, 3, 104, 100)[1] == []
    # 4-3-3 against a stronger one: the 5 defenders' instructions
    notes = tactic_check(OWNERS_433, 3, 100, 103)[1]
    assert notes[0] == "Se mudares para 5-3-2:" and "Estilo de jogo: Contra-ataque" in notes


def test_the_3_5_2_changes_at_home_and_away():
    home = {**OWNERS_433, "formation": 352, "overallMatchTactics": 1, "midfield": 1, "attack": 2, "offsideTrap": True,
            "mentality": 55, "pressing": 62, "tempo": 70}
    assert warnings_of(home, opponent=100) == []
    assert "Estilo de jogo: Jogo de passe, devia ser Remate à vista" in warnings_of(home, opponent=100, away=True)


def test_the_formation_is_4_3_3_a_and_5_defenders_only_against_a_stronger_analysed_opponent():
    b = {"formation": 433, "formationDetail": "B", "style": 2}
    # at home the A is the rule, but the B is right too, with a note (owner, 2026-10-26)
    assert tactic_warnings(b, 108, None) == [] and tactic_warnings(b, 108, 100) == []
    assert tactic_notes(b, [], 108, 100) == ["4-3-3 B aceite: em casa a regra é o 4-3-3 A"]
    assert tactic_notes(b, [], 100, 108) == []  # against a stronger one: 5 defenders, no note
    # away (owner, 2026-10-25): the B is the rule; the A too when clearly stronger (> 12 %, D-074) or with nothing to compare
    a = {**b, "formationDetail": "A"}
    assert tactic_warnings(b, 104, 100, away=True) == [] and tactic_notes(b, [], 104, 100, away=True) == []
    assert tactic_warnings(a, 104, 100, away=True) == ["Formação 4-3-3 A: devia ser 4-3-3 B (fora de casa)"]
    assert tactic_warnings(a, 108, 100, away=True) == ["Formação 4-3-3 A: devia ser 4-3-3 B (fora de casa)"]  # 8 %: not clearly
    assert tactic_warnings(a, 113, 100, away=True) == [] and tactic_notes(a, [], 113, 100, away=True) == [
        "4-3-3 A aceite: fora, mas claramente mais forte (+13%)"]
    assert tactic_warnings(b, 108, 100, away=True) == []
    assert tactic_warnings(b, 108, None, away=True) == []  # a reading that failed: the usual one away
    assert tactic_warnings(a, 108, None, away=True) == ["Formação 4-3-3 A: devia ser 4-3-3 B (fora de casa)"]
    assert tactic_warnings(b, 100, 103, away=True) == ["Formação 4-3-3 B: devia ser de 5 defesas (adversário mais forte)"]
    assert tactic_notes(a, [], 100, 108, away=True) == []
    assert tactic_warnings({"formation": 523, "formationDetail": "A", "style": 2}, 104, 100, away=True) == [
        "Formação 5-2-3: devia ser 4-3-3 B (fora de casa)"]
    five = {"formation": 532, "formationDetail": "A", "style": 2}
    assert tactic_warnings(five, 100, None) == ["Formação 5-3-2: devia ser 4-3-3 A"]  # before the analysis
    assert tactic_warnings(five, 100, 101) == []
    assert tactic_warnings({**five, "formation": 523}, 100, 101) == []  # any 5 defenders (owner, 2026-10-14)
    assert tactic_warnings({**five, "formation": 541}, 100, 101) == []
    assert tactic_warnings({**five, "formation": 523}, 109, 107) == ["Formação 5-2-3: devia ser 4-3-3 A"]
    assert tactic_warnings({**five, "formation": 433}, 100, 101) == [
        "Formação 4-3-3 A: devia ser de 5 defesas (adversário mais forte)"]
    # clearly weaker (> 12 %, D-074): only the 5-2-3, home or away (owner, 2026-10-26)
    assert tactic_warnings(five, 100, 108) == []  # 8 %: any 5 defenders
    assert tactic_warnings({**five, "formation": 523}, 100, 113) == []
    assert tactic_warnings({**five, "formation": 523}, 100, 113, away=True) == []
    assert tactic_warnings(five, 100, 113) == ["Formação 5-3-2: devia ser 5-2-3 (adversário claramente mais forte)"]
    assert tactic_warnings({**five, "formation": 433, "formationDetail": "B"}, 100, 113, away=True) == [
        "Formação 4-3-3 B: devia ser 5-2-3 (adversário claramente mais forte)"]
    assert tactic_notes({**five, "formation": 433, "formationDetail": "B"}, [], 100, 108) == []


def winger(name, side, fitness=90, out=0):
    return {"name": name, "specificPosition": 8 if side == "EE" else 11, "fitness": fitness, "unavailable": out}


def test_without_a_fit_winger_on_a_side_the_4_4_2_b_is_taken_and_noted():
    b442 = {"formation": 442, "formationDetail": "B", "style": 2}
    tired = [winger("Saka", "ED", 72), winger("Doku", "EE", 75)]
    assert tactic_warnings(b442, 108, 100, tired) == [] and tactic_notes(b442, tired, 108, 100) == [
        "4-4-2 B aceite: sem EE em forma (Doku 75 %); sem ED em forma (Saka 72 %)"]
    one_side = [winger("Doku", "EE"), winger("Saka", "ED", out=2)]  # one fit EE is not enough: the ED is out
    assert tactic_notes(b442, one_side, 108, 100) == ["4-4-2 B aceite: sem ED em forma (Saka fora)"]
    assert tactic_notes(b442, [winger("Doku", "EE")], 108, None) == ["4-4-2 B aceite: sem ED no plantel"]


def test_with_a_fit_winger_on_each_side_the_4_4_2_b_is_still_out_of_the_rule():
    b442 = {"formation": 442, "formationDetail": "B", "style": 2}
    fit = [winger("Doku", "EE"), winger("Saka", "ED", 72), winger("Bowen", "ED", 85)]  # a fit one on the bench counts
    assert tactic_warnings(b442, 108, 100, fit) == ["Formação 4-4-2: devia ser 4-3-3 A"]
    assert tactic_notes(b442, fit, 108, 100) == []


def test_only_the_4_4_2_b_and_only_when_the_rule_says_4_3_3_a():
    tired = [winger("Doku", "EE", 70), winger("Saka", "ED", 70)]
    a442 = {"formation": 442, "formationDetail": "A", "style": 2}
    assert tactic_warnings(a442, 108, 100, tired) == ["Formação 4-4-2: devia ser 4-3-3 A"]  # the owner: only the B
    b442 = {**a442, "formationDetail": "B"}
    assert tactic_warnings(b442, 100, 103, tired) == ["Formação 4-4-2: devia ser de 5 defesas (adversário mais forte)"]
    assert tactic_notes(b442, tired, 100, 108) == []


def fullback(name, side, fitness=90, out=0):
    return {"name": name, "specificPosition": 9 if side == "DE" else 12, "fitness": fitness, "unavailable": out}


def test_without_fit_full_backs_3_defenders_serve_and_the_4_3_3_is_told_so():
    squad = [winger("Doku", "EE"), winger("Saka", "ED"), fullback("Cucurella", "DE", 76), fullback("James", "DD")]
    a433 = {"formation": 433, "formationDetail": "A", "style": 2}
    assert tactic_warnings(a433, 108, 100, squad) == [
        "Formação 4-3-3 A sem DE em forma (Cucurella 76 %): serve 3-4-3 ou 3-5-2"]
    t343 = {"formation": 343, "formationDetail": "A", "style": 2}
    assert tactic_warnings(t343, 108, 100, squad) == []
    assert tactic_notes(t343, squad, 108, 100) == ["3-4-3 aceite: sem DE em forma (Cucurella 76 %)"]
    assert tactic_warnings({**t343, "formation": 352}, 108, 100, squad) == []
    assert tactic_warnings({"formation": 442, "formationDetail": "B", "style": 2}, 108, 100, squad) == [
        "Formação 4-4-2: devia ser 4-3-3 A"]  # it needs the full-backs too
    assert tactic_warnings(t343, 100, 103, squad) == [  # against a stronger one: still 5 defenders
        "Formação 3-4-3: devia ser de 5 defesas (adversário mais forte)"]


def test_resting_for_the_important_match_counts_as_tired():
    squad = [winger("Doku", "EE"), winger("Saka", "ED"), fullback("Cucurella", "DE", 82), fullback("James", "DD", 83)]
    t343 = {"formation": 343, "formationDetail": "A", "style": 2}
    assert tactic_warnings(t343, 108, 100, squad) == ["Formação 3-4-3: devia ser 4-3-3 A"]  # not resting: the rule
    assert tactic_warnings(t343, 108, 100, squad, spare=True) == []
    assert tactic_notes(t343, squad, 108, 100, spare=True) == [
        "3-4-3 aceite: sem DE em forma (Cucurella 82 % a poupar); sem DD em forma (James 83 % a poupar)"]


def test_no_wingers_take_two_strikers_and_with_no_full_backs_either_only_the_3_5_2():
    tired = [winger("Doku", "EE", 70), winger("Saka", "ED", 70), fullback("Cucurella", "DE"), fullback("James", "DD")]
    for formation in (532, 352):
        assert tactic_warnings({"formation": formation, "formationDetail": "A", "style": 2}, 108, 100, tired) == []
    assert tactic_warnings({"formation": 433, "formationDetail": "A", "style": 2}, 108, 100, tired) == [
        "Formação 4-3-3 A sem EE em forma (Doku 70 %); sem ED em forma (Saka 70 %): serve 4-4-2 B ou 5-3-2 ou 3-5-2"]
    both = tired[:2] + [fullback("Cucurella", "DE", 70), fullback("James", "DD")]
    assert tactic_warnings({"formation": 433, "formationDetail": "A", "style": 2}, 108, 100, both)[0].endswith(": serve 3-5-2")
    assert tactic_warnings({"formation": 343, "formationDetail": "A", "style": 2}, 108, 100, both) == [
        "Formação 3-4-3: devia ser 4-3-3 A"]


def test_the_warnings_are_translated():
    from osmbot.i18n import set_language, tr

    set_language("en", save=False)
    try:
        assert tr("Akanni 51 entra antes de Ndicka 107") == "Akanni 51 comes on before Ndicka 107"
        assert tr("4-4-2 B aceite: sem EE em forma (Doku 75 %); sem ED no plantel") == \
            "4-4-2 B accepted: no fit LW (Doku 75 %); no RW in the squad"
        assert tr("Aceite") == "Accepted"
        assert tr("GR 103 · S1") == "GK 103 · S1" and tr("lucro ~45,9 M?") == "profit ~45,9 M?"  # the SALE stripe
        assert tr("reforço (> T1 79) · pechincha") == "upgrade (> T1 79) · bargain" and tr("Força") == "Strength"
        assert tr("Agressivo ou Extremo (árbitro muito brando)") == "Aggressive or Extreme (very lenient referee)"
        assert tr("Apoiar meio-campo ou atacar apenas") == "Support midfield or attack only" and tr("Pressão") == "Pressing"
        assert tr("Se mudares para 5-2-3:") == "If you switch to 5-2-3:" and tr("Remate à vista") == "Shoot on sight"
        assert tr("Cantos: A, pela regra B") == "Corners: A, your rule says B"
        assert tr("Messi (ED) a jogar a PL") == "Messi (RW) playing as ST"
        assert tr("Formação 4-3-3 A: devia ser de 5 defesas (adversário mais forte)") == \
            "Formation 4-3-3 A: should have 5 defenders (stronger opponent)"
        assert tr("Formação 5-3-2: devia ser 5-2-3 (adversário claramente mais forte)") == \
            "Formation 5-3-2: should be 5-2-3 (clearly stronger opponent)"
        assert tr("4-3-3 B aceite: em casa a regra é o 4-3-3 A") == "4-3-3 B accepted: at home the rule is the 4-3-3 A"
        assert tr("Formação 5-2-3: devia ser 4-3-3 A") == "Formation 5-2-3: should be 4-3-3 A"
    finally:
        set_language("pt", save=False)


def test_a_player_in_a_bench_place_of_another_position_is_named_as_such():
    # FC Van, 2026-10-16: no forward to spare, the owner put a defender in the attack's place (15)
    players = ELEVEN + [p("Chalobah", 3, 13, 101), p("Akanni", 3, 15, 51), p("Anton", 3, 16, 100), p("Lau", 1, 18, 50)]
    assert bench_warnings(players) == ["Tens um defesa a suplente do ataque: Akanni 51"]  # not "Akanni before Anton"


def test_an_eleven_needs_three_starters_over_and_three_under_26():
    from osmbot.theory.lineup import age_warnings

    eleven = lambda ages: [{"lineup": n, "age": a} for n, a in enumerate(ages, 1)] + [{"lineup": 12, "age": 18}]
    assert age_warnings(eleven([21, 23, 23, 24, 26, 26, 27, 28, 29, 29, 32])) == []
    assert age_warnings(eleven([19, 20, 21, 22, 22, 23, 24, 25, 26, 27, 30])) ==         ["Onze com só 2 jogadores acima de 26 anos"]
    assert age_warnings(eleven([25, 26, 27, 28, 29, 30, 30, 31, 32, 33, 34])) ==         ["Onze com só 1 jogador abaixo de 26 anos"]
    assert age_warnings(eleven([19] * 10)) == []  # no full eleven read: nothing to say


def test_a_green_starter_who_would_reach_the_important_match_yellow_is_warned():
    from osmbot.theory.fitness import rest_warnings

    players = [{"name": "Kane", "lineup": 9, "unavailable": 0, "fitness": 83},
               {"name": "Fresco", "lineup": 2, "unavailable": 0, "fitness": 95},
               {"name": "Cansado", "lineup": 3, "unavailable": 0, "fitness": 78},  # already in the tired line
               {"name": "Banco", "lineup": 14, "unavailable": 0, "fitness": 81}]
    weak, strong = {"opponent": "Elche", "important": False}, {"opponent": "Real Madrid", "important": True}
    assert rest_warnings(players, weak, strong) == [
        {"name": "Kane", "fitness": 83, "then": 79, "first": "Elche", "second": "Real Madrid"}]
    assert rest_warnings(players, strong, strong) == []  # the next one is important too: he plays both
    assert rest_warnings(players, weak, weak) == [] and rest_warnings(players, weak, None) == []


def test_the_next_two_matches():
    from osmbot.board.info import next_matches

    teams = [{"id": 1, "name": "Nós", "ranking": 5}, {"id": 2, "name": "Fraco", "ranking": 18},
             {"id": 3, "name": "Rival", "ranking": 6}]
    matches = [{"weekNr": w, "homeTeamId": h, "awayTeamId": a, "matchType": 0} for w, h, a in ((3, 1, 2), (4, 3, 1), (5, 1, 3))]
    first, second = next_matches(matches, teams, 1, 2)
    assert (first["opponent"], first["side"], first["danger"]) == ("Fraco", "H", False)
    assert (second["opponent"], second["side"], second["danger"]) == ("Rival", "A", True)
