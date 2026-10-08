"""The OSMbot window (D-024): a Windows program around the same bot loop as the console.

It opens on the board with the bot stopped (reading the game is read-only); "Iniciar" runs ``run_active`` in a
background thread that sends the board here; "Parar" asks it to stop at its next pause. Closing the window (X)
only hides it: the bot goes on, and the tray icon (the logo with a green dot when working, grey when stopped)
opens it again or quits. No Windows notifications (owner, 2026-10-08).
"""
from __future__ import annotations

import ctypes
import os
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QLockFile, QObject, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPainter, QPalette, QPen, QPixmap
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QGridLayout, QGroupBox, QHBoxLayout, QHeaderView,
                               QLabel, QMainWindow, QMenu, QMessageBox, QSizePolicy, QSplitter, QStatusBar, QStyle,
                               QSystemTrayIcon, QTableWidget, QTableWidgetItem, QToolBar, QVBoxLayout, QWidget)

from osmbot import __version__
from osmbot.gui.view import BLUE, GREEN, GREY, RED, YELLOW, board_view

COLOURS = {GREEN: "#4caf50", BLUE: "#3d9be0", YELLOW: "#d9a520", GREY: "#8c8c8c", RED: "#e0524a", None: "#dcdcdc"}
TRAY_DOT = {True: "#9be22d", False: "#9a9a9a"}  # lime with a white ring: readable on the green logo at 16 px
ROW_HEIGHT, HEADER_HEIGHT = 22, 24
STYLE = (
    "QGroupBox { font-weight: bold; border: 1px solid #3a3a3a; border-radius: 3px; margin-top: 8px; padding-top: 6px; }"
    "QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }"
    "QGroupBox QLabel, QGroupBox QTableWidget { font-weight: normal; }"
    "QHeaderView::section { background: #262626; color: #a0a0a0; border: none; border-bottom: 1px solid #3a3a3a; padding: 3px 6px; }"
    "QTableWidget { border: 1px solid #333333; }"
    "QToolBar { border-bottom: 1px solid #333333; spacing: 4px; padding: 3px; }"
    "QStatusBar { border-top: 1px solid #333333; color: #a0a0a0; }"
)


def logo_path() -> Path:
    """The logo: next to OSMbot.exe in the portable/installed bot, in tools/assets when run from the repo."""
    here = Path(sys.executable).parent / "osmbot.ico"
    if here.exists():
        return here
    return Path(__file__).resolve().parents[3] / "tools" / "assets" / "osmbot.ico"


def dark_palette() -> QPalette:
    palette = QPalette()
    for role, colour in ((QPalette.Window, "#202020"), (QPalette.WindowText, "#dcdcdc"), (QPalette.Base, "#191919"),
                         (QPalette.AlternateBase, "#1e1e1e"), (QPalette.Text, "#dcdcdc"), (QPalette.Button, "#2b2b2b"),
                         (QPalette.ButtonText, "#dcdcdc"), (QPalette.Highlight, "#2f5f8f"), (QPalette.HighlightedText, "#ffffff"),
                         (QPalette.ToolTipBase, "#2b2b2b"), (QPalette.ToolTipText, "#dcdcdc"), (QPalette.Mid, "#3a3a3a"),
                         (QPalette.Dark, "#151515"), (QPalette.Light, "#3c3c3c"), (QPalette.PlaceholderText, "#8c8c8c")):
        palette.setColor(role, QColor(colour))
    for role in (QPalette.ButtonText, QPalette.WindowText, QPalette.Text):
        palette.setColor(QPalette.Disabled, role, QColor("#666666"))
    return palette


def dark_title_bar(widget: QWidget) -> None:
    """Dark title bar on Windows 10/11 (DWM attribute 20; 19 on older Windows 10)."""
    if sys.platform != "win32":
        return
    try:
        value = ctypes.c_int(1)
        for attribute in (20, 19):
            ctypes.windll.dwmapi.DwmSetWindowAttribute(int(widget.winId()), attribute, ctypes.byref(value), ctypes.sizeof(value))
    except Exception:
        pass


def hide_own_console() -> None:
    """OSMbot.exe is a console program: hide its black window when it was opened by a double click (the console is
    ours alone), never when it was started from a terminal the owner is using."""
    if sys.platform != "win32":
        return
    try:
        kernel = ctypes.windll.kernel32
        console = kernel.GetConsoleWindow()
        processes = (ctypes.c_uint32 * 4)()
        if console and kernel.GetConsoleProcessList(processes, 4) <= 1:
            ctypes.windll.user32.ShowWindow(console, 0)
    except Exception:
        pass


