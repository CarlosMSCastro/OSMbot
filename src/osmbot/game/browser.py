"""Persistent, real browser session for OSM.

Uses a Playwright persistent context stored under the owner's home directory
(never inside the repo, never committed) so a manual login is only needed once
per expiry. No credentials are ever read, typed, or stored by this code - the
owner logs in by hand in the window this opens.
"""
from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

PROFILE_DIR = Path.home() / ".osmbot" / "firefox-profile"
LOGIN_URL = "https://www.onlinesoccermanager.com/"
HOME_URL = "https://en.onlinesoccermanager.com/"


def open_login_session(profile_dir: Path = PROFILE_DIR, url: str = LOGIN_URL) -> None:
    """Open a real, visible browser window for the owner to log into OSM.

    The window stays open until the owner presses Enter in the console. The
    session (cookies/local storage) is saved in ``profile_dir`` and reused by
    future runs automatically - no cookie copying, no stored password.
    """
    profile_dir.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        # Firefox, not Chromium: Facebook's login popup blocks Playwright's
        # "Chrome for Testing" build outright, even for a real manual login.
        context = playwright.firefox.launch_persistent_context(
            str(profile_dir), headless=False
        )
        try:
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(url)
            input(
                "Faz login normalmente na janela que abriu. "
                "Quando terminares, volta aqui e prime Enter... "
            )
        finally:
            context.close()


def open_dashboard(profile_dir: Path = PROFILE_DIR, url: str = HOME_URL) -> None:
    """Open the saved session on the club/team area, for the owner to look at.

    Discovery step: we don't yet know the page's structure (rule 7, CLAUDE.md -
    never guess it), so this just shows it to the owner instead of scraping.
    Once the owner describes what's on screen, real extraction code replaces
    this.
    """
    with sync_playwright() as playwright:
        context = playwright.firefox.launch_persistent_context(
            str(profile_dir), headless=False
        )
        try:
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(url)
            input("Vê o que aparece. Quando quiseres fechar, prime Enter aqui... ")
        finally:
            context.close()
