"""Pre-match warnings on the bench and on the tactics (THEORY.md section 21, owner 2026-10-13). Pure: the bot only
warns, the eleven, the bench and the tactics are the owner's."""
from __future__ import annotations

from osmbot.theory.fitness import YELLOW_BELOW
from osmbot.theory.tactics import Formation, choose_formation

MAIN_STAT = {1: "statAtt", 2: "statOvr", 3: "statDef", 4: "statDef"}  # the rating that counts for each position
ELEVEN = range(1, 12)
# The bench's places and the position each is for, as the game lays it out (seen in the 3 clubs' benches and confirmed
# by the owner, 2026-10-16): 12 GR, 13 DEF, 14 MED, 15 ATA, 16 DEF, 17 MED, 18 ATA
BENCH_PLACES = {12: 4, 13: 3, 14: 2, 15: 1, 16: 3, 17: 2, 18: 1}
POSITION_WORDS = {1: ("um avançado", "do ataque"), 2: ("um médio", "do meio-campo"), 3: ("um defesa", "da defesa"),
                  4: ("um guarda-redes", "da baliza")}
TACKLING = {0: "Cuidadoso", 1: "Normal", 2: "Agressivo", 3: "Extremo"}  # the tactics' `style` (game's TacticStyleOfPlay)
REFEREES = {1: "muito rigoroso", 2: "rigoroso", 3: "normal", 4: "brando", 5: "muito brando"}  # `strictness`
ACCEPTED = {1: {1}, 2: {2}, 3: {2}, 4: {2, 3}, 5: {2, 3}}  # strictness -> tackling the owner accepts (sections 3, 21; very lenient: also Aggressive, 2026-10-14)
# `specificPosition` (game's PlayerSpecificPosition: 1 CAM, 2 CM, 3 CB, 4 ST, 5 CDM, 6 GK, 7 LM, 8 LF, 9 LB, 10 RM,
# 11 RF, 12 RB) as the owner says them
SPECIFIC = {1: "MO", 2: "MC", 3: "DC", 4: "PL", 5: "MDC", 6: "GR", 7: "ME", 8: "EE", 9: "DE", 10: "MD", 11: "ED", 12: "DD"}
# The specific position of each place of each formation, from the game's own lineup page (lineup.js): defenders from
# place 2, then midfielders, then attackers; "A"/"B" is the formation's detail
_DEF = {3: [3, 3, 3], 4: [9, 3, 3, 12], 5: [9, 3, 3, 3, 12], 6: [9, 3, 3, 3, 12, 3]}
_MID = {"2A": [2, 2], "2B": [5, 5], "3A": [2, 1, 2], "3B": [2, 5, 2], "3C": [1, 2, 1], "3D": [2, 2, 2], "3E": [1, 2, 1],
        "4A": [7, 2, 2, 10], "4B": [2, 5, 2, 1], "5A": [7, 2, 5, 2, 10], "5B": [7, 2, 1, 2, 10], "5C": [7, 1, 5, 1, 10],
        "5D": [7, 5, 2, 5, 10]}
_ATT = {"1A": [4], "2A": [4, 4], "2B": [4, 4], "3A": [8, 4, 11], "3B": [8, 4, 11], "4A": [8, 4, 4, 11],
        "4B": [8, 4, 11, 4], "5A": [8, 4, 4, 11, 4], "5B": [4, 8, 4, 4, 11]}
_FORMATIONS = {325: ("2B", "2B", "5A", "5B"), 334: ("3D", "3B", "4A", "4B"), 343: ("4A", "4B", "3A", "3B"),
               352: ("5C", "5D", "2A", "2A"), 433: ("3A", "3B", "3B", "3B"), 451: ("5A", "5B", "1A", "1A"),
               442: ("4A", "4B", "2A", "2A"), 424: ("2A", "2B", "4A", "4B"), 523: ("2A", "2B", "3B", "3A"),
               532: ("3A", "3E", "2A", "2B"), 541: ("4A", "4B", "1A", "1A"), 631: ("3A", "3C", "1A", "1A")}


def rating(player: dict) -> int:
    return player.get(MAIN_STAT.get(player.get("position"), "statOvr")) or 0