def tray_icon(logo: QIcon, working: bool) -> QIcon:
    """The logo with a dot in the corner: green while the bot works, grey while it is stopped."""
    icon = QIcon()
    for size in (16, 20, 24, 32, 48, 64):
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.drawPixmap(0, 0, logo.pixmap(size, size))
        dot = size * 0.5
        painter.setPen(QPen(QColor("#ffffff"), max(1.0, size / 14)))
        painter.setBrush(QColor(TRAY_DOT[working]))
        painter.drawEllipse(QRectF(size - dot - 0.5, size - dot - 0.5, dot, dot))
        painter.end()
        icon.addPixmap(pixmap)
    return icon


def coloured(text: str, colour: str | None = None, bold: bool = False) -> QLabel:
    label = QLabel(text)
    paint(label, colour, bold)
    return label


def paint(label: QLabel, colour: str | None, bold: bool = False) -> None:
    label.setStyleSheet(f"color:{COLOURS.get(colour, COLOURS[None])};" + ("font-weight:bold;" if bold else ""))


class Bar(QWidget):
    """A thin bar in three colours: green = time gone by, blue = the part a video skipped, grey = still to go."""

    def __init__(self, width: int | None = None):
        super().__init__()
        self.done, self.skipped = 0.0, 0.0
        self.setFixedHeight(10)
        self.hide()  # until there is something to show
        if width:
            self.setFixedWidth(width)

    def sizeHint(self) -> QSize:
        return QSize(120, 10)

    def set(self, done: float | None, skipped: float = 0.0) -> None:
        self.setVisible(done is not None)
        self.done, self.skipped = done or 0.0, min(skipped, done or 0.0)
        self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        box = QRectF(self.rect()).adjusted(0, 0, -1, -1)
        painter.fillRect(box, QColor("#2e2e2e"))
        green = box.width() * (self.done - self.skipped)
        painter.fillRect(QRectF(box.x(), box.y(), green, box.height()), QColor(COLOURS[GREEN]))
        painter.fillRect(QRectF(box.x() + green, box.y(), box.width() * self.skipped, box.height()), QColor(COLOURS[BLUE]))
        painter.setPen(QColor("#444444"))
        painter.drawRect(box)


def make_table(headers: list[str], widths: list[int]) -> QTableWidget:
    table = QTableWidget(0, len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.verticalHeader().hide()
    table.verticalHeader().setDefaultSectionSize(ROW_HEIGHT)
    table.horizontalHeader().setFixedHeight(HEADER_HEIGHT)
    table.horizontalHeader().setHighlightSections(False)
    table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    table.horizontalHeader().setStretchLastSection(True)
    table.setAlternatingRowColors(True)
    table.setShowGrid(False)
    table.setFocusPolicy(Qt.NoFocus)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setSelectionMode(QAbstractItemView.NoSelection)
    for column, width in enumerate(widths):
        table.setColumnWidth(column, width)
    return table


def fit_rows(table: QTableWidget, rows: int) -> None:
    """Small tables show all their rows, without scroll bars."""
    if table.rowCount() != rows:
        table.setRowCount(rows)
    table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    table.setFixedHeight(HEADER_HEIGHT + ROW_HEIGHT * rows + 4)


def set_cell(table: QTableWidget, row: int, column: int, text: str, colour: str | None = None) -> None:
    item = table.item(row, column)
    if item is None:
        item = QTableWidgetItem()
        table.setItem(row, column, item)
    item.setText(text)
    item.setForeground(QColor(COLOURS.get(colour, COLOURS[None])))


def set_bar(table: QTableWidget, row: int, column: int, done: float | None, skipped: float = 0.0) -> None:
    holder = table.cellWidget(row, column)
    if holder is None:
        holder = QWidget()
        layout = QHBoxLayout(holder)
        layout.setContentsMargins(6, 0, 6, 0)
        layout.addWidget(Bar())
        table.setCellWidget(row, column, holder)
    holder.findChild(Bar).set(done, skipped)


class ClubPanel(QGroupBox):
    """One club: the five fields, the stadium table, the trainings table and the tired starters."""

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(3)
        self.fields = []
        for index in range(5):
            row, column = divmod(index, 2)
            name, value = coloured("", GREY), coloured("")
            grid.addWidget(name, row, column * 2)
            grid.addWidget(value, row, column * 2 + 1)
            self.fields.append((name, value))
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)
        layout.addLayout(grid)
        self.stadium = make_table(["Estádio", "Nível", "Estado", ""], [90, 50, 110])
        self.trainings = make_table(["Jogador", "Pos.", "Falta", "Progresso"], [110, 45, 60])
        layout.addWidget(self.stadium)
        layout.addWidget(self.trainings)
        self.tired = coloured("", YELLOW)
        layout.addWidget(self.tired)
        layout.addStretch()

    def show_club(self, club: dict) -> None:
        self.setTitle(club["title"])
        for index, (name, value) in enumerate(self.fields):
            if index < len(club["fields"]):
                label, text, colour = club["fields"][index]
                name.setText(label + ":")
                value.setText(text)
                paint(value, colour)
            else:
                name.setText("")
                value.setText("")
        fit_rows(self.stadium, len(club["stadium"]))
        for row, (name, level, state, colour, done) in enumerate(club["stadium"]):
            set_cell(self.stadium, row, 0, name)
            set_cell(self.stadium, row, 1, level)
            set_cell(self.stadium, row, 2, state, colour)
            set_bar(self.stadium, row, 3, done)
        fit_rows(self.trainings, len(club["trainings"]))
        for row, (name, pos, left, colour, done, skipped) in enumerate(club["trainings"]):
            set_cell(self.trainings, row, 0, name)
            set_cell(self.trainings, row, 1, pos, GREY)
            set_cell(self.trainings, row, 2, left, colour)
            set_bar(self.trainings, row, 3, done, skipped)
        self.tired.setText(f"⚠ Cansados: {club['tired']}" if club["tired"] else "")


