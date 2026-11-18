"""Definições → Telegram (D-110, owner 2026-11-18): the same steps for the owner and for any user. 1) make a bot with
@BotFather, 2) paste its token, 3) open the bot's link and press Start (the app finds the chat by itself), 4) a test
message, then a switch per kind of notice. The token stays in this PC's config only. Network calls run in threads, so
the window never freezes; the pure part is in ``osmbot.notify``."""
from __future__ import annotations

import threading

from PySide6.QtCore import QObject, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QImage, QPainter, QPixmap
from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton,
                               QScrollArea, QVBoxLayout, QWidget)

from osmbot.i18n import tr
from osmbot.notify import qr, rules, telegram

MUTED, GOOD, BAD = "#8f95b8", "#5cd17a", "#ff6b6b"
POLL_MS = 2000
QR_SIZE = 150  # pixels
BOTFATHER = "https://t.me/BotFather"


class _Done(QObject):
    finished = Signal(object, object)  # (result, error text or None), back in the window's thread


class TelegramDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Telegram")
        self.config = telegram.load()
        self.token = self.config.get("token") or ""
        self.code = telegram.new_code()
        self.url = ""
        self.busy = False
        self.bridge = _Done()
        self.bridge.finished.connect(self._back)
        self._then = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._poll)
        page = QWidget()  # the steps scroll when the screen is too short for them
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 18, 20, 16)
        layout.setSpacing(10)
        title = QLabel(tr("Notificações no Telegram"))
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        layout.addWidget(self._note(tr("Cada utilizador tem o seu bot: só tu e o Telegram veem as mensagens. O token é a palavra-passe do bot e fica só neste PC.")))

        layout.addWidget(self._step(tr("1. Cria o teu bot")))
        body = QHBoxLayout()  # the text on the left, the QR on the right: the window stays short
        text = QVBoxLayout()
        text.addWidget(self._note(tr("Lê o QR com a câmara do telemóvel (abre o @BotFather no Telegram), envia /newbot, escolhe um nome e um username que acabe em «bot». Ele responde com um token.")))
        text.addWidget(self._button(tr("Abrir o @BotFather neste PC"), lambda: QDesktopServices.openUrl(QUrl(BOTFATHER))), 0, Qt.AlignLeft)
        text.addStretch(1)
        body.addLayout(text, 1)
        botfather = QLabel()  # the phone's camera opens @BotFather: no Telegram needed on this PC
        botfather.setPixmap(self._qr(BOTFATHER))
        body.addWidget(botfather, 0, Qt.AlignTop)
        layout.addLayout(body)

        layout.addWidget(self._step(tr("2. Cola o token")))
        row = QHBoxLayout()
        self.field = QLineEdit(self.token)
        self.field.setEchoMode(QLineEdit.Password)
        self.field.setPlaceholderText("123456789:AAH…")
        row.addWidget(self.field, 1)
        self.verify = self._button(tr("Verificar"), self._verify)
        row.addWidget(self.verify)
        layout.addLayout(row)
        self.token_status = self._status()
        layout.addWidget(self.token_status)

        layout.addWidget(self._step(tr("3. Lê o QR com o telemóvel e carrega em Start")))
        body = QHBoxLayout()
        text = QVBoxLayout()
        self.link_label = self._note("")
        self.link_label.setOpenExternalLinks(True)
        text.addWidget(self.link_label)
        row = QHBoxLayout()
        self.open_button = self._button(tr("Abrir neste PC"), lambda: QDesktopServices.openUrl(QUrl(self.url)))
        self.copy_button = self._button(tr("Copiar o link"), lambda: QApplication.clipboard().setText(self.url))
        row.addWidget(self.open_button)
        row.addWidget(self.copy_button)
        row.addStretch(1)
        text.addLayout(row)
        self.start_status = self._status()
        text.addWidget(self.start_status)
        text.addStretch(1)
        body.addLayout(text, 1)
        self.qr_label = QLabel()
        body.addWidget(self.qr_label, 0, Qt.AlignTop)
        layout.addLayout(body)

        layout.addWidget(self._step(tr("4. Testa")))
        row = QHBoxLayout()
        self.test_button = self._button(tr("Enviar mensagem de teste"), self._test)
        row.addWidget(self.test_button)
        row.addStretch(1)
        layout.addLayout(row)
        self.test_status = self._status()
        layout.addWidget(self.test_status)

        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet("background:#2d3366;")
        layout.addWidget(line)
        layout.addWidget(self._step(tr("O que queres receber")))
        alerts = self.config.get("avisos") or {}
        self.boxes = {}
        for kind, label in rules.KINDS.items():
            box = QCheckBox(tr(label))
            box.setChecked(rules.enabled(alerts, kind))
            box.toggled.connect(lambda on, kind=kind: self._switch(kind, on))
            layout.addWidget(box)
            self.boxes[kind] = box

        row = QHBoxLayout()
        self.off_button = self._button(tr("Desligar o Telegram"), self._turn_off)
        row.addWidget(self.off_button)
        row.addStretch(1)
        row.addWidget(self._button(tr("Fechar"), self.accept))
        layout.addLayout(row)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(page)
        outer.addWidget(scroll)
        screen = (parent.screen() if parent is not None else None) or QApplication.primaryScreen()
        room = int(screen.availableGeometry().height() * 0.88) if screen else 700
        self.setMinimumWidth(580)
        self.resize(580, min(page.sizeHint().height() + 8, room))
        self._refresh()
        if telegram.valid_token(self.token) and not telegram.connected(self.config):
            self._verify()  # a token already pasted but no Start yet: carry on from there

    # --- small pieces ---------------------------------------------------------------------------------------------
    def _note(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet(f"color:{MUTED};")
        return label

    def _step(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet("font-weight: bold; margin-top: 6px;")
        return label

    def _status(self) -> QLabel:
        label = QLabel("")
        label.setWordWrap(True)
        return label

    def _button(self, text: str, slot) -> QPushButton:
        button = QPushButton(text)
        button.clicked.connect(lambda _checked=False: slot())
        return button

    def _say(self, label: QLabel, text: str, good: bool | None = None) -> None:
        label.setText(text)
        label.setStyleSheet(f"color:{GOOD if good else BAD if good is False else MUTED};")

    def _refresh(self) -> None:
        connected = telegram.connected(self.config)
        if connected:
            self._say(self.token_status, tr("Token guardado."), True)
            self._say(self.start_status, tr("Ligado: o bot já sabe a tua conversa."), True)
        has_link = bool(self.url)
        self.link_label.setText(f'<a href="{self.url}">{self.url}</a>' if has_link else tr("Primeiro verifica o token (passo 2)."))
        self.qr_label.setPixmap(self._qr(self.url)) if has_link else self.qr_label.clear()
        self.open_button.setEnabled(has_link)
        self.copy_button.setEnabled(has_link)
        self.test_button.setEnabled(connected)
        self.off_button.setEnabled(bool(self.token))

    def _qr(self, text: str) -> QPixmap:
        """The link as a QR code (white square, dark modules): scan it with the phone's camera."""
        grid = qr.matrix(text)
        image = QImage(len(grid), len(grid), QImage.Format_RGB32)
        image.fill(QColor("white"))
        painter = QPainter(image)
        painter.setPen(QColor("black"))
        for y, row in enumerate(grid):
            for x, dark in enumerate(row):
                if dark:
                    painter.drawPoint(x, y)
        painter.end()
        side = max(1, QR_SIZE // len(grid)) * len(grid)  # a whole number of pixels per module: sharp edges
        return QPixmap.fromImage(image.scaled(side, side, Qt.KeepAspectRatio, Qt.FastTransformation))

    # --- the steps ------------------------------------------------------------------------------------------------
    def _work(self, call, then) -> None:
        """Run ``call`` off the window's thread; ``then(result, error)`` runs back here."""
        self.busy = True
        self._then = then

        def run() -> None:
            try:
                self.bridge.finished.emit(call(), None)
            except telegram.TelegramError as error:
                self.bridge.finished.emit(None, str(error))

        threading.Thread(target=run, daemon=True).start()

    def _back(self, result, error) -> None:
        self.busy = False
        then, self._then = self._then, None
        if then:
            then(result, error)

    def _verify(self) -> None:
        token = self.field.text().strip()
        if not telegram.valid_token(token):
            self._say(self.token_status, tr("Isto não parece um token (algo como 123456789:AAH…). Copia-o inteiro do @BotFather."), False)
            return
        self._say(self.token_status, tr("A verificar…"))
        self._work(lambda: telegram.bot_username(token), lambda name, error: self._verified(token, name, error))

    def _verified(self, token: str, name, error) -> None:
        if error or not name:
            self._say(self.token_status, tr("O Telegram não aceitou o token:") + f" {error or '?'}", False)
            return
        if token != self.token:  # a different bot: the old chat does not belong to it
            self.config = {**self.config, "token": None, "chat_id": None}
            telegram.save(None, None)
        self.token = token
        self.url = telegram.link(name, self.code)
        self._say(self.token_status, tr("Token certo: o teu bot é") + f" @{name}", True)
        if not telegram.connected(self.config):
            self._say(self.start_status, tr("À espera que carregues em Start no Telegram…"))
            self.timer.start(POLL_MS)
        self._refresh()

    def _poll(self) -> None:
        if self.busy or not self.token or not self.url:
            return
        token, code = self.token, self.code
        self._work(lambda: telegram.wait_for_start(token, code), lambda chat, error: self._started(token, chat, error))

    def _started(self, token: str, chat, error) -> None:
        if error:
            self._say(self.start_status, tr("Ainda sem ligação ao Telegram:") + f" {error}", False)
            return
        if chat is None or token != self.token:
            return
        self.timer.stop()
        telegram.save(token, chat)
        self.config = telegram.load()
        self._refresh()

    def _test(self) -> None:
        token, chat = self.config.get("token"), self.config.get("chat_id")
        self._say(self.test_status, tr("A enviar…"))
        self._work(lambda: telegram.send(token, chat, "OSMbot: a ligação ao Telegram está a funcionar ✅"),
                   lambda _ok, error: self._say(self.test_status, (tr("Não enviou:") + f" {error}") if error
                                                else tr("Enviada: vê o Telegram."), error is None))

    def _switch(self, kind: str, on: bool) -> None:
        alerts = {**(self.config.get("avisos") or {}), kind: on}
        self.config = {**self.config, "avisos": alerts}
        telegram.save(self.config.get("token"), self.config.get("chat_id"), alerts)

    def _turn_off(self) -> None:
        self.timer.stop()
        telegram.save(None, None)
        self.config, self.token, self.url = telegram.load(), "", ""
        self.field.clear()
        for label in (self.token_status, self.start_status, self.test_status):
            self._say(label, "")
        self._refresh()

    def done(self, result) -> None:
        self.timer.stop()
        super().done(result)
