"""Daily rewards (writes; requests observed 2026-10-07 with ``inspect-writes``, rules in THEORY.md section 17).

Login reward, the three daily missions plus the day reward, and the reward for accumulated videos. Whatever
the game offers is claimed and KEPT in the inventory, except the login reward, which the site itself spends
into its wallet (energy, boss coins). Nothing from the inventory is ever used. The game's own limits are
respected: no claim that would overfill an inventory slot, and a refused claim is not repeated that day (D-032).
"""
from __future__ import annotations

import time

from osmbot.game import refusals
from osmbot.rewards.policy import (VIDEO_COUNTER_ACTION, day_key, has_room, is_daily, mission_summary, next_claim,
                                   wallet_path)

PAUSE_BETWEEN_WRITES = 1.5  # seconds
MAX_MISSION_CLAIMS = 10  # per pass
API_V11 = "https://web-api.onlinesoccermanager.com/api/v1.1"
COUNTS = {"login": 0, "missions": 0, "videos": 0}  # claimed in this run
_day_done: set[frozenset] = set()  # days whose day reward was already asked for (one per day)
_said: set[str] = set()  # "inventory full" notes already given
_catalogue: list[dict] = []  # the mission catalogue: it hardly ever changes, read once per run
_unspent: dict[int, str] = {}  # login rewards the bot claimed but failed to spend: reward id -> action (tried again)
_missions_read: list = [0.0, None]  # [when, body] of the last missions read
MISSIONS_FRESH = 5 * 60.0  # the board may reuse a missions read this recent (the claims always read anew)


def read_missions(client, max_age: float = 0.0, clock=time.time) -> list[dict]:
    """The user's missions: the site itself asks with a body-less POST every time it opens (observed).
    ``max_age``: reuse the last answer if it is at most this old (the board), so the POST is not repeated
    after every video or claim."""
    when, body = _missions_read
    if body is not None and max_age > 0 and clock() - when <= max_age:
        return body
    status, body = client.request("POST", "usermissions/weeklytrack")
    if status != 200 or not isinstance(body, list):
        raise RuntimeError(f"estado das missões ilegível ({status})")
    _missions_read[:] = [clock(), body]
    return body


def catalogue(client) -> list[dict]:
    if not _catalogue:
        _catalogue.extend(client.get("missions")[1])
    return _catalogue


def _room(client, action_id: str) -> bool:
    """Would the game's own inventory limit allow one more of this action's reward?"""
    return has_room(action_id, client.get(f"{API_V11}/actionrewards")[1], client.get(f"{API_V11}/rewards")[1],
                    client.get("user/userrewards")[1])


def _full_note(key: str, text: str, log) -> None:
    if key not in _said:
        _said.add(key)
        log(text)


def _spend(client, reward_id: int, action: str, coins_before: int | None, value: int, log) -> int:
    """Spend one login reward into its wallet, as the site does. Returns the failures (0 or 1)."""
    path = wallet_path(action)
    status, _ = client.post(path, {"rewardId": reward_id})
    if refusals.is_refusal(status):  # D-032: not asked again today (it stays in the inventory meanwhile)
        _unspent[reward_id] = action
        refusals.refuse(f"início:gastar:{reward_id}", log, f"! Início de sessão: o jogo recusou gastar {action} ({status}); "
                        "volto a tentar amanhã", day=refusals.game_day())
        return 0
    if status != 200:
        _unspent[reward_id] = action
        log(f"Início de sessão: falha ao gastar {action} ({status}); volto a tentar")
        return 1
    _unspent.pop(reward_id, None)
    log(f"Início de sessão: {action} reclamado e gasto")
    if coins_before is not None and path.startswith("user/bosscoinwallet") and             client.get("user/bosscoinwallet")[1]["amount"] < coins_before + value:
        log(f"Início de sessão: erro, os boss coins não subiram depois de gastar {action}")
        return 1
    return 0


def spend_leftovers(client, confirm: bool, log=print) -> int:
    """Login rewards the bot claimed earlier but could not spend: try again (only those, never other items)."""
    if not (_unspent and confirm):
        return 0
    owned = {r["id"]: r for r in client.get("user/userrewards")[1]}
    failures = 0
    for reward_id, action in list(_unspent.items()):
        if reward_id not in owned:  # spent meanwhile (by hand, or the game): nothing to do
            _unspent.pop(reward_id)
            continue
        if refusals.blocked(f"início:gastar:{reward_id}"):
            continue
        failures += _spend(client, reward_id, action, None, 0, log)
        time.sleep(PAUSE_BETWEEN_WRITES)
    return failures


def claim_login(client, confirm: bool, log=print) -> int:
    """The login reward, when ``isClaimable``. Returns the failures."""
    failures = spend_leftovers(client, confirm, log)
    _, state = client.get("user/dailylogin")
    if not isinstance(state, dict) or not state.get("isClaimable") or refusals.blocked("início:reclamar"):
        return failures
    today = next((d for d in state.get("rewardTrackDays", []) if d.get("isClaimable")), {})
    if not confirm:
        log(f"Simulação: reclamaria o início de sessão ({today.get('actionId', '?')})")
        return 0
    known = {r["id"] for r in client.get("user/userrewards")[1]}
    coins_before = client.get("user/bosscoinwallet")[1]["amount"]
    status, _ = client.put("user/dailylogin/claim")
    if refusals.is_refusal(status):
        refusals.refuse("início:reclamar", log, f"! Início de sessão: o jogo recusou ({status}); volto a tentar amanhã",
                        day=refusals.game_day())
        return failures
    if status != 200:
        log(f"Início de sessão: falha ao reclamar ({status})")
        return failures + 1
    COUNTS["login"] += 1
    time.sleep(PAUSE_BETWEEN_WRITES)
    for item in (r for r in client.get("user/userrewards")[1] if r["id"] not in known):
        action = item["action"]["id"]
        if wallet_path(action) is None:
            log(f"Início de sessão: {action} reclamado; fica no inventário")
            continue
        failures += _spend(client, item["id"], action, coins_before, item["reward"]["value"], log)
    return failures


