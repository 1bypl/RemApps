"""Czyszczenie systemu: kosz, osierocone pliki, pamięci podręczne, historia."""

from __future__ import annotations

import os
import shutil
import sqlite3
import subprocess
from dataclasses import dataclass

DOM = os.path.expanduser("~")
UZYTKOWNIK = os.environ.get("USER", "daka")

GRUPY = ("trash", "orphans", "caches", "browser", "logs")


@dataclass
class CleanItem:
    label: str
    path: str
    size: int
    group: str
    needs_root: bool = False


def _size_of(sciezka: str) -> int:
    if os.path.isfile(sciezka):
        try:
            return os.path.getsize(sciezka)
        except OSError:
            return 0
    suma = 0
    for katalog, _, pliki in os.walk(sciezka):
        for plik in pliki:
            try:
                suma += os.path.getsize(os.path.join(katalog, plik))
            except OSError:
                pass
    return suma


# ---------------------------------------------------------------- Kosz
def scan_trash() -> list[CleanItem]:
    katalogi = [os.path.join(DOM, ".local", "share", "Trash")]
    for baza in ("/media", "/mnt", f"/run/media/{UZYTKOWNIK}"):
        if not os.path.isdir(baza):
            continue
        for katalog, podkatalogi, _ in os.walk(baza):
            for pod in list(podkatalogi):
                if pod.startswith(".Trash-"):
                    katalogi.append(os.path.join(katalog, pod))
            # nie schodź głębiej niż 3 poziomy
            if katalog.count(os.sep) - baza.count(os.sep) >= 2:
                podkatalogi[:] = []
    wynik = []
    for kat in katalogi:
        if not os.path.isdir(kat):
            continue
        for pod in ("files", "info"):
            p = os.path.join(kat, pod)
            if os.path.isdir(p):
                wynik.append(CleanItem(f"Kosz: {os.path.basename(kat)}/{pod}", p,
                                       _size_of(p), "trash"))
    return wynik


# ---------------------------------------------------------------- Osierocone
SUFFIXY = (".rpmsave", ".rpmnew", ".dpkg-old", ".dpkg-new", ".dpkg-dist", ".ucf-dist",
           ".dpkg-bak", ".ucf-new", ".pacnew", ".pacsave", ".pacorig")


def scan_orphans() -> list[CleanItem]:
    wynik = []
    for katalog in ("/etc",):
        if not os.path.isdir(katalog):
            continue
        for folder, _, pliki in os.walk(katalog):
            for plik in pliki:
                if plik.endswith(SUFFIXY):
                    p = os.path.join(folder, plik)
                    try:
                        rozmiar = os.path.getsize(p)
                    except OSError:
                        rozmiar = 0
                    wynik.append(CleanItem(plik, p, rozmiar, "orphans", True))
    return wynik


# ---------------------------------------------------------------- Pamięci podręczne
def scan_caches() -> list[CleanItem]:
    wynik = []
    dom_cache = os.path.join(DOM, ".cache")
    if os.path.isdir(dom_cache):
        for wpis in sorted(os.listdir(dom_cache)):
            p = os.path.join(dom_cache, wpis)
            if os.path.isdir(p):
                wynik.append(CleanItem(f"Pamięć podręczna: {wpis}", p, _size_of(p),
                                       "caches"))
    systemowe = [
        ("/var/cache/apt/archives", "Pakiety apt"),
        ("/var/cache/dnf", "Pakiety dnf"),
        ("/var/cache/yum", "Pakiety yum"),
        ("/var/cache/pacman/pkg", "Pakiety pacman"),
    ]
    for sciezka, etykieta in systemowe:
        if os.path.isdir(sciezka):
            wynik.append(CleanItem(etykieta, sciezka, _size_of(sciezka), "caches", True))
    return wynik


# ---------------------------------------------------------------- Przeglądarki
def scan_browser() -> list[CleanItem]:
    wynik = []
    firefox = os.path.join(DOM, ".mozilla", "firefox")
    if os.path.isdir(firefox):
        for profil in os.listdir(firefox):
            baza = os.path.join(firefox, profil, "places.sqlite")
            if os.path.isfile(baza):
                wynik.append(CleanItem(f"Firefox — historia ({profil})", baza,
                                       _size_of(baza), "browser"))
    for przegladarka in ("google-chrome", "chromium", "chromium-browser", "brave", "vivaldi"):
        baza_katalog = os.path.join(DOM, ".config", przegladarka)
        if not os.path.isdir(baza_katalog):
            continue
        for profil in os.listdir(baza_katalog):
            historia = os.path.join(baza_katalog, profil, "History")
            if os.path.isfile(historia):
                wynik.append(CleanItem(f"{przegladarka} — historia ({profil})",
                                       historia, _size_of(historia), "browser"))
    return wynik


