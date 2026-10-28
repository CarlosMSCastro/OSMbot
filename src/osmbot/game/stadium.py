"""Stadium upgrades (writes, owner's rules in THEORY.md section 15; requests observed 2026-10-07).

Starting an upgrade is one POST; a finished one only counts once collected (an empty PUT on the part),
so finished ones are collected before the next one starts (starting it first loses the previous one).
There is no price to read: the bot tries and the game accepts or refuses. Savings are
all-or-nothing and the same empty PUT moves everything the other way, so when the club's
funds are not enough everything is brought to the funds (at most two PUTs, each checked in the
reply), the upgrade is tried again and what is left goes straight back to savings.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from osmbot.game import refusals

from osmbot.stadium.policy import (BOOST_PRODUCT, EVENT_BUDGET, PART_NAMES, event_key, next_part, running_until,
                                   stadium_event, to_claim)

SETTING_NAME = "StadiumUpgrade"  # gamesettings entry with the upgrade duration (id 30 on 2026-10-07)
PAUSE_BETWEEN_WRITES = 1.5  # seconds
COUNTS = {"upgrades": 0, "boosted": 0}
EVENT_FILE = Path.home() / ".osmbot" / "estadio_evento.json"  # boss coins spent per stadium event (D-075)


def _money(client, base: str) -> tuple[int, int]:
    _, data = client.get(f"{base}/finances/balanceandsavings")
    return data["balance"], data["savings"]


def _move_savings(client, base: str) -> dict | None:
    """The empty PUT that moves everything to the other side; returns the reply (new balance and savings)."""
    status, body = client.put(f"{base}/savings/transfer")
    time.sleep(PAUSE_BETWEEN_WRITES)
    return body if status == 200 and isinstance(body, dict) else None


def _bring_to_funds(client, base: str, log) -> bool:
    """Everything into the club's funds. At most two PUTs (the first one may be a deposit if money is split)."""
    for _ in range(2):
        reply = _move_savings(client, base)
        if reply is None:
            log("  transferência da poupança falhou")
            return False
        if reply["savings"] == 0:
            return True
    return False


def _claim_finished(client, team: dict, base: str, parts: list[dict], now: float, confirm: bool, log) -> tuple[list[dict], int]:
    """Collect every finished upgrade. Returns (the stadium parts read again if something was collected, failures)."""
    done = to_claim(parts, now)
    if not done:
        return parts, 0
    failures = 0
    for part in done:
        name = PART_NAMES.get(part["stadiumPartType"], part["stadiumPartType"])
        if not confirm:
            log(f"{team['name']}: {name}: recolheria a melhoria acabada")
            continue
        key, day = f"estádio-recolher:{base}:{part['id']}", refusals.game_day()
        if refusals.blocked(key, day=day):
            failures += 1
            continue  # refused today: try again on the next game day, not every round
        status, _ = client.put(f"{base}/stadiumparts/{part['id']}/claim")
        time.sleep(PAUSE_BETWEEN_WRITES)
        if status == 200:
            refusals.forget(key)
            log(f"{team['name']}: {name}: melhoria recolhida")
            continue
        failures += 1
        if refusals.is_refusal(status):
            refusals.refuse(key, log, f"{team['name']}: {name}: o jogo recusou recolher a melhoria ({status}); volto a tentar amanhã", day=day)
        else:
            log(f"{team['name']}: {name}: recolher a melhoria falhou ({status})")
    if not confirm:
        return parts, 0
    _, stadium = client.get(f"{base}/stadium")
    return stadium["stadiumParts"], failures


def _try_upgrade(client, base: str, part_type: int, setting: int, log) -> tuple[str, float | None]:
    """("ok", end time) / ("refused", None) / ("failed", None)."""
    status, body = client.post(f"{base}/stadiumparts", {"stadiumPartType": part_type, "timerGameSettingId": setting})
    time.sleep(PAUSE_BETWEEN_WRITES)
    if status == 200:
        timer = body.get("countdownTimer") if isinstance(body, dict) else None
        return "ok", (timer or {}).get("finishedTimestamp")
    log(f"  recusado ({status})" if refusals.is_refusal(status) else f"  falhou ({status})")
    return ("refused" if refusals.is_refusal(status) else "failed"), None


def upgrade_club(client, team: dict, base: str, confirm: bool, log=print, now: float | None = None) -> tuple[int, list[float]]:
    """One club: start the next upgrade if the club is free. Returns (failures, times to wake at)."""
    now = time.time() if now is None else now
    _, stadium = client.get(f"{base}/stadium")
    parts, failures = _claim_finished(client, team, base, stadium["stadiumParts"], now, confirm, log)
    if failures or (confirm and to_claim(parts, now)):
        return failures or 1, []  # never start the next one over an uncollected one: it would be lost
    busy = running_until(parts, now)
    if busy is not None:
        if not confirm:
            log(f"{team['name']}: melhoria em curso, acaba em {int((busy - now) // 3600)}h{int((busy - now) % 3600 // 60):02d}")
        return 0, [busy]
    part_type = next_part(parts, now)
    if part_type is None:
        if not confirm:
            log(f"{team['name']}: estádio no máximo")
        return 0, []
    balance, savings = _money(client, base)
    total = balance + savings
    if refusals.blocked(f"estádio:{base}", money=total):
        return 0, []  # no new money since the last refusal: do not touch savings for nothing (D-032)
    label = f"{team['name']}: {PART_NAMES[part_type]}"
    if not confirm:
        log(f"{label}: tentaria melhorar (fundos {balance}, poupança {savings})")
        return 0, []
    _, settings = client.get(f"leagues/{team['leagueId']}/gamesettings")
    setting = next((g["id"] for g in settings if g["name"] == SETTING_NAME), None)
    if setting is None:
        log(f"{label}: duração da melhoria não encontrada nas definições do jogo")
        return 1, []
    outcome, ends = "refused", None
    if balance > 0:
        outcome, ends = _try_upgrade(client, base, part_type, setting, log)
    if outcome == "refused" and savings > 0:
        moved = False
        try:
            moved = _bring_to_funds(client, base, log)
            if moved:
                outcome, ends = _try_upgrade(client, base, part_type, setting, log)
        finally:  # whatever happened, the money goes straight back to savings
            in_funds, in_savings = _money(client, base)
            if in_funds > 0 and in_savings == 0 and _move_savings(client, base) is None:
                log("  AVISO: não consegui voltar a depositar a poupança")
        if not moved:
            return 1, []
    if outcome == "ok":
        COUNTS["upgrades"] += 1
        refusals.forget(f"estádio:{base}")
        paid = total - sum(_money(client, base))  # the price is not in the reply: measured on the money
        log(f"{label}: melhoria iniciada · custou {paid}")
        return 0, [ends] if ends else []
    if outcome == "refused":
        refusals.refuse(f"estádio:{base}", log, f"{label}: sem dinheiro para melhorar; volto a tentar quando houver mais", money=total)
        return 0, []
    return 1, []


