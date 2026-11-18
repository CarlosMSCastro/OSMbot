"""Shop videos (boss coins) watched in a real, invisible Firefox (D-012, DISCOVERY.md 2026-10-05).

The page itself plays the ad and tells the game it was watched; this only opens the shop and
clicks "Watch ad", exactly like the owner does by hand. It never calls ``videos/watched``.
Limits come from the game (``user/caps/actions/BusinessClub/0``) and are never exceeded; pauses are
random and some SHOP windows are skipped, so the pattern is not that of a machine. Training and money
videos are never skipped: training time is worth more than the coins (owner, 2026-10-08).
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
ENGAGE_CHANCE = 0.85  # share of the SHOP windows in which it watches videos at all (training and money: always, owner 2026-10-08)
MAX_PER_BURST = 9  # the shop's own limit per window
PAUSE = (20.0, 75.0)  # seconds between two videos
WAIT_FOR_REWARD = 90.0  # seconds to wait for the boss coins to arrive
PAGE_TIMEOUT = 60_000  # ms (slow office PCs / networks)
QUICK_CLICK = 15_000  # ms: a first try; if a late window covers the button, close it and try again
MUTED = {"media.volume_scale": "0.0"}  # Firefox plays the ads silently; the page still sees the video playing (owner, 2026-10-08)


def _launch(playwright, headless: bool):
    """The Firefox used for videos: muted, so the ads make no sound on the owner's PC."""
    return playwright.firefox.launch(headless=headless, firefox_user_prefs=MUTED)


AD_COOKIES_FILE = Path.home() / ".osmbot" / "anuncios_cookies.json"
AD_COOKIES_KEPT = 300  # at most this many


def ad_cookies(cookies: list[dict], now: float) -> list[dict]:
    """The cookies worth keeping between two videos (D-112): those of the ad companies and Google, not the game's own
    (its tokens are kept by ``save_browser_session``), and only those still valid. A browser that forgot every cookie
    after each video would reach the ad network as a visitor with no history each time; keeping them is what any
    browser does. Nothing is changed or invented: they are the ones the pages themselves set."""
    kept = [c for c in cookies
            if "onlinesoccermanager" not in c.get("domain", "") and (c.get("expires", -1) in (-1, None) or c["expires"] > now)]
    return kept[-AD_COOKIES_KEPT:]


def save_ad_cookies(cookies: list[dict], path: Path = AD_COOKIES_FILE, now: float | None = None) -> None:
    from osmbot.game.client import save_private

    try:
        save_private(path, ad_cookies(cookies, time.time() if now is None else now))
    except Exception:  # a failed save never stops a video
        pass


def load_ad_cookies(path: Path = AD_COOKIES_FILE, now: float | None = None) -> list[dict]:
    import json

    try:
        return ad_cookies(json.loads(path.read_text(encoding="utf-8")), time.time() if now is None else now)
    except (OSError, ValueError, TypeError):
        return []


def new_context(browser):
    """The browser context for every video: the game's session as always, plus the ad cookies kept from the last videos."""
    from osmbot.game.browser import STATE_FILE

    context = browser.new_context(storage_state=str(STATE_FILE), viewport={"width": 1280, "height": 900})
    saved = load_ad_cookies()
    try:
        context.add_cookies(saved)
    except Exception:  # one odd cookie must not stop the rest: add them one by one
        for cookie in saved:
            try:
                context.add_cookies([cookie])
            except Exception:
                pass
    return context


_TRACKED: dict[int, list[str]] = {}  # id(page) -> what the page and the network did during this attempt
NOTES_KEPT = 200  # lines per attempt


def _plain(url: str) -> str:
    """A URL as host and path only: no query string (it can carry tokens)."""
    return url.split("?", 1)[0].split("#", 1)[0][:140]


def track(page) -> None:
    """Note, for the failure files (owner, 2026-11-18, audit of the video errors): the page's console errors, the
    requests that failed and the answers of 400 and above, each as a line with host and path only."""
    notes: list[str] = []
    _TRACKED[id(page)] = notes

    def add(line: str) -> None:
        if len(notes) < NOTES_KEPT:
            notes.append(f"{time.strftime('%H:%M:%S')} {line}")

    try:
        page.on("console", lambda m: add(f"console.{m.type}: {m.text[:200]}") if m.type in ("error", "warning") else None)
        page.on("pageerror", lambda e: add(f"pageerror: {str(e)[:200]}"))
        page.on("requestfailed", lambda r: add(f"falhou {r.method} {_plain(r.url)}: {(r.failure or '')[:80]}"))
        page.on("response", lambda r: add(f"{r.status} {r.request.method} {_plain(r.url)}") if r.status >= 400 else None)
    except Exception:
        pass


