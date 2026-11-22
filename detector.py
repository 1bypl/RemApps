"""Wykrywanie dystrybucji i systemu pakietów."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass


@dataclass
class DistroInfo:
    id: str
    name: str
    version: str
    family: str  # "rpm", "deb" albo "arch"
    package_manager: str  # "dnf", "yum", "apt" albo "pacman"


def _read_os_release() -> dict:
    dane = {}
    sciezka = "/etc/os-release"
    if not os.path.exists(sciezka):
        return dane
    with open(sciezka, encoding="utf-8", errors="replace") as plik:
        for linia in plik:
            linia = linia.strip()
            if not linia or linia.startswith("#") or "=" not in linia:
                continue
            klucz, wartosc = linia.split("=", 1)
            dane[klucz] = wartosc.strip().strip('"')
    return dane


RPM_IDS = {
    "fedora", "rhel", "centos", "rocky", "almalinux",
    "opensuse", "opensuse-leap", "sles", "mageia",
}
DEB_IDS = {
    "debian", "ubuntu", "linuxmint", "pop", "elementary",
    "kali", "raspbian", "zorin", "neon", "mx",
}
ARCH_IDS = {"arch", "manjaro", "endeavouros", "artix", "arcolinux", "garuda"}


def detect() -> DistroInfo:
    dane = _read_os_release()
    ident = dane.get("ID", "unknown").lower()
    nazwa = dane.get("PRETTY_NAME", dane.get("NAME", "Linux"))
    wersja = dane.get("VERSION_ID", "")
    podobne = dane.get("ID_LIKE", "").lower()

    rodzina = "unknown"
    if ident in RPM_IDS or any(
        x in podobne for x in ("fedora", "rhel", "centos", "suse", "mandriva", "mageia")
    ):
        rodzina = "rpm"
    elif ident in DEB_IDS or "debian" in podobne or "ubuntu" in podobne:
        rodzina = "deb"
    elif ident in ARCH_IDS or "arch" in podobne or "manjaro" in podobne:
        rodzina = "arch"

    if rodzina == "unknown":
        if has_command("rpm"):
            rodzina = "rpm"
        elif has_command("dpkg"):
            rodzina = "deb"
        elif has_command("pacman"):
            rodzina = "arch"

    if rodzina == "rpm":
        menedzer = "yum" if not has_command("dnf") and has_command("yum") else "dnf"
    elif rodzina == "deb":
        menedzer = "apt"
    elif rodzina == "arch":
        menedzer = "pacman"
    else:
        menedzer = "unknown"

    return DistroInfo(ident, nazwa, wersja, rodzina, menedzer)


def has_command(nazwa: str) -> bool:
    return shutil.which(nazwa) is not None
