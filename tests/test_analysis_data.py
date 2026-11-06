from osmbot.analysis import data


def match(n, home, away, result, mine=None, formation=("433A", "433A"), week=5, league="77", tatica=None, analise=None,
          kind="liga", t=1_000_000, managers=(None, None)):
    side = lambda team, key, manager: {"id": team, "nome": f"C{team}", "meu": mine == key, "media_11": 70 + team,
                                       **({"treinador": manager} if manager is not None else {})}
    return {"jogo": f"{league}_{n}_{week}", "t": t, "tipo": kind, "semana": week, "resultado": result,
            "campo_neutro": False, "casa": side(1, "casa", managers[0]), "fora": side(2, "fora", managers[1]),
            "estatisticas": {"casa": {"forca": home, "formacao": formation[0], "remates": 10, "posse": 60},
                             "fora": {"forca": away, "formacao": formation[1], "remates": 4, "posse": 40}},
            "tatica": tatica, "analise": analise}


OWN = {"overallMatchTactics": 2, "style": 1, "marking": False, "offsideTrap": True, "mentality": 70, "pressing": 64,
       "tempo": 75, "attack": 2, "midfield": 0, "defense": 0}


def test_each_match_gives_two_rows_with_the_owner_s_whole_tactic_and_the_analyst_s_report_on_his_rival():
    report = [{"leagueId": 77, "teamId": 2, "weekNr": 4, "formation": 433, "formationDetail": "A",
               "overallMatchTactics": 3, "style": 2, "marking": True, "offsideTrap": False, "managerName": "x"}]
    rows = data.rows([match(1, 120, 100, "2-1", mine="casa", tatica=OWN, analise=report)])
    home, away = rows
    assert (home.points, away.points, home.goals, away.against) == (3, 0, 2, 2)
    assert home.tactic == {"formacao": "4-3-3 A", "plano": "Pelas alas", "desarme": "Normal", "marcacao": "Zona",
                           "armadilha": "Sim", "mentalidade": "70–79", "pressao": "60–69", "tempo": "70–79",
                           "avancados": "Atacar apenas", "medios": "Ajudar a defesa", "defesa": "Defender atrás"}
    assert away.tactic["plano"] == "Contra-ataque" and away.tactic["marcacao"] == "Individual"
    assert home.rival_tactic == away.tactic and away.rival_mine
    assert home.human is True and away.human is True  # the owner's club; the report's manager
    assert round(home.edge) == 20 and home.shots == 10 and away.possession == 40


def test_other_clubs_take_the_report_of_the_round_before_only_with_the_formation_played():
    games = [match(1, 100, 100, "1-1", formation=("433A", "352A"))]
    reports = [{"relatorio": {"leagueId": 77, "teamId": 1, "weekNr": 4, "formation": 433, "formationDetail": "A",
                              "overallMatchTactics": 1, "managerName": ""}},
               {"relatorio": {"leagueId": 77, "teamId": 2, "weekNr": 4, "formation": 433, "formationDetail": "A",
                              "overallMatchTactics": 4, "managerName": "y"}}]
    home, away = data.rows(games, reports)
    assert home.tactic["plano"] == "Jogo de passe" and home.human is False  # the computer
    assert "plano" not in away.tactic and away.human is True  # played a 3-5-2, not the reported 4-3-3; still human
    assert home.points == away.points == 1


def test_the_logged_manager_wins_and_cup_ties_settled_after_90_minutes_are_draws():
    tie = {**match(1, 100, 100, "2-1", kind="taça", managers=(True, False)), "penaltis": True}
    home, away = data.rows([tie])
    assert home.human is True and away.human is False and home.points == away.points == 1


def test_the_odds_by_strength_follow_the_neighbours_of_the_same_ground():
    games = [match(i, 150, 100, "3-0") for i in range(40)] + [match(100 + i, 100, 150, "0-2") for i in range(40)]
    rows = data.rows(games)
    data.add_odds(rows, k=20)  # the 20 nearest of the same ground: all of one strength
    strong = [r for r in rows if r.ratio > 1]
    assert all(r.odds == (1.0, 0.0, 0.0) for r in strong)
    assert all(abs(r.expected - 3) < 1e-9 for r in strong)
    assert data.summary(strong)["ev"] == 0


def test_filters_keep_the_rows_of_both_sides_wanted():
    games = [match(1, 120, 100, "2-0", mine="casa", tatica=OWN, t=1000),
             match(2, 100, 130, "0-0", mine="fora", tatica={**OWN, "offsideTrap": False}, t=5000, week=6),
             match(3, 100, 100, "1-0", league="88", t=9000)]
    rows = data.rows(games)
    assert len(data.keep(rows, {"quem": "Os meus clubes"})) == 2
    assert [r.match for r in data.keep(rows, {"quem": "Os meus clubes", "armadilha": "Sim"})] == ["77_1_5"]
    assert len(data.keep(rows, {"quem": "Outros clubes"}, {"quem": "Os meus clubes"})) == 2
    assert len(data.keep(rows, league="88")) == 2
    assert [r.match for r in data.keep(rows, {"quem": "C1"}, ground="Casa", league="77")] == ["77_1_5", "77_2_6"]
    assert [r.club for r in data.keep(rows, {"quem": "C2"}, ground="Fora", league="77")] == ["C2", "C2"]
    assert [r.edge > 12 for r in data.keep(rows, strength="Muito mais forte (> 12 %)")] == [True, True]
    assert [r.match for r in data.keep(rows, period="Últimos 7 dias", now=9000 + 86400 * 7 - 1)] == ["88_3_5"] * 2
    assert data.keep(rows, {"treinador": "Humano"}, {"treinador": "Humano"}) == []  # the others' managers unknown


def test_summary_patterns_and_matchups():
    games = [match(i, 120, 100, "2-0" if i % 2 else "0-1", mine="casa", tatica={**OWN, "offsideTrap": bool(i % 2)})
             for i in range(6)]
    kept = data.keep(data.rows(games), {"quem": "Os meus clubes"})
    s = data.summary(kept)
    assert s["n"] == 6 and s["real"] == (0.5, 0.0, 0.5) and s["points"] == 1.5 and abs(s["ev"]) < 1e-9
    trap = {value: (n, points) for name, value, n, points, _ in data.patterns(kept, own=True) if name == "Fora de jogo"}
    assert trap == {"Sim": (3, 3), "Não": (3, 0)}
    assert data.matchups(kept) == [("4-3-3 A · Pelas alas", "4-3-3 A", 6, s["ev"])]
    assert data.summary([]) == {"n": 0}
