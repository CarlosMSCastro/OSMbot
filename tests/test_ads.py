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
        return 0 if len(trains) < 4 else 1

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
    assert ads.run_money_ads(lambda: True, lambda: "A", watch, log=lambda m: None, rng=Rng(roll=0.99)) == 0
