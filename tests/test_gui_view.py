import tomllib
from pathlib import Path

import osmbot
from osmbot.gui.view import RED, care_ring, sponsor_view, squad_view, stadium_rings
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
        "cup": ("quartos-de-final", "in"), "value": (2, 588_700_000, 29_435_000.0, 20, 18),
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
    assert view["facts"] == [("Liga", "3.º", None), ("Taça", "quartos-de-final", None)]
    assert view["squad"] == {"place": "2.º", "colour": GREEN, "total": "588,7 M", "tip": "20 jogadores · média 29,43 M",
                             "table_tip": None}
    assert view["money"] == "10,3 M"  # funds and savings together (owner, 2026-10-08)
    assert view["sales"] == ["✓ Jogador 7 vendido · +166,66 M"]
    assert view["alert"] == "1 vaga livre na lista de transferências"
    assert club_view(club(free_slots=0), NOW)["alert"] == ""
    stale_view = club_view(club(stale=[{"name": "Kovacic", "for": 95 * 3600, "normal": 46 * 3600}]), NOW)
    stale = stale_view["alerts"]
    assert stale_view["alerts_tip"] == "Normal a este preço\nKovacic: ~1 dia e 22h00"  # on hover (owner, 2026-10-22)
    assert club_view(club(), NOW)["alerts_tip"] == ""
    rest = club_view(club(rest=[{"name": "Kane", "fitness": 83, "then": 79, "first": "Elche", "second": "Real Madrid"}]), NOW)
    assert rest["rest"] == ["Kane 83%: se jogar contra o Elche, chega a ~79% contra o Real Madrid"]
    assert stale == ["1 vaga livre na lista de transferências",  # one under the other (owner, 2026-10-22)
                     "Kovacic à venda há 3 dias e 23h00"]
    out = club_view(club(cup=("eliminado nos oitavos-de-final", "out"), value=None), NOW)
    assert out["facts"][1][2] == GREY and out["squad"]["total"] == "—"


def test_squad_value_place_is_green_at_the_top_red_at_the_bottom_yellow_between():
    assert [squad_view((place, 1, 1.0, 20, 18))["colour"] for place in (1, 2, 3, 15, 16, 18)] ==         [GREEN, GREEN, YELLOW, YELLOW, RED, RED]
    assert squad_view((17, 1, 1.0))["colour"] == YELLOW  # an older reading without the league size: never red


def test_sponsors_say_only_the_money_and_warn_of_an_empty_slot_on_hover():
    assert sponsor_view({"slots": 4, "revenue": 1_120_000}) == {"text": "1,12 M/ronda", "colour": None, "tip": ""}
    assert sponsor_view({"slots": 3, "revenue": 900_000}) == {"text": "⚠ 900 k/ronda", "colour": YELLOW,
                                                              "tip": "1 vaga vazia nos patrocinadores"}


def test_stadium_has_the_parts_standing_still_and_the_one_going_up_with_its_time():
    view = club_view(club(), NOW)  # the length is unknown here: only the time
    assert view["stadium"] == {"still": [("Campo 3/3", GREEN), ("Capacidade 2/3", None)],
                               "moving": [{"text": "Treinos 2/3", "left": "9h00", "done": None}]}


def test_the_part_going_up_has_a_bar_when_its_length_is_known():
    data = club()
    data["stadium"]["lengths"] = {"Treinos": 18 * 3600}
    assert club_view(data, NOW)["stadium"]["moving"] == [{"text": "Treinos 2/3", "left": "9h00", "done": 0.5}]


def test_pre_match_checklist_shows_done_waiting_and_open_points():
    prep = club_view(club(), NOW)["prep"]
    assert set(prep) == {"steps", "boosts"}  # no percentage, only the marks (owner, 2026-10-09)
    assert prep["steps"] == [("done", "Amigável", "", []), ("waiting", "Análise", "0h10", []), ("open", "Onze", "", [])]
    later = club_view(club(), NOW + 700)["prep"]
    assert later["steps"][1] == ("collect", "Análise", "por levantar", [])


