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
        "  A (ATA): pronto (há 1h00)",
        "  C (MED): recolhido",
        "  B (GR): faltam 1h30",
        "  Próximo jogo: em 2h00",
    ]


def test_no_sessions_no_timer():
    assert summarize_trainings([], [], 0) == []


from osmbot.game.trainings import plan_new_trainings, ready_sessions


def api_player(pid, position, ovr=50, att=50, defe=50, age=25, unavailable=0, lineup=0):
    return {"id": pid, "position": position, "age": age, "statAtt": att, "statOvr": ovr, "statDef": defe,
            "unavailable": unavailable, "injuryId": 0, "lineup": lineup}


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


def test_plan_rotates_among_starters_with_the_round_counts():
    players = [api_player(1, 1, att=110, lineup=9), api_player(2, 1, att=100, lineup=10), api_player(3, 1, att=120, lineup=16)]
    assert plan_new_trainings(players, [], set(), {1: 2, 2: 1})[1].id == 2
    assert plan_new_trainings(players, [], set())[1].id == 3  # no counts: the best player, as before


def test_the_round_record_starts_again_with_a_new_round():
    from osmbot.game.trainings import _record, _recorded

    _record("b", 7, 501, 10)
    _record("b", 7, 502, 11)
    assert _recorded("b", 7) == {"501": 10, "502": 11}
    _record("b", 8, 503, 10)
    assert _recorded("b", 7) == {} and _recorded("b", 8) == {"503": 10}


def test_run_train_starts_several_sessions_and_records_them(monkeypatch):
    """Regression (0.11.0): the round counts reused the name of the int counter, so the first success crashed."""
    import osmbot.game.client as client_module
    from osmbot.game import trainings

    base = "leagues/1/teams/2"
    players = [dict(api_player(1, 1, att=90), name="A"), dict(api_player(2, 2, ovr=90), name="B")]
    replies = {
        "user/accounts": {"teamSlots": {"1": {"team": {"id": 2, "leagueId": 1, "name": "T"}}}},
        f"{base}/trainingsessions/ongoing": [], f"{base}/players": players, f"{base}/transferplayers/0": [],
        "leagues/1/gamesettings": [{"id": 9, "name": trainings.TRAINING_SETTING_NAME}],
        "leagues/1": {"weekNr": 7}, f"{base}/trainingforecasts": [],
    }
    posted = []

    class FakeClient:
        def get(self, path):
            return 200, replies[path]

        def post(self, path, body):
            posted.append(body["playerId"])
            return 200, {"id": 500 + len(posted)}

    monkeypatch.setattr(client_module, "OsmClient", FakeClient)
    monkeypatch.setattr(trainings, "PAUSE_BETWEEN_WRITES", 0)
    assert trainings.run_train(confirm=True) == 0
    assert sorted(posted) == [1, 2]
    assert trainings._recorded(base, 7) == {"501": posted[0], "502": posted[1]}
