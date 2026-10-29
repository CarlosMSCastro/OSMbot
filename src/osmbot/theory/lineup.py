"""Pre-match warnings on the bench and on the tactics (THEORY.md section 21, owner 2026-10-13). Pure: the bot only
warns, the eleven, the bench and the tactics are the owner's."""
from __future__ import annotations

from collections import Counter
from typing import Iterable

from osmbot.theory.fitness import MATCH_DROP, YELLOW_BELOW
from osmbot.theory.tactics import ATTACK, DEFENSE, MIDFIELD, PLANS, Band, Formation, choose_formation, defensive, instructions

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


def _split(players: list[dict]) -> tuple[list[dict], list[dict]]:
    """The available starters and the available bench, in the bench's order."""
    available = [p for p in players if not p.get("unavailable")]
    starters = [p for p in available if p.get("lineup") in ELEVEN]
    return starters, sorted((p for p in available if (p.get("lineup") or 0) > 11), key=lambda p: p["lineup"])


def _better_on_bench(starters: list[dict], subs: list[dict], floor: int) -> list[tuple[dict, dict]]:
    """(substitute, starter) where a substitute with fitness >= ``floor`` is better than the weakest starter of his
    specific position."""
    fit = [p for p in subs if (p.get("fitness") or 0) >= floor]
    pairs = []
    for specific in dict.fromkeys(p.get("specificPosition") for p in fit):  # a winger only against wingers
        best = max((p for p in fit if p.get("specificPosition") == specific), key=rating)
        weakest = min((p for p in starters if p.get("position") == best.get("position")
                       and p.get("specificPosition") == specific), key=rating, default=None)
        if weakest and rating(best) > rating(weakest):
            pairs.append((best, weakest))
    return pairs


def _subs(bench: list[dict], position: int) -> list[dict]:
    return [p for p in bench if p.get("position") == position and BENCH_PLACES.get(p["lineup"], position) == position]


def bench_warnings(players: list[dict], spare: bool = False) -> list[str]:
    """What is out of the rule on the bench: a player in a place of another position (the bench has places per
    position, ``BENCH_PLACES``), a worse substitute ahead of a better one in the places of the same position (always:
    on an injury the first one comes on), and a fit substitute better than a starter of his specific position (the game:
    players do better in their specific position, so a striker is not compared with a winger). With ``spare`` (the next
    match is not important and the one after is, THEORY.md 16) fit means one who would not reach that match yellow."""
    starters, bench = _split(players)
    warnings = []
    for p in bench:  # the owner may cover a place on purpose (2026-10-16: a defender as the attack's substitute)
        place = BENCH_PLACES.get(p["lineup"])
        if place and p.get("position") in POSITION_WORDS and p["position"] != place:
            warnings.append(f"Tens {POSITION_WORDS[p['position']][0]} a suplente {POSITION_WORDS[place][1]}: "
                            f"{p['name']} {rating(p)}")
    for position in MAIN_STAT:
        subs = _subs(bench, position)
        for i, ahead in enumerate(subs):
            better = max(subs[i + 1:], key=rating, default=None)
            if better and rating(better) > rating(ahead):
                warnings.append(f"{ahead['name']} {rating(ahead)} entra antes de {better['name']} {rating(better)}")
                break
        for best, weakest in _better_on_bench(starters, subs, YELLOW_BELOW + (MATCH_DROP if spare else 0)):
            warnings.append(f"{best['name']} {rating(best)} no banco, {weakest['name']} {rating(weakest)} a jogar")
    return warnings


def bench_notes(players: list[dict], important: str | None) -> list[str]:
    """Substitutes better than a starter but kept out on purpose: green, but they would reach the important match
    (``important``: its opponent, when the next match is not important and that one is; THEORY.md 16, 21) yellow."""
    if not important:
        return []
    starters, bench = _split(players)
    return [f"{p['name']} a poupar para o {important} ({p['fitness']} % → {p['fitness'] - MATCH_DROP} %)"
            for position in MAIN_STAT for p, _ in _better_on_bench(starters, _subs(bench, position), YELLOW_BELOW)
            if p["fitness"] < YELLOW_BELOW + MATCH_DROP]


