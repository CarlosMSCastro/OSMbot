from osmbot.models import Position
from osmbot.theory.specialists import (
    pick_captain,
    pick_corner_taker,
    pick_free_kick_taker,
    pick_penalty_taker,
    pick_specialists,
)


def test_captain_is_oldest_regardless_of_rating(make_player):
    young_star = make_player(Position.MID, age=22, ovr=95)
    old_average = make_player(Position.DEF, age=34, deff=40)
    assert pick_captain([young_star, old_average]) is old_average


def test_captain_tiebreak_on_age_is_higher_rating(make_player):
    a = make_player(Position.MID, age=30, ovr=60)
    b = make_player(Position.ATT, age=30, att=80)
    assert pick_captain([a, b]) is b


def test_penalty_taker_is_forward_with_most_attack(make_player):
    striker_low = make_player(Position.ATT, att=70)
    striker_high = make_player(Position.ATT, att=85)
    midfielder_higher = make_player(Position.MID, att=94)  # 9 more: not enough for a midfielder (point 18)
    assert pick_penalty_taker([striker_low, striker_high, midfielder_higher]) is striker_high


def test_penalty_taker_none_without_forward(make_player):
    assert pick_penalty_taker([make_player(Position.MID, att=90)]) is None


def test_free_kick_taker_is_anyone_with_most_attack(make_player):
    striker = make_player(Position.ATT, att=80)
    midfielder = make_player(Position.MID, att=88)
    assert pick_free_kick_taker([striker, midfielder]) is midfielder


def test_corner_taker_is_midfielder_with_most_attack(make_player):
    striker = make_player(Position.ATT, att=99)
    mid_low = make_player(Position.MID, att=60)
    mid_high = make_player(Position.MID, att=75)
    assert pick_corner_taker([striker, mid_low, mid_high]) is mid_high


def test_equal_attack_goes_to_the_better_rest_of_the_stats(make_player):
    marmoush = make_player(Position.ATT, att=111, ovr=65, deff=19, id=1)
    trossard = make_player(Position.ATT, att=111, ovr=73, deff=36, id=2)
    assert pick_penalty_taker([marmoush, trossard]) is trossard  # the owner's case (2026-10-14), not the lower id
    assert pick_free_kick_taker([marmoush, trossard]) is trossard


def test_equal_attack_is_broken_by_rating_then_lower_id(make_player):
    a = make_player(Position.MID, att=70, ovr=60, id=5)
    b = make_player(Position.MID, att=70, ovr=60, id=3)
    assert pick_corner_taker([a, b]) is b


def test_empty_squad_gives_no_specialists():
    result = pick_specialists([])
    assert result.captain is None
    assert result.penalty_taker is None
    assert result.free_kick_taker is None
    assert result.corner_taker is None


def test_pick_specialists_accepts_a_generator(make_player):
    squad = [make_player(Position.ATT, age=30, att=80), make_player(Position.MID, att=70)]
    result = pick_specialists(p for p in squad)
    assert result.captain is squad[0]
    assert result.corner_taker is squad[1]


def _graded(player, grade, matches):
    from dataclasses import replace

    return replace(player, average_grade=grade, matches=matches)


def test_corners_leave_the_free_kick_taker_for_the_midfielder_with_the_best_average(make_player):
    star = _graded(make_player(Position.MID, att=99), 8.9, 20)  # free kicks and the most attack among midfielders
    attacking = _graded(make_player(Position.MID, att=90), 8.1, 20)
    steady = _graded(make_player(Position.MID, att=60), 8.6, 20)
    new = _graded(make_player(Position.MID, att=70), 9.5, 2)  # too few matches
    chosen = pick_specialists([star, attacking, steady, new, make_player(Position.ATT, att=80)])
    assert chosen.free_kick_taker is star and chosen.corner_taker is steady


def test_close_averages_go_to_the_more_defensive_midfielder(make_player):
    star = _graded(make_player(Position.MID, att=99), 8.0, 20)
    a = _graded(make_player(Position.MID, att=80, deff=40), 8.5, 10)
    b = _graded(make_player(Position.MID, att=70, deff=75), 8.3, 10)
    assert pick_corner_taker([star, a, b], star) is b


def test_corners_stay_when_they_do_not_collide_or_nobody_else_can_take_them(make_player):
    mid = _graded(make_player(Position.MID, att=80), 8.0, 20)
    other = _graded(make_player(Position.MID, att=70), 9.0, 20)
    forward = make_player(Position.ATT, att=95)
    assert pick_specialists([mid, other, forward]).corner_taker is mid  # the forward takes the free kicks
    assert pick_corner_taker([mid], mid) is mid
    fresh = _graded(make_player(Position.MID, att=60), 0, 1)
    second = _graded(make_player(Position.MID, att=75), 0, 2)
    assert pick_corner_taker([mid, fresh, second], mid) is second  # nobody with 3 matches: the next by attack


def test_a_midfielder_takes_the_penalties_with_10_more_attack_than_the_best_forward(make_player):
    forward = make_player(Position.ATT, att=100)
    assert pick_penalty_taker([forward, make_player(Position.MID, att=109)]) is forward
    mid = make_player(Position.MID, att=110)
    assert pick_penalty_taker([forward, mid]) is mid
    assert pick_penalty_taker([mid]) is None  # no forward: as before
