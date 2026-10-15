import json

import pytest

from osmbot.game import rewards
from osmbot.rewards.policy import day_key, has_room, is_daily, mission_summary, next_claim, today_index, wallet_path

CATALOGUE = [
    {"id": 287, "threshold": 1}, {"id": 326, "threshold": 2}, {"id": 333, "threshold": 3},
    {"id": 298, "threshold": 3, "actionId": "DailyMissionsRewardUT_48H"},
    {"id": 305, "threshold": 3, "actionId": "DailyMissionsRewardBC_10"},
]


START = 1_000_000.0
END = START + 7 * 86400  # the week's end
DAY3 = START + 2 * 86400 + 100  # during the third day
DAY4 = START + 3 * 86400 + 100


def mission(id, mission_id, progress, order=None, claimed=False, source=3):
    base = {"id": id, "missionId": mission_id, "progress": progress, "isClaimed": claimed, "sourceType": source, "endDateTime": END}
    return {**base, "order": order} if order else base


def week(claimed=()):
    return [
        mission(10, 287, 1, order=1, claimed=10 in claimed), mission(11, 326, 2, order=2, claimed=11 in claimed),
        mission(12, 333, 3, order=3, claimed=12 in claimed),
        mission(20, 298, 0, source=3), mission(21, 305, 0, source=4),
    ]


# --- policy (pure) ---

def test_dailies_are_claimed_in_order_once_their_goal_is_reached():
    assert next_claim(week(), CATALOGUE)["id"] == 10
    assert next_claim(week(claimed={10}), CATALOGUE)["id"] == 11
    unfinished = week()
    unfinished[1]["progress"] = 1  # goal is 2
    unfinished[2]["progress"] = 1  # goal is 3
    assert next_claim(unfinished, CATALOGUE)["id"] == 10
    unfinished[0]["isClaimed"] = True
    assert next_claim(unfinished, CATALOGUE) is None  # the others are not done and the day reward stays shut


def test_the_week_has_seven_days_and_today_is_known_from_its_end():
    open_ = week()
    assert today_index(open_, START + 10) == 1 and today_index(open_, DAY3) == 3 and today_index(open_, END - 10) == 7
    assert today_index([{"id": 1}], DAY3) is None


def test_the_day_reward_opens_after_all_three_and_is_todays():
    claim = next_claim(week(claimed={10, 11, 12}), CATALOGUE, now=DAY3)
    assert claim["id"] == 20 and not is_daily(claim)
    assert next_claim(week(claimed={10, 11}), CATALOGUE, now=DAY3)["id"] == 12  # still a daily first
    assert next_claim(week(claimed={10, 11, 12}), CATALOGUE, now=DAY4)["id"] == 21  # day 4: the day-4 reward


def test_tomorrows_reward_is_never_taken_today_even_after_a_restart():
    after_day3 = [m for m in week(claimed={10, 11, 12}) if m["id"] != 20]  # today's reward already claimed and gone
    assert next_claim(after_day3, CATALOGUE, now=DAY3) is None  # the day-4 reward is listed but is not today's


def test_only_one_day_reward_per_day_so_the_next_days_stay_shut():
    today = week(claimed={10, 11, 12})
    assert next_claim(today, CATALOGUE, now=DAY3)["id"] == 20
    assert next_claim(today, CATALOGUE, day_done={day_key(today)}, now=DAY3) is None  # asked for already (accepted or refused)
    tomorrow = [mission(30, 287, 1, order=1, claimed=True), mission(31, 326, 2, order=2, claimed=True),
                mission(32, 333, 3, order=3, claimed=True), mission(21, 305, 0, source=4)]
    assert next_claim(tomorrow, CATALOGUE, day_done={day_key(today)}, now=DAY4)["id"] == 21  # a new day, a new reward


def test_unknown_goal_is_never_claimed_and_no_dailies_means_no_day_reward():
    odd = [mission(10, 999, 5, order=1)]
    assert next_claim(odd, CATALOGUE) is None
    assert next_claim([mission(20, 298, 0)], CATALOGUE) is None


def test_mission_summary_for_the_board():
    assert mission_summary(week(), CATALOGUE) == {"claimed": 0, "total": 3, "day_pending": False}
    assert mission_summary(week(claimed={10, 11, 12}), CATALOGUE, now=DAY3) == {"claimed": 3, "total": 3, "day_pending": True}


