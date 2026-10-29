"""The theory's measurable rules checked against the match records (`logs/*/jogos`; docs/VERIFICACAO.md, owner
2026-10-28: "uma rotina de ir verificando se temos alguma coisa teórica no código que não faça sentido baseado no
histórico real"). Pure: each check takes the records and returns a ``Result``; reading the logs is
``tools/verificar_teoria.py``'s job.

Verdicts: "bate" (the records agree with the rule), "não bate" (they do not: bring it to the owner), "amostra curta"
(not enough matches yet to say), "pronto a decidir" (a rule still to be set, with enough matches now).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from statistics import mean
from typing import Callable, Iterable

AGREES, DISAGREES, SHORT, READY = "bate", "não bate", "amostra curta", "pronto a decidir"
POINTS = {"W": 3, "D": 1, "L": 0}


@dataclass(frozen=True)
class Result:
    key: str  # the check's id in docs/VERIFICACAO.md
    rule: str  # the rule as THEORY.md says it, short
    measured: str  # what the records say
    sample: int
    verdict: str


def unique_matches(records: Iterable[dict]) -> list[dict]:
    """One record per match (several PCs log the same one): the fullest."""
    best: dict = {}
    for record in records:
        key = record.get("jogo")
        if key and (key not in best or len(str(record)) > len(str(best[key]))):
            best[key] = record
    return list(best.values())


def _league(matches: list[dict]) -> list[dict]:
    """League matches with both sides' strength, not on neutral ground."""
    return [m for m in matches if m.get("tipo") == "liga" and not m.get("campo_neutro")
            and ((m.get("estatisticas") or {}).get("casa") or {}).get("forca")
            and ((m.get("estatisticas") or {}).get("fora") or {}).get("forca")]


def _goals(match: dict) -> tuple[int, int]:
    home, away = (int(x) for x in match["resultado"].split("-"))
    return home, away


def _outcome(match: dict, side: str) -> str:
    """W/D/L for ``side`` ("casa" or "fora")."""
    home, away = _goals(match)
    mine, theirs = (home, away) if side == "casa" else (away, home)
    return "W" if mine > theirs else "L" if mine < theirs else "D"


def _edge(match: dict, side: str) -> float:
    """How much stronger ``side`` was, in % of the other's strength (negative: weaker)."""
    stats = match["estatisticas"]
    other = "fora" if side == "casa" else "casa"
    return (stats[side]["forca"] - stats[other]["forca"]) / stats[other]["forca"] * 100


def _own(matches: list[dict]) -> list[tuple[dict, str]]:
    """The owner's league matches, each with his side."""
    return [(m, side) for m in _league(matches) for side in ("casa", "fora") if (m.get(side) or {}).get("meu")]


def _ppg(pairs: list[tuple[dict, str]]) -> float:
    return mean(POINTS[_outcome(m, side)] for m, side in pairs) if pairs else 0.0


def home_advantage(matches: list[dict], rule: float = 5.0, margin: float = 3.0, minimum: int = 150) -> Result:
    """THEORY.md section 1 [S]: home is worth ~5 % of strength. Measured as the strength the away side needs to be
    even: a straight line through (home's edge, result) in matches within 15 %, where it crosses an even result."""
    near = [(_edge(m, "casa"), {"W": 1, "D": 0, "L": -1}[_outcome(m, "casa")]) for m in _league(matches)]
    near = [(x, y) for x, y in near if abs(x) <= 15]
    if len(near) < minimum:
        return Result("casa", "Casa vale ~5 % de força", f"{len(near)} jogos", len(near), SHORT)
    xs, ys = [x for x, _ in near], [y for _, y in near]
    mx, my = mean(xs), mean(ys)
    slope = sum((x - mx) * (y - my) for x, y in near) / sum((x - mx) ** 2 for x in xs)
    worth = (my - slope * mx) / slope if slope > 0 else float("inf")
    verdict = AGREES if abs(worth - rule) <= margin else DISAGREES
    return Result("casa", "Casa vale ~5 % de força", f"casa vale ~{worth:.1f} % de força", len(near), verdict)


