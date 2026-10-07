"""The console menu that opens when you run ``osmbot`` with no command (D-015, D-016).

Only what the owner uses every day is in the menu: start the bot, log in, leave. The rest
(status, simulation, a run without videos...) stays available as commands: ``osmbot --help``.
"""
from __future__ import annotations

import os
import shutil
import sys
from typing import Callable

RULE_WIDTH = 46
GREEN, YELLOW, GREY, BOLD, RESET = "\x1b[32m", "\x1b[33m", "\x1b[90m", "\x1b[1m", "\x1b[0m"

# "OSM" in 5-row block letters, then the word "bot" spaced under it.
ART = [
    " ███    ████  █   █",
    "█   █  █      ██ ██",
    "█   █   ███   █ █ █",
    "█   █      █  █   █",
    " ███   ████   █   █",
]
SUBTITLE = "b o t"
INTRO = [
    "Trabalha por ti no Online Soccer Manager:",
    "recolhe e põe a treinar, vê os vídeos, sobe o estádio,",
    "assina patrocinadores e avisa das vagas na lista de transferências.",
]


def _default_actions() -> dict[str, tuple[str, Callable[[], None]]]:
    """Menu key -> (label, action). Imported lazily so the menu itself stays light and testable."""
    from osmbot.game.browser import open_login_session
    from osmbot.game.loop import run_active

    return {
        "1": ("Iniciar", lambda: run_active(False)),
        "2": ("Login", open_login_session),
    }


def session_line() -> str:
    from osmbot.game.browser import STATE_FILE

    if STATE_FILE.exists():
        return "Sessão: ok"
    return "Sessão: em falta. Faz o login (2)"


def build_screen(actions, session: str, width: int, colour: bool = False) -> list[str]:
    """The menu as lines of text, centred in ``width`` columns (colour codes never count as width)."""
    def paint(text: str, code: str) -> str:
        return f"{code}{text}{RESET}" if colour else text

    def centred(text: str, code: str = "") -> str:
        return " " * max(0, (width - len(text)) // 2) + (paint(text, code) if code else text)

    options = [f"{key}  {label}" for key, (label, _) in actions.items()] + ["0  Sair"]
    margin = " " * max(0, (width - max(len(option) for option in options)) // 2)
    session_code = GREEN if session.endswith("ok") else YELLOW
    lines = [""]
    lines += [centred(row, BOLD + GREEN) for row in ART]
    lines += [centred(SUBTITLE, GREY), ""]
    lines += [centred(row) for row in INTRO]
    lines += ["", centred("─" * RULE_WIDTH, GREY), ""]
    lines += [margin + option for option in options]
    lines += ["", centred("─" * RULE_WIDTH, GREY), centred(session, session_code)]
    return lines


def run_menu(actions=None, ask: Callable[[str], str] = input, show: Callable[[str], None] = print,
             clear: bool | None = None, width: int | None = None) -> None:
    actions = actions or _default_actions()
    clear = sys.stdout.isatty() if clear is None else clear
    width = width or shutil.get_terminal_size((80, 24)).columns
    while True:
        if clear:
            os.system("cls" if os.name == "nt" else "clear")
        for line in build_screen(actions, session_line(), width, colour=clear):
            show(line)
        try:
            choice = ask(" " * max(0, width // 2 - 8) + "Opção: ").strip()
        except (EOFError, KeyboardInterrupt):
            show("")
            return
        if choice in ("0", "q", "Q", "sair"):
            return
        if choice not in actions:
            show(" Opção inválida")
            continue
        try:
            actions[choice][1]()
        except SystemExit as stop:  # the commands report problems by exiting; keep the menu open instead
            if stop.code not in (None, 0):
                show(f"\n {stop.code}")
        except KeyboardInterrupt:
            show("\n Interrompido")
        try:
            ask("\n Enter para continuar")
        except (EOFError, KeyboardInterrupt):
            return
