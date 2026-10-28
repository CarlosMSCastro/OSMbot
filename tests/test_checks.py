from osmbot.checks import theory


def match(n, home, away, result, mine=None, formation=("433A", "433A"), week=1, tatica=None, analise=None,
          players=(None, None)):
    return {"jogo": f"L_{n}", "tipo": "liga", "semana": week, "resultado": result, "campo_neutro": False,
            "casa": {"id": 1, "meu": mine == "casa", "jogadores": players[0] or []},
            "fora": {"id": 2, "meu": mine == "fora", "jogadores": players[1] or []},
            "estatisticas": {"casa": {"forca": home, "formacao": formation[0]}, "fora": {"forca": away, "formacao": formation[1]}},
            "tatica": tatica, "analise": analise}


def test_the_same_match_from_two_pcs_counts_once_with_the_fuller_record():
    short, full = match(1, 100, 100, "1-0"), {**match(1, 100, 100, "1-0"), "extra": "x" * 50}
    assert theory.unique_matches([short, full]) == [full]


def test_home_advantage_is_where_home_and_away_come_out_even():
    # home wins when no more than 5 % weaker, loses below: home is worth ~5 %
    games = [match(i, 100 + e, 100, "1-0" if e > -5 else "0-1") for i, e in enumerate(range(-15, 16)) for _ in range(6)]
    result = theory.home_advantage(games, minimum=50)
    assert result.verdict == theory.AGREES  # within 3 points of the 5 % (a straight line through a step)
    assert theory.home_advantage(games[:10]).verdict == theory.SHORT


def test_clearly_stronger_agrees_when_the_stronger_loses_much_less_above_12_percent():
    above = [match(i, 120, 100, "2-0") for i in range(45)] + [match(100 + i, 120, 100, "0-1") for i in range(4)]
    below = [match(200 + i, 108, 100, "1-0") for i in range(30)] + [match(300 + i, 108, 100, "0-1") for i in range(12)]
    assert theory.clearly_stronger(above + below).verdict == theory.AGREES
    assert theory.clearly_stronger(above).verdict == theory.SHORT


def test_fatigue_counts_only_who_started_both_rounds():
    def squad(fitness, lineup=1):
        return [{"id": 7, "lineup": lineup, "fitness": fitness}]
    games = [match(i * 2, 100, 100, "1-0", "casa", week=1, players=(squad(100), [])) for i in range(1)]
    games += [match(1, 100, 100, "1-0", "casa", week=2, players=(squad(96), []))]
    games += [match(3, 100, 100, "1-0", "casa", week=3, players=(squad(99, lineup=14), []))]  # on the bench: not counted
    result = theory.fatigue(games, minimum=1)
    assert result.sample == 1 and result.measured == "-4.0 por jogo" and result.verdict == theory.AGREES


def test_the_owner_s_away_433_and_the_counter_attack_wait_for_matches():
    games = [match(i, 100, 100, "0-0", "fora", formation=("433A", "433B")) for i in range(3)]
    assert theory.away_433(games).verdict == theory.SHORT
    report = [{"overallMatchTactics": 3}]
    ready = [match(10 + i, 100, 100, "1-0", "casa", analise=report) for i in range(10)]
    result = theory.counter_attack(ready)
    assert result.sample == 10 and result.verdict == theory.READY