def bench_warnings(players: list[dict]) -> list[str]:
    """What is out of the rule on the bench: a player in a place of another position (the bench has places per
    position, ``BENCH_PLACES``), a worse substitute ahead of a better one in the places of the same position (always:
    on an injury the first one comes on), and a fit substitute better than a starter of his specific position (the game:
    players do better in their specific position, so a striker is not compared with a winger)."""
    available = [p for p in players if not p.get("unavailable")]
    starters = [p for p in available if p.get("lineup") in ELEVEN]
    bench = sorted((p for p in available if (p.get("lineup") or 0) > 11), key=lambda p: p["lineup"])
    warnings = []
    for p in bench:  # the owner may cover a place on purpose (2026-10-16: a defender as the attack's substitute)
        place = BENCH_PLACES.get(p["lineup"])
        if place and p.get("position") in POSITION_WORDS and p["position"] != place:
            warnings.append(f"Tens {POSITION_WORDS[p['position']][0]} a suplente {POSITION_WORDS[place][1]}: "
                            f"{p['name']} {rating(p)}")
    for position in MAIN_STAT:
        subs = [p for p in bench if p.get("position") == position and BENCH_PLACES.get(p["lineup"], position) == position]
        for i, ahead in enumerate(subs):
            better = max(subs[i + 1:], key=rating, default=None)
            if better and rating(better) > rating(ahead):
                warnings.append(f"{ahead['name']} {rating(ahead)} entra antes de {better['name']} {rating(better)}")
                break
        fit = [p for p in subs if (p.get("fitness") or 0) >= YELLOW_BELOW]
        for specific in dict.fromkeys(p.get("specificPosition") for p in fit):  # a winger only against wingers
            best = max((p for p in fit if p.get("specificPosition") == specific), key=rating)
            weakest = min((p for p in starters if p.get("position") == position
                           and p.get("specificPosition") == specific), key=rating, default=None)
            if weakest and rating(best) > rating(weakest):
                warnings.append(f"{best['name']} {rating(best)} no banco, {weakest['name']} {rating(weakest)} a jogar")
    return warnings


