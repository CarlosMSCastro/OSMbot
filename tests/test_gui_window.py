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
    assert "pronto" in window.panels[0].training_rows[0][2].text()
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


def test_four_clubs_go_in_a_2_by_2_grid_and_the_logo_colour_is_its_strongest_colour(window):
    from PySide6.QtGui import QColor, QImage

    from osmbot.gui.window import BOARD, LOADING, logo_colour

    window.go(LOADING)
    window.on_board({"snapshot": {**NOW_SNAPSHOT, "clubs": NOW_SNAPSHOT["clubs"] * 2}, "status": "A TRABALHAR", "notices": []})
    assert window.pages.currentIndex() == BOARD and len(window.panels) == 4
    places = [window.clubs_grid.getItemPosition(window.clubs_grid.indexOf(p))[:2] for p in window.panels]
    assert places == [(0, 0), (0, 1), (1, 0), (1, 1)]
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


def test_a_part_going_up_shows_its_bar_and_the_status_bar_says_now_and_next(window):
    import threading
    import time

    from osmbot.gui.window import BOARD

    now = time.time()
    club = {**NOW_SNAPSHOT["clubs"][0], "stadium": {"parts": [("Treinos", 3, 3, None), ("Campo", 1, 3, now + 9 * 3600)],
                                                    "until": now + 9 * 3600, "lengths": {"Campo": 18 * 3600}}}
    snapshot = {**NOW_SNAPSHOT, "clubs": [club], "ads": {"shop": {"open": True}}}
    hold = threading.Event()
    window.worker = threading.Thread(target=hold.wait, daemon=True)
    window.worker.start()
    try:
        window.go(BOARD)
        window.on_board({"snapshot": snapshot, "status": "A TRABALHAR", "notices": [],
                         "doing": {"text": "vídeo da loja 8/9", "kind": "shop", "count": 8}, "stats": {"start": now}})
        name, bar, left = window.panels[0].upgrade_rows[0]
        assert name.text() == "Campo 1/3" and left.text() in ("9h00", "8h59") and abs(bar.done - 0.5) < 0.01
        assert window.next_label.text() == "· agora: vídeo da loja 8/9 · a seguir: vídeo da loja 9/9"
    finally:
        hold.set()
