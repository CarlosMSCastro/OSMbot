"""Read-only view of each club's training sessions and next match.

Fields come from ``trainingsessions/ongoing`` and ``timers`` (see DISCOVERY.md).
A session whose ``finishedTimestamp`` has passed and is not claimed is ready to
collect (confirmed by the owner on 2026-10-04). ``run_claim`` and ``run_train`` write to
the game, by default (``--simular`` makes them a dry run) (requests observed 2026-10-04, see DISCOVERY.md).
"""
from __future__ import annotations

import time

from osmbot.models import Player
from osmbot.training.policy import plan_training

POSITIONS = {1: "ATA", 2: "MED", 3: "DEF", 4: "GR"}
COUNTS = {"claimed": 0, "started": 0}  # successful writes in this run, for the board summary
NEXT_MATCH_TIMER = 14


def _span(seconds: float) -> str:
    minutes = int(abs(seconds) // 60)
    return f"{minutes // 60}h{minutes % 60:02d}"


def summarize_trainings(sessions: list[dict], timers: list[dict], now: float | None = None) -> list[str]:
    now = time.time() if now is None else now
    lines = []
    for session in sorted(sessions, key=lambda s: s["countdownTimer"]["finishedTimestamp"]):
        timer = session["countdownTimer"]
        player = session["player"]
        left = timer["finishedTimestamp"] - now
        if timer["isClaimed"]:
            state = "recolhido"
        elif left <= 0:
            state = f"pronto (há {_span(left)})"
        else:
            state = f"faltam {_span(left)}"
        lines.append(f"  {player['name']} ({POSITIONS.get(player['position'], '?')}): {state}")
    nxt = next((t for t in timers if t["type"] == NEXT_MATCH_TIMER), None)
    if nxt:
        left = nxt["finishedTimestamp"] - now
        lines.append(f"  Próximo jogo: {'em ' + _span(left) if left > 0 else 'a decorrer'}")
    return lines


ALL_TRAINERS = (1, 2, 3, 4)
TRAINING_SETTING_NAME = "TrainingSession"  # gamesettings entry for the 8h training (hypothesis, see DISCOVERY.md)
PAUSE_BETWEEN_WRITES = 1.5  # seconds


def ready_sessions(sessions: list[dict], now: float) -> list[dict]:
    """Finished sessions not yet claimed."""
    return [
        s for s in sessions
        if not s["countdownTimer"]["isClaimed"] and s["countdownTimer"]["finishedTimestamp"] <= now
    ]


def plan_new_trainings(players: list[dict], sessions: list[dict], listed_ids: set[int]) -> dict[int, Player]:
    """Which player each free trainer slot should train now (owner's policy, THEORY.md section 5).

    A slot is free when no session in ``sessions`` uses it. Players already in a session, and
    players the owner has listed for sale, are never picked.
    """
    busy = {s["trainer"] for s in sessions}
    free = [t for t in ALL_TRAINERS if t not in busy]
    unavailable = {s["playerId"] for s in sessions} | set(listed_ids)
    return plan_training([Player.from_api(p) for p in players], free, unavailable_ids=unavailable)


def _teams(client):
    _, account = client.get("user/accounts")
    for slot, content in sorted((account.get("teamSlots") or {}).items()):
        team = (content or {}).get("team")
        if team:
            yield slot, team, f"leagues/{team['leagueId']}/teams/{team['id']}"


def run_claim(confirm: bool, limit: int | None = None) -> int:
    """Collect every finished training. Without ``confirm`` only shows what it would do. Returns the failures."""
    from osmbot.game.client import NeedsBrowserLogin, OsmClient

    failed = 0
    try:
        client = OsmClient()
        done = 0
        for slot, team, base in _teams(client):
            _, sessions = client.get(f"{base}/trainingsessions/ongoing")
            ready = ready_sessions(sessions, time.time())
            print(f"{team['name']}: {len(ready)} para recolher")
            for session in ready:
                if limit is not None and done >= limit:
                    print("  (limite)")
                    break
                name = session["player"]["name"]
                if not confirm:
                    print(f"  recolheria: {name}")
                    continue
                status, body = client.put(f"https://web-api.onlinesoccermanager.com/api/v1.1/{base}/trainingsessions/{session['id']}/claim")
                gain = body.get("progressImprovement") if isinstance(body, dict) else None
                print(f"  {name}: {'recolhido' if status == 200 else 'falhou'} ({status}{f', +{gain}' if status == 200 and gain is not None else ''})")
                failed += status != 200
                COUNTS["claimed"] += status == 200
                done += 1
                time.sleep(PAUSE_BETWEEN_WRITES)
    except NeedsBrowserLogin as error:
        raise SystemExit(str(error))
    if not confirm:
        print("\nSimulação: nada alterado")
    return failed


def run_train(confirm: bool, limit: int | None = None) -> int:
    """Put the owner's policy choices to train in every free slot. Without ``confirm`` only shows the plan.
    Returns the failures."""
    from osmbot.game.client import NeedsBrowserLogin, OsmClient

    failed = 0
    try:
        client = OsmClient()
        done = 0
        for slot, team, base in _teams(client):
            _, sessions = client.get(f"{base}/trainingsessions/ongoing")
            _, players = client.get(f"{base}/players")
            _, market = client.get(f"{base}/transferplayers/0")
            mine = {p["id"] for p in players}
            listed = {x["player"]["id"] for x in market if x["player"]["id"] in mine}
            _, settings = client.get(f"leagues/{team['leagueId']}/gamesettings")
            setting = next((g["id"] for g in settings if g["name"] == TRAINING_SETTING_NAME), None)
            ready = ready_sessions(sessions, time.time())
            # Preview assumes the ready sessions get collected first; a real run only uses truly free slots.
            considered = sessions if confirm else [s for s in sessions if s not in ready]
            plan = plan_new_trainings(players, considered, listed)
            note = ""
            if ready:
                note = (" (ainda ha %d treino(s) por recolher: corre 'osmbot recolher' primeiro)" if confirm
                        else " (assumindo que recolhes os %d pronto(s) primeiro)") % len(ready)
            print(f"{team['name']}: {len(plan)} treino(s) a iniciar{note}")
            for trainer, player in sorted(plan.items()):
                if limit is not None and done >= limit:
                    print("  (limite)")
                    break
                label = f"{player.name} ({POSITIONS[int(player.position)]}, {player.age} anos, rating {player.rating})"
                if not confirm:
                    print(f"  iniciaria: {label}")
                    continue
                if setting is None:
                    raise SystemExit("Duração do treino não encontrada nas definições do jogo; nada alterado")
                status, _ = client.post(
                    f"{base}/trainingsessions",
                    {"playerId": player.id, "trainer": trainer, "timerGameSettingId": setting},
                )
                print(f"  {label}: {'a treinar' if status == 200 else 'falhou'} ({status})")
                failed += status != 200
                COUNTS["started"] += status == 200
                done += 1
                time.sleep(PAUSE_BETWEEN_WRITES)
    except NeedsBrowserLogin as error:
        raise SystemExit(str(error))
    if not confirm:
        print("\nSimulação: nada alterado")
    return failed


def pending_finish_times(client) -> list[float]:
    """When each unclaimed training of every club finishes (a past time means ready now)."""
    times = []
    for _, _, base in _teams(client):
        _, sessions = client.get(f"{base}/trainingsessions/ongoing")
        times += [s["countdownTimer"]["finishedTimestamp"] for s in sessions if not s["countdownTimer"]["isClaimed"]]
    return times


def run_trainings() -> None:
    from osmbot.game.client import NeedsBrowserLogin, OsmClient

    try:
        client = OsmClient()
        _, account = client.get("user/accounts")
        for slot, content in sorted((account.get("teamSlots") or {}).items()):
            team = (content or {}).get("team")
            if not team:
                continue
            base = f"leagues/{team['leagueId']}/teams/{team['id']}"
            _, sessions = client.get(f"{base}/trainingsessions/ongoing")
            _, timers = client.get(f"{base}/timers")
            print(f"[{slot}] {team['name']}")
            print("\n".join(summarize_trainings(sessions, timers)) or "  (sem sessões)")
    except NeedsBrowserLogin as error:
        raise SystemExit(str(error))
