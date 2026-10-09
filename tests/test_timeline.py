from osmbot.board.timeline import action, add, future_view, past_view

NOW = 1_000_000.0


def test_only_the_bots_actions_go_to_the_past():
    assert action("Loja: vídeo 3")["kind"] == "shop"
    assert action("Haaland: recolhido (1, +1)")["names"] == ["Haaland"]
    assert action("Haaland (ATA, 25 anos, rating 99): a treinar (1)")["kind"] == "train"
    assert action("Médico: Clube A pôs Jogador 3 no médico (8 h)") == {"kind": "match", "title": "Médico",
                                                                       "sub": "Clube A pôs Jogador 3 no médico (8 h)"}
    assert action("Clube A: campo: melhoria iniciada")["title"] == "Estádio: campo a subir"
    for noise in ("Clube A: 0 para recolher", "Próxima verificação: loja reabre em 0h20", "! Clube A: 1 slot(s) de venda livre(s)",
                  "Amigável: Clube A contra Clube B falhou (500)", "Vídeos: erro (x); volto a tentar", "Bot ligado"):
        assert action(noise) is None
    assert action("Patrocinador: Ferro & Cia (10 rondas)")  # a name with "erro" inside is not a failure


def test_runs_of_the_same_thing_are_one_entry_and_newest_comes_first():
    history: list[dict] = []
    for second, line in ((0, "Loja: vídeo 1"), (30, "Loja: vídeo 2"), (60, "Loja: vídeo 3"),
                         (100, "Haaland: recolhido (1, +1)"), (110, "de Jong: recolhido (1, +1)"),
                         (5000, "Loja: vídeo 1")):
        add(history, NOW + second, line)
    rows = past_view(history)
    assert [r["title"] for r in rows] == ["Vídeos da loja", "Treinos recolhidos", "Vídeos da loja ×3"]
    assert rows[1]["sub"] == "Haaland, de Jong"


def test_the_future_soonest_first_with_the_club_and_what_is_due_now():
    snapshot = {
        "ads": {"shop": {"open": True}, "training": {"reopen": NOW + 3600}},
        "daily": {"login": {"renews": NOW + 8 * 3600}},
        "clubs": [{"name": "Clube A", "match": NOW + 6 * 3600,
                   "next": {"opponent": "Clube B", "side": "A", "cup": False},
                   "prep": {"steps": [("Amigável", False, None), ("Análise", True, None)]},
                   "trainings": [{"name": "J1", "finish": NOW + 1800, "claimed": False},
                                 {"name": "J2", "finish": NOW + 1830, "claimed": False},
                                 {"name": "J3", "finish": NOW - 10, "claimed": False}],
                   "stadium": {"parts": [("Campo", 1, 3, NOW + 9 * 3600)]},
                   "injured": [{"name": "J4", "until": NOW + 7200}]}],
    }
    rows = future_view(snapshot, NOW)
    titles = [(r["left"], r["title"], r["club"]) for r in rows]
    assert titles[:2] == [("já", "Recolher treino J3", 0), ("já", "Vídeos da loja", None)]
    assert ("0h30", "Treino J1, J2", 0) in titles  # same minute: one line
    assert ("2h00", "Amigável", 0) in titles  # 4 h before the match, only what is missing
    assert ("6h00", "Clube A vs Clube B", 0) in titles and rows[[t[1] for t in titles].index("Clube A vs Clube B")]["sub"] == "jogo · fora"
    assert ("2h00", "Médico: J4", 0) in titles and ("9h00", "Campo Clube A", 0) in titles
    assert [r["ts"] for r in rows] == sorted(r["ts"] for r in rows)
