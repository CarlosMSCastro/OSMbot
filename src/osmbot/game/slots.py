"""Read-only: how many transfer-list slots each club has free (see DISCOVERY.md, 2026-10-05).

The limit is the game setting ``MaxPlayersOnTransferlist`` (4 normally, 6 in events); a slot is
used by each of the owner's players listed in ``transferplayers/0``.
"""
from __future__ import annotations

from dataclasses import dataclass

MAX_SLOTS_SETTING = "MaxPlayersOnTransferlist"


@dataclass(frozen=True)
class SlotStatus:
    team: str
    listed: int
    maximum: int

    @property
    def free(self) -> int:
        return max(0, self.maximum - self.listed)


def count_listed(players: list[dict], market: list[dict]) -> int:
    """How many of my players are on the transfer list."""
    mine = {p["id"] for p in players}
    return sum(1 for item in market if item["player"]["id"] in mine)


def read_slots(client) -> list[SlotStatus]:
    from osmbot.game.trainings import _teams

    result = []
    for _, team, base in _teams(client):
        _, settings = client.get(f"leagues/{team['leagueId']}/gamesettings")
        maximum = next((g["value"] for g in settings if g["name"] == MAX_SLOTS_SETTING), None)
        if maximum is None:
            raise RuntimeError(f"Nao encontrei '{MAX_SLOTS_SETTING}' nas definicoes do jogo.")
        _, players = client.get(f"{base}/players")
        _, market = client.get(f"{base}/transferplayers/0")
        result.append(SlotStatus(team["name"], count_listed(players, market), maximum))
    return result


def newly_free(statuses: list[SlotStatus], previous: dict[str, int]) -> list[SlotStatus]:
    """Clubs whose number of free slots went up since the last check (``previous`` is updated)."""
    alerts = [s for s in statuses if s.free > previous.get(s.team, 0)]
    previous.update({s.team: s.free for s in statuses})
    return alerts


def describe(status: SlotStatus) -> str:
    return f"{status.team}: {status.free} slot(s) de venda livre(s) ({status.listed}/{status.maximum} ocupados)"


def run_slots() -> None:
    from osmbot.game.client import NeedsBrowserLogin, OsmClient

    try:
        for status in read_slots(OsmClient()):
            print(describe(status))
    except NeedsBrowserLogin as error:
        raise SystemExit(str(error))
