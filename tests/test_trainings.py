from osmbot.game.trainings import summarize_trainings


def session(name, position, finished, claimed=False):
    return {"player": {"name": name, "position": position},
            "countdownTimer": {"finishedTimestamp": finished, "isClaimed": claimed}}


def test_ready_waiting_and_claimed():
    now = 100_000
    lines = summarize_trainings(
        [session("A", 1, now - 3600), session("B", 4, now + 5400), session("C", 2, now - 10, claimed=True)],
        [{"type": 14, "finishedTimestamp": now + 7200}],
        now,
    )
    assert lines == [
        "  A (ATA): PRONTO (ha 1h00)",
        "  C (MED): ja recolhido",
        "  B (GR): faltam 1h30",
        "  Proximo jogo: em 2h00",
    ]


def test_no_sessions_no_timer():
    assert summarize_trainings([], [], 0) == []


from osmbot.game.trainings import plan_new_trainings, ready_sessions


def api_player(pid, position, ovr=50, att=50, defe=50, age=25, unavailable=0):
    return {"id": pid, "position": position, "age": age, "statAtt": att, "statOvr": ovr, "statDef": defe,
            "unavailable": unavailable, "injuryId": 0}


def test_ready_sessions_skips_running_and_claimed():
    now = 1000
    sessions = [session("A", 1, now - 5), session("B", 1, now + 5), session("C", 1, now - 5, claimed=True)]
    assert [s["player"]["name"] for s in ready_sessions(sessions, now)] == ["A"]


def test_plan_fills_free_slots_only_and_skips_listed_busy_old_injured():
    players = [
        api_player(1, 1, att=90, age=31),            # best ATT but 30+
        api_player(2, 1, att=80),                     # ATT: picked
        api_player(3, 2, ovr=99, unavailable=2),      # best MID injured
        api_player(4, 2, ovr=70),                     # MID: picked
        api_player(5, 3, defe=95),                    # DEF slot is busy
        api_player(6, 4, defe=90),                    # GK listed for sale
        api_player(7, 4, defe=60),                    # GK: picked
    ]
    sessions = [{"trainer": 3, "playerId": 5}]
    plan = plan_new_trainings(players, sessions, listed_ids={6})
    assert {t: p.id for t, p in plan.items()} == {1: 2, 2: 4, 4: 7}


def test_goalkeeper_trains_regardless_of_age():
    players = [api_player(1, 4, defe=90, age=34), api_player(2, 4, defe=50, age=22)]
    assert plan_new_trainings(players, [], set())[4].id == 1


def test_outfield_age_limit_still_applies():
    players = [api_player(1, 1, att=90, age=30), api_player(2, 1, att=50, age=22)]
    assert plan_new_trainings(players, [], set())[1].id == 2
