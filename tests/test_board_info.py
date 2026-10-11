from osmbot.board.info import cup_phase, next_match, squad_value, track_sales

ROUNDS = [{"weekNr": 6, "name": "Preliminaries"}, {"weekNr": 14, "name": "Round of 16"},
          {"weekNr": 22, "name": "Quarter-finals"}, {"weekNr": 42, "name": "Final"}]
TEAMS = [{"id": 1, "name": "Nós", "ranking": 2}, {"id": 6, "name": "Getafe", "ranking": 8},
         {"id": 4, "name": "Rival", "ranking": 1}, {"id": 9, "name": "Perto", "ranking": 4}]


def match(week, home, away, kind=0, winner=0):
    return {"weekNr": week, "homeTeamId": home, "awayTeamId": away, "matchType": kind, "winnerTeamId": winner}


def test_next_match_has_the_opponent_its_place_home_or_away():
    matches = [match(14, 1, 19, kind=1, winner=1), match(14, 1, 4, kind=2), match(15, 1, 6), match(16, 4, 1)]
    assert next_match(matches, TEAMS, 1, 14) == {"opponent": "Getafe", "rank": 8, "side": "H", "danger": False, "cup": False}
    assert next_match(matches, TEAMS, 1, 15) == {"opponent": "Rival", "rank": 1, "side": "A", "danger": True, "cup": False}
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
