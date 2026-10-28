"""The theory's measurable rules checked against the match records (`logs/*/jogos`; docs/VERIFICACAO.md, owner
2026-10-28: "uma rotina de ir verificando se temos alguma coisa teórica no código que não faça sentido baseado no
histórico real"). Pure: each check takes the records and returns a ``Result``; reading the logs is
``tools/verificar_teoria.py``'s job.

Verdicts: "bate" (the records agree with the rule), "não bate" (they do not: bring it to the owner), "amostra curta"
(not enough matches yet to say), "pronto a decidir" (a rule still to be set, with enough matches now).
"""
from __future__ import annotations

from dataclasses import dataclass
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


CHECKS: list[Callable[[list[dict]], Result]] = [home_advantage, clearly_stronger, away_433, fatigue,
                                                tempo_against_stronger, counter_attack]


def run(records: Iterable[dict]) -> list[Result]:
    matches = unique_matches(records)
    return [check(matches) for check in CHECKS]
