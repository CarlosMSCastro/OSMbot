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
