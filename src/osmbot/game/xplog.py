"""The manager's experience ("skill rating", the XP bar after each match), logged per match (owner, 2026-10-17:
"estou stuck nos 397-398k, não entendo porque não subo"). Reads only.

After each round of a league where the owner has a club, one line per owner's match in ``logs/<machine>/xp/``:
the result, whether the opponent is a manager (and his rating) or the CPU, the account's rating, the balance in that
league (``leagueSkillRating``, which goes below zero: losses take points) and how much both moved since the last
read, plus the bonuses the game lists for that round (``user/skillratingbonuses``). Reads: ``user/accounts``,
``user/skillratingbonuses``, ``tiers``, the league, its ``matches/filter`` and ``managers`` (DISCOVERY.md section 3).
State in ``~/.osmbot/xp.json``. The opponent's rating is the one after the match (the game gives no older one).
"""
from __future__ import annotations

import json
from pathlib import Path

from osmbot import logs

FILE = Path.home() / ".osmbot" / "xp.json"
MATCH_TYPES = {0: "liga", 1: "taça"}  # as in matchlog: friendlies give no rating (hypothesis, not logged)
BONUS_TYPES = {0: "jogo", 1: "adversário", 2: "equipa", 3: "fim de época (liga)", 4: "fim de época (taça)"}  # enums.js


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


def tier(rating: int | None, tiers: list[dict]) -> dict | None:
    """The level the rating is in, with how much is left to the next one (pure)."""
    if rating is None:
        return None
    for row in sorted(tiers or [], key=lambda t: t.get("startRange", 0)):
        if row.get("startRange", 0) <= rating <= row.get("endRange", 0):
            return {"nivel": row.get("level"), "falta": row["endRange"] + 1 - rating}
    return None


def result(match: dict, team: int) -> str:
    """V/E/D from the owner's side (pure); a draw decided on penalties counts by the winner."""
    home = match["homeTeamId"] == team
    ours, theirs = (match["homeGoals"], match["awayGoals"]) if home else (match["awayGoals"], match["homeGoals"])
    if ours != theirs:
        return "V" if ours > theirs else "D"
    winner = match.get("winnerTeamId")
    if match.get("isDecidedByPenalties") and winner not in (None, 0, -1):
        return "V" if winner == team else "D"
    return "E"


def match_line(match: dict, team: int, slot: str, names: dict, managers: dict, bonuses: list[dict],
               rating: int | None, before: dict) -> dict:
    """One owner's match as logged (pure). ``managers``: the league's human managers by team id; ``before``: the
    state of the last read (``total``, and per league ``semana`` and ``liga``)."""
    home = match["homeTeamId"] == team
    other = match["awayTeamId"] if home else match["homeTeamId"]
    rival = managers.get(other)
    mine = managers.get(team) or {}
    league = mine.get("leagueSkillRating")
    kept = (before.get("ligas") or {}).get(str(match["leagueId"])) or {}
    ours, theirs = (match["homeGoals"], match["awayGoals"]) if home else (match["awayGoals"], match["homeGoals"])
    delta = lambda now, then: now - then if now is not None and then is not None else None
    return {"jogo": match["id"], "liga": match["leagueId"], "semana": match["weekNr"], "slot": slot,
            "tipo": MATCH_TYPES.get(match.get("matchType"), f"tipo {match.get('matchType')}"),
            "clube": names.get(team), "adversario": names.get(other), "casa": home,
            "resultado": result(match, team), "golos": f"{ours}-{theirs}",
            "adversario_humano": rival is not None,
            "rating_adversario": (rival or {}).get("skillRating"),
            "rating": rating, "rating_variacao": delta(rating, before.get("total")),
            "liga_rating": league, "liga_variacao": delta(league, kept.get("liga")),
            "jornadas": match["weekNr"] - kept["semana"] if kept.get("semana") is not None else None,
            "bonus": [{"tipo": BONUS_TYPES.get(b.get("type"), f"tipo {b.get('type')}"), "valor": b.get("amount")}
                      for b in bonuses
                      if b.get("leagueId") == match["leagueId"] and b.get("weekNr") == match["weekNr"]]}


def _n(value: int) -> str:
    return f"{value:,}".replace(",", " ")


def say(line: dict, level: dict | None) -> str:
    """The line for the bot's log (pure)."""
    change = line["liga_variacao"]
    rival = f"treinador {_n(line['rating_adversario'])}" if line["adversario_humano"] else "CPU"
    bonus = ", ".join(f"{b['tipo']} +{b['valor']}" for b in line["bonus"])
    return (f"XP: {line['clube']} {line['golos']} {line['adversario']} ({line['resultado']}, {rival})"
            + (f" · {change:+d} nesta liga" if change is not None else " · 1.ª leitura nesta liga")
            + (f" ({bonus})" if bonus else "")
            + (f" · total {_n(line['rating'])}" if line["rating"] is not None else "")
            + (f" · nível {level['nivel']}, faltam {_n(level['falta'])}" if level else ""))