def test_secret_training_and_training_camp_come_after_the_steps_green_when_booked():
    boosts = [{"kind": "secret", "name": "Treino secreto", "on": True, "blocked": ""},
              {"kind": "camp", "name": "Estágio", "on": False, "blocked": ""}]
    prep = club_view(club(prep={"steps": [], "boosts": boosts}), NOW)["prep"]
    assert prep["boosts"] == [{"icon": "secret", "name": "Treino secreto", "on": True, "tip": "Marcado para o próximo jogo"},
                              {"icon": "camp", "name": "Estágio", "on": False, "tip": "Não marcado"}]
    blocked = [{**boosts[1], "blocked": "You don't have a match scheduled this matchday."}]
    assert club_view(club(prep={"steps": [], "boosts": blocked}), NOW)["prep"]["boosts"][0]["tip"] == "Sem jogo nesta jornada"


def test_a_step_out_of_the_owner_s_rule_is_yellow_and_says_why():
    data = club()
    data["prep"] = {"steps": [("Banco", False, "fora da regra")], "why": {"Banco": ["Akanni 51 entra antes de Ndicka 107"]}}
    assert club_view(data, NOW)["prep"]["steps"] == [("progress", "Banco", "", ["Akanni 51 entra antes de Ndicka 107"])]


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
    assert parts == [("done", "Início de sessão (dia 5)", GREEN), ("progress", "Missões 2/3", YELLOW),
                     ("open", "Prémio diário", GREY), ("waiting", "Novo dia em 1h00", BLUE)]
    assert videos == {"text": "3/10", "colour": None, "done": 0.3}
    assert daily_view(None, NOW) == ([], None)


def test_the_bottom_panel_has_the_coins_gain_and_the_timers():
    snap = {"coins": 2586, "clubs": [club()], "ads": {"shop": {"open": False, "reopen": NOW + 1800},
                                                      "training": {"open": True}, "money": {"open": False}},
            "daily": {"videos": {"count": 0, "threshold": 10, "claimable": False, "reopen": NOW + 600}}}
    account = account_view(snap, {"start": NOW - 600, "shop_coins": 12}, NOW)
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


def test_the_coins_gain_counts_only_the_shop_videos_never_what_the_owner_spends():
    from osmbot.gui.view import account_view

    snap = {"coins": 2400, "ads": {}, "daily": {}}  # the owner spent 200 since the start
    assert account_view(snap, {"start": NOW - 600, "coins0": 2600, "shop_coins": 9}, NOW)["jump"] == "+9"
    assert account_view(snap, {"start": NOW - 600}, NOW)["jump"] == "+0"


def _game(shop=False, training=False, money=False, trainings=None):
    from datetime import datetime  # noqa: F401 (used by the callers' expected times)

    a = club(name="Clube A", money=(0, 5_000_000), trainings=trainings if trainings is not None else [
        {"id": 1, "name": "Jogador 1", "pos": "ATA", "finish": NOW + 5 * 3600, "claimed": False},
        {"id": 2, "name": "Jogador 2", "pos": "GR", "finish": NOW + 4 * 3600, "claimed": False}])
    b = club(name="Clube B", money=(0, 9_000_000), trainings=[])
    return {"clubs": [a, b], "ads": {"shop": {"open": shop}, "training": {"open": training}, "money": {"open": money}}}


def test_now_and_next_during_a_burst_of_shop_videos():
    from osmbot.gui.view import doing_view

    game = _game(shop=True, training=True)
    assert doing_view(game, {"text": "vídeo da loja 8/9", "kind": "shop", "count": 8}, NOW) == \
        "agora: vídeo da loja 8/9 · a seguir: vídeo da loja 9/9"
    assert doing_view(game, {"text": "vídeo da loja 9/9", "kind": "shop", "count": 9}, NOW) == \
        "agora: vídeo da loja 9/9 · a seguir: vídeo de treino Jogador 1 (Clube A)"


def test_the_next_training_video_goes_to_the_one_with_most_time_left_after_this_one():
    from osmbot.gui.view import doing_view

    game = _game(training=True)
    now = {"text": "vídeo de treino Jogador 1 (Clube A)", "kind": "training", "count": 1, "session": 1}
    assert doing_view(game, now, NOW) == "agora: vídeo de treino Jogador 1 (Clube A) · a seguir: vídeo de treino Jogador 2 (Clube A)"


