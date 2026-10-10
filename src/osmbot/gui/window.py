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

from PySide6.QtCore import QLockFile, QObject, QPoint, QPointF, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtGui import QAction, QColor, QFont, QFontDatabase, QIcon, QImage, QPainter, QPainterPath, QPalette, QPen, QPixmap
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QLabel,
                               QMainWindow, QMenu, QMessageBox, QProxyStyle, QPushButton, QScrollArea, QStackedWidget, QStyle,
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
ASSETS = Path(__file__).resolve().parent / "assets"
COIN_FILE, FUNDS_FILE = ASSETS / "bosscoin.png", ASSETS / "clubfunds.png"  # the game's icons (owner accepted, 2026-10-10)
PICTURES = {"training": ASSETS / "training.png", "doctor": ASSETS / "doctor.png", "lawyer": ASSETS / "lawyer.png",
            "coins": COIN_FILE, "funds": FUNDS_FILE, "missions": ASSETS / "missions.png", "stadium": ASSETS / "stadium.png",
            "timer": ASSETS / "timer.svg", "ball": ASSETS / "ball.svg"}  # waiting, and a club's match (owner, 2026-10-10)
_pictures: dict[tuple[str, bool], QPixmap] = {}


def picture(name: str, grey: bool = False) -> QPixmap:
    """A picture for the inside of a ring (empty if the file is missing); ``grey``: washed out, for "nobody"."""
    if (name, grey) not in _pictures:
        path = PICTURES[name]
        if path.suffix == ".svg":  # drawn at 128 px, then scaled down like the others
            image = QImage(128, 128, QImage.Format_ARGB32)
            image.fill(Qt.transparent)
            svg = QPainter(image)
            svg.setRenderHint(QPainter.Antialiasing)
            QSvgRenderer(str(path)).render(svg)
            svg.end()
        else:
            image = QImage(str(path)).convertToFormat(QImage.Format_ARGB32)
        if grey and not image.isNull():
            for y in range(image.height()):
                for x in range(image.width()):
                    c = image.pixelColor(x, y)
                    level = int(c.red() * 0.3 + c.green() * 0.59 + c.blue() * 0.11)
                    image.setPixelColor(x, y, QColor(level, level, level, c.alpha() * 2 // 5))
        _pictures[name, grey] = QPixmap.fromImage(image)
    return _pictures[name, grey]
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
    f"QToolTip {{ background: #161b40; color: {TEXT}; border: 1px solid rgba(139, 140, 248, 110); padding: 5px 9px; }}"
)


class QuickTips(QProxyStyle):
    """Hover messages show almost at once (owner, 2026-10-10); they take the window's colours from ``STYLE``."""

    def styleHint(self, hint, option=None, widget=None, data=None):
        if hint == QStyle.SH_ToolTip_WakeUpDelay:
            return 60
        if hint == QStyle.SH_ToolTip_FallAsleepDelay:
            return 0
        return super().styleHint(hint, option, widget, data)


def soft(colour: str) -> str:
    """The club's colour half faded, for timers still running (owner, 2026-10-10): a green club stays apart from the
    bright green of "done"."""
    c, grey = QColor(colour), QColor(MUTED)
    return QColor((c.red() + grey.red()) // 2, (c.green() + grey.green()) // 2, (c.blue() + grey.blue()) // 2).name()


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


_reach: dict[int, float] = {}


def reach(pixmap: QPixmap) -> float:
    """How far the drawn (not transparent) part of a picture goes from its centre, as a share of half its diagonal:
    a picture is scaled by this to sit inside a ring, not over it (the training cone's wide base, owner 2026-10-10)."""
    key = pixmap.cacheKey()
    if key not in _reach:
        image = pixmap.toImage()
        w, h = image.width(), image.height()
        far = max(((x - w / 2) ** 2 + (y - h / 2) ** 2 for y in range(0, h, 2) for x in range(0, w, 2)
                   if image.pixelColor(x, y).alpha() > 40), default=0.0) ** 0.5
        _reach[key] = far / max(1.0, ((w / 2) ** 2 + (h / 2) ** 2) ** 0.5) or 1.0
    return _reach[key]


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
        self.hover: tuple[str, str] | None = None  # (text, colour) in the middle while the mouse is over the ring
        self.hovered = False
        self.picture: QPixmap | None = None  # drawn inside the ring instead of the text (owner, 2026-10-10)

    def set(self, text: str, colour: str | None, done: float, skipped: float = 0.0, timer: str = ACCENT) -> None:
        """A training: green and full when ready, else the club's timer colour (light blue for the skipped part)."""
        ready = colour == GREEN
        self.show_ring(text, 1.0 if ready else done, COLOURS[GREEN] if ready else timer,
                       COLOURS[GREEN] if ready else TEXT, 0.0 if ready else skipped)
        self.colour = colour

    def enterEvent(self, _event) -> None:
        self.hovered = True
        self.update()

    def leaveEvent(self, _event) -> None:
        self.hovered = False
        self.update()

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
        hovering = self.hovered and self.hover
        inside = box.adjusted(self.pen / 2 + 3, self.pen / 2 + 3, -self.pen / 2 - 3, -self.pen / 2 - 3)
        if self.picture is not None and not self.picture.isNull() and not hovering:  # on hover: only the time
            pic = self.picture.size()  # its drawn part fits the circle inside the ring, so it never covers the arc
            fit = inside.width() / (reach(self.picture) * (pic.width() ** 2 + pic.height() ** 2) ** 0.5)
            scaled = self.picture.scaled(int(pic.width() * fit), int(pic.height() * fit), Qt.KeepAspectRatio,
                                         Qt.SmoothTransformation)
            path = QPainterPath()
            path.addEllipse(inside)
            painter.setClipPath(path)
            painter.drawPixmap(int(inside.center().x() - scaled.width() / 2), int(inside.center().y() - scaled.height() / 2), scaled)
            return
        text, colour = self.hover if hovering else (self.text, self.text_colour)
        painter.setPen(QColor(colour))
        painter.setFont(QFont("Segoe UI Emoji", self.font_size + 7) if self.emoji else QFont(FONT, self.font_size, QFont.Bold))
        painter.drawText(self.rect(), Qt.AlignCenter, text)


class RingCell(QWidget):
    """A ring with a few lines under it (name, detail...)."""

    def __init__(self, size: int, width: int, font: int, lines: int = 2, cell_width: int = 0):
        super().__init__()
        if cell_width:
            self.setFixedWidth(cell_width)
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


class Mark(QWidget):
    """The red cross of an injury or the red card of a suspension, by the player's name (owner, 2026-10-10)."""

    def __init__(self, kind: str):
        super().__init__()
        self.kind = kind
        self.setFixedSize(11, 13)

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self.draw(painter, self.kind)

    @staticmethod
    def draw(painter: QPainter, kind: str) -> None:
        """The mark in an 11 x 13 box at the painter's origin."""
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#ff4d4d" if kind == "cross" else "#e8262b"))
        if kind == "cross":
            painter.drawRect(QRectF(3.5, 1.5, 4, 10))
            painter.drawRect(QRectF(0.5, 4.5, 10, 4))
        else:
            painter.drawRoundedRect(QRectF(1.5, 0.5, 8, 12), 1.5, 1.5)


class CareCell(QWidget):
    """The doctor or the lawyer (owner, 2026-10-10): the picture in the ring (washed out with nobody); under it the
    player with the cross / the red card and the games out; the time left in the middle on hover; what it is in a
    hover message."""

    def __init__(self, kind: str, width: int):
        super().__init__()
        self.kind = kind
        self.setFixedWidth(width)
        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(3)
        self.ring = Ring()
        column.addWidget(self.ring, 0, Qt.AlignHCenter)
        row = QHBoxLayout()
        row.setSpacing(4)
        self.name = text_label(9)
        self.mark = Mark("cross" if kind == "doctor" else "card")
        self.games = text_label(9, True)
        row.addStretch(1)
        for widget in (self.name, self.mark, self.games):
            row.addWidget(widget, 0, Qt.AlignVCenter)
        row.addStretch(1)
        self.under = QWidget()
        self.under.setLayout(row)
        row.setContentsMargins(0, 0, 0, 0)
        column.addWidget(self.under)

    def show_care(self, ring: dict, timer: str) -> None:
        state = ring["state"]
        nobody = state in ("none", "blocked")  # "not available": washed out (owner, 2026-10-10)
        arc = {"working": timer, "ready": COLOURS[GREEN], "waiting": COLOURS[YELLOW]}.get(state, RING_TRACK)
        share = {"working": ring["done"], "ready": 1.0, "waiting": 1.0}.get(state, 0.0)
        self.ring.show_ring("", share, arc, TEXT)
        self.ring.picture = picture(self.kind, grey=nobody)
        self.ring.hover = None if state == "none" else (tr(ring["centre"]), arc if state != "blocked" else MUTED)
        self.under.setVisible(state != "none")
        self.name.setText(escape_text(ring["name"]))
        self.games.setText(str(ring.get("games") or ""))
        self.games.setStyleSheet(f"color:{TEXT};")
        tip = tr(ring["label"]) + ("" if state == "none" else f" · {ring['name']} · {tr(ring['sub'])}")
        self.setToolTip(tip + (f" · {tr('acaba em')} {ring['centre']}" if state == "working" else ""))


class StepIcon(QWidget):
    """The mark of a pre-match step, all the same size (owner, 2026-10-10): done (green with a tick), waiting for
    the analyst (blue with a clock), to collect (yellow with "!"), still open (grey ring)."""

    COLOURS = {"done": GREEN, "waiting": BLUE, "collect": YELLOW, "open": GREY, "progress": YELLOW}

    def __init__(self, kind: str = "open"):
        super().__init__()
        self.kind = kind
        self.setFixedSize(16, 16)

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        colour = QColor(COLOURS[self.COLOURS[self.kind]])
        box = QRectF(1, 1, 14, 14)
        if self.kind in ("open", "progress"):  # a ring: still to do (grey) or under way (yellow)
            painter.setPen(QPen(colour, 1.6))
            painter.drawEllipse(box)
            return
        painter.setPen(Qt.NoPen)
        painter.setBrush(colour)
        painter.drawEllipse(box)
        mark = QColor("#0b0f2a")
        painter.setPen(QPen(mark, 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        if self.kind == "done":
            painter.drawPolyline([QPointF(4.6, 8.2), QPointF(7.0, 10.6), QPointF(11.4, 5.6)])
        elif self.kind == "waiting":
            painter.drawLine(QPointF(8, 8), QPointF(8, 4.6))
            painter.drawLine(QPointF(8, 8), QPointF(10.6, 9.4))
        else:
            painter.drawLine(QPointF(8, 4.2), QPointF(8, 8.8))
            painter.drawPoint(QPointF(8, 11.4))


class StepList(QWidget):
    """Steps as rows (pre-match) or side by side (the daily rewards): one ``StepIcon`` and the text each."""

    def __init__(self, vertical: bool, size: int, spacing: int):
        super().__init__()
        self.layout_ = QVBoxLayout(self) if vertical else QHBoxLayout(self)
        self.layout_.setContentsMargins(0, 0, 0, 0)
        self.layout_.setSpacing(spacing)
        self.size = size
        self.rows: list[tuple[QWidget, StepIcon, QLabel]] = []
        self.none = text_label(size, colour=GREY)
        self.none.setText("—")
        self.layout_.addWidget(self.none)
        if not vertical:
            self.layout_.addStretch(1)

    def show_steps(self, steps: list[tuple[str, str, str]]) -> None:
        """(kind, text already translated, colour) per step."""
        while len(self.rows) < len(steps):
            row = QWidget()
            line = QHBoxLayout(row)
            line.setContentsMargins(0, 0, 0, 0)
            line.setSpacing(8)
            mark, text = StepIcon(), text_label(self.size)
            line.addWidget(mark, 0, Qt.AlignVCenter)
            line.addWidget(text, 1, Qt.AlignVCenter)
            self.layout_.insertWidget(len(self.rows) + 1, row)
            self.rows.append((row, mark, text))
        self.none.setVisible(not steps)
        for index, (row, mark, text) in enumerate(self.rows):
            row.setVisible(index < len(steps))
            if index < len(steps):
                kind, words, colour = steps[index]
                mark.kind = kind
                mark.update()
                text.setText(rich([(words, colour)]))


def escape_text(text: str) -> str:
    from html import escape

    return escape(text)
STADIUM_RING = {"top": (COLOURS[GREEN], COLOURS[GREEN]), "still": ("#4a5080", MUTED)}  # "moving": the timer colour


def icon(path: Path, size: int) -> QLabel:
    """One of the bundled pictures at ``size`` px (an empty label if the file is missing)."""
    label = QLabel()
    label.setFixedSize(size, size)
    picture = QPixmap(str(path))
    if not picture.isNull():
        label.setPixmap(picture.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    label.setStyleSheet("background: transparent;")
    return label


class SaleArrow(QWidget):
    """A small green arrow going up by the money while a sale is on the card (owner, 2026-10-10); who and how much
    on hover."""

    def __init__(self):
        super().__init__()
        self.setFixedSize(14, 22)
        self.step = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._move)

    def show_sales(self, sales: list[str]) -> None:
        self.setVisible(bool(sales))
        from html import escape

        self.setToolTip("<br>".join(escape(tr(sale)) for sale in sales))
        if sales and not self.timer.isActive():
            self.timer.start(40)
        elif not sales:
            self.timer.stop()

    def _move(self) -> None:
        self.step = (self.step + 1) % 30
        self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        share = self.step / 30
        colour = QColor(COLOURS[GREEN])
        colour.setAlphaF(1 - share * 0.8)
        y = self.height() - 4 - share * 8
        painter.setPen(QPen(colour, 2.4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        middle = self.width() / 2
        painter.drawLine(int(middle), int(y), int(middle), int(y - 11))
        painter.drawLine(int(middle - 5), int(y - 6), int(middle), int(y - 11))
        painter.drawLine(int(middle + 5), int(y - 6), int(middle), int(y - 11))


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
        grid = QGridLayout(self)  # the tag on top; "vs Clube" and "em 3h33" on one line under it (owner, 2026-10-10)
        grid.setContentsMargins(14, 5, 14, 7)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(0)
        self.tag = text_label(7, True)
        self.text = ElidedLabel()
        self.text.setFont(QFont(FONT, 10))
        self.left = text_label(10)
        grid.addWidget(self.tag, 0, 0, 1, 2)
        grid.addWidget(self.text, 1, 0, Qt.AlignBottom)
        grid.addWidget(self.left, 1, 1, Qt.AlignRight | Qt.AlignBottom)
        grid.setColumnStretch(0, 1)
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


TRAINING_WIDTH = 104  # one column of the trainings and of the doctor/lawyer


class ClubCard(QFrame):
    """One club (D-030), three columns: the club (name, match, value, money, sponsors, stadium) · the trainings as
    rings · the pre-match checklist with the tired, injured and suspended players under it."""

    LABEL_WIDTH = 104

    def __init__(self):
        super().__init__()
        self.setObjectName("card")
        self.colour = ""
        self.timer = ACCENT  # running timers: the club's colour half faded once the logo is in
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
        name_row = QHBoxLayout()  # the name, and the money against the right edge with its icon (owner, 2026-10-10)
        name_row.setSpacing(6)
        self.name = ElidedLabel()
        self.name.setFont(QFont(FONT, 16, QFont.Bold))
        self.sale = SaleArrow()
        self.money = text_label(15, True)
        name_row.addWidget(self.name, 1)
        name_row.addWidget(self.sale, 0, Qt.AlignVCenter)
        name_row.addWidget(icon(FUNDS_FILE, 28), 0, Qt.AlignVCenter)
        name_row.addWidget(self.money, 0, Qt.AlignVCenter)
        self.header = text_label(9)
        paint(self.header, None)
        self.header.setStyleSheet(f"color:{MUTED};")
        self.cup = text_label(9)
        self.cup.setStyleSheet(f"color:{MUTED};")
        titles.addLayout(name_row)
        titles.addWidget(self.header)
        titles.addWidget(self.cup)
        head.addLayout(titles, 1)
        club.addLayout(head)
        club.addSpacing(4)
        self.match = MatchStripe()
        club.addWidget(self.match)
        club.addSpacing(4)
        self.facts = QGridLayout()
        self.facts.setHorizontalSpacing(10)
        self.facts.setVerticalSpacing(4)
        club.addLayout(self.facts)
        self.value = self._row(0, "Valor plantel")
        self.sponsors = self._row(1, "Patrocinadores")
        self.alert = text_label(10, True, YELLOW)  # a free transfer-list slot, under the sponsors (owner, 2026-10-10)
        self.alert.setWordWrap(True)
        self.facts.addWidget(self.alert, 2, 0, 1, 4)
        club.addSpacing(6)
        club.addWidget(column_title("ESTÁDIO"))
        stadium = QHBoxLayout()  # three small rings: the part going up fills, the others stand still (owner, 2026-10-09)
        stadium.setSpacing(6)
        stadium.addStretch(1)
        self.stadium_cells = [RingCell(54, 5, 9, lines=1, cell_width=92) for _ in range(3)]
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
        self.rings.setAlignment(Qt.AlignLeft)  # in columns with the doctor and the lawyer under them
        trainings.addLayout(self.rings)
        trainings.addSpacing(10)
        care = QHBoxLayout()  # the doctor and the lawyer under the trainings, in the same columns (owner, 2026-10-10)
        care.setSpacing(10)
        self.care_cells = [CareCell(kind, TRAINING_WIDTH) for kind in ("doctor", "lawyer")]
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
        self.prep = StepList(vertical=True, size=10, spacing=9)  # one row per step: icon and text (owner, 2026-10-10)
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
        value = text_label(10, True)
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
        self.colour, self.timer = colour, soft(colour)
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
        self.alert.setText(f"⚠ {tr(club['alert'])}")
        squad = club["squad"]  # the place in colour, the total in white; players and average on hover
        gap = "&nbsp;&nbsp;&nbsp;" if squad["place"] else ""
        self.value.setText(rich([(squad["place"], squad["colour"])]) + gap + rich([(squad["total"], None if squad["place"] else GREY)]))
        self.value.setToolTip(tr(squad["tip"]))
        self.money.setText(rich([(club["money"], None)]))
        self.sale.show_sales(club["sales"])
        sponsors = club["sponsors"]
        self.sponsors.setText(rich([(sponsors["text"], sponsors["colour"])]))
        self.sponsors.setToolTip(tr(sponsors["tip"]))
        rings = club["stadium_rings"]
        for index, cell in enumerate(self.stadium_cells):
            cell.setVisible(index < len(rings))
            if index < len(rings):
                ring = rings[index]  # only the name under it; on hover the middle says MAX or the time left
                moving = ring["state"] == "moving"
                arc, text = (self.timer, TEXT) if moving else STADIUM_RING[ring["state"]]
                cell.ring.show_ring(ring["level"], ring["done"], arc, text)
                cell.ring.hover = ((ring["left"], TEXT) if moving else ("MAX", COLOURS[GREEN]) if ring["state"] == "top"
                                   else None)
                cell.say((ring["name"], TEXT if moving else MUTED))
        for cell, ring in zip(self.care_cells, club["care"]):
            cell.show_care(ring, self.timer)
        self.prep_title.setText(tr(club["prep_title"]))
        self._show_prep(club["prep"]["steps"])
        self._show_trainings(club["trainings"])
        self.tired.setVisible(bool(club["tired"]))
        self.tired.setText(tr(f"⚠ Cansados: {club['tired']}"))

    def _show_prep(self, steps: list) -> None:
        self.prep.show_steps([(kind, tr(name) + (f" {tr(extra)}" if extra else ""), StepIcon.COLOURS[kind])
                              for kind, name, extra in steps])

    def _show_trainings(self, rows: list) -> None:
        while len(self.ring_cells) < len(rows):
            cell = QWidget()
            cell.setFixedWidth(TRAINING_WIDTH)
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
            ring.set(tr(left), colour, done, skipped, self.timer)  # the cone inside; the time on hover (owner, 2026-10-10)
            ring.picture = picture("training")
            ring.hover = (tr(left), COLOURS[GREEN] if colour == GREEN else TEXT)
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
    ICON = 26  # the event's picture (owner, 2026-10-10: bigger)
    LOGO = 14  # the club's logo before its name on a club's event (owner, 2026-10-10: option A)

    def __init__(self):
        super().__init__()
        self.future: list[dict] = []
        self.past: list[dict] = []
        self.now_text = ""
        self.colours: list[str] = []
        self.logos: list[QPixmap | None] = []
        self.setMinimumHeight(260)

    def set(self, timeline: dict, colours: list[str], now_text: str, logos: list[QPixmap | None] | None = None) -> None:
        self.future, self.past, self.colours, self.now_text = timeline["future"], timeline["past"], colours, now_text
        self.logos = logos or []
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
            logo = self.logos[club] if club is not None and club < len(self.logos) else None
            self._row(painter, y, tr(event["left"]), tr(event["title"]), tr(event["sub"]), colour, 1.0, ACCENT_LIGHT,
                      filled=False, icon=event.get("icon", ""), logo=logo)
        for index, entry in enumerate(self.past):
            y = centre + self.NOW / 2 + index * self.ROW
            if y + self.ROW > self.height():
                break
            fade = max(0.18, 1 - 0.16 * (index + 1))
            self._row(painter, y, entry["time"], tr(entry["title"]), tr(entry["sub"]), MUTED, fade, MUTED, filled=True,
                      icon=entry.get("icon", ""))
        pill = QRectF(4, top_of_now + 3, width - 8, self.NOW - 6)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(139, 140, 248, 60))
        painter.drawRoundedRect(pill, 10, 10)
        if self.now_text == "à espera":  # the bot waits: the timer on the line (owner, 2026-10-10)
            timer = picture("timer").scaled(self.ICON + 4, self.ICON + 4, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            painter.drawPixmap(int(line_x - timer.width() / 2), int(centre - timer.height() / 2), timer)
        else:
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
             time_colour: str, filled: bool, icon: str = "", logo: QPixmap | None = None) -> None:
        def tone(name: str) -> QColor:
            c = QColor(name)
            c.setAlphaF(fade)
            return c

        line_x = self.TIME_WIDTH + 14
        text_x = line_x + 22
        room = int(self.width() - text_x - 6)
        painter.setPen(tone(time_colour))
        painter.setFont(QFont(FONT, 10, QFont.Bold))
        painter.drawText(QRectF(0, y, self.TIME_WIDTH, self.ROW * 0.55), Qt.AlignRight | Qt.AlignVCenter, when)
        middle = QPointF(line_x, y + self.ROW * 0.275)
        if icon:  # the kind of event as a picture on the line (owner, 2026-10-10)
            painter.setOpacity(fade)
            if icon in ("cross", "card"):
                painter.save()
                painter.translate(middle.x(), middle.y())
                painter.scale(1.8, 1.8)
                painter.translate(-5.5, -6.5)
                Mark.draw(painter, icon)
                painter.restore()
            else:
                picture_ = picture(icon).scaled(self.ICON, self.ICON, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                painter.drawPixmap(int(middle.x() - picture_.width() / 2), int(middle.y() - picture_.height() / 2), picture_)
            painter.setOpacity(1.0)
        else:
            painter.setPen(QPen(tone(colour), 2.5))
            painter.setBrush(tone(colour) if filled else QColor(BACKGROUND))
            painter.drawEllipse(QRectF(line_x - 5, y + self.ROW * 0.275 - 5, 10, 10))
        painter.setPen(tone(TEXT))
        painter.setFont(QFont(FONT, 10))
        painter.drawText(QRectF(text_x, y, room, self.ROW * 0.55), Qt.AlignLeft | Qt.AlignVCenter,
                         painter.fontMetrics().elidedText(title, Qt.ElideRight, room))
        if sub:
            sub_x = text_x
            if logo is not None and not logo.isNull():  # whose event: the club's logo, small, before the line
                small = logo.scaled(self.LOGO, self.LOGO, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                painter.setOpacity(fade)
                painter.drawPixmap(int(sub_x), int(y + self.ROW * 0.7 - small.height() / 2), small)
                painter.setOpacity(1.0)
                sub_x += self.LOGO + 4
            painter.setPen(tone(MUTED))
            painter.setFont(QFont(FONT, 8))
            painter.drawText(QRectF(sub_x, y + self.ROW * 0.5, room - (sub_x - text_x), self.ROW * 0.4),
                             Qt.AlignLeft | Qt.AlignVCenter,
                             painter.fontMetrics().elidedText(sub, Qt.ElideRight, int(room - (sub_x - text_x))))


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

    GAP = 14  # board: between the clubs and the right column
    SIDE = 340  # board: the right column (boss coins, timeline)

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
        whole = QVBoxLayout(page)  # the top bar across the whole width: the boss coins start level with the first
        whole.setContentsMargins(14, 12, 14, 14)  # club (owner, 2026-10-10)
        whole.setSpacing(12)
        outer = QHBoxLayout()
        outer.setSpacing(self.GAP)

        main = QVBoxLayout()
        main.setSpacing(12)
        top = QFrame()
        top.setObjectName("card")
        bar = QHBoxLayout(top)
        bar.setContentsMargins(18, 9, 18, 9)
        bar.setSpacing(14)
        bar.addWidget(column_title("DIÁRIAS"))
        self.daily = StepList(vertical=False, size=10, spacing=18)  # the same icons as the pre-match (owner, 2026-10-10)
        bar.addWidget(self.daily, 1)
        bar.addStretch(1)
        self.state_dot = text_label(10)
        self.state_text = text_label(10)
        bar.addWidget(self.state_dot)
        bar.addWidget(self.state_text)
        whole.addWidget(top)
        whole.addLayout(outer, 1)

        inner = QWidget()
        inner.setAttribute(Qt.WA_TranslucentBackground)
        self.clubs_column = QVBoxLayout(inner)
        self.clubs_column.setContentsMargins(0, 0, 0, 0)
        self.clubs_column.setSpacing(12)  # no stretch: the cards share the spare height and end level with the timeline
        self.clubs_scroll = scroll = QScrollArea()  # 3 or 4 clubs may not fit: the clubs scroll, the rest stays
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(inner)
        scroll.setStyleSheet("QScrollArea, QScrollArea > QWidget > QWidget { background: transparent; }")
        self.panels: list[ClubCard] = []
        main.addWidget(scroll, 1)
        outer.addLayout(main, 1)

        side = QVBoxLayout()
        side.setContentsMargins(0, 0, 0, 0)  # level with the clubs and the top bar
        side.setSpacing(14)
        coins = QFrame()
        coins.setObjectName("coins")
        across = QHBoxLayout(coins)  # the numbers on the left, the boss coin big on the right (owner, 2026-10-10)
        across.setContentsMargins(20, 14, 16, 14)
        box = QVBoxLayout()
        box.setSpacing(0)
        box.addWidget(column_title("BOSS COINS"))
        line = QHBoxLayout()
        line.setSpacing(8)
        self.coins = text_label(28, True, YELLOW)
        self.coins_jump = text_label(14, True, GREEN)
        line.addWidget(self.coins)
        line.addWidget(self.coins_jump, 0, Qt.AlignVCenter)
        line.addStretch()
        box.addLayout(line)
        self.coins_since = text_label(9)
        self.coins_since.setStyleSheet(f"color:{MUTED};")
        box.addWidget(self.coins_since)
        across.addLayout(box, 1)
        across.addWidget(icon(COIN_FILE, 64), 0, Qt.AlignVCenter)
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
        right.setFixedWidth(self.SIDE)
        outer.addWidget(right)
        return page

    def _build_menu(self) -> None:
        style = self.style()
        self.menuBar().clear()
        self.start_action = QAction(style.standardIcon(QStyle.SP_MediaPlay), tr("Iniciar"), self, triggered=self.start_bot)
        self.stop_action = QAction(style.standardIcon(QStyle.SP_MediaStop), tr("Parar"), self, triggered=self.stop_bot)
        self.login_action = QAction(tr("Login"), self, triggered=self.do_login)
        self.notices_action = QAction(tr("Avisos e erros"), self, triggered=self.show_notices)
        self.reload_action = QAction(tr("Atualizar"), self, triggered=lambda: self.read_game(fresh=True))
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

    def read_game(self, fresh: bool = False) -> None:
        """Ver → Atualizar (and every 3 min): read the game now, GETs only, beside the bot and never waiting for it.
        ``fresh`` (the menu): forget the slow reads kept for a while (squad values, fixtures) and read them again."""
        from osmbot.game.browser import STATE_FILE

        if self.reading or self.busy or not STATE_FILE.exists():
            return
        if fresh:
            from osmbot.game.clubinfo import forget

            forget()
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
        self.daily.show_steps([(kind, tr(text), colour) for kind, text, colour in view["daily"]])
        if running:
            doing = view["timeline"]["now"] or "a trabalhar…"
        else:
            doing = "Parado · Bot → Iniciar para voltar a trabalhar"
        logos = [self._logo(club) for club in view["clubs"]]
        colours = [soft(colour or ACCENT) for _, colour in logos]  # timers: half faded
        self.timeline.set(view["timeline"], colours, doing, [pixmap for pixmap, _ in logos])

    def _show_clubs(self, clubs: list[dict]) -> None:
        if len(self.panels) != len(clubs):
            for panel in self.panels:
                panel.deleteLater()
            self.panels = [ClubCard() for _ in clubs]
            for index, panel in enumerate(self.panels):
                self.clubs_column.addWidget(panel, 1)  # one per row (D-030)
        for panel, club in zip(self.panels, clubs):
            panel.set_logo(*self._logo(club))  # first: the timers take the club's colour
            panel.show_club(club)
        QTimer.singleShot(0, self._fit_width)  # once the cards are laid out

    def _fit_width(self) -> None:
        """Never narrower than a card (with room for the scroll bar): the window can't be made so narrow that the
        cards' right side is cut off (owner, 2026-10-10). A window already narrower grows to it."""
        widest = max((panel.minimumSizeHint().width() for panel in self.panels), default=0)
        need = widest + self.clubs_scroll.verticalScrollBar().sizeHint().width()
        self.clubs_scroll.setMinimumWidth(need)
        margin = self.clubs_scroll.mapTo(self, QPoint(0, 0)).x()  # the same on the right of the boss coins
        self.setMinimumWidth(margin + need + self.GAP + self.SIDE + margin)

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
    app.setStyle(QuickTips("Fusion"))
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
