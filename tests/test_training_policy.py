from osmbot.models import Player, Position
from osmbot.training.policy import pick_trainee, plan_training, round_sessions


def test_picks_best_of_the_position(make_player):
    best = make_player(Position.ATT, age=24, att=80)
    other = make_player(Position.ATT, age=22, att=70)
    assert pick_trainee([other, best], Position.ATT) is best


def test_skips_players_aged_30_or_more(make_player):
    old_star = make_player(Position.DEF, age=30, deff=90)
    young = make_player(Position.DEF, age=27, deff=70)
    assert pick_trainee([old_star, young], Position.DEF) is young


def test_age_limit_is_configurable(make_player):
    p = make_player(Position.DEF, age=31, deff=90)
    assert pick_trainee([p], Position.DEF, max_age=32) is p


def test_skips_injured_and_unavailable(make_player):
    injured = make_player(Position.MID, ovr=90, injured=True)
    busy = make_player(Position.MID, ovr=85)
    free = make_player(Position.MID, ovr=60)
    chosen = pick_trainee(
        [injured, busy, free], Position.MID, unavailable_ids=frozenset({busy.id})
    )
    assert chosen is free


def test_rating_depends_on_position(make_player):
    # A goalkeeper's rating is his defence stat, not his attack.
    gk_a = make_player(Position.GK, att=90, deff=50)
    gk_b = make_player(Position.GK, att=10, deff=70)
    assert pick_trainee([gk_a, gk_b], Position.GK) is gk_b


def test_none_when_nobody_eligible(make_player):
    assert pick_trainee([make_player(Position.ATT, age=35)], Position.ATT) is None
    assert pick_trainee([], Position.GK) is None


def test_forecast_zero_excludes_player_when_forecasts_given(make_player):
    maxed = make_player(Position.ATT, att=95)
    growing = make_player(Position.ATT, att=80)
    forecasts = {maxed.id: 0, growing.id: 40}
    assert pick_trainee([maxed, growing], Position.ATT, forecasts=forecasts) is growing


def test_forecast_breaks_rating_ties(make_player):
    a = make_player(Position.ATT, att=80)
    b = make_player(Position.ATT, att=80)
    forecasts = {a.id: 20, b.id: 35}
    assert pick_trainee([a, b], Position.ATT, forecasts=forecasts) is b


def test_plan_fills_each_free_trainer_once(make_player):
    att = make_player(Position.ATT, att=80)
    mid = make_player(Position.MID, ovr=75)
    dfd = make_player(Position.DEF, deff=70)
    gk = make_player(Position.GK, deff=60)
    plan = plan_training([att, mid, dfd, gk], [1, 2, 3, 4])
    assert plan == {1: att, 2: mid, 3: dfd, 4: gk}


def test_plan_only_touches_free_trainers_and_ignores_universal(make_player):
    att = make_player(Position.ATT, att=80)
    mid = make_player(Position.MID, ovr=75)
    plan = plan_training([att, mid], [2, 5])
    assert plan == {2: mid}


def test_plan_leaves_trainer_empty_when_nobody_fits(make_player):
    plan = plan_training([make_player(Position.ATT, age=33, att=90)], [1])
    assert plan == {}


def test_plan_respects_unavailable_ids(make_player):
    busy = make_player(Position.ATT, att=90)
    other = make_player(Position.ATT, att=70)
    plan = plan_training([busy, other], [1], unavailable_ids=[busy.id])
    assert plan == {1: other}


def test_from_api_maps_reported_fields():
    p = Player.from_api(
        {
            "id": "7",
            "name": "Test",
            "position": 3,
            "age": "28",
            "statAtt": 10,
            "statOvr": 20,
            "statDef": 30,
            "injuryId": 0,
        }
    )
    assert p == Player(7, "Test", Position.DEF, 28, 10, 20, 30, False)
    assert p.rating == 30
    assert Player.from_api({**{"id": 1, "position": 1, "age": 20}, "unavailable": 2}).injured
    # injuryId alone does not mean injured (observed 2026-10-04)
    assert not Player.from_api({"id": 1, "position": 1, "age": 20, "injuryId": 27, "unavailable": 0}).injured


