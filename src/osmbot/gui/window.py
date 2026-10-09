"""The OSMbot window (D-024): a Windows program around the same bot loop as the console.

It opens small, on the start screen (Abrir · Login · Sair). "Abrir" shows a loading sign, runs ``run_active`` in a
background thread that sends the board here, and grows to the full board once the game has been read. Iniciar,
Parar and Login are in the menu "Bot" and in the tray icon; the warnings and errors in Ver → Avisos e erros.
The window also reads the board itself (GETs only) every 3 min and on Ver → Atualizar, bot busy or not (D-027).
While the bot works, closing the window (X) only hides it; the tray icon (the logo with a green dot when working,
grey when stopped) opens it again or quits. No Windows notifications (owner, 2026-10-08).
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
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QImage, QPainter, QPalette, QPen, QPixmap
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QLabel,
                               QMainWindow, QMenu, QMessageBox, QPushButton, QScrollArea, QStackedWidget, QStatusBar, QStyle,
                               QSystemTrayIcon, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from osmbot import __version__
from osmbot.gui.view import BLUE, GREEN, GREY, RED, YELLOW, board_view

COLOURS = {GREEN: "#5cb85c", BLUE: "#5aa9ff", YELLOW: "#f0b429", GREY: "#8b9099", RED: "#e5534b", None: "#e8e8e8"}
BACKGROUND, CARD, LINE = "#1b1c1f", "#25272b", "#33363b"
LOGOS = Path.home() / ".osmbot" / "logos"
TRAY_DOT = {True: "#9be22d", False: "#9a9a9a"}  # lime with a white ring: readable on the green logo at 16 px
ROW_HEIGHT, HEADER_HEIGHT = 22, 24
STYLE = (
    "QGroupBox { font-weight: bold; border: 1px solid #3a3a3a; border-radius: 3px; margin-top: 8px; padding-top: 6px; }"
    "QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }"
    "QGroupBox QLabel, QGroupBox QTableWidget { font-weight: normal; }"
    "QHeaderView::section { background: #262626; color: #a0a0a0; border: none; border-bottom: 1px solid #3a3a3a; padding: 3px 6px; }"
    "QTableWidget { border: 1px solid #333333; }"
    "QStatusBar { border-top: 1px solid #333333; color: #a0a0a0; }"
    f"QFrame#card {{ background: {CARD}; border: 1px solid {LINE}; border-radius: 8px; }}"
    "QFrame#card QLabel { background: transparent; }"
    f"QScrollArea, QScrollArea > QWidget > QWidget {{ background: {BACKGROUND}; }}"
    f"QScrollBar:vertical {{ background: {BACKGROUND}; width: 10px; }}"
    f"QScrollBar::handle:vertical {{ background: {LINE}; border-radius: 4px; min-height: 30px; }}"
    "QScrollBar::add-line, QScrollBar::sub-line { height: 0; }"
)


def logo_path() -> Path:
    """The logo: next to OSMbot.exe in the portable/installed bot, in tools/assets when run from the repo."""
    here = Path(sys.executable).parent / "osmbot.ico"
    if here.exists():
        return here
    return Path(__file__).resolve().parents[3] / "tools" / "assets" / "osmbot.ico"


def dark_palette() -> QPalette:
    palette = QPalette()
    for role, colour in ((QPalette.Window, BACKGROUND), (QPalette.WindowText, "#dcdcdc"), (QPalette.Base, "#191919"),
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


def set_cell(table: QTableWidget, row: int, column: int, text: str, colour: str | None = None) -> None:
    item = table.item(row, column)
    if item is None:
        item = QTableWidgetItem()
        table.setItem(row, column, item)
    item.setText(text)
    item.setForeground(QColor(COLOURS.get(colour, COLOURS[None])))


def rich(pieces: list[tuple[str, str | None]]) -> str:
    """Coloured pieces of text as one label's HTML."""
    from html import escape

    return "".join(f"<span style='color:{COLOURS.get(colour, COLOURS[None])}'>{escape(text)}</span>" for text, colour in pieces)