WINDOWS_JS = r"""() => [...document.querySelectorAll('[id*=modal i],[class*=modal i],[role=dialog],[class*=popup i],[class*=overlay i]')]
    .filter(e => e.offsetWidth > 60 && e.offsetHeight > 60)
    .map(e => e.tagName + '#' + (e.id || '') + '.' + String(e.className || '').slice(0, 60) + ' ' + e.offsetWidth + 'x' + e.offsetHeight
         + ' text=' + (e.innerText || '').replace(/\s+/g, ' ').slice(0, 70)).slice(0, 14)"""


def save_failure(page, tag: str, image: bytes | None = None) -> None:
    """Keep a screenshot of what the browser was showing when a video failed (~/.osmbot/failures/), to debug later,
    and beside it a .txt with what the page and the network did (``track``). ``image``: one taken earlier (e.g. just
    after the click) instead of a new one."""
    try:
        folder = Path.home() / ".osmbot" / "failures"
        folder.mkdir(parents=True, exist_ok=True)
        for pattern in ("*.png", "*.txt"):
            for old in sorted(folder.glob(pattern))[:-10]:  # keep the last 10 of each only
                old.unlink()
        stamp = time.strftime('%Y%m%d-%H%M%S')
        target = folder / f"{stamp}-{tag}.png"
        if image is not None:
            target.write_bytes(image)
        else:
            page.screenshot(path=str(target))
        notes = _TRACKED.get(id(page))
        if notes is not None:
            try:  # the windows in front of the page (which one covered the card?): id, class, size and the start of its text
                notes = notes + [f"janelas visiveis: {item}" for item in page.evaluate(WINDOWS_JS)] if hasattr(page, "evaluate") else notes
            except Exception:
                pass
            (folder / f"{stamp}-{tag}.txt").write_text("\n".join(notes) or "(nada a registar)", encoding="utf-8")
    except Exception:
        pass


class AdsError(Exception):
    """The ad flow did not work (button missing, coins did not arrive...). The loop tries again later."""


def is_claimable(client, action_id: str = SHOP_ACTION) -> bool:
    _, cap = client.get(f"user/caps/actions/{action_id}/0")
    return bool(cap.get("isClaimable")) and not cap.get("isCapReached")


def run_shop_ads(claimable: Callable[[], bool], watch_one: Callable[[], None], *, dry_run: bool = False,
                 log: Callable[[str], None] = print, rng=random, sleep=time.sleep,
                 training_ready: Callable[[], bool] = lambda: False) -> int:
    """Watch shop videos while the game allows it. Returns how many were watched. Stops between two videos when a
    training is ready to collect (owner, 2026-10-14: in 2 h events a burst of ~20 min costs too much); the rest of
    the window is watched in the next pass, once the trainings are collected and started again."""
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
        if training_ready():
            log("Loja: pausa, há treinos para recolher")
            break
        sleep(rng.uniform(*PAUSE))
    return watched


def _wallet_amount(client) -> int:
    _, wallet = client.get("user/bosscoinwallet")
    return wallet["amount"]


AFTER_CLICK = 5000  # ms: the screenshot kept (only if the video then fails) to tell "never started" from "no coins"


def watch_shop_video(client, headless: bool = True) -> int:
    """Open the shop in Firefox, scroll to the "Watch ad" button, click it and wait for the boss coins to arrive.
    Returns the boss coins the video gave."""
    from playwright.sync_api import sync_playwright

    from osmbot.game.client import save_browser_session

    before = _wallet_amount(client)
    cookies, gained = None, 0
    with sync_playwright() as playwright:
        browser = _launch(playwright, headless)
        try:
            context = new_context(browser)
            page = context.new_page()
            track(page)
            _open_game(page)
            try:
                _click_past_windows(page, page.locator("a:visible", has_text="Shop").first)
                button = page.get_by_text("Watch ad", exact=False).filter(visible=True).first
                button.scroll_into_view_if_needed(timeout=PAGE_TIMEOUT)  # the videos are at the far right of the shop
                _click_past_windows(page, button)
            except Exception as error:
                save_failure(page, "loja")
                raise AdsError(f"botão da loja não encontrado ({type(error).__name__})") from error
            page.wait_for_timeout(AFTER_CLICK)
            try:
                clicked = page.screenshot()
            except Exception:
                clicked = None
            deadline = time.time() + WAIT_FOR_REWARD
            while time.time() < deadline:
                page.wait_for_timeout(3000)
                gained = _wallet_amount(client) - before
                if gained > 0:
                    break
            else:
                save_failure(page, "loja-clique", clicked)
                save_failure(page, "loja")
                raise AdsError("os boss coins não subiram")
            cookies = context.cookies()
        finally:
            try:  # also after a failed video: the ad cookies are kept for the next one (D-112)
                save_ad_cookies(context.cookies())
            except Exception:
                pass
            browser.close()
    if cookies:  # the site may have renewed the tokens: keep the saved session in step with it (if newer)
        save_browser_session(cookies)
    return gained


