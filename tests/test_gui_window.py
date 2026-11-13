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
    monkeypatch.setattr("osmbot.logs.CONFIG_FILE", tmp_path / "config.json")  # never touches the real choices
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
    assert names[0] == "Atualizar" and names[1] == "Dados" and len(names) == 5  # Ver → Dados (2026-11-06); the pin and the language went to Definições (2026-11-13)
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


def test_hidden_it_reads_only_every_15_minutes(window, monkeypatch):
    from osmbot.gui import window as module

    reads, now = [], {"t": 10_000.0}
    monkeypatch.setattr(window, "read_game", lambda: reads.append(now["t"]))
    monkeypatch.setattr(module.time, "time", lambda: now["t"])
    window.go(module.BOARD)
    window.hide()
    for _ in range(6):  # 6 ticks of 3 minutes = 18 minutes
        window.auto_read()
        now["t"] += module.READ_EVERY
    assert reads == [10_000.0, 10_000.0 + 5 * module.READ_EVERY]


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
        assert menus == ["Bot", "Ver", "Definições"]  # Ajuda merged into Ver, the language and "Sobre" into Definições
        window.choose_language("en")
        assert [action.text() for action in window.menuBar().actions()] == ["Bot", "View", "Settings"]
        settings_menu = next(a.menu() for a in window.menuBar().actions() if a.text() == "Settings")
        assert "Idioma / Language" in [a.text() for a in settings_menu.actions()]
        assert window.language_actions["en"].isChecked() and window.pages.currentIndex() == BOARD
        assert window.notices_window.table.item(0, 1).text() == "Error"
        assert window.notices_window.table.item(0, 2).text() == "Shop: window skipped"
        assert window.panels[0].prep_title.text().startswith("PRE-MATCH") or window.panels[0].prep_title.text() == "PRE-MATCH"
    finally:
        i18n.set_language("pt", save=False)


def test_hovers_have_the_first_line_as_a_title_and_one_line_stays_plain():
    from osmbot.gui.window import tip_html, tip_text

    assert tip_text("Só uma linha") == "Só uma linha"
    html = tip_text("Força 108\nValor do plantel: 998 M\n\nMédia: 29 M")
    assert html.startswith("<div") and "Força 108</div>" in html and "Valor do plantel: 998 M" in html and "<br><br>" in html
    assert "Fora da regra</div>" in tip_html([(None, "Akanni 51 entra antes de Ndicka 107", None)], "Fora da regra")


def test_a_hovers_title_is_on_its_own_line_as_qt_draws_it():
    from PySide6.QtGui import QTextDocument

    from osmbot.gui.window import tip_html, tip_text

    QApplication.instance() or QApplication([])

    def drawn(html: str) -> list[str]:
        document = QTextDocument()
        document.setHtml(html)
        return document.toPlainText().split("\n")

    # owner, 2026-11-03: "AdvogadoAlexander-Arnold" in the lawyer's ring
    assert drawn(tip_text("Advogado\nNome\n1 jogo · não dá")) == ["Advogado", "Nome", "1 jogo · não dá"]
    assert drawn(tip_text("Vendas\n\nX")) == ["Vendas", "", "X"]
    assert drawn(tip_html([(None, "a", None)], "Título"))[:2] == ["Título", "a"]


def test_the_right_column_opens_from_the_tab_over_the_clubs_and_can_be_pinned(window):
    from osmbot.gui.window import BOARD
    from osmbot.i18n import get_pref

    window.go(BOARD)
    assert window.side_tab.isVisibleTo(window.board_page) and not window.side_panel.isVisibleTo(window.board_page)
    window._open_side()
    assert window.side_panel.isVisibleTo(window.board_page) and window.side_timer.isActive()
    window._check_side()  # the mouse is not there
    assert not window.side_panel.isVisibleTo(window.board_page) and not window.side_timer.isActive()
    window.pin_side(True)
    assert window.side_panel.isVisibleTo(window.board_page) and not window.side_tab.isVisibleTo(window.board_page)
    assert get_pref("side_pinned") is True
    window.pin_side(False)
    assert not window.side_panel.isVisibleTo(window.board_page)