def clearly_stronger(matches: list[dict], cut: float = 12.0, minimum: int = 40) -> Result:
    """D-074: "clearly stronger" = more than 12 %: from there the stronger side loses ~1 in 8; below, ~1 in 4."""
    rows = []
    for m in _league(matches):
        edge = _edge(m, "casa")
        side = "casa" if edge >= 0 else "fora"
        rows.append((abs(edge), _outcome(m, side)))
    above = [o for e, o in rows if e > cut]
    below = [o for e, o in rows if 5 < e <= cut]
    if len(above) < minimum or len(below) < minimum:
        return Result("12pc", "Claramente mais forte = > 12 %", f"{len(below)} jogos 5–12 %, {len(above)} acima", len(rows), SHORT)
    lost_above, lost_below = (sum(o == "L" for o in group) / len(group) * 100 for group in (above, below))
    verdict = AGREES if lost_above <= 15 and lost_below > lost_above + 5 else DISAGREES
    return Result("12pc", "Claramente mais forte = > 12 %",
                  f"o mais forte perde {lost_below:.0f} % entre 5 e 12 % e {lost_above:.0f} % acima de 12 %", len(rows), verdict)


def away_433(matches: list[dict], minimum: int = 10) -> Result:
    """THEORY.md section 1 [S] (owner, 2026-10-25): away, the 4-3-3 B rather than the A (few matches when measured)."""
    away = [(m, s) for m, s in _own(matches) if s == "fora" and _edge(m, s) <= 12]
    a = [(m, s) for m, s in away if (m["estatisticas"][s].get("formacao") or "") == "433A"]
    b = [(m, s) for m, s in away if (m["estatisticas"][s].get("formacao") or "") == "433B"]
    measured = f"fora, até 12 % mais forte: B {_ppg(b):.2f} pts/jogo ({len(b)}), A {_ppg(a):.2f} ({len(a)})"
    if len(a) < minimum or len(b) < minimum:
        return Result("433fora", "Fora: 4-3-3 B melhor do que o A", measured, len(a) + len(b), SHORT)
    return Result("433fora", "Fora: 4-3-3 B melhor do que o A", measured, len(a) + len(b), AGREES if _ppg(b) >= _ppg(a) else DISAGREES)


def fatigue(matches: list[dict], rule: float = -4.0, margin: float = 1.0, minimum: int = 50) -> Result:
    """THEORY.md section 16: a starter loses ~4 of condition per match. Measured as it was (208 cases, 2026-10-22):
    the owner's players who started two rounds in a row of the same club (the condition as read for each match)."""
    by_club: dict = {}
    for m, side in _own(matches):
        by_club.setdefault(m[side]["id"], {})[m["semana"]] = m[side].get("jogadores") or []
    drops = []
    for rounds in by_club.values():
        for week, squad in rounds.items():
            following = {p.get("id"): p for p in rounds.get(week + 1, [])}
            for p in squad:
                after = following.get(p.get("id"))
                if (1 <= (p.get("lineup") or 0) <= 11 and after and 1 <= (after.get("lineup") or 0) <= 11  # starter in both
                        and p.get("fitness") is not None and after.get("fitness") is not None):
                    drops.append(after["fitness"] - p["fitness"])
    if len(drops) < minimum:
        return Result("cansaco", "Titular perde ~4 de condição por jogo", f"{len(drops)} casos", len(drops), SHORT)
    drop = mean(drops)
    return Result("cansaco", "Titular perde ~4 de condição por jogo", f"{drop:+.1f} por jogo", len(drops),
                  AGREES if abs(drop - rule) <= margin else DISAGREES)


