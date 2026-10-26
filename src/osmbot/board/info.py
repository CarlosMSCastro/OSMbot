"""What the club card shows beyond the plain numbers (D-026): next match, cup, squad value, sales. Pure: no network."""
from __future__ import annotations

import re

LEAGUE_MATCH, CUP_MATCH = 0, 1  # matchType in matches/filter (DISCOVERY.md section 3)
DIRECT_RIVAL = 2  # places apart in the table that make a match a direct confrontation (THEORY.md section 1)
CUP_NAMES = {"Preliminaries": "pré-eliminatória", "Round of 64": "32 avos-de-final", "Round of 32": "16 avos-de-final",
             "Round of 16": "oitavos-de-final", "Quarter-finals": "quartos-de-final", "Semi-finals": "meias-finais",
             "Final": "final"}


def _side(match: dict, team_id: int) -> tuple[int, str]:
    home = match["homeTeamId"] == team_id
    return (match["awayTeamId"] if home else match["homeTeamId"]), ("H" if home else "A")


def next_match(matches: list[dict], teams: list[dict], team_id: int, week: int) -> dict | None:
    """The club's next official match after ``week`` (the last one played): opponent, its place, (H)ome/(A)way,
    whether it is a direct confrontation (1 or 2 places apart) and whether it is a cup match."""
    ahead = next_matches(matches, teams, team_id, week, 1)
    return ahead[0] if ahead else None


def next_matches(matches: list[dict], teams: list[dict], team_id: int, week: int, count: int = 2) -> list[dict]:
    """The club's next ``count`` official matches after ``week``, each as ``next_match`` gives it (THEORY.md 16:
    the one after the next, to rest a starter before it)."""
    ahead = sorted((m for m in matches if team_id in (m["homeTeamId"], m["awayTeamId"])
                    and m["matchType"] in (LEAGUE_MATCH, CUP_MATCH) and m["weekNr"] > week), key=lambda m: m["weekNr"])
    return [_upcoming(m, teams, team_id) for m in ahead[:count]]


def _upcoming(match: dict, teams: list[dict], team_id: int) -> dict:
    opponent, side = _side(match, team_id)
    places = {t["id"]: t for t in teams}
    mine, theirs = places.get(team_id, {}).get("ranking"), places.get(opponent, {})
    rank = theirs.get("ranking")
    danger = bool(mine and rank and abs(rank - mine) <= DIRECT_RIVAL)
    return {"opponent": theirs.get("name", "?"), "opponent_id": opponent, "rank": rank, "side": side, "danger": danger,
            "cup": match["matchType"] == CUP_MATCH, "referee_id": match.get("refereeId"),
            "neutral": bool(match.get("isPlayedOnNeutralGround"))}


def cup_phase(rounds: list[dict], matches: list[dict], team_id: int, week: int) -> tuple[str, str]:
    """(text, state): the round the club plays next ("quartos-de-final"), "eliminado nos oitavos-de-final",
    "vencedor", or "—" when the club is not in the cup. state: "in", "out", "won" or "none"."""
    names = {r["weekNr"]: CUP_NAMES.get(r["name"], r["name"]) for r in rounds}
    cup = sorted((m for m in matches if m["matchType"] == CUP_MATCH and team_id in (m["homeTeamId"], m["awayTeamId"])),
                 key=lambda m: m["weekNr"])
    ahead = [m for m in cup if m["weekNr"] > week]
    if ahead:
        return names.get(ahead[0]["weekNr"], "?"), "in"
    played = [m for m in cup if m["weekNr"] <= week]
    if not played:
        future = sorted(r["weekNr"] for r in rounds if r["weekNr"] > week)
        return (names[future[0]], "in") if future and rounds else ("—", "none")
    last = played[-1]
    if last["winnerTeamId"] != team_id:
        return f"eliminado nos {names.get(last['weekNr'], '?')}", "out"
    if rounds and last["weekNr"] == max(r["weekNr"] for r in rounds):
        return "vencedor", "won"
    later = sorted(r["weekNr"] for r in rounds if r["weekNr"] > last["weekNr"])
    return (names[later[0]], "in") if later else ("vencedor", "won")


def squad_value(values: dict[int, tuple[int, int]], team_id: int) -> tuple[int, int, float, int, int] | None:
    """(place in the league by total squad value, total, average per player, players, teams in the league) from
    {team id: (total, players)}."""
    if team_id not in values:
        return None
    order = sorted(values, key=lambda t: -values[t][0])
    total, count = values[team_id]
    return order.index(team_id) + 1, total, total / max(1, count), count, len(values)


def value_table(values: dict[int, tuple[int, int]], names: dict[int, str], team_id: int) -> list[tuple]:
    """The league's table by squad value around the club (owner, 2026-10-15), as the game's: the 2 below when it is
    1st, else 1 above and 1 below. Rows (place, name, total, players, average, mine)."""
    if team_id not in values:
        return []
    order = sorted(values, key=lambda t: -values[t][0])
    at = order.index(team_id)
    picked = order[:3] if at == 0 else order[at - 1:at + 2]
    return [(order.index(t) + 1, names.get(t, "?"), values[t][0], values[t][1], values[t][0] / max(1, values[t][1]), t == team_id)
            for t in picked]


