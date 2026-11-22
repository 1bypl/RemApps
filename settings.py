"""Ustawienia programu zapisywane w folderze użytkownika."""

from __future__ import annotations

import json
import os

from .detector import detect

KATALOG = os.path.join(os.path.expanduser("~"), ".config", "remapps")
PLIK = os.path.join(KATALOG, "settings.json")

DOMYSLNE = {
    "language": "pl",
    "theme": "auto",          # auto / light / dark
    "search_mode": "standard",  # standard / exact / dirs
    "simulation": False,
    "ask_config": True,
    "cache_results": True,
    "first_run": True,
}


def wczytaj() -> dict:
    ustawienia = dict(DOMYSLNE)
    if os.path.exists(PLIK):
        try:
            with open(PLIK, encoding="utf-8") as plik:
                dane = json.load(plik)
            if isinstance(dane, dict):
                ustawienia.update(dane)
        except (OSError, ValueError):
            pass
    return ustawienia


def zapisz(ustawienia: dict) -> None:
    try:
        os.makedirs(KATALOG, exist_ok=True)
        with open(PLIK, "w", encoding="utf-8") as plik:
            json.dump(ustawienia, plik, ensure_ascii=False, indent=2)
    except OSError:
        pass


def opis_systemu() -> str:
    d = detect()
    return f"{d.name}  •  pakiety: {d.package_manager}"