def away_523(matches: list[dict], minimum: int = 15) -> Result:
    """OSMPro OSMPROworld point 2, to measure (owner, 2026-10-28): away, the 5-2-3 rather than the 4-3-3? Every club
    of the leagues (not only the owner's), away sides within 12 % of the home side's strength (not clearly
    stronger or weaker, THEORY.md section 1)."""
    groups: dict[str, list[tuple[dict, str]]] = {"433": [], "523": []}
    for m in _league(matches):
        form = (m["estatisticas"]["fora"].get("formacao") or "")[:3]
        if form in groups and abs(_edge(m, "fora")) <= 12:
            groups[form].append((m, "fora"))
    a, b = groups["433"], groups["523"]
    measured = f"fora, forças parecidas: 4-3-3 {_ppg(a):.2f} pts/jogo ({len(a)}), 5-2-3 {_ppg(b):.2f} ({len(b)})"
    return Result("523fora", "Fora: 4-3-3 (a regra) ou 5-2-3 (o autor)?", measured, len(a) + len(b),
                  READY if len(a) >= minimum and len(b) >= minimum else SHORT)


def against_stronger(matches: list[dict], minimum: int = 15) -> Result:
    """OSMPro OSMPROworld point 3, to measure (owner, 2026-10-28): against a stronger side, 5 defenders (the rule,
    THEORY.md section 1) or the 4-5-1 / 4-2-3-1 (the author, 2024-26)? Every club of the leagues, home or away, the
    side more than 3 % weaker."""
    five, four = [], []
    for m in _league(matches):
        for side in ("casa", "fora"):
            if _edge(m, side) >= -3:
                continue
            form = m["estatisticas"][side].get("formacao") or ""
            (five if form.startswith("5") else four if form[:3] == "451" else []).append((m, side))
    measured = f"contra mais forte: 5 defesas {_ppg(five):.2f} pts/jogo ({len(five)}), 4-5-1 {_ppg(four):.2f} ({len(four)})"
    return Result("451", "Contra mais forte: 5 defesas (a regra) ou 4-5-1 (o autor)?", measured, len(five) + len(four),
                  READY if len(five) >= minimum and len(four) >= minimum else SHORT)


def tempo_against_stronger(matches: list[dict], minimum: int = 8) -> Result:
    """OSMPro Táticas point 12, to measure (owner, 2026-10-28): 5 defenders against a stronger side with the tempo at
    60–80 (the rule) or below 60 (the game's help text: "not fast against a better side")."""
    pairs = [(m, s) for m, s in _own(matches) if m.get("tatica") and _edge(m, s) < 0
             and (m["estatisticas"][s].get("formacao") or "").startswith("5")]
    low = [(m, s) for m, s in pairs if (m["tatica"].get("tempo") or 0) < 60]
    rule = [(m, s) for m, s in pairs if 60 <= (m["tatica"].get("tempo") or 0) <= 80]
    measured = f"temporização 60–80: {_ppg(rule):.2f} pts/jogo ({len(rule)}); abaixo de 60: {_ppg(low):.2f} ({len(low)})"
    verdict = SHORT if len(low) < minimum or len(rule) < minimum else AGREES if _ppg(rule) >= _ppg(low) else DISAGREES
    return Result("tempo", "5 defesas contra mais forte: temporização 60–80", measured, len(pairs), verdict)


def tempo_by_strength(matches: list[dict], minimum: int = 8) -> Result:
    """OSMPro series point 4 with Táticas point 12 (owner, 2026-10-28): the tempo by the strength gap, in any
    formation: points per match with it below 60, at 60–80 (the rule) and above 80, stronger and weaker apart.
    "Pronto a decidir" once each side has ``minimum`` matches in the rule's band and in one other."""
    bands = (("<60", lambda t: t < 60), ("60–80", lambda t: 60 <= t <= 80), (">80", lambda t: t > 80))
    pairs = [(m, s) for m, s in _own(matches) if (m.get("tatica") or {}).get("tempo") is not None]
    parts, ready = [], True
    for label, stronger in (("mais forte", True), ("mais fraco", False)):
        side = [(m, s) for m, s in pairs if (_edge(m, s) > 0) == stronger]
        cells = {name: [(m, s) for m, s in side if test(m["tatica"]["tempo"])] for name, test in bands}
        parts.append(f"{label}: " + ", ".join(f"{name} {_ppg(c):.2f} ({len(c)})" for name, c in cells.items()))
        others = [len(c) for name, c in cells.items() if name != "60–80"]
        ready = ready and len(cells["60–80"]) >= minimum and max(others) >= minimum
    return Result("ritmo", "Temporização 60–80 qualquer que seja a força (§2)", "; ".join(parts), len(pairs),
                  READY if ready else SHORT)


