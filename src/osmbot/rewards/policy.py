"""Daily rewards: what to claim and what never to touch (THEORY.md section 17). Pure: no network, no I/O."""
from __future__ import annotations

VIDEO_COUNTER_ACTION = "RewardedVideoCounterPositionModifier"
# What the site itself does right after the login claim: spend the reward into its wallet.
# Prefix of the reward's action id -> path of the "consumereward" request (form: rewardId).
LOGIN_WALLETS = {
    "DailyLoginEnergy": "user/wallets/energy/consumereward",
    "DailyLoginBossCoin": "user/bosscoinwallet/consumereward",
}


def wallet_path(action_id: str) -> str | None:
    """The wallet request that spends a login reward, or None (e.g. the day-21 bag): it stays in the inventory."""
    return next((path for prefix, path in LOGIN_WALLETS.items() if action_id.startswith(prefix)), None)


def is_daily(mission: dict) -> bool:
    """The three daily missions carry an ``order``; the others are the week's day rewards."""
    return "order" in mission


def thresholds(catalogue: list[dict]) -> dict[int, int]:
    return {m["id"]: m["threshold"] for m in catalogue if "threshold" in m}


def day_key(user_missions: list[dict]) -> frozenset:
    """Identifies "today": the ids of the three daily missions (they are new every day)."""
    return frozenset(m["id"] for m in user_missions if is_daily(m))


WEEK_SECONDS = 7 * 86400


def today_index(user_missions: list[dict], now: float) -> int | None:
    """Which day (1 to 7) of the week's reward track it is. The week ends at ``endDateTime`` and has 7 days of
    24h (they change at 04:00 UTC); checked on 2026-10-07, when day 3 was the one on screen. None if unknown."""
    ends = [m["endDateTime"] for m in user_missions if "endDateTime" in m]
    if not ends:
        return None
    start = max(ends) - WEEK_SECONDS
    return min(7, max(1, int((now - start) // 86400) + 1))


def next_claim(user_missions: list[dict], catalogue: list[dict], refused: set[int] | frozenset = frozenset(),
               day_done: set | frozenset = frozenset(), now: float = 0.0) -> dict | None:
    """The next mission to claim, or None.

    1. A daily mission whose progress reached its threshold (lowest ``order`` first).
    2. Once every daily mission is claimed, TODAY's day reward: the open mission without ``order`` whose
       ``sourceType`` is today's day of the week (the game opens it after the three; its own progress is not
       what unlocks it). The later days' rewards are also in the list but are not today's: never touched.
    A mission the game already refused (``refused``) is skipped. At most ONE day reward per day: once one was
    asked for (``day_done`` holds the days), the list still shows the later days' rewards, which stay shut."""
    goal = thresholds(catalogue)
    dailies = sorted((m for m in user_missions if is_daily(m)), key=lambda m: m["order"])
    for mission in dailies:
        if not mission["isClaimed"] and mission["id"] not in refused:
            needed = goal.get(mission["missionId"])
            if needed is not None and mission["progress"] >= needed:
                return mission
    if dailies and all(m["isClaimed"] for m in dailies) and day_key(user_missions) not in day_done:
        today = today_index(user_missions, now)
        open_rewards = [m for m in user_missions if not is_daily(m) and not m["isClaimed"] and m["id"] not in refused
                        and m["sourceType"] == today]
        if open_rewards:
            return min(open_rewards, key=lambda m: m["id"])
    return None


def mission_summary(user_missions: list[dict], catalogue: list[dict], refused: set[int] | frozenset = frozenset(),
                    day_done: set | frozenset = frozenset(), now: float = 0.0) -> dict:
    """For the board: {"claimed", "total", "day_pending"} (day_pending: the day reward can be claimed now)."""
    dailies = [m for m in user_missions if is_daily(m)]
    claim = next_claim(user_missions, catalogue, refused, day_done, now)
    return {"claimed": sum(m["isClaimed"] for m in dailies), "total": len(dailies),
            "day_pending": bool(claim) and not is_daily(claim)}


def has_room(action_id: str, action_rewards: list[dict], rewards: list[dict], inventory: list[dict]) -> bool:
    """False if the reward(s) of this action would take an inventory item above the game's own limit.
    An action the catalogues do not list is allowed: the game itself refuses what it cannot take."""
    limits = {r["id"]: r.get("inventoryLimit") for r in rewards}
    owned: dict[int, int] = {}
    for item in inventory:
        owned[item["reward"]["id"]] = owned.get(item["reward"]["id"], 0) + 1
    for row in (r for r in action_rewards if r["actionId"] == action_id):
        limit = limits.get(row["rewardId"])
        if limit is not None and owned.get(row["rewardId"], 0) + row.get("amount", 1) > limit:
            return False
    return True
