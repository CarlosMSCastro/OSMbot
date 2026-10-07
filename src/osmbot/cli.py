"""Thin CLI over the osmbot library. See CLAUDE.md rule 5 and D-013/D-004."""
from __future__ import annotations

import argparse
import sys

from osmbot.game.client import run_probe
from osmbot.game.loop import run_active
from osmbot.game.slots import run_slots
from osmbot.game.sponsors import run_sponsors
from osmbot.game.stadium import run_stadium
from osmbot.game.status import run_status
from osmbot.game.trainings import run_claim, run_train, run_trainings
from osmbot.game.browser import inspect_network, inspect_writes, inspect_session, open_dashboard, open_login_session, token_info


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="osmbot")
    subparsers = parser.add_subparsers(dest="command")  # no command: the menu
    subparsers.add_parser(
        "login",
        help="Open a browser window to log into OSM; the session is saved for reuse.",
    )
    subparsers.add_parser(
        "dashboard",
        help="Open the saved session on the club area (discovery step, no data extraction yet).",
    )
    subparsers.add_parser(
        "inspect-session",
        help="Discovery: after a manual login, list where the session is stored (names only).",
    )
    subparsers.add_parser(
        "token-info",
        help="Print token expiry from the saved session (local only, no values).",
    )
    subparsers.add_parser(
        "inspect-network",
        help="Discovery: list the requests the site makes with the saved session (no headers/bodies).",
    )
    subparsers.add_parser("status", help="Read-only: list your active clubs (no browser needed).")
    for name, text in (
        ("recolher", "Collect finished trainings. Writes to the game; add --simular to only show what it would do."),
        ("estadio", "Start the next stadium upgrade where a club is free. Writes to the game; add --simular to only show what it would do."),
        ("patrocinadores", "Fill free sponsor slots with the best-paying offers. Writes to the game; add --simular to only show what it would do."),
        ("treinar", "Start trainings in free slots by the owner's policy. Writes to the game; add --simular to only show the plan."),
    ):
        writer = subparsers.add_parser(name, help=text)
        writer.add_argument("--simular", action="store_true", help="dry run: show what would be done, write nothing")
        writer.add_argument("--confirmar", action="store_true", help=argparse.SUPPRESS)  # old flag, now the default
        writer.add_argument("--max", type=int, default=None, help="stop after this many actions (for first tests)")
    active = subparsers.add_parser(
        "ativo",
        help="Active mode: keeps collecting and training on its own, waking when each training ends. Ctrl+C stops.",
    )
    active.add_argument("--sem-anuncios", action="store_true", help="do not watch shop videos")
    active.add_argument("--sem-quadro", action="store_true", help="plain log lines instead of the board")
    active.add_argument("--simular", action="store_true", help="one dry pass: show the plan and when it would wake up")
    subparsers.add_parser("slots", help="Read-only: free transfer-list slots per club.")
    subparsers.add_parser("treinos", help="Read-only: training sessions (ready / time left) and next match.")
    subparsers.add_parser(
        "inspect-writes",
        help="Discovery: you act in the window, it lists the write requests the site makes (no values).",
    )
    probe = subparsers.add_parser(
        "probe",
        help="Read-only: GET one API path and print the status and the SHAPE of the answer (no values).",
    )
    probe.add_argument("path", help="e.g. user/bosscoinwallet (relative to /api/v1)")
    probe.add_argument("--slot", default="0", help="team slot used to fill {L} and {T} (default 0)")
    args = parser.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):  # Windows consoles default to a legacy codepage
        stream.reconfigure(encoding="utf-8", errors="replace")

    if args.command is None:
        from osmbot.menu import run_menu

        run_menu()
    elif args.command == "login":
        open_login_session()
    elif args.command == "dashboard":
        open_dashboard()
    elif args.command == "inspect-session":
        inspect_session()
    elif args.command == "token-info":
        token_info()
    elif args.command == "inspect-network":
        inspect_network()
    elif args.command == "inspect-writes":
        inspect_writes()
    elif args.command == "recolher":
        run_claim(not args.simular, args.max)
    elif args.command == "treinar":
        run_train(not args.simular, args.max)
    elif args.command == "estadio":
        failed, _ = run_stadium(not args.simular)
        if failed:
            raise SystemExit(1)
    elif args.command == "patrocinadores":
        failed, _ = run_sponsors(not args.simular)
        if failed:
            raise SystemExit(1)
    elif args.command == "ativo":
        run_active(
            args.simular,
            **({"ads": None} if args.sem_anuncios else {}),
            **({"use_screen": False} if args.sem_quadro else {}),
        )
    elif args.command == "slots":
        run_slots()
    elif args.command == "treinos":
        run_trainings()
    elif args.command == "status":
        run_status()
    elif args.command == "probe":
        run_probe(args.path, args.slot)


if __name__ == "__main__":
    main()
