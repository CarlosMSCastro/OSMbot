from osmbot.board.info import cup_phase, next_match, squad_value, track_sales

ROUNDS = [{"weekNr": 6, "name": "Preliminaries"}, {"weekNr": 14, "name": "Round of 16"},
          {"weekNr": 22, "name": "Quarter-finals"}, {"weekNr": 42, "name": "Final"}]
TEAMS = [{"id": 1, "name": "Nós", "ranking": 2}, {"id": 6, "name": "Getafe", "ranking": 8},
         {"id": 4, "name": "Rival", "ranking": 1}, {"id": 9, "name": "Perto", "ranking": 4}]


def match(week, home, away, kind=0, winner=0):
    return {"weekNr": week, "homeTeamId": home, "awayTeamId": away, "matchType": kind, "winnerTeamId": winner}


def test_next_match_has_the_opponent_its_place_home_or_away():
    matches = [match(14, 1, 19, kind=1, winner=1), match(14, 1, 4, kind=2), match(15, 1, 6), match(16, 4, 1)]
    assert next_match(matches, TEAMS, 1, 14) == {"opponent": "Getafe", "opponent_id": 6, "rank": 8, "side": "H", "danger": False, "cup": False}
    assert next_match(matches, TEAMS, 1, 15) == {"opponent": "Rival", "opponent_id": 4, "rank": 1, "side": "A", "danger": True, "cup": False}
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
    standings = [{"teamId": i, "points": p} for i, p in zip(range(1, 6), (46, 45, 43, 40, 32))]
    ahead = [match(20, 2, 3), match(21, 4, 2)]  # the 2nd still has 2 league matches
    summary = league_summary(standings, teams, ahead, 2, 19, 4)
    assert summary == {"rows": [(1, "Clube 1", 46, False), (2, "Clube 2", 45, True), (3, "Clube 3", 43, False)],
                       "goal": 4, "champion": False}
    assert [r[0] for r in league_summary(standings, teams, ahead, 5, 19, 11)["rows"]] == [1, 2, 5]  # below 3rd
    won = [{"teamId": 1, "points": 52}, {"teamId": 2, "points": 45}]
    assert league_summary(won, teams, ahead, 1, 19, 1)["champion"]  # 45 + 2×3 = 51 < 52
    assert not league_summary([{"teamId": 1, "points": 51}, {"teamId": 2, "points": 45}], teams, ahead, 1, 19, 1)["champion"]
    assert league_summary([], teams, ahead, 1, 19, 1) is None
