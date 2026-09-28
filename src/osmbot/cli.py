"""Thin CLI over the osmbot library. See CLAUDE.md rule 5 and D-013/D-004."""
from __future__ import annotations

import argparse

from osmbot.game.browser import open_dashboard, open_login_session


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="osmbot")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser(
        "login",
        help="Open a browser window to log into OSM; the session is saved for reuse.",
    )
    subparsers.add_parser(
        "dashboard",
        help="Open the saved session on the club area (discovery step, no data extraction yet).",
    )
    args = parser.parse_args(argv)

    if args.command == "login":
        open_login_session()
    elif args.command == "dashboard":
        open_dashboard()


if __name__ == "__main__":
    main()
