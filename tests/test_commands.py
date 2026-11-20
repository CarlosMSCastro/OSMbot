from osmbot.notify.commands import STALE, Commander, addressed, parse, pc_name, stale_offset

NOW = 10_000.0
CHAT = 42


def msg(uid, text, chat=CHAT, age=5, kind="private"):
    return {"update_id": uid, "message": {"chat": {"id": chat, "type": kind}, "date": NOW - age, "text": text}}


def test_only_the_owners_chat_is_read():
    updates = [msg(1, "/parar PT-LA", chat=99), msg(2, "/parar PT-LA", kind="group"), msg(3, "/parar PT-LA")]
    assert [c.update_id for c in parse(updates, CHAT, NOW)] == [3]


def test_commands_old_or_before_this_run_are_ignored():
    updates = [msg(1, "/parar PT-LA", age=STALE + 1), msg(2, "/parar PT-LA", age=60), msg(3, "/estado", age=2)]
    assert [c.update_id for c in parse(updates, CHAT, NOW)] == [2, 3]
    assert [c.update_id for c in parse(updates, CHAT, NOW, since=NOW - 10)] == [3]  # 2 came before the PC opened


def test_the_command_forms():
    got = parse([msg(1, "/parar@meubot PT-LA-02"), msg(2, "/ESTADO"), msg(3, "/parar"), msg(4, "olá"), msg(5, "/start")], CHAT, NOW)
    assert [(c.kind, c.target) for c in got] == [("stop", "PT-LA-02"), ("status", ""), ("stop", "")]


def test_a_pc_answers_only_to_its_own_name():
    assert addressed("pt-la", "PT-LA-02-0095-N") and addressed("0095", "PT-LA-02-0095-N")
    assert not addressed("desktop", "PT-LA-02-0095-N") and not addressed("pt", "PT-LA-02-0095-N")  # too short
    assert not addressed("", "PT-LA-02-0095-N")


def test_only_the_old_updates_are_marked_as_read():
    updates = [msg(1, "x", age=STALE + 5), msg(2, "/parar PT-LA", age=3), msg(3, "y", age=STALE + 1)]
    assert stale_offset(updates, NOW) == 3
    assert stale_offset([msg(2, "/parar PT-LA", age=3)], NOW) is None


def make(updates, machine="PT-LA-02-0095-N", uptime=3725.0, config=None):
    out = {"sent": [], "acks": [], "stops": 0}
    config = {"token": "t", "chat_id": CHAT} if config is None else config
    commander = Commander(lambda: config, lambda token: updates, lambda token, n: out["acks"].append(n),
                          lambda token, chat, text: out["sent"].append(text), machine, lambda: uptime,
                          lambda: out.__setitem__("stops", out["stops"] + 1), now=lambda: NOW)
    return commander, out


def test_stop_for_this_pc_closes_it_once():
    commander, out = make([msg(1, "/parar pt-la")])
    commander.poll_once()
    commander.poll_once()  # the same update, still unread on Telegram: not twice
    assert out["stops"] == 1 and len(out["sent"]) == 1 and "a fechar" in out["sent"][0]
    assert out["acks"] == []  # fresh: left for the other PCs to see


def test_stop_for_another_pc_is_left_alone():
    commander, out = make([msg(1, "/parar desktop-kam")])
    commander.poll_once()
    assert out["stops"] == 0 and out["sent"] == []


def test_stop_without_a_name_does_nothing_but_ask():
    commander, out = make([msg(1, "/parar")])
    commander.poll_once()
    assert out["stops"] == 0 and out["sent"] == ["Diz qual o PC: /parar PT-LA-02-0095-N"]


def test_status_says_the_pc_and_how_long():
    commander, out = make([msg(1, "/estado")])
    commander.poll_once()
    assert out["sent"][0].startswith("💻 PT-LA-02-0095-N: a trabalhar há 1 h 02 min")
    commander2, out2 = make([msg(1, "/estado")], uptime=None)
    commander2.poll_once()
    assert "parado" in out2["sent"][0]


def test_nothing_without_telegram_set_up():
    commander, out = make([msg(1, "/parar pt-la")], config={})
    commander.poll_once()
    assert out == {"sent": [], "acks": [], "stops": 0}


def test_old_updates_are_marked_as_read():
    commander, out = make([msg(1, "/parar pt-la", age=STALE + 10)])
    commander.poll_once()
    assert out["stops"] == 0 and out["acks"] == [1]


def test_the_pcs_own_name_is_the_one_the_owner_gave_it():
    assert pc_name("PCTrabalho") == "PCTrabalho" and pc_name(" PC Casa ") == "PCCasa"
    assert pc_name("", "PT-LA-02-0095-N") == "PT-LA-02-0095-N"  # none given: the network name
    assert addressed("pctrabalho", "PCTrabalho") and not addressed("pctrabalho", "PCCasa")
