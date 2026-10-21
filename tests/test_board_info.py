from osmbot.board.info import cup_phase, next_match, squad_value, track_sales

ROUNDS = [{"weekNr": 6, "name": "Preliminaries"}, {"weekNr": 14, "name": "Round of 16"},
          {"weekNr": 22, "name": "Quarter-finals"}, {"weekNr": 42, "name": "Final"}]
TEAMS = [{"id": 1, "name": "Nós", "ranking": 2}, {"id": 6, "name": "Getafe", "ranking": 8},
         {"id": 4, "name": "Rival", "ranking": 1}, {"id": 9, "name": "Perto", "ranking": 4}]


def match(week, home, away, kind=0, winner=0):
    return {"weekNr": week, "homeTeamId": home, "awayTeamId": away, "matchType": kind, "winnerTeamId": winner}


def test_next_match_has_the_opponent_its_place_home_or_away():
    matches = [match(14, 1, 19, kind=1, winner=1), match(14, 1, 4, kind=2), match(15, 1, 6), match(16, 4, 1)]
    assert next_match(matches, TEAMS, 1, 14) == {"opponent": "Getafe", "opponent_id": 6, "rank": 8, "side": "H", "danger": False, "cup": False, "referee_id": None, "neutral": False}
    assert next_match(matches, TEAMS, 1, 15) == {"opponent": "Rival", "opponent_id": 4, "rank": 1, "side": "A", "danger": True, "cup": False, "referee_id": None, "neutral": False}
    assert next_match([match(15, 9, 1)], TEAMS, 1, 14)["danger"]  # 2 places apart: still a direct confrontation
    assert next_match(matches, TEAMS, 1, 16) is None


def test_cup_phase_next_round_eliminated_winner_and_out_of_the_cup():
    assert cup_phase(ROUNDS, [match(14, 1, 19, 1, winner=1), match(22, 16, 1, 1)], 1, 14) == ("quartos-de-final", "in")
    assert cup_phase(ROUNDS, [match(14, 1, 19, 1, winner=19)], 1, 14) == ("eliminado nos oitavos-de-final", "out")
    assert cup_phase(ROUNDS, [match(14, 1, 19, 1, winner=1)], 1, 15) == ("quartos-de-final", "in")  # not drawn yet
    assert cup_phase(ROUNDS, [match(42, 1, 3, 1, winner=1)], 1, 42) == ("vencedor", "won")
    assert cup_phase(ROUNDS, [], 1, 2) == ("pré-eliminatória", "in")  # before the cup starts
    assert cup_phase(ROUNDS, [], 1, 43) == ("—", "none")


def test_squad_value_place_total_and_average():
    values = {1: (588_000_000, 20), 4: (592_000_000, 20), 6: (79_000_000, 23)}
    assert squad_value(values, 1) == (2, 588_000_000, 29_400_000.0, 20, 3)
    assert squad_value(values, 99) is None


def test_a_sale_is_a_listed_player_gone_from_the_squad_and_stays_until_a_slot_is_filled():
    state = track_sales({}, {7: {"name": "A", "price": 100}, 8: {"name": "B", "price": 50}}, {7, 8, 9})
    assert state["sales"] == []  # the first read only learns what is listed
    state = track_sales(state, {8: {"name": "B", "price": 50}}, {8, 9})  # A left the list and the squad: sold
    assert [(s["name"], s["price"]) for s in state["sales"]] == [("A", 100)]
    state = track_sales(state, {}, {8, 9})  # B taken off the list but still in the squad: not a sale
    assert [(s["name"], s["price"]) for s in state["sales"]] == [("A", 100)] and state["new_sales"] == []
    state = track_sales(state, {9: {"name": "C", "price": 70}}, {8, 9})  # the owner lists another: the sale goes away
    assert state["sales"] == []


def test_listing_and_sale_times_for_the_log():
    from osmbot.game.sales import describe

    state = track_sales({}, {7: {"name": "A", "price": 100, "value": 40}}, {7, 8}, now=1000.0)
    assert state["listed"][7]["since"] is None  # already listed before the bot looked: unknown
    state = track_sales(state, {7: {"name": "A", "price": 100, "value": 40},
                                8: {"name": "B", "price": 75_000_000, "value": 40_000_000}}, {7, 8}, now=2000.0)
    assert state["listed"][8]["since"] == 2000.0 and [i["name"] for i in state["new_listings"]] == ["B"]
    assert describe("Clube", state) == ["Lista de transferências: B (Clube) à venda por 75 M (75% do máximo ≈ 100 M)"]
    state = track_sales(state, {7: {"name": "A", "price": 100, "value": 40}}, {7}, now=2000.0 + 5 * 3600 + 12 * 60)
    assert state["new_sales"][0]["since"] == 2000.0 and state["listed"][7]["since"] is None  # kept from read to read
    line = describe("Clube", state)[0]
    assert line.startswith("Venda: B (Clube) vendido por 75 M (75% do máximo ≈ 100 M); à venda desde ") and line.endswith("demorou 5h12")