def test_inventory_limits_are_respected():
    action_rewards = [{"actionId": "A", "rewardId": 5, "amount": 1}]
    rewards_catalogue = [{"id": 5, "inventoryLimit": 2}]
    item = {"reward": {"id": 5}}
    assert has_room("A", action_rewards, rewards_catalogue, [item])
    assert not has_room("A", action_rewards, rewards_catalogue, [item, item])
    assert has_room("Unknown", action_rewards, rewards_catalogue, [item, item])  # the game itself refuses what it cannot take


def test_login_rewards_have_a_wallet_only_when_the_site_spends_them():
    assert wallet_path("DailyLoginEnergy_1") == "user/wallets/energy/consumereward"
    assert wallet_path("DailyLoginBossCoin_5") == "user/bosscoinwallet/consumereward"
    assert wallet_path("DailyLoginStreakBag_TestB_ExpUser") is None


# --- the game side, with a fake client ---

class FakeGame:
    def __init__(self, login_action="DailyLoginEnergy_1", claimed=(), inventory=(), counter=(10, 10), cap_open=True,
                 wallet=100, reject=()):
        self.login_action, self.claimed, self.reject = login_action, set(claimed), set(reject)
        self.inventory, self.wallet = list(inventory), wallet
        self.login_open, self.counter, self.cap_open = True, counter, cap_open
        self.calls = []

    # reads
    def get(self, path):
        if path == "user/dailylogin":
            return 200, {"isClaimable": self.login_open, "consecutiveLoginCount": 15,
                         "countdownTimer": {"finishedTimestamp": 2_000_000_000},
                         "rewardTrackDays": [{"dayNumber": 16, "actionId": self.login_action, "isClaimable": self.login_open}]}
        if path == "user/userrewards":
            return 200, list(self.inventory)
        if path == "user/bosscoinwallet":
            return 200, {"amount": self.wallet}
        if path == "missions":
            return 200, CATALOGUE
        if path.endswith("actionrewards"):
            return 200, [{"actionId": "DailyMissionsRewardUT_48H", "rewardId": 1317, "amount": 1},
                         {"actionId": rewards.VIDEO_COUNTER_ACTION, "rewardId": 1110, "amount": 1}]
        if path.endswith("/rewards"):
            return 200, [{"id": 1317, "inventoryLimit": 10}, {"id": 1110, "inventoryLimit": 10}]
        if path.startswith("user/caps/actions/"):
            return 200, {"isClaimable": self.cap_open, "isCapReached": True, "timestampUntilUnreached": 0}
        if path.startswith("user/caps/counters/"):
            return 200, {"currentCount": self.counter[0], "threshold": self.counter[1]}
        raise AssertionError(path)

    # writes
    def request(self, method, path, form=None):
        self.calls.append((method, path))
        if path == "usermissions/weeklytrack":
            return 200, [dict(m, isClaimed=m["id"] in self.claimed) for m in week()]
        if path.startswith("user/actions/"):
            self.inventory.append({"id": "video-item", "reward": {"id": 1110, "value": 1}, "action": {"id": rewards.VIDEO_COUNTER_ACTION}})
            return 200, []
        raise AssertionError(path)

    def put(self, path):
        self.calls.append(("PUT", path))
        if path in self.reject:
            return 400, "no"
        if path == "user/dailylogin/claim":
            self.login_open = False
            self.inventory.append({"id": "new-1", "reward": {"id": 1408, "value": 5}, "action": {"id": self.login_action}})
        elif path.startswith("usermissions/"):
            self.claimed.add(int(path.split("/")[1]))
        return 200, {}

    def post(self, path, form):
        self.calls.append(("POST", path, form))
        if "bosscoin" in path:
            self.wallet += 5
        return 200, {}


@pytest.fixture(autouse=True)
def _quick(monkeypatch):
    monkeypatch.setattr(rewards.time, "sleep", lambda seconds: None)
    rewards._missions_read[:] = [0.0, None]
    rewards._unspent.clear()


def test_login_energy_is_claimed_and_spent_like_the_site_does():
    game, said = FakeGame(), []
    assert rewards.claim_login(game, True, said.append) == 0
    assert ("PUT", "user/dailylogin/claim") in game.calls
    assert ("POST", "user/wallets/energy/consumereward", {"rewardId": "new-1"}) in game.calls
    assert rewards.COUNTS["login"] == 1 and "gasto" in said[0]


