#!/bin/sh
# Instalator RemApps dla Fedory i pochodnych (RPM).
# Użycie: sh install/install_fedora.sh

. "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/common.sh"

info "Instalacja RemApps dla Fedory / RPM"

if ! command -v dnf >/dev/null 2>&1; then
    blad "Nie wykryto dnf — ten instalator jest dla Fedory."
fi

MENEDZER="dnf"
if [ "$(id -u)" -ne 0 ]; then
    command -v sudo >/dev/null 2>&1 || \
        blad "Brak polecenia sudo. Zainstaluj sudo lub uruchom: sudo sh install/install_fedora.sh"
    MENEDZER="sudo dnf"
fi
INSTALACJA="install -y"
PAKIET_PYSIDE="python3-pyside6"
PAKIET_POLKIT="polkit"

sprawdz_python
sprawdz_pyside
sprawdz_pkexec
kopiuj_pliki
utworz_launcher
utworz_skrót
zakoncz
