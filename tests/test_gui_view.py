import tomllib
from pathlib import Path

import osmbot
from osmbot.gui.view import BLUE, GREEN, GREY, YELLOW, account_view, board_view, club_view, daily_view, next_check

NOW = 1_000_000.0


def club(**changes):
    base = {
        "name": "Clube A", "ranking": 3, "league": "Liga A", "match": NOW + 3600 * 2, "slots": (3, 4),
        "money": (9_300_000, 1_000_000), "sponsors": {"slots": 4, "revenue": 1_200_000},
        "stadium": {"parts": [("Treinos", 2, 3, NOW + 9 * 3600), ("Campo", 3, 3, None), ("Capacidade", 2, 3, None)],
                    "until": NOW + 9 * 3600},
        "trainings": [{"id": 1, "name": "Jogador 1", "pos": "ATA", "finish": NOW + 4 * 3600, "claimed": False},
                      {"id": 2, "name": "Jogador 24", "pos": "GR", "finish": NOW - 60, "claimed": False}],
        "tired": [{"id": 9, "name": "Jogador 5", "pos": "DEF", "fitness": 68}],
        "next": {"opponent": "Clube B", "rank": 4, "side": "H", "danger": True, "cup": False},
        "cup": ("quartos-de-final", "in"), "value": (2, 588_700_000, 29_435_000.0),
        "free_slots": 1, "sales": [{"name": "Jogador 7", "price": 166_664_480}],
        "prep": {"pct": 35, "steps": [("Amigável", True, None), ("Análise", False, NOW + 600), ("Onze", False, None)]},
        "injured": [{"name": "Jogador 3", "games": 6, "until": NOW + 3600, "ready": False}],
        "suspended": [],
    }
    base.update(changes)
    return base


def test_the_version_in_the_window_is_the_version_of_the_project():
    project = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text(encoding="utf-8"))
    assert osmbot.__version__ == project["project"]["version"]


def test_the_card_header_says_the_opponent_home_or_away_and_warns_of_a_direct_rival():
    view = club_view(club(), NOW)
    assert view["subtitle"] == [("⚠ confronto direto · ", YELLOW), ("vs Clube B (4.º) (H) · em 2h00", YELLOW)]
    calm = club_view(club(next={"opponent": "Clube C", "rank": 12, "side": "A", "danger": False, "cup": True}), NOW)
    assert calm["subtitle"] == [("vs Clube C (12.º) (A) · taça · em 2h00", None)]


def test_league_cup_and_squad_value_and_one_money_line_with_the_sales():
    view = club_view(club(), NOW)
    assert view["facts"] == [("Liga", "3.º", None), ("Taça", "quartos-de-final", None),
                             ("Valor do plantel", "2.º · 588,7 M · média 29,43 M", None)]
    assert view["money"] == "10,3 M"  # funds and savings together (owner, 2026-10-08)
    assert view["sales"] == ["✓ Jogador 7 vendido · +166,66 M"]
    assert view["alert"] == "1 vaga livre na lista de transferências"
    assert club_view(club(free_slots=0), NOW)["alert"] == ""
    out = club_view(club(cup=("eliminado nos oitavos-de-final", "out"), value=None), NOW)
    assert out["facts"][1][2] == GREY and out["facts"][2][1:] == ("—", GREY)


def test_stadium_has_the_parts_standing_still_and_the_one_going_up_with_its_time():
    view = club_view(club(), NOW)
    assert view["stadium"] == {"still": [("Campo 3/3", GREEN), ("Capacidade 2/3", None)],
                               "moving": [("Treinos 2/3 · a subir, acaba em 9h00", BLUE)]}


def test_pre_match_checklist_shows_done_waiting_and_open_points():
    prep = club_view(club(), NOW)["prep"]
    assert prep["pct"] == "35%" and prep["colour"] == YELLOW
    assert prep["steps"] == [("✓ Amigável", GREEN), ("⏳ Análise 0h10", BLUE), ("○ Onze", GREY)]
    later = club_view(club(), NOW + 700)["prep"]
    assert later["steps"][1] == ("◉ Análise por levantar", YELLOW)


def test_injured_and_suspended_players_with_the_doctor_timer():
    view = club_view(club(), NOW)
    assert view["injured"] == [("Jogador 3 (6 jogos)", YELLOW), (" → no médico · acaba em 1h00", BLUE)]
    assert view["suspended"] == [("0", GREY)]
    assert view["tired"] == "Jogador 5 68%"
    first, ready = view["trainings"]
    assert first[2:4] == ("4h00", BLUE) and ready[2:5] == ("pronto", GREEN, 1.0)


def test_daily_rewards_and_the_accumulated_videos():
    daily = {"login": {"claimable": False, "day": 5, "renews": NOW + 3600},
             "missions": {"total": 3, "claimed": 2, "day_pending": False},
             "videos": {"count": 3, "threshold": 10, "claimable": False, "reopen": None}}
    parts, videos = daily_view(daily, NOW)
    assert parts == [("início de sessão ✓ (dia 5)", GREEN), ("missões 2/3", YELLOW), ("prémio do dia —", GREY),
                     ("novo dia em 1h00", BLUE)]
    assert videos == {"text": "3/10", "colour": None, "done": 0.3}
    assert daily_view(None, NOW) == ([], None)


def test_the_bottom_panel_has_the_coins_gain_and_the_timers():
    snap = {"coins": 2586, "clubs": [club()], "ads": {"shop": {"open": False, "reopen": NOW + 1800},
                                                      "training": {"open": True}, "money": {"open": False}},
            "daily": {"videos": {"count": 0, "threshold": 10, "claimable": False, "reopen": NOW + 600}}}
    account = account_view(snap, {"start": NOW - 600, "coins0": 2574}, NOW)
    assert account["coins"] == "2 586" and account["jump"] == "+12"
    assert account["since"] == "desde que o bot foi ligado (0h10)"
    assert account["timers"] == [("Vídeos da loja", "◷ em 0h30", BLUE), ("Acelerar treinos", "● disponível", GREEN),
                                 ("Vídeos de dinheiro", "—", GREY), ("Reward cumulativo", "0/10 · reabre em 0h10", None)]
    stopped = account_view(snap, None, NOW)
    assert stopped["jump"] == "" and stopped["since"] == ""


def test_the_status_bar_says_only_the_next_thing_and_nothing_before_the_first_read():
    snap = {"coins": 1, "clubs": [club()], "ads": {"shop": {"open": False, "reopen": NOW + 1800}}}
    assert next_check(snap, NOW) == "próximo: treino por recolher em 0h00"
    assert board_view(None, None, NOW) is None
    assert [c["name"] for c in board_view(snap, None, NOW)["clubs"]] == ["Clube A"]


def test_a_club_read_without_the_extras_still_shows():
    bare = {k: v for k, v in club().items() if k not in ("next", "cup", "value", "free_slots", "sales", "prep",
                                                         "injured", "suspended")}
    view = club_view(bare, NOW)
    assert view["subtitle"] == [("Liga A · em 2h00", GREY)] and view["facts"][1][1] == "—"
    assert view["injured"] == [("0", GREY)] and view["prep"]["steps"] == []