def test_login_boss_coins_are_spent_into_the_boss_coin_wallet_and_checked():
    game, said = FakeGame(login_action="DailyLoginBossCoin_5"), []
    assert rewards.claim_login(game, True, said.append) == 0
    assert ("POST", "user/bosscoinwallet/consumereward", {"rewardId": "new-1"}) in game.calls and game.wallet == 105


def test_a_login_reward_without_a_wallet_stays_in_the_inventory():
    game, said = FakeGame(login_action="DailyLoginStreakBag_TestB_ExpUser"), []
    assert rewards.claim_login(game, True, said.append) == 0
    assert not [c for c in game.calls if c[0] == "POST"] and "inventário" in said[0]


def test_login_does_nothing_when_not_claimable_or_when_only_simulating():
    closed = FakeGame()
    closed.login_open = False
    assert rewards.claim_login(closed, True, print) == 0 and not closed.calls
    sim, said = FakeGame(), []
    assert rewards.claim_login(sim, False, said.append) == 0
    assert not sim.calls and "Simulação" in said[0]


def test_missions_are_claimed_in_order_and_the_day_reward_is_kept_not_used():
    game, said = FakeGame(), []
    assert rewards.claim_missions(game, True, said.append, clock=lambda: DAY3) == 0
    puts = [c[1] for c in game.calls if c[0] == "PUT"]
    assert puts == ["usermissions/10/claim", "usermissions/11/claim", "usermissions/12/claim", "usermissions/20/claim"]
    assert not [c for c in game.calls if "consume" in c[1] or "actions/" in c[1]]  # nothing is ever spent or used
    assert rewards.COUNTS["missions"] == 4 and "guardado no inventário" in said[-1]
    assert rewards.claim_missions(game, True, said.append, clock=lambda: DAY3) == 0 and len([c for c in game.calls if c[0] == "PUT"]) == 4  # nothing more today


def test_a_refused_day_reward_is_not_asked_again_nor_replaced_by_another_days():
    game, said = FakeGame(claimed={10, 11, 12}, reject={"usermissions/20/claim"}), []
    rewards.claim_missions(game, True, said.append, clock=lambda: DAY3)
    rewards.claim_missions(game, True, said.append, clock=lambda: DAY3)
    assert [c for c in game.calls if c[0] == "PUT"] == [("PUT", "usermissions/20/claim")]
    assert any("recusou" in line for line in said)


def test_the_day_reward_is_not_claimed_when_the_inventory_is_full():
    full = [{"reward": {"id": 1317}, "id": str(i), "action": {"id": "x"}} for i in range(10)]
    game, said = FakeGame(claimed={10, 11, 12}, inventory=full), []
    rewards.claim_missions(game, True, said.append, clock=lambda: DAY3)
    rewards.claim_missions(game, True, said.append, clock=lambda: DAY3)
    assert not [c for c in game.calls if c[0] == "PUT"]
    assert len(said) == 1 and "inventário cheio" in said[0]  # said once, not every pass


def test_missions_only_simulated_write_nothing():
    game, said = FakeGame(), []
    rewards.claim_missions(game, False, said.append, clock=lambda: DAY3)
    assert not [c for c in game.calls if c[0] == "PUT"] and "Simulação" in said[0]


def test_the_accumulated_videos_reward_goes_to_the_inventory_only_at_the_threshold():
    game, said = FakeGame(), []
    assert rewards.claim_video_reward(game, True, said.append) == 0
    assert ("POST", "user/actions/RewardedVideoCounterPositionModifier") in game.calls and rewards.COUNTS["videos"] == 1
    early = FakeGame(counter=(7, 10))
    rewards.claim_video_reward(early, True, print)
    assert not early.calls or all(c[0] != "POST" for c in early.calls)
    shut = FakeGame(cap_open=False)
    rewards.claim_video_reward(shut, True, print)
    assert not [c for c in shut.calls if c[0] == "POST"]


