"""Punkt wejścia aplikacji RemApps."""

from __future__ import annotations

import os
import sys
import traceback

SCIEZKA_LOGU = os.path.join(
    os.path.expanduser("~"), ".local", "share", "remapps", "error.log"
)


def _zapisz_log(tekst: str) -> None:
    """Zapisuje błąd do pliku, żeby użytkownik mógł go dosłać autorowi."""
    try:
        os.makedirs(os.path.dirname(SCIEZKA_LOGU), exist_ok=True)
        with open(SCIEZKA_LOGU, "w", encoding="utf-8") as plik:
            plik.write(tekst)
    except OSError:
        pass


def _obsluga_bledu(typ, wartosc, tb) -> None:
    tekst = "".join(traceback.format_exception(typ, wartosc, tb))
    sys.stderr.write(tekst)
    _zapisz_log(tekst)


sys.excepthook = _obsluga_bledu

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication, QMessageBox

    from .ui.icons import app_icon
    from .ui.main_window import MainWindow
except BaseException:  # noqa: BLE001
    _zapisz_log(traceback.format_exc())
    raise


def main() -> int:
    try:
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        aplikacja = QApplication(sys.argv)
        aplikacja.setApplicationName("RemApps")
        aplikacja.setApplicationDisplayName("RemApps")
        aplikacja.setWindowIcon(app_icon())
        okno = MainWindow()
        okno.show()
        return aplikacja.exec()
    except BaseException as exc:  # noqa: BLE001
        tekst = traceback.format_exc()
        sys.stderr.write(tekst)
        _zapisz_log(tekst)
        try:
            QMessageBox.critical(
                None, "RemApps — błąd uruchomienia",
                f"Nie udało się uruchomić programu:\n{exc}\n\n"
                f"Szczegóły zapisano w:\n{SCIEZKA_LOGU}",
            )
        except Exception:
            print(tekst, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
