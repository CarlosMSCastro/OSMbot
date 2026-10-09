import pytest

from osmbot.game import ads, loop
from osmbot.game.ads import AdsError, MAX_PER_BURST, run_shop_ads


class Rng:
    def __init__(self, roll=0.0, pause=1.0):
        self.roll, self.pause = roll, pause

    def random(self):
        return self.roll

    def uniform(self, a, b):
        return self.pause


def test_nothing_happens_when_the_game_limit_is_closed():
    watched = []
    assert run_shop_ads(lambda: False, lambda: watched.append(1), log=lambda m: None, rng=Rng()) == 0
    assert watched == []


def test_some_windows_are_skipped_on_purpose():
    watched = []
    assert run_shop_ads(lambda: True, lambda: watched.append(1), log=lambda m: None, rng=Rng(roll=0.99)) == 0
    assert watched == []


def test_dry_run_watches_nothing():
    watched = []
    assert run_shop_ads(lambda: True, lambda: watched.append(1), dry_run=True, log=lambda m: None, rng=Rng()) == 0
    assert watched == []


def test_watches_until_the_game_closes_the_limit():
    state = {"left": 3}

    def watch():
        state["left"] -= 1

    pauses = []
    count = run_shop_ads(lambda: state["left"] > 0, watch, log=lambda m: None, rng=Rng(pause=7), sleep=pauses.append)
    assert count == 3 and pauses == [7, 7]  # no pause after the last one


def test_never_exceeds_the_burst_maximum_even_if_the_game_keeps_it_open():
    count = run_shop_ads(lambda: True, lambda: None, log=lambda m: None, rng=Rng(), sleep=lambda s: None)
    assert count == MAX_PER_BURST


def test_a_failed_video_stops_the_burst():
    def watch():
        raise AdsError("sem botao")

    with pytest.raises(AdsError):
        run_shop_ads(lambda: True, watch, log=lambda m: None, rng=Rng(), sleep=lambda s: None)


def test_loop_keeps_retrying_ads_and_training_after_failures(monkeypatch):
    attempts, trains = [], []

    def broken(dry_run):
        attempts.append(1)
        raise AdsError("x")

    def train(confirm):
        trains.append(1)
        if len(trains) >= 4:
            raise SystemExit(1)
        return 0

    with pytest.raises(SystemExit):
        loop.run_active(claim=lambda c: 0, train=train, finish_times=lambda: [], ads=broken,
                        sleep=lambda s: None, rng=Rng())
    assert len(attempts) == 3 and len(trains) == 4


def _session(trainer, finishes, claimed=False):
    return {"id": trainer, "trainer": trainer, "countdownTimer": {"finishedTimestamp": finishes, "isClaimed": claimed}}


def test_pick_session_takes_the_one_with_most_time_left():
    now = 1000
    sessions = [("A", _session(1, now + 3 * 3600)), ("A", _session(2, now + 7 * 3600)), ("B", _session(3, now + 5 * 3600))]
    club, chosen = ads.pick_session(sessions, now)
    assert (club, chosen["trainer"]) == ("A", 2)


def test_pick_session_skips_short_claimed_and_empty():
    now = 1000
    assert ads.pick_session([("A", _session(1, now + 3600)), ("A", _session(2, now + 9 * 3600, claimed=True))], now) is None
    assert ads.pick_session([], now) is None


def test_training_videos_even_out_the_sessions():
    finishes = {1: 8 * 3600, 2: 8 * 3600, 3: 5 * 3600, 4: 3 * 3600}
    used = []

    def sessions():
        return [("A", _session(t, f)) for t, f in finishes.items()]

    def watch(club, session):
        used.append(session["trainer"])
        finishes[session["trainer"]] -= 2 * 3600

    ads.run_training_ads(lambda: len(used) < 4, sessions, watch, log=lambda m: None, rng=Rng(),
                         sleep=lambda s: None, clock=lambda: 0)
    assert used == [1, 2, 1, 2]  # always the one with most time left; the 3h one is never touched


def test_training_videos_dry_run_clicks_nothing():
    watched = []
    ads.run_training_ads(lambda: True, lambda: [("A", _session(1, 9 * 3600))], lambda c, s: watched.append(1),
                         dry_run=True, log=lambda m: None, rng=Rng(), clock=lambda: 0)
    assert watched == []


def test_money_videos_go_to_the_club_with_most_savings():
    assert ads.pick_money_club({"A": 28_000_000, "B": 4_900_000}) == "A"
    assert ads.pick_money_club({}) is None


def test_money_state_open_and_reopen_time():
    class Client:
        def __init__(self, caps):
            self.caps = caps

        def get(self, path):
            return 200, self.caps[path.split("/")[-2]]

    free = {"isClaimable": True, "isCapReached": False}
    capped = lambda t: {"isClaimable": False, "isCapReached": True, "timestampUntilUnreached": t}  # noqa: E731
    assert ads.money_state(Client({"Multistep1": capped(500), "Multistep2": free, "Multistep3": free})) == {"open": True, "reopen": None}
    assert ads.money_state(Client({"Multistep1": capped(900), "Multistep2": capped(700), "Multistep3": capped(800)})) == {"open": False, "reopen": 700}


