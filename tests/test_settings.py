from osmbot import settings
from osmbot.game.trainings import _teams
from osmbot.i18n import set_pref


def test_everything_is_on_until_a_switch_is_turned_off():
    assert settings.allowed({}, "1_9") and settings.allowed({}, "1_9", "amigavel")
    clubs = settings.with_club({}, "1_9", automation="amigavel", on=False)
    assert not settings.allowed(clubs, "1_9", "amigavel") and settings.allowed(clubs, "1_9", "analise")
    assert settings.allowed(clubs, "1_9") and settings.allowed(clubs, "1_7", "amigavel")  # the others stay on


def test_an_inactive_club_allows_nothing_and_a_change_does_not_touch_the_original():
    original = settings.with_club({}, "1_9", automation="analise", on=False)
    clubs = settings.with_club(original, "1_9", active=False)
    assert not settings.allowed(clubs, "1_9") and not settings.allowed(clubs, "1_9", "analise")
    assert settings.allowed(original, "1_9")  # a copy: the first dict is unchanged
    assert settings.with_club(clubs, "1_9", active=True)["1_9"]["automacoes"] == {"analise": False}


def test_the_club_key_is_league_and_team_and_the_config_survives_a_bad_value():
    assert settings.club_key({"leagueId": 215, "id": 9}) == "215_9"
    set_pref("clubes", "lixo")
    assert settings.load() == {}


class Client:
    def get(self, path):
        teams = {"1": {"team": {"id": 9, "leagueId": 5, "name": "A"}}, "2": {"team": {"id": 7, "leagueId": 5, "name": "B"}}}
        return 200, {"teamSlots": teams}


def test_writing_skips_inactive_clubs_and_clubs_without_that_automation_but_reading_sees_all():
    set_pref("clubes", settings.with_club(settings.with_club({}, "5_9", active=False), "5_7", automation="medico", on=False))
    names = lambda *args, **kwargs: [t["name"] for _, t, _ in _teams(Client(), *args, **kwargs)]
    assert names() == ["A", "B"]  # reading: every club
    assert names(writing=True) == ["B"]  # A is off
    assert names("medico", writing=True) == []  # B has no médico
    assert names("analise", writing=True) == ["B"]


class TrainingClient(Client):
    def get(self, path):
        if path == "user/accounts":
            return super().get(path)
        return 200, [{"countdownTimer": {"finishedTimestamp": 100.0, "isClaimed": False}}]


def test_a_club_left_out_does_not_keep_the_loop_awake_with_trainings_it_will_never_collect():
    from osmbot.game.trainings import pending_finish_times

    assert pending_finish_times(TrainingClient()) == [100.0, 100.0]
    set_pref("clubes", settings.with_club(settings.with_club({}, "5_9", active=False), "5_7", automation="treino", on=False))
    assert pending_finish_times(TrainingClient()) == []


def test_the_account_switches_are_on_until_turned_off_and_the_ceiling_needs_a_positive_number():
    assert settings.account_allowed({}, "videos") and not settings.account_allowed({"videos": False}, "videos")
    assert settings.spending_cap({}) is None and settings.spending_cap({settings.CAP: 0}) is None
    assert settings.spending_cap({settings.CAP: 60}) == 60 and settings.spending_cap({settings.CAP: "x"}) is None
    set_pref("conta", "lixo")
    assert settings.load_account() == {}


def test_the_ceiling_counts_what_the_bot_spent_today_and_says_so_once(tmp_path, monkeypatch):
    from datetime import datetime

    from osmbot.game import wallet

    monkeypatch.setattr(wallet, "FILE", tmp_path / "carteira.json")
    monkeypatch.setattr(wallet, "_pending", {})
    monkeypatch.setattr(wallet, "_warned", {})
    now = datetime(2026, 11, 13, 12, 0)
    wallet.FILE.write_text('{"dia": "2026-11-13", "totais": {"amigáveis": -40, "vídeos da loja": 80, "fora do bot": -90}}', encoding="utf-8")
    wallet.note("treinos acabados", -10)  # not in the totals yet
    assert wallet.spent_today(now) == 50  # the videos and what was done outside the bot are not the bot's spending
    lines = []
    assert not wallet.cap_reached(10, 60, lines.append, now) and not wallet.cap_reached(10, None, lines.append, now)
    assert wallet.cap_reached(11, 60, lines.append, now) and wallet.cap_reached(11, 60, lines.append, now)
    assert len(lines) == 1 and "60" in lines[0]  # once a day
    assert wallet.spent_today(datetime(2026, 11, 14)) == 10  # a new day: only the pending spending


def test_with_videos_off_the_bot_watches_none(monkeypatch):
    from osmbot.game import loop

    set_pref("conta", {"videos": False})
    monkeypatch.setattr(loop, "_shop_ads", lambda dry_run: (_ for _ in ()).throw(AssertionError("watched a video")))
    assert loop._all_ads(False) == 0