# ---------------------------------------------------------------- Logi
def scan_logs() -> list[CleanItem]:
    wynik = []
    journal = subprocess.run(
        ["journalctl", "--disk-usage", "--no-pager"],
        capture_output=True, text=True, errors="replace",
    )
    if journal.returncode == 0:
        wynik.append(CleanItem("Dzienniki systemowe (journal)", "JOURNAL",
                               0, "logs", True))
    for sciezka in ("/var/log",):
        if os.path.isdir(sciezka):
            for plik in os.listdir(sciezka):
                if plik.endswith((".old", ".gz", ".1")):
                    p = os.path.join(sciezka, plik)
                    if os.path.isfile(p):
                        wynik.append(CleanItem(f"Log: {plik}", p, _size_of(p),
                                               "logs", True))
    return wynik


def scan_all(grupy: set[str]) -> list[CleanItem]:
    funkcje = {
        "trash": scan_trash,
        "orphans": scan_orphans,
        "caches": scan_caches,
        "browser": scan_browser,
        "logs": scan_logs,
    }
    wynik = []
    for grupa in GRUPY:
        if grupa in grupy:
            wynik.extend(funkcje[grupa]())
    return wynik


# ---------------------------------------------------------------- Usuwanie
def _usun_root(pozycje: list[CleanItem]) -> tuple[int, str]:
    if not pozycje:
        return 0, ""
    sciezki = [p.path for p in pozycje if p.path != "JOURNAL"]
    log = ""
    if sciezki:
        wynik = subprocess.run(
            ["pkexec", "rm", "-rf", "--"] + sciezki,
            capture_output=True, text=True, errors="replace", timeout=300,
        )
        log += (wynik.stdout or "") + (wynik.stderr or "")
        if wynik.returncode != 0:
            log += "\nNie udało się usunąć części plików systemowych (brak uprawnień)."
    if any(p.path == "JOURNAL" for p in pozycje):
        wynik = subprocess.run(
            ["pkexec", "journalctl", "--vacuum-time=7d"],
            capture_output=True, text=True, errors="replace", timeout=300,
        )
        log += (wynik.stdout or "") + (wynik.stderr or "")
    return len(pozycje), log.strip()


def _wyczysc_firefox(sciezka: str) -> bool:
    try:
        polaczenie = sqlite3.connect(sciezka, timeout=5)
        kursor = polaczenie.cursor()
        kursor.execute("DELETE FROM moz_historyvisits")
        kursor.execute("DELETE FROM moz_inputhistory")
        polaczenie.commit()
        polaczenie.execute("VACUUM")
        polaczenie.close()
        return True
    except (sqlite3.Error, OSError):
        return False


def clean(pozycje: list[CleanItem]) -> tuple[int, str]:
    """Us selected items. Zwraca (liczba usuniętych, log)."""
    usuniete = 0
    logi = []
    root_items = [p for p in pozycje if p.needs_root]
    user_items = [p for p in pozycje if not p.needs_root]

    for p in user_items:
        if p.group == "browser" and p.path.endswith("places.sqlite"):
            if _wyczysc_firefox(p.path):
                usuniete += 1
                logi.append(f"Wyczyszczono historię: {p.label}")
            else:
                logi.append(f"Nie udało się wyczyścić (zamknij przeglądarkę): {p.label}")
            continue
        try:
            if os.path.isdir(p.path):
                shutil.rmtree(p.path)
            elif os.path.isfile(p.path):
                os.remove(p.path)
            else:
                continue
            usuniete += 1
            logi.append(f"Usunięto: {p.label}")
        except OSError as exc:
            logi.append(f"Nie udało się usunąć {p.label}: {exc}")

    if root_items:
        liczba, log = _usun_root(root_items)
        usuniete += liczba
        if log:
            logi.append(log)

    return usuniete, "\n".join(logi)