def _report(match: dict) -> dict:
    """The analyst's report on the opponent (``spyresults`` gives a list with the round's report)."""
    report = match.get("analise") or {}
    return (report[0] if report and isinstance(report[0], dict) else {}) if isinstance(report, list) else report


def counter_attack(matches: list[dict], minimum: int = 10) -> Result:
    """OSMPro Táticas point 7, to measure: our 4-3-3 against an opponent in counter-attack (the analyst's report,
    `analise.overallMatchTactics` 3; recorded from version 0.14.6)."""
    pairs = [(m, s) for m, s in _own(matches) if _report(m).get("overallMatchTactics") == 3
             and (m["estatisticas"][s].get("formacao") or "").startswith("433")]
    measured = f"4-3-3 contra contra-ataque: {_ppg(pairs):.2f} pts/jogo ({len(pairs)})"
    return Result("contra", "4-3-3 contra contra-ataque (por medir)", measured, len(pairs), SHORT if len(pairs) < minimum else READY)


MAIN = {1: "att", 2: "ovr", 3: "def", 4: "def"}  # the stat that rises with a level, by position


def _gain(player: dict) -> int:
    """Training progress a friendly gave a player: a level is 100 (the progress starts again)."""
    stat = MAIN.get(player.get("pos"), "ovr")
    levels = (player.get(f"{stat}_depois") or 0) - (player.get(f"{stat}_antes") or 0)
    return (player.get("progresso_depois") or 0) - (player.get("progresso_antes") or 0) + 100 * levels


def friendly_specialists(friendlies: list[dict], minimum: int = 30) -> Result:
    """OSMPro series point 6, to measure (owner, 2026-10-28): does a specialist gain more in a friendly? The players a
    friendly changed, specialists against the rest (recorded from the version after 0.14.7)."""
    mine, rest = [], []
    for record in friendlies:
        roles = set((record.get("especialistas") or {}).values())
        if not roles:
            continue
        for player in record.get("jogadores") or []:
            (mine if player.get("id") in roles else rest).append(_gain(player))
    measured = (f"especialistas +{mean(mine):.1f} ({len(mine)}), os outros +{mean(rest):.1f} ({len(rest)})"
                if mine and rest else f"{len(mine)} especialistas registados")
    return Result("especialistas", "Especialistas evoluem mais nos amigáveis? (por medir)", measured, len(mine),
                  READY if len(mine) >= minimum and rest else SHORT)


OLD_CORNERS_UNTIL = datetime(2026, 10, 29).timestamp()  # matches logged before: corners and free kicks could be one man
NEW_CORNERS_FROM = datetime(2026, 10, 30).timestamp()  # from the match of 2026-10-29 on (logged the morning after)


def _taker(players: list[dict]) -> int | None:
    """The one with most attack, ties to the rest of his stats (THEORY.md section 4)."""
    best = max(players, key=lambda p: (p.get("statAtt") or 0, (p.get("statOvr") or 0) + (p.get("statDef") or 0)), default=None)
    return best.get("id") if best else None


def _corners_clash(match: dict, side: str) -> bool | None:
    """Whether the corners and the free kicks were one man in a match where the midfielder with most attack is
    also the starter with most attack (the clash of THEORY.md section 4); None when there was no clash or it cannot
    be told. The places recorded before the match when there (from the version after 0.14.10), else by the date:
    the old rule (one man) before 2026-10-28, the new one (another midfielder) from 2026-10-29."""
    starters = [p for p in (match.get("onze") or {}).get(side) or [] if 1 <= (p.get("lineup") or 0) <= 11]
    if len(starters) < 11 or _taker(starters) != _taker([p for p in starters if p.get("position") == 2]):
        return None
    places = match.get("especialistas") or {}
    if places.get("corners") and places.get("freekick"):
        return places["corners"] == places["freekick"]
    when = match.get("t") or 0
    return True if when < OLD_CORNERS_UNTIL else False if when >= NEW_CORNERS_FROM else None


