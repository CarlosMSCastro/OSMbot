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
    assert state["login"] == {"claimable": True, "day": 15, "renews": 2_000_000_000}
    assert state["missions"] == {"claimed": 3, "total": 3, "day_pending": True}
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