def test_after_the_videos_it_names_what_it_waits_for():
    from datetime import datetime

    from osmbot.gui.view import doing_view

    game = _game()
    at = f"{datetime.fromtimestamp(NOW + 4 * 3600):%H:%M}"
    assert doing_view(game, {"text": "à espera"}, NOW) == f"agora: à espera · a seguir: recolher treino Jogador 2 (Clube A) às {at}"
    money = _game(money=True)
    assert doing_view(money, {"text": "estádio"}, NOW) == "agora: estádio · a seguir: vídeo de dinheiro (Clube B)"
    assert doing_view(money, {"text": "à espera"}, NOW).startswith("agora: à espera · a seguir: recolher treino")
    assert doing_view(game, None, NOW) == ""


def test_stadium_rings_say_which_part_goes_up_and_the_level_of_the_others():
    rings = stadium_rings({"parts": [("Treinos", 3, 3, None), ("Capacidade", 0, 3, None), ("Campo", 1, 3, NOW + 9 * 3600)],
                           "lengths": {"Campo": 18 * 3600}}, NOW)
    assert [(r["name"], r["level"], r["state"], r["left"]) for r in rings] == [
        ("Treinos", "3/3", "top", "no máximo"), ("Capacidade", "0/3", "still", "parado"), ("Campo", "1/3", "moving", "9h00")]
    assert rings[2]["done"] == 0.5


def test_doctor_and_lawyer_rings():
    assert care_ring("Médico", [], NOW)["state"] == "none"
    working = care_ring("Médico", [{"name": "J3", "games": 2, "until": NOW + 3600}], NOW)
    assert (working["state"], working["centre"], working["name"]) == ("working", "1h00", "J3") and working["done"] == 7 / 8
    event = care_ring("Médico", [{"name": "J3", "games": 2, "until": NOW + 3600, "length": 3 * 3600}], NOW)
    assert round(event["done"], 3) == round(2 / 3, 3)  # a 3 h case of the Super Staff: drawn against its own length, not 8 h
    assert care_ring("Médico", [{"name": "J3", "games": 2, "ready": True}], NOW)["centre"] == "pronto"
    assert care_ring("Médico", [{"name": "J3", "games": 4}, {"name": "J5", "games": 1}], NOW)["name"] == "J3 +1"
    one = care_ring("Advogado", [{"name": "J8", "games": 1}], NOW, lawyer=True)
    assert (one["state"], one["sub"]) == ("blocked", "1 jogo · não dá")  # the game refuses a 1-game suspension
    assert care_ring("Advogado", [{"name": "J8", "games": 3}], NOW, lawyer=True)["state"] == "waiting"


def test_daily_hover_texts():
    from osmbot.gui.view import daily_tips

    daily = {"login": {"claimable": False, "day": 21, "renews": NOW + 3600, "today": {"type": 1, "value": 5}},
             "missions": {"total": 3, "claimed": 1, "day_pending": False, "today": 2,
                          "dailies": [{"text": "Train any player", "progress": 2, "goal": 2, "claimed": True},
                                      {"text": "Spend Club Funds", "progress": 10, "goal": 5_000_000, "claimed": False}],
                          "week": [{"day": 2, "prize": {"type": 15, "value": 2}, "claimed": False},
                                   {"day": 3, "prize": {"type": 8, "value": 3_000_000}, "claimed": False}]}}
    tips = daily_tips(daily)
    assert tips["login"] == [("coins", "Hoje: 5 boss coins", None)]
    assert tips["missions"] == [("done", "Treinar um jogador (2/2)", None), ("progress", "Gastar fundos do clube (0 M/5 M)", None)]
    assert tips["day"] == [("missions", "Hoje: 2 de energia (depois das 3 missões)", None),
                           ("funds", "Amanhã: pacote de 3 M de fundos", GREY)]
    assert daily_tips(daily, "en")["missions"][0] == ("done", "Train any player (2/2)", None)
    daily["missions"]["today"] = 1  # the week's day 1: the game lists no prize for it
    assert daily_tips(daily)["day"] == [(None, "Sem prémio do dia", GREY), ("missions", "Amanhã: 2 de energia", GREY)]
    pieces = board_view({"clubs": [], "coins": 1, "ads": {}, "daily": daily}, None, NOW)["daily"]
    assert [p[3][0][1] for p in pieces] == ["Hoje: 5 boss coins", "Treinar um jogador (2/2)", "Sem prémio do dia"]