def log_xp(client=None, log=print) -> int:
    """Every league of the owner's clubs: the owner's matches of the round just played, once (the league's
    ``weekNr`` moved on). Returns the matches logged."""
    from osmbot.game.client import OsmClient

    client = client or OsmClient()
    account = _body(client, "user/accounts") or {}
    rating = account.get("skillRating")
    data = _load()
    done = data.setdefault("ligas", {})
    bonuses = tiers = None
    count = 0
    for slot, content in sorted((account.get("teamSlots") or {}).items()):
        team = (content or {}).get("team")
        if not team:
            continue
        league_id, team_id = team["leagueId"], team["id"]
        week = (_body(client, f"leagues/{league_id}") or {}).get("weekNr")
        kept = done.get(str(league_id)) or {}
        if week is None or kept.get("semana") == week:
            continue
        matches = [m for m in _body(client, f"leagues/{league_id}/matches/filter") or []
                   if m.get("weekNr") == week and m.get("matchType") in MATCH_TYPES and m.get("homeGoals") is not None
                   and team_id in (m["homeTeamId"], m["awayTeamId"])]
        managers = {m["teamId"]: m for m in _body(client, f"leagues/{league_id}/managers") or [] if m.get("teamId")}
        if not matches:  # nothing played this round (pre-season): keep the balance, nothing to log
            done[str(league_id)] = {"semana": week, "liga": (managers.get(team_id) or {}).get("leagueSkillRating")}
            continue
        if bonuses is None:
            bonuses = _body(client, "user/skillratingbonuses") or []
            tiers = _body(client, "tiers") or []
        names = {t["id"]: t["name"] for t in _body(client, f"leagues/{league_id}/teams") or []}
        for match in matches:
            line = match_line(match, team_id, slot, names, managers, bonuses, rating, data)
            line["nivel"] = tier(rating, tiers)
            logs.record("xp", line)
            log(say(line, line["nivel"]))
            count += 1
        done[str(league_id)] = {"semana": week, "liga": (managers.get(team_id) or {}).get("leagueSkillRating")}
    if rating is not None:
        data["total"] = rating
    _save(data)
    return count


def read_lines(repo: Path | None = None) -> list[dict]:
    """Every XP line of every PC (``logs/*/xp``), oldest first, each match once."""
    repo = repo or logs.repo_folder()
    seen: dict[str, dict] = {}
    if repo is None:
        return []
    for path in sorted((repo / "logs").glob("*/xp/*.jsonl")):
        try:
            for raw in path.read_text(encoding="utf-8").splitlines():
                line = json.loads(raw)
                seen.setdefault(line.get("jogo"), line)
        except (OSError, ValueError):
            continue
    return sorted(seen.values(), key=lambda line: line.get("t", 0))


def summary(lines: list[dict]) -> list[str]:
    """The study (pure): one row per match, then the average change in the league by result and opponent. Only
    matches read one round after the last (``jornadas`` 1) count in the averages."""
    rows = []
    groups: dict[tuple[str, str], list[int]] = {}
    for line in lines:
        rival = "humano" if line.get("adversario_humano") else "CPU"
        change = line.get("liga_variacao")
        bonus = " ".join(f"{b['tipo']}+{b['valor']}" for b in line.get("bonus") or [])
        rows.append(f"{line.get('semana'):>3} {line.get('clube') or '?':<22} {line.get('golos'):>5} {line.get('resultado')}"
                    f" {rival:<6} {line.get('rating_adversario') or '':>7} {'' if change is None else f'{change:+d}':>6}"
                    f" {line.get('rating') or '':>7} {bonus}")
        if change is not None and line.get("jornadas") == 1:
            groups.setdefault((line.get("resultado"), rival), []).append(change)
    out = ["Sem. Clube                  Golos R Adv.   Rating  Liga±  Total   Bónus"] + rows
    if groups:
        out.append("")
        out.append("Média da variação na liga por resultado e adversário:")
        for (res, rival), values in sorted(groups.items()):
            out.append(f"  {res} vs {rival:<6} {sum(values) / len(values):+.0f} ({len(values)} jogos)")
    return out


def run_report() -> None:
    lines = read_lines()
    if not lines:
        raise SystemExit("Ainda não há registo da XP (logs/<PC>/xp/). O bot regista depois de cada jornada.")
    print("\n".join(summary(lines)))
