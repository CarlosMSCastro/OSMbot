"""Watch the game's transfer engine in one league, from reads of its transfer list (D-034). Pure: no network.

The game buys players listed by managers a few times a day ("8 times a day at random intervals", staff;
DISCOVERY.md section 6c) and, on each of those rounds, lowers a little the price of the players it listed itself
(clubs from outside the league, ``team.isForeignTeam``). So, between two reads of the list:

- a game listing that is cheaper than before = the engine went round (hypothesis to check with these records);
- a manager's listing that is gone = sold (if it shows in the league's transfers) or taken off the list.

Each change is one record: when (between which two reads), what was for sale at the read before (price, value,
age, ratings, whose), and what left. With time this says how likely a sale is per price and per % of the maximum.
"""
from __future__ import annotations

GAP = 15 * 60  # s: reads further apart than this can't place a round well; the record says so ("lacuna")
MAX_PRICE = 2.5  # the game's maximum asking price ≈ 2.5 × value (THEORY.md 7.5)
SALE_RATIO = 1.5  # the "SALE" ribbon: price <= 1.5 × value (gamesettings SaleTransferLabelRatio = 150, web code; 2026-10-12)
MAIN_STAT = {1: "statAtt", 2: "statOvr", 3: "statDef", 4: "statDef"}  # the number in bold for each position
POSITIONS = {1: "ATA", 2: "MED", 3: "DEF", 4: "GR"}


def _row(item: dict, owner: int | None) -> dict:
    player, team = item.get("player") or {}, item.get("team") or {}
    value = player.get("value") or 0
    price = item.get("price") or 0
    return {"anuncio": item["id"], "jogador": player.get("id"), "equipa": item.get("teamId"),
            "utilizador": bool(team.get("userId")), "dono": bool(owner) and team.get("userId") == owner,
            "preco": price, "valor": value, "do_maximo": round(price / (MAX_PRICE * value), 3) if value else None,
            "idade": player.get("age"), "pos": player.get("position"), "ovr": player.get("statOvr"),
            "att": player.get("statAtt"), "def": player.get("statDef"), "desde": item.get("timeStampForSale")}


def split(market: list[dict], owner: int | None = None) -> tuple[dict[str, int], dict[str, dict]]:
    """({game listing id: price}, {manager listing id: row}). Keys are text, to survive a JSON round trip."""
    game, people = {}, {}
    for item in market:
        if (item.get("team") or {}).get("isForeignTeam"):
            game[str(item["id"])] = item.get("price") or 0
        else:
            people[str(item["id"])] = _row(item, owner)
    return game, people


def observe(state: dict | None, market: list[dict], now: float, owner: int | None = None) -> tuple[dict, dict | None]:
    """The new state of the league and, when something changed since the last read, the record of it."""
    game, people = split(market, owner)
    new_state = {"t": now, "jogo": game, "pessoas": people}
    if not state:  # the first read only learns what is listed
        return new_state, None
    before_game, before_people = state.get("jogo") or {}, state.get("pessoas") or {}
    drops = sum(1 for key, price in game.items() if key in before_game and price < before_game[key])
    gone = [key for key in before_people if key not in people]
    if not drops and not gone:
        return new_state, None
    record = {"t": now, "antes": state.get("t"), "lacuna": now - (state.get("t") or 0) > GAP,
              "descidas": drops, "jogo_novos": sum(1 for key in game if key not in before_game),
              "jogo_saidos": sum(1 for key in before_game if key not in game),
              "a_venda": list(before_people.values()), "sairam": [before_people[key]["jogador"] for key in gone]}
    return new_state, record


def sale_rows(market: list[dict], ratio: float = SALE_RATIO) -> dict[str, dict]:
    """The game's players with the "SALE" ribbon (never a manager's: the owner buys only from the game, THEORY.md 7.6)."""
    rows = {}
    for item in market:
        player, team = item.get("player") or {}, item.get("team") or {}
        value, price = player.get("value") or 0, item.get("price") or 0
        if team.get("userId") or not value or price > ratio * value:
            continue
        position = player.get("position")
        rows[str(item["id"])] = {"anuncio": item["id"], "jogador": player.get("id"), "nome": player.get("name"),
                                 "pos": POSITIONS.get(position), "rating": player.get(MAIN_STAT.get(position, "statOvr")),
                                 "idade": player.get("age"), "preco": price, "valor": value,
                                 "razao": round(price / value, 2), "fora_da_liga": bool(team.get("isForeignTeam")),
                                 "desde": item.get("timeStampForSale")}
    return rows


def sale_options(market: list[dict], position: str, budget: int, count: int = 3) -> list[dict]:
    """The "SALE" players of one position (ATA/MED/DEF/GR) the club can pay for, best rating first (THEORY.md 16)."""
    rows = [r for r in sale_rows(market).values() if r["pos"] == position and r["preco"] <= budget]
    return sorted(rows, key=lambda r: (-(r["rating"] or 0), r["preco"]))[:count]


