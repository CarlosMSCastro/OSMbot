"""The matches, logged to study the game (owner, 2026-10-12: "regista tudo"; D-041). Reads only.

After each round of a league, one line per league or cup match in ``logs/<machine>/jogos/``: the result, the
referee and his strictness, both clubs' places, squad value and best-eleven rating, and every player's grade and
goals in that match (``lastPlayerGrade``, ``goalsLastMatch``). The owner's matches carry more: his tactics as they
were just before the match and, when the analyst's report could be read, the opponent's (other clubs' tactics are
refused by the game, 403). Reads: ``matches/filter``, ``teams``, ``referees``, each club's ``players``,
``teamtactics`` and ``spyresults`` (DISCOVERY.md section 3). State in ``~/.osmbot/jogos.json``.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from osmbot import logs

FILE = Path.home() / ".osmbot" / "jogos.json"
LEAGUE_MATCH, CUP_MATCH, FRIENDLY_MATCH = 0, 1, 2  # matchType (1 = cup: hypothesis; 3 seen too, meaning unknown)
TYPES = {LEAGUE_MATCH: "liga", CUP_MATCH: "taça"}
ELEVEN = 11


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


def _body(client, path: str):
    status, body = client.get(path)
    return body if status == 200 else None


def note_prematch(client, base: str, week: int, now: float | None = None) -> None:
    """Keep the owner's tactics (and the analyst's report, if the game gives it) as they are before the match: read
    on every pass of the last hours, so the last read is the one the match was played with."""
    data = _load()
    entry = {"semana": week, "lido": now or time.time(), "tatica": _body(client, f"{base}/teamtactics")}
    report = _body(client, f"{base}/spyresults")
    if report:
        entry["analise"] = report
    elif (data.get("antes", {}).get(base) or {}).get("semana") == week:
        entry["analise"] = data["antes"][base].get("analise")  # the report may go once read: keep the earlier one
    data.setdefault("antes", {})[base] = entry
    _save(data)


def squad(players: list[dict], mine: bool) -> dict:
    """A club's squad as logged: value, the best eleven's average rating, and every player (pure)."""
    best = sorted((p.get("statOvr") or 0 for p in players), reverse=True)[:ELEVEN]
    keep = (("id", "name", "position", "specificPosition", "age", "statAtt", "statDef", "statOvr", "value", "lineup",
             "lastPlayerGrade", "goalsLastMatch", "goals", "assists", "matchesPlayed", "yellowCards", "unavailable",
             "fitness", "morale", "trainingProgress") if mine else  # the other clubs: the essentials (the log is in the repo)
            ("name", "position", "age", "statAtt", "statDef", "statOvr", "lastPlayerGrade", "goalsLastMatch"))
    return {"valor": sum(p.get("value") or 0 for p in players),
            "media_11": round(sum(best) / len(best), 1) if best else None,
            "jogadores": [{k: p.get(k) for k in keep} for p in players]}


def match_line(match: dict, names: dict, ranks: dict, referees: dict, squads: dict, mine: set[int]) -> dict:
    """One match as logged (pure)."""
    referee = referees.get(match.get("refereeId")) or {}
    side = lambda team: {"id": team, "nome": names.get(team), "lugar": ranks.get(team, {}).get("ranking"),
                         "lugar_antes": ranks.get(team, {}).get("previousRanking"), "meu": team in mine,
                         **(squads.get(team) or {})}
    return {"jogo": match["id"], "semana": match["weekNr"], "tipo": TYPES.get(match["matchType"], f"tipo {match['matchType']}"),
            "resultado": f"{match['homeGoals']}-{match['awayGoals']}", "vencedor": match.get("winnerTeamId"),
            "prolongamento": match.get("isExtraTimePlayed"), "penaltis": match.get("isDecidedByPenalties"),
            "campo_neutro": match.get("isPlayedOnNeutralGround"),
            "arbitro": {"id": match.get("refereeId"), "nome": referee.get("name"), "rigor": referee.get("strictness")},
            "casa": side(match["homeTeamId"]), "fora": side(match["awayTeamId"])}


def log_round(client, league_id: int, my_teams: dict[int, dict], log, now: float | None = None) -> int:
    """Log the round just played in one league, once (the league's ``weekNr`` moved on). Returns matches logged."""
    league = f"leagues/{league_id}"
    week = (_body(client, league) or {}).get("weekNr")
    data = _load()
    done = data.setdefault("ligas", {})
    if week is None or done.get(str(league_id)) == week:
        return 0
    matches = [m for m in _body(client, f"{league}/matches/filter") or []
               if m.get("weekNr") == week and m.get("matchType") in (LEAGUE_MATCH, CUP_MATCH) and m.get("homeGoals") is not None]
    teams = _body(client, f"{league}/teams") or []
    names = {t["id"]: t["name"] for t in teams}
    ranks = {t["id"]: t for t in teams}
    referees = {r["id"]: r for r in _body(client, f"{league}/referees") or []}
    playing = {m["homeTeamId"] for m in matches} | {m["awayTeamId"] for m in matches}
    squads = {t: squad(_body(client, f"{league}/teams/{t}/players") or [], t in my_teams) for t in sorted(playing)}
    before = data.get("antes") or {}
    for match in matches:
        line = match_line(match, names, ranks, referees, squads, set(my_teams))
        for team in (match["homeTeamId"], match["awayTeamId"]):
            if team not in my_teams:
                continue
            base = f"{league}/teams/{team}"
            kept = before.get(base) or {}
            same = kept.get("semana") == week - 1 or kept.get("semana") == week  # read during the round just played
            line["tatica"] = kept.get("tatica") if same and kept.get("tatica") else _body(client, f"{base}/teamtactics")
            line["tatica_lida"] = "antes do jogo" if same and kept.get("tatica") else "depois do jogo"
            line["analise"] = kept.get("analise") if same else None
            mine_home = team == match["homeTeamId"]
            score = f"{match['homeGoals']}-{match['awayGoals']}" if mine_home else f"{match['awayGoals']}-{match['homeGoals']}"
            other = match["awayTeamId"] if mine_home else match["homeTeamId"]
            graded = [p for p in squads[team]["jogadores"] if 1 <= (p.get("lineup") or 0) <= ELEVEN and p.get("lastPlayerGrade")]
            top = max(graded, key=lambda p: p["lastPlayerGrade"], default=None)
            referee = line["arbitro"]
            log(f"Jogo: {names.get(team, team)} {score} {names.get(other, other)} ({'casa' if mine_home else 'fora'})"
                + (f" · árbitro rigor {referee['rigor']}" if referee.get("rigor") is not None else "")
                + (f" · melhor nota {top['name']} {top['lastPlayerGrade']}" if top else ""))
        logs.record("jogos", line)
    done[str(league_id)] = week
    _save(data)
    return len(matches)


def log_history(client, league_id: int, my_teams: dict[int, dict], log) -> int:
    """Once per league: every match already played before the current round (the season so far), with the result and
    the referee only; the players' grades of old matches are gone (the game keeps only the last). Marked "histórico"."""
    league = f"leagues/{league_id}"
    data = _load()
    if str(league_id) in data.get("historico", {}):
        return 0
    week = (_body(client, league) or {}).get("weekNr")
    if week is None:
        return 0
    matches = [m for m in _body(client, f"{league}/matches/filter") or []
               if m.get("matchType") != FRIENDLY_MATCH and m.get("weekNr", week) < week and m.get("homeGoals") is not None]
    teams = _body(client, f"{league}/teams") or []
    names = {t["id"]: t["name"] for t in teams}
    referees = {r["id"]: r for r in _body(client, f"{league}/referees") or []}
    for match in sorted(matches, key=lambda m: (m["weekNr"], str(m["id"]))):
        line = match_line(match, names, {}, referees, {}, set(my_teams))
        logs.record("jogos", {**line, "historico": True})
    data.setdefault("historico", {})[str(league_id)] = week
    _save(data)
    log(f"Registo dos jogos: histórico da liga {league_id} guardado ({len(matches)} jogos até à jornada {week - 1})")
    return len(matches)


def log_rounds(client=None, log=print) -> int:
    """Every league of the owner's clubs (see ``log_round``)."""
    from osmbot.game.client import OsmClient
    from osmbot.game.trainings import _teams

    client = client or OsmClient()
    leagues: dict[int, dict[int, dict]] = {}
    for _, team, _ in _teams(client):
        leagues.setdefault(team["leagueId"], {})[team["id"]] = team
    return sum(log_history(client, league, teams, log) + log_round(client, league, teams, log)
               for league, teams in leagues.items())