def places(tactic: dict | None) -> dict[int, int]:
    """Place in the eleven (1-11) -> its specific position, for the tactics' formation; {} when unknown."""
    formation = (tactic or {}).get("formation")
    if formation not in _FORMATIONS:
        return {}
    mid_a, mid_b, att_a, att_b = _FORMATIONS[formation]
    a = (tactic.get("formationDetail") or "A") == "A"
    codes = [6] + _DEF[formation // 100] + _MID[mid_a if a else mid_b] + _ATT[att_a if a else att_b]
    return dict(enumerate(codes, start=1))


def empty_places(players: list[dict], tactic: dict | None) -> list[str]:
    """Places of the eleven with nobody in them (FC Van, 2026-10-18: a starter sold and the place left empty), with
    the specific position the formation wants there when known (THEORY.md section 21)."""
    taken = {p.get("lineup") for p in players}
    if not taken & set(ELEVEN):  # no eleven read: nothing to say
        return []
    spots = places(tactic)
    return [f"Lugar {n} do 11 vazio" + (f" ({SPECIFIC[spots[n]]})" if n in spots else "") for n in ELEVEN if n not in taken]


AGE_LINE, AGE_MIN = 26, 3  # at least 3 starters older and 3 younger than 26 (THEORY.md section 21)


def age_warnings(players: list[dict]) -> list[str]:
    """An eleven too young (or too old) for the game: fewer than 3 starters on one side of 26 (THEORY.md section 21)."""
    ages = [p["age"] for p in players if p.get("lineup") in ELEVEN and p.get("age")]
    if len(ages) < len(ELEVEN):
        return []
    warnings = []
    for count, side, why in ((sum(1 for a in ages if a > AGE_LINE), "acima", "jovem"),
                             (sum(1 for a in ages if a < AGE_LINE), "abaixo", "velho")):
        if count < AGE_MIN:
            warnings.append(f"Onze com só {count} jogador{'es' if count != 1 else ''} {side} de {AGE_LINE} anos "
                            f"(o jogo dá bónus negativo a um onze demasiado {why})")
    return warnings


def position_warnings(players: list[dict], tactic: dict | None) -> list[str]:
    """Starters out of their specific position, as the game counts its step "Position your players" (the game:
    players do better in their specific position; THEORY.md section 21)."""
    spots = places(tactic)
    return [f"{p['name']} ({SPECIFIC.get(p.get('specificPosition'), '?')}) a jogar a {SPECIFIC[spots[p['lineup']]]}"
            for p in sorted(players, key=lambda p: p.get("lineup") or 0)
            if p.get("lineup") in spots and p.get("specificPosition") and p["specificPosition"] != spots[p["lineup"]]]


def formation_name(tactic: dict) -> str:
    """The tactics' formation as THEORY.md writes it: 433 + "A" -> "4-3-3 A", 532 -> "5-3-2"."""
    digits = "-".join(str(tactic.get("formation") or ""))
    detail = tactic.get("formationDetail") or ""
    return f"{digits} {detail}".strip() if digits == "4-3-3" else digits


WINGERS = {8: "EE", 11: "ED"}  # specificPosition of the wingers the 4-3-3 needs, one on each side


def _no_wingers(players: list[dict]) -> str | None:
    """Why the 4-3-3 cannot be played (owner, 2026-10-14): a side with no winger fit to play (fitness >= 80, not
    injured or suspended), in the whole squad. None when both sides have one."""
    missing = []
    for code, side in WINGERS.items():
        mine = [p for p in players if p.get("specificPosition") == code]
        if any(not p.get("unavailable") and (p.get("fitness") or 0) >= YELLOW_BELOW for p in mine):
            continue
        who = ", ".join(f"{p['name']} {'fora' if p.get('unavailable') else str(p.get('fitness') or 0) + ' %'}"
                        for p in mine)
        missing.append(f"sem {side} em forma ({who})" if who else f"sem {side} no plantel")
    return "; ".join(missing) or None


def _wingerless(tactic: dict, players: list[dict] | None) -> str | None:
    """The 4-4-2 B (2 strikers, no wingers) taken in place of the 4-3-3 A when a side has no fit winger: the reason,
    or None when it does not apply."""
    if tactic.get("formation") != 442 or (tactic.get("formationDetail") or "") != "B" or players is None:
        return None
    return _no_wingers(players)


CLEARLY_STRONGER = 0.05  # [S] away, more than 5 % stronger (match strength): the 4-3-3 A is right too (owner, 2026-10-25)


def _clearly_stronger(mine: float | None, opponent: float | None) -> bool:
    return bool(mine and opponent) and mine > opponent * (1 + CLEARLY_STRONGER)


def _wanted(mine: float | None, opponent: float | None, away: bool) -> list[str]:
    """The 4 defenders' formations the rule takes (THEORY.md section 1): at home the 4-3-3 A; away the 4-3-3 B (it did
    better away in the logs, owner 2026-10-25), and the A as well when clearly stronger. With no strength to compare
    (a reading that failed) each side's usual one, as at home."""
    if not away:
        return [Formation.F433_A.value]
    if _clearly_stronger(mine, opponent):
        return [Formation.F433_A.value, Formation.F433_B.value]
    return [Formation.F433_B.value]


def _home_b(tactic: dict, away: bool) -> bool:
    """The 4-3-3 B at home: not the rule (the A is), but right too (owner, 2026-10-26)."""
    return not away and formation_name(tactic) == Formation.F433_B.value


def tactic_notes(tactic: dict | None, players: list[dict] | None, mine: float | None, opponent: float | None,
                 away: bool = False) -> list[str]:
    """What the tactics do differently from the rule, on purpose and within it (the step stays green): the 4-4-2 B
    for want of wingers, the 4-3-3 A away when clearly stronger, the 4-3-3 B at home (THEORY.md section 1)."""
    if not tactic or (mine and opponent and choose_formation(mine, opponent) == Formation.F532):
        return []
    if away and formation_name(tactic) == Formation.F433_A.value and _clearly_stronger(mine, opponent):
        return [f"4-3-3 A aceite: fora, mas claramente mais forte (+{mine / opponent - 1:.0%})"]
    if _home_b(tactic, away):
        return ["4-3-3 B aceite: em casa a regra é o 4-3-3 A"]
    why = _wingerless(tactic, players)
    return [f"4-4-2 B aceite: {why}"] if why else []


def tactic_warnings(tactic: dict | None, strictness: int | None, mine: float | None, opponent: float | None,
                    players: list[dict] | None = None, away: bool = False) -> list[str]:
    """What is out of the rule in the tactics: the tackling for the next match's referee, and the formation
    (``_wanted``: 4-3-3 A at home (the B too), B away, or the 4-4-2 B when a side has no fit winger; 5 defenders, any of them,
    against a stronger opponent, only the 5-2-3 against a clearly stronger one). ``opponent``: before the analysis an estimate (THEORY.md section 1); None when unknown."""
    if not tactic:
        return []
    warnings = []
    style = tactic.get("style")
    if strictness in ACCEPTED and style is not None and style not in ACCEPTED[strictness]:
        wanted = " ou ".join(TACKLING[s] for s in sorted(ACCEPTED[strictness]))
        warnings.append(f"Desarme {TACKLING.get(style, style)} com árbitro {REFEREES[strictness]}: devia ser {wanted}")
    wanted_formation = choose_formation(mine, opponent) if mine and opponent else Formation.F433_A
    current = formation_name(tactic)
    if wanted_formation == Formation.F532:  # any formation with 5 defenders: the owner picks the one that fits the players
        if current and _clearly_stronger(opponent, mine):  # clearly weaker: only the 5-2-3 (owner, 2026-10-26)
            if current != "5-2-3":
                warnings.append(f"Formação {current}: devia ser 5-2-3 (adversário claramente mais forte)")
        elif current and not current.startswith("5-"):
            warnings.append(f"Formação {current}: devia ser de 5 defesas (adversário mais forte)")
    elif (current and current not in (wanted := _wanted(mine, opponent, away)) and not _home_b(tactic, away)
          and not _wingerless(tactic, players)):
        warnings.append(f"Formação {current}: devia ser {' ou '.join(wanted)}" + (" (fora de casa)" if away else ""))
    return warnings
