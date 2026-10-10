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