def test_daily_state_for_the_board():
    state = rewards.daily_state(FakeGame(claimed={10, 11, 12}, counter=(7, 10), cap_open=False), clock=lambda: DAY3)
    assert state["login"] == {"claimable": True, "day": 15, "renews": 2_000_000_000, "today": {"action": "DailyLoginEnergy_1"},
                              "tomorrow": {"action": "DailyLoginEnergy_1"}}
    missions = state["missions"]
    assert {k: missions[k] for k in ("claimed", "total", "day_pending")} == {"claimed": 3, "total": 3, "day_pending": True}
    assert [d["claimed"] for d in missions["dailies"]] == [True, True, True] and missions["today"] == 3
    assert [d["day"] for d in missions["week"]] == [3, 4]  # today's day reward first, never the days gone by
    assert state["videos"]["count"] == 7 and not state["videos"]["claimable"]


def test_the_board_reuses_a_recent_missions_read_but_claims_always_read_anew():
    game = FakeGame(claimed={10, 11, 12, 20})
    now = {"t": DAY3}
    rewards.daily_state(game, clock=lambda: now["t"])
    rewards.daily_state(game, clock=lambda: now["t"] + 60)
    assert game.calls.count(("POST", "usermissions/weeklytrack")) == 1
    rewards.claim_missions(game, True, print, clock=lambda: now["t"] + 60)
    assert game.calls.count(("POST", "usermissions/weeklytrack")) == 2


def test_a_login_reward_that_could_not_be_spent_is_tried_again_on_the_next_pass():
    game, said = FakeGame(), []

    def refuse_once(path, form, original=game.post):
        if not said or "falha" not in said[-1]:
            game.calls.append(("POST", path, form))
            said.append("falha simulada")
            return 500, {}
        return original(path, form)

    game.post = refuse_once
    assert rewards.claim_login(game, True, said.append) == 1
    assert rewards._unspent == {"new-1": "DailyLoginEnergy_1"}
    assert rewards.claim_login(game, True, said.append) == 0  # login already claimed: only the leftover is spent
    assert rewards._unspent == {} and "gasto" in said[-1]


def test_the_video_counter_has_no_reopen_time_while_its_cap_is_not_reached():
    class Open(FakeGame):
        def get(self, path):
            if path.startswith("user/caps/actions/"):
                return 200, {"isClaimable": True, "isCapReached": False, "timestampUntilUnreached": 2_000_000_000}
            return super().get(path)

    assert rewards.daily_state(Open(counter=(3, 10)), clock=lambda: DAY3)["videos"]["reopen"] is None


def test_prize_and_mission_texts_for_the_board_hover():
    from osmbot.rewards.policy import prize_index
    from osmbot.rewards.texts import amount, mission_text, prize_text

    prizes = prize_index([{"actionId": "DailyMissionsRewardCF_3M", "rewardId": 1}, {"actionId": "DailyLoginBossCoin_5", "rewardId": 2}],
                         [{"id": 1, "type": 8, "value": 3_000_000}, {"id": 2, "type": 1, "value": 5}])
    assert prize_text(prizes["DailyMissionsRewardCF_3M"]) == "pacote de 3 M de fundos"
    assert prize_text(prizes["DailyLoginBossCoin_5"], "en") == "5 boss coins"
    assert prize_text({"action": "DailyMissionsRewardUT_48H"}) == "UT_48H" and prize_text(None) == "—"
    assert mission_text("Buy�any Defender rated 85+") == "Comprar um defesa com rating 85+"
    assert mission_text("Buy any player via the Scout") == "Comprar um jogador pelo olheiro"
    assert mission_text("Buy any Goalkeeper for 10M+") == "Comprar um guarda-redes por 10 M+"
    assert mission_text("Train any GK") == "Treinar um GR" and mission_text("Start training any CDM") == "Pôr a treinar um CDM"
    assert mission_text("Spend Club Funds") == "Gastar fundos do clube"
    assert mission_text(" Buy any player for 5M+", "en") == "Buy any player for 5M+"
    assert mission_text("Something new") == "Something new"
    assert amount(111_824_555, 5_000_000) == "5 M/5 M" and amount(1, 2) == "1/2"


