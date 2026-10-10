import os

import pytest

pytest.importorskip("PySide6.QtWidgets")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

NOW_SNAPSHOT = {
    "coins": 2586,
    "clubs": [{"name": name, "ranking": 1, "league": "Liga", "match": None, "slots": (3, 4), "money": (1_000_000, 0),
               "stadium": {"parts": [("Treinos", 3, 3, None)], "until": None},
               "trainings": [{"id": 1, "name": "Jogador 1", "pos": "ATA", "finish": 0, "claimed": False}], "tired": []}
              for name in ("Clube A", "Clube B")],
    "ads": {"shop": {"open": True, "reopen": None}},
}


@pytest.fixture
def window(monkeypatch, tmp_path):
    from osmbot.game import browser
    from osmbot.gui import window as module

    monkeypatch.setattr(browser, "STATE_FILE", tmp_path / "no-session.json")  # never reads the real game
    app = QApplication.instance() or QApplication([])
    win = module.MainWindow(app)
    yield win
    win.quitting = True
    win.tray.hide()
    win.close()


def test_it_opens_small_on_the_start_screen_and_asks_for_a_login_first(window):
    from osmbot.gui.window import LAUNCHER_SIZE, START

    assert window.pages.currentIndex() == START and window.size() == LAUNCHER_SIZE
    assert not window.menuBar().isVisible() and not window.open_button.isEnabled()  # no session yet
    assert "Login" in window.session_label.text() and window.login_button.isEnabled()


def test_abrir_shows_loading_then_grows_to_the_board_when_the_game_is_read(window):
    from osmbot.gui.window import BOARD, LOADING

    window.go(LOADING)
    window.on_board({"snapshot": None, "status": "A TRABALHAR", "notices": []})
    assert window.pages.currentIndex() == LOADING  # nothing read yet: still loading
    window.on_board({"snapshot": NOW_SNAPSHOT, "status": "A TRABALHAR", "notices": [("09:26:15", "Erro", "Loja: erro")]})
    assert window.pages.currentIndex() == BOARD and window.width() >= 1000
    assert [p.name.text() for p in window.panels] == ["Clube A", "Clube B"]
    assert window.panels[0].ring_cells[0][1].text == "pronto" and window.panels[0].ring_cells[0][2].text() == "Jogador 1"
    assert window.coins.text() == "2 586"
    assert window.notices_window.table.rowCount() == 1 and window.notices_action.text() == "Avisos e erros (1)"


def test_closing_hides_the_window_only_while_the_bot_works(window):
    import threading

    hold = threading.Event()
    window.worker = threading.Thread(target=hold.wait, daemon=True)
    window.worker.start()
    window.show()
    window.close()
    assert not window.isVisible() and not window.quitting
    hold.set()
    window.worker.join()


def test_four_clubs_go_one_per_row_and_the_logo_colour_is_its_strongest_colour(window):
    from PySide6.QtGui import QColor, QImage

    from osmbot.gui.window import BOARD, LOADING, logo_colour

    window.go(LOADING)
    window.on_board({"snapshot": {**NOW_SNAPSHOT, "clubs": NOW_SNAPSHOT["clubs"] * 2}, "status": "A TRABALHAR", "notices": []})
    assert window.pages.currentIndex() == BOARD and len(window.panels) == 4
    assert [window.clubs_column.indexOf(p) for p in window.panels] == [0, 1, 2, 3]  # one per row (D-030)
    image = QImage(20, 20, QImage.Format_ARGB32)
    image.fill(QColor("#ffffff"))
    for x in range(10):
        for y in range(20):
            image.setPixelColor(x, y, QColor("#1a8a3a"))
    assert QColor(logo_colour(image)).hue() in range(120, 150)


def test_atualizar_comes_first_in_ver_and_works_while_the_bot_works(window, monkeypatch, tmp_path):
    import threading

    from osmbot.game import browser

    view = next(menu.menu() for menu in window.menuBar().actions() if menu.text() == "Ver")
    names = [action.text() for action in view.actions() if not action.isSeparator()]
    assert names[0] == "Atualizar" and len(names) == 4
    session = tmp_path / "session.json"
    session.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(browser, "STATE_FILE", session)
    hold = threading.Event()
    window.worker = threading.Thread(target=hold.wait, daemon=True)
    window.worker.start()
    try:
        window.refresh_state()
        assert window.reload_action.isEnabled()
        window.reading = True  # one reading at a time
        window.refresh_state()
        assert not window.reload_action.isEnabled()
    finally:
        hold.set()


def test_the_board_always_shows_the_newest_reading_whoever_made_it(window):
    from osmbot.gui.window import BOARD

    window.go(BOARD)
    old, new = {**NOW_SNAPSHOT, "read_at": 100, "coins": 1}, {**NOW_SNAPSHOT, "read_at": 200, "coins": 2}
    window.reading = True
    window.on_read({"snapshot": new})  # the window's own reading, every 3 min
    assert not window.reading
    window.on_board({"snapshot": old, "status": "ATIVO", "notices": []})  # the bot still shows its older one
    assert window.payload["snapshot"]["coins"] == 2 and window.payload["status"] == "ATIVO"
    window.on_board({"snapshot": {**old, "read_at": 300}, "status": "ATIVO", "notices": []})
    assert window.payload["snapshot"]["read_at"] == 300
    window.on_read({"snapshot": new})  # a reading that started before the bot's: kept out
    assert window.payload["snapshot"]["read_at"] == 300