def test_money_videos_stop_when_the_game_closes_the_limit():
    left = {"n": 2}
    seen = []

    def watch(club):
        seen.append(club)
        left["n"] -= 1

    count = ads.run_money_ads(lambda: left["n"] > 0, lambda: "A", watch, log=lambda m: None, rng=Rng(), sleep=lambda s: None)
    assert count == 2 and seen == ["A", "A"]
    assert ads.run_money_ads(lambda: True, lambda: "A", watch, dry_run=True, log=lambda m: None, rng=Rng()) == 0
    left["n"] = 1
    assert ads.run_money_ads(lambda: left["n"] > 0, lambda: "A", watch, log=lambda m: None, rng=Rng(roll=0.99)) == 1  # never skipped


def test_training_videos_are_never_skipped_only_the_shop_ones_are():
    session = {"id": 1, "trainer": 4, "countdownTimer": {"finishedTimestamp": 10_000, "isClaimed": False}}
    seen, said = [], []
    count = ads.run_training_ads(lambda: len(seen) < 1, lambda: [("A", session)], lambda c, s: seen.append(c),
                                 log=said.append, rng=Rng(roll=0.99), sleep=lambda s: None, clock=lambda: 0)
    assert count == 1 and not [m for m in said if "saltada" in m]


class _Locator:
    def __init__(self, page, shows):
        self.page, self.shows = page, shows
        self.first = self

    def filter(self, **kwargs):
        return self

    def count(self):
        return 1 if self.shows() else 0

    def click(self, timeout=None):
        self.page.advance()


class _Mouse:
    def __init__(self, page):
        self.page = page

    def click(self, x, y):
        assert self.page.top() == "xp"  # only ever clicks beside the XP window
        self.page.advance()


class _Page:
    """A page that shows the screens after a round one after the other: "continue", "skip" (the match,
    under a "Matchday" header) and "xp" (the manager-XP window). A plain int = that many "continue"."""

    viewport_size = {"width": 1280, "height": 900}

    def __init__(self, screens):
        self.screens = ["continue"] * screens if isinstance(screens, int) else list(screens)
        self.clicks = 0
        self.mouse = _Mouse(self)

    @property
    def remaining(self):
        return len(self.screens)

    def top(self):
        return self.screens[0] if self.screens else None

    def advance(self):
        self.clicks += 1
        if self.screens and not (len(self.screens) == 1 and self.endless):
            self.screens.pop(0)

    endless = False

    def get_by_text(self, pattern):
        if pattern.match("Continue"):
            assert not pattern.match("Continue training")
            return _Locator(self, lambda: self.top() == "continue")
        if pattern.match("Skip"):
            return _Locator(self, lambda: self.top() == "skip")
        if pattern.match("Unclaimed Energy") or pattern.match("Claim"):
            return _Locator(self, lambda: self.top() == "energy")
        assert pattern.match("Matchday 12/26")
        return _Locator(self, lambda: self.top() in ("continue", "skip"))

    def locator(self, selector):
        assert selector == "#skillRatingUpdate-modal-content"
        return _Locator(self, lambda: self.top() == "xp")

    def wait_for_timeout(self, ms):
        pass


def test_the_matchday_screen_is_dismissed_before_the_club_is_used():
    from osmbot.game.ads import _dismiss_matchday

    page = _Page(screens=1)
    _dismiss_matchday(page)
    assert page.clicks == 1 and page.remaining == 0


def test_the_whole_chain_after_a_round_is_dismissed_skip_and_xp_window_included():
    from osmbot.game.ads import _dismiss_matchday

    page = _Page(["continue", "skip", "continue", "xp"])  # seen in the game on 2026-10-07
    _dismiss_matchday(page)
    assert page.clicks == 4 and page.remaining == 0


def test_the_unclaimed_energy_window_is_claimed_like_the_owner_does():
    from osmbot.game.ads import _dismiss_matchday

    page = _Page(["energy", "continue"])  # seen on the career page after the daily missions (2026-10-09)
    _dismiss_matchday(page)
    assert page.clicks == 2 and page.remaining == 0


def test_nothing_is_clicked_when_there_is_no_matchday_screen():
    from osmbot.game.ads import _dismiss_matchday

    page = _Page(screens=0)
    _dismiss_matchday(page)
    assert page.clicks == 0


def test_it_never_clicks_continue_forever():
    from osmbot.game.ads import MAX_CONTINUES, _dismiss_matchday

    page = _Page(screens=1)
    page.endless = True
    _dismiss_matchday(page)
    assert page.clicks == MAX_CONTINUES


def test_every_browser_job_starts_by_getting_past_the_continue_screen():
    from osmbot.game.ads import _open_game

    class Page(_Page):
        def goto(self, url):
            self.opened = url

    page = Page(screens=2)
    _open_game(page)
    assert page.opened.startswith("https://en.onlinesoccermanager.com") and page.clicks == 2