def test_the_games_listing_time_wins():
    state = track_sales({}, {7: {"name": "A", "price": 100, "since": 500.0}}, {7}, now=1000.0)
    assert state["listed"][7]["since"] == 500.0  # timeStampForSale: known even at the very first read
    state = track_sales(state, {}, set(), now=4000.0)
    assert state["new_sales"][0]["since"] == 500.0 and state["new_sales"][0]["sold"] == 4000.0


def test_a_sale_takes_its_price_and_time_from_the_leagues_transfers():
    from osmbot.board.info import settle_sales
    from osmbot.game.sales import describe

    listed = {7: {"name": "A", "price": 104_000_000, "value": 44_700_000, "since": 1000.0},
              8: {"name": "B", "price": 89_000_000, "value": 35_600_000, "since": 2000.0}}
    state = track_sales(track_sales({}, listed, {7, 8}, now=3000.0), {}, set(), now=90_000.0)  # the bot was stopped
    transfers = [{"player": {"id": 7}, "sourceTeam": {"id": 5}, "price": 83_970_000, "timestamp": 50_000.0},  # listed again
                 {"player": {"id": 8}, "sourceTeam": {"id": 5}, "price": 89_000_000, "timestamp": 60_000.0},
                 {"player": {"id": 8}, "sourceTeam": {"id": 6}, "price": 1, "timestamp": 70_000.0}]  # another club's
    settle_sales(state["new_sales"], transfers, team_id=5)
    a, b = state["new_sales"]
    assert (a["price"], a["sold"], a["since"], a["confirmada"]) == (83_970_000, 50_000.0, None, True)
    assert (b["price"], b["sold"], b["since"]) == (89_000_000, 60_000.0, 2000.0) and state["sales"][0] is a
    lines = describe("Clube", state)
    assert "vendido por 83,97 M (75% do máximo" in lines[0] and "listado de novo com o bot parado, vendido às " in lines[0]
    assert "demorou" not in lines[0] and "à venda desde " in lines[1] and "vendido às " in lines[1]


def test_the_teams_strength_is_the_best_player_for_each_place_of_the_current_formation():
    from osmbot.board.info import team_rating

    def player(pos, rating, lineup=0):
        return {"position": pos, "statAtt": rating, "statOvr": rating, "statDef": rating, "lineup": lineup}

    # a 3-5-2 eleven; the squad has more strong forwards than the formation uses
    eleven = [player(4, 70, 1)] + [player(3, 72, 2 + i) for i in range(3)] + [player(2, 74, 5 + i) for i in range(5)]         + [player(1, 70, 10), player(1, 70, 11)]
    squad = eleven + [player(1, 90), player(1, 90), player(1, 90), player(3, 80), player(4, 99)]
    # GR 99, DEF 80 72 72, MED 74×5, ATA 90 90 -> 873 / 11 = 79.36; the 3rd forward and the spare keeper do not count
    assert team_rating(squad) == 79
    assert team_rating([dict(p, lineup=0) for p in squad]) is None  # another club before the analysis: no eleven known


def test_league_summary_has_the_top_3_with_points_the_goal_and_when_the_title_is_won():
    from osmbot.board.info import league_summary

    teams = [{"id": i, "name": f"Clube {i}", "ranking": i} for i in range(1, 6)]
    standings = [{"teamId": i, "points": p, "won": 14, "drew": 4, "lost": 2, "goalsFor": 40, "goalsAgainst": 10 + i}
                 for i, p in zip(range(1, 6), (46, 45, 43, 40, 32))]
    ahead = [match(20, 2, 3), match(21, 4, 2)]  # the 2nd still has 2 league matches
    summary = league_summary(standings, teams, ahead, 2, 19, 4)
    assert summary == {"rows": [(1, "Clube 1", 46, False, 20, 29), (2, "Clube 2", 45, True, 20, 28),
                                (3, "Clube 3", 43, False, 20, 27)],
                       "goal": 4, "champion": False}
    assert [r[0] for r in league_summary(standings, teams, ahead, 5, 19, 11)["rows"]] == [1, 2, 5]  # below 3rd
    won = [{"teamId": 1, "points": 52}, {"teamId": 2, "points": 45}]
    assert league_summary(won, teams, ahead, 1, 19, 1)["champion"]  # 45 + 2×3 = 51 < 52
    assert not league_summary([{"teamId": 1, "points": 51}, {"teamId": 2, "points": 45}], teams, ahead, 1, 19, 1)["champion"]
    assert league_summary([], teams, ahead, 1, 19, 1) is None


