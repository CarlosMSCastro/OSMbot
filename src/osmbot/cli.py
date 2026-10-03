"""Thin CLI over the osmbot library. See CLAUDE.md rule 5 and D-013/D-004."""
from __future__ import annotations

import argparse

from osmbot.game.client import run_probe
from osmbot.game.status import run_status
from osmbot.game.browser import inspect_network, inspect_session, open_dashboard, open_login_session, token_info


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
    probe = subparsers.add_parser(
        "probe",
        help="Read-only: GET one API path and print the status and the SHAPE of the answer (no values).",
    )
    probe.add_argument("path", help="e.g. user/bosscoinwallet (relative to /api/v1)")
    args = parser.parse_args(argv)

    if args.command == "login":
        open_login_session()
    elif args.command == "dashboard":
        open_dashboard()
    elif args.command == "inspect-session":
        inspect_session()
    elif args.command == "token-info":
        token_info()
    elif args.command == "inspect-network":
        inspect_network()
    elif args.command == "status":
        run_status()
    elif args.command == "probe":
        run_probe(args.path)


if __name__ == "__main__":
    main()