def test_a_button_covered_by_a_late_xp_window_is_clicked_after_closing_it():
    from osmbot.game.ads import _click_past_windows

    page = _Page([])

    class Tile:
        tries = 0

        def click(self, timeout=None):
            Tile.tries += 1
            if page.top() == "xp":
                raise TimeoutError("covered by the XP window")

    page.screens = ["xp"]  # shows up only after the club was opened (seen 2026-10-08)
    _click_past_windows(page, Tile())
    assert Tile.tries == 2 and page.remaining == 0


def test_a_free_button_is_clicked_once():
    from osmbot.game.ads import _click_past_windows

    page = _Page(screens=0)

    class Tile:
        tries = 0

        def click(self, timeout=None):
            Tile.tries += 1

    _click_past_windows(page, Tile())
    assert Tile.tries == 1 and page.clicks == 0


def test_video_firefox_is_muted():
    seen = {}

    class Firefox:
        def launch(self, **options):
            seen.update(options)

    class Playwright:
        firefox = Firefox()

    ads._launch(Playwright(), headless=True)
    assert seen == {"headless": True, "firefox_user_prefs": {"media.volume_scale": "0.0"}}


class _Game:
    """A browser on the game: ``where`` is "career", a club's name, or "result" (the last match's screen,
    whose Continue goes back to the career page). ``late`` = the result screen shows up right after the
    first club card is clicked, too late for the dismissal (seen 2026-10-09)."""

    viewport_size = {"width": 1280, "height": 900}

    def __init__(self, late=0, lands_on=None):
        self.where, self.late, self.lands_on, self.cards = "career", late, lands_on, 0

    def goto(self, url):
        self.where = "career"

    def wait_for_timeout(self, ms):
        if self.late and self.where != "career":
            self.late -= 1
            self.where = "result"

    def locator(self, selector, has_text=None):
        if selector == ".clubslot-main-title":
            def open_card():
                assert self.where == "career"
                self.cards += 1
                self.where = self.lands_on or has_text
            return _Element(lambda: self.where == "career", open_card)
        return _Element(lambda: False)

    def get_by_text(self, pattern, exact=False):
        if pattern.match("Continue"):
            return _Element(lambda: self.where == "result", lambda: setattr(self, "where", "career"))
        if pattern.match("Skip") or pattern.match("Matchday 12/26"):
            return _Element(lambda: False)
        return _Element(lambda: self.where != "result" and pattern.match(self.last), y=27)  # the career page names it too

    @property
    def last(self):
        return self.where if self.where not in ("career", "result") else getattr(self, "_last", "")

    def __setattr__(self, name, value):
        if name == "where" and value not in ("career", "result"):
            object.__setattr__(self, "_last", value)
        object.__setattr__(self, name, value)


class _Element:
    def __init__(self, shown, on_click=None, y=500):
        self.shown, self.on_click, self.y = shown, on_click, y

    def filter(self, visible=None):
        return self

    @property
    def first(self):
        return self

    def count(self):
        return int(bool(self.shown()))

    def all(self):
        return [self] if self.shown() else []

    def bounding_box(self):
        return {"x": 20, "y": self.y, "width": 100, "height": 20}

    def click(self, timeout=None, force=None):
        if not self.shown():
            raise TimeoutError("not on screen")
        self.on_click()


def test_the_club_is_opened_again_when_the_last_match_screen_sends_it_back_to_the_career_page():
    from osmbot.game.ads import _open_club

    page = _Game(late=1)
    _open_club(page, "Clube B")
    assert page.where == "Clube B" and page.cards == 2


def test_it_never_stays_in_another_club():
    from osmbot.game.ads import CLUB_TRIES, AdsError, _open_club

    page = _Game(lands_on="Clube A")
    with pytest.raises(AdsError, match="Clube B"):
        _open_club(page, "Clube B")
    assert page.cards == CLUB_TRIES


def test_the_step_inside_the_club_is_tried_again_from_the_start_when_it_fails():
    from osmbot.game.ads import _open_club

    page, tries = _Game(), []

    def training():
        tries.append(1)
        if len(tries) == 1:
            raise TimeoutError("Training tile covered")

    _open_club(page, "Clube B", training)
    assert len(tries) == 2 and page.where == "Clube B"


def test_the_career_page_is_not_taken_for_the_club_although_it_names_it_at_the_top():
    from osmbot.game.ads import _in_club

    page = _Game()
    page.where = "Clube B"
    page.where = "career"
    assert page.last == "Clube B" and not _in_club(page, "Clube B")


def test_after_every_try_failing_the_last_error_is_raised():
    from osmbot.game.ads import CLUB_TRIES, _open_club

    page = _Game()

    def training():
        raise TimeoutError("Training tile covered")

    with pytest.raises(TimeoutError):
        _open_club(page, "Clube B", training)
    assert page.cards == CLUB_TRIES
