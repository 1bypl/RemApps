"""Okna dialogowe RemApps."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox, QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout,
    QLabel, QPlainTextEdit, QPushButton, QVBoxLayout,
)

from .. import i18n
from ..core.detector import DistroInfo
from ..core.packages import Package
from ..core.remover import build_plan, jest_chroniony
from .icons import package_icon


class DetailsDialog(QDialog):
    def __init__(self, pakiet: Package, parent=None):
        super().__init__(parent)
        self.setWindowTitle(i18n.tr("details_title"))
        self.setMinimumWidth(460)
        layout = QVBoxLayout(self)

        naglowek = QHBoxLayout()
        ikona = QLabel()
        ikona.setPixmap(package_icon(pakiet.icon_hint, pakiet.source).pixmap(48, 48))
        naglowek.addWidget(ikona)
        tytul = QLabel(pakiet.name)
        tytul.setObjectName("title")
        naglowek.addWidget(tytul, 1)
        layout.addLayout(naglowek)

        formularz = QFormLayout()
        formularz.addRow(i18n.tr("detail_name") + ":", QLabel(pakiet.name))
        formularz.addRow(i18n.tr("detail_version") + ":", QLabel(pakiet.version or "—"))
        formularz.addRow(i18n.tr("detail_size") + ":", QLabel(pakiet.size_text))
        formularz.addRow(i18n.tr("detail_source") + ":", QLabel(pakiet.source))
        formularz.addRow(i18n.tr("detail_desc") + ":", QLabel(pakiet.description or "—"))
        if pakiet.origin_path:
            formularz.addRow(i18n.tr("detail_path") + ":", QLabel(pakiet.origin_path))
        layout.addLayout(formularz)

        przycisk = QPushButton(i18n.tr("close"))
        przycisk.clicked.connect(self.accept)
        layout.addWidget(przycisk, alignment=Qt.AlignmentFlag.AlignRight)


class ConfirmRemoveDialog(QDialog):
    def __init__(self, pakiet: Package, distro: DistroInfo, symulacja: bool,
                 pytaj_o_config: bool = True, parent=None):
        super().__init__(parent)
        self.pakiet = pakiet
        self.distro = distro
        self._sim = symulacja
        self.setWindowTitle(i18n.tr("remove_title", name=pakiet.name))
        self.setMinimumWidth(560)

        layout = QVBoxLayout(self)

        self.intro = QLabel(i18n.tr("remove_intro"))
        self.intro.setWordWrap(True)
        layout.addWidget(self.intro)

        ikona = QLabel()
        ikona.setPixmap(package_icon(pakiet.icon_hint, pakiet.source).pixmap(40, 40))
        nazwa = QLabel(f"<b>{pakiet.name}</b>  ·  {pakiet.version or ''}  ·  {pakiet.size_text}")
        rzad = QHBoxLayout()
        rzad.addWidget(ikona)
        rzad.addWidget(nazwa, 1)
        layout.addLayout(rzad)

        self.chk_deps = QCheckBox(i18n.tr("remove_deps"))
        self.chk_deps.setChecked(False)
        self.chk_config = QCheckBox(i18n.tr("remove_config"))
        self.chk_config.setChecked(pytaj_o_config and pakiet.source in ("rpm", "deb"))
        layout.addWidget(self.chk_deps)
        if pakiet.source in ("rpm", "deb"):
            layout.addWidget(self.chk_config)

        self.ostrzezenie = QLabel(i18n.tr("protected_warn"))
        self.ostrzezenie.setStyleSheet("color:#d9482f; font-weight:bold;")
        self.ostrzezenie.setWordWrap(True)
        jest_chronione = jest_chroniony(pakiet.name, distro)
        self.jest_chronione = jest_chronione
        self.ostrzezenie.setVisible(jest_chronione)
        layout.addWidget(self.ostrzezenie)

        self.chk_ryzyko = QCheckBox("Rozumiem ryzyko / I understand the risk")
        self.chk_ryzyko.setVisible(jest_chronione)
        layout.addWidget(self.chk_ryzyko)

        if symulacja:
            sym = QLabel(i18n.tr("remove_sim_note"))
            sym.setStyleSheet("color:#2fb35f; font-weight:bold;")
            sym.setWordWrap(True)
            layout.addWidget(sym)

        if pakiet.source in ("desktop", "appimage"):
            info_dod = QLabel(i18n.tr("desktop_remove_note"))
            info_dod.setObjectName("hint")
            info_dod.setWordWrap(True)
            layout.addWidget(info_dod)

        root_info = QLabel(i18n.tr("need_root"))
        root_info.setObjectName("hint")
        root_info.setWordWrap(True)
        layout.addWidget(root_info)

        layout.addWidget(QLabel(i18n.tr("preview_label")))
        self.podglad = QPlainTextEdit()
        self.podglad.setReadOnly(True)
        self.podglad.setMaximumHeight(90)
        self.podglad.setFont(QFont("Monospace", 10))
        layout.addWidget(self.podglad)

        self.box = QDialogButtonBox()
        self.btn_tak = QPushButton(i18n.tr("btn_remove"))
        self.btn_tak.setObjectName("danger")
        self.btn_tak.clicked.connect(self.accept)
        self.box.addButton(self.btn_tak, QDialogButtonBox.ButtonRole.AcceptRole)
        btn_nie = QPushButton(i18n.tr("btn_cancel"))
        btn_nie.clicked.connect(self.reject)
        self.box.addButton(btn_nie, QDialogButtonBox.ButtonRole.RejectRole)
        layout.addWidget(self.box)

        self.chk_deps.toggled.connect(self.odswiez_podglad)
        self.chk_config.toggled.connect(self.odswiez_podglad)
        self.chk_ryzyko.toggled.connect(self.odswiez_podglad)
        self.odswiez_podglad()

    def odswiez_podglad(self) -> None:
        plan = build_plan(
            self.pakiet, self.distro,
            zalezności=self.chk_deps.isChecked(),
            konfiguracja=self.chk_config.isChecked(),
            symulacja=self._symulacja,
        )
        tekst = plan.preview()
        if plan.config_files:
            tekst += "\n\n# " + i18n.tr("remove_config") + ":\n"
            tekst += "\n".join("#  " + p for p in plan.config_files[:20])
            if len(plan.config_files) > 20:
                tekst += f"\n#  ... (+{len(plan.config_files) - 20})"
        self.podglad.setPlainText(tekst)
        self.btn_tak.setEnabled(not self.jest_chronione
                                or self.chk_ryzyko.isChecked())

    @property
    def _symulacja(self) -> bool:
        return bool(self._sim)

    def ustaw_symulacje(self, wartosc: bool) -> None:
        self._sim = wartosc
        self.odswiez_podglad()

    def options(self) -> tuple[bool, bool]:
        return self.chk_deps.isChecked(), self.chk_config.isChecked()


class CleanupConfirmDialog(QDialog):
    def __init__(self, liczba: int, rozmiar: int, zawiera_browser: bool, parent=None):
        super().__init__(parent)
        from ..core.packages import human_size
        self.setWindowTitle(i18n.tr("clean_confirm_title"))
        self.setMinimumWidth(420)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(i18n.tr("clean_confirm_body",
                                        n=liczba, size=human_size(rozmiar))))
        if zawiera_browser:
            warn = QLabel(i18n.tr("clean_warn_browser"))
            warn.setWordWrap(True)
            warn.setStyleSheet("color:#d9482f; font-weight:bold;")
            layout.addWidget(warn)
        box = QDialogButtonBox()
        tak = QPushButton(i18n.tr("btn_remove"))
        tak.setObjectName("danger")
        tak.clicked.connect(self.accept)
        box.addButton(tak, QDialogButtonBox.ButtonRole.AcceptRole)
        nie = QPushButton(i18n.tr("btn_cancel"))
        nie.clicked.connect(self.reject)
        box.addButton(nie, QDialogButtonBox.ButtonRole.RejectRole)
        layout.addWidget(box)


class ReportDialog(QDialog):
    def __init__(self, tytul: str, tresc: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tytul)
        self.setMinimumSize(520, 320)
        layout = QVBoxLayout(self)
        pole = QPlainTextEdit(tresc)
        pole.setReadOnly(True)
        layout.addWidget(pole)
        przycisk = QPushButton(i18n.tr("close"))
        przycisk.clicked.connect(self.accept)
        layout.addWidget(przycisk, alignment=Qt.AlignmentFlag.AlignRight)
