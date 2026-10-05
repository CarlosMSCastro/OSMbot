"""The console menu that opens when you run ``osmbot`` with no command (D-015, D-016)."""
from __future__ import annotations

import os
import sys
from typing import Callable

TITLE = "OSMbot"
RULE = "─" * 56


def _default_actions() -> dict[str, tuple[str, Callable[[], None]]]:
    """Menu key -> (label, action). Imported lazily so the menu itself stays light and testable."""
    from osmbot.game.browser import open_login_session
    from osmbot.game.loop import run_active
    from osmbot.game.slots import run_slots
    from osmbot.game.status import run_status
    from osmbot.game.trainings import run_trainings

    def status() -> None:
        run_status()
        print()
        run_trainings()
        print()
        run_slots()

    return {
        "1": ("Iniciar o bot  (treinos, anúncios, avisos)", lambda: run_active(False)),
        "2": ("Iniciar o bot, sem anúncios", lambda: run_active(False, ads=None)),
        "3": ("Estado: clubes, treinos e slots de venda", status),
        "4": ("Ensaio: ver o que faria, sem escrever nada", lambda: run_active(True)),
        "5": ("Login: fazer ou refazer (abre o Firefox)", open_login_session),
    }


def session_line() -> str:
    from osmbot.game.browser import STATE_FILE

    if STATE_FILE.exists():
        return "Sessão: guardada neste PC"
    return "Sessão: NENHUMA neste PC. Escolhe 5 para fazer o login primeiro."


def run_menu(actions=None, ask: Callable[[str], str] = input, show: Callable[[str], None] = print,
             clear: bool | None = None) -> None:
    actions = actions or _default_actions()
    clear = sys.stdout.isatty() if clear is None else clear
    while True:
        if clear:
            os.system("cls" if os.name == "nt" else "clear")
        show(f"\n {TITLE}\n {RULE}")
        for key, (label, _) in actions.items():
            show(f"  {key}  {label}")
        show("  0  Sair")
        show(f" {RULE}\n {session_line()}")
        try:
            choice = ask("\n Escolha: ").strip()
        except (EOFError, KeyboardInterrupt):
            show("")
            return
        if choice in ("0", "q", "Q", "sair"):
            return
        if choice not in actions:
            show(" Opção inválida.")
            continue
        try:
            actions[choice][1]()
        except SystemExit as stop:  # the commands report problems by exiting; keep the menu open instead
            if stop.code not in (None, 0):
                show(f"\n {stop.code}")
        except KeyboardInterrupt:
            show("\n Interrompido.")
        try:
            ask("\n Enter para voltar ao menu...")
        except (EOFError, KeyboardInterrupt):
            return
