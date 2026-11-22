#!/bin/sh
# Instalator RemApps dla Debiana, Ubuntu i pochodnych (DEB).
# Użycie: sh install/install_debian.sh

. "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/common.sh"

info "Instalacja RemApps dla Debiana / Ubuntu"

if ! command -v apt-get >/dev/null 2>&1; then
    blad "Nie wykryto apt-get — ten instalator jest dla Debiana/Ubuntu."
fi

MENEDZER="apt-get"
INSTALACJA="install -y"
PAKIET_PYSIDE="python3-pyside6.qtwidgets python3-pyside6.qtsvg python3-pyside6.qtcore python3-pyside6.qtgui"
PAKIET_POLKIT="policykit-1"

info "Odświeżam listy pakietów (może poprosić o hasło)..."
if [ "$(id -u)" -eq 0 ]; then
    apt-get update -qq || true
else
    sudo apt-get update -qq || true
fi

# Jeśli nie jesteśmy rootem, dodaj sudo do menedżera pakietów
if [ "$(id -u)" -ne 0 ]; then
    command -v sudo >/dev/null 2>&1 || \
        blad "Brak polecenia sudo. Zainstaluj sudo lub uruchom: sudo sh install/install_debian.sh"
    MENEDZER="sudo apt-get"
fi

sprawdz_python
sprawdz_pyside
sprawdz_pkexec
kopiuj_pliki
utworz_launcher
utworz_skrót
zakoncz
