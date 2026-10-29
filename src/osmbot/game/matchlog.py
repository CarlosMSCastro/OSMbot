"""The matches, logged to study the game (owner, 2026-10-12: "regista tudo"; D-041, D-044). Reads only.

After each round of a league, one line per league or cup match in ``logs/<machine>/jogos/``: the result, the
referee and his strictness, both clubs' places, squad value and best-eleven rating, and every player's grade and
goals in that match (``lastPlayerGrade``, ``goalsLastMatch``). The owner's matches carry more: his tactics as they
were just before the match and, when the analyst's report could be read, the opponent's (other clubs' tactics are
refused by the game, 403). Reads: ``matches/filter``, ``teams``, ``referees``, each club's ``players``,
``teamtactics`` and ``spyresults`` (v1.1; DISCOVERY.md section 3). State in ``~/.osmbot/jogos.json``.

The match itself (D-044, as the game's Results page shows it): the game's strength of each side in that match,
formations and statistics (``matchData`` of ``matches/filter``), who played with his grade (``playergrades``) and
every event by minute (``matches/{n}/events/{week}``). Once per league, every match of the season so far too (the
game keeps them all); a match already logged in full by any PC (``logs/*/jogos``) is not read again. The players'
ratings are the ones at logging time (the game gives no older ones).
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from osmbot import logs

FILE = Path.home() / ".osmbot" / "jogos.json"
API_V11 = "https://web-api.onlinesoccermanager.com/api/v1.1"  # the analyst's report is v1.1 only (v1 gives 404)
LEAGUE_MATCH, CUP_MATCH, FRIENDLY_MATCH = 0, 1, 2  # matchType (1 = cup: hypothesis; 3 seen too, meaning unknown)
TYPES = {LEAGUE_MATCH: "liga", CUP_MATCH: "taça"}
ELEVEN = 11
EVENTS = {0: "golo", 10: "golo de penálti", 11: "golo", 12: "golo", 21: "golo", 1: "amarelo", 2: "vermelho",
          13: "vermelho", 3: "lesão", 6: "ocasião falhada", 8: "ocasião falhada", 9: "ocasião falhada",
          7: "penálti falhado", 18: "substituição", 19: "VAR", 20: "VAR", 16: "penálti marcado (desempate)",
          17: "penálti falhado (desempate)"}  # eventNr (DISCOVERY.md; 10-12 and 21 told apart only by the game)
STATS = (("forca_ataque", "Att"), ("forca_defesa", "Def"), ("forca", "Ovr"), ("remates", "Chances"),
         ("posse", "Possession"), ("cantos", "Corners"), ("faltas", "Fouls"), ("conversao", "Accuracy"),
         ("estagio", "Camp"))
PAUSE = 0.3  # seconds between the reads of the season so far (a few hundred, once per league)


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


def note_prematch(client, base: str, week: int, now: float | None = None, opponent: int | None = None) -> None:
    """Keep the owner's tactics (and the analyst's report on the ``opponent``, if the game gives it) as they are
    before the match: read on every pass of the last hours, so the last read is the one the match was played with.
    The game gives a report per club analysed in the round (``teamId``; the analyst also goes round the league)."""
    data = _load()
    entry = {"semana": week, "lido": now or time.time(), "tatica": _body(client, f"{base}/teamtactics"),
             "especialistas": _body(client, f"{base}/specialists")}  # places of the eleven (corners ≠ free kicks, THEORY.md 4)
    report = _body(client, f"{API_V11}/{base}/spyresults")
    if isinstance(report, list) and opponent is not None:
        report = [r for r in report if isinstance(r, dict) and r.get("teamId") == opponent]
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


def match_detail(match: dict, grades: list[dict], events: list[dict], people: dict) -> dict:
    """The match as the game's Results page shows it (pure): per side the game's strength in that match, the
    formation, the statistics and who played (starters 1-11, then the substitutes who came on), plus the events by
    minute. ``grades``: ``playergrades`` rows of both clubs; ``people``: players by id (name, position, ratings)."""
    data = match.get("matchData") or {}
    sides = {match["homeTeamId"]: "casa", match["awayTeamId"]: "fora"}
    name = lambda pid: (people.get(pid) or {}).get("name") or pid
    detail = {"estatisticas": {}, "onze": {}}
    for side, key in (("casa", "home"), ("fora", "away")):
        stats = {label: data.get(key + field) for label, field in STATS}
        stats["formacao"] = f"{data.get(key + 'Formation') or ''}{data.get(key + 'FormationDetail') or ''}" or None
        detail["estatisticas"][side] = stats
    detail["estatisticas"]["zonas"] = {"esquerda": data.get("fieldBalanceLeft"), "meio": data.get("fieldBalanceMiddle"),
                                       "direita": data.get("fieldBalanceRight")}
    detail["estatisticas"]["homem_do_jogo"] = name(data["manOfTheMatchPlayerId"]) if data.get("manOfTheMatchPlayerId") else None
    for team, side in sides.items():
        rows = sorted((g for g in grades if g.get("teamId") == team), key=lambda g: g.get("lineup") or 99)
        detail["onze"][side] = [{"id": g.get("playerId"), "nome": name(g.get("playerId")), "lineup": g.get("lineup"),
                                 "nota": g.get("grade"),
                                 **{k: (people.get(g.get("playerId")) or {}).get(k) for k in ("position", "statAtt", "statDef", "statOvr")}}
                                for g in rows]
    detail["eventos"] = [{"min": e.get("minute"), "equipa": sides.get(e.get("teamId")),
                          "tipo": EVENTS.get(e.get("eventNr"), f"evento {e.get('eventNr')}"), "n": e.get("eventNr"),
                          "jogador": (e.get("player") or {}).get("name"),
                          "outro": (e.get("involvedPlayer") or {}).get("name"), "causa": e.get("causeName")}
                         for e in sorted(events, key=lambda e: (e.get("minute") or 0, e.get("id") or 0))]
    return detail


def detailed_ids(repo: Path | None = None) -> set[str]:
    """The matches some PC already logged in full (``logs/*/jogos``), so the season is read once, not per PC."""
    repo = repo or logs.repo_folder()
    found: set[str] = set()
    if repo is None:
        return found
    for path in (repo / "logs").glob("*/jogos/*.jsonl"):
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                if '"eventos"' in line:
                    found.add(json.loads(line).get("jogo"))
        except (OSError, ValueError):
            continue
    return found


def _people(players: dict[int, list[dict]], events: list[dict]) -> dict:
    people = {p["id"]: p for squad_ in players.values() for p in squad_ or [] if p.get("id")}
    for e in events:
        for key in ("player", "involvedPlayer"):
            p = e.get(key) or {}
            if p.get("id"):
                people.setdefault(p["id"], p)
    return people


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
    logged = detailed_ids()
    matches = [m for m in matches if m["id"] not in logged]  # another PC already logged them in full
    playing = {m["homeTeamId"] for m in matches} | {m["awayTeamId"] for m in matches}
    players = {t: _body(client, f"{league}/teams/{t}/players") or [] for t in sorted(playing)}
    squads = {t: squad(players[t], t in my_teams) for t in sorted(playing)}
    grades = [g for t in sorted(playing) for g in _body(client, f"{league}/teams/{t}/playergrades/{week}") or []]
    before = data.get("antes") or {}
    for match in matches:
        line = match_line(match, names, ranks, referees, squads, set(my_teams))
        events = _body(client, f"{league}/matches/{match.get('matchId')}/events/{week}") or []
        if events or match.get("matchData"):
            line.update(match_detail(match, [g for g in grades if g.get("matchId") == match.get("matchId")], events,
                                     _people(players, events)))
        for team in (match["homeTeamId"], match["awayTeamId"]):
            if team not in my_teams:
                continue
            base = f"{league}/teams/{team}"
            kept = before.get(base) or {}
            same = kept.get("semana") == week - 1 or kept.get("semana") == week  # read during the round just played
            line["tatica"] = kept.get("tatica") if same and kept.get("tatica") else _body(client, f"{base}/teamtactics")
            line["tatica_lida"] = "antes do jogo" if same and kept.get("tatica") else "depois do jogo"
            line["analise"] = kept.get("analise") if same else None
            line["especialistas"] = kept.get("especialistas") if same else None
            mine_home = team == match["homeTeamId"]
            score = f"{match['homeGoals']}-{match['awayGoals']}" if mine_home else f"{match['awayGoals']}-{match['homeGoals']}"
            other = match["awayTeamId"] if mine_home else match["homeTeamId"]
            graded = [p for p in squads[team]["jogadores"] if 1 <= (p.get("lineup") or 0) <= ELEVEN and p.get("lastPlayerGrade")]
            top = max(graded, key=lambda p: p["lastPlayerGrade"], default=None)
            referee = line["arbitro"]
            strength = {k: (v or {}).get("forca") for k, v in line.get("estatisticas", {}).items() if k in ("casa", "fora")}
            ours, theirs = (strength.get("casa"), strength.get("fora")) if mine_home else (strength.get("fora"), strength.get("casa"))
            log(f"Jogo: {names.get(team, team)} {score} {names.get(other, other)} ({'casa' if mine_home else 'fora'})"
                + (f" · força do jogo {ours}/{theirs}" if ours and theirs else "")
                + (f" · árbitro rigor {referee['rigor']}" if referee.get("rigor") is not None else "")
                + (f" · melhor nota {top['name']} {top['lastPlayerGrade']}" if top else ""))
        logs.record("jogos", line)
    done[str(league_id)] = week
    _save(data)
    return len(matches)


def log_history(client, league_id: int, my_teams: dict[int, dict], log, sleep=time.sleep) -> int:
    """Once per league: every match of the season so far not yet logged in full by any PC, with the match itself
    (``match_detail``: the game keeps every week's grades and events). Marked "histórico". The reads are spaced out."""
    league = f"leagues/{league_id}"
    data = _load()
    if str(league_id) in data.get("historico_completo", {}):
        return 0
    week = (_body(client, league) or {}).get("weekNr")
    if week is None:
        return 0
    logged = detailed_ids()
    matches = [m for m in _body(client, f"{league}/matches/filter") or []
               if m.get("matchType") in (LEAGUE_MATCH, CUP_MATCH) and m["id"] not in logged
               and (m.get("matchData") or (m.get("weekNr", week) < week and m.get("homeGoals") is not None))]
    teams = _body(client, f"{league}/teams") or []
    names = {t["id"]: t["name"] for t in teams}
    referees = {r["id"]: r for r in _body(client, f"{league}/referees") or []}
    playing = sorted({m["homeTeamId"] for m in matches} | {m["awayTeamId"] for m in matches})
    players, grades = {}, []
    for team in playing:
        players[team] = _body(client, f"{league}/teams/{team}/players") or []
        grades += _body(client, f"{league}/teams/{team}/playergrades/") or []
        sleep(PAUSE)
    for match in sorted(matches, key=lambda m: (m["weekNr"], str(m["id"]))):
        line = {**match_line(match, names, {}, referees, {}, set(my_teams)), "historico": True}
        events = _body(client, f"{league}/matches/{match.get('matchId')}/events/{match['weekNr']}") or []
        sleep(PAUSE)
        if events or match.get("matchData"):
            same = [g for g in grades if g.get("weekNr") == match["weekNr"] and g.get("matchId") == match.get("matchId")]
            line.update(match_detail(match, same, events, _people(players, events)))
        logs.record("jogos", line)
    data.setdefault("historico_completo", {})[str(league_id)] = week
    _save(data)
    log(f"Registo dos jogos: época da liga {league_id} guardada ({len(matches)} jogos com onze, notas e eventos)")
    return len(matches)


def log_rounds(client=None, log=print) -> int:
    """Every league of the owner's clubs: the round just played first (with the squads and the owner's tactics),
    then the rest of the season once (see ``log_round`` and ``log_history``)."""
    from osmbot.game.client import OsmClient
    from osmbot.game.trainings import _teams

    client = client or OsmClient()
    leagues: dict[int, dict[int, dict]] = {}
    for _, team, _ in _teams(client):
        leagues.setdefault(team["leagueId"], {})[team["id"]] = team
    return sum(log_round(client, league, teams, log) + log_history(client, league, teams, log)
               for league, teams in leagues.items())
