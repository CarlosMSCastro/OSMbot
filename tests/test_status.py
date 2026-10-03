from osmbot.game.status import summarize


def test_summarize_skips_empty_slots_and_formats_budget():
    account = {"teamSlots": {
        "0": {"team": {"name": "Clube A", "ranking": 3, "budget": 1234567}, "league": {"name": "L1", "weekNr": 5}},
        "1": None,
        "2": {"team": None},
    }}
    assert summarize(account) == ["[0] Clube A | liga: L1 (semana 5) | ranking: 3 | orcamento: 1.234.567"]


def test_summarize_without_slots():
    assert summarize({}) == []