def watch_with_retry(watch: Callable[[], int], claimable: Callable[[], bool]) -> int:
    """One shop video, tried a second time straight away if it fails: the ad network sometimes has no video for a
    moment (~4% of the videos, 2026-10-08/09), and waiting 10 min may let the shop window close. Not retried when
    the shop has closed meanwhile (the game may have counted it)."""
    try:
        return watch()
    except AdsError:
        if not claimable():
            return 0
        return watch()


def pick_session(candidates: list[tuple[str, dict]], now: float) -> tuple[str, dict] | None:
    """The session that should get the next -2h video: the one with the MOST time left, so all of
    them end up finishing around the same time (owner's choice, 2026-10-05). Sessions with less
    than 2h left are skipped (the video would be partly wasted). ``candidates`` = (club name, session)."""
    usable = [(club, s) for club, s in candidates  # not the universal trainer's (trainer 5): its page button is not known
              if s.get("trainer") in COACH_TITLES and not s["countdownTimer"]["isClaimed"]
              and s["countdownTimer"]["finishedTimestamp"] - now >= VIDEO_SAVES]
    if not usable:
        return None
    return max(usable, key=lambda c: c[1]["countdownTimer"]["finishedTimestamp"])


def run_training_ads(claimable: Callable[[], bool], load_sessions: Callable[[], list[tuple[str, dict]]],
                     watch_one: Callable[[str, dict], None], *, dry_run: bool = False,
                     log: Callable[[str], None] = print, rng=random, sleep=time.sleep, clock=time.time) -> int:
    """Use training videos (-2h) while the game allows it. Returns how many were watched."""
    if not claimable():
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


MAX_CONTINUES = 6  # screens in a row after a round: Continue, the match (Skip), Continue, manager XP
# "Unclaimed Energy" seen 2026-10-09; the boss-coins title is not seen in English yet (the owner saw it in Portuguese)
UNCLAIMED = re.compile(r"^\s*(unclaimed\s+(energy|boss\s*coins?)|boss\s*coins?\s+(unclaimed|não\s+reclamad[ao]s))\s*$", re.I)