def test_rotation_goes_to_the_starter_with_fewest_sessions_this_round(make_player):
    star = make_player(Position.ATT, att=110, lineup=9)
    second = make_player(Position.ATT, att=104, lineup=10)
    bench = make_player(Position.ATT, att=115, lineup=15)  # better, but on the bench
    squad = [star, second, bench]
    assert pick_trainee(squad, Position.ATT, sessions={}) is star  # nobody trained yet: the best starter
    assert pick_trainee(squad, Position.ATT, sessions={star.id: 1}) is second
    assert pick_trainee(squad, Position.ATT, sessions={star.id: 1, second.id: 1}) is star  # all once: best again
    assert pick_trainee(squad, Position.ATT) is bench  # without counts: the old rule (best of all)


def test_rotation_falls_back_to_the_rest_without_an_eligible_starter(make_player):
    old = make_player(Position.ATT, age=33, att=110, lineup=9)
    bench_a = make_player(Position.ATT, att=100, lineup=15)
    bench_b = make_player(Position.ATT, att=95, lineup=0)
    assert pick_trainee([old, bench_a, bench_b], Position.ATT, sessions={bench_a.id: 1}) is bench_b


def test_rotation_keeps_the_goalkeeper_rule(make_player):
    keeper = make_player(Position.GK, age=34, deff=100, lineup=1)
    spare = make_player(Position.GK, deff=60, lineup=12)
    assert pick_trainee([keeper, spare], Position.GK, sessions={keeper.id: 3}) is keeper  # the only starter keeper


def test_round_sessions_counts_each_session_once():
    ongoing = [{"id": 1, "playerId": 10, "weekNr": 7}, {"id": 2, "playerId": 11, "weekNr": 7},
               {"id": 3, "playerId": 12, "weekNr": 6}]  # started before the last match: another round
    recorded = {"1": 10, "9": 10}  # the bot's own: session 1 is also ongoing, 9 already collected
    assert round_sessions(ongoing, recorded, 7) == {10: 2, 11: 1}


def test_rotation_ties_go_to_the_highest_forecast_then_the_best(make_player):
    star = make_player(Position.GK, deff=115, lineup=1)
    young = make_player(Position.GK, deff=104, lineup=1)  # both starters here only to test the tie
    squad = [star, young]
    assert pick_trainee(squad, Position.GK, sessions={}, forecasts={star.id: 13, young.id: 29}) is young
    assert pick_trainee(squad, Position.GK, sessions={young.id: 1}, forecasts={star.id: 13, young.id: 29}) is star
    assert pick_trainee(squad, Position.GK, sessions={}, forecasts={star.id: 20, young.id: 20}) is star  # same: the best


def test_finishing_a_training_costs_what_the_game_charges_for_the_hours_left_rounded_up():
    from osmbot.training.policy import boost_product

    products = [{"id": 506 + h, "name": "TrainingBoostCost", "value": 2 * h, "increment": h} for h in range(1, 9)]
    products.append({"id": 80, "name": "TrainingBoostCostPerHour", "value": 2, "increment": 0})
    assert boost_product(products, 20 * 60)["value"] == 2  # 20 min = 1 h (the owner: it can be done under 1 h)
    assert boost_product(products, 3 * 3600 + 20 * 60)["value"] == 8  # 3h20 = 4 h
    assert boost_product(products, 8 * 3600)["id"] == 514 and boost_product(products, 9 * 3600)["value"] == 16
    assert boost_product([], 3600) is None


def test_the_trainings_put_before_a_training_event_are_the_ones_to_finish():
    from osmbot.training.policy import pre_event_sessions

    now = 1_000_000.0

    def session(sid, left, trainer=1, claimed=False):
        return {"id": sid, "trainer": trainer, "countdownTimer": {"finishedTimestamp": now + left, "isClaimed": claimed}}

    sessions = [session(1, 5 * 3600),  # an 8 h one with 5 h to go: more than the event's 2 h
                session(2, 90 * 60),  # 1h30 to go: put in the event, or before it (only the bot's memory says)
                session(3, 100 * 60, trainer=5),  # the universal trainer lasts 1h30 in the event: began before it
                session(4, -60), session(5, 4 * 3600, claimed=True)]  # ready to collect / already collected
    assert [s["id"] for s in pre_event_sessions(sessions, now, (120, 90))] == [1, 3]
    assert [s["id"] for s in pre_event_sessions(sessions, now, (120, 90), before={2})] == [1, 2, 3]
