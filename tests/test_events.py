import json
from datetime import date, datetime

from osmbot.events.calendar import active_changes, months_needed, parse_schedule, span_of, upcoming

POST = """<p>OSM Events schedule: October 2026</p>
<p>03 - 04 October: Training Camp Mania</p><p>Higher Training Progression (when claiming) with every Training and Friendly</p>
<p>10 - 11 October: Transfer Madness</p><p>Higher sale chance and more players added by engine on each transfer round</p>
<p>Possible to put up to 6 players on transfer list</p>
<p>14 October: Super Staff</p><p>Faster Analyst: 15min to bring a report</p>
<p>31 October - 01 November: Extreme Training</p><p>Extreme Training Progression with every Training and Friendly</p>
<p>Note: This schedule is subject to change.</p>"""


def test_the_staff_post_becomes_a_calendar():
    calendar = parse_schedule(POST)
    assert calendar["mes"] == "2026-10"
    assert [(e["inicio"], e["fim"], e["nome"]) for e in calendar["eventos"]] == [
        ("2026-10-03", "2026-10-04", "Training Camp Mania"), ("2026-10-10", "2026-10-11", "Transfer Madness"),
        ("2026-10-14", "2026-10-14", "Super Staff"), ("2026-10-31", "2026-11-01", "Extreme Training")]
    madness = calendar["eventos"][1]
    assert madness["tags"] == ["transferencias"] and len(madness["efeitos"]) == 2
    assert calendar["eventos"][3]["efeitos"] == ["Extreme Training Progression with every Training and Friendly"]  # not the note
    assert parse_schedule("<p>Some other post</p>") is None


def test_what_is_on_now_and_this_week():
    calendar = parse_schedule(POST)
    now = datetime(2026, 10, 11, 12).timestamp()
    names = [e["nome"] for e in upcoming([calendar], now)]
    assert names == ["Transfer Madness", "Super Staff"]  # going on, and within 7 days
    start, end = span_of(calendar["eventos"][2])
    assert start == datetime(2026, 10, 14).timestamp() and end == datetime(2026, 10, 15).timestamp()


def test_what_an_event_changed_in_the_settings():
    normal = [{"name": "TrainingSession", "value": 480}, {"name": "MaxPlayersOnTransferlist", "value": 4}]
    assert active_changes(normal) == []
    event = [{"name": "TrainingSession", "value": 120}, {"name": "MaxPlayersOnTransferlist", "value": 6}]
    assert active_changes(event) == ["treinos 120 min", "vagas de venda 6"]


def test_months_to_have():
    assert months_needed(date(2026, 10, 12)) == ["2026-10"]
    assert months_needed(date(2026, 12, 27)) == ["2026-12", "2027-01"]


def test_the_forum_is_read_only_when_a_month_is_missing_and_once_a_day(monkeypatch):
    from osmbot.game import events

    refresh = events.real["refresh"]
    reads, lines = [], []

    def read():
        reads.append(1)
        return POST

    refresh(log=lines.append, read=read, now=datetime(2026, 10, 12, 9))
    assert reads == [1] and lines[0].startswith("Calendário de eventos de 2026-10: 4 · Training Camp Mania (03–04)")
    refresh(log=lines.append, read=read, now=datetime(2026, 10, 12, 23))
    assert reads == [1]  # October is there
    saved = json.loads(events.FILE.read_text(encoding="utf-8"))
    assert list(saved["meses"]) == ["2026-10"] and saved["tentativa"] == "2026-10-12"
    assert [e["nome"] for e in events.calendar_events(datetime(2026, 10, 12, 9).timestamp())] == ["Super Staff"]


def test_a_failed_read_or_a_new_format_is_said_and_retried_tomorrow():
    from osmbot.game import events

    refresh = events.real["refresh"]
    lines = []

    def broken():
        raise TimeoutError

    refresh(log=lines.append, read=broken, now=datetime(2026, 10, 12, 9))
    refresh(log=lines.append, read=lambda: POST, now=datetime(2026, 10, 12, 10))  # same day: not again
    refresh(log=lines.append, read=lambda: "<p>new layout</p>", now=datetime(2026, 10, 13, 10))
    assert lines == ["Calendário de eventos: não consegui ler o fórum (TimeoutError); tento amanhã",
                     "! Calendário de eventos: o post do fórum mudou de formato; não percebi as datas"]


def test_an_event_in_the_settings_is_logged_when_it_starts_and_ends():
    from osmbot.game import events

    check = events.real["check_league"]

    class Client:
        settings = [{"name": "SpyInstructionTimer", "value": 15}]

        def get(self, path):
            return (200, self.settings) if path.endswith("gamesettings") else (404, "")

    client, lines = Client(), []
    assert check(client, 9, "Liga", log=lines.append, now=1000.0) == ["analista 15 min"]
    assert check(client, 9, "Liga", log=lines.append, now=1600.0) == ["analista 15 min"]  # within the hour: not read
    client.settings = [{"name": "SpyInstructionTimer", "value": 60}]
    assert check(client, 9, "Liga", log=lines.append, now=5000.0) == []
    when = f"{datetime.fromtimestamp(1000):%H:%M} e {datetime.fromtimestamp(5000):%H:%M}"  # the previous reading and this one
    assert lines == ["Evento no jogo (Liga): analista 15 min", f"Evento no jogo (Liga): acabou, tudo normal (mudou entre {when})"]


def test_the_settings_are_read_every_10_min_early_in_the_morning():
    from osmbot.game import events

    day = datetime(2026, 10, 17)
    assert [events.check_every(day.replace(hour=h, minute=m).timestamp()) for h, m in ((5, 29), (5, 30), (6, 59), (7, 0))]         == [3600, 600, 600, 3600]


def test_the_timeline_shows_the_event_going_on_and_the_next_ones():
    from osmbot.board.timeline import future_view

    calendar = parse_schedule(POST)
    now = datetime(2026, 10, 11, 12).timestamp()
    rows = future_view({"events": upcoming([calendar], now)}, now)
    assert [(r["title"], r["sub"]) for r in rows] == [("Evento: Transfer Madness", "10/10–11/10"),
                                                     ("Evento: Super Staff", "14/10")]
    assert rows[0]["left"] == "já" and rows[1]["ts"] == datetime(2026, 10, 14).timestamp()


def test_event_lines_in_english():
    from osmbot.i18n import set_language, tr

    set_language("en", save=False)
    try:
        assert tr("Evento: Transfer Madness") == "Event: Transfer Madness"
        assert tr("Evento no jogo (Spain): treinos 120 min, vagas de venda 6") == \
            "Event in the game (Spain): trainings 120 min, transfer list places 6"
    finally:
        set_language("pt", save=False)


def test_on_a_training_event_day_the_bot_looks_for_it_from_0530_every_10_minutes_until_it_shows():
    from datetime import datetime

    from osmbot.game.events import training_event_wake

    day = datetime(2026, 10, 17).timestamp()
    event = {"tags": ["treinos", "lendas"], "start": day}
    at = lambda h, m=0: day + h * 3600 + m * 60
    assert training_event_wake([event], [], at(-2)) == at(5, 30)  # the evening before: wake at 05:30
    assert training_event_wake([event], [], at(5, 40)) == at(5, 50)  # in the window: every 10 min
    assert training_event_wake([event], [["treinos 120 min"]], at(6, 10)) is None  # it began: nothing to wait for
    assert training_event_wake([event], [], at(7, 30)) is None  # after 07:00
    assert training_event_wake([{"tags": ["olheiro"], "start": day}], [], at(5, 40)) is None  # not a training event
