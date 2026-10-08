import tomllib
from pathlib import Path

import osmbot
from osmbot.gui.view import BLUE, GREEN, GREY, YELLOW, account_view, board_view, club_view, daily_view, next_check, session_view

NOW = 1_000_000.0


def club(**changes):
    base = {
        "name": "Clube A", "ranking": 3, "league": "Liga A", "match": NOW + 3600 * 2, "slots": (3, 4),
        "money": (9_300_000, 0), "sponsors": {"slots": 4, "revenue": 1_200_000},
        "stadium": {"parts": [("Treinos", 2, 3, NOW + 9 * 3600), ("Campo", 3, 3, None), ("Capacidade", 2, 3, None)],
                    "until": NOW + 9 * 3600},
        "trainings": [{"id": 1, "name": "Jogador 1", "pos": "ATA", "finish": NOW + 4 * 3600, "claimed": False},
                      {"id": 2, "name": "Jogador 24", "pos": "GR", "finish": NOW - 60, "claimed": False}],
        "tired": [{"id": 9, "name": "Jogador 5", "pos": "DEF", "fitness": 68}],
    }
    base.update(changes)
    return base


def test_the_version_in_the_window_is_the_version_of_the_project():
    project = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text(encoding="utf-8"))
    assert osmbot.__version__ == project["project"]["version"]


def test_a_club_panel_shows_the_same_as_the_console_board():
    view = club_view(club(), NOW, {1: 2 * 3600})
    assert view["title"] == "Clube A  —  3.º · Liga A"
    fields = {name: (text, colour) for name, text, colour in view["fields"]}
    assert fields["Próximo jogo"] == ("2h00", BLUE)
    assert fields["Lista de transf."] == ("3/4", YELLOW)  # a free slot needs attention
    assert fields["Fundos"][0] == "9,3 M" and fields["Poupança"] == ("0", GREY)
    assert fields["Patrocinadores"] == ("4/4  ·  1,2 M/ronda", GREEN)
    treinos, campo, capacidade = view["stadium"]
    assert treinos[2:4] == ("a subir · 9h00", BLUE) and 0 < treinos[4] < 1
    assert campo[2:] == ("máximo", GREEN, None) and capacidade[2:] == ("—", GREY, None)
    first, ready = view["trainings"]
    assert first[2:4] == ("4h00", BLUE) and first[4] == 0.5 and first[5] == 0.25  # half gone, a quarter by a video
    assert ready[2:5] == ("pronto", GREEN, 1.0)
    assert view["tired"] == "Jogador 5 68%"


def test_a_full_transfer_list_is_plain_and_unknown_values_say_so():
    view = club_view(club(slots=None, money=None, match=None, sponsors=None, tired=[]), NOW)
    fields = {name: (text, colour) for name, text, colour in view["fields"]}
    assert fields["Lista de transf."] == ("?", GREY) and fields["Fundos"] == ("?", GREY)
    assert fields["Próximo jogo"] == ("—", GREY) and "Patrocinadores" not in fields and view["tired"] == ""
    assert club_view(club(), NOW)["fields"][1][1:] == ("3/4", YELLOW)
    assert dict((n, (t, c)) for n, t, c in club_view(club(slots=(4, 4)), NOW)["fields"])["Lista de transf."] == ("4/4", None)


def test_daily_rewards_and_the_accumulated_videos():
    daily = {"login": {"claimable": False, "day": 5, "renews": NOW + 3600},
             "missions": {"total": 3, "claimed": 2, "day_pending": False},
             "videos": {"count": 3, "threshold": 10, "claimable": False, "reopen": None}}
    parts, videos = daily_view(daily, NOW)
    assert parts == [("início de sessão ✓ (dia 5)", GREEN), ("missões 2/3", YELLOW), ("prémio do dia —", GREY),
                     ("novo dia em 1h00", BLUE)]
    assert videos == {"text": "3/10", "colour": None, "done": 0.3}
    daily["videos"]["claimable"] = True
    assert daily_view(daily, NOW)[1]["text"] == "por reclamar"
    assert daily_view(None, NOW) == ([], None)


def test_the_account_box_counts_coins_since_the_start_and_shows_the_shop_wait():
    snap = {"coins": 2586, "clubs": [club()], "ads": {"shop": {"open": False, "reopen": NOW + 1800}}}
    account = account_view(snap, {"start": NOW - 600, "coins0": 2574, "shop": 9}, NOW)
    assert account["coins"] == "2 586  (+12 desde o arranque)"
    assert account["shop"] == {"text": "reabre em 0h30", "colour": BLUE, "done": 0.5}
    stopped = account_view({**snap, "ads": {"shop": {"open": True}}}, None, NOW)
    assert stopped["coins"] == "2 586" and stopped["shop"]["text"] == "vídeos disponíveis"


def test_the_session_row_is_one_labelled_number_per_box():
    stats = {"start": NOW - 38 * 60, "shop": 9, "training": 4, "claimed": 3, "started": 3, "r_missions": 3}
    boxes = dict(session_view(stats, NOW))
    assert boxes["Ligado há"] == "0h38" and boxes["Vídeos loja"] == "9" and boxes["Vídeos treino"] == "4 (−8 h)"
    assert boxes["Vídeos dinheiro"] == "0" and boxes["Recolhidos"] == "3" and boxes["Recompensas"] == "3"
    assert session_view(None, NOW) == [] and session_view({"start": None}, NOW) == []


def test_the_status_bar_says_what_the_bot_waits_for_and_nothing_before_the_first_read():
    snap = {"coins": 1, "clubs": [club()], "ads": {"shop": {"open": False, "reopen": NOW + 1800}}}
    assert next_check(snap, NOW).startswith("Próxima verificação: treino por recolher em 0h00 · loja reabre em 0h30 · treino acaba em 4h00")
    assert board_view(None, None, NOW) is None
    assert [c["name"] for c in board_view(snap, None, NOW)["clubs"]] == ["Clube A"]
