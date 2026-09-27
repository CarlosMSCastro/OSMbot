from osmbot.models import Player, Position
from osmbot.training.policy import pick_trainee, plan_training


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
    assert Player.from_api({**{"id": 1, "position": 1, "age": 20}, "injuryId": 4}).injured
