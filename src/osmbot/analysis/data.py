"""The data behind Ver → Dados (owner, 2026-11-06): every logged league and cup match as two rows, one per side,
with what is known of each side's tactic, and the odds the two squads' strength gave.

Pure: ``rows(matches, reports)`` takes the records of ``logs/*/jogos`` and ``logs/*/analista``; ``summary`` sums up
the rows a filter kept. Where each side's tactic comes from:
- the owner's clubs: his tactic as read before the match (``tatica``): everything, sliders and lines included;
- his opponents: the analyst's report of that round (``analise``);
- every other club: the analyst's report on it (``logs/*/analista``) of the round before the match (``weekNr`` + 1);
- the formation of both sides always comes from the match itself.
A report counts only when the club played the formation the report shows (the same rule as the theory checks).

Human or the computer: the owner's clubs are human; else the match's own ``treinador`` (logged from 2026-11-06);
else the nearest analyst's report on that club in the same league (``managerName``); else unknown.

The odds by strength: for each row, the share of wins, draws and losses among the ``NEIGHBOURS`` rows of all clubs
closest to it in strength ratio (``forca`` of the game, home and away apart). "EV" is points won minus the points
those odds gave (3 × win + draw). The window counts in wins (``tally``, ``verdict``): won 45 of 55 where the odds
gave 36 is "9 a mais" (owner, 2026-11-06, D-096: "+0,xx" read as nothing).
"""
from __future__ import annotations

import bisect
import math
from dataclasses import dataclass, field
from datetime import datetime
from statistics import mean

PLANS = {0: "Bola longa", 1: "Jogo de passe", 2: "Pelas alas", 3: "Contra-ataque", 4: "Remate à vista"}
TACKLING = {0: "Cuidadoso", 1: "Normal", 2: "Agressivo", 3: "Extremo"}
ATTACK = {0: "Ajudar a defender", 1: "Apoiar meio-campo", 2: "Atacar apenas"}
MIDFIELD = {0: "Ajudar a defesa", 1: "Manter posições", 2: "Pressionar na frente"}
DEFENSE = {0: "Defender atrás", 1: "Defender na frente"}
NEIGHBOURS = 80  # rows behind each row's odds by strength
SLIDER_BANDS = ((0, 40, "0–39"), (40, 60, "40–59"), (60, 70, "60–69"), (70, 80, "70–79"), (80, 101, "80–100"))


def band(value) -> str | None:
    if value is None:
        return None
    return next((name for low, high, name in SLIDER_BANDS if low <= value < high), None)


@dataclass
class Row:
    """One side of one match."""
    match: str
    league: str
    when: float
    kind: str  # "liga" / "taça"
    home: bool
    neutral: bool
    club: str
    mine: bool
    human: bool | None
    goals: int
    against: int
    points: int
    strength: float
    rival_strength: float
    eleven: float | None
    rival_eleven: float | None
    shots: int | None
    rival_shots: int | None
    possession: int | None
    rival: str
    result: str  # as the match shows it, home first
    tactic: dict = field(default_factory=dict)  # this side: formation, plan, tackling, marking, trap (+ sliders, lines)
    rival_tactic: dict = field(default_factory=dict)
    rival_human: bool | None = None
    rival_mine: bool = False
    odds: tuple[float, float, float] = (0.0, 0.0, 0.0)  # win, draw, loss by strength

    @property
    def ratio(self) -> float:
        return self.strength / self.rival_strength

    @property
    def edge(self) -> float:
        """How much stronger, in % of the rival (negative: weaker)."""
        return (self.ratio - 1) * 100

    @property
    def expected(self) -> float:
        return 3 * self.odds[0] + self.odds[1]

    @property
    def outcome(self) -> str:
        return "V" if self.points == 3 else "E" if self.points == 1 else "D"


def _report_tactic(report: dict) -> dict:
    return {"plano": PLANS.get(report.get("overallMatchTactics")), "desarme": TACKLING.get(report.get("style")),
            "marcacao": "Individual" if report.get("marking") else "Zona" if report.get("marking") is not None else None,
            "armadilha": "Sim" if report.get("offsideTrap") else "Não" if report.get("offsideTrap") is not None else None}


