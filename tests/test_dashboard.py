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
    assert bar(0).count("█") == 20
    assert len(bar(4 * 3600)) == 20


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
    free = render(snap, NOW, "ATIVO", [], "Windows", colour=True)
    full = render(snapshot(), NOW, "ATIVO", [], "Windows", colour=True)
    assert "\x1b[1m\x1b[33m3/4\x1b[0m" in free  # only the numbers turn yellow
    club_line = next(line for line in full.split("\n") if "Lista de Transf." in line)
    assert "\x1b[33m" not in club_line  # a full list stays plain


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
    assert "A seguir" not in text and "Lista de Transf. 4/4" in text and "Slots" not in text and "LIVRE" not in text


def test_there_is_no_videos_line_any_more():
    assert "Vídeos:" not in render(snapshot(), NOW, "ATIVO", [], "Windows", colour=False)


def test_boss_coins_line_shows_when_the_shop_videos_come_back():
    closed = snapshot()
    closed["ads"]["shop"] = {"open": False, "reopen": NOW + 1800}
    line = next(l for l in render(closed, NOW, "ATIVO", [], "Windows", colour=False).split("\n") if "Boss coins" in l)
    assert "loja █" in line and "0h30" in line  # half of the hour gone: a half-full little bar
    open_line = next(l for l in render(snapshot(), NOW, "ATIVO", [], "Windows", colour=False).split("\n") if "Boss coins" in l)
    assert "loja" not in open_line  # videos available: nothing to count down


def test_board_shows_no_log_area_unless_there_are_problems():
    quiet = render(snapshot(), NOW, "ATIVO", [], "Windows", colour=False)
    assert "(sem eventos)" not in quiet and not quiet.rstrip().endswith("─")
    loud = render(snapshot(), NOW, "ATIVO", ["12:00:00 Vídeos: erro (x)"], "Windows", colour=True)
    assert "Vídeos: erro (x)" in loud and "\x1b[31m12:00:00 Vídeos: erro (x)" in loud  # in red


def test_tired_starters_take_one_line_for_the_club():
    snap = snapshot()
    snap["clubs"][0]["tired"] = [{"id": i, "name": f"Nome Apelido{i}", "pos": "MED", "fitness": 60 + i} for i in range(4)]
    lines = render(snap, NOW, "ATIVO", [], "Windows", colour=False).split("\n")
    assert len([line for line in lines if "cansados" in line]) == 1


def test_stadium_building_part_gets_a_bar_and_done_parts_a_tick():
    snap = snapshot()
    snap["clubs"][0]["stadium"] = {"parts": [("campo", 3, 3, None), ("capacidade", 1, 3, NOW + 3600 * 9)], "until": NOW + 3600 * 9}
    text = render(snap, NOW, "ATIVO", [], "Windows", colour=False)
    assert "campo 3/3 √" in text and "capacidade 1/3 █" in text and "9h00" in text and "█" in text


def test_sponsors_say_chosen_and_use_millions():
    snap = snapshot()
    snap["clubs"][0]["sponsors"] = {"slots": 4, "revenue": 1_000_000}
    text = render(snap, NOW, "ATIVO", [], "Windows", colour=False)
    assert "4/4 escolhidos" in text and "1 M/ronda" in text


def test_board_summary_is_one_line_with_the_videos_and_the_hours_saved():
    from osmbot.game.dashboard import summary_lines

    stats = {"start": NOW - 3600, "coins0": 2450, "shop": 1, "training": 3, "money": 0, "claimed": 8, "started": 8}
    board = summary_lines(snapshot(), stats, NOW)
    assert len(board) == 1 and "encurtadas 6 h" in board[0] and "loja 1" in board[0]
    assert "salto" not in board[0] and "recolhidos" not in board[0]
    full = " ".join(summary_lines(snapshot(), stats, NOW, full=True))
    assert "salto +2 boss coins" in full and "8 recolhidos" in full


def test_boss_coins_line_shows_the_jump_right_after_the_balance():
    stats = {"start": NOW - 3600, "coins0": 2449}
    text = render(snapshot(), NOW, "ATIVO", [], "Windows", colour=False, stats=stats)
    assert "Boss coins 2452  +3" in text
    lines = text.split("\n")
    assert not any(line.startswith(" Vídeos:") for line in lines)


def test_top_line_says_how_to_stop():
    assert "Para parar: Ctrl+C" in render(snapshot(), NOW, "ATIVO", [], "Windows", colour=False).split("\n")[0]


def test_club_line_is_green_for_every_club_whatever_its_slots():
    snap = snapshot()
    snap["clubs"][0]["slots"] = (3, 4)
    snap["clubs"].append(dict(snap["clubs"][0], name="Clube B", slots=(4, 4)))
    text = render(snap, NOW, "ATIVO", [], "Windows", colour=True)
    assert text.count("\x1b[1m\x1b[32mCLUBE ") == 2
    lines = text.split("\n")
    assert lines[[i for i, line in enumerate(lines) if "CLUBE B" in line][0] - 1] == ""  # a blank line above the second club