def run_stadium(confirm: bool) -> tuple[int, list[float]]:
    """Every club, in the owner's order. Returns (failures, times to wake at). Without ``confirm`` only shows."""
    from osmbot.game.client import NeedsBrowserLogin, OsmClient
    from osmbot.game.trainings import _teams

    failures, wake = 0, []
    try:
        client = OsmClient()
        for _, team, base in _teams(client):
            failed, times = upgrade_club(client, team, base, confirm)
            failures += failed
            wake += times
    except NeedsBrowserLogin as error:
        raise SystemExit(str(error))
    return failures, wake


def _spent() -> dict:
    try:
        return json.loads(EVENT_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _boost_running(client, team: dict, base: str, products: list[dict], room: int, log) -> int:
    """Finish the club's running upgrade with boss coins when it costs no more than ``room``; it counts at once, with
    nothing to collect (DISCOVERY.md section 3, 2026-10-19/24). Returns the boss coins spent (0: not done)."""
    from osmbot.training.policy import boost_product

    _, stadium = client.get(f"{base}/stadium")
    now = time.time()
    part = next((p for p in stadium["stadiumParts"]
                 if p.get("countdownTimer") and p["countdownTimer"]["finishedTimestamp"] > now), None)
    if part is None:
        return 0
    left = part["countdownTimer"]["finishedTimestamp"] - now
    product = boost_product(products, left, BOOST_PRODUCT)
    if product is None or product["value"] > room:
        return 0
    _, wallet = client.get("user/bosscoinwallet")
    if (wallet or {}).get("amount", 0) < product["value"]:
        return 0
    status, _ = client.request("PUT", f"{base}/stadiumparts/{part['id']}/boost", {"productId": product["id"]})
    time.sleep(PAUSE_BETWEEN_WRITES)
    label = f"{team['name']}: {PART_NAMES.get(part['stadiumPartType'], '?')}"
    if status != 200:
        log(f"{label}: acelerar falhou ({status})")
        return 0
    COUNTS["boosted"] += 1
    from osmbot.game import wallet as ledger

    ledger.note("estádio", -product["value"])
    log(f"{label}: melhoria acelerada com {product['value']} boss coins (faltavam {int(left // 3600)}h{int(left % 3600 // 60):02d})")
    return product["value"]


def run_event_stadium_boost(confirm: bool, log=print) -> int:
    """In a stadium event (the upgrade at 4 h), finish upgrades with boss coins and start the next, a club at a time,
    up to ``EVENT_BUDGET`` boss coins per event (owner, 2026-10-28, D-075; THEORY.md section 8). Without ``confirm``
    only shows. Returns the failures."""
    from osmbot.game.client import NeedsBrowserLogin, OsmClient
    from osmbot.game.clubinfo import timer_minutes
    from osmbot.game.events import calendar_events
    from osmbot.game.trainings import _products, _teams

    try:
        client = OsmClient()
        clubs = [(team, base) for _, team, base in _teams(client)
                 if stadium_event(timer_minutes(client, team["leagueId"], "StadiumUpgrade"))]
        if not clubs:
            return 0
        key = event_key(calendar_events(days=0), refusals.game_day())
        used = _spent().get(key, 0)
        if used >= EVENT_BUDGET:
            return 0
        if not confirm:
            log(f"Evento de estádio: aceleraria até {EVENT_BUDGET - used} boss coins em {len(clubs)} clube(s)")
            return 0
        products, failures, moved = _products(client), 0, True
        while moved and used < EVENT_BUDGET:
            moved = False
            for team, base in clubs:
                failures += upgrade_club(client, team, base, confirm, log)[0]  # collect, then start the next if free
                cost = _boost_running(client, team, base, products, EVENT_BUDGET - used, log)
                if cost:
                    used, moved = used + cost, True
                    EVENT_FILE.parent.mkdir(parents=True, exist_ok=True)
                    EVENT_FILE.write_text(json.dumps({key: used}), encoding="utf-8")
                if used >= EVENT_BUDGET:
                    break
        for team, base in clubs:  # the next one at the event's length, as on any pass
            failures += upgrade_club(client, team, base, confirm, log)[0]
        if moved or used >= EVENT_BUDGET:
            log(f"Evento de estádio: {used} de {EVENT_BUDGET} boss coins gastas a acelerar")
        return failures
    except NeedsBrowserLogin as error:
        raise SystemExit(str(error))
