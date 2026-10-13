"""Pre-match warnings on the bench and on the tactics (THEORY.md section 21, owner 2026-10-13). Pure: the bot only
warns, the eleven, the bench and the tactics are the owner's."""
from __future__ import annotations

from osmbot.theory.fitness import YELLOW_BELOW
from osmbot.theory.tactics import Formation, choose_formation

MAIN_STAT = {1: "statAtt", 2: "statOvr", 3: "statDef", 4: "statDef"}  # the rating that counts for each position
ELEVEN = range(1, 12)
TACKLING = {0: "Cuidadoso", 1: "Normal", 2: "Agressivo", 3: "Extremo"}  # the tactics' `style` (game's TacticStyleOfPlay)
REFEREES = {1: "muito rigoroso", 2: "rigoroso", 3: "normal", 4: "brando", 5: "muito brando"}  # `strictness`
ACCEPTED = {1: {1}, 2: {2}, 3: {2}, 4: {2, 3}, 5: {3}}  # strictness -> tackling the owner accepts (sections 3, 21)


def rating(player: dict) -> int:
    return player.get(MAIN_STAT.get(player.get("position"), "statOvr")) or 0


def bench_warnings(players: list[dict]) -> list[str]:
    """What is out of the rule on the bench: a worse substitute ahead of a better one of the same position (always:
    on an injury the first one comes on), and a fit substitute better than a starter of his position."""
    available = [p for p in players if not p.get("unavailable")]
    starters = [p for p in available if p.get("lineup") in ELEVEN]
    bench = sorted((p for p in available if (p.get("lineup") or 0) > 11), key=lambda p: p["lineup"])
    warnings = []
    for position in MAIN_STAT:
        subs = [p for p in bench if p.get("position") == position]
        for i, ahead in enumerate(subs):
            better = max(subs[i + 1:], key=rating, default=None)
            if better and rating(better) > rating(ahead):
                warnings.append(f"{ahead['name']} {rating(ahead)} entra antes de {better['name']} {rating(better)}")
                break
        weakest = min((p for p in starters if p.get("position") == position), key=rating, default=None)
        fit = [p for p in subs if (p.get("fitness") or 0) >= YELLOW_BELOW]
        best = max(fit, key=rating, default=None)
        if weakest and best and rating(best) > rating(weakest):
            warnings.append(f"{best['name']} {rating(best)} no banco, {weakest['name']} {rating(weakest)} a jogar")
    return warnings


def formation_name(tactic: dict) -> str:
    """The tactics' formation as THEORY.md writes it: 433 + "A" -> "4-3-3 A", 532 -> "5-3-2"."""
    digits = "-".join(str(tactic.get("formation") or ""))
    detail = tactic.get("formationDetail") or ""
    return f"{digits} {detail}".strip() if digits == "4-3-3" else digits


def tactic_warnings(tactic: dict | None, strictness: int | None, mine: float | None, opponent: float | None) -> list[str]:
    """What is out of the rule in the tactics: the tackling for the next match's referee, and the formation
    (4-3-3 A; 5-3-2 once the analysis shows an opponent stronger by more than 5 %). ``opponent``: None before the
    analysis."""
    if not tactic:
        return []
    warnings = []
    style = tactic.get("style")
    if strictness in ACCEPTED and style is not None and style not in ACCEPTED[strictness]:
        wanted = " ou ".join(TACKLING[s] for s in sorted(ACCEPTED[strictness]))
        warnings.append(f"Desarme {TACKLING.get(style, style)} com árbitro {REFEREES[strictness]}: devia ser {wanted}")
    wanted_formation = choose_formation(mine, opponent) if mine and opponent else Formation.F433_A
    current = formation_name(tactic)
    if current and current.replace(" ", "") != wanted_formation.value.replace(" ", "") and \
            not (wanted_formation == Formation.F532 and current.startswith("5-3-2")):
        reason = " (adversário mais de 5 % mais forte)" if wanted_formation == Formation.F532 else ""
        warnings.append(f"Formação {current}: devia ser {wanted_formation.value}{reason}")
    return warnings
