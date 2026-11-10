from osmbot.game import clubinfo


def test_forget_drops_the_kept_reads():
    reads = []
    clubinfo.forget()
    assert clubinfo._cached(("x",), 3600, lambda: reads.append(1) or 1) == 1
    clubinfo._cached(("x",), 3600, lambda: reads.append(1) or 1)
    assert reads == [1]  # kept
    clubinfo.forget()
    clubinfo._cached(("x",), 3600, lambda: reads.append(1) or 1)
    assert reads == [1, 1]  # read again after Ver -> Atualizar


def test_secret_training_only_when_the_game_says_so():
    off = lambda text: {"type": 5, "enabled": False, "disabledText": text}
    assert clubinfo.secret_training(off("The opponent is on a secret training"))
    assert not clubinfo.secret_training(off("You don't have a match scheduled this matchday."))  # pre-season day
    assert not clubinfo.secret_training({"type": 5, "enabled": True})
    assert not clubinfo.secret_training(None)


def test_the_note_of_what_he_played_against_us():  # D-100
    from osmbot.game.clubinfo import vs_us_note
    assert vs_us_note({"formation": 523, "detail": "A", "camp": True, "week": 24, "type": "liga"}) == \
        "Contra nós jogou 5-2-3 com estágio (liga, semana 24)"
    assert vs_us_note({"formation": 433, "detail": "B", "camp": False, "week": 3, "type": "taça"}) == \
        "Contra nós jogou 4-3-3 B (taça, semana 3)"
    assert vs_us_note(None) is None