class Bridge(QObject):
    """Carries what the background threads read to the window (Qt widgets live in the main thread only)."""

    board = Signal(object)
    finished = Signal(str)
    read = Signal(object)
    login = Signal(str)


class MainWindow(QMainWindow):
    def __init__(self, app: QApplication):
        super().__init__()
        from osmbot.logs import machine

        self.app = app
        self.bridge = Bridge()
        self.bridge.board.connect(self.on_board)
        self.bridge.finished.connect(self.on_finished)
        self.bridge.read.connect(self.on_read)
        self.bridge.login.connect(self.on_login)
        self.payload: dict = {}
        self.worker: threading.Thread | None = None
        self.busy = ""  # "login" / "a ler" while a helper thread runs
        self.quitting = False
        self.started_at: float | None = None
        self.message = ""
        self.logo = QIcon(str(logo_path()))
        self.setWindowTitle(f"OSMbot {__version__} — {machine()}")
        self.setWindowIcon(self.logo)
        self.resize(1060, 680)
        self._build_actions()
        self._build_body()
        self._build_tray()
        self.clock = QTimer(self)
        self.clock.timeout.connect(self.render)
        self.clock.start(1000)
        self.refresh_state()
        self.read_game()

    # ---- building -------------------------------------------------------------------------------------------
    def _build_actions(self) -> None:
        style = self.style()
        self.start_action = QAction(style.standardIcon(QStyle.SP_MediaPlay), "Iniciar", self, triggered=self.start_bot)
        self.stop_action = QAction(style.standardIcon(QStyle.SP_MediaStop), "Parar", self, triggered=self.stop_bot)
        self.login_action = QAction(style.standardIcon(QStyle.SP_DialogApplyButton), "Login", self, triggered=self.do_login)
        self.logs_action = QAction(style.standardIcon(QStyle.SP_DirOpenIcon), "Pasta dos logs", self, triggered=self.open_logs)
        self.failures_action = QAction("Capturas das falhas", self, triggered=self.open_failures)
        self.reload_action = QAction("Atualizar quadro", self, triggered=self.read_game)
        self.quit_action = QAction("Sair", self, triggered=self.quit_app)
        about = QAction("Sobre o OSMbot", self, triggered=self.about)

        bot = self.menuBar().addMenu("Bot")
        for action in (self.start_action, self.stop_action, self.login_action):
            bot.addAction(action)
        bot.addSeparator()
        bot.addAction(self.quit_action)
        view = self.menuBar().addMenu("Ver")
        for action in (self.reload_action, self.logs_action, self.failures_action):
            view.addAction(action)
        self.menuBar().addMenu("Ajuda").addAction(about)

        bar = QToolBar()
        bar.setMovable(False)
        bar.setIconSize(QSize(16, 16))
        bar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        for action in (self.start_action, self.stop_action):
            bar.addAction(action)
        bar.addSeparator()
        bar.addAction(self.login_action)
        bar.addAction(self.logs_action)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        bar.addWidget(spacer)
        self.state_dot = coloured("●", GREY)
        self.state_text = QLabel()
        bar.addWidget(self.state_dot)
        bar.addWidget(self.state_text)
        bar.addWidget(QLabel("  "))
        self.addToolBar(bar)

    def _build_body(self) -> None:
        central = QWidget()
        outer = QVBoxLayout(central)
        outer.setContentsMargins(8, 8, 8, 6)
        top = QWidget()
        top_layout = QVBoxLayout(top)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(8)
        self.clubs_row = QHBoxLayout()
        self.clubs_row.setSpacing(8)
        self.panels: list[ClubPanel] = []
        self.loading = coloured("A ler o jogo…", GREY)
        self.loading.setAlignment(Qt.AlignCenter)
        self.clubs_row.addWidget(self.loading)
        top_layout.addLayout(self.clubs_row, 1)

        account = QGroupBox("Conta")
        grid = QGridLayout(account)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(4)
        self.coins = coloured("—", YELLOW, True)
        self.shop_bar, self.shop_text = Bar(110), coloured("—", GREY)
        self.daily = QLabel("—")
        self.videos_bar, self.videos_text = Bar(110), coloured("—")
        self.summary = QLabel("—")
        grid.addWidget(coloured("Boss coins:", GREY), 0, 0)
        grid.addWidget(self.coins, 0, 1)
        grid.addWidget(coloured("Loja:", GREY), 0, 2)
        grid.addLayout(self._bar_row(self.shop_bar, self.shop_text), 0, 3)
        grid.addWidget(coloured("Diárias:", GREY), 1, 0)
        grid.addWidget(self.daily, 1, 1)
        grid.addWidget(coloured("Troca de posição:", GREY), 1, 2)
        grid.addLayout(self._bar_row(self.videos_bar, self.videos_text), 1, 3)
        grid.addWidget(coloured("Desde o arranque:", GREY), 2, 0)
        grid.addWidget(self.summary, 2, 1, 1, 3)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)
        top_layout.addWidget(account)

        notices = QGroupBox("Avisos e erros")
        notices_layout = QVBoxLayout(notices)
        self.notices = make_table(["Hora", "Tipo", "Mensagem"], [70, 60])
        self.notices.setMinimumHeight(HEADER_HEIGHT + ROW_HEIGHT * 2 + 4)
        self.notices.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        notices_layout.addWidget(self.notices)

        split = QSplitter(Qt.Vertical)
        split.addWidget(top)
        split.addWidget(notices)
        split.setChildrenCollapsible(False)
        split.setStretchFactor(0, 1)
        split.setStretchFactor(1, 0)
        outer.addWidget(split)
        self.setCentralWidget(central)

        status = QStatusBar()
        self.next_label = QLabel()
        self.clock_label = QLabel()
        status.addWidget(self.next_label, 1)
        status.addPermanentWidget(self.clock_label)
        self.setStatusBar(status)

    @staticmethod
    def _bar_row(bar: Bar, text: QLabel) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(bar)
        row.addWidget(text)
        row.addStretch()
        return row

    def _build_tray(self) -> None:
        self.tray_icons = {working: tray_icon(self.logo, working) for working in (True, False)}
        self.tray = QSystemTrayIcon(self.tray_icons[False], self)
        menu = QMenu()
        menu.addAction(QAction("Abrir", self, triggered=self.show_window))
        self.tray_toggle = QAction("Iniciar", self, triggered=self.toggle_bot)
        menu.addAction(self.tray_toggle)
        menu.addSeparator()
        menu.addAction(self.quit_action)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(lambda reason: self.show_window() if reason in (
            QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick) else None)
        self.tray.show()

    # ---- state ----------------------------------------------------------------------------------------------
    def running(self) -> bool:
        return self.worker is not None and self.worker.is_alive()

    def refresh_state(self) -> None:
        from osmbot.game.browser import STATE_FILE

        working = self.running()
        idle = not working and not self.busy
        self.start_action.setEnabled(idle and not self.quitting)
        self.stop_action.setEnabled(working and not self.quitting and not self.stopping)
        self.login_action.setEnabled(idle)
        self.reload_action.setEnabled(idle)
        self.tray_toggle.setText("Parar" if working else "Iniciar")
        self.tray_toggle.setEnabled((working and not self.stopping) or idle)
        self.tray.setIcon(self.tray_icons[working])
        if working:
            since = datetime.fromtimestamp(self.started_at).strftime("%H:%M") if self.started_at else "?"
            text = "A parar…" if self.stopping else f"A trabalhar desde {since}"
        elif self.busy == "login":
            text = "Login: entra no jogo e FECHA a janela do Firefox"
        elif self.busy:
            text = "A ler o jogo…"
        else:
            text = "Parado · " + ("sessão iniciada" if STATE_FILE.exists() else "sem sessão: faz Login")
        if not self.panels:  # nothing read yet: say why
            if working or self.busy == "a ler":
                self.loading.setText("A ler o jogo…")
            elif not STATE_FILE.exists():
                self.loading.setText("Sem sessão. Carrega em Login, entra no jogo e fecha a janela do Firefox.")
            else:
                self.loading.setText("Sem dados do jogo. Ver → Atualizar quadro.")
        paint(self.state_dot, GREEN if working else GREY)
        self.state_text.setText(" " + text)
        self.tray.setToolTip(f"OSMbot · {text}")

    stopping = False

    # ---- the bot --------------------------------------------------------------------------------------------
    def start_bot(self) -> None:
        if self.running() or self.busy:
            return
        from osmbot.game.loop import run_active

        self.stopping = False
        self.started_at = time.time()
        self.message = ""

        def work() -> None:
            reason = ""
            try:
                run_active(False, board=self.bridge.board.emit)
            except SystemExit as stop:
                reason = stop.code if isinstance(stop.code, str) else ("Parou: ver o registo" if stop.code else "")
            except BaseException as error:  # never die silently: say it in the window
                reason = f"Parou: erro ({error})"
            self.bridge.finished.emit(reason)

        self.worker = threading.Thread(target=work, name="osmbot-loop", daemon=True)
        self.worker.start()
        self.refresh_state()

    def stop_bot(self) -> None:
        if not self.running():
            return
        from osmbot.game.loop import request_stop

        request_stop()
        self.stopping = True
        self.refresh_state()

    def toggle_bot(self) -> None:
        self.stop_bot() if self.running() else self.start_bot()

    def on_board(self, payload: dict) -> None:
        self.payload = payload
        self.render()

    def on_finished(self, reason: str) -> None:
        self.stopping = False
        self.started_at = None
        self.message = reason
        self.worker = None
        self.refresh_state()
        self.render()
        if self.quitting:
            self.app.quit()

    # ---- reading the game while stopped, and the login -------------------------------------------------------
    def read_game(self) -> None:
        from osmbot.game.browser import STATE_FILE

        if self.running() or self.busy or not STATE_FILE.exists():
            self.refresh_state()
            return
        self.busy = "a ler"
        self.refresh_state()

        def work() -> None:
            from osmbot.game.client import OsmClient
            from osmbot.game.dashboard import collect

            try:
                self.bridge.read.emit({"snapshot": collect(OsmClient())})
            except BaseException as error:
                self.bridge.read.emit({"error": f"Não consegui ler o jogo ({error})"})

        threading.Thread(target=work, name="osmbot-read", daemon=True).start()

    def on_read(self, result: dict) -> None:
        self.busy = ""
        if "snapshot" in result and not self.running():
            self.payload = {**self.payload, "snapshot": result["snapshot"], "status": "PARADO"}
        self.message = result.get("error", "")
        self.refresh_state()
        self.render()

    def do_login(self) -> None:
        if self.running() or self.busy:
            return
        from osmbot.game.browser import open_login_session

        self.busy = "login"
        self.refresh_state()

        def work() -> None:
            try:
                open_login_session()
                self.bridge.login.emit("")
            except BaseException as error:
                self.bridge.login.emit(f"Login: erro ({error})")

        threading.Thread(target=work, name="osmbot-login", daemon=True).start()

    def on_login(self, error: str) -> None:
        self.busy = ""
        self.message = error
        self.refresh_state()
        if not error:
            self.read_game()

    # ---- drawing --------------------------------------------------------------------------------------------
    def render(self) -> None:
        now = time.time()
        self.clock_label.setText(datetime.now().strftime("%H:%M:%S") + "  ")
        view = board_view(self.payload.get("snapshot"), self.payload.get("stats") if self.running() else None, now)
        if view:
            self._show_clubs(view["clubs"])
            account = view["account"]
            self.coins.setText(account["coins"])
            self.shop_bar.set(account["shop"]["done"])
            self.shop_text.setText(account["shop"]["text"])
            paint(self.shop_text, account["shop"]["colour"])
            self.daily.setText(" · ".join(f"<span style='color:{COLOURS.get(c, COLOURS[None])}'>{t}</span>"
                                          for t, c in account["daily"]) or "—")
            videos = account["videos"]
            self.videos_bar.set(videos["done"] if videos else None)
            self.videos_text.setText(videos["text"] if videos else "—")
            paint(self.videos_text, videos["colour"] if videos else GREY)
            self.summary.setText(account["summary"] if self.running() else "—")
        self._show_notices(self.payload.get("notices") or [])
        if self.message:
            self.next_label.setText("  " + self.message)
            paint(self.next_label, RED)
        elif self.running():
            self.next_label.setText("  " + ((view or {}).get("next") or "A trabalhar…"))
            paint(self.next_label, GREY)
        else:
            self.next_label.setText("  Parado. Carrega em Iniciar para o bot começar a trabalhar.")
            paint(self.next_label, GREY)

    def _show_clubs(self, clubs: list[dict]) -> None:
        if len(self.panels) != len(clubs):
            self.loading.hide()
            for panel in self.panels:
                panel.deleteLater()
            self.panels = [ClubPanel() for _ in clubs]
            for panel in self.panels:
                self.clubs_row.addWidget(panel)
        for panel, club in zip(self.panels, clubs):
            panel.show_club(club)

    def _show_notices(self, notices: list) -> None:
        if self.notices.rowCount() == len(notices):
            return
        self.notices.setRowCount(len(notices))
        for row, (when, kind, text) in enumerate(notices):
            set_cell(self.notices, row, 0, when)
            set_cell(self.notices, row, 1, kind, RED if kind == "Erro" else YELLOW)
            set_cell(self.notices, row, 2, text)
        self.notices.scrollToBottom()

    # ---- window, tray, quitting -----------------------------------------------------------------------------
    def show_window(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event) -> None:
        if self.quitting:
            event.accept()
            return
        event.ignore()  # the X only hides the window: the bot goes on, the tray icon brings it back
        self.hide()

    def quit_app(self) -> None:
        self.quitting = True
        if self.running():
            self.stop_bot()  # on_finished quits once the loop has stopped and written its summary
            self.refresh_state()
            self.hide()
            QTimer.singleShot(150_000, self.app.quit)  # a video in the middle can take ~90 s; never hang forever
        else:
            self.app.quit()

    def open_logs(self) -> None:
        from osmbot.logs import machine, repo_folder

        repo = repo_folder()
        folder = repo / "logs" / machine() if repo else Path.home() / ".osmbot"
        folder.mkdir(parents=True, exist_ok=True)
        os.startfile(folder) if sys.platform == "win32" else None

    def open_failures(self) -> None:
        folder = Path.home() / ".osmbot" / "failures"
        folder.mkdir(parents=True, exist_ok=True)
        os.startfile(folder) if sys.platform == "win32" else None

    def about(self) -> None:
        QMessageBox.about(self, "Sobre o OSMbot",
                          f"<b>OSMbot {__version__}</b><br>Trabalha por ti no Online Soccer Manager: recolhe e põe a treinar, "
                          "vê os vídeos, sobe o estádio, assina patrocinadores e avisa das vagas na lista de transferências."
                          "<br><br>Projeto independente, sem ligação à Gamebasics.")


def run_gui() -> None:
    """``osmbot`` with no command (and OSMbot.exe): the window. One window per PC user at a time."""
    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setApplicationName("OSMbot")
    app.setQuitOnLastWindowClosed(False)  # the X hides the window; the tray keeps the program alive
    app.setStyle("Fusion")
    app.setPalette(dark_palette())
    app.setFont(QFont("Segoe UI", 9))
    app.setStyleSheet(STYLE)
    lock = QLockFile(str(Path.home() / ".osmbot" / "window.lock"))
    (Path.home() / ".osmbot").mkdir(parents=True, exist_ok=True)
    if not lock.tryLock(100):
        QMessageBox.information(None, "OSMbot", "O OSMbot já está aberto (vê o ícone junto ao relógio).")
        return
    window = MainWindow(app)
    window.winId()
    dark_title_bar(window)
    window.show()
    hide_own_console()
    app.exec()
    lock.unlock()