def test_today_s_login_prize_after_it_was_claimed():
    from osmbot.rewards.policy import login_today

    prizes = {"DailyLoginBossCoin_5": {"type": 1, "value": 5, "action": "DailyLoginBossCoin_5"}}
    later = [{"actionId": "DailyLoginEnergy_1", "isClaimable": False}]  # once claimed, only the coming days
    assert login_today([{"actionId": "DailyLoginBossCoin_5", "isClaimable": True}], None, [], 0, prizes, "2026-10-12")["value"] == 5
    assert login_today(later, {"day": "2026-10-12", "action": "DailyLoginBossCoin_5"}, [], 0, prizes, "2026-10-12")["type"] == 1
    assert login_today(later, {"day": "2026-10-11", "action": "DailyLoginBossCoin_5"}, [], 0, prizes, "2026-10-12") is None
    bag = [{"action": {"id": "DailyLoginStreakBag_X"}, "creationTimestamp": 500}, {"action": {"id": "Other"}, "creationTimestamp": 900}]
    assert login_today(later, None, bag, 400, prizes, "2026-10-12") == {"action": "DailyLoginStreakBag_X"}
    assert login_today(later, None, bag, 600, prizes, "2026-10-12") is None  # yesterday's bag


def test_claiming_the_login_notes_today_s_prize_for_the_board():
    rewards.claim_login(FakeGame(), True, print)
    assert json.loads(rewards.LOGIN_FILE.read_text(encoding="utf-8"))["action"] == "DailyLoginEnergy_1"


def test_today_s_login_prize_from_an_earlier_read_and_tomorrow_s():
    from osmbot.rewards.policy import login_today, login_tomorrow, track_seen

    prizes = {"DailyLoginBossCoin_5": {"type": 1, "value": 5, "action": "DailyLoginBossCoin_5"}}
    yesterday = [{"dayNumber": 23, "actionId": "DailyLoginEnergy_1"}, {"dayNumber": 24, "actionId": "DailyLoginBossCoin_5"}]
    seen = track_seen(yesterday, None, 23)
    later = [{"dayNumber": 25, "actionId": "DailyLoginEnergy_1"}]  # claimed on another PC: only the coming days
    seen = track_seen(later, seen, 24)
    assert seen == {"24": "DailyLoginBossCoin_5", "25": "DailyLoginEnergy_1"}  # day 23 is gone
    assert login_today(later, None, [], 0, prizes, "2026-10-15", seen, 24)["value"] == 5
    assert login_today(later, None, [], 0, prizes, "2026-10-15", {}, 24) is None
    assert login_tomorrow(later, 24, prizes) == {"action": "DailyLoginEnergy_1"} and login_tomorrow(later, 25, prizes) is None


def test_money_in_the_inventory_goes_to_the_wallets_the_other_items_stay():
    from osmbot.rewards.policy import money_items, poorest

    inventory = [{"id": "a", "action": {"id": "DailyMissionsRewardBC_5"}, "reward": {"type": 1, "value": 5}},
                 {"id": "b", "action": {"id": "DailyMissionsRewardCF_3M"}, "reward": {"type": 8, "value": 3_000_000}},
                 {"id": "c", "action": {"id": "DailyMissionsRewardTP_Boost100"}, "reward": {"type": 9, "value": 100}},
                 {"id": "d", "action": {"id": "RewardedVideoCounterPositionModifier"}, "reward": {"type": 7, "value": 1}}]
    assert [i["id"] for i in money_items(inventory)] == ["a", "b"]
    assert poorest({"L1/T1": (10, 500), "L2/T2": (300, 0)}) == "L2/T2" and poorest({}) is None

    class Client:
        def __init__(self):
            self.posts = []

        def get(self, path):
            if path == "user/userrewards":
                return 200, inventory
            if path == "user/accounts":
                return 200, {"teamSlots": {"0": {"team": {"id": 1, "leagueId": 7, "name": "Rico"}},
                                           "1": {"team": {"id": 2, "leagueId": 8, "name": "Pobre"}}}}
            return 200, {"balance": 0, "savings": 900} if path.startswith("leagues/7/") else {"balance": 5, "savings": 0}

        def post(self, path, form):
            self.posts.append((path, form))
            return 200, {}

    client, lines = Client(), []
    assert rewards.claim_money(client, True, lines.append) == 0
    assert client.posts == [("user/bosscoinwallet/consumereward", {"rewardId": "a"}),
                            ("leagues/8/teams/2/finances/consumereward", {"rewardId": "b"})]
    assert lines == ["Inventário: 5 boss coins (DailyMissionsRewardBC_5) na carteira",
                     "Inventário: 3 M para o Pobre (DailyMissionsRewardCF_3M) na carteira"]
    simulated = Client()
    assert rewards.claim_money(simulated, False, lines.append) == 0 and simulated.posts == []