def claim_missions(client, confirm: bool, log=print, clock=time.time) -> int:
    """The daily missions that reached their goal, then the day reward (always kept, never used)."""
    goals = {m["id"]: m for m in catalogue(client)}
    for _ in range(MAX_MISSION_CLAIMS):
        state = read_missions(client)
        refused = {m["id"] for m in state if refusals.blocked(f"missão:{m['id']}")}  # D-032: kept for the game day
        mission = next_claim(state, list(goals.values()), refused, _day_done, clock())
        if mission is None:
            return 0
        daily = is_daily(mission)
        action = goals.get(mission["missionId"], {}).get("actionId")
        label = f"missão {mission['order']}" if daily else f"prémio do dia ({action})"
        if not daily and action and not _room(client, action):
            _full_note(f"mission-{mission['id']}", f"Missões: inventário cheio para {action}; não reclamo o prémio do dia por agora", log)
            return 0
        if not confirm:
            log(f"Simulação: reclamaria {label}")
            return 0
        status, _ = client.put(f"usermissions/{mission['id']}/claim")
        time.sleep(PAUSE_BETWEEN_WRITES)
        if not daily and status < 500:
            _day_done.add(day_key(state))  # accepted or refused: not another day's reward today
        if status == 200:
            COUNTS["missions"] += 1
            log(f"Missões: {label} reclamado" + ("" if daily else " e guardado no inventário"))
        elif refusals.is_refusal(status):
            refusals.refuse(f"missão:{mission['id']}", log, f"Missões: o jogo recusou {label} ({status}); não insisto hoje",
                            day=refusals.game_day())
        else:
            log(f"Missões: falha ao reclamar {label} ({status})")
            return 1
    return 0


def claim_video_reward(client, confirm: bool, log=print) -> int:
    """The reward for accumulated videos (counter at its threshold): goes to the inventory, never used."""
    _, cap = client.get(f"user/caps/actions/{VIDEO_COUNTER_ACTION}/0")
    _, counter = client.get(f"user/caps/counters/{VIDEO_COUNTER_ACTION}")
    if not (isinstance(cap, dict) and cap.get("isClaimable") and counter["currentCount"] >= counter["threshold"]):
        return 0
    if not _room(client, VIDEO_COUNTER_ACTION):
        _full_note("videos", "Vídeos acumulados: inventário cheio; não reclamo a troca de posição por agora", log)
        return 0
    if not confirm:
        log("Simulação: reclamaria a recompensa dos vídeos acumulados")
        return 0
    status, _ = client.request("POST", f"user/actions/{VIDEO_COUNTER_ACTION}")
    if status != 200:
        log(f"Vídeos acumulados: falha ao reclamar ({status})")
        return 1
    COUNTS["videos"] += 1
    log("Vídeos acumulados: troca de posição reclamada e guardada no inventário")
    return 0


def daily_state(client, clock=time.time) -> dict:
    """What the board shows about the daily rewards. A part that could not be read is None."""
    out = {"login": None, "missions": None, "videos": None}
    try:
        state = client.get("user/dailylogin")[1]
        out["login"] = {"claimable": bool(state["isClaimable"]), "day": state["consecutiveLoginCount"],
                        "renews": state["countdownTimer"]["finishedTimestamp"]}
    except Exception:
        pass
    try:
        state = read_missions(client, MISSIONS_FRESH, clock)
        refused = {m["id"] for m in state if refusals.blocked(f"missão:{m['id']}")}
        out["missions"] = mission_summary(state, catalogue(client), refused, _day_done, clock())
    except Exception:
        pass
    try:
        cap = client.get(f"user/caps/actions/{VIDEO_COUNTER_ACTION}/0")[1]
        counter = client.get(f"user/caps/counters/{VIDEO_COUNTER_ACTION}")[1]
        out["videos"] = {"count": counter["currentCount"], "threshold": counter["threshold"],
                         "claimable": bool(cap.get("isClaimable")) and counter["currentCount"] >= counter["threshold"],
                         "reopen": (cap.get("timestampUntilUnreached") or None) if cap.get("isCapReached") else None}
    except Exception:
        pass
    return out


def run_rewards(confirm: bool) -> tuple[int, list[float]]:
    """All three, each independent of the others. Returns (failures, times to wake at).
    Without ``confirm`` only shows what it would do."""
    from osmbot.game.client import NeedsBrowserLogin, OsmClient

    failures, wake = 0, []
    try:
        client = OsmClient()
        for step in (claim_login, claim_missions, claim_video_reward):
            try:
                failures += step(client, confirm)
            except (NeedsBrowserLogin, OSError):
                raise
            except Exception as error:
                print(f"Recompensas: erro ({error})")
                failures += 1
        state = daily_state(client)
        now = time.time()
        wake = [t for t in ((state["login"] or {}).get("renews"), (state["videos"] or {}).get("reopen")) if t and t > now]
    except NeedsBrowserLogin as error:
        raise SystemExit(str(error))
    return failures, wake
