"""Domain models. Pure data, no I/O.

Field names in ``Player.from_api`` follow what third-party projects report about
the game's API (see docs/PRIOR_ART.md). They are unverified until we observe the
real API ourselves.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Mapping


class Position(IntEnum):
    """Coarse position codes reported by the API: 1=ATT 2=MID 3=DEF 4=GK."""

    ATT = 1
    MID = 2
    DEF = 3
    GK = 4


@dataclass(frozen=True)
class Player:
    id: int
    name: str
    position: Position
    age: int
    stat_att: int
    stat_ovr: int
    stat_def: int
    injured: bool = False

    @property
    def rating(self) -> int:
        """The player's main stat for his position (hypothesis, see THEORY.md).

        Forwards use attack, midfielders overall, defenders and goalkeepers defence.
        """
        if self.position is Position.ATT:
            return self.stat_att
        if self.position is Position.MID:
            return self.stat_ovr
        return self.stat_def

    @classmethod
    def from_api(cls, data: Mapping[str, Any]) -> "Player":
        return cls(
            id=int(data["id"]),
            name=str(data.get("name") or data.get("fullName") or data["id"]),
            position=Position(int(data["position"])),
            age=int(data["age"]),
            stat_att=int(data.get("statAtt") or 0),
            stat_ovr=int(data.get("statOvr") or 0),
            stat_def=int(data.get("statDef") or 0),
            injured=int(data.get("injuryId") or 0) > 0,
        )