def _own_tactic(tactic: dict) -> dict:
    found = _report_tactic(tactic)
    found.update({"mentalidade": band(tactic.get("mentality")), "pressao": band(tactic.get("pressing")),
                  "tempo": band(tactic.get("tempo")), "avancados": ATTACK.get(tactic.get("attack")),
                  "medios": MIDFIELD.get(tactic.get("midfield")), "defesa": DEFENSE.get(tactic.get("defense"))})
    return found


def _formation(stats: dict) -> str | None:
    form = stats.get("formacao") or ""
    return f"{form[0]}-{form[1]}-{form[2:3]}{(' ' + form[3:]) if form[3:] else ''}" if len(form) >= 3 else None


def _first(report) -> dict:
    if isinstance(report, list):
        return report[0] if report and isinstance(report[0], dict) else {}
    return report if isinstance(report, dict) else {}


def _same_formation(stats: dict, report: dict) -> bool:
    return (stats.get("formacao") or "") == f"{report.get('formation')}{report.get('formationDetail') or ''}"


def unique(matches) -> list[dict]:
    """One record per match (several PCs log the same one): the fullest."""
    best: dict = {}
    for record in matches:
        key = record.get("jogo")
        if key and (key not in best or len(str(record)) > len(str(best[key]))):
            best[key] = record
    return list(best.values())


def rows(matches, reports=()) -> list[Row]:
    """Two rows per league or cup match with both sides' strength (see the module's text), odds included."""
    by_round: dict[tuple, dict] = {}
    by_club: dict[tuple, list[tuple[int, bool]]] = {}
    matches = unique(matches)
    kept_with = [a for m in matches for a in (m.get("analise") if isinstance(m.get("analise"), list) else [])
                 if isinstance(a, dict)]  # the reports on the owner's opponents count for the manager too
    for line in list(reports) + kept_with:
        r = line.get("relatorio") or line
        if r.get("leagueId") is None or r.get("teamId") is None:
            continue
        key = (str(r["leagueId"]), r["teamId"])
        by_round[key + ((r.get("weekNr") or 0) + 1,)] = r
        by_club.setdefault(key, []).append((r.get("weekNr") or 0, bool(r.get("managerName"))))
    found: list[Row] = []
    for m in matches:
        stats = m.get("estatisticas") or {}
        home_s, away_s = stats.get("casa") or {}, stats.get("fora") or {}
        if m.get("tipo") not in ("liga", "taça") or not home_s.get("forca") or not away_s.get("forca"):
            continue
        try:
            hg, ag = (int(x) for x in str(m["resultado"]).split("-"))
        except (KeyError, ValueError):
            continue
        league = str(m.get("jogo", "")).split("_")[0]
        week = m.get("semana") or 0
        draw = bool(m.get("penaltis") or m.get("prolongamento"))  # a cup tie settled after 90 min: a draw
        sides = {}
        for side, other in (("casa", "fora"), ("fora", "casa")):
            club = m.get(side) or {}
            own_stats = stats[side]
            tactic = {"formacao": _formation(own_stats)}
            if club.get("meu") and m.get("tatica"):
                tactic.update(_own_tactic(m["tatica"]))
            else:
                report = None
                if (m.get(other) or {}).get("meu") and _first(m.get("analise")):
                    report = _first(m.get("analise"))
                report = report or by_round.get((league, club.get("id"), week))
                if report and _same_formation(own_stats, report):
                    tactic.update(_report_tactic(report))
            human = True if club.get("meu") else club.get("treinador")
            if human is None:
                seen = by_club.get((league, club.get("id"))) or []
                if seen:
                    human = min(seen, key=lambda s: abs(s[0] + 1 - week))[1]
            sides[side] = (tactic, human)
        for side, other in (("casa", "fora"), ("fora", "casa")):
            club, rival = m.get(side) or {}, m.get(other) or {}
            goals, against = (hg, ag) if side == "casa" else (ag, hg)
            points = 1 if draw or goals == against else 3 if goals > against else 0
            found.append(Row(
                match=m["jogo"], league=league, when=m.get("t") or 0, kind=m["tipo"], home=side == "casa",
                neutral=bool(m.get("campo_neutro")), club=club.get("nome") or str(club.get("id")),
                mine=bool(club.get("meu")), human=sides[side][1], goals=goals, against=against, points=points,
                strength=stats[side]["forca"], rival_strength=stats[other]["forca"],
                eleven=club.get("media_11"), rival_eleven=rival.get("media_11"),
                shots=stats[side].get("remates"), rival_shots=stats[other].get("remates"),
                possession=stats[side].get("posse"), rival=rival.get("nome") or str(rival.get("id")),
                result=m["resultado"], tactic=sides[side][0], rival_tactic=sides[other][0],
                rival_human=sides[other][1], rival_mine=bool(rival.get("meu"))))
    add_odds(found)
    return found


