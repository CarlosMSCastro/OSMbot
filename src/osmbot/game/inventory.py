"""The inventory items that expire: used 4 h before they would (writes; owner's rules in THEORY.md section 20, D-039).

Requests read in the game's public web code (DISCOVERY.md section 3): a universal trainer is
``PUT leagues/{L}/teams/{T}/universaltrainer/{item}/claim`` (first use seen 2026-10-12: a 24 h timer of type 17)
and then trains with the usual ``POST trainingsessions`` on trainer 5 (6 h sessions); a bag is
``PUT user/randomrewards/{item}/claim`` (never done yet), whose boss coins the site spends at once into the
wallet. Swaps and progression never expire and are never used. A refused request is not repeated that day (D-032).
"""
from __future__ import annotations

import time

from osmbot import logs
from osmbot.game import refusals
from osmbot.game.timers import minutes_text
from osmbot.inventory.policy import (BAG, UNIVERSAL, UNIVERSAL_TRAINER, active_until, due, expires, pick_club,
                                     universal_trainee, wake_times)
from osmbot.rewards.texts import prize_text

PAUSE_BETWEEN_WRITES = 1.5  # seconds
UNIVERSAL_SETTING = "TrainingUniversalSession"  # gamesettings: the 6 h session of the universal trainer
BOSS_COINS = 1  # reward type
COUNTS = {"universal": 0, "bags": 0, "sessions": 0}


def _name(player: dict) -> str:
    return player.get("name") or player.get("fullName") or str(player.get("id"))


class _Club:
    """What the bot reads of one club to choose and place the universal trainer's player."""

    def __init__(self, client, team: dict, base: str, now: float):
        from osmbot.game.trainings import _recorded, note_seen
        from osmbot.training.policy import round_sessions

        self.team, self.base, self.league = team, base, team["leagueId"]
        _, self.timers = client.get(f"{base}/timers")
        _, self.sessions = client.get(f"{base}/trainingsessions/ongoing")
        _, self.players = client.get(f"{base}/players")
        _, market = client.get(f"{base}/transferplayers/0")
        mine = {p["id"] for p in self.players}
        self.listed = {x["player"]["id"] for x in market or [] if x["player"]["id"] in mine}
        status, forecasts = client.get(f"{base}/trainingforecasts")
        self.forecasts = ({f["playerId"]: f.get("forecastUniversal") or 0 for f in forecasts}
                          if status == 200 and isinstance(forecasts, list) else {})
        _, league = client.get(f"leagues/{self.league}")
        self.week = league["weekNr"]
        note_seen(base, self.sessions)
        self.rounds = round_sessions(self.sessions, _recorded(base, self.week), self.week)
        self.until = active_until(self.timers, now)
        self.value = sum(p.get("value") or 0 for p in self.players)
        self.trainee = universal_trainee(self.players, self.sessions, self.listed, self.rounds, self.forecasts)

    def universal_busy(self) -> bool:
        """A session on the universal trainer is running or waits to be collected."""
        return any(s["trainer"] == UNIVERSAL_TRAINER for s in self.sessions)


def _setting(client, league: int) -> tuple[int, int] | None:
    """The universal session's setting: its id and its length now, in minutes (360 normally, 90 in the Super Staff)."""
    _, settings = client.get(f"leagues/{league}/gamesettings")
    return next(((g["id"], g.get("value")) for g in settings or [] if g.get("name") == UNIVERSAL_SETTING), None)


_minutes = minutes_text  # the time as the log says it (game/timers)


def _train(client, club: _Club, confirm: bool, log) -> int:
    """Put the chosen player on the universal trainer. Returns the failures."""
    from osmbot.game.trainings import _record

    player = club.trainee
    if player is None:
        refusals.refuse(f"universal:ninguém:{club.base}", log, f"Treinador universal ({club.team['name']}): ninguém para treinar",
                        day=refusals.game_day())
        return 0
    key = f"universal:treinar:{club.base}"
    if refusals.blocked(key, day=refusals.game_day()):
        return 0
    label = f"{_name(player)} ({club.team['name']}, previsão {club.forecasts.get(player['id'], '?')})"
    if not confirm:
        log(f"Simulação: poria {label} no treinador universal")
        return 0
    found = _setting(client, club.league)
    if found is None:
        log("Treinador universal: duração da sessão não encontrada nas definições do jogo")
        return 1
    setting, minutes = found
    status, body = client.post(f"{club.base}/trainingsessions",
                               {"playerId": player["id"], "trainer": UNIVERSAL_TRAINER, "timerGameSettingId": setting})
    time.sleep(PAUSE_BETWEEN_WRITES)
    if status == 200:
        session_id = body.get("id") if isinstance(body, dict) else None
        _record(club.base, club.week, session_id or f"bot-{time.time():.0f}-{player['id']}", player["id"])
        COUNTS["sessions"] += 1
        logs.record("treinos", {"evento": "pôr", "clube": club.base, "sessao": session_id, "semana": club.week,
                                "treinador": UNIVERSAL_TRAINER, "jogador": {"id": player["id"], "nome": _name(player)},
                                "previsao": club.forecasts.get(player["id"]), "n_na_jornada": club.rounds.get(player["id"], 0) + 1})
        log(f"Treinador universal: {label} a treinar ({_minutes(minutes)})")
        return 0
    if refusals.is_refusal(status):
        refusals.refuse(key, log, f"! Treinador universal: o jogo recusou {label} ({status}); volto a tentar amanhã",
                        day=refusals.game_day())
        return 0
    log(f"Treinador universal: falhou pôr {label} ({status})")
    return 1