def test_events_calendar_for_the_top_bar():
    from datetime import datetime

    from osmbot.gui.view import ORANGE, calendar_view

    months = [{"mes": "2026-10", "eventos": [
        {"inicio": "2026-10-10", "fim": "2026-10-11", "nome": "Transfer Madness", "efeitos": ["Possible to put up to 6 players on transfer list"]},
        {"inicio": "2026-10-14", "fim": "2026-10-14", "nome": "Super Staff", "efeitos": ["Faster Analyst: 15min to bring a report"]}]}]
    now = datetime(2026, 10, 12, 20).timestamp()
    view = calendar_view(months, now)
    assert view["label"] == [("Próximo evento: ", GREY), ("Super Staff", ORANGE), (" · 14/10", None)]
    month, = view["months"]
    assert month["title"] == "Outubro 2026" and len(month["weeks"]) == 5  # 1 Oct is a Thursday, 31 a Saturday
    assert month["weeks"][0][:3] == [None, None, None] and month["weeks"][0][3]["day"] == 1
    cells = {c["day"]: c for week in month["weeks"] for c in week if c}
    assert len(cells) == 31 and cells[12]["today"] and cells[10]["past"]
    assert cells[10]["events"] == [{"name": "Transfer Madness", "when": "10–11/10", "effects": ["Até 6 jogadores na lista de transferências"]}]
    assert cells[13]["events"] == []
    during = calendar_view(months, datetime(2026, 10, 14, 9).timestamp(), "en")
    assert during["label"][0] == ("Event now: ", GREY) and during["months"][0]["title"] == "October 2026"
    assert calendar_view(None, now) is None


def test_every_effect_of_the_october_schedule_reads_in_portuguese():
    from osmbot.events.calendar import effect_text

    lines = ["Legend players will be added on Transfer List",
             "Higher Training Progression (when claiming) with every Training and Friendly",
             "Faster stadium upgrades (4H)", "More progression and faster trainings: 5H regular trainers, 4H Universal Trainer",
             "Higher sale chance and more players added by engine on each transfer round",
             "Possible to put up to 6 players on transfer list", "Faster Scout: 2H instead of 16H",
             "Faster Analyst: 15min to bring a report", "Shorter timers for Doctor and lawyer: 3H",
             "Faster trainers: Normal trainers 2H and Universal Trainer 1:30H",
             "Higher training progression, when claiming results, for old players",
             "Faster training: 2H normal trainers and 1:30H Universal Trainer", "Scouted players less expensive",
             "Extra Training Progression with every Friendly", "Shorter timers when upgrading your stadium (4H)",
             "Training timers: 4H normal trainers and 3H Universal Trainer",
             "Extreme Training Progression (when claiming) with every Training and Friendly",
             "Faster training: 3H normal trainers and 2H Universal Trainer"]
    for line in lines:
        assert effect_text(line) != line, line
    assert effect_text("Faster trainers: Normal trainers 2H and Universal Trainer 1:30H") == "Treinos de 2 h; treinador universal 1:30 h"
    assert effect_text("Extra Training Progression with every Friendly") == "Progressão extra de treino em cada amigável"


def test_the_circle_shows_the_strength_ours_blue_the_opponents_compared_with_ours():
    from osmbot.gui.view import rating_badge

    assert rating_badge(109) == {"text": "109", "colour": BLUE, "tip": ""}  # no hover (owner, 2026-10-15)
    assert [rating_badge(theirs, ours=108)["colour"] for theirs in (73, 107, 109, 110)] == [GREEN, YELLOW, YELLOW, RED]
    assert rating_badge(None, ours=108) is None  # not analysed yet: no circle


def test_the_place_says_champions_once_won_and_the_hover_has_the_top_3_and_the_goal():
    from osmbot.gui.view import table_view

    table = {"rows": [(1, "Clube 1", 46, False, 20, 31), (2, "Clube 2", 45, True, 20, -2), (3, "Clube 3", 43, False)],
             "goal": 4, "champion": False}  # the 3rd as in an older reading: no games and goal difference
    header, grid = table_view({"ranking": 2, "table": table})
    assert header == "2.º Campeonato" and [name for name, _ in grid["columns"]] == ["#", "Clube", "J", "DG", "Pts"]
    assert grid["rows"] == [(["1", "Clube 1", "20", "+31", "46"], False), (["2", "Clube 2", "20", "-2", "45"], True),
                            (["3", "Clube 3", "", "", "43"], False)]
    assert grid["foot"] == "Objetivo: 4.º ou acima" and grid["mark"] is None  # no round played yet: no mark
    assert table_view({"ranking": 2, "week": 20, "table": table})[1]["mark"] == "done"  # within the goal: the green tick
    assert table_view({"ranking": 5, "week": 20, "table": table})[1]["mark"] == "collect"  # below it: yellow (owner, 2026-10-15)
    assert table_view({"ranking": 5, "week": -2, "table": table})[1]["mark"] is None  # pre-season
    assert table_view({"ranking": 1, "table": {**table, "champion": True, "goal": 1}})[0] == "Campeões"
    assert table_view({"ranking": 1, "table": {**table, "goal": 1}})[1]["foot"] == "Objetivo: 1.º"
    assert table_view({"ranking": 3}) == ("3.º Campeonato", None)