def test_value_table_shows_the_2_below_when_first_else_1_above_and_1_below():
    from osmbot.board.info import value_table

    values = {1: (1_033_000_000, 21), 2: (940_000_000, 22), 3: (534_000_000, 19), 4: (100_000_000, 20)}
    names = {1: "A", 2: "B", 3: "C", 4: "D"}
    assert [(r[0], r[1], r[5]) for r in value_table(values, names, 1)] == [(1, "A", True), (2, "B", False), (3, "C", False)]
    assert [r[0] for r in value_table(values, names, 3)] == [2, 3, 4]
    assert [r[0] for r in value_table(values, names, 4)] == [3, 4]
    assert value_table(values, names, 9) == []


def test_someone_new_in_the_squad_is_a_purchase_only_when_the_league_has_it():
    from osmbot.board.info import purchases
    from osmbot.game.sales import describe

    state = track_sales({}, {}, {1, 2}, now=1000.0)
    assert state["new_members"] == []  # the first read only learns the squad
    state = track_sales(state, {}, {1, 2, 3, 4}, now=2000.0)
    assert state["new_members"] == [3, 4]
    transfers = [{"player": {"id": 3, "name": "Fagioli"}, "destinationTeam": {"id": 9}, "sourceTeam": {"name": "Fiorentina"},
                  "price": 8_860_000, "value": 6_490_000, "timestamp": 1900.0},
                 {"player": {"id": 4, "name": "Outro"}, "destinationTeam": {"id": 2}, "price": 1, "timestamp": 1900.0}]
    state["bought"] = purchases(state["new_members"], transfers, team_id=9)  # 4 came from a pack: no purchase
    assert describe("Clube", state) == ["Compra: Fagioli (Clube) comprado por 8,86 M (1,37 × o valor), de Fiorentina"]


def test_a_sale_says_the_profit_since_the_purchase():
    from osmbot.board.info import settle_sales
    from osmbot.game.sales import describe

    state = track_sales(track_sales({}, {7: {"name": "A", "price": 20_000_000, "value": 8_000_000, "since": 1000.0}}, {7},
                                    now=1000.0), {}, set(), now=1000.0 + 3600)
    transfers = [{"player": {"id": 7}, "destinationTeam": {"id": 5}, "price": 12_000_000, "timestamp": 1000.0 - 86_400},
                 {"player": {"id": 7}, "sourceTeam": {"id": 5}, "price": 20_000_000, "timestamp": 1000.0 + 3600}]
    settle_sales(state["new_sales"], transfers, team_id=5)
    assert describe("Clube", state)[0].endswith("demorou 1h00; lucro +8 M em 1 dia e 1h00")


def test_a_player_on_the_list_twice_the_usual_time_for_his_price_is_warned():
    from osmbot.board.info import sale_time, stale_listings

    hour = 3600
    history = [(3e6, 4 * hour), (4e6, 5 * hour), (2e6, 6 * hour), (70e6, 40 * hour), (80e6, 50 * hour)]
    listed = {1: {"name": "Barato", "price": 3e6, "since": 0}, 2: {"name": "Novo", "price": 4e6, "since": 9 * hour},
              3: {"name": "Caro", "price": 90e6, "since": 0}, 4: {"name": "Sem hora", "price": 1e6, "since": None}}
    assert stale_listings(listed, history, now=11 * hour) == [{"name": "Barato", "for": 11 * hour, "normal": 5 * hour}]
    # the 50-100 M band has only 2 sales: no warning there yet
    line = "2026-10-17 19:24:06  Venda: Chalobah (FC Van) vendido por 91,26 M (75% do máximo ≈ 121,04 M); " \
           "à venda desde 16/10 11:59, vendido às 17/10 19:23, demorou 1 dia e 7h24; lucro +30 M em 2 dias e 0h10"
    assert sale_time(line) == (("Chalobah", "FC Van", "17/10 19:23"), 91.26e6, (31 * 60 + 24) * 60)
    assert sale_time("Venda: X (C) vendido por 450 k; à venda desde 1/1 10:00, vendido às 1/1 12:00, demorou 2h00")[1:] == (450e3, 7200)
    assert sale_time("Venda: Guirassy (FC Van) vendido por 54,65 M; à venda desde antes de o bot começar a seguir, vendido até 12/10 09:13") is None
