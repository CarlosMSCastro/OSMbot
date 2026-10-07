from osmbot.game import loop
from osmbot.game.dashboard import render
from osmbot.theory.fitness import tired_starters


def player(id, lineup, fitness, unavailable=0, position=2):
    return {"id": id, "name": f"P{id}", "position": position, "lineup": lineup, "fitness": fitness, "unavailable": unavailable}


def test_only_starters_below_80_count_most_tired_first():
    players = [player(1, 1, 79), player(2, 5, 80), player(3, 11, 60), player(4, 12, 40),  # bench: ignored
               player(5, 0, 30), player(6, 3, 50, unavailable=2)]  # not in the squad / injured: ignored
    assert [p["id"] for p in tired_starters(players)] == [3, 1]


def _snap(tired):
    return {"coins": 1, "ads": {"shop": {"open": False}, "training": {"open": False}},
            "clubs": [{"name": "Club", "ranking": 1, "league": "L", "match": None, "slots": None, "trainings": [], "tired": tired}]}


def test_board_shows_the_tired_starters():
    text = render(_snap(tired_starters([player(3, 2, 71, position=3)])), 0, "ATIVO", [], "Windows", colour=False)
    assert "⚠ P3" in text and "71%" in text and "DEF" in text


def test_log_warns_once_until_the_player_recovers(monkeypatch):
    lines = []
    monkeypatch.setattr(loop, "_log", lines.append)
    tired = [{"id": 3, "name": "P3", "pos": "DEF", "fitness": 71}]
    seen = loop._check_fitness(_snap(tired), set())
    seen = loop._check_fitness(_snap(tired), seen)
    assert len(lines) == 1 and "71%" in lines[0]
    seen = loop._check_fitness(_snap([]), seen)
    loop._check_fitness(_snap(tired), seen)
    assert len(lines) == 2


def test_board_shows_money_stadium_and_sponsors():
    snap = _snap([])
    snap["clubs"][0].update(money=(0, 30_388_270),
                            stadium={"parts": [("campo de treinos", 3, 3, None), ("campo", 1, 3, 9000), ("capacidade", 0, 3, None)], "until": 9000},
                            sponsors={"slots": 3, "revenue": 454_000})
    text = render(snap, 0, "ATIVO", [], "Windows", colour=False)
    assert "poupança 30,39 M" in text and "campo de treinos 3/3 ✓" in text and "campo 1/3 ▶" in text
    assert "3/4 espaços" in text and "454 k/ronda" in text


def test_board_never_taller_than_the_window():
    tired = [{"id": i, "name": f"Jogador {i}", "pos": "MED", "fitness": 70 + i} for i in range(8)]
    snap = _snap(tired)
    snap["clubs"][0].update(trainings=[{"name": f"T{i}", "pos": "ATA", "finish": 9999, "claimed": False} for i in range(4)],
                            money=(1, 2), stadium={"parts": [("campo", 1, 3, None)], "until": None},
                            sponsors={"slots": 4, "revenue": 1})
    snap["clubs"].append(dict(snap["clubs"][0], name="Outro"))
    full = render(snap, 0, "ATIVO", ["a", "b", "c", "d", "e"], "Windows", colour=False)
    assert full.count("\n") + 1 > 26  # taller than a small window
    for rows in (40, 30, 26, 20, 12):
        text = render(snap, 0, "ATIVO", ["a", "b", "c", "d", "e"], "Windows", colour=False, rows=rows)
        assert text.count("\n") + 1 <= rows - 1
