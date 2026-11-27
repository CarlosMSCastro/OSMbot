"""Training camp + secret training in the last 10 minutes before a match (owner, 2026-11-27, D-103; THEORY.md section 6).

Pure: no I/O. The owner lights a lamp on the club's pre-match, match by match, after seeing the price; at 10 minutes
before the match the bot books the secret training and then the camp, never one without the other.

From the site's code (``teamTraining.js`` v4057, DISCOVERY.md section 3): ``POST leagues/{L}/teams/{T}/teamtrainings``
with ``type`` (1 secret training, 2 camp) and ``productId``: the catalogue's products named "Secret" and "Camp", in
its order, the index being how many the club already used this season. ``GET .../teamtrainings`` lists them, each
with the ``week`` before its match (``week + 1`` = the match's ``weekNr``); one with ``week`` = the league's
``weekNr`` is booked for the next match.

The lamp kept in the config (``estagio``)::

    {"215028346_9": {"semana": 37, "jogo": 1764276060.0, "estagio": 50, "secreto": 3, "total": 53, "aceite": ...}}
"""
from __future__ import annotations

SECRET, CAMP = 1, 2  # teamtrainings ``type`` (the site's TeamTrainingType)
NAMES = {SECRET: "Secret", CAMP: "Camp"}  # bosscoinproducts ``name``
LEAD = 10 * 60.0  # the bot books them 10 min before the match (owner, 2026-11-27)
LAST = 60.0  # and tries again every minute until 1 min before it
RETRY = 60.0
OFFICIAL = (0, 1)  # matchType: league, cup (the friendlies have no camp)


def used(trainings: list[dict], kind: int, matches: list[dict] | None = None, team_id: int | None = None) -> int:
    """How many of ``kind`` the club used this season. As the site: only those whose match (``week + 1``) is one of
    the club's league or cup matches; without the matches, all of them ([S] the list is this season's)."""
    mine = [t for t in trainings if isinstance(t, dict) and t.get("type") == kind]
    if matches is None or team_id is None:
        return len(mine)
    weeks = {m.get("weekNr") for m in matches if isinstance(m, dict) and m.get("matchType") in OFFICIAL
             and team_id in (m.get("homeTeamId"), m.get("awayTeamId"))}
    return sum(1 for t in mine if isinstance(t.get("week"), int) and t["week"] + 1 in weeks)


def booked(trainings: list[dict], kind: int, week: int) -> bool:
    """Booked for the next match (the site's ``onTrainingCamp``: ``week`` = the league's ``weekNr``)."""
    return any(isinstance(t, dict) and t.get("type") == kind and t.get("week") == week for t in trainings)


def product(products: list[dict], kind: int, count: int) -> dict | None:
    """The catalogue's next product of ``kind`` after ``count`` used ({"id", "value"}); None when none is left."""
    mine = [p for p in products if isinstance(p, dict) and p.get("name") == NAMES[kind]]
    return mine[count] if 0 <= count < len(mine) else None


def offer(trainings: list[dict], products: list[dict], week: int, matches: list[dict] | None = None,
          team_id: int | None = None) -> dict:
    """What the next match's camp + secret training cost now. ``camp``/``secret``: the product to buy, or None when it
    is already booked (``*_booked``) or none is left this season."""
    result = {}
    for kind, word in ((CAMP, "camp"), (SECRET, "secret")):
        count = used(trainings, kind, matches, team_id)
        done = booked(trainings, kind, week)
        result[f"{word}_booked"] = done
        result[f"{word}_nr"] = count + (0 if done else 1)
        result[word] = None if done else product(products, kind, count)
    result["total"] = sum((result[w] or {}).get("value") or 0 for w in ("camp", "secret"))
    return result


def why_not(item: dict) -> str | None:
    """Why the lamp cannot be lit (None when it can): both must be there, or already booked (owner: never the secret
    training alone; THEORY.md section 21)."""
    if item["camp_booked"] and item["secret_booked"]:
        return "Estágio e treino secreto já marcados"
    if not item["camp"] and not item["camp_booked"]:
        return "Sem estágios nesta época (6 de 6)"
    if not item["secret"] and not item["secret_booked"]:
        return "Sem treinos secretos nesta época (6 de 6)"
    return None


def question(club: str, rival: str | None, item: dict, at: str) -> str:
    """What the window asks before lighting the lamp, with the cost."""
    parts = []
    if item["camp"]:
        parts.append(f"estágio n.º {item['camp_nr']} ({item['camp']['value']} BC)")
    if item["secret"]:
        parts.append(f"treino secreto ({item['secret']['value']} BC)")
    match = f"{club} × {rival}" if rival else club
    return f"{match}: {' + '.join(parts)} = {item['total']} BC às {at}. Ligar?"


def lamp(item: dict, week: int, match: float, now: float) -> dict:
    """The lamp as kept once the owner says yes: what he accepted to pay."""
    return {"semana": week, "jogo": match, "estagio": (item["camp"] or {}).get("value") or 0,
            "secreto": (item["secret"] or {}).get("value") or 0, "total": item["total"], "aceite": now}


def valid(light: dict | None, week: int, match: float | None, now: float) -> bool:
    """A lamp counts only for the match it was lit for, and only until it."""
    return bool(light) and light.get("semana") == week and match is not None and light.get("jogo") == match and now < match


def due(match: float, now: float) -> bool:
    """Within the last 10 minutes and before the last one."""
    return match - LEAD <= now < match - LAST


def decide(light: dict | None, item: dict, week: int, match: float | None, now: float) -> str:
    """What to do with a club now: "none" (no lamp, or not for this match), "wait" (before the 10 min), "done" (both
    booked), "dearer" (it costs more than the owner accepted), "missing" (none left), "late" (the last minute came and
    they are not booked), "book"."""
    if not valid(light, week, match, now):
        return "none"
    if item["camp_booked"] and item["secret_booked"]:
        return "done"
    if now >= match - LAST:
        return "late"
    if now < match - LEAD:
        return "wait"
    if why_not(item):
        return "missing"
    if ((item["camp"] or {}).get("value") or 0) > (light.get("estagio") or 0) \
            or ((item["secret"] or {}).get("value") or 0) > (light.get("secreto") or 0):
        return "dearer"
    return "book"


def to_book(item: dict) -> list[tuple[int, dict]]:
    """The secret training first, then the camp (the site's advice: with the secret training first he is not warned
    of the camp), each only if not booked yet."""
    return [(kind, item[word]) for kind, word in ((SECRET, "secret"), (CAMP, "camp")) if item[word]]