def corners_not_free_kicks(matches: list[dict], minimum: int = 10) -> Result:
    """THEORY.md section 4 (owner, 2026-10-28; OSMPro Táticas point 17), to keep measuring (owner, 2026-10-29: "os
    nossos resultados eram bons com a teoria antiga"): the owner's league matches where the midfielder with most
    attack also takes the free kicks, with him on the corners too (the old rule) or another midfielder (the new)."""
    groups: dict[bool, list[tuple[dict, str]]] = {True: [], False: []}
    for match, side in _own(matches):
        clash = _corners_clash(match, side)
        if clash is not None:
            groups[clash].append((match, side))
    same, other = groups[True], groups[False]
    goals = lambda pairs: mean(_goals(m)[0 if s == "casa" else 1] for m, s in pairs) if pairs else 0.0
    edge = lambda pairs: mean(_edge(m, s) for m, s in pairs) if pairs else 0.0
    measured = (f"o mesmo nos cantos e livres {_ppg(same):.2f} pts/jogo, {goals(same):.1f} golos, força {edge(same):+.0f} % ({len(same)}); "
                f"outro médio nos cantos {_ppg(other):.2f}, {goals(other):.1f} golos, força {edge(other):+.0f} % ({len(other)})")
    verdict = SHORT if min(len(same), len(other)) < minimum else AGREES if _ppg(other) >= _ppg(same) else DISAGREES
    return Result("cantos", "Cantos ≠ livres (§4): outro médio nos cantos", measured, len(same) + len(other), verdict)


def manager_xp(lines: list[dict], minimum: int = 10) -> Result:
    """THEORY.md section 22, to keep measuring (owner, 2026-10-28; OSMPro series point 11): the change of the
    manager's rating in the league by result and opponent, from ``logs/*/xp`` (only matches read one round after the
    last, as ``osmbot xp``), without the end-of-season prizes that come with a match, humans split by whether their
    rating is above the owner's. How many wins against the CPU a loss to a human wipes out."""
    groups: dict[tuple[str, str], list[int]] = {}
    for line in {line.get("jogo"): line for line in lines}.values():
        if line.get("liga_variacao") is not None and line.get("jornadas") == 1:
            rival = "CPU"
            if line.get("adversario_humano"):  # the "not the favourite" bonus (OSMPro updates point 1): by his rating
                stronger = (line.get("rating_adversario") or 0) > (line.get("rating") or 0)
                rival = "humano mais forte" if stronger else "humano mais fraco"
            season = sum(b.get("valor") or 0 for b in line.get("bonus") or [] if str(b.get("tipo", "")).startswith("fim de época"))
            groups.setdefault((line.get("resultado"), rival), []).append(line["liga_variacao"] - season)  # the match only
    names = {"V": "vitória", "E": "empate", "D": "derrota"}
    measured = ", ".join(f"{names.get(res, res)} {rival} {mean(v):+.0f} ({len(v)})" for (res, rival), v in sorted(groups.items()))
    losses = groups.get(("D", "humano mais forte"), []) + groups.get(("D", "humano mais fraco"), [])
    wins = groups.get(("V", "CPU"), [])
    if losses and wins and mean(wins) > 0:
        measured += f"; uma derrota com um humano = ~{-mean(losses) / mean(wins):.0f} vitórias contra o CPU"
    return Result("xp", "XP: perder com humanos custa muito (§22, só estudo)", measured or "sem jogos", sum(map(len, groups.values())),
                  AGREES if len(losses) >= minimum else SHORT)


CHECKS: list[Callable[[list[dict]], Result]] = [home_advantage, clearly_stronger, away_433, fatigue,
                                                away_523, against_stronger, tempo_against_stronger, tempo_by_strength, counter_attack,
                                                corners_not_free_kicks]


def run(records: Iterable[dict], friendlies: Iterable[dict] = (), xp: Iterable[dict] = ()) -> list[Result]:
    """Every check: the match records (``logs/*/jogos``), the friendlies' (``logs/*/amigaveis``) and the manager's
    XP (``logs/*/xp``)."""
    matches = unique_matches(records)
    return [check(matches) for check in CHECKS] + [friendly_specialists(list(friendlies)), manager_xp(list(xp))]
