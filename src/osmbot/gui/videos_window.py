"""Ver → Vídeos (owner, 2026-11-19): the videos the bot tried, a day at a time, and which went through. Reads only
``logs/*/videos`` on this PC (every PC's folder that is here); never talks to the game. The sums are
``osmbot.analysis.videos`` (pure, tested)."""
from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from osmbot import logs
from osmbot.analysis import videos
from osmbot.gui import window as w
from osmbot.gui.data_window import STYLE, TABLE_STYLE, label
from osmbot.gui.view import GREEN, RED
from osmbot.i18n import tr


def read_videos(root: Path | None = None) -> list[dict]:
    """Every line of ``logs/<PC>/videos/*.jsonl``, with the PC it came from."""
    root = root or logs.repo_folder()
    found: list[dict] = []
    if root is None:
        return found
    for path in sorted((root / "logs").glob("*/videos/*.jsonl")):
        pc = path.parent.parent.name
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines():
            try:
                found.append({**json.loads(line), "pc": pc})
            except ValueError:
                pass
    return found


class VideosWindow(QWidget):
    """Ver → Vídeos: a day (arrows or the list), what to show (all, through, failed) and the kind of video."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle(tr("OSMbot — Vídeos"))
        self.setStyleSheet(STYLE)
        self.resize(1000, 640)
        self.records = read_videos()
        self.days = videos.days(self.records)

        back = w.Backdrop()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(back)
        whole = QVBoxLayout(back)
        whole.setContentsMargins(16, 14, 16, 14)
        whole.setSpacing(10)

        bar = QHBoxLayout()
        self.older = QPushButton("◀", objectName="chip", clicked=lambda: self.step(1))
        self.newer = QPushButton("▶", objectName="chip", clicked=lambda: self.step(-1))
        self.day = QComboBox()
        self.day.addItems([f"{d:%d/%m/%Y}" for d in self.days])
        self.which = QComboBox()
        self.which.addItems([tr(f) for f in videos.FILTERS])
        self.kind = QComboBox()
        self.kind.addItems([tr("Todos os tipos")] + [tr(k.capitalize()) for k in videos.KINDS])
        for box in (self.day, self.which, self.kind):
            box.currentIndexChanged.connect(self.refresh)
        for widget in (self.older, self.day, self.newer, self.which, self.kind):
            bar.addWidget(widget)
        bar.addStretch(1)
        whole.addLayout(bar)

        self.headline = label("", 11, True)
        whole.addWidget(self.headline)
        self.table = w.make_table(["Hora", "Tipo", "Clube", "Jogador", "Resultado", "PC", "Motivo"],
                                  [60, 80, 150, 150, 130, 150, 300])
        self.table.setStyleSheet(TABLE_STYLE)
        whole.addWidget(self.table, 1)
        self.refresh()

    def step(self, by: int) -> None:
        """◀ the day before, ▶ the day after (the list is newest first)."""
        index = self.day.currentIndex() + by
        if 0 <= index < self.day.count():
            self.day.setCurrentIndex(index)

    def refresh(self) -> None:
        if not self.days:
            self.headline.setText(tr("Ainda não há vídeos registados (o registo começou a 2026-11-19)"))
            self.table.setRowCount(0)
            return
        day = self.days[max(self.day.currentIndex(), 0)]
        kind = None if self.kind.currentIndex() <= 0 else videos.KINDS[self.kind.currentIndex() - 1]
        shown = videos.rows(self.records, day, videos.FILTERS[max(self.which.currentIndex(), 0)], kind)
        self.headline.setText(videos.summary(self.records, day))
        self.older.setEnabled(self.day.currentIndex() < self.day.count() - 1)
        self.newer.setEnabled(self.day.currentIndex() > 0)
        self.table.setRowCount(len(shown))
        for row, r in enumerate(shown):
            colour = GREEN if r["ok"] else RED
            for column, text in enumerate((r["hora"], r["tipo"], r["clube"], r["jogador"], r["resultado"], r["pc"], r["motivo"])):
                w.set_cell(self.table, row, column, text, colour if column == 4 else None)
