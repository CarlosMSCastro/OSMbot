"""Shop videos (boss coins) watched in a real, invisible Firefox (D-012, DISCOVERY.md 2026-10-05).

The page itself plays the ad and tells the game it was watched; this only opens the shop and
clicks "Watch ad", exactly like the owner does by hand. It never calls ``videos/watched``.
Limits come from the game (``user/caps/actions/BusinessClub/0``) and are never exceeded; some
windows are skipped and pauses are random, so the pattern is not that of a machine.
"""
from __future__ import annotations

import random
import re
import time
from pathlib import Path
from typing import Callable

SHOP_ACTION = "BusinessClub"
TRAINING_ACTION = "TrainingTimer"
POSITION_NAMES = {1: "ATA", 2: "MED", 3: "DEF", 4: "GR"}
COACH_TITLES = {1: "Attacking coach", 2: "Midfielder coach", 3: "Defending coach", 4: "Goalkeeping coach"}
VIDEO_SAVES = 2 * 3600  # a training video takes 2h off one session
MAX_TRAINING_VIDEOS = 4  # the game's own limit per 3 hours
ENGAGE_CHANCE = 0.85  # share of the windows (cap open) in which it watches videos at all
MAX_PER_BURST = 9  # the shop's own limit per window
PAUSE = (20.0, 75.0)  # seconds between two videos
WAIT_FOR_REWARD = 90.0  # seconds to wait for the boss coins to arrive
PAGE_TIMEOUT = 60_000  # ms (slow office PCs / networks)


def save_failure(page, tag: str) -> None:
    """Keep a screenshot of what the browser was showing when a video failed (~/.osmbot/failures/), to debug later."""
    try:
        folder = Path.home() / ".osmbot" / "failures"
        folder.mkdir(parents=True, exist_ok=True)
        for old in sorted(folder.glob("*.png"))[:-10]:  # keep the last 10 only
            old.unlink()
        page.screenshot(path=str(folder / f"{time.strftime('%Y%m%d-%H%M%S')}-{tag}.png"))
    except Exception:
        pass


class AdsError(Exception):
    """The ad flow did not work (button missing, coins did not arrive...). The loop turns ads off after two."""


def is_claimable(client, action_id: str = SHOP_ACTION) -> bool:
    _, cap = client.get(f"user/caps/actions/{action_id}/0")
    return bool(cap.get("isClaimable")) and not cap.get("isCapReached")


def run_shop_ads(claimable: Callable[[], bool], watch_one: Callable[[], None], *, dry_run: bool = False,
                 log: Callable[[str], None] = print, rng=random, sleep=time.sleep) -> int:
    """Watch shop videos while the game allows it. Returns how many were watched."""
    if not claimable():
        return 0
    if rng.random() > ENGAGE_CHANCE:
        log("Loja: janela saltada")
        return 0
    if dry_run:
        log("Simulação: veria vídeos da loja")
        return 0
    watched = 0
    while watched < MAX_PER_BURST:
        watch_one()
        watched += 1
        log(f"Loja: vídeo {watched}")
        if not claimable():
            break
        sleep(rng.uniform(*PAUSE))
    return watched


def _wallet_amount(client) -> int:
    _, wallet = client.get("user/bosscoinwallet")
    return wallet["amount"]


def watch_shop_video(client, headless: bool = True) -> None:
    """Open the shop in Firefox, click "Watch ad" and wait for the boss coin to arrive."""
    from playwright.sync_api import sync_playwright

    from osmbot.game.browser import STATE_FILE
    from osmbot.game.client import save_private

    before = _wallet_amount(client)
    state = None
    with sync_playwright() as playwright:
        browser = playwright.firefox.launch(headless=headless)
        try:
            context = browser.new_context(storage_state=str(STATE_FILE), viewport={"width": 1280, "height": 900})
            page = context.new_page()
            page.goto("https://en.onlinesoccermanager.com/")
            try:
                page.locator("a:visible", has_text="Shop").first.click(timeout=PAGE_TIMEOUT)
                page.get_by_text("Watch ad", exact=False).first.click(timeout=PAGE_TIMEOUT)
            except Exception as error:
                save_failure(page, "loja")
                raise AdsError(f"botão da loja não encontrado ({type(error).__name__})") from error
            deadline = time.time() + WAIT_FOR_REWARD
            while time.time() < deadline:
                page.wait_for_timeout(3000)
                if _wallet_amount(client) > before:
                    break
            else:
                save_failure(page, "loja")
                raise AdsError("os boss coins não subiram")
            cookies = context.cookies()
            if any(c["name"] == "access_token" for c in cookies):
                state = {"cookies": cookies, "origins": []}
        finally:
            browser.close()
    if state:  # the site may have renewed the tokens: keep the saved session in step with it
        save_private(STATE_FILE, state)


