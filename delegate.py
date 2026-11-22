"""Lekki przycisk „Usuń" rysowany bezpośrednio w komórce tabeli.

Dzięki temu nie tworzymy tysięcy osobnych widgetów QPushButton
(co na Fedorze z ponad 2000 pakietów blokowało interfejs).
"""

from __future__ import annotations

from PySide6.QtCore import QEvent, QModelIndex, QRect, Signal
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QApplication, QStyle, QStyleOptionButton, QStyledItemDelegate,
)


class RemoveButtonDelegate(QStyledItemDelegate):
    """Przycisk w komórce tabeli — bez tworzenia widgetu dla każdego wiersza."""

    clicked = Signal(QModelIndex)

    def __init__(self, tekst: str = "Usuń", parent=None):
        super().__init__(parent)
        self._tekst = tekst

    def setText(self, tekst: str) -> None:
        self._tekst = tekst

    def _prostokat(self, option) -> QRect:
        return option.rect.adjusted(4, 4, -4, -4)

    def paint(self, painter: QPainter, option, index: QModelIndex) -> None:
        przycisk = QStyleOptionButton()
        przycisk.text = self._tekst
        przycisk.rect = self._prostokat(option)
        przycisk.state = QStyle.StateFlag.State_Enabled
        if option.state & QStyle.StateFlag.State_MouseOver:
            przycisk.state |= QStyle.StateFlag.State_MouseOver
        if option.state & QStyle.StateFlag.State_Selected:
            przycisk.state |= QStyle.StateFlag.State_Active
        QApplication.style().drawControl(
            QStyle.ControlElement.CE_PushButton, przycisk, painter
        )

    def editorEvent(self, event, model, option, index: QModelIndex) -> bool:
        if event.type() == QEvent.Type.MouseButtonRelease:
            pozycja = (
                event.position().toPoint()
                if hasattr(event, "position")
                else event.pos()
            )
            if self._prostokat(option).contains(pozycja):
                self.clicked.emit(index)
                return True
        return False
