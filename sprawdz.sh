#!/bin/sh
# RemApps — szybka diagnostyka instalacji.
# Użycie: sh install/sprawdz.sh

printf '===========================================\n'
printf ' RemApps — sprawdzenie instalacji\n'
printf '===========================================\n\n'

printf 'System:        '
if [ -f /etc/os-release ]; then
    . /etc/os-release 2>/dev/null
    printf '%s\n' "${PRETTY_NAME:-nieznany}"
else
    printf 'nieznany\n'
fi

printf 'Pakiet RPM:    '
if command -v rpm >/dev/null 2>&1; then
    rpm -q remapps 2>&1 | head -1
else
    printf 'rpm niedostępny\n'
fi

printf 'Polecenie:     '
if command -v remapps >/dev/null 2>&1; then
    printf '%s\n' "$(command -v remapps)"
else
    printf 'BRAK — dodaj ~/.local/bin do PATH lub zainstaluj pakiet\n'
fi

printf 'Plik główny:   '
if [ -f /usr/share/remapps/main.py ]; then
    printf 'OK (/usr/share/remapps/main.py)\n'
elif [ -f "$HOME/.local/share/remapps/main.py" ]; then
    printf 'OK (%s/.local/share/remapps/main.py)\n' "$HOME"
else
    printf 'BRAK\n'
fi

printf 'Python:        '
python3 --version 2>&1

printf 'PySide6:       '
python3 -c 'import PySide6; print(PySide6.__version__)' 2>&1 | head -1

printf 'QtSvg:         '
python3 -c 'from PySide6 import QtSvg; print("OK")' 2>&1 | head -1

printf 'pkexec:        '
if command -v pkexec >/dev/null 2>&1; then
    printf 'OK\n'
else
    printf 'BRAK — zainstaluj: sudo dnf install polkit\n'
fi

printf '\n--- Zależności pakietu (RPM) ---\n'
if command -v rpm >/dev/null 2>&1; then
    rpm -qR remapps 2>&1 | head -20 || true
fi

printf '\n===========================================\n'
printf 'Jeśli PySide6 pokazuje błąd, uruchom:\n'
printf '  sudo dnf install python3-pyside6\n'
printf '===========================================\n'
