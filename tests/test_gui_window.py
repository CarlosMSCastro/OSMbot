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


def test_the_window_opens_stopped_and_draws_the_clubs_side_by_side(window):
    assert window.start_action.isEnabled() and not window.stop_action.isEnabled()
    assert "sem sessão" in window.state_text.text() and "Login" in window.loading.text()
    window.on_board({"snapshot": NOW_SNAPSHOT, "status": "PARADO", "notices": [("09:26:15", "Erro", "Loja: erro")]})
    assert [p.title() for p in window.panels] == ["Clube A  —  1.º · Liga", "Clube B  —  1.º · Liga"]
    assert window.panels[0].trainings.item(0, 2).text() == "pronto"
    assert window.coins.text() == "2 586" and window.notices.rowCount() == 1
    assert "Iniciar" in window.next_label.text()


def test_closing_the_window_only_hides_it(window):
    window.show()
    window.close()
    assert not window.isVisible() and not window.quitting