def track_sales(state: dict, listed: dict[int, dict], squad: set[int], now: float | None = None) -> dict:
    """Follow one club's transfer list between reads. ``listed``: {player id: {"name", "price", "value"}} on the list
    now; ``squad``: the club's player ids now. A player that left the list AND the squad was sold (at the listed
    price, which is what reaches the club's money, owner 2026-10-09). A sale stays on the card until the owner fills
    a slot again: each new listing clears the oldest sale. Returns the new state {"listed": ..., "sales": [...]} and,
    for the log, what happened since the last read: "new_listings" and "new_sales".

    Times (owner, 2026-10-10, for the 100 M€ study): each listing keeps "since", when it was listed (the game's
    ``timeStampForSale`` when given; else the read that first saw it, None when already listed at the very first
    read); each sale has "since" and "sold", the read that saw it gone (as close as the bot's reads, a few minutes)."""
    before = {int(k): v for k, v in (state.get("listed") or {}).items()}
    first = state.get("listed") is None  # the very first read only learns what is listed
    listed = {pid: {**item, "since": item.get("since") or (None if first else before.get(pid, {"since": now}).get("since"))}
              for pid, item in listed.items()}
    sales = list(state.get("sales") or [])
    new_listings, new_sales = [], []
    if not first:
        new_sales = [{**item, "player": pid, "sold": now} for pid, item in before.items() if pid not in listed and pid not in squad]
        new_listings = [item for pid, item in listed.items() if pid not in before]
        sales = (sales + new_sales)[len(new_listings):]
    known = state.get("squad")  # the squad at the last read; None before the first one (owner, 2026-10-22: the buys)
    new_members = sorted(squad - set(known)) if known is not None else []
    return {"listed": listed, "sales": sales, "squad": sorted(squad), "new_listings": new_listings,
            "new_sales": new_sales, "new_members": new_members}



def settle_sales(sales: list[dict], transfers: list[dict], team_id: int) -> None:
    """Each new sale as the league's transfers have it (2026-10-16), changed in place. What the bot last saw of a
    listing can be old: with the bot stopped, or on another PC (``~/.osmbot`` is per machine), the owner may have
    listed the player again at another price. A sale found in the transfers (the club as the seller) takes its price
    and time from there (``confirmada``); when that price is not the one last seen, the player was listed again
    meanwhile and the time he went on the list is unknown (``since`` None)."""
    for sale in sales:
        found = [t for t in transfers if (t.get("player") or {}).get("id") == sale.get("player")
                 and (t.get("sourceTeam") or {}).get("id") == team_id and t.get("price")]
        if not found:
            continue
        last = max(found, key=lambda t: t.get("timestamp") or 0)
        if last["price"] != sale["price"]:
            sale["since"] = None
        sale.update(price=last["price"], sold=last.get("timestamp") or sale["sold"], confirmada=True)
    for sale in sales:  # what the club paid for him, for the profit (THEORY.md 7.5, owner 2026-10-22)
        buy = _last_buy(transfers, sale.get("player"), team_id, sale.get("sold"))
        if buy:
            sale.update(bought=buy["price"], bought_at=buy.get("timestamp"))


def _last_buy(transfers: list[dict], player: int | None, team_id: int, before: float | None = None) -> dict | None:
    found = [t for t in transfers if (t.get("player") or {}).get("id") == player
             and (t.get("destinationTeam") or {}).get("id") == team_id and t.get("price")
             and (before is None or (t.get("timestamp") or 0) <= before)]
    return max(found, key=lambda t: t.get("timestamp") or 0, default=None)


def purchases(new_members: list[int], transfers: list[dict], team_id: int) -> list[dict]:
    """The players new in the squad that the club bought (THEORY.md 7.5): name, price, value, seller. A player from a
    pack or the youth has no purchase in the league's transfers and is left out."""
    bought = []
    for pid in new_members:
        buy = _last_buy(transfers, pid, team_id)
        if buy:
            bought.append({"name": (buy.get("player") or {}).get("name", "?"), "price": buy["price"],
                           "value": buy.get("value") or 0, "from": (buy.get("sourceTeam") or {}).get("name")})
    return bought


SALE_BANDS = (5e6, 15e6, 50e6, 100e6)  # the price bands of the "parado na lista" warning (THEORY.md 7.5)
STALE_FACTOR = 2  # warned past twice the band's median time
STALE_MIN_SALES = 3  # a band with fewer sales does not warn


def _band(price: float) -> int:
    return sum(1 for limit in SALE_BANDS if price >= limit)


