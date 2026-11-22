"""Ikony: logo krokodyla oraz ikony programów z motywu systemu."""

from __future__ import annotations

import os

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap

LOGO_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                         "resources", "logo.svg")

_cache: dict[int, QIcon] = {}


def logo_icon(size: int = 128) -> QIcon:
    if size in _cache:
        return _cache[size]
    pixmap = QPixmap(LOGO_PATH)
    if pixmap.isNull():
        # awaryjne rysowanie, gdy QtSvg nie jest dostępny
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        p = QPainter(pixmap)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QColor("#2fb35f"))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 0, size, size, size // 5, size // 5)
        p.end()
    else:
        pixmap = pixmap.scaled(
            QSize(size, size), Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
    ikona = QIcon(pixmap)
    _cache[size] = ikona
    return ikona


def logo_pixmap(size: int = 256) -> QPixmap:
    return logo_icon(size).pixmap(QSize(size, size))


def app_icon() -> QIcon:
    return logo_icon(64)


# Bufor ikon — zapobiega wielokrotnemu przeszukiwaniu motywu dla
# tysięcy wierszy listy (główna przyczyna spowolnienia na Fedorze).
_ikona_cache: dict[tuple[str, str], QIcon] = {}


_ICON_HINTS = {
    "rpm": ("package", "application-x-executable"),
    "deb": ("package", "application-x-executable"),
    "flatpak": ("flatpak", "application-x-executable"),
    "snap": ("snap", "application-x-executable"),
    "desktop": ("applications-games", "application-x-executable"),
    "appimage": ("application-x-executable", "package"),
}

# rozszerzenia nazw pakietów → ikony z motywu
_NAZWY_IKON = {
    "firefox": "firefox", "google-chrome": "google-chrome",
    "chromium": "chromium", "chromium-browser": "chromium",
    "thunderbird": "thunderbird", "libreoffice": "libreoffice",
    "gimp": "gimp", "inkscape": "inkscape", "vlc": "vlc",
    "code": "code", "visual-studio-code": "code", "git": "git",
    "steam": "steam", "discord": "discord", "spotify": "spotify",
    "qt": "qtcreator", "python": "python", "java": "java",
    "blender": "blender", "audacity": "audacity", "kdenlive": "kdenlive",
    "okular": "okular", "dolphin": "system-file-manager",
    "plasmashell": "kde", "kwin": "kde", "gsettings-desktop-schemas": "gnome",
}


def package_icon(hint: str, source: str = "") -> QIcon:
    klucz = (hint or "", source or "")
    if klucz in _ikona_cache:
        return _ikona_cache[klucz]
    kandydaci: list[str] = []
    if hint:
        kandydaci.append(hint)
        dolny = hint.lower()
        for klucz, ikona in _NAZWY_IKON.items():
            if klucz in dolny:
                kandydaci.append(ikona)
                break
    kandydaci.extend(_ICON_HINTS.get(source, ("application-x-executable",)))
    kandydaci.append("application-x-executable")
    for nazwa in kandydaci:
        ikona = QIcon.fromTheme(nazwa)
        if not ikona.isNull():
            _ikona_cache[klucz] = ikona
            return ikona
    ikona = QIcon.fromTheme("package-x-generic")
    _ikona_cache[klucz] = ikona
    return ikona


def nav_icon(nazwa: str) -> QIcon:
    mapa = {
        "programy": ("applications-games", "package-x-generic"),
        "czyszczenie": ("edit-clear", "user-trash"),
        "ustawienia": ("preferences-system", "configure"),
        "o": ("help-about", "information"),
    }
    for kandydat in mapa.get(nazwa, ("application-x-executable",)):
        ikona = QIcon.fromTheme(kandydat)
        if not ikona.isNull():
            return ikona
    return QIcon()
