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
    return {"opponent": theirs.get("name", "?"), "rank": rank, "side": side, "danger": danger,
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


def squad_value(values: dict[int, tuple[int, int]], team_id: int) -> tuple[int, int, float] | None:
    """(place in the league by total squad value, total, average per player) from {team id: (total, players)}."""
    if team_id not in values:
        return None
    order = sorted(values, key=lambda t: -values[t][0])
    total, count = values[team_id]
    return order.index(team_id) + 1, total, total / max(1, count)


def track_sales(state: dict, listed: dict[int, dict], squad: set[int]) -> dict:
    """Follow one club's transfer list between reads. ``listed``: {player id: {"name", "price"}} on the list now;
    ``squad``: the club's player ids now. A player that left the list AND the squad was sold (at the listed price,
    which is what reaches the club's money, owner 2026-10-09). A sale stays on the card until the owner fills a slot
    again: each new listing clears the oldest sale. Returns the new state {"listed": ..., "sales": [...]}."""
    before = {int(k): v for k, v in (state.get("listed") or {}).items()}
    sales = list(state.get("sales") or [])
    if state.get("listed") is not None:  # the very first read only learns what is listed
        sales += [{"name": item["name"], "price": item["price"]} for pid, item in before.items()
                  if pid not in listed and pid not in squad]
        new = sum(1 for pid in listed if pid not in before)
        sales = sales[new:]
    return {"listed": listed, "sales": sales}
