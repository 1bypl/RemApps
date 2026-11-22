"""Wyszukiwanie zainstalowanego oprogramowania.

Program szuka paczek w bazie systemu (rpm/dpkg), a także aplikacji
z innych źródeł: Flatpak, Snap, pliki .desktop oraz AppImage.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from dataclasses import dataclass, field, asdict

from .detector import DistroInfo, has_command

CACHE_PATH = os.path.join(
    os.path.expanduser("~"), ".cache", "remapps", "packages.json"
)
CACHE_MAX_AGE = 1800  # 30 minut
CACHE_VERSION = 2  # zmiana struktury danych -> stare cache ignorowane

# Pomiar czasu poszczególnych skanerów (do celów diagnostycznych)
OSTATNI_CZASY: dict[str, float] = {}


def _zmierz(nazwa: str, funkcja, *args):
    poczatek = time.perf_counter()
    wynik = funkcja(*args)
    OSTATNI_CZASY[nazwa] = round(time.perf_counter() - poczatek, 2)
    return wynik


@dataclass
class Package:
    name: str
    version: str = ""
    size: int = 0  # w bajtach
    description: str = ""
    source: str = ""  # rpm / deb / flatpak / snap / desktop / appimage
    icon_hint: str = ""
    origin_path: str = ""
    config_files: list[str] = field(default_factory=list)
    package_id: str = ""  # np. de.haeckerfelix.Shortwave dla Flatpak

    @property
    def size_text(self) -> str:
        return human_size(self.size)


def human_size(liczba: int) -> str:
    if liczba <= 0:
        return "—"
    wartosc = float(liczba)
    for jednostka in ("B", "KB", "MB", "GB", "TB"):
        if wartosc < 1024 or jednostka == "TB":
            return f"{int(wartosc)} B" if jednostka == "B" else f"{wartosc:.1f} {jednostka}"
        wartosc /= 1024.0
    return f"{wartosc:.1f} TB"


# --------------------------------------------------------------------------
# Zapamiętywanie wyników (dzięki temu program startuje od razu)
# --------------------------------------------------------------------------

def cache_key(distro: DistroInfo, tryb: str) -> str:
    return f"{distro.family}:{tryb}"


def wczytaj_cache(klucz: str, max_age: int | None = CACHE_MAX_AGE) -> list[Package] | None:
    """Czyta zapisaną listę. max_age=None przyjmuje też przestarzałą listę."""
    try:
        with open(CACHE_PATH, encoding="utf-8") as plik:
            dane = json.load(plik)
        if dane.get("key") != klucz or dane.get("version") != CACHE_VERSION:
            return None
        if max_age is not None and time.time() - dane.get("time", 0) > max_age:
            return None
        return [Package(**p) for p in dane.get("packages", [])]
    except (OSError, ValueError, TypeError):
        return None


def usun_cache() -> None:
    """Usuwa zapisaną listę — wymusza świeży skan przy następnym odświeżeniu."""
    try:
        if os.path.exists(CACHE_PATH):
            os.remove(CACHE_PATH)
    except OSError:
        pass


def usun_z_cache(klucz: str, nazwa: str, zrodlo: str) -> None:
    """Wyreśla jeden wpis z zapisanej listy po udanym usunięciu."""
    try:
        with open(CACHE_PATH, encoding="utf-8") as plik:
            dane = json.load(plik)
        if dane.get("key") != klucz:
            return
        dane["packages"] = [
            p for p in dane.get("packages", [])
            if not (p.get("name") == nazwa and p.get("source") == zrodlo)
        ]
        dane["time"] = time.time()
        with open(CACHE_PATH, "w", encoding="utf-8") as plik:
            json.dump(dane, plik, ensure_ascii=False)
    except (OSError, ValueError, TypeError):
        pass


def zapisz_cache(klucz: str, pakiety: list[Package]) -> None:
    try:
        os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
        with open(CACHE_PATH, "w", encoding="utf-8") as plik:
            json.dump(
                {"key": klucz, "version": CACHE_VERSION, "time": time.time(),
                 "packages": [asdict(p) for p in pakiety]},
                plik, ensure_ascii=False,
            )
    except (OSError, TypeError, ValueError):
        pass


def _run(argi: list[str], timeout: int = 120) -> str:
    try:
        wynik = subprocess.run(
            argi, capture_output=True, text=True,
            errors="replace", timeout=timeout,
        )
        return wynik.stdout or ""
    except Exception:
        return ""


# --------------------------------------------------------------------------
# Bazy pakietów
# --------------------------------------------------------------------------

def list_rpm() -> list[Package]:
    if not has_command("rpm"):
        return []
    fmt = "%{NAME}\t%{VERSION}-%{RELEASE}\t%{SIZE}\t%{SUMMARY}\n"
    wyjscie = _run(["rpm", "-qa", "--qf", fmt])
    wynik = []
    for linia in wyjscie.splitlines():
        czesci = linia.split("\t")
        if len(czesci) < 3:
            continue
        nazwa = czesci[0].strip()
        if not nazwa:
            continue
        wersja = czesci[1].strip()
        try:
            rozmiar = int(czesci[2])
        except ValueError:
            rozmiar = 0
        opis = czesci[3].strip() if len(czesci) > 3 else ""
        wynik.append(Package(nazwa, wersja, rozmiar, opis, "rpm", icon_hint=nazwa))
    return wynik


def list_deb() -> list[Package]:
    if not has_command("dpkg-query"):
        return []
    fmt = "${Package}\t${Version}\t${Installed-Size}\t${binary:Summary}\n"
    wyjscie = _run(["dpkg-query", "-W", "-f=" + fmt])
    wynik = []
    for linia in wyjscie.splitlines():
        czesci = linia.split("\t")
        if len(czesci) < 2:
            continue
        nazwa = czesci[0].strip()
        if not nazwa:
            continue
        wersja = czesci[1].strip()
        try:
            kb = int(czesci[2]) if len(czesci) > 2 and czesci[2].strip().isdigit() else 0
            rozmiar = kb * 1024
        except ValueError:
            rozmiar = 0
        opis = czesci[3].strip() if len(czesci) > 3 else ""
        wynik.append(Package(nazwa, wersja, rozmiar, opis, "deb", icon_hint=nazwa))
    return wynik


def list_pacman() -> list[Package]:
    """Pakiety Arch Linux / Manjaro (baza pacman)."""
    if not has_command("pacman"):
        return []
    wyjscie = _run(["pacman", "-Q"])
    wynik = []
    for linia in wyjscie.splitlines():
        czesci = linia.split(maxsplit=1)
        if len(czesci) < 2:
            continue
        nazwa, wersja = czesci[0].strip(), czesci[1].strip()
        if not nazwa:
            continue
        rozmiar = 0
        opis = ""
        katalog = f"/var/lib/pacman/local/{nazwa}-{wersja}"
        plik_opisu = os.path.join(katalog, "desc")
        if os.path.exists(plik_opisu):
            try:
                with open(plik_opisu, encoding="utf-8", errors="replace") as f:
                    linie = [l.strip() for l in f]
                for i, l in enumerate(linie[:-1]):
                    if l == "%INSTALLED SIZE%" and linie[i + 1].isdigit():
                        rozmiar = int(linie[i + 1]) * 1024
                    elif l == "%DESC%" and linie[i + 1]:
                        opis = linie[i + 1]
            except OSError:
                pass
        wynik.append(Package(nazwa, wersja, rozmiar, opis, "pacman", icon_hint=nazwa))
    return wynik


# --------------------------------------------------------------------------
# Inne źródła
# --------------------------------------------------------------------------

def list_flatpak() -> list[Package]:
    if not has_command("flatpak"):
        return []
    wyjscie = _run(["flatpak", "list", "--app", "--columns=application,version,size,name"])
    wynik = []
    for linia in wyjscie.splitlines():
        czesci = linia.split("\t")
        if not czesci or not czesci[0].strip():
            continue
        ident = czesci[0].strip()
        wersja = czesci[1].strip() if len(czesci) > 1 else ""
        rozmiar = 0
        if len(czesci) > 2:
            dopasowanie = re.search(r"([\d.,]+)\s*(kB|MB|GB|B)", czesci[2], re.I)
            if dopasowanie:
                rozmiar = _parse_size(dopasowanie.group(1), dopasowanie.group(2))
        nazwa = czesci[3].strip() if len(czesci) > 3 and czesci[3].strip() else ident
        wynik.append(Package(nazwa, wersja, rozmiar, ident, "flatpak",
                             icon_hint=ident, package_id=ident))
    return wynik


def _parse_size(liczba: str, jednostka: str) -> int:
    try:
        wartosc = float(liczba.replace(",", "."))
    except ValueError:
        return 0
    mnoznik = {"B": 1, "KB": 1024, "MB": 1024 ** 2, "GB": 1024 ** 3}.get(
        jednostka.upper(), 1
    )
    return int(wartosc * mnoznik)


def list_snap() -> list[Package]:
    if not has_command("snap"):
        return []
    wyjscie = _run(["snap", "list"])
    wynik = []
    for linia in wyjscie.splitlines()[1:]:
        czesci = linia.split()
        if len(czesci) < 2:
            continue
        wynik.append(Package(czesci[0], czesci[1], 0, "Snap", "snap", icon_hint=czesci[0]))
    return wynik


DESKTOP_DIRS = [
    "/usr/share/applications",
    "/usr/local/share/applications",
    "/var/lib/snapd/desktop/applications",
    "/var/lib/flatpak/exports/share/applications",
]


def _user_desktop_dirs() -> list[str]:
    dom = os.path.expanduser("~")
    return [
        os.path.join(dom, ".local", "share", "applications"),
        os.path.join(dom, ".local", "share", "flatpak", "exports", "share", "applications"),
    ]


def _desktop_files() -> list[str]:
    sciezki = []
    widziane = set()
    for katalog in DESKTOP_DIRS + _user_desktop_dirs():
        if not os.path.isdir(katalog):
            continue
        try:
            wpisy = os.listdir(katalog)
        except OSError:
            continue
        for wpis in wpisy:
            if not wpis.endswith(".desktop"):
                continue
            pelna = os.path.join(katalog, wpis)
            if pelna not in widziane:
                widziane.add(pelna)
                sciezki.append(pelna)
    return sciezki


def _parse_desktop(sciezka: str) -> tuple[str, str, str, bool]:
    nazwa = ""
    ikona = ""
    polecenie = ""
    ukryty = False
    try:
        with open(sciezka, encoding="utf-8", errors="replace") as plik:
            w_glownym = False
            for linia in plik:
                linia = linia.strip()
                if linia.startswith("["):
                    w_glownym = linia == "[Desktop Entry]"
                    continue
                if not w_glownym or "=" not in linia:
                    continue
                klucz, wartosc = linia.split("=", 1)
                if klucz == "Name":
                    nazwa = wartosc.strip()
                elif klucz == "Icon":
                    ikona = wartosc.strip()
                elif klucz == "Exec":
                    polecenie = wartosc.strip()
                elif klucz in ("NoDisplay", "Hidden") and wartosc.strip().lower() == "true":
                    ukryty = True
    except OSError:
        pass
    if not nazwa:
        nazwa = os.path.basename(sciezka)[:-8]
    return nazwa, ikona, polecenie, ukryty


def list_desktop_apps(wlasne_nazwy: set[str] | None = None) -> list[Package]:
    """Aplikacje z plików .desktop, których nie ma w bazie pakietów."""
    nazwy = wlasne_nazwy or set()
    wynik = []
    for sciezka in _desktop_files():
        nazwa, ikona, polecenie, ukryty = _parse_desktop(sciezka)
        if ukryty:
            continue
        # Skróty Flatpak/Snap są już obsługiwane przez własne skanery —
        # pokazywanie ich dodatkowo jako „Skrót" prowadziło do usuwania
        # samego skrótu zamiast całej aplikacji.
        pole_dolne = polecenie.lower()
        if "flatpak run" in pole_dolne or "snap run" in pole_dolne:
            continue
        plik = os.path.basename(sciezka)[:-8].lower()
        klucz = nazwa.lower().replace(" ", "-")
        if plik in nazwy or klucz in nazwy:
            continue
        wynik.append(
            Package(
                name=nazwa, description=polecenie, source="desktop",
                icon_hint=ikona, origin_path=sciezka,
            )
        )
    return wynik


def list_appimages() -> list[Package]:
    dom = os.path.expanduser("~")
    katalogi = [
        os.path.join(dom, "Applications"),
        os.path.join(dom, "Downloads"),
        os.path.join(dom, "Pulpit"),
        os.path.join(dom, "Desktop"),
        "/opt",
    ]
    wynik = []
    for katalog in katalogi:
        if not os.path.isdir(katalog):
            continue
        try:
            for wpis in os.listdir(katalog):
                if wpis.lower().endswith(".appimage"):
                    pelna = os.path.join(katalog, wpis)
                    rozmiar = 0
                    try:
                        rozmiar = os.path.getsize(pelna)
                    except OSError:
                        pass
                    wynik.append(
                        Package(wpis[:-9], "", rozmiar, "AppImage",
                                "appimage", icon_hint="appimage", origin_path=pelna)
                    )
        except OSError:
            continue
    return wynik


def scan_all(distro: DistroInfo, tryb: str = "standard",
             uzyj_cache: bool = True) -> list[Package]:
    """Skanuje WSZYSTKIE źródła niezależnie od trybu.

    Tryb określa tylko dokładność:
      standard – szybki skan wszystkich baz,
      exact    – dodatkowo skróty .desktop z całego systemu,
      dirs     – nacisk na katalogi instalacji i pliki AppImage.
    """
    klucz = cache_key(distro, tryb)
    if uzyj_cache:
        zapisane = wczytaj_cache(klucz)
        if zapisane is not None:
            return zapisane

    wynik: list[Package] = []
    OSTATNI_CZASY.clear()

    # Baza pakietów systemu — we WSZYSTKICH trybach
    if distro.family == "rpm":
        wynik.extend(_zmierz("rpm", list_rpm))
    elif distro.family == "deb":
        wynik.extend(_zmierz("dpkg", list_deb))
    elif distro.family == "arch":
        wynik.extend(_zmierz("pacman", list_pacman))

    # Flatpak/Flathub, Snap i AppImage — we WSZYSTKICH trybach
    wynik.extend(_zmierz("flatpak", list_flatpak))
    wynik.extend(_zmierz("snap", list_snap))
    wynik.extend(_zmierz("appimage", list_appimages))

    # Skróty .desktop
    własne = {p.name.lower() for p in wynik}
    własne |= {p.name.lower().replace(" ", "-") for p in wynik}
    if tryb == "dirs":
        wynik.extend(_zmierz("desktop", list_desktop_apps))
    else:
        wynik.extend(_zmierz("desktop", list_desktop_apps, własne))

    # usuwanie duplikatów
    widziane = set()
    unikalne = []
    for p in wynik:
        klucz_p = (p.name.lower(), p.source)
        if klucz_p in widziane:
            continue
        widziane.add(klucz_p)
        unikalne.append(p)
    unikalne.sort(key=lambda p: p.name.lower())
    zapisz_cache(klucz, unikalne)
    return unikalne