def _activate(client, item: dict, clubs: list[_Club], confirm: bool, log) -> int:
    """Use a universal trainer item on the club with the most to gain, then put its player on it."""
    free = [c for c in clubs if c.until is None]
    chosen = pick_club([{"club": c, "gain": c.forecasts.get(c.trainee["id"]) if c.trainee else None, "value": c.value}
                        for c in free])
    hours = round((item["reward"].get("value") or 0) / 60)
    key = f"universal:ativar:{item['id']}"
    if chosen is None:
        refusals.refuse(key, log, f"! Treinador universal de {hours} h vai expirar: nenhuma equipa livre com quem treinar",
                        day=refusals.game_day())
        return 0
    club = chosen["club"]
    if refusals.blocked(key, day=refusals.game_day()):
        return 0
    if not confirm:
        log(f"Simulação: ativaria o treinador universal de {hours} h em {club.team['name']}")
        return 0
    status, body = client.put(f"{club.base}/universaltrainer/{item['id']}/claim")
    time.sleep(PAUSE_BETWEEN_WRITES)
    if status != 200:
        if refusals.is_refusal(status):
            refusals.refuse(key, log, f"! Treinador universal: o jogo recusou ativar em {club.team['name']} ({status})",
                            day=refusals.game_day())
            return 0
        log(f"Treinador universal: falhou ativar em {club.team['name']} ({status})")
        return 1
    COUNTS["universal"] += 1
    club.until = (body or {}).get("finishedTimestamp") if isinstance(body, dict) else time.time() + hours * 3600
    logs.record("inventario", {"evento": "treinador universal", "item": item["action"]["id"], "clube": club.base,
                               "ate": club.until})
    log(f"Treinador universal de {hours} h ativado em {club.team['name']} (ia expirar no inventário)")
    return _train(client, club, confirm, log)


def _open_bag(client, item: dict, confirm: bool, log) -> int:
    """Open a bag; its boss coins go to the wallet (as the site does), the rest stays in the inventory."""
    key = f"saco:{item['id']}"
    if refusals.blocked(key, day=refusals.game_day()):
        return 0
    if not confirm:
        log("Simulação: abriria o saco do inventário antes de expirar")
        return 0
    status, body = client.put(f"user/randomrewards/{item['id']}/claim")
    time.sleep(PAUSE_BETWEEN_WRITES)
    if status != 200:
        if refusals.is_refusal(status):
            refusals.refuse(key, log, f"! Saco: o jogo recusou abrir ({status}); volto a tentar amanhã", day=refusals.game_day())
            return 0
        log(f"Saco: falhou abrir ({status})")
        return 1
    COUNTS["bags"] += 1
    got = body if isinstance(body, list) else [body] if isinstance(body, dict) else []
    got = [g for part in got for g in (part if isinstance(part, list) else [part]) if isinstance(g, dict)]
    failures = 0
    for reward in got:
        if (reward.get("reward") or {}).get("type") == BOSS_COINS and reward.get("id"):
            spent, _ = client.post("user/bosscoinwallet/consumereward", {"rewardId": reward["id"]})
            time.sleep(PAUSE_BETWEEN_WRITES)
            failures += spent != 200
    names = ", ".join(prize_text({**(g.get("reward") or {}), "action": (g.get("action") or {}).get("id")}) for g in got) or "?"
    logs.record("inventario", {"evento": "saco", "item": item["action"]["id"], "saiu": [
        {"acao": (g.get("action") or {}).get("id"), "tipo": (g.get("reward") or {}).get("type"),
         "valor": (g.get("reward") or {}).get("value")} for g in got]})
    log(f"Saco aberto antes de expirar: {names}")
    return failures


def run_inventory(confirm: bool, log=None, clock=time.time) -> tuple[int, list[float]]:
    """Keep each active universal trainer busy, then use the items due (THEORY.md section 20).
    Returns (failures, times to wake at). Without ``confirm`` only shows the plan."""
    from osmbot.game.client import NeedsBrowserLogin, OsmClient
    from osmbot.game.trainings import _teams

    if log is None:
        from osmbot.game.loop import _log as log
    failures, wake = 0, []
    try:
        client = OsmClient()
        now = clock()
        _, items = client.get("user/userrewards")
        items = items if isinstance(items, list) else []
        teams = list(_teams(client))
        active = [bool(active_until(client.get(f"{base}/timers")[1] or [], now)) for _, _, base in teams]
        if not (any(active) or due(items, now)):  # nothing to do: the squads are not read
            return 0, [t for t in wake_times(items, now) if t > clock()]
        clubs = [_Club(client, team, base, now) for _, team, base in teams]
        for club in clubs:
            if club.until and not club.universal_busy():
                failures += _train(client, club, confirm, log)
            if club.until:
                wake.append(club.until)
        for item in due(items, now):
            kind = item["reward"]["type"]
            if kind == UNIVERSAL:
                failures += _activate(client, item, clubs, confirm, log)
            elif kind == BAG:
                failures += _open_bag(client, item, confirm, log)
        wake += wake_times(items, now)
    except NeedsBrowserLogin as error:
        raise SystemExit(str(error))
    return failures, [t for t in wake if t > clock()]


def inventory_items(client) -> list[dict]:
    """The board's view of the inventory: every item, with when it expires (None: never)."""
    _, items = client.get("user/userrewards")
    return [{"type": i["reward"].get("type"), "value": i["reward"].get("value"), "action": i["action"]["id"],
             "expires": expires(i)} for i in items or [] if isinstance(i, dict)]
