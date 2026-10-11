"""Records of the game's transfer engine, one file per league (D-034). Read-only (GET).

Every read of the board already brings each league's transfer list (every 3 minutes). Here it is compared with
the read before (kept in ``~/.osmbot/mercado.json``, so a restart doesn't lose it); when the engine went round or
a manager's player left the list, one line goes to ``<repo>/logs/<machine>/transferencias/motor/<league>.jsonl``
(one JSON record per line, for the study) and a short line to the bot's log.
"""
from __future__ import annotations

import json
import threading
import time
from datetime import datetime
from pathlib import Path

from osmbot.logs import machine, repo_folder
from osmbot.transfers.engine import classify, describe, observe

STATE_FILE = Path.home() / ".osmbot" / "mercado.json"
SAME_READ = 60.0  # s: two clubs in the same league bring the same list; the second read within this is skipped
_LOCK = threading.Lock()


def _load() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def records_file(repo: Path, league_id: int) -> Path:
    return repo / "logs" / machine() / "transferencias" / "motor" / f"{league_id}.jsonl"


def _clock(ts: float | None) -> str:
    return f"{datetime.fromtimestamp(ts):%H:%M}" if ts else "?"


def watch(client, league_id: int, league_name: str, market: list[dict], owner: int | None, log=None,
          now: float | None = None) -> dict | None:
    """Compare this read of the league's list with the last one; save and log what changed. Returns the record."""
    now = time.time() if now is None else now
    with _LOCK:
        data = _load()
        state = data.get(str(league_id))
        if state and now - state.get("t", 0) < SAME_READ:
            return None
        data[str(league_id)], record = observe(state, market, now, owner)
        try:
            STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            STATE_FILE.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        except OSError:
            pass
    if record is None:
        return None
    transfers = []
    if record["sairam"]:
        status, body = client.get(f"leagues/{league_id}/transfers")
        transfers = body if status == 200 and isinstance(body, list) else []
    record = {"liga": league_id, **classify(record, transfers)}
    repo = repo_folder()
    if repo is not None:
        path = records_file(repo, league_id)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as out:
                out.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
        except OSError:
            pass
    if log is None:
        from osmbot.game.loop import _log as log  # the bot's log: ~/.osmbot/bot.log and the repo (D-022)
    log(describe(record, league_name or str(league_id), _clock))
    return record