def test_it_reads_the_game_every_3_minutes_only_on_the_board(window, monkeypatch):
    from osmbot.gui.window import BOARD, READ_EVERY, START

    reads = []
    monkeypatch.setattr(window, "read_game", lambda: reads.append(1))
    assert window.reader.interval() == READ_EVERY * 1000 == 180_000
    window.go(START)
    window.auto_read()
    window.go(BOARD)
    window.auto_read()
    assert reads == [1]


def test_the_stadium_rings_the_doctor_and_the_top_says_only_since_when_the_bot_works(window):
    import threading
    import time

    from osmbot.gui.window import ACCENT, BOARD

    now = time.time()
    club = {**NOW_SNAPSHOT["clubs"][0], "sales": [{"name": "Jogador 7", "price": 2_000_000}], "stadium": {"parts": [("Treinos", 3, 3, None), ("Campo", 1, 3, now + 9 * 3600)],
                                                    "until": now + 9 * 3600, "lengths": {"Campo": 18 * 3600}}}
    snapshot = {**NOW_SNAPSHOT, "clubs": [club], "ads": {"shop": {"open": True}}}
    hold = threading.Event()
    window.worker = threading.Thread(target=hold.wait, daemon=True)
    window.worker.start()
    try:
        window.go(BOARD)
        window.on_board({"snapshot": snapshot, "status": "A TRABALHAR", "notices": [],
                         "doing": {"text": "vídeo da loja 8/9", "kind": "shop", "count": 8}, "stats": {"start": now}})
        still, going = window.panels[0].stadium_cells[:2]
        assert going.ring.text == "1/3" and going.lines[0].text() == "Campo" and len(going.lines) == 1  # only the name
        assert going.ring.hover[0] in ("9h00", "8h59")  # the time left in the middle on hover (owner, 2026-10-10)
        assert abs(going.ring.done - 0.5) < 0.01 and going.ring.arc == ACCENT  # the club's colour once its logo is in
        assert still.ring.text == "3/3" and still.ring.hover[0] == "MAX"
        assert not window.panels[0].sale.isHidden() and "Jogador 7" in window.panels[0].sale.toolTip()  # the sale arrow
        doctor, lawyer = window.panels[0].care_cells
        assert doctor.ring.picture is not None and doctor.ring.hover is None and doctor.under.isHidden()  # nobody: washed out
        assert doctor.toolTip() == "Médico"
        assert window.timeline.now_text == "vídeo da loja 8/9"
        assert window.state_text.text().startswith("A trabalhar desde")
    finally:
        hold.set()


def test_the_timeline_has_now_in_the_middle_the_next_things_above_and_what_the_bot_did_below(window):
    import threading
    import time

    from osmbot.gui.window import BOARD

    hold = threading.Event()
    window.worker = threading.Thread(target=hold.wait, daemon=True)
    window.worker.start()
    try:
        window.go(BOARD)
        history = [{"kind": "shop", "title": "Vídeos da loja", "ts": time.time() - 60, "count": 3}]
        window.on_board({"snapshot": NOW_SNAPSHOT, "status": "A TRABALHAR", "notices": [],
                         "doing": {"text": "à espera"}, "history": history})
        assert window.timeline.now_text == "à espera"
        assert window.timeline.past[0]["title"] == "Vídeos da loja ×3"
        due = [(e["title"], e["left"]) for e in window.timeline.future if e["left"] == "já"]
        assert ("Vídeos da loja", "já") in due and ("Recolher treino Jogador 1", "já") in due
        window.timeline.grab()  # it draws without errors
        assert window.panels[0].grab()
    finally:
        hold.set()


def test_idioma_language_switches_the_window_at_once(window):
    from osmbot import i18n
    from osmbot.gui.window import BOARD

    try:
        window.go(BOARD)
        window.on_board({"snapshot": NOW_SNAPSHOT, "status": "A TRABALHAR", "notices": [("09:26:15", "Erro", "Loja: janela saltada")]})
        menus = [action.text() for action in window.menuBar().actions()]
        assert "Idioma / Language" in menus and "Ver" in menus
        window.choose_language("en")
        assert [action.text() for action in window.menuBar().actions()] == ["Bot", "View", "Idioma / Language", "Help"]
        assert window.language_actions["en"].isChecked() and window.pages.currentIndex() == BOARD
        assert window.notices_window.table.item(0, 1).text() == "Error"
        assert window.notices_window.table.item(0, 2).text() == "Shop: window skipped"
        assert window.panels[0].prep_title.text().startswith("PRE-MATCH") or window.panels[0].prep_title.text() == "PRE-MATCH"
    finally:
        i18n.set_language("pt", save=False)
