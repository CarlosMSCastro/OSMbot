from osmbot.game.slots import SlotStatus, count_listed, newly_free


def test_free_slots_never_negative():
    assert SlotStatus("A", 4, 4).free == 0
    assert SlotStatus("A", 1, 4).free == 3
    assert SlotStatus("A", 7, 6).free == 0


def test_count_listed_ignores_other_managers_players():
    players = [{"id": 1}, {"id": 2}, {"id": 3}]
    market = [{"player": {"id": 2}}, {"player": {"id": 99}}, {"player": {"id": 3}}]
    assert count_listed(players, market) == 2


def test_newly_free_reports_first_check_with_free_slots():
    previous = {}
    assert [s.team for s in newly_free([SlotStatus("A", 4, 4), SlotStatus("B", 2, 4)], previous)] == ["B"]
    assert previous == {"A": 0, "B": 2}
