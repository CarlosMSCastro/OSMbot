"""The inventory items that expire (owner, 2026-10-12; THEORY.md section 20, D-039). Pure: no network, no I/O.

Universal trainers and bags expire 7 days after they arrive; the bot uses them 4 h before they would, and the
window warns 24 h before. A universal trainer goes to the club with the most to gain and trains, while it lasts,
the starter of any position the rotation picks (section 5, with the game's forecast for the universal trainer).
"""
from __future__ import annotations

UNIVERSAL, BAG = 12, 13  # reward types of the items the bot uses (v1.1/rewards)
USED_TYPES = (UNIVERSAL, BAG)
USE_BEFORE = 4 * 3600  # owner: "quando faltar 3 ou 4 horas"
WARN_BEFORE = 24 * 3600
NEVER = 4_000_000_000  # an item that does not expire carries a huge expiredTimestamp
UNIVERSAL_TRAINER = 5  # TrainerType.Universal in the web code
UNIVERSAL_TIMER = 17  # "Universal coach availability"
FIELD_AGE_LIMIT, GOALKEEPER = 30, 4  # as the normal trainings (section 5): 30+ only for goalkeepers


def expires(item: dict) -> float | None:
    """When an item expires (None: never)."""
    when = item.get("expiredTimestamp")
    return when if when and when < NEVER else None


def due(items: list[dict], now: float) -> list[dict]:
    """The universal trainers and bags to use now: within USE_BEFORE of expiring (and not expired), soonest first."""
    found = [i for i in items if i["reward"]["type"] in USED_TYPES and expires(i) and now < expires(i) <= now + USE_BEFORE]
    return sorted(found, key=expires)


def wake_times(items: list[dict], now: float) -> list[float]:
    """When the next items become due (so the bot wakes for them)."""
    return sorted(expires(i) - USE_BEFORE for i in items
                  if i["reward"]["type"] in USED_TYPES and expires(i) and expires(i) - USE_BEFORE > now)


def active_until(timers: list[dict], now: float) -> float | None:
    """Until when a club's universal trainer is available (None: not active)."""
    ends = [t["finishedTimestamp"] for t in timers if t.get("type") == UNIVERSAL_TIMER and t["finishedTimestamp"] > now]
    return max(ends) if ends else None


def universal_trainee(players: list[dict], sessions: list[dict], listed: set[int], rounds: dict[int, int],
                      forecasts: dict[int, int]) -> dict | None:
    """Who the universal trainer should train: a starter (lineup 1-11) of any position with the fewest sessions this
    round, then the highest forecast for the universal trainer; never someone training, listed for sale, out
    (injured/suspended) or 30+ (goalkeepers any age). No starter fits: the rest of the squad by the same rule [S]."""
    busy = {s["playerId"] for s in sessions}

    def fits(p: dict) -> bool:
        return (p["id"] not in busy and p["id"] not in listed and not p.get("unavailable")
                and (p["age"] < FIELD_AGE_LIMIT or p["position"] == GOALKEEPER))

    def best(group: list[dict]) -> dict | None:
        return min(group, key=lambda p: (rounds.get(p["id"], 0), -forecasts.get(p["id"], 0)), default=None)

    pool = [p for p in players if fits(p)]
    return best([p for p in pool if 1 <= p.get("lineup", 0) <= 11]) or best(pool)


def pick_club(options: list[dict]) -> dict | None:
    """The club a universal trainer goes to: the most to gain (the chosen player's forecast for it), a tie to the
    weaker squad (lower value). ``options``: {"gain", "value", ...}; clubs with nobody to train are left out."""
    usable = [o for o in options if o.get("gain") is not None]
    return min(usable, key=lambda o: (-o["gain"], o.get("value") or 0), default=None)
