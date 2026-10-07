"""The bot's log, also kept inside the repo (D-022) so the owner can read it from any machine.

``~/.osmbot/bot.log`` stays as it was. Each line also goes to ``<repo>/logs/<machine>/AAAA-MM-DD.log``
(one folder per PC, one file per day: two PCs never write the same file, so git never conflicts).
The repo folder is found on its own when the bot runs from the source; the installed bot is told once
(menu "Pasta dos logs", or ``osmbot pasta-logs``) and remembers it in ``~/.osmbot/config.json``.
The bot never runs git: committing and pushing the logs is the owner's (rule 9).
Secrets never go in (rule 6): anything that looks like a token or an e-mail is blanked out first.
"""
from __future__ import annotations

import json
import os
import platform
import re
from datetime import datetime
from pathlib import Path

CONFIG_FILE = Path.home() / ".osmbot" / "config.json"
OLD_LOG = Path.home() / ".osmbot" / "bot.log"
SOURCE_ROOT = Path(__file__).resolve().parents[2]  # the repo, when running from the source
_SECRETS = (
    (re.compile(r"eyJ[\w-]{8,}\.[\w-]{8,}\.[\w-]*"), "[token]"),  # JWT (access/refresh tokens)
    (re.compile(r"(?i)(bearer|token|secret|password|cookie)([\"':= ]+)\S+"), r"\1\2[apagado]"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "[e-mail]"),
)


def clean(text: str) -> str:
    """The line without anything that looks like a secret."""
    for pattern, replacement in _SECRETS:
        text = pattern.sub(replacement, text)
    return text


def machine() -> str:
    """This PC's folder name (its network name), safe as a folder on Windows and macOS."""
    name = platform.node().split(".")[0] or platform.system() or "pc"
    return re.sub(r"[^\w-]", "_", name)


def is_repo(folder: Path) -> bool:
    return (folder / "pyproject.toml").is_file() and (folder / "src" / "osmbot").is_dir()


def _config() -> dict:
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def repo_folder() -> Path | None:
    """The repo the logs go to: ``OSMBOT_REPO``, else the folder chosen once, else the source checkout."""
    for candidate in (os.environ.get("OSMBOT_REPO"), _config().get("repo")):
        if candidate and is_repo(Path(candidate)):
            return Path(candidate)
    return SOURCE_ROOT if is_repo(SOURCE_ROOT) else None


def day_file(repo: Path, when: datetime) -> Path:
    return repo / "logs" / machine() / f"{when:%Y-%m-%d}.log"


def write(when: datetime, message: str, repo: Path | None = None) -> None:
    """Add one line to today's file in the repo. Never fails: the log must never stop the bot."""
    try:
        repo = repo or repo_folder()
        if repo is None:
            return
        target = day_file(repo, when)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as handle:
            handle.write(f"{when:%Y-%m-%d %H:%M:%S}  {clean(message)}\n")
    except Exception:
        pass


def import_history(repo: Path, old_log: Path = OLD_LOG) -> int:
    """Copy the lines of ``~/.osmbot/bot.log`` into the repo's day files, for the days that have no file
    yet (so running it twice adds nothing). Returns the number of days copied."""
    if not old_log.is_file():
        return 0
    days: dict[str, list[str]] = {}
    for line in old_log.read_text(encoding="utf-8", errors="replace").splitlines():
        if re.match(r"\d{4}-\d{2}-\d{2} ", line):
            days.setdefault(line[:10], []).append(clean(line))
    copied = 0
    for day, lines in days.items():
        target = repo / "logs" / machine() / f"{day}.log"
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("\n".join(lines) + "\n", encoding="utf-8")
        copied += 1
    return copied


def choose_repo(path: str) -> Path:
    """Remember the repo folder for the logs (and copy the old log in). SystemExit with a message if wrong."""
    folder = Path(path.strip().strip('"')).expanduser()
    if not is_repo(folder):
        raise SystemExit(f"{folder} não é a pasta do repo OSMbot (falta pyproject.toml / src/osmbot)")
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps({**_config(), "repo": str(folder.resolve())}), encoding="utf-8")
    return folder.resolve()


def run_logs_folder(path: str | None = None, ask=input, show=print) -> None:
    """Command / menu option: show where the logs go, or set it."""
    current = repo_folder()
    show(f"Logs no repo: {current / 'logs' / machine() if current else 'não definido (só ~/.osmbot/bot.log)'}")
    if path is None:
        try:
            path = ask("Pasta do repo OSMbot neste PC (Enter mantém): ").strip()
        except (EOFError, KeyboardInterrupt):
            return
        if not path:
            return
    folder = choose_repo(path)
    days = import_history(folder)
    show(f"Logs passam a ir para {folder / 'logs' / machine()}" + (f" ({days} dia(s) do registo antigo copiados)" if days else ""))
    show("Commit e push são contigo (o bot não mexe no git).")