def test_the_board_opens_maximized_unless_it_was_left_otherwise(window):
    from osmbot.gui.window import BOARD, START
    from osmbot.i18n import set_pref

    window.go(BOARD)
    assert window.windowState() & __import__("PySide6.QtCore").QtCore.Qt.WindowMaximized
    window.go(START)
    set_pref("maximized", False)
    window.go(BOARD)
    assert not window.windowState() & __import__("PySide6.QtCore").QtCore.Qt.WindowMaximized


def test_the_data_window_reads_the_logs_and_follows_the_filters(window, monkeypatch, tmp_path):
    import json

    from osmbot.gui import data_window

    folder = tmp_path / "logs" / "PC" / "jogos"
    folder.mkdir(parents=True)
    line = lambda n, result, trap: {
        "jogo": f"77_{n}_5", "t": 1000 + n, "tipo": "liga", "semana": 5, "resultado": result, "campo_neutro": False,
        "casa": {"id": 1, "nome": "Clube A", "meu": True, "media_11": 80}, "fora": {"id": 2, "nome": "Clube B", "meu": False},
        "estatisticas": {"casa": {"forca": 120, "formacao": "433A"}, "fora": {"forca": 100, "formacao": "442A"}},
        "tatica": {"overallMatchTactics": 2, "style": 2, "marking": False, "offsideTrap": trap}}
    lines = [line(i, "2-0" if i % 2 else "1-1", bool(i % 2)) for i in range(6)]
    (folder / "2026-11.jsonl").write_text("\n".join(json.dumps(x) for x in lines), encoding="utf-8")
    monkeypatch.setattr("osmbot.logs.repo_folder", lambda: tmp_path)
    data = data_window.DataWindow()
    assert len(data.kept) == 6  # the owner's clubs by default: one side of 6 matches
    assert "3 de 6" in data.headline.text()
    data.set_filter("own", "armadilha", "Sim")
    data.refresh()
    assert len(data.kept) == 3 and data.matches.rowCount() == 3 and "3 de 3" in data.headline.text()
    assert data.chips[-1].property("on") == "true"
    data.set_filter("own", "quem", "Todos os clubes")
    data.refresh()
    assert len(data.kept) == 3  # still the trap: only the owner's side has one
    data.clear()
    assert len(data.kept) == 6 and data.chips[0].property("on") == "false"
    data.close()


def test_the_end_of_the_season_is_built_once_not_every_second(window):
    from osmbot.gui.window import ClubCard, QLabel

    end = {"rows": [{"icon": "league", "title": "Campeão da liga", "note": "1.º · 111 pontos"}],
           "ticket": {"title": "Taça dos Vencedores", "expires": "expira a 13/11 às 20:09"}}
    card = ClubCard()
    card.season_end.show_end(end)
    first = card.season_end.findChildren(QLabel)
    card.season_end.show_end(dict(end))  # the next second: the same content
    assert card.season_end.findChildren(QLabel) == first and len(first) == 8
    card.season_end.show_end(None)
    assert card.season_end.isHidden()


def test_pinning_the_right_column_grows_the_window_and_unpinning_shrinks_it_back(window, monkeypatch):
    from PySide6.QtCore import QRect

    from osmbot.gui.window import BOARD, SideTab

    class Screen:
        def availableGeometry(self):
            return QRect(0, 0, 4000, 3000)

    monkeypatch.setattr(window, "screen", lambda: Screen())
    window.go(BOARD)
    window.showNormal()
    window.pin_side(False)
    window.resize(1500, 800)
    before = window.width()
    window.pin_side(True)
    assert window.width() == before + window.SIDE - SideTab.WIDTH  # the clubs keep their width
    window.pin_side(False)
    assert window.width() == before


def test_a_club_turned_off_has_its_card_grey_and_it_comes_back_with_the_switch(window):
    from osmbot import settings
    from osmbot.gui.window import BOARD
    from osmbot.i18n import set_pref

    window.go(BOARD)
    window.on_board({"snapshot": NOW_SNAPSHOT, "status": "PARADO", "notices": []})
    card = window.panels[0]
    name = card.club_name
    assert card.graphicsEffect() is None and not card.name.text().endswith("desativado")
    card.key = "5_9"
    set_pref("clubes", settings.with_club({}, "5_9", active=False))
    window.refresh_off()
    assert card.graphicsEffect() is not None and card.name.text() == f"{name}  ·  desativado"
    set_pref("clubes", settings.with_club(settings.load(), "5_9", active=True))
    window.refresh_off()
    assert card.graphicsEffect() is None and card.name.text() == name
