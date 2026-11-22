"""Główne okno RemApps."""

from __future__ import annotations

import os
import subprocess

from PySide6.QtCore import Qt, QSortFilterProxyModel, QTimer
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDialog, QFrame, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMessageBox,
    QProgressBar, QPushButton, QScrollArea, QStackedWidget, QTableView,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from .. import __version__, i18n
from ..core import cleaner, packages as packages_mod, settings as settings_mod
from ..core.detector import detect
from ..core.packages import (
    Package, cache_key, human_size, scan_all, usun_cache, usun_z_cache, wczytaj_cache,
)
from ..core.remover import aftercare, build_plan, sprawdz_czy_istnieje, wykonaj
from .delegate import RemoveButtonDelegate
from .dialogs import CleanupConfirmDialog, ConfirmRemoveDialog, DetailsDialog, ReportDialog
from .icons import app_icon, logo_pixmap, nav_icon, package_icon
from .loading import LoadingWidget
from .styles import stylesheet
from .workers import Worker

GITHUB_URL = "https://github.com/1bypl/RemApps"
SEARCH_ROLE = Qt.ItemDataRole.UserRole + 100

GRUPY_ETYKIETY = {
    "trash": "clean_trash",
    "orphans": "clean_orphans",
    "caches": "clean_caches",
    "browser": "clean_browser",
    "logs": "clean_logs",
}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ustawienia = settings_mod.wczytaj()
        i18n.set_language(self.ustawienia.get("language", "pl"))
        self.distro = detect()
        self.packages: list[Package] = []
        self.clean_items: list[cleaner.CleanItem] = []
        self._worker: Worker | None = None
        self._wypelniane: list[Package] = []
        self._wiersze_pakiety: list[Package] = []
        self._wiersz = 0
        self._generacja = 0
        self._workers: list[Worker] = []
        self._zamykanie = False
        self._ustawiam = False
        self._system_dark = self._system_czy_ciemny()
        self.setWindowIcon(app_icon())
        self.resize(1120, 720)
        self.setMinimumSize(900, 600)
        self.aktywny_motyw = self._ustal_motyw()
        self.setStyleSheet(stylesheet(self.aktywny_motyw))
        self._zbuduj_interfejs()
        self.retranslate()

        # Jeśli mamy zapisaną listę, pokazujemy ją NATYCHMIAST, a świeży
        # skan robimy w tle — program nie czeka kilku minut przy starcie.
        klucz = cache_key(self.distro, self.mode_combo.currentData() or "standard")
        zapisane = wczytaj_cache(klucz, max_age=None)
        if zapisane:
            self.packages = zapisane
            self._wypelnij_tabele(zapisane)
            self.table_stack.setCurrentWidget(self.table)
            self.status(i18n.tr("status_ready"))
            QTimer.singleShot(50, lambda: self.odswiez_liste(False))
        else:
            QTimer.singleShot(50, self.odswiez_liste)

    # ------------------------------------------------------------ pomocnicze
    def _system_czy_ciemny(self) -> bool:
        """Sprawdza motyw systemowy (KDE, GNOME, zmienne środowiskowe)."""
        # Wynik liczymy raz przy starcie — odpytywanie gsettings przy każdej
        # zmianie ustawienia potrafiło wstrzymać interfejs na kilka sekund.
        if hasattr(self, "_system_dark"):
            return self._system_dark
        # KDE Plasma
        try:
            kdeglobals = os.path.join(os.path.expanduser("~"), ".config", "kdeglobals")
            if os.path.exists(kdeglobals):
                with open(kdeglobals, encoding="utf-8", errors="replace") as plik:
                    for linia in plik:
                        if linia.strip().lower().startswith("colorscheme="):
                            schemat = linia.split("=", 1)[1].strip().lower()
                            return "dark" in schemat
        except OSError:
            pass
        # GNOME / GTK
        try:
            wynik = subprocess.run(
                ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
                capture_output=True, text=True, errors="replace", timeout=3,
            )
            if wynik.returncode == 0 and "dark" in wynik.stdout.lower():
                return True
        except (OSError, subprocess.SubprocessError):
            pass
        if "dark" in os.environ.get("GTK_THEME", "").lower():
            return True
        # Ostatecznie paleta Qt
        try:
            return self.palette().window().color().lightness() < 128
        except Exception:
            return False

    def _ustal_motyw(self) -> str:
        m = self.ustawienia.get("theme", "auto")
        if m != "auto":
            return m
        return "dark" if self._system_czy_ciemny() else "light"

    def status(self, tekst: str) -> None:
        self.statusBar().showMessage(tekst)

    def _tlo_roboty(self, funkcja, *args, on_done, on_error=None, status=""):
        if self._zamykanie:
            return
        if status:
            self.status(status)
        worker = Worker(funkcja, *args, parent=self)

        def _po(wynik):
            if not self._zamykanie:
                on_done(wynik)

        def _blad2(msg):
            if not self._zamykanie:
                (on_error or self._blad)(msg)

        worker.finished_ok.connect(_po)
        worker.failed.connect(_blad2)
        worker.finished.connect(lambda w=worker: self._zwolnij_worker(w))
        self._workers.append(worker)
        self._worker = worker
        worker.start()

    def _zwolnij_worker(self, worker: Worker) -> None:
        try:
            worker.finished_ok.disconnect()
            worker.failed.disconnect()
            worker.finished.disconnect()
        except (RuntimeError, TypeError):
            pass
        if worker in self._workers:
            self._workers.remove(worker)
        if self._worker is worker:
            self._worker = None

    def _blad(self, komunikat: str) -> None:
        if hasattr(self, "table_stack"):
            self.table_stack.setCurrentWidget(self.table)
        QMessageBox.critical(self, i18n.tr("error_title"), komunikat)
        self.status(i18n.tr("status_ready"))

    def closeEvent(self, event) -> None:
        """Spokojnie zatrzymuje wątki — bez terminate(), które może wywalić Pythona."""
        self._zamykanie = True
        for worker in list(self._workers):
            try:
                worker.finished_ok.disconnect()
                worker.failed.disconnect()
                worker.finished.disconnect()
            except (RuntimeError, TypeError):
                pass
            try:
                worker.requestInterruption()
            except AttributeError:
                pass
            worker.quit()
            worker.wait(5000)
        self._workers.clear()
        self._worker = None
        super().closeEvent(event)

    # ------------------------------------------------------------ interfejs
    def _zbuduj_interfejs(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        glowny = QHBoxLayout(central)
        glowny.setContentsMargins(0, 0, 0, 0)
        glowny.setSpacing(0)

        # --- pasek boczny
        sidebar = QFrame()
        sidebar.setObjectName("card")
        sidebar.setMinimumWidth(230)
        sidebar.setMaximumWidth(250)
        pion = QVBoxLayout(sidebar)
        pion.setContentsMargins(14, 18, 14, 14)

        logo = QLabel()
        logo.setPixmap(logo_pixmap(96))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pion.addWidget(logo)

        nazwa = QLabel(i18n.tr("app_name"))
        nazwa.setObjectName("title")
        nazwa.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pion.addWidget(nazwa)

        self.lbl_tagline = QLabel(i18n.tr("app_tagline"))
        self.lbl_tagline.setObjectName("subtitle")
        self.lbl_tagline.setWordWrap(True)
        self.lbl_tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pion.addWidget(self.lbl_tagline)
        pion.addSpacing(20)

        self.nav = QListWidget()
        self.nav.setObjectName("nav")
        self.nav.setIconSize(self.nav.iconSize())
        for tekst, klucz, ikona in (
            ("nav_programs", 0, "programy"),
            ("nav_cleanup", 1, "czyszczenie"),
            ("nav_settings", 2, "ustawienia"),
            ("nav_about", 3, "o"),
        ):
            item = QListWidgetItem(nav_icon(ikona), i18n.tr(tekst))
            item.setData(Qt.ItemDataRole.UserRole, klucz)
            item.setSizeHint(item.sizeHint().expandedTo(self.nav.iconSize()))
            self.nav.addItem(item)
        self.nav.setCurrentRow(0)
        self.nav.currentRowChanged.connect(self._zmien_strone)
        pion.addWidget(self.nav, 1)

        system = QLabel(f"{self.distro.name}\n{self.distro.package_manager}")
        system.setObjectName("hint")
        system.setWordWrap(True)
        system.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pion.addWidget(system)
        glowny.addWidget(sidebar)

        # --- strony
        self.pages = QStackedWidget()
        self.page_programs = self._strona_programy()
        self.page_cleanup = self._strona_czyszczenie()
        self.page_settings = self._strona_ustawienia()
        self.page_about = self._strona_o()
        for strona in (self.page_programs, self.page_cleanup,
                       self.page_settings, self.page_about):
            self.pages.addWidget(strona)
        glowny.addWidget(self.pages, 1)

        self.statusBar().showMessage(i18n.tr("status_ready"))

    def _strona_programy(self) -> QWidget:
        strona = QWidget()
        pion = QVBoxLayout(strona)
        pion.setContentsMargins(22, 18, 22, 18)

        self.lbl_programs_title = QLabel(i18n.tr("programs_title"))
        self.lbl_programs_title.setObjectName("title")
        pion.addWidget(self.lbl_programs_title)
        self.lbl_programs_hint = QLabel(i18n.tr("programs_hint"))
        self.lbl_programs_hint.setObjectName("subtitle")
        self.lbl_programs_hint.setWordWrap(True)
        pion.addWidget(self.lbl_programs_hint)

        narzedzia = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText(i18n.tr("search_placeholder"))
        self.search.setClearButtonEnabled(True)
        # Wyszukiwanie odroczone o 250 ms — nie przebudowujemy listy
        # przy każdej literze (na 2000 pakietów byłoby to bardzo wolne).
        self._wyszukiwanie_timer = QTimer(self)
        self._wyszukiwanie_timer.setSingleShot(True)
        self._wyszukiwanie_timer.timeout.connect(
            lambda: self._filtruj(self.search.text())
        )
        self.search.textChanged.connect(
            lambda: self._wyszukiwanie_timer.start(120)
        )
        narzedzia.addWidget(self.search, 1)

        self.lbl_mode = QLabel(i18n.tr("mode_label"))
        narzedzia.addWidget(self.lbl_mode)
        self.mode_combo = QComboBox()
        for klucz in ("mode_standard", "mode_exact", "mode_dirs"):
            self.mode_combo.addItem(i18n.tr(klucz), klucz.split("_")[1])
        domyslny = self.ustawienia.get("search_mode", "standard")
        idx = self.mode_combo.findData(domyslny)
        self.mode_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.mode_combo.currentIndexChanged.connect(self._zmien_tryb)
        narzedzia.addWidget(self.mode_combo)

        self.btn_refresh = QPushButton(i18n.tr("refresh"))
        self.btn_refresh.setObjectName("primary")
        self.btn_refresh.clicked.connect(lambda: self.odswiez_liste(True, True))
        narzedzia.addWidget(self.btn_refresh)
        pion.addLayout(narzedzia)

        self.lbl_found = QLabel("")
        self.lbl_found.setObjectName("hint")
        pion.addWidget(self.lbl_found)

        self.model = QStandardItemModel(0, 5)
        self.model.setHorizontalHeaderLabels([
            i18n.tr("col_program"), i18n.tr("col_version"), i18n.tr("col_size"),
            i18n.tr("col_source"), i18n.tr("col_action"),
        ])
        # Filtrowanie odbywa się w bibliotece Qt (szybko), nie w Pythonie
        self.proxy = QSortFilterProxyModel()
        self.proxy.setSourceModel(self.model)
        self.proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.proxy.setFilterKeyColumn(0)
        self.proxy.setFilterRole(SEARCH_ROLE)

        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self._szczegoly)
        self.remove_delegate = RemoveButtonDelegate(i18n.tr("remove_btn"))
        self.remove_delegate.clicked.connect(self._na_klik_usuniecia)
        self.table.setItemDelegateForColumn(4, self.remove_delegate)
        naglowek = self.table.horizontalHeader()
        naglowek.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        naglowek.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        naglowek.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        naglowek.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        naglowek.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        # Ekran ładowania wyświetlany w czasie skanowania systemu
        self.loading = LoadingWidget()
        self.table_stack = QStackedWidget()
        self.table_stack.addWidget(self.table)
        self.table_stack.addWidget(self.loading)
        self.table_stack.setCurrentWidget(self.loading)
        pion.addWidget(self.table_stack, 1)
        return strona

    def _strona_czyszczenie(self) -> QWidget:
        strona = QWidget()
        pion = QVBoxLayout(strona)
        pion.setContentsMargins(22, 18, 22, 18)

        self.lbl_clean_title = QLabel(i18n.tr("cleanup_title"))
        self.lbl_clean_title.setObjectName("title")
        pion.addWidget(self.lbl_clean_title)
        self.lbl_clean_hint = QLabel(i18n.tr("cleanup_hint"))
        self.lbl_clean_hint.setObjectName("subtitle")
        self.lbl_clean_hint.setWordWrap(True)
        pion.addWidget(self.lbl_clean_hint)

        self.chk_grupy = {}
        for grupa, klucz in GRUPY_ETYKIETY.items():
            chk = QCheckBox(i18n.tr(klucz))
            chk.setChecked(grupa != "logs")
            self.chk_grupy[grupa] = chk
            pion.addWidget(chk)

        rzad = QHBoxLayout()
        self.btn_scan = QPushButton(i18n.tr("scan_btn"))
        self.btn_scan.setObjectName("primary")
        self.btn_scan.clicked.connect(self.skanuj_czyszczenie)
        rzad.addWidget(self.btn_scan)
        self.btn_clean = QPushButton(i18n.tr("clean_execute"))
        self.btn_clean.setObjectName("danger")
        self.btn_clean.clicked.connect(self.wykonaj_czyszczenie)
        rzad.addWidget(self.btn_clean)
        rzad.addStretch(1)
        pion.addLayout(rzad)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        pion.addWidget(self.progress)

        self.lbl_results = QLabel(i18n.tr("group_results"))
        self.lbl_results.setObjectName("hint")
        pion.addWidget(self.lbl_results)
        self.tree = QTreeWidget()
        self.tree.setColumnCount(3)
        self.tree.setHeaderHidden(True)
        self.tree.setRootIsDecorated(True)
        self.tree.itemChanged.connect(self._na_drzewie_zmiany)
        pion.addWidget(self.tree, 1)
        return strona

    def _na_drzewie_zmiany(self, item, kolumna: int) -> None:
        """Zaznaczenie grupy zaznacza/odznacza wszystkie jej elementy."""
        if kolumna != 0:
            return
        self.tree.blockSignals(True)
        if item.childCount() > 0:
            stan = item.checkState(0)
            for i in range(item.childCount()):
                item.child(i).setCheckState(0, stan)
        else:
            rodzic = item.parent()
            if rodzic is not None:
                stany = [rodzic.child(i).checkState(0) for i in range(rodzic.childCount())]
                if all(s == Qt.CheckState.Checked for s in stany):
                    rodzic.setCheckState(0, Qt.CheckState.Checked)
                elif all(s == Qt.CheckState.Unchecked for s in stany):
                    rodzic.setCheckState(0, Qt.CheckState.Unchecked)
                else:
                    rodzic.setCheckState(0, Qt.CheckState.PartiallyChecked)
        self.tree.blockSignals(False)

    def _strona_ustawienia(self) -> QWidget:
        strona = QWidget()
        pion = QVBoxLayout(strona)
        pion.setContentsMargins(22, 18, 22, 18)
        self.lbl_settings_title = QLabel(i18n.tr("settings_title"))
        self.lbl_settings_title.setObjectName("title")
        pion.addWidget(self.lbl_settings_title)

        karta = QFrame()
        karta.setObjectName("card")
        form = QVBoxLayout(karta)

        self.lbl_lang = QLabel(i18n.tr("set_language"))
        form.addWidget(self.lbl_lang)
        self.lang_combo = QComboBox()
        for kod, nazwa in i18n.JESTZYKI.items():
            self.lang_combo.addItem(nazwa, kod)
        aktualny = self.ustawienia.get("language", "pl")
        self.lang_combo.setCurrentIndex(max(0, self.lang_combo.findData(aktualny)))
        self.lang_combo.currentIndexChanged.connect(self._zmien_jezyk)
        form.addWidget(self.lang_combo)

        self.lbl_theme = QLabel(i18n.tr("set_theme"))
        form.addWidget(self.lbl_theme)
        self.theme_combo = QComboBox()
        for etykieta, dane in (("theme_light", "light"), ("theme_dark", "dark"),
                               ("theme_auto", "auto")):
            self.theme_combo.addItem(i18n.tr(etykieta), dane)
        self.theme_combo.setCurrentIndex(max(0, self.theme_combo.findData(
            self.ustawienia.get("theme", "auto"))))
        self.theme_combo.currentIndexChanged.connect(self._zmien_motyw)
        form.addWidget(self.theme_combo)
        self.lbl_theme_status = QLabel("")
        self.lbl_theme_status.setObjectName("hint")
        form.addWidget(self.lbl_theme_status)

        self.lbl_def_mode = QLabel(i18n.tr("set_mode"))
        form.addWidget(self.lbl_def_mode)
        self.def_mode_combo = QComboBox()
        for klucz in ("mode_standard", "mode_exact", "mode_dirs"):
            self.def_mode_combo.addItem(i18n.tr(klucz), klucz.split("_")[1])
        self.def_mode_combo.setCurrentIndex(max(0, self.def_mode_combo.findData(
            self.ustawienia.get("search_mode", "standard"))))
        self.def_mode_combo.currentIndexChanged.connect(self._zmien_domyslny_tryb)
        form.addWidget(self.def_mode_combo)

        self.chk_sim = QCheckBox(i18n.tr("set_sim"))
        self.chk_sim.setChecked(bool(self.ustawienia.get("simulation", False)))
        self.chk_sim.toggled.connect(lambda v: self._zapisz("simulation", v))
        form.addWidget(self.chk_sim)
        self.lbl_sim_hint = QLabel(i18n.tr("set_sim_hint"))
        self.lbl_sim_hint.setObjectName("hint")
        self.lbl_sim_hint.setWordWrap(True)
        form.addWidget(self.lbl_sim_hint)

        self.chk_config = QCheckBox(i18n.tr("set_config_ask"))
        self.chk_config.setChecked(bool(self.ustawienia.get("ask_config", True)))
        self.chk_config.toggled.connect(lambda v: self._zapisz("ask_config", v))
        form.addWidget(self.chk_config)

        self.btn_reset = QPushButton(i18n.tr("set_reset"))
        self.btn_reset.clicked.connect(self._reset_ustawien)
        form.addWidget(self.btn_reset)
        pion.addWidget(karta)
        pion.addStretch(1)
        return strona

    def _strona_o(self) -> QWidget:
        strona = QWidget()
        pion = QVBoxLayout(strona)
        pion.setContentsMargins(0, 0, 0, 0)
        suwak = QScrollArea()
        suwak.setWidgetResizable(True)
        zawartosc = QWidget()
        pion2 = QVBoxLayout(zawartosc)
        pion2.setContentsMargins(28, 22, 28, 22)
        pion2.setSpacing(10)

        logo = QLabel()
        logo.setPixmap(logo_pixmap(140))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pion2.addWidget(logo)

        self.lbl_about_title = QLabel(i18n.tr("about_title"))
        self.lbl_about_title.setObjectName("title")
        self.lbl_about_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pion2.addWidget(self.lbl_about_title)

        self.lbl_about_tag = QLabel(i18n.tr("app_tagline"))
        self.lbl_about_tag.setObjectName("subtitle")
        self.lbl_about_tag.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pion2.addWidget(self.lbl_about_tag)
        pion2.addSpacing(14)

        self.sekcje = {}
        for klucz in ("about_purpose", "about_how", "about_arch", "about_license",
                      "about_disclaimer", "about_author"):
            lbl = QLabel(i18n.tr(klucz))
            lbl.setWordWrap(True)
            lbl.setTextFormat(Qt.TextFormat.RichText)
            lbl.setObjectName("card")
            lbl.setStyleSheet(self._styl_karty())
            pion2.addWidget(lbl)
            self.sekcje[klucz] = lbl

        self.lbl_github = QLabel(f'<a href="{GITHUB_URL}">{i18n.tr("about_github")}</a>')
        self.lbl_github.setObjectName("link")
        self.lbl_github.setOpenExternalLinks(True)
        pion2.addWidget(self.lbl_github)

        self.lbl_version = QLabel(i18n.tr("about_version", v=__version__))
        self.lbl_version.setObjectName("hint")
        pion2.addWidget(self.lbl_version)
        pion2.addStretch(1)
        suwak.setWidget(zawartosc)
        pion.addWidget(suwak)
        return strona

    def _odswiez_styl_o(self) -> None:
        """Karty w zakładce „O programie" muszą zmieniać kolor wraz ze skórką."""
        for lbl in getattr(self, "sekcje", {}).values():
            lbl.setStyleSheet(self._styl_karty())

    def _styl_karty(self) -> str:
        return ("background:#ffffff; border:1px solid #d8e2da; "
                "border-radius:14px; padding:14px;") if self.aktywny_motyw != "dark" else (
                "background:#252b2f; border:1px solid #394247; "
                "border-radius:14px; padding:14px;")

    # ------------------------------------------------------------ retranslate
    def retranslate(self) -> None:
        self.lbl_tagline.setText(i18n.tr("app_tagline"))
        self.lbl_programs_title.setText(i18n.tr("programs_title"))
        self.lbl_programs_hint.setText(i18n.tr("programs_hint"))
        self.search.setPlaceholderText(i18n.tr("search_placeholder"))
        self.lbl_mode.setText(i18n.tr("mode_label"))
        self.btn_refresh.setText(i18n.tr("refresh"))
        self.remove_delegate.setText(i18n.tr("remove_btn"))
        self.model.setHorizontalHeaderLabels([
            i18n.tr("col_program"), i18n.tr("col_version"), i18n.tr("col_size"),
            i18n.tr("col_source"), i18n.tr("col_action"),
        ])
        for i in range(self.model.rowCount()):
            self.model.setItem(i, 4, QStandardItem(i18n.tr("remove_btn")))
        self.lbl_clean_title.setText(i18n.tr("cleanup_title"))
        self.lbl_clean_hint.setText(i18n.tr("cleanup_hint"))
        self.btn_scan.setText(i18n.tr("scan_btn"))
        self.btn_clean.setText(i18n.tr("clean_execute"))
        self.lbl_results.setText(i18n.tr("group_results"))
        for i in range(self.nav.count()):
            item = self.nav.item(i)
            item.setText(i18n.tr(["nav_programs", "nav_cleanup", "nav_settings",
                                  "nav_about"][i]))
        for i, klucz in enumerate(("mode_standard", "mode_exact", "mode_dirs")):
            self.mode_combo.setItemText(i, i18n.tr(klucz))
            self.def_mode_combo.setItemText(i, i18n.tr(klucz))
        for i, (etykieta, _) in enumerate((("theme_light", ""), ("theme_dark", ""),
                                            ("theme_auto", ""))):
            self.theme_combo.setItemText(i, i18n.tr(etykieta))
        self._odswiez_status_motywu()
        self.lbl_settings_title.setText(i18n.tr("settings_title"))
        self.lbl_lang.setText(i18n.tr("set_language"))
        self.lbl_theme.setText(i18n.tr("set_theme"))
        self.lbl_def_mode.setText(i18n.tr("set_mode"))
        self.chk_sim.setText(i18n.tr("set_sim"))
        self.lbl_sim_hint.setText(i18n.tr("set_sim_hint"))
        self.chk_config.setText(i18n.tr("set_config_ask"))
        self.btn_reset.setText(i18n.tr("set_reset"))
        for grupa, klucz in GRUPY_ETYKIETY.items():
            self.chk_grupy[grupa].setText(i18n.tr(klucz))
        self.lbl_about_title.setText(i18n.tr("about_title"))
        self.lbl_about_tag.setText(i18n.tr("app_tagline"))
        for klucz, lbl in self.sekcje.items():
            lbl.setText(i18n.tr(klucz))
            lbl.setStyleSheet(self._styl_karty())
        self.lbl_github.setText(f'<a href="{GITHUB_URL}">{i18n.tr("about_github")}</a>')
        self.lbl_version.setText(i18n.tr("about_version", v=__version__))
        self.loading.retranslate()
        self.status(i18n.tr("status_ready"))
        self._aktualizuj_teksty_listy()

    def _aktualizuj_teksty_listy(self) -> None:
        """Zmienia napisy w już istniejącej liście (bez jej przebudowy)."""
        if not hasattr(self, "model"):
            return
        self.model.blockSignals(True)
        for i, p in enumerate(self._wiersze_pakiety):
            pierwsza = self.model.item(i, 0)
            if pierwsza is not None:
                pierwsza.setData(
                    " ".join((p.name, p.description, p.package_id, p.source)).lower(),
                    SEARCH_ROLE,
                )
            self.model.setItem(i, 3, QStandardItem(i18n.tr("src_" + p.source)))
            self.model.setItem(i, 4, QStandardItem(i18n.tr("remove_btn")))
        self.model.blockSignals(False)
        self.proxy.invalidate()
        self.lbl_found.setText(i18n.tr("found_count", n=self.proxy.rowCount()))

    # ------------------------------------------------------------ nawigacja
    def _zmien_strone(self, indeks: int) -> None:
        self.pages.setCurrentIndex(indeks)

    def _zapisz(self, klucz: str, wartosc) -> None:
        self.ustawienia[klucz] = wartosc
        settings_mod.zapisz(self.ustawienia)

    def _zmien_jezyk(self) -> None:
        kod = self.lang_combo.currentData()
        self._zapisz("language", kod)
        i18n.set_language(kod)
        self.retranslate()

    def _odswiez_status_motywu(self) -> None:
        if not hasattr(self, "lbl_theme_status"):
            return
        wybrany = self.ustawienia.get("theme", "auto")
        if wybrany == "auto":
            system = "dark" if self._system_czy_ciemny() else "light"
            self.lbl_theme_status.setText(
                f"{i18n.tr('theme_auto')}: {i18n.tr('theme_' + system)}"
            )
        else:
            self.lbl_theme_status.setText(i18n.tr("theme_" + wybrany))

    def _zmien_motyw(self) -> None:
        motyw = self.theme_combo.currentData()
        self._zapisz("theme", motyw)
        self.aktywny_motyw = self._ustal_motyw()
        self.setStyleSheet(stylesheet(self.aktywny_motyw))
        self._odswiez_styl_o()
        self._odswiez_status_motywu()

    def _zmien_tryb(self) -> None:
        if self._ustawiam:
            return
        self.odswiez_liste()

    def _zmien_domyslny_tryb(self) -> None:
        # Zmiana domyślnego trybu nie musi przeliczać aktualnej listy.
        self._zapisz("search_mode", self.def_mode_combo.currentData())

    def _reset_ustawien(self) -> None:
        self._ustawiam = True
        self.ustawienia = dict(settings_mod.DOMYSLNE)
        settings_mod.zapisz(self.ustawienia)
        i18n.set_language("pl")
        self.lang_combo.setCurrentIndex(self.lang_combo.findData("pl"))
        self.theme_combo.setCurrentIndex(self.theme_combo.findData("auto"))
        self.def_mode_combo.setCurrentIndex(self.def_mode_combo.findData("standard"))
        self.mode_combo.setCurrentIndex(self.mode_combo.findData("standard"))
        self._ustawiam = False
        self.chk_sim.setChecked(False)
        self.chk_config.setChecked(True)
        self.aktywny_motyw = self._ustal_motyw()
        self.setStyleSheet(stylesheet(self.aktywny_motyw))
        self._odswiez_styl_o()
        self._odswiez_status_motywu()
        self.retranslate()

    # ------------------------------------------------------------ programy
    def odswiez_liste(self, pokaz_ladowanie: bool = True, wymus: bool = False) -> None:
        tryb = self.mode_combo.currentData() or "standard"
        if wymus:
            usun_cache()
        self.loading.retranslate()
        if pokaz_ladowanie:
            self.table_stack.setCurrentWidget(self.loading)
        self._tlo_roboty(scan_all, self.distro, tryb,
                         on_done=self._po_skanowaniu,
                         status=i18n.tr("status_scanning"))

    def _po_skanowaniu(self, pakiety: list[Package]) -> None:
        self.packages = pakiety
        self.table_stack.setCurrentWidget(self.table)
        tekst = self.search.text().strip()
        self._wypelnij_tabele(pakiety)
        if tekst:
            self._filtruj(tekst)
        czasy = packages_mod.OSTATNI_CZASY
        if czasy:
            opis = ", ".join(f"{k}: {v}s" for k, v in czasy.items())
            self.status(f"{i18n.tr('status_ready')} — skan: {opis}")
        else:
            self.status(i18n.tr("status_ready"))

    def _wypelnij_tabele(self, pakiety: list[Package]) -> None:
        """Wypełnia model partiami po 150 wierszy, żeby okno się nie blokowało."""
        self._generacja += 1
        self._wypelniane = list(pakiety)
        self._wiersze_pakiety = list(pakiety)
        self._wiersz = 0
        self.model.setRowCount(0)
        self.model.setRowCount(len(pakiety))
        self.lbl_found.setText(i18n.tr("found_count", n=len(pakiety)))
        self._dodaj_wiersze(self._generacja)

    def _dodaj_wiersze(self, generacja: int) -> None:
        if generacja != self._generacja:
            return
        koniec = min(self._wiersz + 150, len(self._wypelniane))
        self.model.blockSignals(True)
        self.table.setUpdatesEnabled(False)
        for i in range(self._wiersz, koniec):
            p = self._wypelniane[i]
            item_nazwa = QStandardItem(p.name)
            item_nazwa.setIcon(package_icon(p.icon_hint, p.source))
            item_nazwa.setToolTip(p.description)
            #Tekst do wyszukiwania: nazwa, opis, ID i źródło
            item_nazwa.setData(
                " ".join((p.name, p.description, p.package_id, p.source)).lower(),
                SEARCH_ROLE,
            )
            self.model.setItem(i, 0, item_nazwa)
            self.model.setItem(i, 1, QStandardItem(p.version or "—"))
            self.model.setItem(i, 2, QStandardItem(p.size_text))
            self.model.setItem(i, 3, QStandardItem(i18n.tr("src_" + p.source)))
            self.model.setItem(i, 4, QStandardItem(i18n.tr("remove_btn")))
        self.table.setUpdatesEnabled(True)
        self.model.blockSignals(False)
        self._wiersz = koniec
        if self._wiersz < len(self._wypelniane):
            QTimer.singleShot(0, lambda: self._dodaj_wiersze(generacja))
        else:
            self.proxy.invalidate()

    def _filtruj(self, tekst: str) -> None:
        """Filtrowanie w modelu Qt — szybkie nawet dla tysięcy wierszy."""
        self.proxy.setFilterFixedString(tekst.strip())
        self.lbl_found.setText(i18n.tr("found_count", n=self.proxy.rowCount()))

    def _pakiet_z_wiersza(self, wiersz: int) -> Package | None:
        if 0 <= wiersz < len(self._wiersze_pakiety):
            return self._wiersze_pakiety[wiersz]
        return None

    def _usun_z_listy(self, pakiet: Package) -> None:
        """Usuwa jeden wiersz bez ponownego skanowania całego systemu."""
        klucz = cache_key(self.distro, self.mode_combo.currentData() or "standard")
        usun_z_cache(klucz, pakiet.name, pakiet.source)
        indeks = next(
            (i for i, p in enumerate(self._wiersze_pakiety)
             if p.name == pakiet.name and p.source == pakiet.source), -1,
        )
        if indeks < 0 or self._wiersz < len(self._wypelniane):
            # Lista jeszcze się wypełnia — bezpiecznie wczytaj ją z cache
            self.odswiez_liste(False)
            return
        for lista in (self.packages, self._wypelniane, self._wiersze_pakiety):
            if 0 <= indeks < len(lista):
                lista.pop(indeks)
        self.model.removeRow(indeks)
        self._wiersz = len(self._wypelniane)
        self._generacja += 1
        self.proxy.invalidate()
        self.lbl_found.setText(i18n.tr("found_count", n=self.proxy.rowCount()))

    def _na_klik_usuniecia(self, index) -> None:
        zrodlo = self.proxy.mapToSource(index)
        pakiet = self._pakiet_z_wiersza(zrodlo.row())
        if pakiet:
            self._usun(pakiet)

    def _szczegoly(self, index) -> None:
        zrodlo = self.proxy.mapToSource(index)
        pakiet = self._pakiet_z_wiersza(zrodlo.row())
        if pakiet:
            DetailsDialog(pakiet, self).exec()

    def _usun(self, pakiet: Package) -> None:
        symulacja = bool(self.ustawienia.get("simulation", False))
        dlg = ConfirmRemoveDialog(pakiet, self.distro, symulacja,
                                  bool(self.ustawienia.get("ask_config", True)), self)
        dlg.ustaw_symulacje(symulacja)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        deps, cfg = dlg.options()
        plan = build_plan(pakiet, self.distro, zalezności=deps,
                          konfiguracja=cfg, symulacja=symulacja)

        def zadanie():
            ok, log = wykonaj(plan)
            dodatkowe = aftercare(plan, self.distro, symulacja)
            pozostalo = sprawdz_czy_istnieje(pakiet) if (ok and not symulacja) else False
            return ok, log, dodatkowe, pozostalo

        def po(rezultat):
            ok, log, dodatkowe, pozostalo = rezultat
            if dodatkowe:
                log += "\n\nUsunięto dodatkowo:\n" + "\n".join(dodatkowe)
            if symulacja:
                QMessageBox.information(self, i18n.tr("remove_title", name=pakiet.name),
                                        i18n.tr("remove_sim_ok") + "\n\n" + log[:1500])
            elif pozostalo:
                ReportDialog(
                    i18n.tr("remove_still_exists", name=pakiet.name),
                    i18n.tr("remove_still_exists", name=pakiet.name) + "\n\n" + log,
                    self,
                ).exec()
            elif ok:
                QMessageBox.information(self, i18n.tr("remove_title", name=pakiet.name),
                                        i18n.tr("remove_ok", name=pakiet.name))
                self._usun_z_listy(pakiet)
            else:
                ReportDialog(i18n.tr("remove_fail", name=pakiet.name), log, self).exec()
            self.status(i18n.tr("status_ready"))

        self._tlo_roboty(zadanie, on_done=po, on_error=self._blad,
                         status=i18n.tr("status_removing"))

    # ------------------------------------------------------------ czyszczenie
    def skanuj_czyszczenie(self) -> None:
        wybrane = {g for g, chk in self.chk_grupy.items() if chk.isChecked()}
        self.tree.clear()
        self.clean_items = []
        self.progress.setVisible(True)
        self.btn_scan.setEnabled(False)

        def po(pozycje):
            self.clean_items = pozycje
            self.progress.setVisible(False)
            self.btn_scan.setEnabled(True)
            self._wypelnij_drzewo(pozycje)
            self.status(i18n.tr("status_ready"))

        def blad(msg):
            self.progress.setVisible(False)
            self.btn_scan.setEnabled(True)
            self._blad(msg)

        self._tlo_roboty(cleaner.scan_all, wybrane, on_done=po, on_error=blad,
                         status=i18n.tr("status_scanning"))

    def _wypelnij_drzewo(self, pozycje: list[cleaner.CleanItem]) -> None:
        self.tree.blockSignals(True)
        grupy: dict[str, list[cleaner.CleanItem]] = {}
        for p in pozycje:
            grupy.setdefault(p.group, []).append(p)
        for grupa, lista in grupy.items():
            nadrzedny = QTreeWidgetItem(self.tree, [i18n.tr(GRUPY_ETYKIETY[grupa])])
            nadrzedny.setFlags(nadrzedny.flags() | Qt.ItemFlag.ItemIsUserCheckable
                               | Qt.ItemFlag.ItemIsTristate)
            nadrzedny.setCheckState(0, Qt.CheckState.Checked)
            for p in lista:
                dziecko = QTreeWidgetItem(nadrzedny, [
                    f"{p.label}  ({human_size(p.size)})", p.path,
                    "root" if p.needs_root else "",
                ])
                dziecko.setFlags(dziecko.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                dziecko.setCheckState(0, Qt.CheckState.Checked)
                dziecko.setData(0, Qt.ItemDataRole.UserRole, p)
            nadrzedny.setExpanded(True)
        self.tree.blockSignals(False)
        if not pozycje:
            self.status(i18n.tr("clean_nothing"))

    def _zaznaczone_do_czyszczenia(self) -> list[cleaner.CleanItem]:
        wynik = []
        for i in range(self.tree.topLevelItemCount()):
            rodzic = self.tree.topLevelItem(i)
            for j in range(rodzic.childCount()):
                dziecko = rodzic.child(j)
                if dziecko.checkState(0) == Qt.CheckState.Checked:
                    p = dziecko.data(0, Qt.ItemDataRole.UserRole)
                    if p:
                        wynik.append(p)
        return wynik

    def wykonaj_czyszczenie(self) -> None:
        pozycje = self._zaznaczone_do_czyszczenia()
        if not pozycje:
            QMessageBox.information(self, i18n.tr("cleanup_title"),
                                    i18n.tr("clean_nothing"))
            return
        rozmiar = sum(p.size for p in pozycje)
        zawiera_browser = any(p.group == "browser" for p in pozycje)
        dlg = CleanupConfirmDialog(len(pozycje), rozmiar, zawiera_browser, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        self.progress.setVisible(True)
        self.btn_clean.setEnabled(False)

        def po(rezultat):
            liczba, log = rezultat
            self.progress.setVisible(False)
            self.btn_clean.setEnabled(True)
            ReportDialog(i18n.tr("cleanup_title"),
                         i18n.tr("clean_ok", n=liczba) + "\n\n" + log, self).exec()
            self.status(i18n.tr("status_ready"))
            self.skanuj_czyszczenie()

        def blad(msg):
            self.progress.setVisible(False)
            self.btn_clean.setEnabled(True)
            self._blad(msg)

        self._tlo_roboty(cleaner.clean, pozycje, on_done=po, on_error=blad,
                         status=i18n.tr("status_cleaning"))