def test_a_tired_starter_without_cover_says_so_and_the_sale_options_show_on_hover():
    from osmbot.gui.view import tired_view

    club = {"tired": [{"name": "Jogador 1", "pos": "DEF", "fitness": 68}, {"name": "Jogador 2", "pos": "MED", "fitness": 76}],
            "cover": {"DEF": [{"nome": "Jogador 9", "pos": "DEF", "especifica": 3, "rating": 88, "idade": 24, "preco": 9_000_000}]}}
    text, tip = tired_view(club)
    assert text == "Jogador 1 68% (sem suplente DEF) · Jogador 2 76%"
    assert tip == "SALE DEF que cabem no dinheiro:\nDC 88 · Jogador 9 (24 anos) · 9 M"  # the specific position (2026-10-20)
    assert tired_view({**club, "cover": {"DEF": []}})[1] == "Nenhum SALE DEF cabe no dinheiro"
    assert tired_view({"tired": []}) == ("", "")


def test_the_sale_line_shows_the_best_and_the_three_on_hover():
    from osmbot.gui.view import sale_view

    pick = {"pos": "DEF", "rating": 85, "nome": "S1", "idade": 26, "preco": 11_000_000, "razao": 1.1, "lucro": 14_000_000,
            "reforco": True, "fraco": "T1 79", "pechincha": True}
    deal = {**pick, "nome": "S2", "lucro": 9_000_000, "reforco": False, "fraco": None, "pechincha": False}
    assert sale_view({}) is None and sale_view({"sale": {"picks": [], "certo": True}}) is None
    sale = sale_view({"sale": {"picks": [pick, deal], "certo": True}})
    assert (sale["player"], sale["price"], sale["profit"]) == ("DEF 85 · S1", "11 M", "lucro ~14 M")
    assert sale["tags"] == ["reforço", "pechincha"] and sale["more"] == 1  # the blue stripe (owner, 2026-10-15)
    assert sale["sale"] and not sale_view({"sale": {"picks": [{**deal, "razao": 1.7}], "certo": True}})["sale"]  # no ribbon
    rows = sale["tip"]["rows"]
    assert rows[0][0][-1] == "reforço (> T1 79) · pechincha" and rows[1][0][-1] == "" and not sale["tip"]["foot"]
    assert rows[0][0][5] == "1,1×" and sale["tip"]["columns"][5][0] == "× valor"  # price against value, with a comma
    winger = sale_view({"sale": {"picks": [{**pick, "especifica": 8}], "certo": True}})  # EE, not MED (owner, 2026-10-20)
    assert winger["player"] == "EE 85 · S1" and winger["tip"]["rows"][0][0][0] == "EE"
    unsure = sale_view({"sale": {"picks": [deal], "certo": False}})
    assert unsure["profit"] == "lucro ~9 M?" and unsure["tip"]["foot"] == "? = esta liga não vendeu ao máximo nos últimos 3 dias"


def test_squad_hover_is_the_table_by_value():
    from osmbot.gui.view import squad_view

    rows = [(1, "A", 1_032_740_000, 21, 49_178_095, True), (2, "B", 940_000_000, 22, 42_727_272, False)]
    grid = squad_view((1, 1_032_740_000, 49_178_095, 21, 20), rows)["table_tip"]
    assert [name for name, _ in grid["columns"]] == ["#", "Clube", "Valor", "Jogadores", "Média"]
    assert grid["rows"][0] == (["1", "A", "1032,74 M", "21", "49,18 M"], True) and grid["rows"][1][1] is False
    assert squad_view((1, 10, 1, 10, 20))["table_tip"] is None  # no table: the players and average only
    from osmbot.gui.view import rating_badge

