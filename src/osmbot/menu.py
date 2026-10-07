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


def build_screen(actions, session: str, width: int, colour: bool = False, selected: int | None = None) -> list[str]:
    """The menu as lines of text, centred in ``width`` columns (colour codes never count as width).
    With ``selected`` (the arrow-key mode) that option is highlighted and a hint is shown."""
    def paint(text: str, code: str) -> str:
        return f"{code}{text}{RESET}" if colour else text

    def centred(text: str, code: str = "") -> str:
        return " " * max(0, (width - len(text)) // 2) + (paint(text, code) if code else text)

    options = [f"{key}  {label}" for key, (label, _) in actions.items()] + ["0  Sair"]
    marker = selected is not None
    margin = " " * max(0, (width - max(len(option) for option in options) - (2 if marker else 0)) // 2)
    session_code = GREEN if session.endswith("ok") else YELLOW
    lines = [""]
    lines += [centred(row, BOLD + GREEN) for row in ART]
    lines += [centred(SUBTITLE, GREY), ""]
    lines += [centred(row) for row in INTRO]
    lines += ["", centred("─" * RULE_WIDTH, GREY), ""]
    for index, option in enumerate(options):
        if not marker:
            lines.append(margin + option)
        elif index == selected:
            lines.append(margin + paint("» " + option, BOLD + GREEN))
        else:
            lines.append(margin + "  " + option)
    lines += ["", centred("─" * RULE_WIDTH, GREY), centred(session, session_code)]
    if marker:
        lines += ["", centred("↑ ↓ para escolher  ·  Enter para confirmar", GREY)]
    return lines


def read_key() -> str:
    """One key press: "up", "down", "enter", "esc" or the character typed (Windows, macOS and Linux)."""
    if os.name == "nt":
        import msvcrt

        key = msvcrt.getwch()
        if key in ("\x00", "\xe0"):  # arrows and function keys come as two codes
            return {"H": "up", "P": "down"}.get(msvcrt.getwch(), "")
        if key == "\x03":
            raise KeyboardInterrupt
        return {"\r": "enter", "\x1b": "esc"}.get(key, key)
    import select
    import termios
    import tty

    fd = sys.stdin.fileno()
    saved = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        key = sys.stdin.read(1)
        if key == "\x1b":  # an arrow is ESC [ A / ESC [ B; a lone Esc has nothing after it
            if select.select([sys.stdin], [], [], 0.05)[0]:
                return {"[A": "up", "[B": "down"}.get(sys.stdin.read(2), "")
            return "esc"
        if key == "\x03":
            raise KeyboardInterrupt
        return {"\r": "enter", "\n": "enter"}.get(key, key)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, saved)


def _pick(actions, width: int, key: Callable[[], str]) -> str | None:
    """Arrow-key selection on a screen that redraws in place. Returns the chosen key ("0" = leave), None = leave."""
    labels = [*actions, "0"]
    index = 0
    os.system("cls" if os.name == "nt" else "clear")
    sys.stdout.write("\x1b[?25l")
    try:
        while True:
            frame = build_screen(actions, session_line(), width, colour=True, selected=index)
            sys.stdout.write("\x1b[H" + "\x1b[K\n".join(frame) + "\x1b[K\x1b[J")
            sys.stdout.flush()
            pressed = key()
            if pressed == "up":
                index = (index - 1) % len(labels)
            elif pressed == "down":
                index = (index + 1) % len(labels)
            elif pressed == "enter":
                return labels[index]
            elif pressed in labels:  # typing the number still works
                return pressed
            elif pressed in ("esc", "q", "Q"):
                return None
    finally:
        sys.stdout.write("\x1b[?25h")
        sys.stdout.flush()


def run_menu(actions=None, ask: Callable[[str], str] = input, show: Callable[[str], None] = print,
             clear: bool | None = None, width: int | None = None, key: Callable[[], str] | None = None) -> None:
    """``key`` = how to read a key press: given, the menu is chosen with the arrow keys; by default that is
    so on a real terminal, otherwise (tests, pipes) the option number is typed and Enter pressed."""
    actions = actions or _default_actions()
    clear = sys.stdout.isatty() if clear is None else clear
    if key is None and clear and sys.stdin.isatty():
        key = read_key
        if os.name == "nt":
            os.system("")  # switches on ANSI escape codes in the Windows console
    width = width or shutil.get_terminal_size((80, 24)).columns
    while True:
        if key:
            try:
                choice = _pick(actions, width, key)
            except KeyboardInterrupt:
                return
            if choice in (None, "0"):
                return
            os.system("cls" if os.name == "nt" else "clear")
        else:
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
