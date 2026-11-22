"""Animacja „Skanowanie systemu — proszę czekać"."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from .. import i18n
from .icons import logo_pixmap

AKCENT = QColor("#2fb35f")


class Spinner(QWidget):
    """Obracający się pierścień — działa w głównym wątku, ale nie blokuje GUI."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(56, 56)
        self._kat = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._obrot)

    def _obrot(self) -> None:
        self._kat = (self._kat + 30) % 360
        self.update()

    def showEvent(self, event) -> None:
        if not self._timer.isActive():
            self._timer.start(45)
        super().showEvent(event)

    def hideEvent(self, event) -> None:
        self._timer.stop()
        super().hideEvent(event)

    def paintEvent(self, event) -> None:
        malarz = QPainter(self)
        malarz.setRenderHint(QPainter.RenderHint.Antialiasing)
        malarz.translate(self.width() / 2, self.height() / 2)
        for i in range(12):
            malarz.save()
            malarz.rotate(i * 30 + self._kat)
            alfa = int(40 + 215 * i / 12)
            malarz.setPen(QPen(QColor(AKCENT.red(), AKCENT.green(),
                                      AKCENT.blue(), alfa),
                               5, Qt.PenStyle.SolidLine,
                               Qt.PenCapStyle.RoundCap))
            malarz.drawLine(0, -17, 0, -23)
            malarz.restore()
        malarz.end()


class LoadingWidget(QFrame):
    """Ekran ładowania wyświetlany nad listą programów w czasie skanowania."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        pion = QVBoxLayout(self)
        pion.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.logo = QLabel()
        self.logo.setPixmap(logo_pixmap(110))
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pion.addWidget(self.logo)
        pion.addSpacing(14)

        rzad = QHBoxLayout()
        rzad.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spinner = Spinner()
        rzad.addWidget(self.spinner)
        self.tytul = QLabel(i18n.tr("scanning"))
        self.tytul.setStyleSheet("font-size:20px; font-weight:700;")
        rzad.addWidget(self.tytul)
        pion.addLayout(rzad)

        self.podtytul = QLabel(i18n.tr("please_wait"))
        self.podtytul.setObjectName("subtitle")
        self.podtytul.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pion.addWidget(self.podtytul)

    def retranslate(self) -> None:
        self.tytul.setText(i18n.tr("scanning"))
        self.podtytul.setText(i18n.tr("please_wait"))
