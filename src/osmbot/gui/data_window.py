"""Ver → Dados (owner, 2026-11-06; look of D-096): the logged matches studied in the board's look. Reads only
``logs/*/jogos`` and ``logs/*/analista`` on this PC; never talks to the game. The sums are ``osmbot.analysis.data``
(pure, tested).

One measure everywhere, in wins: "won 45 of 55, normal 36, 9 more", where the normal is how many the squads' strength
gave (``data.tally`` / ``data.verdict``). A sentence sums up what the filters keep; then a card per thing (each field
of the tactic; on the rival's tab his difficulty, human or the computer and each field of his tactic), one line per
value, faded under 15 matches. A click on a line opens its numbers (wins/draws/losses against the normal, goals,
shots, possession, strength, the eleven, human rivals). The filters are chips: club, period, difficulty, the rival
(human or the computer and his tactic) and "+ Filtro" (league, competition, ground and this side's tactic).
The third tab lists the matches.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QActionGroup, QColor, QCursor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel, QMenu, QPushButton, QScrollArea, QSizePolicy,
                               QTabWidget, QVBoxLayout, QWidget)

from osmbot import logs
from osmbot.analysis import data
from osmbot.i18n import tr
from osmbot.gui.view import GREEN, GREY, RED, YELLOW
from osmbot.gui import window as w

TEXT, MUTED, ACCENT, LINE = "#eef0ff", "#8f95b8", "#8b8cf8", "#2d3366"
WIN, CARD, TRACK = "#5cd17a", "rgba(16, 20, 54, 232)", "#232a5c"
FEW = 15  # under this many matches a line is faded: a few matches swing a lot
SHOWN = 5  # lines a card shows before "mais N"
WHO = ["Os meus clubes", "Todos os clubes", "Outros clubes"]
STYLE = (
    "QFrame#dcard { background: %s; border: 1px solid rgba(139, 140, 248, 55); border-radius: 12px; }"
    "QPushButton#chip { background: rgba(26, 32, 82, 235); color: #eef0ff; border: 1px solid rgba(139, 140, 248, 70);"
    " border-radius: 13px; padding: 4px 14px; }"
    "QPushButton#chip:hover { border-color: rgba(139, 140, 248, 170); }"
    "QPushButton#chip[on=\"true\"] { background: rgba(139, 140, 248, 95); border-color: #8b8cf8; font-weight: bold; }"
    "QPushButton#chip::menu-indicator { image: none; width: 0; }"
    "QPushButton#link { background: transparent; color: #8b8cf8; border: none; padding: 4px 6px; }"
    "QPushButton#link:hover { color: #b9baff; }"
    "QMenu { background: #161b40; color: #eef0ff; border: 1px solid rgba(139, 140, 248, 110); padding: 4px; }"
    "QMenu::item { padding: 4px 22px 4px 22px; border-radius: 5px; }"
    "QMenu::item:selected { background: #3a3f8a; }"
    "QMenu::separator { height: 1px; background: #2d3366; margin: 4px 8px; }"
    "QWidget#line:hover { background: rgba(139, 140, 248, 22); border-radius: 6px; }"
    "QTabWidget::pane { border: none; }"
    "QTabBar::tab { background: transparent; color: #8f95b8; padding: 6px 16px; border: none;"
    " border-bottom: 2px solid transparent; font-weight: bold; }"
    "QTabBar::tab:selected { color: #eef0ff; border-bottom: 2px solid #8b8cf8; }"
    "QTabBar::tab:hover { color: #b9baff; }"
    "QScrollArea, QScrollArea > QWidget > QWidget { background: transparent; }"
    "QLabel { background: transparent; }"
) % CARD
TABLE_STYLE = (
    "QTableWidget { background: rgba(16, 20, 54, 232); alternate-background-color: rgba(139, 140, 248, 14);"
    " color: #eef0ff; border: 1px solid rgba(139, 140, 248, 55); border-radius: 12px; }"
    "QHeaderView::section { background: rgba(11, 15, 42, 230); color: #8f95b8; border: none;"
    " border-bottom: 1px solid #2d3366; padding: 3px 6px; font-weight: bold; }"
    "QTableCornerButton::section { background: transparent; border: none; }"
)
OWN_CARDS = [(key, name) for key, name in data.TACTIC_FIELDS + data.OWN_FIELDS] + [("onde", "Casa ou fora")]
RIVAL_CARDS = [("dificuldade", "Dificuldade"), ("treinador", "Treinador dele")] + \
              [(f"rival:{key}", f"{name} dele") for key, name in data.TACTIC_FIELDS]


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


def num(value: float | None, digits: int = 1) -> str:
    return "—" if value is None else f"{value:.{digits}f}".replace(".", ",")


def label(text: str = "", size: float = 9, bold: bool = False, colour: str = TEXT) -> QLabel:
    found = w.text_label(size, bold)
    found.setStyleSheet(f"color:{colour};")
    found.setText(text)
    return found


def card() -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("dcard")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(16, 12, 16, 12)
    layout.setSpacing(4)
    return frame, layout


class WinBar(QWidget):
    """The share of wins (green) over all the matches; the white mark is the normal by strength."""

    def __init__(self, t: dict, few: bool):
        super().__init__()
        self.t, self.few = t, few
        self.setFixedHeight(20)
        self.setMinimumWidth(50)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def sizeHint(self) -> QSize:
        return QSize(120, 20)

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        n, width = self.t["n"] or 1, self.width()
        track = QPainterPath()
        track.addRoundedRect(QRectF(0, 4, width, 12), 6, 6)
        painter.fillPath(track, QColor(TRACK))
        painter.setClipPath(track)
        painter.fillRect(QRectF(0, 4, width * self.t["wins"] / n, 12), QColor(w.blend(WIN, 0.45) if self.few else WIN))
        painter.setClipping(False)
        x = round(width * self.t["normal"][0] / n)
        painter.setPen(QPen(QColor("#ffffff"), 2.5))
        painter.drawLine(x, 0, x, 20)


def verdict_label(t: dict, size: float = 9) -> QLabel:
    text, sign = data.verdict(t)
    return label(tr(text), size, True, w.COLOURS[GREEN] if sign > 0 else w.COLOURS[RED] if sign < 0 else MUTED)


def details(kept: list) -> QWidget:
    """A line's numbers: wins/draws/losses against the normal, goals, shots, possession, strength, the eleven."""
    s, t = data.summary(kept), data.tally(kept)
    normal = " / ".join(f"{x:.0f}" for x in t["normal"])
    edge = s["edge"]
    facts = [("Vitórias / empates / derrotas", f"{t['wins']} / {t['draws']} / {t['losses']}", f"normal: {normal}"),
             ("Golos por jogo", f"{num(s['goals'])} – {num(s['against'])}", "marcados – sofridos"),
             ("Remates por jogo", f"{num(s['shots'])} – {num(s['rival_shots'])}", "teus – dele"),
             ("Posse de bola", num(s["possession"], 0) + (" %" if s["possession"] is not None else ""), ""),
             ("Força das equipas", f"{s['strength']:.0f} – {s['rival_strength']:.0f}",
              f"eras {abs(edge):.0f} % mais {'forte' if edge >= 0 else 'fraco'}"),
             ("Média do onze", f"{num(s['eleven'])} – {num(s['rival_eleven'])}", ""),
             ("Adversário humano", f"{sum(r.rival_human is True for r in kept)} de {t['n']}", "")]
    box = QWidget()
    grid = QGridLayout(box)
    grid.setContentsMargins(8, 4, 8, 8)
    grid.setHorizontalSpacing(18)
    grid.setVerticalSpacing(6)
    for i, (name, value, note) in enumerate(facts):
        cell = QVBoxLayout()
        cell.setSpacing(0)
        cell.addWidget(label(tr(name).upper(), 7, True, MUTED))
        cell.addWidget(label(value, 11, True))
        if note:
            cell.addWidget(label(tr(note), 8, colour=MUTED))
        cell.addStretch(1)
        grid.addLayout(cell, i // 3, i % 3)
    return box


class Line(QWidget):
    """One value of a card: name, bar, "45 de 55", "normal 36", "9 a mais"; a click opens its numbers."""

    def __init__(self, name: str, kept: list, name_width: int = 100):
        super().__init__()
        self.kept = kept
        self.setObjectName("line")
        self.setAttribute(Qt.WA_StyledBackground)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        t = data.tally(kept)
        few = t["n"] < FEW
        column = QVBoxLayout(self)
        column.setContentsMargins(4, 1, 4, 1)
        column.setSpacing(0)
        row = QHBoxLayout()
        row.setSpacing(8)
        self.arrow = label("▸", 8, colour=MUTED)
        self.arrow.setFixedWidth(8)
        row.addWidget(self.arrow)
        title = label(tr(name), 9, colour=w.blend(TEXT, 0.5) if few else TEXT)
        title.setFixedWidth(name_width)
        title.setToolTip(tr(name))
        w.fit(title, name_width, 9, 7)
        row.addWidget(title)
        row.addWidget(WinBar(t, few), 1)
        count = label(f"<b>{t['wins']}</b> {tr('de')} {t['n']}", 9, colour=MUTED if few else TEXT)
        count.setFixedWidth(54)
        row.addWidget(count)
        normal = label(f"{tr('normal')} {t['normal'][0]:.0f}", 9, colour=MUTED)
        normal.setFixedWidth(66)
        row.addWidget(normal)
        word = verdict_label(t)
        word.setFixedWidth(70)
        row.addWidget(word)
        column.addLayout(row)
        self.more: QWidget | None = None
        self.column = column

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.LeftButton:
            return
        if self.more is None:
            self.more = details(self.kept)
            self.column.addWidget(self.more)
            self.more.show()
        else:
            self.more.setVisible(not self.more.isVisible())
        self.arrow.setText("▾" if self.more.isVisible() else "▸")
        self.updateGeometry()


class FieldCard(QFrame):
    """A card per thing: one line per value, the first ``SHOWN``; "mais N" shows the rest."""

    def __init__(self, title: str, groups: list, note: str = ""):
        super().__init__()
        self.setObjectName("dcard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(2)
        top = QHBoxLayout()
        top.addWidget(label(tr(title).upper(), 8, True, MUTED))
        if note:
            top.addWidget(label(tr(note), 8, colour=MUTED))
        top.addStretch(1)
        self.extra: list[Line] = []
        if len(groups) > SHOWN:
            self.toggle = QPushButton(tr(f"mais {len(groups) - SHOWN} ▸"))
            self.toggle.setObjectName("link")
            self.toggle.setCursor(QCursor(Qt.PointingHandCursor))
            self.toggle.clicked.connect(self.show_all)
            top.addWidget(self.toggle)
        layout.addLayout(top)
        for i, (value, kept) in enumerate(groups):
            line = Line(value, kept)
            layout.addWidget(line)
            if i >= SHOWN:
                line.hide()
                self.extra.append(line)
        layout.addStretch(1)

    def show_all(self) -> None:
        hidden = bool(self.extra) and self.extra[0].isHidden()
        for line in self.extra:
            line.setVisible(hidden)
        self.toggle.setText(tr("menos ▴") if hidden else tr(f"mais {len(self.extra)} ▸"))


class Chip(QPushButton):
    """A filter: its menu holds one or more fields, each a list of exclusive values."""

    def __init__(self, owner: "DataWindow", name: str, fields: list[tuple[str, str, str, list[str]]]):
        super().__init__()
        self.setObjectName("chip")
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.owner, self.name, self.fields = owner, name, fields
        menu = QMenu(self)
        for scope, key, title, options in fields:
            target = menu if len(fields) == 1 else menu.addMenu(tr(title))
            group = QActionGroup(target)
            group.setExclusive(True)
            for option in options:
                action = target.addAction(owner.shown(option))
                action.setCheckable(True)
                action.setChecked(owner.get(scope, key) == option)
                action.setData((scope, key, option))
                group.addAction(action)
            group.triggered.connect(lambda action: owner.set_filter(*action.data()))
        self.setMenu(menu)

    def update_text(self) -> None:
        chosen = [self.owner.get(scope, key) for scope, key, _title, options in self.fields]
        active = [value for value, (_s, _k, _t, options) in zip(chosen, self.fields) if value != options[0]]
        if self.name == "Clube":
            text, on = self.owner.shown(chosen[0]), chosen[0] != WHO[0]
        elif len(self.fields) == 1:
            text, on = self.owner.shown(chosen[0]) if active else tr(self.name), bool(active)
        else:
            text = tr(self.name) + (": " + " · ".join(self.owner.shown(v) for v in active) if active else "")
            on = bool(active)
        self.setText(text + "  ▾")
        self.setProperty("on", "true" if on else "false")
        self.style().unpolish(self)
        self.style().polish(self)
        for action in self.menu().actions() + [a for m in self.menu().findChildren(QMenu) for a in m.actions()]:
            if action.data():
                action.setChecked(self.owner.get(*action.data()[:2]) == action.data()[2])


class DataWindow(QWidget):
    """Ver → Dados."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle(tr("OSMbot — Dados"))
        self.setStyleSheet(STYLE)
        self.resize(1440, 900)
        self.rows = data.rows(read_records("jogos"), read_records("analista"))
        self.read_at = datetime.now()
        self.kept: list = []
        self.filters = self.defaults()
        self.timer = QTimer(self, singleShot=True, interval=60, timeout=self.refresh)

        back = w.Backdrop()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(back)
        whole = QVBoxLayout(back)
        whole.setContentsMargins(16, 14, 16, 14)
        whole.setSpacing(10)
        whole.addWidget(self._top())
        whole.addWidget(self._headline())
        self.tabs = QTabWidget()
        self.own_grid, own = self._grid()
        self.rival_grid, rival = self._grid()
        self.matches = w.make_table(["Data", "Clube", "", "Res.", "Adversário", "Dificuldade", "Táticas (tu × ele)"],
                                    [82, 150, 60, 50, 160, 140, 420])
        self.matches.setStyleSheet(TABLE_STYLE)
        self.tabs.addTab(own, tr("A minha tática"))
        self.tabs.addTab(rival, tr("O adversário"))
        self.tabs.addTab(self.matches, tr("Jogos"))
        whole.addWidget(self.tabs, 1)
        legend = label(f"<span style='color:{WIN}'>■</span> {tr('vitórias')} &nbsp; <b style='color:white'>|</b> "
                       f"{tr('quantas seria normal ganhar, pela força das equipas')} &nbsp;&nbsp; "
                       f"{tr('esbatido: menos de 15 jogos')} &nbsp;&nbsp; {tr('clica numa linha para ver os números')}",
                       8, colour=MUTED)
        whole.addWidget(legend)
        self.refresh()

    # --- filters ---------------------------------------------------------------------------------------------

    @staticmethod
    def defaults() -> dict:
        return {"own": {"quem": WHO[0]}, "rival": {}, "all": {"league": data.ANY, "period": "Tudo", "kind": data.ANY,
                                                             "ground": data.ANY, "strength": data.ANY}}

    def shown(self, value: str) -> str:
        """A filter's value as the chips and menus show it."""
        return tr(getattr(self, "names", {}).get(value, value))

    def get(self, scope: str, key: str) -> str:
        return self.filters[scope].get(key, data.ANY)

    def set_filter(self, scope: str, key: str, value: str) -> None:
        self.filters[scope][key] = value
        self.timer.start()

    def clear(self) -> None:
        self.filters = self.defaults()
        self.refresh()

    def _top(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("dcard")
        bar = QHBoxLayout(frame)
        bar.setContentsMargins(18, 10, 18, 10)
        bar.setSpacing(8)
        titles = QVBoxLayout()
        titles.setSpacing(0)
        titles.addWidget(label(tr("Dados dos jogos"), 13, True))
        self.counts = label("", 8, colour=MUTED)
        titles.addWidget(self.counts)
        bar.addLayout(titles)
        bar.addStretch(1)
        rows = self.rows
        clubs = sorted({r.club for r in rows if r.mine})
        mine: dict = {}
        for r in rows:
            if r.mine:
                mine.setdefault(r.league, set()).add(r.club)
        leagues = sorted({r.league for r in rows}, key=lambda x: (x not in mine, x))
        self.names = {x: (f"Liga de {' / '.join(sorted(mine[x]))}" if x in mine else f"Liga {x}") for x in leagues}
        self.names.update({"liga": "Liga", "taça": "Taça", "Casa": "Em casa", "Neutro": "Campo neutro",
                           "Humano": "humano", "Computador": "computador"})
        any_ = [data.ANY]
        own_fields = [("own", key, name, any_ + data.choices(rows, key)) for key, name in data.TACTIC_FIELDS + data.OWN_FIELDS]
        rival_fields = [("rival", "treinador", "Treinador", any_ + ["Humano", "Computador"]),
                        ("rival", "quem", "Clube", any_ + ["Os meus clubes", "Outros clubes"])]
        rival_fields += [("rival", key, name, any_ + data.choices(rows, key, True)) for key, name in data.TACTIC_FIELDS]
        self.chips = [
            Chip(self, "Clube", [("own", "quem", "Clube", WHO + clubs)]),
            Chip(self, "Período", [("all", "period", "Período", list(data.PERIODS))]),
            Chip(self, "Dificuldade", [("all", "strength", "Dificuldade", list(data.STRENGTH_BANDS))]),
            Chip(self, "Adversário", rival_fields),
            Chip(self, "+ Filtro", [("all", "league", "Liga", any_ + leagues),
                                    ("all", "kind", "Competição", any_ + ["liga", "taça"]),
                                    ("all", "ground", "Casa ou fora", any_ + ["Casa", "Fora", "Neutro"])] + own_fields),
        ]
        for chip in self.chips:
            bar.addWidget(chip)
        clear = QPushButton(tr("Limpar"))
        clear.setObjectName("link")
        clear.setCursor(QCursor(Qt.PointingHandCursor))
        clear.clicked.connect(self.clear)
        bar.addWidget(clear)
        return frame

    def _headline(self) -> QFrame:
        frame, layout = card()
        layout.setContentsMargins(20, 12, 20, 10)
        layout.setSpacing(6)
        self.headline = label("", 14)
        self.headline.setWordWrap(True)
        layout.addWidget(self.headline)
        self.all_line = QVBoxLayout()
        self.all_line.setSpacing(0)
        layout.addLayout(self.all_line)
        return frame

    def _grid(self) -> tuple[QGridLayout, QScrollArea]:
        inside = QWidget()
        inside.setAttribute(Qt.WA_TranslucentBackground)
        column = QVBoxLayout(inside)
        column.setContentsMargins(0, 4, 6, 4)
        grid = QGridLayout()
        grid.setSpacing(10)
        for i in range(3):
            grid.setColumnStretch(i, 1)
        column.addLayout(grid)
        column.addStretch(1)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(inside)
        return grid, scroll

    # --- filling ---------------------------------------------------------------------------------------------

    def refresh(self) -> None:
        own = dict(self.filters["own"])
        if own.get("quem") == "Todos os clubes":
            own["quem"] = None
        kept = data.keep(self.rows, own, self.filters["rival"], **self.filters["all"])
        self.kept = kept
        for chip in self.chips:
            chip.update_text()
        matches = len({r.match for r in self.rows})
        known = len({r.match for r in self.rows if r.tactic.get("plano")})
        self.counts.setText(tr(f"{matches} jogos registados · {known} com tática conhecida · lidos às {self.read_at:%H:%M}"))
        self._fill_headline(kept)
        mine = bool(kept) and all(r.mine for r in kept)
        self._fill_grid(self.own_grid, kept, OWN_CARDS, mine)
        self._fill_grid(self.rival_grid, kept, RIVAL_CARDS, mine)
        self._fill_matches(kept)

    def _fill_headline(self, kept: list) -> None:
        while self.all_line.count():
            item = self.all_line.takeAt(0)
            gone = item.widget()
            if gone:
                gone.setParent(None)  # off the screen now, not at the next turn of the loop
                gone.deleteLater()
        if not kept:
            self.headline.setText(tr("Sem jogos com estes filtros."))
            return
        t = data.tally(kept)
        text, sign = data.verdict(t)
        colour = w.COLOURS[GREEN] if sign > 0 else w.COLOURS[RED] if sign < 0 else MUTED
        gap = text.replace("a mais", "vitórias a mais").replace("a menos", "vitórias a menos") if sign else "exatamente o esperado"
        who = "Ganhaste" if all(r.mine for r in kept) else "Ganharam"
        self.headline.setText(tr(f"{who} <b>{t['wins']} de {t['n']}</b> jogos. Pela força das equipas, o normal seria "
                                 f"ganhar <b>{t['normal'][0]:.0f}</b>: ") + f"<b style='color:{colour}'>{tr(gap)}</b>.")
        self.all_line.addWidget(Line("Todos estes jogos", kept))

    def _fill_grid(self, grid: QGridLayout, kept: list, cards: list, mine: bool) -> None:
        while grid.count():
            item = grid.takeAt(0)
            gone = item.widget()
            if gone:
                gone.setParent(None)  # off the screen now, not at the next turn of the loop
                gone.deleteLater()
        place = 0
        own_only = {key for key, _ in data.OWN_FIELDS}
        for key, title in cards:
            groups = data.split(kept, key)
            if not groups:
                continue
            note = "só os teus clubes" if key in own_only and not mine else ""
            grid.addWidget(FieldCard(title, groups, note), place // 3, place % 3)
            place += 1

    def _fill_matches(self, kept: list) -> None:
        shown = sorted(kept, key=lambda r: -r.when)[:500]
        self.matches.setRowCount(len(shown))
        tactic = lambda t: " · ".join(v for v in (t.get("formacao"), t.get("plano"), t.get("desarme"),
                                                   ("fora de jogo" if t.get("armadilha") == "Sim" else None)) if v)
        for i, r in enumerate(shown):
            w.set_cell(self.matches, i, 0, datetime.fromtimestamp(r.when).strftime("%Y-%m-%d") if r.when else "")
            w.set_cell(self.matches, i, 1, r.club, YELLOW if r.mine else None)
            w.set_cell(self.matches, i, 2, tr("neutro" if r.neutral else "casa" if r.home else "fora"), GREY)
            w.set_cell(self.matches, i, 3, f"{r.goals}-{r.against}", GREEN if r.points == 3 else RED if r.points == 0 else GREY)
            w.set_cell(self.matches, i, 4, r.rival, YELLOW if r.rival_mine else None)
            w.set_cell(self.matches, i, 5, tr(data.difficulty(r)), GREY)
            w.set_cell(self.matches, i, 6, f"{tactic(r.tactic)}  ×  {tactic(r.rival_tactic)}")