def pick_session(candidates: list[tuple[str, dict]], now: float) -> tuple[str, dict] | None:
    """The session that should get the next -2h video: the one with the MOST time left, so all of
    them end up finishing around the same time (owner's choice, 2026-10-05). Sessions with less
    than 2h left are skipped (the video would be partly wasted). ``candidates`` = (club name, session)."""
    usable = [(club, s) for club, s in candidates
              if not s["countdownTimer"]["isClaimed"] and s["countdownTimer"]["finishedTimestamp"] - now >= VIDEO_SAVES]
    if not usable:
        return None
    return max(usable, key=lambda c: c[1]["countdownTimer"]["finishedTimestamp"])


def run_training_ads(claimable: Callable[[], bool], load_sessions: Callable[[], list[tuple[str, dict]]],
                     watch_one: Callable[[str, dict], None], *, dry_run: bool = False,
                     log: Callable[[str], None] = print, rng=random, sleep=time.sleep, clock=time.time) -> int:
    """Use training videos (-2h) while the game allows it. Returns how many were watched."""
    if not claimable():
        return 0
    if rng.random() > ENGAGE_CHANCE:
        log("Treino: janela saltada")
        return 0
    watched = 0
    while watched < MAX_TRAINING_VIDEOS:
        choice = pick_session(load_sessions(), clock())
        if choice is None:
            log("Treino: sem sessões com 2h ou mais")
            break
        club, session = choice
        if dry_run:
            log(f"Simulação: veria 1 vídeo de treino em {club} ({POSITION_NAMES.get(session['trainer'], '?')})")
            break
        watch_one(club, session)
        watched += 1
        log(f"Treino: vídeo {watched} ({club}, {POSITION_NAMES.get(session['trainer'], '?')})")
        if not claimable():
            break
        sleep(rng.uniform(*PAUSE))
    return watched


def _open_club(page, club: str) -> None:
    """Career page -> the club's card (opens the club's home screen)."""
    page.goto("https://en.onlinesoccermanager.com/")
    page.locator(".clubslot-main-title", has_text=club).first.click(force=True, timeout=PAGE_TIMEOUT)
    page.wait_for_timeout(6000)


def _open_training_page(page, club: str) -> None:
    """The club's card, then its "TRAINING" tile (the top "Training Ground" menu does not react to clicks)."""
    _open_club(page, club)
    page.locator("text=/^training$/i").filter(visible=True).first.click(timeout=PAGE_TIMEOUT)
    page.wait_for_timeout(5000)


def _coach_button(page, trainer: int):
    """The "- 2h" button in the column of the given trainer (never "Train instantly", which costs boss coins)."""
    title = page.get_by_text(COACH_TITLES[trainer], exact=True).filter(visible=True).first
    title_box = title.bounding_box(timeout=PAGE_TIMEOUT)
    buttons = page.get_by_text(re.compile(r"^\s*-\s*2h\s*$")).filter(visible=True).all()
    if not buttons:
        raise AdsError("botões '- 2h' não encontrados")
    centre = title_box["x"] + title_box["width"] / 2

    def distance(button) -> float:
        box = button.bounding_box()
        return abs(box["x"] + box["width"] / 2 - centre)

    return min(buttons, key=distance)


def watch_training_video(client, club: str, session: dict, base: str, headless: bool = True,
                         dry_run: bool = False) -> None:
    """Open the club's training page and click "-2h" in the session's column; wait for the timer to drop.
    With ``dry_run`` it only navigates and checks that the button is found (clicks nothing)."""
    from playwright.sync_api import sync_playwright

    from osmbot.game.browser import STATE_FILE
    from osmbot.game.client import save_private

    def finishes() -> float:
        _, sessions = client.get(f"{base}/trainingsessions/ongoing")
        return next(s["countdownTimer"]["finishedTimestamp"] for s in sessions if s["id"] == session["id"])

    before = finishes()
    state = None
    with sync_playwright() as playwright:
        browser = playwright.firefox.launch(headless=headless)
        try:
            context = browser.new_context(storage_state=str(STATE_FILE), viewport={"width": 1280, "height": 900})
            page = context.new_page()
            try:
                _open_training_page(page, club)
                button = _coach_button(page, session["trainer"])
                if dry_run:
                    return
                button.click(timeout=PAGE_TIMEOUT)
            except Exception as error:
                save_failure(page, "treino")
                if isinstance(error, AdsError):
                    raise
                raise AdsError(f"botão do vídeo de treino não encontrado ({type(error).__name__})") from error
            deadline = time.time() + WAIT_FOR_REWARD
            while time.time() < deadline:
                page.wait_for_timeout(3000)
                if before - finishes() >= VIDEO_SAVES / 2:
                    break
            else:
                save_failure(page, "treino")
                raise AdsError("o tempo do treino não baixou")
            cookies = context.cookies()
            if any(c["name"] == "access_token" for c in cookies):
                state = {"cookies": cookies, "origins": []}
        finally:
            browser.close()
    if state:
        save_private(STATE_FILE, state)


