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
from PySide6.QtGui import QAction, QColor, QFont, QFontDatabase, QIcon, QImage, QPainter, QPalette, QPen, QPixmap
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QLabel,
                               QMainWindow, QMenu, QMessageBox, QPushButton, QScrollArea, QStackedWidget, QStyle,
                               QSystemTrayIcon, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from osmbot import __version__
from osmbot.i18n import LANGUAGES, language, load_language, set_language, tr
from osmbot.gui.view import BLUE, GREEN, GREY, RED, YELLOW, board_view

COLOURS = {GREEN: "#5cd17a", BLUE: "#7cc4ff", YELLOW: "#f5c542", GREY: "#8f95b8", RED: "#ff6b6b", None: "#eef0ff"}
BACKGROUND, CARD, LINE = "#0b0f2a", "rgba(16, 20, 50, 232)", "#2d3366"  # night-stadium blues (D-030)
TEXT, MUTED, ACCENT, ACCENT_LIGHT, RING_TRACK = "#eef0ff", "#8f95b8", "#8b8cf8", "#b9baff", "#2a2f5a"
BACKGROUND_FILE = Path(__file__).resolve().parent / "assets" / "fundo.jpg"  # the board's background picture (D-030)
FONT_FILE = Path(__file__).resolve().parent / "assets" / "Sora.ttf"  # the window's typeface (owner, 2026-10-10; OFL)
FONT = "Segoe UI"  # until Sora is loaded (load_font)
LOGOS = Path.home() / ".osmbot" / "logos"
TRAY_DOT = {True: "#9be22d", False: "#9a9a9a"}  # lime with a white ring: readable on the green logo at 16 px
ROW_HEIGHT, HEADER_HEIGHT = 22, 24
STYLE = (
    "QGroupBox { font-weight: bold; border: 1px solid #3a3a3a; border-radius: 3px; margin-top: 8px; padding-top: 6px; }"
    "QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }"
    "QGroupBox QLabel, QGroupBox QTableWidget { font-weight: normal; }"
    "QHeaderView::section { background: #262626; color: #a0a0a0; border: none; border-bottom: 1px solid #3a3a3a; padding: 3px 6px; }"
    "QTableWidget { border: 1px solid #333333; }"
    f"QFrame#card {{ background: {CARD}; border: 1px solid rgba(139, 140, 248, 45); border-radius: 14px; }}"
    "QFrame#coins { border: 1px solid rgba(245, 197, 66, 70); border-radius: 14px; background: qlineargradient("
    "x1:0, y1:0, x2:1, y2:1, stop:0 rgba(16, 20, 50, 238), stop:1 rgba(90, 70, 20, 218)); }"
    "QFrame#coins QLabel { background: transparent; }"
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


def load_font() -> None:
    """Sora for the whole window, shipped with the bot; Segoe UI stays if the file cannot be loaded."""
    global FONT
    families = QFontDatabase.applicationFontFamilies(QFontDatabase.addApplicationFont(str(FONT_FILE)))
    if families:
        FONT = families[0]


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
    label = QLabel(tr(text))
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
    table.setHorizontalHeaderLabels([tr(h) for h in headers])
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
    item.setText(tr(text))
    item.setForeground(QColor(COLOURS.get(colour, COLOURS[None])))


def rich(pieces: list[tuple[str, str | None]]) -> str:
    """Coloured pieces of text as one label's HTML."""
    from html import escape

    return "".join(f"<span style='color:{COLOURS.get(colour, COLOURS[None])}'>{escape(tr(text))}</span>" for text, colour in pieces)


def text_label(size: int = 9, bold: bool = False, colour: str | None = None) -> QLabel:
    label = QLabel()
    label.setTextFormat(Qt.RichText)
    font = QFont(FONT, size)
    font.setBold(bold)
    label.setFont(font)
    paint(label, colour, bold)
    return label


def logo_colour(image: QImage) -> str:
    """The logo's main colour (card, match stripe, timeline dot): the most common strong colour inside the shield,
    ignoring transparent, white, black and grey pixels. Only the middle is read: every OSM logo has the same gold
    frame, which would otherwise win."""
    from collections import Counter

    counts: Counter = Counter()
    width, height = image.width(), image.height()
    for y in range(int(height * 0.25), int(height * 0.8), 2):
        for x in range(int(width * 0.25), int(width * 0.75), 2):
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


class Ring(QWidget):
    """A ring (D-030). Trainings: the arc is the time gone by (the part a video skipped in light blue), the time left
    in the middle, full and green when ready. ``show_ring`` paints any other ring: the arc's share, its colour and the
    text colour (the stadium parts standing still and the doctor/lawyer with nobody are dimmed)."""

    def __init__(self, size: int = 78, width: int = 6, font: int = 11):
        super().__init__()
        self.setFixedSize(size, size)
        self.pen, self.font_size = width, font
        self.text, self.colour, self.done, self.skipped = "", None, 0.0, 0.0
        self.arc, self.text_colour, self.emoji = ACCENT, TEXT, False

    def set(self, text: str, colour: str | None, done: float, skipped: float = 0.0) -> None:
        """A training: green and full when ready, else the accent colour (and light blue for the skipped part)."""
        ready = colour == GREEN
        self.show_ring(text, 1.0 if ready else done, COLOURS[GREEN] if ready else ACCENT,
                       COLOURS[GREEN] if ready else TEXT, 0.0 if ready else skipped)
        self.colour = colour

    def show_ring(self, text: str, done: float, arc: str, text_colour: str, skipped: float = 0.0, emoji: bool = False) -> None:
        self.text, self.done, self.arc, self.text_colour, self.emoji = text, done, arc, text_colour, emoji
        self.skipped = min(skipped, done)
        self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        margin = self.pen / 2 + 2
        box = QRectF(self.rect()).adjusted(margin, margin, -margin, -margin)
        painter.setPen(QPen(QColor(RING_TRACK), self.pen))
        painter.drawEllipse(box)
        own = self.done - self.skipped
        start = 90 * 16  # from the top, clockwise
        if own > 0:
            painter.setPen(QPen(QColor(self.arc), self.pen, Qt.SolidLine, Qt.RoundCap))
            painter.drawArc(box, start, -int(own * 360 * 16))
        if self.skipped:
            painter.setPen(QPen(QColor(COLOURS[BLUE]), self.pen, Qt.SolidLine, Qt.RoundCap))
            painter.drawArc(box, start - int(own * 360 * 16), -int(self.skipped * 360 * 16))
        painter.setPen(QColor(self.text_colour))
        painter.setFont(QFont("Segoe UI Emoji", self.font_size + 7) if self.emoji else QFont(FONT, self.font_size, QFont.Bold))
        painter.drawText(self.rect(), Qt.AlignCenter, self.text)


class RingCell(QWidget):
    """A ring with a few lines under it (name, detail...)."""

    def __init__(self, size: int, width: int, font: int, lines: int = 2):
        super().__init__()
        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(1)
        self.ring = Ring(size, width, font)
        column.addWidget(self.ring, 0, Qt.AlignHCenter)
        self.lines = [text_label(10 if index == 0 else 8) for index in range(lines)]
        for label in self.lines:
            label.setAlignment(Qt.AlignHCenter)
            column.addWidget(label, 0, Qt.AlignHCenter)

    def say(self, *texts: tuple[str, str]) -> None:
        """(text, css colour) for each line."""
        for label, (text, colour) in zip(self.lines, texts):
            label.setText(tr(text))
            label.setStyleSheet(f"color:{colour};")
            label.setVisible(bool(text))


CARE_EMOJI = {"Médico": "🩺", "Advogado": "⚖️"}
STADIUM_RING = {"moving": (ACCENT, TEXT), "top": (COLOURS[GREEN], COLOURS[GREEN]), "still": ("#4a5080", MUTED)}
CARE_RING = {"none": (RING_TRACK, MUTED), "working": (ACCENT, TEXT), "ready": (COLOURS[GREEN], COLOURS[GREEN]),
             "waiting": (COLOURS[YELLOW], COLOURS[YELLOW]), "blocked": ("#4a5080", MUTED)}


class ElidedLabel(QLabel):
    """One line that ends in "…" when it does not fit, instead of breaking."""

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setPen(self.palette().color(QPalette.WindowText))
        painter.setFont(self.font())
        painter.drawText(self.rect(), Qt.AlignLeft | Qt.AlignVCenter,
                         painter.fontMetrics().elidedText(self.text(), Qt.ElideRight, self.width()))

    def minimumSizeHint(self) -> QSize:
        return QSize(20, super().minimumSizeHint().height())


class MatchStripe(QFrame):
    """The next match (D-030): a small "CASA"/"FORA" tag in the corner, "vs Clube (8.º)" on one line and "em 3h33";
    painted in the club's colour (from its logo), the same home or away (owner, 2026-10-10); ⚠ for a direct rival."""

    def __init__(self):
        super().__init__()
        row = QHBoxLayout(self)
        row.setContentsMargins(14, 5, 14, 7)
        texts = QVBoxLayout()
        texts.setSpacing(0)
        self.tag = text_label(7, True)
        self.text = ElidedLabel()
        self.text.setFont(QFont(FONT, 10))
        texts.addWidget(self.tag)
        texts.addWidget(self.text)
        self.left = text_label(10)
        row.addLayout(texts, 1)
        row.addWidget(self.left, 0, Qt.AlignVCenter)
        self.colour = ""
        self.set_colour(None)

    def set_colour(self, colour: str | None) -> None:
        """The club's colour, darkened enough for white text on top (the accent until the logo is in)."""
        c = QColor(colour or ACCENT)
        hue, sat, val, _ = c.getHsv()
        start = QColor.fromHsv(hue, sat, min(val, 150))
        name = start.name()
        if name == self.colour:
            return
        self.colour = name
        end = f"rgba({start.red()},{start.green()},{start.blue()},40)"
        self.setStyleSheet(f"MatchStripe {{ border-radius: 8px; background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
                           f"stop:0 {name}, stop:1 {end}); }} QLabel {{ background: transparent; color: #f2f2f7; }}")

    def show_match(self, match: dict | None) -> None:
        self.setVisible(bool(match))
        if not match:
            return
        self.tag.setText(tr(match["tag"]))
        self.tag.setStyleSheet("color: rgba(255,255,255,170); letter-spacing: 1px;")
        self.text.setText(("⚠ " if match["danger"] else "") + tr(match["text"]))
        self.left.setText(f"{tr('em')} <b style='font-size:15pt'>{match['left']}</b>" if match["left"] else "")


def column_title(text: str = "") -> QLabel:
    label = text_label(8, True)
    label.setStyleSheet(f"color:{MUTED}; letter-spacing:1px; font-weight:bold;")
    label.setText(tr(text))
    return label


def divider() -> QFrame:
    line = QFrame()
    line.setFixedWidth(1)
    line.setStyleSheet(f"background:{LINE};")
    return line


class ClubCard(QFrame):
    """One club (D-030), three columns: the club (name, match, value, money, sponsors, stadium) · the trainings as
    rings · the pre-match checklist with the tired, injured and suspended players under it."""

    LABEL_WIDTH = 104

    def __init__(self):
        super().__init__()
        self.setObjectName("card")
        self.colour = ""
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)

        club = QVBoxLayout()
        club.setContentsMargins(18, 14, 16, 14)
        club.setSpacing(5)
        head = QHBoxLayout()
        head.setSpacing(10)
        self.logo = QLabel()
        self.logo.setFixedSize(48, 48)
        head.addWidget(self.logo)
        titles = QVBoxLayout()
        titles.setSpacing(0)
        self.name = text_label(16, True)
        self.header = text_label(9)
        paint(self.header, None)
        self.header.setStyleSheet(f"color:{MUTED};")
        self.cup = text_label(9)
        self.cup.setStyleSheet(f"color:{MUTED};")
        titles.addWidget(self.name)
        titles.addWidget(self.header)
        titles.addWidget(self.cup)
        head.addLayout(titles, 1)
        club.addLayout(head)
        club.addSpacing(4)
        self.match = MatchStripe()
        club.addWidget(self.match)
        club.addSpacing(4)
        self.alert = text_label(9, True, YELLOW)
        self.alert.setWordWrap(True)
        club.addWidget(self.alert)
        self.facts = QGridLayout()
        self.facts.setHorizontalSpacing(10)
        self.facts.setVerticalSpacing(4)
        club.addLayout(self.facts)
        self.value = self._row(0, "Valor plantel")
        self.money = self._row(1, "Dinheiro")
        self.sales = text_label(8)  # a smaller line under the money, so the sale fits on one line with Sora
        self.sales.setWordWrap(True)
        self.facts.addWidget(self.sales, 2, 1, 1, 3)
        self.sponsors = self._row(3, "Patrocinadores")
        club.addSpacing(6)
        club.addWidget(column_title("ESTÁDIO"))
        stadium = QHBoxLayout()  # three small rings: the part going up fills, the others stand still (owner, 2026-10-09)
        stadium.setSpacing(22)
        stadium.addStretch(1)
        self.stadium_cells = [RingCell(54, 5, 9, lines=2) for _ in range(3)]
        for cell in self.stadium_cells:
            stadium.addWidget(cell)
        stadium.addStretch(1)
        club.addLayout(stadium)
        club.addStretch(1)
        left = QWidget()
        left.setLayout(club)
        left.setFixedWidth(345)
        row.addWidget(left)
        row.addWidget(divider())

        trainings = QVBoxLayout()
        trainings.setContentsMargins(16, 14, 16, 14)
        trainings.setSpacing(8)
        trainings.addWidget(column_title("TREINOS"))
        self.rings = QHBoxLayout()
        self.rings.setSpacing(10)
        trainings.addLayout(self.rings)
        trainings.addSpacing(10)
        care = QHBoxLayout()  # the doctor and the lawyer under the trainings (owner, 2026-10-09)
        care.setSpacing(24)
        self.care_cells = [RingCell(62, 5, 9, lines=3) for _ in range(2)]
        for cell in self.care_cells:
            care.addWidget(cell)
        care.addStretch(1)
        trainings.addLayout(care)
        trainings.addStretch(1)
        self.ring_cells: list[tuple[QWidget, Ring, QLabel, QLabel]] = []
        row.addLayout(trainings, 1)
        row.addWidget(divider())

        prep = QVBoxLayout()
        prep.setContentsMargins(18, 14, 18, 14)
        prep.setSpacing(3)
        self.prep_title = column_title()
        prep.addWidget(self.prep_title)
        prep.addSpacing(4)
        self.prep = text_label(11)
        prep.addWidget(self.prep)
        prep.addSpacing(8)
        self.tired = text_label(9, colour=YELLOW)
        self.tired.setWordWrap(True)
        prep.addWidget(self.tired)
        prep.addStretch(1)
        right = QWidget()
        right.setLayout(prep)
        right.setFixedWidth(235)
        row.addWidget(right)

    def _row(self, index: int, name: str) -> QLabel:
        title = text_label(9)
        title.setStyleSheet(f"color:{MUTED};")
        title.setText(tr(name))
        title.setFixedWidth(self.LABEL_WIDTH)
        value = text_label(10)
        value.setWordWrap(True)
        self.facts.addWidget(title, index, 0, Qt.AlignTop)
        self.facts.addWidget(value, index, 1, 1, 3)
        return value

    def set_logo(self, pixmap: QPixmap | None, colour: str | None = None) -> None:
        self.match.set_colour(colour)
        self.set_colour(colour)
        if pixmap is not None and not pixmap.isNull():
            self.logo.setPixmap(pixmap.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def set_colour(self, colour: str | None) -> None:
        """The club's colour, kept discreet (owner, 2026-10-10, option C): a thin line on top, a soft glow under it
        and the border; the plain card until the logo is in."""
        if not colour or colour == self.colour:
            return
        self.colour = colour
        c = QColor(colour)
        glow, border = (f"rgba({c.red()},{c.green()},{c.blue()},{alpha})" for alpha in (70, 90))
        self.setStyleSheet(f"QFrame#card {{ background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {glow}, "
                           f"stop:0.25 {CARD}, stop:1 {CARD}); border: 1px solid {border}; "
                           f"border-top: 3px solid {colour}; border-radius: 14px; }}")

    def show_club(self, club: dict) -> None:
        self.name.setText(club["name"])
        self.header.setText(tr(club["header"]))
        self.cup.setText(tr(f"🏆 {club['cup_line']}"))
        self.match.show_match(club["match"])
        self.alert.setVisible(bool(club["alert"]))
        self.alert.setText(f"❗ {tr(club['alert'])}")
        _, value, colour = club["facts"][2]
        self.value.setText(rich([(value, colour)]))
        self.money.setText(f"<b>{rich([(club['money'], None)])}</b>")
        self.sales.setVisible(bool(club["sales"]))
        self.sales.setText("<br>".join(rich([("✓ ", GREEN), (sale.removeprefix("✓ "), None)]).replace(" M<", "&nbsp;M<") for sale in club["sales"]))
        self.sponsors.setText(rich([club["sponsors"]]))
        rings = club["stadium_rings"]
        for index, cell in enumerate(self.stadium_cells):
            cell.setVisible(index < len(rings))
            if index < len(rings):
                ring = rings[index]
                arc, text = STADIUM_RING[ring["state"]]
                cell.ring.show_ring(ring["level"], ring["done"], arc, text)  # names and states go through say()
                moving = ring["state"] == "moving"
                cell.say((ring["name"], TEXT if moving else MUTED), (ring["left"], COLOURS[BLUE] if moving else MUTED))
        for cell, ring in zip(self.care_cells, club["care"]):
            arc, text = CARE_RING[ring["state"]]
            share = {"working": ring["done"], "ready": 1.0, "waiting": 1.0}.get(ring["state"], 0.0)
            nobody = ring["state"] == "none"  # nobody: the emoji of each one instead of "—" (owner, 2026-10-09)
            cell.ring.show_ring(CARE_EMOJI[ring["label"]] if nobody else tr(ring["centre"]), share, arc, text, emoji=nobody)
            cell.say((ring["label"], TEXT), (ring["name"], MUTED if ring["state"] == "none" else text), (ring["sub"], MUTED))
        self.prep_title.setText(tr(club["prep_title"]))
        self.prep.setText("<br>".join(rich([step]) for step in club["prep"]["steps"]) or rich([("—", GREY)]))
        self._show_trainings(club["trainings"])
        self.tired.setVisible(bool(club["tired"]))
        self.tired.setText(tr(f"⚠ Cansados: {club['tired']}"))

    def _show_trainings(self, rows: list) -> None:
        while len(self.ring_cells) < len(rows):
            cell = QWidget()
            column = QVBoxLayout(cell)
            column.setContentsMargins(0, 0, 0, 0)
            column.setSpacing(2)
            ring, name, pos = Ring(), text_label(10), text_label(8)
            pos.setStyleSheet(f"color:{MUTED};")
            for widget in (ring, name, pos):
                column.addWidget(widget, 0, Qt.AlignHCenter)
            self.rings.addWidget(cell)
            self.ring_cells.append((cell, ring, name, pos))
        for index, (cell, ring, name, pos) in enumerate(self.ring_cells):
            cell.setVisible(index < len(rows))
            if index >= len(rows):
                continue
            player, position, left, colour, done, skipped = rows[index]
            ring.set(tr(left), colour, done, skipped)
            name.setText(player)
            pos.setText(tr(position))


class Backdrop(QWidget):
    """The board's background (D-030): the stadium picture, filling the window, darkened so the boxes read well."""

    def __init__(self):
        super().__init__()
        self.picture = QPixmap(str(BACKGROUND_FILE)) if BACKGROUND_FILE.exists() else QPixmap()
        self.cache: QPixmap | None = None

    def resizeEvent(self, _event) -> None:
        self.cache = None

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        if self.picture.isNull():
            painter.fillRect(self.rect(), QColor(BACKGROUND))
            return
        if self.cache is None or self.cache.size() != self.size():
            scaled = self.picture.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            x, y = (scaled.width() - self.width()) // 2, (scaled.height() - self.height()) // 2
            self.cache = scaled.copy(x, y, self.width(), self.height())
        painter.drawPixmap(0, 0, self.cache)
        painter.fillRect(self.rect(), QColor(4, 6, 22, 120))


class Timeline(QWidget):
    """The timeline (D-030): "now" in the middle; above it what comes next, the soonest right above "now";
    below it what the bot already did, newest first, fading as it goes down."""

    ROW = 46
    NOW = 44
    TIME_WIDTH = 62

    def __init__(self):
        super().__init__()
        self.future: list[dict] = []
        self.past: list[dict] = []
        self.now_text = ""
        self.colours: list[str] = []
        self.setMinimumHeight(260)

    def set(self, timeline: dict, colours: list[str], now_text: str) -> None:
        self.future, self.past, self.colours, self.now_text = timeline["future"], timeline["past"], colours, now_text
        self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        width, centre = self.width(), self.height() / 2
        line_x = self.TIME_WIDTH + 14
        painter.setPen(QPen(QColor(LINE), 2))
        painter.drawLine(int(line_x), 0, int(line_x), self.height())
        top_of_now = centre - self.NOW / 2
        for index, event in enumerate(self.future):
            y = top_of_now - (index + 1) * self.ROW
            if y < 0:  # only whole rows
                break
            club = event.get("club")
            colour = self.colours[club] if club is not None and club < len(self.colours) else ACCENT
            self._row(painter, y, tr(event["left"]), tr(event["title"]), tr(event["sub"]), colour, 1.0, ACCENT_LIGHT, filled=False)
        for index, entry in enumerate(self.past):
            y = centre + self.NOW / 2 + index * self.ROW
            if y + self.ROW > self.height():
                break
            fade = max(0.18, 1 - 0.16 * (index + 1))
            self._row(painter, y, entry["time"], tr(entry["title"]), tr(entry["sub"]), MUTED, fade, MUTED, filled=True)
        pill = QRectF(4, top_of_now + 3, width - 8, self.NOW - 6)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(139, 140, 248, 60))
        painter.drawRoundedRect(pill, 10, 10)
        painter.setBrush(QColor(ACCENT))
        painter.drawEllipse(QRectF(line_x - 7, centre - 7, 14, 14))
        painter.setPen(QColor(ACCENT_LIGHT))
        painter.setFont(QFont(FONT, 8, QFont.Bold))
        painter.drawText(QRectF(4, top_of_now, self.TIME_WIDTH, self.NOW), Qt.AlignRight | Qt.AlignVCenter, tr("AGORA"))
        painter.setPen(QColor(TEXT))
        painter.setFont(QFont(FONT, 10, QFont.Bold))
        text = painter.fontMetrics().elidedText(tr(self.now_text), Qt.ElideRight, int(width - line_x - 30))
        painter.drawText(QRectF(line_x + 18, top_of_now, width - line_x - 24, self.NOW), Qt.AlignLeft | Qt.AlignVCenter, text)

    def _row(self, painter: QPainter, y: float, when: str, title: str, sub: str, colour: str, fade: float,
             time_colour: str, filled: bool) -> None:
        def tone(name: str) -> QColor:
            c = QColor(name)
            c.setAlphaF(fade)
            return c

        line_x = self.TIME_WIDTH + 14
        text_x = line_x + 18
        room = int(self.width() - text_x - 6)
        painter.setPen(tone(time_colour))
        painter.setFont(QFont(FONT, 10, QFont.Bold))
        painter.drawText(QRectF(0, y, self.TIME_WIDTH, self.ROW * 0.55), Qt.AlignRight | Qt.AlignVCenter, when)
        painter.setPen(QPen(tone(colour), 2.5))
        painter.setBrush(tone(colour) if filled else QColor(BACKGROUND))
        painter.drawEllipse(QRectF(line_x - 5, y + self.ROW * 0.275 - 5, 10, 10))
        painter.setPen(tone(TEXT))
        painter.setFont(QFont(FONT, 10))
        painter.drawText(QRectF(text_x, y, room, self.ROW * 0.55), Qt.AlignLeft | Qt.AlignVCenter,
                         painter.fontMetrics().elidedText(title, Qt.ElideRight, room))
        if sub:
            painter.setPen(tone(MUTED))
            painter.setFont(QFont(FONT, 8))
            painter.drawText(QRectF(text_x, y + self.ROW * 0.5, room, self.ROW * 0.4), Qt.AlignLeft | Qt.AlignVCenter,
                             painter.fontMetrics().elidedText(sub, Qt.ElideRight, room))


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
        self.setWindowTitle(tr("OSMbot — Avisos e erros"))
        layout = QVBoxLayout(self)
        self.table = make_table(["Hora", "Tipo", "Mensagem"], [70, 60])
        layout.addWidget(self.table)
        self.resize(760, 320)

    def show_notices(self, notices: list, again: bool = False) -> None:
        if self.table.rowCount() == len(notices) and not again:
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
BOARD_SIZE = QSize(1400, 800)
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
        title.setFont(QFont(FONT, 16, QFont.Bold))
        right.addWidget(title)
        right.addWidget(coloured(f"Versão {__version__}", GREY))
        text = QLabel(tr("Trabalha por ti no Online Soccer Manager: treinos, vídeos, estádio, patrocinadores, amigável e "
                         "análise antes do jogo, médico e advogado, e avisa das vagas na lista de transferências."))
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
        self.login_button = QPushButton(tr("Login"))
        self.quit_button = QPushButton(tr("Sair"))
        self.open_button = QPushButton(tr("Abrir"))
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
        """The board (D-030): on the stadium picture, the daily rewards and the bot's state on top; the clubs on the
        left (one per row, scrolling when 3 or 4 don't fit); the boss coins and the timeline on the right."""
        page = Backdrop()
        outer = QHBoxLayout(page)
        outer.setContentsMargins(14, 12, 14, 14)
        outer.setSpacing(14)

        main = QVBoxLayout()
        main.setSpacing(12)
        top = QFrame()
        top.setObjectName("card")
        bar = QHBoxLayout(top)
        bar.setContentsMargins(18, 9, 18, 9)
        bar.setSpacing(14)
        bar.addWidget(column_title("DIÁRIAS"))
        self.daily = text_label(10)
        bar.addWidget(self.daily)
        bar.addStretch(1)
        self.state_dot = text_label(10)
        self.state_text = text_label(10)
        bar.addWidget(self.state_dot)
        bar.addWidget(self.state_text)
        main.addWidget(top)

        inner = QWidget()
        inner.setAttribute(Qt.WA_TranslucentBackground)
        self.clubs_column = QVBoxLayout(inner)
        self.clubs_column.setContentsMargins(0, 0, 0, 0)
        self.clubs_column.setSpacing(12)
        self.clubs_column.addStretch(1)
        scroll = QScrollArea()  # 3 or 4 clubs may not fit: the clubs scroll, the rest stays
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(inner)
        scroll.setStyleSheet("QScrollArea, QScrollArea > QWidget > QWidget { background: transparent; }")
        self.panels: list[ClubCard] = []
        main.addWidget(scroll, 1)
        outer.addLayout(main, 1)

        side = QVBoxLayout()
        side.setSpacing(14)
        coins = QFrame()
        coins.setObjectName("coins")
        box = QVBoxLayout(coins)
        box.setContentsMargins(20, 14, 20, 14)
        box.setSpacing(0)
        box.addWidget(column_title("BOSS COINS"))
        line = QHBoxLayout()
        self.coins = text_label(28, True, YELLOW)
        self.coins_jump = text_label(14, True, GREEN)
        line.addWidget(self.coins)
        line.addWidget(self.coins_jump, 0, Qt.AlignBottom)
        line.addStretch()
        box.addLayout(line)
        self.coins_since = text_label(9)
        self.coins_since.setStyleSheet(f"color:{MUTED};")
        box.addWidget(self.coins_since)
        side.addWidget(coins)
        timeline = QFrame()
        timeline.setObjectName("card")
        column = QVBoxLayout(timeline)
        column.setContentsMargins(12, 12, 12, 12)
        column.addWidget(column_title("A SEGUIR"))
        self.timeline = Timeline()
        column.addWidget(self.timeline, 1)
        side.addWidget(timeline, 1)
        right = QWidget()
        right.setAttribute(Qt.WA_TranslucentBackground)
        right.setLayout(side)
        right.setFixedWidth(340)
        outer.addWidget(right)
        return page

    def _build_menu(self) -> None:
        style = self.style()
        self.menuBar().clear()
        self.start_action = QAction(style.standardIcon(QStyle.SP_MediaPlay), tr("Iniciar"), self, triggered=self.start_bot)
        self.stop_action = QAction(style.standardIcon(QStyle.SP_MediaStop), tr("Parar"), self, triggered=self.stop_bot)
        self.login_action = QAction(tr("Login"), self, triggered=self.do_login)
        self.notices_action = QAction(tr("Avisos e erros"), self, triggered=self.show_notices)
        self.reload_action = QAction(tr("Atualizar"), self, triggered=self.read_game)
        self.logs_action = QAction(tr("Pasta dos logs"), self, triggered=self.open_logs)
        self.failures_action = QAction(tr("Capturas das falhas"), self, triggered=self.open_failures)
        self.quit_action = QAction(tr("Sair"), self, triggered=self.quit_app)
        bot = self.menuBar().addMenu(tr("Bot"))
        for action in (self.start_action, self.stop_action, self.login_action):
            bot.addAction(action)
        bot.addSeparator()
        bot.addAction(self.quit_action)
        view = self.menuBar().addMenu(tr("Ver"))
        view.addAction(self.reload_action)
        view.addSeparator()
        for action in (self.notices_action, self.logs_action, self.failures_action):
            view.addAction(action)
        languages = self.menuBar().addMenu("Idioma / Language")  # the same in both languages, so it is always found (D-031)
        self.language_actions = {}
        for code, name in LANGUAGES.items():
            action = QAction(name, self, checkable=True, triggered=lambda _checked=False, code=code: self.choose_language(code))
            action.setChecked(code == language())
            languages.addAction(action)
            self.language_actions[code] = action
        self.menuBar().addMenu(tr("Ajuda")).addAction(QAction(tr("Sobre o OSMbot"), self, triggered=self.about))

    def _build_tray(self) -> None:
        self.tray_icons = {working: tray_icon(self.logo, working) for working in (True, False)}
        self.tray = QSystemTrayIcon(self.tray_icons[False], self)
        self._tray_menu()
        self.tray.activated.connect(lambda reason: self.show_window() if reason in (
            QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick) else None)
        self.tray.show()

    def _tray_menu(self) -> None:
        self.tray_menu = QMenu()
        self.tray_menu.addAction(QAction(tr("Abrir"), self, triggered=self.show_window))
        self.tray_toggle = QAction(tr("Iniciar"), self, triggered=self.toggle_bot)
        self.tray_menu.addAction(self.tray_toggle)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(self.quit_action)
        self.tray.setContextMenu(self.tray_menu)

    def choose_language(self, code: str) -> None:
        """Idioma / Language: remember the choice and show the window in it at once (D-031)."""
        set_language(code)
        page = self.pages.currentIndex()
        for index in reversed(range(self.pages.count())):
            widget = self.pages.widget(index)
            self.pages.removeWidget(widget)
            widget.deleteLater()
        self.panels = []
        for build in (self._build_start, self._build_loading, self._build_board):
            self.pages.addWidget(build())
        self._build_menu()
        self._tray_menu()
        self.notices_window.setWindowTitle(tr("OSMbot — Avisos e erros"))
        self.notices_window.table.setHorizontalHeaderLabels([tr(h) for h in ("Hora", "Tipo", "Mensagem")])
        self.notices_window.show_notices(self.payload.get("notices") or [], again=True)
        self.go(page)
        self.render()

    def go(self, page: int) -> None:
        """Show one face; the window takes that face's size (small for the start screen, big for the board)."""
        self.pages.setCurrentIndex(page)
        self.menuBar().setVisible(page == BOARD)
        if page == BOARD:
            self.setMinimumSize(1180, 600)
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
        self.tray_toggle.setText(tr("Parar" if working else "Iniciar"))
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
        self.session_label.setText(tr(session))
        paint(self.session_label, colour)
        if working:
            since = datetime.fromtimestamp(self.started_at).strftime("%H:%M") if self.started_at else "?"
            text = "A parar…" if self.stopping else f"A trabalhar desde {since}"
        elif self.busy or self.reading:
            text = "A ler o jogo…"
        else:
            text = "Parado"
        self.state_dot.setText("●")
        paint(self.state_dot, GREEN if working else GREY)
        if self.message and self.pages.currentIndex() == BOARD:  # a problem: said in red where the state is
            self.state_text.setText(tr(self.message))
            paint(self.state_text, RED)
        else:
            self.state_text.setText(tr(text))
            self.state_text.setStyleSheet(f"color:{MUTED};")
        self.tray.setToolTip(f"OSMbot · {tr(text)}")
        count = len(self.payload.get("notices") or [])
        self.notices_action.setText(tr(f"Avisos e erros ({count})" if count else "Avisos e erros"))

    # ---- the bot --------------------------------------------------------------------------------------------
    def open_board(self) -> None:
        """Abrir: show "loading", start the bot, and grow to the board when the game has been read."""
        if self.running() or self.busy:
            return
        self.message = ""
        self.loading_label.setText(tr("A carregar o jogo…"))
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
        notices = self.payload.get("notices") or []
        self.notices_window.show_notices(notices)
        self.refresh_state()
        if self.pages.currentIndex() != BOARD:
            return
        running = self.running()
        view = board_view(self.payload.get("snapshot"), self.payload.get("stats") if running else None, now,
                          self.payload.get("doing") if running else None, self.payload.get("history") if running else None)
        if not view:
            return
        self._show_clubs(view["clubs"])
        account = view["account"]
        self.coins.setText(account["coins"])
        self.coins_jump.setText(account["jump"])
        self.coins_since.setText(tr(account["since"]))
        self.daily.setText("&nbsp;&nbsp;&nbsp;".join(rich([part]) for part in view["daily"]) or rich([("—", GREY)]))
        if running:
            doing = view["timeline"]["now"] or "a trabalhar…"
        else:
            doing = "Parado · Bot → Iniciar para voltar a trabalhar"
        colours = [(self._logo(club)[1] or ACCENT) for club in view["clubs"]]
        self.timeline.set(view["timeline"], colours, doing)

    def _show_clubs(self, clubs: list[dict]) -> None:
        if len(self.panels) != len(clubs):
            for panel in self.panels:
                panel.deleteLater()
            self.panels = [ClubCard() for _ in clubs]
            for index, panel in enumerate(self.panels):
                self.clubs_column.insertWidget(index, panel)  # one per row (D-030); the stretch stays last
        for panel, club in zip(self.panels, clubs):
            panel.show_club(club)
            panel.set_logo(*self._logo(club))

    def _logo(self, club: dict) -> tuple[QPixmap | None, str | None]:
        """The club's logo and colour (match stripe, timeline dot); fetched in the background the first time (then kept on disk)."""
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
        if language() == "en":
            QMessageBox.about(self, tr("Sobre o OSMbot"),
                              f"<b>OSMbot {__version__}</b><br>Works for you in Online Soccer Manager: collects and starts the "
                              "trainings, watches the videos, upgrades the stadium, signs sponsors, does the friendly and the analysis "
                              "before the match, handles the doctor and the lawyer and tells you about free transfer-list slots."
                              "<br><br>Independent project, not linked to Gamebasics.")
            return
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
    load_font()
    app.setFont(QFont(FONT, 9))
    app.setStyleSheet(STYLE)
    (Path.home() / ".osmbot").mkdir(parents=True, exist_ok=True)
    load_language()
    lock = QLockFile(str(Path.home() / ".osmbot" / "window.lock"))
    if not lock.tryLock(100):
        QMessageBox.information(None, "OSMbot", tr("O OSMbot já está aberto (vê o ícone junto ao relógio)."))
        return
    window = MainWindow(app)
    window.winId()
    dark_title_bar(window)
    window.show()
    hide_own_console()
    app.exec()
    lock.unlock()