BARGAIN = 1.1  # a "SALE" at no more than this × value is a bargain (owner, 2026-10-14)
BIG_SALE, BIG_SALE_SHARE = 100e6, 0.75  # above 100 M the owner asks 75 % of the maximum (THEORY.md 7)
SELLS_AT_MAX = 2.4  # a league sale at this × value or more: the league buys at the maximum (THEORY.md 7.7)


def resale(value: float) -> float:
    """What the owner would ask for a player when listing it: the maximum (≈ 2.5 × value, a hypothesis from the
    sales of 2026-10-14), or 75 % of it above 100 M."""
    top = MAX_PRICE * value
    return BIG_SALE_SHARE * top if top > BIG_SALE else top


def sells_at_max(transfers: list[dict], now: float, days: float = 3) -> bool:
    """Whether a club of this league sold at the maximum in the last days (else the resale profit is uncertain:
    a league whose market buys only below it, DISCOVERY.md)."""
    return any(not (t.get("sourceTeam") or {}).get("isForeignTeam") and (t.get("sourceTeam") or {}).get("id")
               and t.get("value") and t.get("price", 0) >= SELLS_AT_MAX * t["value"]
               and t.get("timestamp", 0) >= now - days * 86400 for t in transfers)


def sale_picks(market: list[dict], players: list[dict], money: float, free_slots: int, count: int = 3) -> list[dict]:
    """The "SALE" players worth a look on the club card (THEORY.md 7.7): those the club can pay for, best estimated
    resale profit first. Each says if it beats the lowest starter of its general position (``reforco``: shown even
    with no free sale slot), and if it is a bargain (``pechincha``, at most 1.1 × value). A pure deal needs a free
    slot, to list it again at once."""
    from osmbot.theory.lineup import rating

    weakest: dict[str, dict] = {}
    for p in players:
        position = POSITIONS.get(p.get("position"))
        if position and p.get("lineup") in range(1, 12) and (position not in weakest or rating(p) < rating(weakest[position])):
            weakest[position] = p
    picks = []
    for row in sale_rows(market).values():
        if row["preco"] > money:
            continue
        low = weakest.get(row["pos"])
        better = bool(low) and (row["rating"] or 0) > rating(low)
        if not better and free_slots <= 0:
            continue
        picks.append({**row, "lucro": resale(row["valor"]) - row["preco"], "reforco": better,
                      "fraco": f"{low['name']} {rating(low)}" if better else None, "pechincha": row["razao"] <= BARGAIN})
    return sorted(picks, key=lambda r: -r["lucro"])[:count]


def sale_changes(before: dict | None, rows: dict[str, dict], now: float) -> tuple[dict, list[dict], list[dict]]:
    """(new "SALE" state, those that appeared, those that left) between two reads. Each keeps when it was first seen;
    the first read only learns what is there."""
    state = {key: {**row, "visto": (before or {}).get(key, {}).get("visto", now)} for key, row in rows.items()}
    if before is None:
        return state, [], []
    appeared = [state[key] for key in rows if key not in before]
    gone = [{**row, "durou": now - row["visto"]} for key, row in before.items() if key not in rows]
    return state, appeared, gone


def describe_sales(appeared: list[dict], league: str, money) -> str:
    """The log line for new "SALE" players, best first."""
    best = sorted(appeared, key=lambda r: -(r["rating"] or 0))
    shown = "; ".join(f"{r['pos']} {r['rating']} {r['nome']} ({r['idade']} anos) {money(r['preco'])}" for r in best[:5])
    more = f" e mais {len(best) - 5}" if len(best) > 5 else ""
    return f"SALE novos ({league}): {len(best)} · {shown}{more}"


def classify(record: dict, transfers: list[dict], slack: float = 120.0) -> dict:
    """Split the players that left the list into sold (seen in the league's transfers between the two reads,
    give or take ``slack`` seconds) and taken off; keeps the time of each sale."""
    start, end = (record.get("antes") or 0) - slack, record["t"] + slack
    sold = {}
    for row in transfers:
        player = (row.get("player") or {}).get("id")
        if player in record["sairam"] and start <= (row.get("timestamp") or 0) <= end:
            sold[player] = row.get("timestamp")
    return {**record, "vendidos": [{"jogador": p, "quando": t} for p, t in sold.items()],
            "retirados": [p for p in record["sairam"] if p not in sold]}


def describe(record: dict, league: str, clock) -> str:
    """The log line: when the engine went round, how many managers' players were for sale, how many sold
    (and how many of them were the owner's)."""
    listed = [r for r in record["a_venda"] if r["utilizador"]]
    sold = {s["jogador"] for s in record.get("vendidos", [])}
    mine = [r for r in listed if r["dono"]]
    mine_sold = sum(1 for r in mine if r["jogador"] in sold)
    when = f"entre {clock(record['antes'])} e {clock(record['t'])}"
    seen = "passou" if record["descidas"] else "sem descida de preços"
    return (f"Motor de transferências ({league}): {seen} {when}; vendidos {len(sold)} de {len(listed)} à venda "
            f"(teus: {mine_sold} de {len(mine)})")