MONEY_ACTIONS = ("Multistep1", "Multistep2", "Multistep3")
MAX_MONEY_VIDEOS = 3  # per day, set by the game
MONEY_CARD = ".multistep-block-container.step-available"  # the next free-reward card (done ones are .step-reached)
MONEY_DONE = ".multistep-block-container.step-reached"


def money_state(client) -> dict:
    """Free-reward videos: {"open": a card can be watched now, "reopen": when the cards come back (or None)}."""
    open_now, reopen = False, []
    for action in MONEY_ACTIONS:
        _, cap = client.get(f"user/caps/actions/{action}/0")
        if cap.get("isClaimable") and not cap.get("isCapReached"):
            open_now = True
        elif cap.get("isCapReached") and cap.get("timestampUntilUnreached"):
            reopen.append(cap["timestampUntilUnreached"])
    return {"open": open_now, "reopen": None if open_now or not reopen else min(reopen)}


def pick_money_club(savings: dict[str, int]) -> str | None:
    """The reward is a percentage of the club's savings, so the club with the most savings gets it."""
    return max(savings, key=savings.get) if savings else None


def run_money_ads(claimable: Callable[[], bool], pick_club: Callable[[], str | None],
                  watch_one: Callable[[str], None], *, dry_run: bool = False,
                  log: Callable[[str], None] = print, rng=random, sleep=time.sleep) -> int:
    """Watch the free-reward (money) videos while the game allows it. Returns how many were watched."""
    if not claimable():
        return 0
    if rng.random() > ENGAGE_CHANCE:
        log("Dinheiro: janela saltada")
        return 0
    club = pick_club()
    if club is None:
        return 0
    if dry_run:
        log(f"Simulação: veria vídeos de dinheiro em {club}")
        return 0
    watched = 0
    while watched < MAX_MONEY_VIDEOS:
        watch_one(club)
        watched += 1
        log(f"Dinheiro: vídeo {watched} ({club})")
        if not claimable():
            break
        sleep(rng.uniform(*PAUSE))
    return watched


def watch_money_video(client, club: str, headless: bool = True) -> None:
    """Open the club, click the money bar, click the next free-reward card and wait until it counts as done."""
    from playwright.sync_api import sync_playwright

    from osmbot.game.browser import STATE_FILE
    from osmbot.game.client import save_private

    state = None
    with sync_playwright() as playwright:
        browser = playwright.firefox.launch(headless=headless)
        try:
            context = browser.new_context(storage_state=str(STATE_FILE), viewport={"width": 1280, "height": 900})
            page = context.new_page()
            try:
                _open_club(page, club)
                page.locator(".clubfunds-wallet").first.click(timeout=PAGE_TIMEOUT)
                page.wait_for_selector(MONEY_CARD, timeout=PAGE_TIMEOUT)
                before = page.locator(MONEY_DONE).count()
                page.locator(MONEY_CARD).first.click(timeout=PAGE_TIMEOUT)
            except Exception as error:
                save_failure(page, "dinheiro")
                raise AdsError(f"cartão de dinheiro não encontrado ({type(error).__name__})") from error
            deadline = time.time() + WAIT_FOR_REWARD
            claimed_by_hand = False
            while time.time() < deadline:
                page.wait_for_timeout(3000)
                if page.locator(MONEY_DONE).count() > before:
                    break
                if not claimed_by_hand and time.time() > deadline - WAIT_FOR_REWARD + 20:
                    button = page.get_by_role("button", name=re.compile(r"^\s*(claim|collect|get reward)\s*$", re.I))
                    if button.count():  # some rewards may need a click to collect
                        button.first.click()
                    claimed_by_hand = True
            else:
                save_failure(page, "dinheiro")
                raise AdsError("o cartão de dinheiro não passou a visto")
            cookies = context.cookies()
            if any(c["name"] == "access_token" for c in cookies):
                state = {"cookies": cookies, "origins": []}
        finally:
            browser.close()
    if state:
        save_private(STATE_FILE, state)
