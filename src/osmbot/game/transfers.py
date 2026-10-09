"""Save every transfer of the owner's leagues, once a day, for the price study (D-029). Read-only (GET).

``GET leagues/{L}/transfers`` gives only the last 100 (DISCOVERY.md section 3), so the bot keeps adding them to
``<repo>/logs/<machine>/transferencias/<league>.json``: one folder per PC like the log (D-022), each transfer once.
Nothing is decided from this yet; the owner studies it later.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from osmbot.logs import machine, repo_folder
from osmbot.transfers.history import due, merge


def league_file(repo: Path, league_id: int) -> Path:
    return repo / "logs" / machine() / "transferencias" / f"{league_id}.json"


def _read(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def save_transfers(client_factory=None, log=print, today: str | None = None) -> int:
    """Read and save the leagues not read today. Returns how many new transfers were saved."""
    repo = repo_folder()
    if repo is None:  # no repo found: nowhere shared to keep them (the bot's log says the same)
        return 0
    today = today or f"{datetime.now():%Y-%m-%d}"
    if client_factory is None:
        from osmbot.game.client import OsmClient as client_factory
    client = client_factory()
    _, account = client.get("user/accounts")
    leagues = {team["leagueId"] for slot in (account.get("teamSlots") or {}).values()
               if (team := (slot or {}).get("team"))}
    total = 0
    for league_id in sorted(leagues):
        path = league_file(repo, league_id)
        saved = _read(path)
        if not due(saved, today):
            continue
        status, rows = client.get(f"leagues/{league_id}/transfers")
        if status != 200 or not isinstance(rows, list):
            log(f"Transferências: liga {league_id} não respondeu ({status}); volto a tentar")
            continue
        _, league = client.get(f"leagues/{league_id}")
        name = league.get("name", "") if isinstance(league, dict) else ""
        data, new = merge(saved, {"id": league_id, "name": name}, rows, today)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        log(f"Transferências: {data['nome'] or league_id} +{new} (guardadas {len(data['transferencias'])})")
        total += new
    return total