def test_a_training_bar_shows_the_time_a_video_skipped_in_blue():
    snap = snapshot()
    snap["clubs"][0]["trainings"] = [{"id": 7, "name": "Jogador 1", "pos": "ATA", "finish": NOW + 4 * 3600, "claimed": False}]
    text = render(snap, NOW, "ATIVO", [], "Windows", colour=True, stats={"shortened": {7: 2 * 3600}})
    blue = "\x1b[36m" + "█" * 5 + "\x1b[0m"  # 2h of 8h on a 20-cell bar
    assert blue in text and "\x1b[32m" + "█" * 5 + "\x1b[0m" in text  # 4h gone by: 5 cells green + 5 blue
    assert blue not in render(snap, NOW, "ATIVO", [], "Windows", colour=True)




def test_board_fits_a_narrow_window():
    text = render(snapshot(), NOW, "ATIVO", ["12:00:00 olá"], "Windows", colour=False, cols=60)
    assert max(len(line) for line in text.split("\n")) <= 59
def test_every_trainer_keeps_a_line_and_a_bar_at_every_compaction_level():
    from osmbot.game.dashboard import _render

    snap = snapshot()
    snap["clubs"][0]["trainings"] = [{"id": i, "name": f"Jogador {i}", "pos": "ATA", "finish": NOW + 3600 * i, "claimed": False} for i in range(1, 5)]
    for level in range(4):
        lines = [line for line in _render(snap, NOW, "ATIVO", [], "Windows", False, None, level, 100).split("\n") if "Jogador" in line]
        assert len(lines) == 4 and all("█" in line or "░" in line for line in lines)


def test_stadium_bar_is_on_the_same_line_as_the_parts():
    snap = snapshot()
    snap["clubs"][0]["stadium"] = {"parts": [("Treinos", 3, 3, None), ("Campo", 0, 3, NOW + 9 * 3600), ("Capacidade", 0, 3, None)], "until": NOW + 9 * 3600}
    text = render(snap, NOW, "ATIVO", [], "Windows", colour=False)
    line = next(line for line in text.split("\n") if "estádio" in line)
    assert "Treinos 3/3 √" in line and "Campo 0/3 " in line and "█" in line and "9h00" in line and "Capacidade 0/3" in line
    assert "a construir" not in text


def daily(**changes):
    base = {"login": {"claimable": False, "day": 16, "renews": NOW + 3600 * 16.5},
            "missions": {"claimed": 3, "total": 3, "day_pending": False},
            "videos": {"count": 7, "threshold": 10, "claimable": False, "reopen": None}}
    base.update(changes)
    return base


def below_coins(text, count):
    lines = text.split("\n")
    first = next(i for i, line in enumerate(lines) if "Boss coins" in line)
    return lines[first + 1:first + 1 + count]


def test_daily_rewards_take_two_lines_under_the_boss_coins():
    text = render(snapshot(daily=daily()), NOW, "ATIVO", [], "Windows", colour=False)
    first, second = below_coins(text, 2)
    for expected in ("início de sessão √ (dia 16)", "missões 3/3 √", "prémio do dia √", "novo dia em 16h30"):
        assert expected in first
    assert "troca de posição" in second and "7/10" in second and "█" in second and "reabre" not in second


def test_daily_rewards_say_what_is_still_to_claim():
    pending = daily(login={"claimable": True, "day": 16, "renews": NOW + 3600},
                    missions={"claimed": 3, "total": 3, "day_pending": True},
                    videos={"count": 10, "threshold": 10, "claimable": True, "reopen": None})
    first, second = below_coins(render(snapshot(daily=pending), NOW, "ATIVO", [], "Windows", colour=False), 2)
    assert "início de sessão por reclamar" in first and "prémio do dia por reclamar" in first
    assert "troca de posição por reclamar" in second


def test_daily_rewards_wait_for_the_dailies_and_show_when_the_videos_come_back():
    waiting = daily(missions={"claimed": 1, "total": 3, "day_pending": False},
                    videos={"count": 0, "threshold": 10, "claimable": False, "reopen": NOW + 3600 * 11.7})
    first, second = below_coins(render(snapshot(daily=waiting), NOW, "ATIVO", [], "Windows", colour=False), 2)
    assert "missões 1/3" in first and "√" not in first.split("missões")[1].split("·")[0] and "prémio do dia -" in first
    assert "0/10" in second and "reabre em 11h42" in second


def test_daily_rewards_collapse_to_one_line_when_space_is_short_and_vanish_without_data():
    from osmbot.game.dashboard import _render

    short = _render(snapshot(daily=daily()), NOW, "ATIVO", [], "Windows", False, None, 2, 100)
    line = below_coins(short, 1)[0]
    assert "início √" in line and "posição" in line and "novo dia 16h30" in line
    assert len(line) < 100
    plain = render(snapshot(), NOW, "ATIVO", [], "Windows", colour=False)
    assert "diárias" not in plain and "troca de posição" not in plain


def test_the_bot_wakes_when_a_new_day_starts_and_when_the_videos_reopen():
    snap = snapshot(daily=daily(videos={"count": 0, "threshold": 10, "claimable": False, "reopen": NOW + 5000}))
    events = dict(wake_events(snap, NOW))
    assert events["novo dia"] == NOW + 3600 * 16.5 and events["vídeos acumulados reabrem"] == NOW + 5000


def test_a_training_that_finished_while_the_bot_was_busy_wakes_it_at_once():
    snap = snapshot()
    snap["clubs"][0]["trainings"][1]["finish"] = NOW - 15 * 60  # finished during a burst of shop videos
    events = wake_events(snap, NOW)
    assert events[0] == ("treino por recolher", NOW)
    assert ("treino acaba", NOW + 3600 * 5) in events