def stale_listings(listed: dict[int, dict], history: list[tuple[float, float]], now: float) -> list[dict]:
    """The owner's players on the list for more than twice the usual time at their price (owner, 2026-10-22).
    ``listed``: {player id: {"name", "price", "since"}}; ``history``: (price, seconds it took) of the sales logged.
    Returns [{"name", "for", "normal"}] (seconds), longest first."""
    times: dict[int, list[float]] = {}
    for price, took in history:
        times.setdefault(_band(price), []).append(took)
    stale = []
    for item in listed.values():
        took = sorted(times.get(_band(item.get("price") or 0)) or [])
        if len(took) < STALE_MIN_SALES or item.get("since") is None:
            continue
        half = len(took) // 2
        normal = took[half] if len(took) % 2 else (took[half - 1] + took[half]) / 2
        if now - item["since"] > STALE_FACTOR * normal:
            stale.append({"name": item.get("name", "?"), "for": now - item["since"], "normal": normal})
    return sorted(stale, key=lambda s: -s["for"])


_SALE_LINE = re.compile(r"Venda: (.+?) \((.+?)\) vendido por ([\d,]+) (M|k)\b.*?, vendido (?:às|até) ([^,;]+)"
                        r", demorou (?:(\d+) dias? e )?(\d+)h(\d+)")


def sale_time(line: str) -> tuple[tuple[str, str, str], float, float] | None:
    """A "Venda:" line of the log as (who, club, when sold), price, seconds it took; None without the time."""
    found = _SALE_LINE.search(line)
    if not found:
        return None
    name, club, amount, unit, sold, days, hours, minutes = found.groups()
    price = float(amount.replace(",", ".")) * (1e6 if unit == "M" else 1e3)
    return (name, club, sold), price, ((int(days or 0) * 24 + int(hours)) * 60 + int(minutes)) * 60

ELEVEN = 11
MAIN_STAT = {1: "statAtt", 2: "statOvr", 3: "statDef", 4: "statDef"}  # the number in bold for each position


def team_rating(players: list[dict], formation: int | None = None) -> int | None:
    """The team's strength as the game shows it: the average main rating of the best player for each place of the
    club's current formation (how many DEF/MED/ATA its eleven has, and 1 GR), rounded (DISCOVERY.md, checked on 3
    clubs, 2026-10-13). None when the eleven is not known: the game shows another club's only after the analysis.
    ``formation`` (the tactics' 433, 532…): the shape from it, so a hole in the eleven (an injured starter taken
    out) does not hide the club's own strength (owner, 2026-10-13)."""
    digits = [int(d) for d in str(formation or "")]
    if len(digits) == 3 and sum(digits) == 10:
        shape = {4: 1, 3: digits[0], 2: digits[1], 1: digits[2]}
    else:
        eleven = [p for p in players if 1 <= (p.get("lineup") or 0) <= ELEVEN]
        if len(eleven) < ELEVEN:
            return None
        shape = {pos: sum(1 for p in eleven if p.get("position") == pos) for pos in MAIN_STAT}
    best = []
    for pos, count in shape.items():
        best += sorted((p.get(MAIN_STAT[pos]) or 0 for p in players if p.get("position") == pos), reverse=True)[:count]
    return round(sum(best) / len(best)) if best else None


def eleven_seen(players: list[dict]) -> bool:
    """Whether another club's whole eleven is to be seen (after the analysis, with no hole in it)."""
    return sum(1 for p in players if 1 <= (p.get("lineup") or 0) <= ELEVEN) >= ELEVEN


def opponent_rating(players: list[dict], guess: int) -> int | None:
    """Another club's strength for the formation rule: his eleven's once analysed; before the analysis (no eleven to
    see, owner 2026-10-25: his squad already says he is stronger) or with a hole in it (a player sold, injured or not
    yet put back, owner 2026-10-24), an estimate: his best in the ``guess`` formation (THEORY.md section 1)."""
    return team_rating(players) if eleven_seen(players) else team_rating(players, guess)


def league_summary(standings: list[dict], teams: list[dict], matches: list[dict], team_id: int, week: int,
                   goal: int | None) -> dict | None:
    """The hover on the club's place (owner, 2026-10-13; THEORY.md section 19): the top 3 with their points (the top 2
    and the club when it is below 3rd), the season's goal, and whether the title is mathematically won. Rows:
    (place, name, points, mine, games played, goal difference), the columns of the game's table (owner, 2026-10-15)."""
    points = {row["teamId"]: row.get("points") or 0 for row in standings}
    record = {row["teamId"]: ((row.get("won") or 0) + (row.get("drew") or 0) + (row.get("lost") or 0),
                              (row.get("goalsFor") or 0) - (row.get("goalsAgainst") or 0)) for row in standings}
    table = sorted((t for t in teams if t.get("ranking")), key=lambda t: t["ranking"])
    if not points or not table:
        return None
    mine = next((t for t in table if t["id"] == team_id), None)
    shown = table[:3] if not mine or mine["ranking"] <= 3 else table[:2] + [mine]
    rows = [(t["ranking"], t["name"], points.get(t["id"], 0), t["id"] == team_id, *record.get(t["id"], (0, 0))) for t in shown]
    champion = False
    if mine and mine["ranking"] == 1 and len(table) > 1:
        second = table[1]["id"]
        left = sum(1 for m in matches if m.get("matchType") == LEAGUE_MATCH and m["weekNr"] > week
                   and second in (m["homeTeamId"], m["awayTeamId"]))
        champion = points.get(second, 0) + 3 * left < points.get(team_id, 0)
    return {"rows": rows, "goal": goal, "champion": champion}
