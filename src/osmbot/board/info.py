"""What the club card shows beyond the plain numbers (D-026): next match, cup, squad value, sales. Pure: no network."""
from __future__ import annotations

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
    ahead = sorted((m for m in matches if team_id in (m["homeTeamId"], m["awayTeamId"])
                    and m["matchType"] in (LEAGUE_MATCH, CUP_MATCH) and m["weekNr"] > week), key=lambda m: m["weekNr"])
    if not ahead:
        return None
    opponent, side = _side(ahead[0], team_id)
    places = {t["id"]: t for t in teams}
    mine, theirs = places.get(team_id, {}).get("ranking"), places.get(opponent, {})
    rank = theirs.get("ranking")
    danger = bool(mine and rank and abs(rank - mine) <= DIRECT_RIVAL)
    return {"opponent": theirs.get("name", "?"), "opponent_id": opponent, "rank": rank, "side": side, "danger": danger,
            "cup": ahead[0]["matchType"] == CUP_MATCH}


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
        new_sales = [{**item, "sold": now} for pid, item in before.items() if pid not in listed and pid not in squad]
        new_listings = [item for pid, item in listed.items() if pid not in before]
        sales = (sales + new_sales)[len(new_listings):]
    return {"listed": listed, "sales": sales, "new_listings": new_listings, "new_sales": new_sales}


ELEVEN = 11
MAIN_STAT = {1: "statAtt", 2: "statOvr", 3: "statDef", 4: "statDef"}  # the number in bold for each position


def team_rating(players: list[dict]) -> int | None:
    """The team's strength as the game shows it: the average main rating of the best player for each place of the
    club's current formation (how many DEF/MED/ATA its eleven has, and 1 GR), rounded (DISCOVERY.md, checked on 3
    clubs, 2026-10-13). None when the eleven is not known: the game shows another club's only after the analysis."""
    eleven = [p for p in players if 1 <= (p.get("lineup") or 0) <= ELEVEN]
    if len(eleven) < ELEVEN:
        return None
    shape = {pos: sum(1 for p in eleven if p.get("position") == pos) for pos in MAIN_STAT}
    best = []
    for pos, count in shape.items():
        best += sorted((p.get(MAIN_STAT[pos]) or 0 for p in players if p.get("position") == pos), reverse=True)[:count]
    return round(sum(best) / len(best)) if best else None


def league_summary(standings: list[dict], teams: list[dict], matches: list[dict], team_id: int, week: int,
                   goal: int | None) -> dict | None:
    """The hover on the club's place (owner, 2026-10-13; THEORY.md section 19): the top 3 with their points (the top 2
    and the club when it is below 3rd), the season's goal, and whether the title is mathematically won."""
    points = {row["teamId"]: row.get("points") or 0 for row in standings}
    table = sorted((t for t in teams if t.get("ranking")), key=lambda t: t["ranking"])
    if not points or not table:
        return None
    mine = next((t for t in table if t["id"] == team_id), None)
    shown = table[:3] if not mine or mine["ranking"] <= 3 else table[:2] + [mine]
    rows = [(t["ranking"], t["name"], points.get(t["id"], 0), t["id"] == team_id) for t in shown]
    champion = False
    if mine and mine["ranking"] == 1 and len(table) > 1:
        second = table[1]["id"]
        left = sum(1 for m in matches if m.get("matchType") == LEAGUE_MATCH and m["weekNr"] > week
                   and second in (m["homeTeamId"], m["awayTeamId"]))
        champion = points.get(second, 0) + 3 * left < points.get(team_id, 0)
    return {"rows": rows, "goal": goal, "champion": champion}
