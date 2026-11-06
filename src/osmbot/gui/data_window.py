"""Ver → Dados (owner, 2026-11-06): the logged matches studied in the board's look. Reads only ``logs/*/jogos`` and
``logs/*/analista`` on this PC; never talks to the game. The sums are ``osmbot.analysis.data`` (pure, tested).

Two sides, A and its rival B, each with its filters (who, human or the computer, formation, style, tackling, marking,
offside trap; the sliders and lines only for the owner's clubs), and filters for both (league, period, competition,
ground, strength). For what is kept: the win/draw/loss odds the squads' strength gave against what happened, the EV
(points won minus the points the odds gave), goals, shots, possession, both squads' strength, and three tables:
patterns (each value of each field of side A), matchups (formation and style against the rival's) and the matches.
Every number shows how many matches are behind it; few matches swing a lot.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath
from PySide6.QtWidgets import (QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
                               QSizePolicy, QTabWidget, QVBoxLayout, QWidget)

from osmbot import logs
from osmbot.analysis import data
from osmbot.i18n import tr
from osmbot.gui.view import GREEN, GREY, RED, YELLOW
from osmbot.gui import window as w

WIN, DRAW, LOSS = "#5cd17a", "#8f95b8", "#ff6b6b"
LEAGUE_LABEL = "Liga {n}"
STYLE = (
    "QComboBox { background: rgba(26, 32, 82, 230); color: #eef0ff; border: 1px solid rgba(139, 140, 248, 70);"
    " border-radius: 7px; padding: 3px 8px; min-height: 20px; }"
    "QComboBox:hover { border-color: rgba(139, 140, 248, 160); }"
    "QComboBox::drop-down { border: none; width: 18px; }"
    "QComboBox QAbstractItemView { background: #161b40; color: #eef0ff; selection-background-color: #3a3f8a;"
    " border: 1px solid rgba(139, 140, 248, 110); outline: none; }"
    "QPushButton { background: rgba(139, 140, 248, 60); color: #eef0ff; border: 1px solid rgba(139, 140, 248, 120);"
    " border-radius: 8px; padding: 5px 14px; }"
    "QPushButton:hover { background: rgba(139, 140, 248, 110); }"
    "QTabWidget::pane { border: none; }"
    "QTabBar::tab { background: transparent; color: #8f95b8; padding: 6px 14px; border: none;"
    " border-bottom: 2px solid transparent; font-weight: bold; }"
    "QTabBar::tab:selected { color: #eef0ff; border-bottom: 2px solid #8b8cf8; }"
    "QTabBar::tab:hover { color: #b9baff; }"
    "QTableWidget { background: transparent; alternate-background-color: rgba(139, 140, 248, 14); color: #eef0ff;"
    " border: none; }"
    "QHeaderView::section { background: transparent; color: #8f95b8; border: none;"
    " border-bottom: 1px solid #2d3366; padding: 3px 6px; font-weight: bold; }"
    "QLabel { background: transparent; }"
)


TABLE_STYLE = (
    "QTableWidget { background: transparent; alternate-background-color: rgba(139, 140, 248, 14); color: #eef0ff;"
    " border: none; }"
    "QHeaderView::section { background: rgba(11, 15, 42, 200); color: #8f95b8; border: none;"
    " border-bottom: 1px solid #2d3366; padding: 3px 6px; font-weight: bold; }"
    "QTableCornerButton::section { background: transparent; border: none; }"
)


def read_records(kind: str, root: Path | None = None) -> list[dict]:
    """Every line of ``logs/*/<kind>/*.jsonl`` (all PCs' folders that are here)."""
    root = root or logs.repo_folder()
    found = []
    if root is None:
        return found
    for path in sorted((root / "logs").glob(f"*/{kind}/*.jsonl")):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines():
            try:
                found.append(json.loads(line))
            except ValueError:
                pass
    return found


class OddsBar(QWidget):
    """Win / draw / loss in one rounded bar, the share written inside each part (D-030 look)."""

    def __init__(self):
        super().__init__()
        self.parts: tuple[float, float, float] | None = None
        self.setFixedHeight(26)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def sizeHint(self) -> QSize:
        return QSize(360, 26)

    def set(self, parts) -> None:
        self.parts = parts
        self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        box = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        clip = QPainterPath()
        clip.addRoundedRect(box, 8, 8)
        painter.setClipPath(clip)
        painter.fillRect(box, QColor(w.RING_TRACK))
        if not self.parts:
            return
        x = box.x()
        font = QFont(w.FONT, 9)
        font.setBold(True)
        painter.setFont(font)
        for share, colour in zip(self.parts, (WIN, DRAW, LOSS)):
            width = box.width() * share
            part = QRectF(x, box.y(), width, box.height())
            painter.fillRect(part, QColor(colour))
            if width > 34:
                painter.setPen(QColor("#0b0f2a"))
                painter.drawText(part, Qt.AlignCenter, f"{share * 100:.0f}%")
            x += width


def card(name: str = "card") -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName(name)
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(16, 12, 16, 14)
    layout.setSpacing(8)
    return frame, layout


def signed(value: float | None, digits: int = 2) -> str:
    return "—" if value is None else f"{value:+.{digits}f}"


def plain(value: float | None, digits: int = 1, suffix: str = "") -> str:
    return "—" if value is None else f"{value:.{digits}f}{suffix}"


def ev_colour(ev: float | None) -> str:
    return w.COLOURS[GREY] if ev is None or abs(ev) < 0.05 else w.COLOURS[GREEN] if ev > 0 else w.COLOURS[RED]


class SideFilters(QFrame):
    """One side's filters: who, manager, the tactic's fields (and the owner's sliders and lines for side A)."""

    def __init__(self, title: str, clubs: list[str], rows: list, rival: bool, changed):
        super().__init__()
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 14)
        layout.setSpacing(6)
        layout.addWidget(w.column_title(title))
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(6)
        self.boxes: dict[str, QComboBox] = {}
        fields = [("quem", "Quem", ["Todos", "Os meus clubes", "Outros clubes"] + clubs),
                  ("treinador", "Treinador", [data.ANY, "Humano", "Computador"])]
        fields += [(key, name, [data.ANY] + data.choices(rows, key, rival)) for key, name in data.TACTIC_FIELDS]
        if not rival:
            fields += [(key, name, [data.ANY] + data.choices(rows, key)) for key, name in data.OWN_FIELDS]
        for i, (key, name, options) in enumerate(fields):
            if i == len(data.TACTIC_FIELDS) + 2:
                note = w.text_label(8, colour=GREY)
                note.setText(tr("Só nos jogos dos teus clubes"))
                grid.addWidget(note, i, 0, 1, 2)
            row = i + (1 if i >= len(data.TACTIC_FIELDS) + 2 else 0)
            label = w.text_label(9, colour=GREY)
            label.setText(tr(name))
            box = QComboBox()
            for option in options:
                box.addItem(tr(option), option)
            box.currentIndexChanged.connect(changed)
            grid.addWidget(label, row, 0)
            grid.addWidget(box, row, 1)
            self.boxes[key] = box
        grid.setColumnStretch(1, 1)
        layout.addLayout(grid)

    def wanted(self) -> dict:
        found = {key: box.currentData() for key, box in self.boxes.items()}
        if found.get("quem") == "Todos":
            found["quem"] = None
        return found

    def reset(self) -> None:
        for box in self.boxes.values():
            box.blockSignals(True)
            box.setCurrentIndex(0)
            box.blockSignals(False)


class DataWindow(QWidget):
    """Ver → Dados."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle(tr("OSMbot — Dados"))
        self.setStyleSheet(STYLE)
        self.resize(1360, 860)
        self.rows = data.rows(read_records("jogos"), read_records("analista"))
        self.read_at = datetime.now()
        back = w.Backdrop()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(back)
        whole = QVBoxLayout(back)
        whole.setContentsMargins(16, 14, 16, 14)
        whole.setSpacing(12)
        self.timer = QTimer(self, singleShot=True, interval=60, timeout=self.refresh)
        whole.addWidget(self._top())
        body = QHBoxLayout()
        body.setSpacing(12)
        whole.addLayout(body, 1)

        left = QWidget()
        left.setAttribute(Qt.WA_TranslucentBackground)
        column = QVBoxLayout(left)
        column.setContentsMargins(0, 0, 4, 0)
        column.setSpacing(12)
        clubs = sorted({r.club for r in self.rows if r.mine})
        self.side_a = SideFilters("LADO A", clubs, self.rows, False, self.later)
        self.side_b = SideFilters("LADO B · ADVERSÁRIO", clubs, self.rows, True, self.later)
        column.addWidget(self.side_a)
        column.addWidget(self.side_b)
        clear = QPushButton(tr("Limpar filtros"))
        clear.clicked.connect(self.clear)
        column.addWidget(clear)
        column.addStretch(1)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea, QScrollArea > QWidget > QWidget { background: transparent; }")
        scroll.setWidget(left)
        scroll.setFixedWidth(330)
        body.addWidget(scroll)

        right = QVBoxLayout()
        right.setSpacing(12)
        right.addWidget(self._result())
        right.addWidget(self._tables(), 1)
        body.addLayout(right, 1)
        self.refresh()

    # --- building --------------------------------------------------------------------------------------------

    def _combo(self, options: list[tuple[str, str]]) -> QComboBox:
        box = QComboBox()
        for label, value in options:
            box.addItem(tr(label), value)
        box.currentIndexChanged.connect(self.later)
        return box

    def _top(self) -> QFrame:
        top = QFrame()
        top.setObjectName("card")
        bar = QHBoxLayout(top)
        bar.setContentsMargins(18, 10, 18, 10)
        bar.setSpacing(10)
        titles = QVBoxLayout()
        titles.setSpacing(0)
        title = w.text_label(13, True)
        title.setText(tr("Dados dos jogos"))
        self.counts = w.text_label(8, colour=GREY)
        titles.addWidget(title)
        titles.addWidget(self.counts)
        bar.addLayout(titles)
        bar.addStretch(1)
        mine = {}
        for r in self.rows:
            if r.mine:
                mine.setdefault(r.league, set()).add(r.club)
        leagues = sorted({r.league for r in self.rows}, key=lambda x: (x not in mine, x))
        self.league = self._combo([("Todas as ligas", data.ANY)]
                                  + [(f"Liga de {' / '.join(sorted(mine[x]))}" if x in mine else LEAGUE_LABEL.format(n=x), x)
                                     for x in leagues])
        self.period = self._combo([(p, p) for p in data.PERIODS])
        self.kind = self._combo([("Liga e taça", data.ANY), ("Liga", "liga"), ("Taça", "taça")])
        self.ground = self._combo([("Casa e fora (lado A)", data.ANY), ("Em casa", "Casa"), ("Fora", "Fora"),
                                   ("Campo neutro", "Neutro")])
        self.strength = self._combo([(f"Força: {s}" if s == "Qualquer" else f"A {s[0].lower()}{s[1:]}", s)
                                     for s in data.STRENGTH_BANDS])
        for box in (self.league, self.period, self.kind, self.ground, self.strength):
            bar.addWidget(box)
        return top

    def _result(self) -> QFrame:
        frame, layout = card()
        head = QHBoxLayout()
        head.setSpacing(16)
        left = QVBoxLayout()
        left.setSpacing(2)
        self.games = w.text_label(22, True)
        self.games_note = w.text_label(8, colour=GREY)
        left.addWidget(self.games)
        left.addWidget(self.games_note)
        head.addLayout(left)
        head.addStretch(1)
        right = QVBoxLayout()
        right.setSpacing(2)
        self.ev = w.text_label(22, True)
        self.ev.setAlignment(Qt.AlignRight)
        self.ev_note = w.text_label(8, colour=GREY)
        self.ev_note.setAlignment(Qt.AlignRight)
        right.addWidget(self.ev)
        right.addWidget(self.ev_note)
        head.addLayout(right)
        layout.addLayout(head)

        bars = QGridLayout()
        bars.setHorizontalSpacing(12)
        bars.setVerticalSpacing(6)
        self.odds_bar, self.real_bar = OddsBar(), OddsBar()
        self.odds_text, self.real_text = w.text_label(9, colour=GREY), w.text_label(9, colour=GREY)
        for row, (name, bar, text) in enumerate((("Esperado pela força", self.odds_bar, self.odds_text),
                                                  ("O que aconteceu", self.real_bar, self.real_text))):
            label = w.text_label(9)
            label.setText(tr(name))
            label.setFixedWidth(140)
            bars.addWidget(label, row, 0)
            bars.addWidget(bar, row, 1)
            text.setFixedWidth(170)
            bars.addWidget(text, row, 2)
        bars.setColumnStretch(1, 1)
        layout.addLayout(bars)
        legend = w.text_label(8, colour=GREY)
        legend.setText(f"<span style='color:{WIN}'>■</span> {tr('vitória')} &nbsp; <span style='color:{DRAW}'>■</span> "
                       f"{tr('empate')} &nbsp; <span style='color:{LOSS}'>■</span> {tr('derrota')}")
        layout.addWidget(legend)

        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet(f"background:{w.LINE};")
        layout.addWidget(line)
        stats = QGridLayout()
        stats.setHorizontalSpacing(28)
        stats.setVerticalSpacing(4)
        self.stat_cells: dict[str, tuple[QLabel, QLabel]] = {}
        names = (("goals", "Golos por jogo"), ("shots", "Remates"), ("possession", "Posse de bola"),
                 ("strength", "Força do jogo"), ("eleven", "Média do onze"))
        head_a, head_b = w.column_title("LADO A"), w.column_title("LADO B")
        stats.addWidget(head_a, 0, 1, Qt.AlignRight)
        stats.addWidget(head_b, 0, 2, Qt.AlignRight)
        for i, (key, name) in enumerate(names, start=1):
            label = w.text_label(9, colour=GREY)
            label.setText(tr(name))
            a, b = w.text_label(10, True), w.text_label(10, True)
            a.setAlignment(Qt.AlignRight)
            b.setAlignment(Qt.AlignRight)
            stats.addWidget(label, i, 0)
            stats.addWidget(a, i, 1)
            stats.addWidget(b, i, 2)
            self.stat_cells[key] = (a, b)
        stats.setColumnStretch(3, 1)
        self.edge = w.text_label(9, colour=GREY)
        self.edge.setWordWrap(True)
        self.edge.setMinimumWidth(260)
        stats.addWidget(self.edge, 1, 3, len(names), 1, Qt.AlignTop | Qt.AlignRight)
        layout.addLayout(stats)
        return frame

    def _tables(self) -> QFrame:
        frame, layout = card()
        layout.setContentsMargins(10, 6, 10, 10)
        self.tabs = QTabWidget()
        self.patterns = w.make_table(["Campo (lado A)", "Valor", "Jogos", "Pts/jogo", "EV"], [150, 190, 70, 80])
        self.matchups = w.make_table(["Lado A", "Lado B", "Jogos", "EV"], [230, 230, 70])
        self.matches = w.make_table(["Data", "Lado A", "", "Res.", "Lado B", "Força", "Táticas (A × B)", "Pts", "EV"],
                                    [82, 140, 60, 50, 150, 80, 400, 36])
        for table, name in ((self.patterns, "Padrões"), (self.matchups, "Confrontos"), (self.matches, "Jogos")):
            table.setStyleSheet(TABLE_STYLE)
            self.tabs.addTab(table, tr(name))
        layout.addWidget(self.tabs)
        return frame

    # --- filling ---------------------------------------------------------------------------------------------

    def later(self, *_args) -> None:
        self.timer.start()  # several boxes reset at once: one refresh

    def clear(self) -> None:
        for side in (self.side_a, self.side_b):
            side.reset()
        for box in (self.league, self.period, self.kind, self.ground, self.strength):
            box.blockSignals(True)
            box.setCurrentIndex(0)
            box.blockSignals(False)
        self.refresh()

    def refresh(self) -> None:
        kept = data.keep(self.rows, self.side_a.wanted(), self.side_b.wanted(), league=self.league.currentData(),
                         period=self.period.currentData(), kind=self.kind.currentData(),
                         ground=self.ground.currentData(), strength=self.strength.currentData())
        matches = len({r.match for r in self.rows})
        known = len({r.match for r in self.rows if r.tactic.get("plano")})
        self.counts.setText(tr(f"{matches} jogos registados · {known} com tática conhecida de pelo menos um lado · "
                               f"lidos às {self.read_at:%H:%M}"))
        s = data.summary(kept)
        n = s["n"]
        self.games.setText(f"{n} {tr('jogo' if n == 1 else 'jogos')}")
        self.games_note.setText(tr("do lado A com estes filtros (um jogo entre dois clubes que passam conta duas vezes)"
                                   + (" · poucos jogos: os números saltam muito" if 0 < n < 15 else "")))
        if not n:
            self.ev.setText("—")
            self.ev_note.setText(tr("sem jogos"))
            self.odds_bar.set(None)
            self.real_bar.set(None)
            self.odds_text.setText("")
            self.real_text.setText("")
            for a, b in self.stat_cells.values():
                a.setText("—")
                b.setText("—")
            self.edge.setText("")
            for table in (self.patterns, self.matchups, self.matches):
                table.setRowCount(0)
            return
        self.ev.setText(f"<span style='color:{ev_colour(s['ev'])}'>{signed(s['ev'])}</span>")
        self.ev_note.setText(tr(f"EV · pontos por jogo acima do esperado ({s['points']:.2f} feitos, {s['expected']:.2f} esperados)"))
        self.odds_bar.set(s["odds"])
        self.real_bar.set(s["real"])
        self.odds_text.setText(tr(f"{s['expected']:.2f} pts/jogo"))
        self.real_text.setText(tr(f"{s['points']:.2f} pts/jogo"))
        cells = {"goals": (plain(s["goals"], 2), plain(s["against"], 2)),
                 "shots": (plain(s["shots"]), plain(s["rival_shots"])),
                 "possession": (plain(s["possession"], 0, " %"),
                                plain(None if s["possession"] is None else 100 - s["possession"], 0, " %")),
                 "strength": (plain(s["strength"], 0), plain(s["rival_strength"], 0)),
                 "eleven": (plain(s["eleven"]), plain(s["rival_eleven"]))}
        for key, (a, b) in cells.items():
            self.stat_cells[key][0].setText(a)
            self.stat_cells[key][1].setText(b)
        humans = sum(r.human is True for r in kept), sum(r.rival_human is True for r in kept)
        self.edge.setText(tr(f"Lado A {s['edge']:+.0f} % de força em média.\n"
                             f"Treinador humano: A em {humans[0]}, B em {humans[1]} de {n}."))
        self._fill_patterns(kept)
        self._fill_matchups(kept)
        self._fill_matches(kept)

    def _ev_cell(self, table, row: int, column: int, ev: float, games: int) -> None:
        w.set_cell(table, row, column, signed(ev), GREEN if ev >= 0.05 else RED if ev <= -0.05 else GREY)
        if games < 5:
            table.item(row, column).setForeground(QColor(w.blend(ev_colour(ev), 0.55)))

    def _fill_patterns(self, kept: list) -> None:
        own = all(r.mine for r in kept)
        found = data.patterns(kept, own=own)
        self.patterns.setRowCount(len(found))
        for i, (name, value, games, points, ev) in enumerate(found):
            w.set_cell(self.patterns, i, 0, name, GREY)
            w.set_cell(self.patterns, i, 1, value)
            w.set_cell(self.patterns, i, 2, str(games), None if games >= 15 else YELLOW if games >= 5 else RED)
            w.set_cell(self.patterns, i, 3, f"{points:.2f}")
            self._ev_cell(self.patterns, i, 4, ev, games)

    def _fill_matchups(self, kept: list) -> None:
        found = data.matchups(kept)
        self.matchups.setRowCount(len(found))
        for i, (a, b, games, ev) in enumerate(found):
            w.set_cell(self.matchups, i, 0, a)
            w.set_cell(self.matchups, i, 1, b)
            w.set_cell(self.matchups, i, 2, str(games), None if games >= 15 else YELLOW if games >= 5 else RED)
            self._ev_cell(self.matchups, i, 3, ev, games)

    def _fill_matches(self, kept: list) -> None:
        shown = sorted(kept, key=lambda r: -r.when)[:500]
        self.matches.setRowCount(len(shown))
        for i, r in enumerate(shown):
            goals = f"{r.goals}-{r.against}"
            tactic = lambda t: " · ".join(v for v in (t.get("formacao"), t.get("plano"), t.get("desarme"),
                                                       ("fj" if t.get("armadilha") == "Sim" else None)) if v)
            w.set_cell(self.matches, i, 0, datetime.fromtimestamp(r.when).strftime("%Y-%m-%d") if r.when else "")
            w.set_cell(self.matches, i, 1, r.club, YELLOW if r.mine else None)
            w.set_cell(self.matches, i, 2, "neutro" if r.neutral else "casa" if r.home else "fora", GREY)
            w.set_cell(self.matches, i, 3, goals, GREEN if r.points == 3 else RED if r.points == 0 else GREY)
            w.set_cell(self.matches, i, 4, r.rival, YELLOW if r.rival_mine else None)
            w.set_cell(self.matches, i, 5, f"{r.strength:.0f}/{r.rival_strength:.0f}", GREY)
            w.set_cell(self.matches, i, 6, f"{tactic(r.tactic)}  ×  {tactic(r.rival_tactic)}")
            w.set_cell(self.matches, i, 7, str(r.points))
            ev = r.points - r.expected
            w.set_cell(self.matches, i, 8, signed(ev), GREEN if ev >= 0.05 else RED if ev <= -0.05 else GREY)
