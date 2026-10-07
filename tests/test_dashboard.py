from osmbot.game.dashboard import bar, render, span, wake_events

NOW = 1_000_000.0


def snapshot(**changes):
    base = {
        "coins": 2452,
        "clubs": [{
            "name": "Clube A", "ranking": 1, "league": "Liga A", "match": NOW + 3600 * 22, "slots": (4, 4),
            "trainings": [
                {"name": "Jogador 1", "pos": "ATA", "finish": NOW + 3600 * 5, "claimed": False},
                {"name": "Jogador 24", "pos": "GR", "finish": NOW + 3600 * 3, "claimed": False},
            ],
        }],
        "ads": {"shop": {"open": True, "reopen": None}, "training": {"open": False, "reopen": NOW + 3600}},
    }
    base.update(changes)
    return base


def test_span_and_bar():
    assert span(3 * 3600 + 6 * 60) == "3h06"
    assert span(-5) == "0h00"
    assert bar(8 * 3600).count("█") == 0
    assert bar(0).count("█") == 18
    assert len(bar(4 * 3600)) == 18


def test_wake_events_are_sorted_and_labelled():
    events = wake_events(snapshot(), NOW)
    assert [label for label, _ in events] == ["vídeo de treino reabre", "treino acaba"]
    assert events[0][1] == NOW + 3600 and events[1][1] == NOW + 3 * 3600


def test_wake_events_ignore_past_claimed_and_open_windows():
    snap = snapshot()
    snap["clubs"][0]["trainings"][1]["claimed"] = True
    snap["ads"]["training"]["reopen"] = NOW - 5
    assert [label for label, _ in wake_events(snap, NOW)] == ["treino acaba"]
    assert wake_events(None, NOW) == []


def test_render_shows_clubs_trainings_and_log():
    text = render(snapshot(), NOW, "ATIVO", ["12:00:00 olá"], "Windows", colour=False)
    for expected in ("CLUBE A", "Jogador 1", "Jogador 24", "3h00", "2452", "12:00:00 olá", "Ctrl+C", "ATIVO"):
        assert expected in text


def test_render_flags_a_free_slot():
    snap = snapshot()
    snap["clubs"][0]["slots"] = (3, 4)
    assert "LIVRE: 1" in render(snap, NOW, "ATIVO", [], "Windows", colour=False)
    assert "LIVRE" not in render(snapshot(), NOW, "ATIVO", [], "Windows", colour=False)


def test_render_without_data_and_without_colour_codes():
    text = render(None, NOW, "ATIVO", [], "Windows", colour=False)
    assert "a carregar" in text and "\x1b" not in text


def test_summary_shows_coin_change_videos_and_trainings():
    from osmbot.game.dashboard import summary_text

    stats = {"start": NOW - 2 * 3600, "coins0": 2450, "shop": 5, "training": 2, "claimed": 8, "started": 8}
    text = summary_text(snapshot(), stats, NOW)
    for expected in ("2h00", "+2 boss coins", "loja 5", "treino 2", "8 recolhido", "8 posto"):
        assert expected in text
    assert summary_text(snapshot(), None, NOW) == ""
    assert "Desde o arranque" in render(snapshot(), NOW, "ATIVO", [], "Windows", colour=False, stats=stats)


def test_money_switches_to_millions_at_a_thousand_k():
    from osmbot.game.dashboard import money

    assert money(450_000) == "450 k"
    assert money(999_600) == "1 M" and money(1_000_000) == "1 M"
    assert money(1_500_000) == "1,5 M" and money(12_345_678) == "12,35 M"


def test_board_has_no_next_line_and_says_transfer_list():
    text = render(snapshot(), NOW, "ATIVO", [], "Windows", colour=False)
    assert "A seguir" not in text and "Lista de transferências 4/4" in text and "Slots" not in text


def test_shop_shows_a_bar_while_closed_and_a_tick_when_open():
    closed = snapshot()
    closed["ads"]["shop"] = {"open": False, "reopen": NOW + 3600}
    text = render(closed, NOW, "ATIVO", [], "Windows", colour=False)
    assert "loja █" in text and "1h00" in text
    assert "loja √" in render(snapshot(), NOW, "ATIVO", [], "Windows", colour=False)


def test_tired_starters_take_one_line_for_the_club():
    snap = snapshot()
    snap["clubs"][0]["tired"] = [{"id": i, "name": f"Nome Apelido{i}", "pos": "MED", "fitness": 60 + i} for i in range(4)]
    lines = render(snap, NOW, "ATIVO", [], "Windows", colour=False).split("\n")
    assert len([line for line in lines if "cansados" in line]) == 1


def test_stadium_building_part_gets_a_bar_and_done_parts_a_tick():
    snap = snapshot()
    snap["clubs"][0]["stadium"] = {"parts": [("campo", 3, 3, None), ("capacidade", 1, 3, NOW + 3600 * 9)], "until": NOW + 3600 * 9}
    text = render(snap, NOW, "ATIVO", [], "Windows", colour=False)
    assert "campo 3/3 √" in text and "a construir capacidade 1/3" in text and "9h00" in text


def test_sponsors_say_chosen_and_use_millions():
    snap = snapshot()
    snap["clubs"][0]["sponsors"] = {"slots": 4, "revenue": 1_000_000}
    text = render(snap, NOW, "ATIVO", [], "Windows", colour=False)
    assert "4/4 escolhidos" in text and "1 M/ronda" in text


def test_board_summary_has_the_jump_and_hours_saved_but_not_trainings():
    from osmbot.game.dashboard import summary_lines

    stats = {"start": NOW - 3600, "coins0": 2450, "shop": 1, "training": 3, "money": 0, "claimed": 8, "started": 8}
    board = " ".join(summary_lines(snapshot(), stats, NOW))
    assert "salto +2 boss coins" in board and "encurtadas 6 h" in board and "recolhidos" not in board
    assert "\x1b[32m" in "".join(summary_lines(snapshot(), stats, NOW, colour=True))
