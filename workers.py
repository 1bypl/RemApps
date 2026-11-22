"""Wątki robocze — długie operacje nie blokują okna."""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QThread, Signal


class Worker(QThread):
    """Uruchamia funkcję w tle i zwraca wynik sygnałem."""

    finished_ok = Signal(object)
    failed = Signal(str)

    def __init__(self, funkcja: Callable, *args, parent=None, **kwargs):
        super().__init__(parent)
        self._funkcja = funkcja
        self._args = args
        self._kwargs = kwargs

    def run(self) -> None:
        try:
            wynik = self._funkcja(*self._args, **self._kwargs)
            self.finished_ok.emit(wynik)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))