def _dismiss_matchday(page) -> None:
    """After a round the game shows, over the club's home, a chain of screens that hide the menus (seen
    2026-10-07): "Matchday ... Continue", then the match itself ("Skip"), "Continue" again, and the
    manager-XP window, which only closes with a click outside it. Go through them as the owner does by
    hand. "Skip" is only pressed on the matchday screen; nothing in the XP window is clicked.
    The "Unclaimed Energy" window (energy waiting, e.g. after the daily missions) is claimed: the owner always
    does so (2026-10-09, THEORY.md section 17); the energy goes to its wallet. So is the boss-coins one (D-055: boss
    coins go to the wallet): on 2026-10-15 it covered the shop and the training page for 3h30 after the missions'
    5 boss coins went to the inventory (title assumed by analogy, UNCLAIMED)."""
    for _ in range(MAX_CONTINUES):
        button = page.get_by_text(re.compile(r"^\s*continue\s*$", re.I)).filter(visible=True)
        if not button.count() and page.get_by_text(re.compile(r"^\s*matchday\b", re.I)).filter(visible=True).count():
            button = page.get_by_text(re.compile(r"^\s*skip\s*$", re.I)).filter(visible=True)
        if not button.count() and page.get_by_text(UNCLAIMED).filter(visible=True).count():
            button = page.get_by_text(re.compile(r"^\s*claim\s*$", re.I)).filter(visible=True)
        if button.count():
            button.first.click(timeout=PAGE_TIMEOUT)
        elif page.locator("#skillRatingUpdate-modal-content").filter(visible=True).count():
            size = page.viewport_size or {"width": 1280, "height": 900}
            page.mouse.click(size["width"] - 40, size["height"] // 2)  # the dark backdrop, beside the window
        else:
            return
        page.wait_for_timeout(3000)


def _click_past_windows(page, locator) -> None:
    """Click, but if the round's screens (above all the manager-XP window) show up late and cover the
    button, get past them and click again. Seen 2026-10-08: the XP window came after the check."""
    try:
        locator.click(timeout=QUICK_CLICK)
    except Exception:
        _dismiss_matchday(page)
        locator.click(timeout=PAGE_TIMEOUT)


def _open_game(page) -> None:
    """Open the game (the career page) and get past the "Continue" screen the game often shows after a
    match, whatever the task: every browser job starts here."""
    page.goto("https://en.onlinesoccermanager.com/")
    page.wait_for_timeout(4000)
    _dismiss_matchday(page)


CLUB_TRIES = 3  # the last match's screen can show up late and send the browser back to the career page
HEADER_BOTTOM = 80  # px: the club in use is named at the top left, above the menu (seen 2026-10-09)


def _in_club(page, club: str) -> bool:
    """True when the club's name is at the top left (the club in use), no round screen is in front and it is not the
    career page (which also names the last club used up there, seen 2026-10-09)."""
    if page.get_by_text(re.compile(r"^\s*continue\s*$", re.I)).filter(visible=True).count():
        return False
    if page.locator(".clubslot-main-title").filter(visible=True).count():
        return False
    names = page.get_by_text(re.compile(rf"^\s*{re.escape(club)}\s*$", re.I)).filter(visible=True).all()
    return any((box := name.bounding_box()) and box["y"] < HEADER_BOTTOM for name in names)


def _open_club(page, club: str, then: Callable[[], None] | None = None) -> None:
    """Career page -> the club's card (opens the club's home screen), then ``then`` (e.g. a tile inside the club).
    The last match's screen shows up on the first visit of every new session, at no fixed moment (owner,
    2026-10-09); its "Continue" can land on the career page or on another club. So it checks where it ended up
    and starts again from the career page, up to CLUB_TRIES times."""
    error: Exception | None = None
    for _ in range(CLUB_TRIES):
        try:
            _open_game(page)
            page.locator(".clubslot-main-title", has_text=club).first.click(force=True, timeout=PAGE_TIMEOUT)
            page.wait_for_timeout(6000)
            _dismiss_matchday(page)
            if then:
                then()
            if _in_club(page, club):
                return
            error = None
        except Exception as failure:
            error = failure
    if error:
        raise error
    raise AdsError(f"não consegui ficar em {club} (outro clube ou ecrã do jogo à frente)")


def _open_training_page(page, club: str, trainer: int) -> None:
    """The club's card, then its "TRAINING" tile (the top "Training Ground" menu does not react to clicks), until
    the trainer's column is on screen."""

    def training() -> None:
        _click_past_windows(page, page.locator("text=/^training$/i").filter(visible=True).first)
        page.wait_for_timeout(5000)
        page.get_by_text(COACH_TITLES[trainer], exact=True).filter(visible=True).first.wait_for(timeout=QUICK_CLICK)

    _open_club(page, club, training)


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

    from osmbot.game.client import save_browser_session

    def finishes() -> float:
        _, sessions = client.get(f"{base}/trainingsessions/ongoing")
        return next(s["countdownTimer"]["finishedTimestamp"] for s in sessions if s["id"] == session["id"])

    before = finishes()
    cookies = None
    with sync_playwright() as playwright:
        browser = _launch(playwright, headless)
        try:
            context = new_context(browser)
            page = context.new_page()
            track(page)
            try:
                _open_training_page(page, club, session["trainer"])
                button = _coach_button(page, session["trainer"])
                if dry_run:
                    return
                _click_past_windows(page, button)
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
        finally:
            try:  # also after a failed video: the ad cookies are kept for the next one (D-112)
                save_ad_cookies(context.cookies())
            except Exception:
                pass
            browser.close()
    if cookies:
        save_browser_session(cookies)


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

    from osmbot.game.client import save_browser_session

    cookies = None
    with sync_playwright() as playwright:
        browser = _launch(playwright, headless)
        try:
            context = new_context(browser)
            page = context.new_page()
            track(page)
            try:
                _open_club(page, club)
                _click_past_windows(page, page.locator(".clubfunds-wallet").first)
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
        finally:
            try:  # also after a failed video: the ad cookies are kept for the next one (D-112)
                save_ad_cookies(context.cookies())
            except Exception:
                pass
            browser.close()
    if cookies:
        save_browser_session(cookies)
