"""Stadium upgrades (writes, owner's rules in THEORY.md section 15; requests observed 2026-10-07).

Starting an upgrade is one POST; when it ends the next one is just started (nothing to collect).
There is no price to read: the bot tries and the game accepts or refuses. Savings are
all-or-nothing and the same empty PUT moves everything the other way, so when the club's
funds are not enough everything is brought to the funds (at most two PUTs, each checked in the
reply), the upgrade is tried again and what is left goes straight back to savings.
"""
from __future__ import annotations

import time

from osmbot.stadium.policy import PART_NAMES, next_part, running_until

SETTING_NAME = "StadiumUpgrade"  # gamesettings entry with the upgrade duration (id 30 on 2026-10-07)
PAUSE_BETWEEN_WRITES = 1.5  # seconds
COUNTS = {"upgrades": 0}
_last_refused: dict[str, int] = {}  # club base path -> total money (funds + savings) at its last refusal


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


def _try_upgrade(client, base: str, part_type: int, setting: int, log) -> tuple[str, float | None]:
    """("ok", end time) / ("refused", None) / ("failed", None)."""
    status, body = client.post(f"{base}/stadiumparts", {"stadiumPartType": part_type, "timerGameSettingId": setting})
    time.sleep(PAUSE_BETWEEN_WRITES)
    if status == 200:
        timer = body.get("countdownTimer") if isinstance(body, dict) else None
        return "ok", (timer or {}).get("finishedTimestamp")
    log(f"  recusado ({status})" if 400 <= status < 500 else f"  falhou ({status})")
    return ("refused" if 400 <= status < 500 else "failed"), None


def upgrade_club(client, team: dict, base: str, confirm: bool, log=print, now: float | None = None) -> tuple[int, list[float]]:
    """One club: start the next upgrade if the club is free. Returns (failures, times to wake at)."""
    now = time.time() if now is None else now
    _, stadium = client.get(f"{base}/stadium")
    parts = stadium["stadiumParts"]
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
    if total <= _last_refused.get(base, -1):
        return 0, []  # no new money since the last refusal: do not touch savings for nothing
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
        _last_refused.pop(base, None)
        log(f"{label}: melhoria iniciada")
        return 0, [ends] if ends else []
    if outcome == "refused":
        _last_refused[base] = total
        log(f"{label}: sem dinheiro para melhorar")
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