def places(tactic: dict | None) -> dict[int, int]:
    """Place in the eleven (1-11) -> its specific position, for the tactics' formation; {} when unknown."""
    formation = (tactic or {}).get("formation")
    if formation not in _FORMATIONS:
        return {}
    mid_a, mid_b, att_a, att_b = _FORMATIONS[formation]
    a = (tactic.get("formationDetail") or "A") == "A"
    codes = [6] + _DEF[formation // 100] + _MID[mid_a if a else mid_b] + _ATT[att_a if a else att_b]
    return dict(enumerate(codes, start=1))


def listed_starters(players: list[dict], listed: Iterable) -> list[str]:
    """Starters on the transfer list, at any time (owner, 2026-10-29; before only in the 4 hours before the match):
    the game's transfer engine may sell them minutes before a match and leave the place empty (THEORY.md section 21)."""
    ids = set(listed)
    return [f"{p['name']}: Titular à venda" for p in sorted(players, key=lambda p: p.get("lineup") or 0)
            if p.get("lineup") in ELEVEN and p.get("id") in ids]


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
    """An eleven too young (or too old) for the game: fewer than 3 starters on one side of 26 (THEORY.md section 21).
    A note, not a warning (owner, 2026-10-27)."""
    ages = [p["age"] for p in players if p.get("lineup") in ELEVEN and p.get("age")]
    if len(ages) < len(ELEVEN):
        return []
    warnings = []
    for count, side in ((sum(1 for a in ages if a > AGE_LINE), "acima"), (sum(1 for a in ages if a < AGE_LINE), "abaixo")):
        if count < AGE_MIN:
            warnings.append(f"Onze com só {count} jogador{'es' if count != 1 else ''} {side} de {AGE_LINE} anos")
    return warnings


def position_warnings(players: list[dict], tactic: dict | None) -> list[str]:
    """Starters out of their specific position, as the game counts its step "Position your players" (the game:
    players do better in their specific position; THEORY.md section 21)."""
    spots = places(tactic)
    return [f"{p['name']} ({SPECIFIC.get(p.get('specificPosition'), '?')}) a jogar a {SPECIFIC[spots[p['lineup']]]}"
            for p in sorted(players, key=lambda p: p.get("lineup") or 0)
            if p.get("lineup") in spots and p.get("specificPosition") and p["specificPosition"] != spots[p["lineup"]]]


def centre_notes(players: list[dict], tactic: dict | None) -> list[str]:
    """Where the centre-backs play (owner, 2026-10-28; OSMPro Táticas point 19; THEORY.md section 21), as notes: with
    3, the best in the middle and the 2nd on the side of the weaker full-back; with 2 [S], the better on that side.
    [S] The defence's places go from left to right (DE first, DD last, as in the game's lineup page)."""
    spots = places(tactic)
    at = {p.get("lineup"): p for p in players if not p.get("unavailable")}
    centres = [n for n in sorted(spots) if spots[n] == 3 and n in at]
    if sum(1 for code in spots.values() if code == 3) != len(centres) or len(centres) not in (2, 3):
        return []
    sides = {code: at.get(n) for n, code in spots.items() if code in FULLBACKS}
    left, right = sides.get(9), sides.get(12)
    weak = None if not left or not right or rating(left) == rating(right) else (9 if rating(left) < rating(right) else 12)
    notes, rest = [], [at[n] for n in centres]
    if len(centres) == 3:
        best = max(rest, key=rating)
        if rating(best) > rating(at[centres[1]]):
            notes.append(f"{best['name']} {rating(best)} devia ser o central do meio")
        rest = [p for p in rest if p is not best]
        flanks = [at[centres[0]], at[centres[2]]]
    else:
        flanks = rest
    if weak:
        second = max(rest, key=rating)
        there = flanks[0] if weak == 9 else flanks[-1]
        if there is not second and rating(there) != rating(second):  # also the best there, when he belongs in the middle
            notes.append(f"{second['name']} {rating(second)} devia jogar do lado do {FULLBACKS[weak]} (lateral mais fraco)")
    return notes


def formation_name(tactic: dict) -> str:
    """The tactics' formation as THEORY.md writes it: 433 + "A" -> "4-3-3 A", 532 -> "5-3-2"."""
    digits = "-".join(str(tactic.get("formation") or ""))
    detail = tactic.get("formationDetail") or ""
    return f"{digits} {detail}".strip() if digits == "4-3-3" else digits


WINGERS = {8: "EE", 11: "ED"}  # specificPosition of the wingers the 4-3-3 needs, one on each side
FULLBACKS = {9: "DE", 12: "DD"}  # and of the full-backs of any 4 defenders
MO, MDC, DC = 1, 5, 3
MIDDLE = {MO: "MO", MDC: "MDC"}  # the 4-3-3 A's attacking midfielder and the B's defensive one
# The places a formation is judged by (owner, 2026-10-14, 2026-10-27 and 2026-10-29; THEORY.md section 1): each
# winger, full-back, MO and MDC place needs a fit player of that specific position somewhere in the squad
WATCHED = {**WINGERS, **FULLBACKS, **MIDDLE}
FIVE_SQUAD = 7  # defenders in the squad for 5 at the back: 5 starters and 2 on the bench (owner, 2026-10-29)
FIVE = (("5-3-2", 532), ("5-2-3", 523), ("5-4-1", 541))  # in the order the "Tática" step suggests them
# What serves instead of the rule's 4-3-3 when the squad cannot play it, in the order asked for: name, formation,
# detail (None: either), the positions with nobody fit that make it right and whether it takes all of them (owner,
# 2026-10-14, 2026-10-27 and 2026-10-29; THEORY.md section 1)
INSTEAD = (("4-3-3 B", 433, "B", {MO}, False), ("4-3-3 A", 433, "A", {MDC}, False),
           ("4-4-2 B", 442, "B", set(WINGERS), False), ("5-3-2", 532, None, set(WINGERS), False),
           ("3-4-3", 343, None, set(FULLBACKS), False), ("3-5-2", 352, None, set(WINGERS) | set(FULLBACKS), False),
           ("5-2-3 A", 523, "A", set(MIDDLE), True), ("4-2-4", 424, None, set(MIDDLE), True))
GET_ONE = 'arranja um MO ou MDC: mercado, olheiro ou carta "mudar posição"'  # only advice: buying, the scout, items are writes


def _state(p: dict) -> str:
    if p.get("unavailable"):
        return "fora"
    fitness = p.get("fitness") or 0
    return f"{fitness} %" + (" a poupar" if fitness >= YELLOW_BELOW else "")


def _short(codes: Iterable[int], players: list[dict], spare: bool = False) -> dict[int, str]:
    """Specific position -> why the squad cannot fill its places in ``codes`` (one per place): fewer players of it
    fit (fitness >= 80, not injured or suspended) than places; with ``spare`` (the next match is not important and the
    one after is, THEORY.md 16) also not one who would reach that match yellow."""
    floor = YELLOW_BELOW + (MATCH_DROP if spare else 0)
    short = {}
    for code, count in Counter(codes).items():
        mine = [p for p in players if p.get("specificPosition") == code]
        out = [p for p in mine if p.get("unavailable") or (p.get("fitness") or 0) < floor]
        fit = len(mine) - len(out)
        if fit >= count:
            continue
        who = ", ".join(f"{p['name']} {_state(p)}" for p in out)
        if fit:
            short[code] = f"só {fit} {SPECIFIC[code]} em forma para {count}" + (f" ({who})" if who else "")
        else:
            short[code] = f"sem {SPECIFIC[code]} em forma ({who})" if who else f"sem {SPECIFIC[code]} no plantel"
    return short


def _lacks(formation: int, detail: str | None, players: list[dict] | None, spare: bool = False) -> dict[int, str]:
    """Why the squad cannot play a formation (THEORY.md section 1): its watched places with nobody fit and, with 5 at
    the back, fewer than 7 defenders in the squad or than 3 fit centre-backs (the tired ones can sit on the bench).
    {} when it can, or with no squad to judge by; ``detail`` None: either detail."""
    if not players:
        return {}
    if detail is None:
        a, b = (_lacks(formation, d, players, spare) for d in "AB")
        return a if a and b else {}
    codes = [c for c in places({"formation": formation, "formationDetail": detail}).values() if c in WATCHED]
    lacks = _short(codes, players, spare)
    if formation // 100 == 5:
        lacks.update(_short([DC] * 3, players, spare))
        defenders = sum(1 for p in players if p.get("position") == 3)
        if defenders < FIVE_SQUAD:
            lacks[0] = f"só {defenders} defesas no plantel"
    return dict(sorted(lacks.items()))


def _names(choices: list[tuple]) -> str:
    return " ou ".join(dict.fromkeys(c[0] for c in choices))


CLEARLY_STRONGER = 0.12  # more than 12 % stronger (match strength; measured in 572 matches, D-074): the 4-3-3 A away, the offside trap, only the 5-2-3


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


def _plan(tactic: dict | None, players: list[dict] | None, mine: float | None, opponent: float | None,
          away: bool = False, spare: bool = False) -> tuple[list[str], list[str], tuple[str, int, str | None] | None]:
    """The "Onze" step on the formation (THEORY.md section 1): (warnings, notes on what is right on purpose, the
    formation to switch to when the one set is out of the rule). Only formations the squad can play are asked for
    (owner, 2026-10-29): 5 defenders against a stronger opponent (only the 5-2-3 against a clearly stronger one), else
    the 4-3-3 A at home (the B too) and the B away, and when the squad cannot play those, ``INSTEAD``."""
    if not tactic:
        return [], [], None
    current, code = formation_name(tactic), tactic.get("formation")
    detail = tactic.get("formationDetail") or "A"
    own = _lacks(code, detail, players, spare) if code else {}

    def set_(choice: tuple) -> bool:
        return choice[1] == code and choice[2] in (None, detail)

    def judge(choices: list[tuple], rule: list[tuple], wanted: str, note: str | None = None):
        """Right when the formation set is one of ``choices`` (the ones the squad can play) and it can play it."""
        if any(set_(c) for c in choices) and not own:
            return [], [note] if note else [], None
        if any(set_(c) for c in rule) and own:
            return [f"Formação {current} {'; '.join(own.values())}: serve {_names(choices)}"], [], choices[0][:3]
        return [f"Formação {current}: devia ser {wanted}"], [], choices[0][:3]

    fallback = []
    if mine and opponent and choose_formation(mine, opponent) == Formation.F532:
        rule = [(name, formation, None) for name, formation in FIVE]
        fives = [c for c in rule if not _lacks(c[1], None, players, spare)]
        if _clearly_stronger(opponent, mine):  # clearly weaker: only the 5-2-3 (owner, 2026-10-26)
            only = [c for c in fives if c[1] == 523]
            if only:
                return judge(only, only, "5-2-3 (adversário claramente mais forte)")
            if fives:  # [S] the 5-2-3 cannot be played: any 5 defenders the squad can
                why = "; ".join(_lacks(523, None, players, spare).values())
                return judge(fives, rule, "de 5 defesas (adversário claramente mais forte)", f"{current} aceite: {why}")
        elif fives:
            return judge(fives, rule, "de 5 defesas (adversário mais forte)")
        fallback = [f"Sem 5 defesas contra um mais forte: {'; '.join(_lacks(532, None, players, spare).values())}"]
    rule = [(name, 433, name[-1]) for name in _wanted(mine, opponent, away)]
    able = [c for c in rule if not _lacks(c[1], c[2], players, spare)]
    where = " (fora de casa)" if away else ""
    if able:
        if not away and current == Formation.F433_B.value and not own:  # right too, not the rule (owner, 2026-10-26)
            return [], ["4-3-3 B aceite: em casa a regra é o 4-3-3 A"] + fallback, None
        note = (f"4-3-3 A aceite: fora, mas claramente mais forte (+{mine / opponent - 1:.0%})"
                if away and current == Formation.F433_A.value and _clearly_stronger(mine, opponent) else None)
        warnings, notes, other = judge(able, rule, _names(able) + where, note)
        return warnings, notes + (fallback if not warnings else []), other
    gone = _short(list(WATCHED), players or [], spare)
    get = [GET_ONE] if MIDDLE.keys() <= gone.keys() else []
    alts = [(name, formation, d, group) for name, formation, d, group, every in INSTEAD
            if (group <= gone.keys() if every else group & gone.keys()) and not _lacks(formation, d, players, spare)]
    hit = next((a for a in alts if set_(a)), None)
    if hit and not own:
        why = "; ".join(why for c, why in sorted(gone.items()) if c in hit[3])
        return [], [f"{hit[0]} aceite: {why}"] + get + fallback, None
    if alts:
        warnings, _, other = judge(alts, rule + alts, _names(alts))
        return warnings + get, fallback, other
    if any(set_(c) for c in rule):  # nothing the squad can play
        return [f"Formação {current} {'; '.join(own.values())}"] + get, fallback, None
    lacks = "; ".join(_lacks(433, rule[0][2], players, spare).values())
    return [f"Formação {current}: devia ser {_names(rule)}{where}, mas {lacks}"] + get, fallback, None


def tactic_notes(tactic: dict | None, players: list[dict] | None, mine: float | None, opponent: float | None,
                 away: bool = False, spare: bool = False) -> list[str]:
    """What the tactics do differently from the rule, on purpose and within it (the step stays green): the 4-3-3 B
    for want of an MO, the 4-4-2 B (or 5-3-2, 3-5-2) for want of wingers, the 3-4-3 (or 3-5-2) for want of full-backs,
    the 5-2-3 A or 4-2-4 for want of both an MO and an MDC, the 4-3-3 A away when clearly stronger, the 4-3-3 B at home
    (THEORY.md section 1)."""
    return _plan(tactic, players, mine, opponent, away, spare)[1]


def tactic_warnings(tactic: dict | None, mine: float | None, opponent: float | None,
                    players: list[dict] | None = None, away: bool = False, spare: bool = False) -> list[str]:
    """What is out of the rule in the formation (the tackling went to the "Tática" step, ``tactic_check``): see
    ``_plan``. ``opponent``: before the analysis an estimate (THEORY.md section 1); None when unknown."""
    return _plan(tactic, players, mine, opponent, away, spare)[0]


def _suggested(tactic: dict, players: list[dict] | None, mine: float | None, opponent: float | None, away: bool,
               spare: bool) -> tuple[str, int, str | None] | None:
    """The formation the "Onze" step asks for when the one set is out of the rule (``tactic_warnings``): its name,
    code and detail, for the "Tática" step to say what the instructions would be; None when it is right."""
    return _plan(tactic, players, mine, opponent, away, spare)[2]


FIELDS = (("Estilo de jogo", "overallMatchTactics", "plan", PLANS), ("Defesa", "defense", "defense", DEFENSE),
          ("Médios", "midfield", "midfield", MIDFIELD), ("Avançados", "attack", "attack", ATTACK),
          ("Marcação", "marking", "marking", {False: "À zona", True: "Individual"}),
          ("Fora de jogo", "offsideTrap", "offside", {True: "Sim", False: "Não"}),
          ("Pressão", "pressing", "pressing", None), ("Estilo", "mentality", "mentality", None),
          ("Temporização", "tempo", "tempo", None))


def _rule(value, names: dict | None) -> str:
    if isinstance(value, Band):
        return f"{value.low}–{value.high} (~{value.aim})"
    return " ou ".join(names.get(c, f"código {c}") for c in sorted(value)).capitalize()


def tactic_check(tactic: dict | None, strictness: int | None, mine: float | None, opponent: float | None,
                 players: list[dict] | None = None, away: bool = False, spare: bool = False,
                 forwards: int | None = None) -> tuple[list[str], list[str], bool]:
    """The "Tática" step (owner, 2026-10-28, D-073; THEORY.md 2 and 21): the instructions, the sliders and the tackling
    set in the game against the rule for the formation that is set. Returns (warnings, notes, known): a warning per
    field out of the rule, "Pressão: 45, devia ser 60–80 (~75)"; notes with what the formation the "Onze" step asks for
    would take ("Se mudares para 5-2-3:" and a line per field); known False when section 2 has no rule for the
    formation set (the step stays grey). ``forwards``: how many his eleven has, after the analysis."""
    if not tactic:
        return [], [], False
    starters = [p for p in players or [] if p.get("lineup") in ELEVEN]
    context = dict(away=away, clearly_stronger=_clearly_stronger(mine, opponent),
                   clearly_weaker=_clearly_stronger(opponent, mine), forwards=forwards,
                   defensive_forwards=defensive(starters))
    rule = instructions(tactic.get("formation"), tactic.get("formationDetail"), **context)
    warnings, notes = [], []
    if rule:
        for label, key, field, names in FIELDS:
            value, wanted = tactic.get(key), getattr(rule, field)
            if value is not None and value not in wanted:
                now = value if names is None else names.get(value, f"código {value}")
                warnings.append(f"{label}: {now}, devia ser {_rule(wanted, names)}")
    else:
        notes.append(f"Sem regra para o {formation_name(tactic)}")
    style = tactic.get("style")
    if strictness in ACCEPTED and style is not None and style not in ACCEPTED[strictness]:
        wanted = " ou ".join(TACKLING[s] for s in sorted(ACCEPTED[strictness]))
        warnings.append(f"Desarme: {TACKLING.get(style, style)}, devia ser {wanted} (árbitro {REFEREES[strictness]})")
    other = _suggested(tactic, players, mine, opponent, away, spare)
    if other and (better := instructions(other[1], other[2], **context)):
        notes.append(f"Se mudares para {other[0]}:")
        notes += [f"{label}: {_rule(getattr(better, field), names)}" for label, _, field, names in FIELDS]
    return warnings, notes, rule is not None
