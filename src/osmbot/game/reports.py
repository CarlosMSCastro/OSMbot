"""The match report (owner, 2026-10-25: "guardar TODOS os relatórios"): what the game's presenter and pundit say
about each match of the owner's clubs, league, cup and friendlies. Reads only.

The game gives it only while the match is in the round on show: ``GET leagues/{L}/teams/{T}/matches/{matchId}/
{weekNr}/commentatorevents`` answers 404 once the next round comes (DISCOVERY.md section 3). So every pass reads
the reports of the club's matches the fixtures still show as played (``matchData``) and not yet kept: one line per
match in ``logs/<machine>/relatorios/`` with every comment, and the pundit's verdict in the day's log. State in
``~/.osmbot/relatorios.json``. To be studied from time to time (THEORY.md section 23).
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from osmbot import logs

FILE = Path.home() / ".osmbot" / "relatorios.json"
TYPES = {0: "liga", 1: "taça", 2: "amigável"}  # matchType
PHASES = {0: "antes", 1: "intervalo", 4: "fim"}  # commentatorPhase (2 and 3 not seen)
SPEAKERS = {0: "apresentador", 1: "comentador"}  # commentatorType (the game's Presenter and Pundit)
POST_MATCH, PUNDIT = 4, 1
RETRY = 15 * 60  # a played match with no report yet (404) is asked again after this long
KEEP = 400  # matches remembered as kept: far more than the rounds a report lives


def _load() -> dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _save(data: dict) -> None:
    try:
        FILE.parent.mkdir(parents=True, exist_ok=True)
        FILE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


def key(league_id: int, team_id: int, match: dict) -> str:
    return f"{league_id}:{team_id}:{match['weekNr']}:{match['matchId']}"


def pending(matches: list[dict], league_id: int, team_id: int, kept: set[str], waiting: dict[str, float],
            now: float) -> list[dict]:
    """The club's played matches (the fixtures still carry their ``matchData``) whose report is not kept yet, and
    not asked in the last ``RETRY`` seconds (pure)."""
    return [m for m in matches if team_id in (m.get("homeTeamId"), m.get("awayTeamId")) and m.get("matchData")
            and key(league_id, team_id, m) not in kept and now - waiting.get(key(league_id, team_id, m), 0) >= RETRY]


def comments(events: list[dict], team_id: int) -> list[dict]:
    """Every comment in the order of the match: the generic ones and this club's (pure)."""
    order = {phase: n for n, phase in enumerate(sorted(PHASES))}
    mine = [e for e in events if e.get("teamId") in (0, team_id) and e.get("text")]
    return [{"fase": PHASES.get(e.get("commentatorPhase"), e.get("commentatorPhase")),
             "quem": SPEAKERS.get(e.get("commentatorType"), e.get("commentatorType")), "texto": e["text"]}
            for e in sorted(mine, key=lambda e: (order.get(e.get("commentatorPhase"), 9), e.get("id") or 0))]


def verdict(events: list[dict], team_id: int) -> list[str]:
    """What the game shows at the end of the match: the pundit's post-match lines, the highlight first and the tip
    last (``getPostMatchTop`` and ``getPostMatchTip`` of the site; pure)."""
    return [e["text"] for e in sorted(events, key=lambda e: e.get("id") or 0)
            if e.get("commentatorPhase") == POST_MATCH and e.get("commentatorType") == PUNDIT
            and e.get("teamId") == team_id and e.get("text")]


def record(match: dict, team: dict, names: dict, events: list[dict]) -> dict:
    """One match's report as logged (pure)."""
    home = match["homeTeamId"] == team["id"]
    other = match["awayTeamId"] if home else match["homeTeamId"]
    goals = (match.get("homeGoals"), match.get("awayGoals"))
    return {"clube": team.get("name"), "liga": team["leagueId"], "equipa": team["id"], "semana": match["weekNr"],
            "jogo": match["matchId"], "tipo": TYPES.get(match.get("matchType"), f"tipo {match.get('matchType')}"),
            "casa": home, "adversario": names.get(other, other),
            "resultado": f"{goals[0]}-{goals[1]}" if home else f"{goals[1]}-{goals[0]}",
            "veredito": verdict(events, team["id"]), "comentarios": comments(events, team["id"])}


def save_reports(client=None, log=print, now: float | None = None) -> int:
    """Keep the report of every played match of the owner's clubs not kept yet. Returns how many were kept."""
    from osmbot.game.client import OsmClient
    from osmbot.game.clubinfo import FIXTURES_FOR, _cached, _list
    from osmbot.game.trainings import _teams

    client = client or OsmClient()
    now = now or time.time()
    data = _load()
    kept = list(data.get("guardados") or [])
    waiting = {k: v for k, v in (data.get("espera") or {}).items() if now - v < RETRY}
    saved = 0
    for _, team, base in _teams(client):
        league = f"leagues/{team['leagueId']}"
        matches = _cached(("matches", league), FIXTURES_FOR, lambda: _list(client, f"{league}/matches/filter"))
        todo = pending(matches, team["leagueId"], team["id"], set(kept), waiting, now)
        if not todo:
            continue
        names = {t["id"]: t["name"] for t in _cached(("teams", league), FIXTURES_FOR, lambda: _list(client, f"{league}/teams"))}
        for match in sorted(todo, key=lambda m: (m["weekNr"], m["matchId"])):
            status, events = client.get(f"{base}/matches/{match['matchId']}/{match['weekNr']}/commentatorevents")
            if status != 200 or not isinstance(events, list) or not events:
                waiting[key(team["leagueId"], team["id"], match)] = now  # not out yet: ask again later
                continue
            line = record(match, team, names, events)
            logs.record("relatorios", line)
            if line["veredito"]:
                log(f"Relatório: {line['clube']} {line['resultado']} {line['adversario']} ({line['tipo']}): "
                    + " · ".join(line["veredito"]))
            kept.append(key(team["leagueId"], team["id"], match))
            saved += 1
    data.update(guardados=kept[-KEEP:], espera=waiting)
    _save(data)
    return saved
