"""Training camp + secret training 10 minutes before the match, when the owner lit the lamp (D-103; THEORY.md
section 6). The rules are in ``osmbot.prematch.camp``; here the reads, the writes and the lamps kept in the config.

The write comes from the site's code (``teamTraining.js`` v4057), never observed before the first real use: the
owner's yes on the lamp is his OK (rule 5). Each booking is confirmed with a read and the wallet before and after.
"""
from __future__ import annotations

import time

from osmbot import logs
from osmbot.game import wallet as ledger
from osmbot.prematch import camp as rules

PREF = "estagio"  # the lamps, in ~/.osmbot/config.json
PAUSE_BETWEEN_WRITES = 1.5  # seconds
_products: list[dict] = []  # bosscoinproducts: the same for everyone, read once
_warned: set[tuple[str, int]] = set()  # (club, week) already told it could not be booked


def lamps() -> dict:
    from osmbot.i18n import get_pref

    kept = get_pref(PREF, {})
    return kept if isinstance(kept, dict) else {}


def lamp(key: str) -> dict | None:
    light = lamps().get(key)
    return light if isinstance(light, dict) else None


def set_lamp(key: str, light: dict | None) -> None:
    """Light (``light``) or put out (None) a club's lamp."""
    from osmbot.i18n import set_pref

    kept = lamps()
    if light is None:
        kept.pop(key, None)
    else:
        kept[key] = light
    set_pref(PREF, kept)


def soon(now: float, ahead: float = 0.0) -> bool:
    """A lit lamp whose 10 minutes start within ``ahead`` seconds (the videos give way to it)."""
    return any(isinstance(l, dict) and isinstance(l.get("jogo"), (int, float))
               and l["jogo"] - rules.LEAD - ahead <= now < l["jogo"] for l in lamps().values())


def products(client) -> list[dict]:
    if not _products:
        status, body = client.get("bosscoinproducts")
        if status == 200 and isinstance(body, list):
            _products.extend(p for p in body if isinstance(p, dict) and p.get("name") in rules.NAMES.values())
    return _products


def read_offer(client, team: dict, base: str, week: int, matches: list[dict] | None = None) -> dict:
    """What the next match's camp + secret training cost now (reads only)."""
    status, trainings = client.get(f"{base}/teamtrainings")  # 404 when the club never had one
    trainings = trainings if status == 200 and isinstance(trainings, list) else []
    return rules.offer(trainings, products(client), week, matches, team["id"])


def _wallet(client) -> int | None:
    status, body = client.get("user/bosscoinwallet")
    return body.get("amount") if status == 200 and isinstance(body, dict) else None


def book_club(client, team: dict, base: str, key: str, week: int, match: float | None, now: float, confirm: bool,
              log, matches: list[dict] | None = None) -> float | None:
    """One club: book the camp + secret training if its lamp is lit and it is time. Returns when to look again."""
    light = lamp(key)
    if not light:
        return None
    if not rules.valid(light, week, match, now):  # its match went by (or another one is next): the lamp goes out
        if match is not None:  # (a failed read of the match leaves it as it is)
            set_lamp(key, None)
        return None
    item = read_offer(client, team, base, week, matches)
    action = rules.decide(light, item, week, match, now)
    name = team.get("name", "?")
    if action == "wait":
        return match - rules.LEAD
    if action == "done":
        log(f"Estágio + secreto: {name} já marcados")
        set_lamp(key, None)
        return None
    if action in ("late", "missing", "dearer"):
        half = " (só o treino secreto ficou marcado)" if item["secret_booked"] else (
            " (só o estágio ficou marcado)" if item["camp_booked"] else "")
        reason = {"late": "o jogo está a 1 min e não ficaram marcados" + half,
                  "missing": rules.why_not(item) or "?",
                  "dearer": f"custa agora {item['total']} BC, aceitaste {light.get('total')} BC"}[action]
        log(f"! Estágio não ligado: {name} ({reason})")
        set_lamp(key, None)
        return None
    if not confirm:
        log(f"{name}: ligaria o treino secreto e o estágio ({item['total']} BC)")
        return None
    coins = _wallet(client)
    if coins is not None and coins < item["total"]:
        log(f"! Estágio não ligado: {name} (sem boss coins: {coins} de {item['total']})")
        set_lamp(key, None)
        return None
    for kind, bought in rules.to_book(item):
        word = "estágio" if kind == rules.CAMP else "treino secreto"
        status, body = client.post(f"{base}/teamtrainings", {"type": kind, "productId": bought["id"]})
        time.sleep(PAUSE_BETWEEN_WRITES)
        if status != 200:
            text = body if isinstance(body, str) else str(body)
            log(f"Estágio: {name}, {word} falhou ({status}): {text[:200] or 'vazia'}; tento outra vez dentro de 1 min")
            return now + rules.RETRY
    after = read_offer(client, team, base, week, matches)
    if not (after["camp_booked"] and after["secret_booked"]):
        log(f"Estágio: {name}, o jogo ainda não os mostra marcados; vejo outra vez dentro de 1 min")
        return now + rules.RETRY
    left = _wallet(client)
    paid = coins - left if coins is not None and left is not None else item["total"]
    ledger.note("estágio", -paid)
    at = time.strftime("%H:%M", time.localtime(now))
    log(f"Estágio + secreto: {name}, {at}, {paid} BC" + (f" (esperado {item['total']})" if paid != item["total"] else ""))
    logs.record("estagios", {"clube": base, "semana": week, "jogo": match, "estagio_n": item["camp_nr"],
                             "custo": item["total"], "pago": paid, "aceite": light.get("total")})
    set_lamp(key, None)
    return None


def run_camps(confirm: bool, log=None) -> tuple[int, list[float]]:
    """Every club with a lit lamp. Returns (failures, times to wake at)."""
    from osmbot import settings
    from osmbot.game.client import NeedsBrowserLogin, OsmClient
    from osmbot.game.prematch import _match_time
    from osmbot.game.trainings import _teams

    log = log or print
    kept = lamps()
    if not kept:
        return 0, []
    wake: list[float] = []
    try:
        client = OsmClient()
        for _, team, base in _teams(client, writing=True):
            key = settings.club_key(team)
            if key not in kept:
                continue
            league = base.rsplit("/teams/", 1)[0]
            _, info = client.get(league)
            week = info.get("weekNr") if isinstance(info, dict) else None
            _, matches = client.get(f"{league}/matches/filter")
            at = book_club(client, team, base, key, week, _match_time(client, base), time.time(), confirm, log,
                           matches if isinstance(matches, list) else None)
            if at:
                wake.append(at)
    except NeedsBrowserLogin as error:
        raise SystemExit(str(error))
    return 0, wake