def add_odds(found: list[Row], k: int = NEIGHBOURS) -> None:
    """Each row's win/draw/loss odds by strength: the outcomes of the ``k`` rows nearest in log strength ratio, with
    the same ground (home, away, neutral)."""
    groups: dict[str, list[Row]] = {}
    for row in found:
        groups.setdefault("n" if row.neutral else "c" if row.home else "f", []).append(row)
    for group in groups.values():
        group.sort(key=lambda r: math.log(r.ratio))
        keys = [math.log(r.ratio) for r in group]
        size = min(k, len(group))
        for i, row in enumerate(group):
            x = keys[i]
            lo = max(0, min(bisect.bisect_left(keys, x) - size // 2, len(group) - size))
            # slide the window to the nearest ``size`` rows
            while lo > 0 and abs(keys[lo - 1] - x) < abs(keys[lo + size - 1] - x):
                lo -= 1
            while lo + size < len(group) and abs(keys[lo + size] - x) < abs(keys[lo] - x):
                lo += 1
            near = group[lo:lo + size]
            row.odds = tuple(sum(r.points == p for r in near) / len(near) for p in (3, 1, 0))


# --- filters -----------------------------------------------------------------------------------------------------

TACTIC_FIELDS = (("formacao", "Formação"), ("plano", "Estilo de jogo"), ("desarme", "Desarme"),
                 ("marcacao", "Marcação"), ("armadilha", "Fora de jogo"))
OWN_FIELDS = (("mentalidade", "Mentalidade"), ("pressao", "Pressão"), ("tempo", "Temporização"),
              ("avancados", "Avançados"), ("medios", "Médios"), ("defesa", "Defesa"))
ANY = "Qualquer"
STRENGTH_BANDS = {"Qualquer": (-1000, 1000), "vs muito mais forte": (-1000, -12), "vs mais forte": (-12, -5),
                  "vs parecido": (-5, 5), "vs mais fraco": (5, 12), "vs muito mais fraco": (12, 1000)}
"""The rival's strength against this side's (owner, 2026-11-06: "vs muito mais forte, mais forte, etc."): the rival
much stronger means this side more than 12 % weaker."""
PERIODS = {"Tudo": None, "Últimos 7 dias": 7, "Últimos 30 dias": 30, "Últimos 90 dias": 90}


def choices(found: list[Row], key: str, rival: bool = False) -> list[str]:
    """The values a tactic field takes in the rows, for the filter's list."""
    values = {(r.rival_tactic if rival else r.tactic).get(key) for r in found}
    return sorted(v for v in values if v)


def keep(found: list[Row], side: dict | None = None, rival: dict | None = None, league: str = ANY, period: str = "Tudo",
         kind: str = ANY, ground: str = ANY, strength: str = "Qualquer", now: float | None = None) -> list[Row]:
    """The rows that pass every filter. ``side`` / ``rival``: field → wanted value for this side and its rival
    (tactic fields, plus "quem": "Os meus clubes" / "Outros clubes" / a club's name, and "treinador":
    "Humano" / "Computador"). Rows where a wanted field is unknown are left out."""
    side, rival = side or {}, rival or {}
    low, high = STRENGTH_BANDS.get(strength, STRENGTH_BANDS["Qualquer"])
    days = PERIODS.get(period)
    since = (now or datetime.now().timestamp()) - days * 86400 if days else None

    def fits(row_tactic: dict, human, mine: bool, club: str, wanted: dict) -> bool:
        for key, value in wanted.items():
            if value in (None, ANY):
                continue
            if key == "quem":
                if value == "Os meus clubes" and not mine or value == "Outros clubes" and mine:
                    return False
                if value not in ("Os meus clubes", "Outros clubes") and club != value:
                    return False
            elif key == "treinador":
                if human is None or human != (value == "Humano"):
                    return False
            elif row_tactic.get(key) != value:
                return False
        return True

    kept = []
    for r in found:
        if league != ANY and r.league != league or kind != ANY and r.kind != kind:
            continue
        if ground == "Casa" and not (r.home and not r.neutral) or ground == "Fora" and (r.home or r.neutral) \
                or ground == "Neutro" and not r.neutral:
            continue
        if since and r.when < since or not (low < r.edge <= high if high < 1000 else r.edge > low):
            continue
        if fits(r.tactic, r.human, r.mine, r.club, side) and fits(r.rival_tactic, r.rival_human, r.rival_mine, r.rival, rival):
            kept.append(r)
    return kept


# --- summing up --------------------------------------------------------------------------------------------------

def _avg(values) -> float | None:
    values = [v for v in values if v is not None]
    return mean(values) if values else None


def summary(kept: list[Row]) -> dict:
    """What the window shows for the rows a filter kept: how many, the odds by strength against what happened, the
    EV, goals, shots, possession and both squads' strength."""
    n = len(kept)
    if not n:
        return {"n": 0}
    real = tuple(sum(r.points == p for r in kept) / n for p in (3, 1, 0))
    odds = tuple(mean(r.odds[i] for r in kept) for i in range(3))
    return {"n": n, "real": real, "odds": odds,
            "points": mean(r.points for r in kept), "expected": mean(r.expected for r in kept),
            "ev": mean(r.points - r.expected for r in kept),
            "goals": mean(r.goals for r in kept), "against": mean(r.against for r in kept),
            "shots": _avg(r.shots for r in kept), "rival_shots": _avg(r.rival_shots for r in kept),
            "possession": _avg(r.possession for r in kept),
            "strength": mean(r.strength for r in kept), "rival_strength": mean(r.rival_strength for r in kept),
            "eleven": _avg(r.eleven for r in kept), "rival_eleven": _avg(r.rival_eleven for r in kept),
            "edge": mean(r.edge for r in kept)}


def difficulty(row: Row) -> str:
    """The row's band of ``STRENGTH_BANDS`` (the rival's strength against this side's)."""
    for name, (low, high) in list(STRENGTH_BANDS.items())[1:]:
        if (low < row.edge <= high) if high < 1000 else row.edge > low:
            return name
    return "vs muito mais forte"


def tally(kept: list[Row]) -> dict:
    """Wins, draws and losses, and how many of each the odds by strength gave (the "normal")."""
    return {"n": len(kept), "wins": sum(r.points == 3 for r in kept), "draws": sum(r.points == 1 for r in kept),
            "losses": sum(r.points == 0 for r in kept), "normal": tuple(sum(r.odds[i] for r in kept) for i in range(3))}


def verdict(t: dict) -> tuple[str, int]:
    """Wins against the normal, in words: ("9 a mais", 1), ("2 a menos", -1) or ("o esperado", 0) when under one."""
    gap = t["wins"] - t["normal"][0]
    if abs(gap) < 1:
        return "o esperado", 0
    return f"{round(abs(gap))} a {'mais' if gap > 0 else 'menos'}", 1 if gap > 0 else -1


ORDERED = {"mentalidade", "pressao", "tempo"}  # the sliders' bands read best in their own order


def split(kept: list[Row], key: str) -> list[tuple[str, list[Row]]]:
    """The kept rows by one thing: a field of this side's tactic, ``rival:<field>`` for the rival's, ``dificuldade``,
    ``treinador`` (the rival human or the computer) or ``onde`` (home, away, neutral). Most matches first, except the
    sliders and the difficulty (in their own order)."""
    groups: dict[str, list[Row]] = {}
    for r in kept:
        if key == "dificuldade":
            value = difficulty(r)
        elif key == "treinador":
            value = None if r.rival_human is None else "Humano" if r.rival_human else "Computador"
        elif key == "onde":
            value = "Campo neutro" if r.neutral else "Em casa" if r.home else "Fora"
        elif key.startswith("rival:"):
            value = r.rival_tactic.get(key[6:])
        else:
            value = r.tactic.get(key)
        if value:
            groups.setdefault(value, []).append(r)
    found = list(groups.items())
    if key == "dificuldade":
        order = list(STRENGTH_BANDS)
        return sorted(found, key=lambda g: order.index(g[0]))
    if key.split(":")[-1] in ORDERED:
        return sorted(found)
    return sorted(found, key=lambda g: (-len(g[1]), g[0]))