def text_label(size: int = 9, bold: bool = False, colour: str | None = None) -> QLabel:
    label = QLabel()
    label.setTextFormat(Qt.RichText)
    font = QFont("Segoe UI", size)
    font.setBold(bold)
    label.setFont(font)
    paint(label, colour, bold)
    return label


def logo_colour(image: QImage) -> str:
    """The logo's main colour (for the stripe on top of the card): the most common strong colour, ignoring
    transparent, white, black and grey pixels."""
    from collections import Counter

    counts: Counter = Counter()
    for y in range(0, image.height(), 2):
        for x in range(0, image.width(), 2):
            c = image.pixelColor(x, y)
            if c.alpha() < 200 or c.saturation() < 70 or c.value() < 50:
                continue
            counts[(c.hue() // 15, c.saturation() // 64, c.value() // 64)] += 1
    if not counts:
        return COLOURS[GREY]
    (hue, sat, val), _ = counts.most_common(1)[0]
    return QColor.fromHsv(hue * 15 + 7, min(255, sat * 64 + 32), min(255, val * 64 + 32)).name()


def fetch_logo(key: str, url: str) -> Path | None:
    """The club's logo from the game's image server, kept in ~/.osmbot/logos (fetched once per club)."""
    import urllib.request

    target = LOGOS / f"{key}.png"
    if target.exists():
        return target
    try:
        LOGOS.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(url, timeout=20) as response:
            target.write_bytes(response.read())
        return target
    except Exception:
        return None


class ClubCard(QFrame):
    """One club (D-026): logo, name, next match; Liga · Taça · Valor do plantel; money, sponsors, stadium, pre-match;
    trainings; tired, injured and suspended players."""

    LABEL_WIDTH = 108

    def __init__(self):
        super().__init__()
        self.setObjectName("card")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 10)
        outer.setSpacing(0)
        self.stripe = QFrame()
        self.stripe.setFixedHeight(5)
        outer.addWidget(self.stripe)
        body = QVBoxLayout()
        body.setContentsMargins(14, 10, 14, 0)
        body.setSpacing(5)
        outer.addLayout(body)

        head = QHBoxLayout()
        self.logo = QLabel()
        self.logo.setFixedSize(46, 46)
        head.addWidget(self.logo)
        titles = QVBoxLayout()
        titles.setSpacing(0)
        self.name = text_label(16, True)
        self.subtitle = text_label()
        titles.addWidget(self.name)
        titles.addWidget(self.subtitle)
        head.addLayout(titles, 1)
        body.addLayout(head)

        facts = QGridLayout()
        facts.setHorizontalSpacing(0)
        facts.setVerticalSpacing(0)
        self.facts = []
        for column, span_ in ((0, 1), (1, 1), (2, 2)):
            title, value = text_label(8, colour=GREY), text_label(10, True)
            title.setAlignment(Qt.AlignCenter)
            value.setAlignment(Qt.AlignCenter)
            facts.addWidget(title, 0, column if column < 2 else 2, 1, span_)
            facts.addWidget(value, 1, column if column < 2 else 2, 1, span_)
            self.facts.append((title, value))
        for column in range(4):
            facts.setColumnStretch(column, 1)
        body.addSpacing(6)
        body.addLayout(facts)
        body.addSpacing(8)

        self.alert = text_label(9, True, YELLOW)
        body.addWidget(self.alert)
        self.money = self._row(body, "Dinheiro")
        self.sponsors = self._row(body, "Patrocinadores")
        self.stadium = self._row(body, "Estádio")
        self.prep = self._row(body, "Pré-jogo")
        self.prep.setWordWrap(True)

        body.addSpacing(4)
        self.trainings = QGridLayout()
        self.trainings.setHorizontalSpacing(10)
        self.trainings.setVerticalSpacing(3)
        self.trainings.addWidget(text_label(8, colour=GREY), 0, 0)
        self.trainings.itemAtPosition(0, 0).widget().setText("Treinos")
        self.trainings.setColumnStretch(3, 1)
        self.training_rows: list[tuple[QLabel, QLabel, QLabel, Bar]] = []
        body.addLayout(self.trainings)
        body.addSpacing(2)
        self.tired = text_label(9, colour=YELLOW)
        self.injured = text_label()
        self.suspended = text_label()
        for label in (self.tired, self.injured, self.suspended):
            label.setWordWrap(True)
            body.addWidget(label)

    def _row(self, body: QVBoxLayout, name: str) -> QLabel:
        row = QHBoxLayout()
        row.setSpacing(8)
        title = text_label(colour=GREY)
        title.setText(name)
        title.setFixedWidth(self.LABEL_WIDTH)
        title.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        value = text_label()
        row.addWidget(title)
        row.addWidget(value, 1)
        body.addLayout(row)
        return value

    def set_logo(self, pixmap: QPixmap | None, colour: str | None) -> None:
        if pixmap is not None and not pixmap.isNull():
            self.logo.setPixmap(pixmap.scaled(46, 46, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.stripe.setStyleSheet(f"background:{colour or LINE}; border-top-left-radius:8px; border-top-right-radius:8px;")

    def show_club(self, club: dict) -> None:
        self.name.setText(club["name"])
        self.subtitle.setText(rich(club["subtitle"]))
        for (title, value), (name, text, colour) in zip(self.facts, club["facts"]):
            title.setText(name)
            value.setText(rich([(text, colour)]))
        self.alert.setVisible(bool(club["alert"]))
        self.alert.setText(f"❗ {club['alert']}")
        self.money.setText(f"<b>{rich([(club['money'], None)])}</b>" + rich([("     " + sale, GREEN) for sale in club["sales"]]))
        self.sponsors.setText(rich([club["sponsors"]]))
        still = rich([piece for index, part in enumerate(club["stadium"]["still"]) for piece in ((" · ", GREY),) * bool(index) + (part,)])
        moving = "<br>".join(rich([part]) for part in club["stadium"]["moving"])
        self.stadium.setText("<br>".join(line for line in (still, moving) if line) or rich([("—", GREY)]))
        prep = club["prep"]
        head = rich([(prep["pct"], prep["colour"])]) + "&nbsp;&nbsp;" if prep["pct"] else ""
        steps = [rich([step]) for step in prep["steps"]]
        half = (len(steps) + 1) // 2
        self.prep.setText(head + "&nbsp;&nbsp;".join(steps[:half]) + "<br>" + "&nbsp;&nbsp;".join(steps[half:]) if steps
                          else rich([("—", GREY)]))
        self._show_trainings(club["trainings"])
        self.tired.setVisible(bool(club["tired"]))
        self.tired.setText(f"⚠ Cansados: {club['tired']}")
        self.injured.setText(rich([("Lesionados: ", GREY)] + club["injured"]))
        self.suspended.setText(rich([("Suspensos: ", GREY)] + club["suspended"]))

    def _show_trainings(self, rows: list) -> None:
        while len(self.training_rows) < len(rows):
            index = len(self.training_rows) + 1
            cells = (text_label(), text_label(colour=GREY), text_label(), Bar())
            for column, cell in enumerate(cells):
                self.trainings.addWidget(cell, index, column)
            self.training_rows.append(cells)
        for index, cells in enumerate(self.training_rows):
            visible = index < len(rows)
            for cell in cells:
                cell.setVisible(visible)
            if not visible:
                continue
            name, pos, left, colour, done, skipped = rows[index]
            cells[0].setText(name)
            cells[1].setText(pos)
            cells[2].setText(rich([(left, colour)]))
            cells[3].set(done, skipped)


class Spinner(QWidget):
    """The "loading" sign: an arc that turns while the game is being read."""

    def __init__(self, size: int = 44):
        super().__init__()
        self.angle = 0
        self.setFixedSize(size, size)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._turn)

    def _turn(self) -> None:
        self.angle = (self.angle + 30) % 360
        self.update()

    def showEvent(self, _event) -> None:
        self.timer.start(80)

    def hideEvent(self, _event) -> None:
        self.timer.stop()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        box = QRectF(self.rect()).adjusted(4, 4, -4, -4)
        painter.setPen(QPen(QColor("#333333"), 4))
        painter.drawEllipse(box)
        painter.setPen(QPen(QColor(COLOURS[GREEN]), 4, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(box, -self.angle * 16, 100 * 16)


class Bridge(QObject):
    """Carries what the background threads read to the window (Qt widgets live in the main thread only)."""

    board = Signal(object)
    finished = Signal(str)
    read = Signal(object)
    login = Signal(str)
    logo = Signal(str)


class NoticesWindow(QWidget):
    """Ver → Avisos e erros: the problems and warnings of this run, in a window of their own."""

    def __init__(self, parent: QWidget):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("OSMbot — Avisos e erros")
        layout = QVBoxLayout(self)
        self.table = make_table(["Hora", "Tipo", "Mensagem"], [70, 60])
        layout.addWidget(self.table)
        self.resize(760, 320)

    def show_notices(self, notices: list) -> None:
        if self.table.rowCount() == len(notices):
            return
        self.table.setRowCount(len(notices))
        for row, (when, kind, text) in enumerate(notices):
            set_cell(self.table, row, 0, when)
            set_cell(self.table, row, 1, kind, RED if kind == "Erro" else YELLOW)
            set_cell(self.table, row, 2, text)
        self.table.scrollToBottom()


READ_EVERY = 180  # s: the window reads the board on its own this often (owner, 2026-10-09)
READ_ERROR = "Não consegui ler o jogo"


def newest(snapshot: dict | None, other: dict | None) -> dict | None:
    """The more recent of two readings of the game: the bot's and the window's own come in any order."""
    if not snapshot or not other:
        return snapshot or other
    return snapshot if snapshot.get("read_at", 0) >= other.get("read_at", 0) else other


LAUNCHER_SIZE = QSize(520, 290)
BOARD_SIZE = QSize(1060, 600)
START, LOADING, BOARD = 0, 1, 2


class MainWindow(QMainWindow):
    """One window, three faces: the start screen (Abrir · Login · Sair), "loading" while the game is read, and the
    full board (it grows to it). Abrir starts the bot (owner, 2026-10-08); Iniciar/Parar/Login live in the menu
    "Bot" and in the tray icon."""

    def __init__(self, app: QApplication):
        super().__init__()
        from osmbot.logs import machine

        self.app = app
        self.bridge = Bridge()
        self.bridge.board.connect(self.on_board)
        self.bridge.finished.connect(self.on_finished)
        self.bridge.read.connect(self.on_read)
        self.bridge.login.connect(self.on_login)
        self.bridge.logo.connect(lambda _key: self.render())
        self.logos: dict[str, tuple[QPixmap, str] | None] = {}  # club key -> (logo, stripe colour); None while fetching
        self.payload: dict = {}
        self.worker: threading.Thread | None = None
        self.busy = ""  # "login" while the login runs
        self.reading = False  # the window reads the board on its own, bot working or not (D-027)
        self.quitting = False
        self.stopping = False
        self.started_at: float | None = None
        self.message = ""
        self.logo = QIcon(str(logo_path()))
        self.setWindowTitle(f"OSMbot {__version__} — {machine()}")
        self.setWindowIcon(self.logo)
        self.pages = QStackedWidget()
        self.pages.addWidget(self._build_start())
        self.pages.addWidget(self._build_loading())
        self.pages.addWidget(self._build_board())
        self.setCentralWidget(self.pages)
        self._build_menu()
        self._build_status()
        self._build_tray()
        self.notices_window = NoticesWindow(self)
        self.clock = QTimer(self)
        self.clock.timeout.connect(self.render)
        self.clock.start(1000)
        self.reader = QTimer(self)
        self.reader.timeout.connect(self.auto_read)
        self.reader.start(READ_EVERY * 1000)
        self.go(START)

    # ---- the three faces ------------------------------------------------------------------------------------
    def _build_start(self) -> QWidget:
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(22, 22, 22, 18)
        layout.setSpacing(22)
        logo = QLabel()
        logo.setPixmap(self.logo.pixmap(128, 128))
        logo.setAlignment(Qt.AlignTop)
        layout.addWidget(logo)
        right = QVBoxLayout()
        right.setSpacing(6)
        title = QLabel("OSMbot")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        right.addWidget(title)
        right.addWidget(coloured(f"Versão {__version__}", GREY))
        text = QLabel("Trabalha por ti no Online Soccer Manager: treinos, vídeos, estádio, patrocinadores, amigável e "
                      "análise antes do jogo, médico e advogado, e avisa das vagas na lista de transferências.")
        text.setWordWrap(True)
        right.addSpacing(6)
        right.addWidget(text)
        right.addSpacing(8)
        self.session_label = QLabel()
        self.session_label.setWordWrap(True)
        right.addWidget(self.session_label)
        right.addStretch()
        buttons = QHBoxLayout()
        buttons.addStretch()
        self.login_button = QPushButton("Login")
        self.quit_button = QPushButton("Sair")
        self.open_button = QPushButton("Abrir")
        self.open_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.open_button.setDefault(True)
        for button, slot in ((self.login_button, self.do_login), (self.quit_button, self.quit_app), (self.open_button, self.open_board)):
            button.setMinimumWidth(88)
            button.clicked.connect(slot)
            buttons.addWidget(button)
        right.addLayout(buttons)
        layout.addLayout(right, 1)
        return page

    def _build_loading(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addStretch()
        self.spinner = Spinner()
        layout.addWidget(self.spinner, 0, Qt.AlignHCenter)
        layout.addSpacing(12)
        self.loading_label = coloured("A carregar o jogo…", GREY)
        self.loading_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.loading_label)
        layout.addStretch()
        return page

    def _build_board(self) -> QWidget:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(10, 8, 10, 6)
        outer.setSpacing(10)
        inner = QWidget()
        column = QVBoxLayout(inner)
        column.setContentsMargins(0, 0, 0, 0)
        self.clubs_grid = QGridLayout()
        self.clubs_grid.setSpacing(10)
        self.clubs_grid.setColumnStretch(0, 1)
        self.clubs_grid.setColumnStretch(1, 1)
        column.addLayout(self.clubs_grid)
        column.addStretch(1)
        scroll = QScrollArea()  # 3 or 4 clubs may not fit: the clubs scroll, the account panel stays (owner, 2026-10-09)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(inner)
        self.panels: list[ClubCard] = []
        outer.addWidget(scroll, 1)

        account = QFrame()
        account.setObjectName("card")
        row = QHBoxLayout(account)
        row.setContentsMargins(16, 10, 16, 10)
        row.setSpacing(28)
        coins = QVBoxLayout()
        coins.setSpacing(0)
        coins.addWidget(coloured("Boss coins", GREY))
        line = QHBoxLayout()
        self.coins = text_label(22, True, YELLOW)
        self.coins_jump = text_label(11, True, GREEN)
        line.addWidget(self.coins)
        line.addWidget(self.coins_jump, 0, Qt.AlignBottom)
        line.addStretch()
        coins.addLayout(line)
        self.coins_since = text_label(8, colour=GREY)
        coins.addWidget(self.coins_since)
        row.addLayout(coins)
        divider = QFrame()
        divider.setFrameShape(QFrame.VLine)
        divider.setStyleSheet(f"color:{LINE};")
        row.addWidget(divider)
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(4)
        self.timer_cells: list[tuple[QLabel, QLabel]] = []
        for index in range(4):
            r, c = (index, 0) if index < 3 else (index - 3, 2)
            name, value = text_label(colour=GREY), text_label()
            grid.addWidget(name, r, c)
            grid.addWidget(value, r, c + 1)
            self.timer_cells.append((name, value))
        grid.addWidget(coloured("Diárias", GREY), 1, 2)
        self.daily = text_label()
        grid.addWidget(self.daily, 1, 3)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 2)
        row.addLayout(grid, 1)
        outer.addWidget(account)
        return page

    def _build_menu(self) -> None:
        style = self.style()
        self.start_action = QAction(style.standardIcon(QStyle.SP_MediaPlay), "Iniciar", self, triggered=self.start_bot)
        self.stop_action = QAction(style.standardIcon(QStyle.SP_MediaStop), "Parar", self, triggered=self.stop_bot)
        self.login_action = QAction("Login", self, triggered=self.do_login)
        self.notices_action = QAction("Avisos e erros", self, triggered=self.show_notices)
        self.reload_action = QAction("Atualizar", self, triggered=self.read_game)
        self.logs_action = QAction("Pasta dos logs", self, triggered=self.open_logs)
        self.failures_action = QAction("Capturas das falhas", self, triggered=self.open_failures)
        self.quit_action = QAction("Sair", self, triggered=self.quit_app)
        bot = self.menuBar().addMenu("Bot")
        for action in (self.start_action, self.stop_action, self.login_action):
            bot.addAction(action)
        bot.addSeparator()
        bot.addAction(self.quit_action)
        view = self.menuBar().addMenu("Ver")
        view.addAction(self.reload_action)
        view.addSeparator()
        for action in (self.notices_action, self.logs_action, self.failures_action):
            view.addAction(action)
        self.menuBar().addMenu("Ajuda").addAction(QAction("Sobre o OSMbot", self, triggered=self.about))

    def _build_status(self) -> None:
        status = QStatusBar()
        self.state_dot = coloured("●", GREY)
        self.state_text = QLabel()
        self.next_label = QLabel()
        self.clock_label = QLabel()
        status.addWidget(QLabel(" "))
        status.addWidget(self.state_dot)
        status.addWidget(self.state_text)
        status.addWidget(self.next_label, 1)
        status.addPermanentWidget(self.clock_label)
        self.setStatusBar(status)

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

    def go(self, page: int) -> None:
        """Show one face; the window takes that face's size (small for the start screen, big for the board)."""
        self.pages.setCurrentIndex(page)
        self.menuBar().setVisible(page == BOARD)
        self.statusBar().setVisible(page == BOARD)
        if page == BOARD:
            self.setMinimumSize(800, 480)
            self.setMaximumSize(16777215, 16777215)
            if self.width() < BOARD_SIZE.width():
                centre = self.frameGeometry().center()
                self.resize(BOARD_SIZE)
                frame = self.frameGeometry()
                frame.moveCenter(centre)
                self.move(frame.topLeft())
        else:
            self.setFixedSize(LAUNCHER_SIZE)
        self.refresh_state()

    # ---- state ----------------------------------------------------------------------------------------------
    def running(self) -> bool:
        return self.worker is not None and self.worker.is_alive()

    def refresh_state(self) -> None:
        from osmbot.game.browser import STATE_FILE

        working = self.running()
        idle = not working and not self.busy
        has_session = STATE_FILE.exists()
        self.start_action.setEnabled(idle and not self.quitting)
        self.stop_action.setEnabled(working and not self.quitting and not self.stopping)
        self.login_action.setEnabled(idle)
        self.reload_action.setEnabled(has_session and not self.reading and not self.busy)
        self.open_button.setEnabled(idle and has_session)
        self.login_button.setEnabled(idle)
        self.tray_toggle.setText("Parar" if working else "Iniciar")
        self.tray_toggle.setEnabled((working and not self.stopping) or (idle and has_session))
        self.tray.setIcon(self.tray_icons[working])
        if self.busy == "login":
            session, colour = "Login: entra no jogo no Firefox e FECHA essa janela.", BLUE
        elif self.message and self.pages.currentIndex() == START:
            session, colour = self.message, RED
        elif has_session:
            session, colour = "● Sessão iniciada", GREEN
        else:
            session, colour = "● Sem sessão: carrega em Login primeiro.", YELLOW
        self.session_label.setText(session)
        paint(self.session_label, colour)
        if working:
            since = datetime.fromtimestamp(self.started_at).strftime("%H:%M") if self.started_at else "?"
            text = "A parar…" if self.stopping else f"A trabalhar desde {since}"
        elif self.busy or self.reading:
            text = "A ler o jogo…"
        else:
            text = "Parado"
        paint(self.state_dot, GREEN if working else GREY)
        self.state_text.setText(text + "   ")
        self.tray.setToolTip(f"OSMbot · {text}")
        count = len(self.payload.get("notices") or [])
        self.notices_action.setText(f"Avisos e erros ({count})" if count else "Avisos e erros")

    # ---- the bot --------------------------------------------------------------------------------------------
    def open_board(self) -> None:
        """Abrir: show "loading", start the bot, and grow to the board when the game has been read."""
        if self.running() or self.busy:
            return
        self.message = ""
        self.loading_label.setText("A carregar o jogo…")
        self.go(LOADING)
        self.start_bot()

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
        if self.running():
            self.stop_bot()
        elif self.pages.currentIndex() == START:
            self.show_window()
            self.open_board()
        else:
            self.start_bot()

    def on_board(self, payload: dict) -> None:
        self.payload = {**payload, "snapshot": newest(payload.get("snapshot"), self.payload.get("snapshot"))}
        if payload.get("snapshot") and self.pages.currentIndex() == LOADING:
            self.go(BOARD)
        self.render()

    def on_finished(self, reason: str) -> None:
        self.stopping = False
        self.started_at = None
        self.message = reason
        self.worker = None
        if self.quitting:
            self.app.quit()
            return
        if self.pages.currentIndex() == LOADING:  # it stopped before the game could be read: back to the start
            self.go(START)
            self.show_window()
        self.refresh_state()
        self.render()

    # ---- reading the game (any time), and the login -------------------------------------------------------------
    def auto_read(self) -> None:
        """Every READ_EVERY seconds the board is read again, even while the bot is busy (a video, say)."""
        if self.pages.currentIndex() == BOARD:
            self.read_game()

    def read_game(self) -> None:
        """Ver → Atualizar (and every 3 min): read the game now, GETs only, beside the bot and never waiting for it."""
        from osmbot.game.browser import STATE_FILE

        if self.reading or self.busy or not STATE_FILE.exists():
            return
        self.reading = True
        self.refresh_state()

        def work() -> None:
            from osmbot.game.client import OsmClient
            from osmbot.game.dashboard import collect

            try:
                self.bridge.read.emit({"snapshot": collect(OsmClient())})
            except BaseException as error:
                self.bridge.read.emit({"error": f"{READ_ERROR} ({error})"})

        threading.Thread(target=work, name="osmbot-read", daemon=True).start()

    def on_read(self, result: dict) -> None:
        self.reading = False
        if "snapshot" in result:
            self.payload = {**self.payload, "snapshot": newest(result["snapshot"], self.payload.get("snapshot"))}
            if not self.running():
                self.payload["status"] = "PARADO"
            if self.message.startswith(READ_ERROR):
                self.message = ""
        else:
            self.message = result["error"]
        self.refresh_state()
        self.render()

    def do_login(self) -> None:
        if self.running() or self.busy:
            return
        from osmbot.game.browser import open_login_session

        self.busy = "login"
        self.message = ""
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
        if not error and self.pages.currentIndex() == BOARD:
            self.read_game()

    # ---- drawing --------------------------------------------------------------------------------------------
    def render(self) -> None:
        now = time.time()
        self.clock_label.setText(datetime.now().strftime("%H:%M:%S") + "  ")
        notices = self.payload.get("notices") or []
        self.notices_window.show_notices(notices)
        self.refresh_state()
        if self.pages.currentIndex() != BOARD:
            return
        view = board_view(self.payload.get("snapshot"), self.payload.get("stats") if self.running() else None, now)
        if view:
            self._show_clubs(view["clubs"])
            account = view["account"]
            self.coins.setText(account["coins"])
            self.coins_jump.setText(account["jump"])
            self.coins_since.setText(account["since"])
            for (name, value), (label, text, colour) in zip(self.timer_cells, account["timers"]):
                name.setText(label)
                value.setText(rich([(text, colour)]))
            self.daily.setText(rich([piece for index, part in enumerate(account["daily"])
                                     for piece in ((" · ", GREY),) * bool(index) + (part,)]) or rich([("—", GREY)]))
        if self.message:
            self.next_label.setText("· " + self.message)
            paint(self.next_label, RED)
        elif self.running():
            self.next_label.setText("· " + ((view or {}).get("next") or "a trabalhar…"))
            paint(self.next_label, GREY)
        else:
            self.next_label.setText("· Bot → Iniciar para voltar a trabalhar")
            paint(self.next_label, GREY)

    def _show_clubs(self, clubs: list[dict]) -> None:
        if len(self.panels) != len(clubs):
            for panel in self.panels:
                panel.deleteLater()
            self.panels = [ClubCard() for _ in clubs]
            for index, panel in enumerate(self.panels):
                self.clubs_grid.addWidget(panel, index // 2, index % 2, Qt.AlignTop)  # 2 x 2 (owner, 2026-10-08)
        for panel, club in zip(self.panels, clubs):
            panel.show_club(club)
            panel.set_logo(*self._logo(club))

    def _logo(self, club: dict) -> tuple[QPixmap | None, str | None]:
        """The club's logo and stripe colour; fetched in the background the first time (then kept on disk)."""
        key, url = club["logo_key"], club.get("logo")
        if key in self.logos:
            return self.logos[key] or (None, None)
        self.logos[key] = None
        target = LOGOS / f"{key}.png"
        if not target.exists() and url:
            def work() -> None:
                if fetch_logo(key, url):
                    self.logos.pop(key, None)
                    self.bridge.logo.emit(key)

            threading.Thread(target=work, name="osmbot-logo", daemon=True).start()
            return None, None
        if target.exists():
            image = QImage(str(target))
            self.logos[key] = (QPixmap.fromImage(image), logo_colour(image))
            return self.logos[key]
        return None, None

    # ---- window, tray, quitting -----------------------------------------------------------------------------
    def show_notices(self) -> None:
        self.notices_window.show()
        self.notices_window.raise_()
        self.notices_window.activateWindow()
        dark_title_bar(self.notices_window)

    def show_window(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event) -> None:
        if self.quitting or not self.running():
            event.accept()  # nothing working: the X closes the program
            self.quitting = True
            self.tray.hide()
            self.app.quit()
            return
        event.ignore()  # the bot works: the X only hides the window; the tray icon brings it back
        self.hide()

    def quit_app(self) -> None:
        self.quitting = True
        if self.running():
            self.stop_bot()  # on_finished quits once the loop has stopped and written its summary
            self.refresh_state()
            self.hide()
            QTimer.singleShot(150_000, self.app.quit)  # a video in the middle can take ~90 s; never hang forever
        else:
            self.tray.hide()
            self.app.quit()

    def open_logs(self) -> None:
        from osmbot.logs import machine, repo_folder

        repo = repo_folder()
        folder = repo / "logs" / machine() if repo else Path.home() / ".osmbot"
        folder.mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(folder)

    def open_failures(self) -> None:
        folder = Path.home() / ".osmbot" / "failures"
        folder.mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(folder)

    def about(self) -> None:
        QMessageBox.about(self, "Sobre o OSMbot",
                          f"<b>OSMbot {__version__}</b><br>Trabalha por ti no Online Soccer Manager: recolhe e põe a treinar, "
                          "vê os vídeos, sobe o estádio, assina patrocinadores, faz o amigável e a análise antes do jogo, trata do médico "
                          "e do advogado e avisa das vagas na lista de transferências."
                          "<br><br>Projeto independente, sem ligação à Gamebasics.")


def run_gui() -> None:
    """``osmbot`` with no command (and OSMbot.exe): the window. One window per PC user at a time."""
    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setApplicationName("OSMbot")
    app.setQuitOnLastWindowClosed(False)  # the X hides the window while the bot works; the tray keeps it alive
    app.setStyle("Fusion")
    app.setPalette(dark_palette())
    app.setFont(QFont("Segoe UI", 9))
    app.setStyleSheet(STYLE)
    (Path.home() / ".osmbot").mkdir(parents=True, exist_ok=True)
    lock = QLockFile(str(Path.home() / ".osmbot" / "window.lock"))
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
