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
    midfielder_higher = make_player(Position.MID, att=99)
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
