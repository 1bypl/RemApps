#!/bin/sh
# Wspólna część instalatorów RemApps.
# Instalacja odbywa się do katalogu użytkownika (~/.local), więc nie potrzeba sudo.

set -e

SKLADNIA=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
KATALOG_DANYCH="$HOME/.local/share/remapps"
KATALOG_BIN="$HOME/.local/bin"
KATALOG_DESKTOP="$HOME/.local/share/applications"

info()  { printf '\033[1;32m[RemApps]\033[0m %s\n' "$1"; }
blad()  { printf '\033[1;31m[RemApps BŁĄD]\033[0m %s\n' "$1" >&2; exit 1; }

sprawdz_python() {
    if ! command -v python3 >/dev/null 2>&1; then
        blad "Nie znaleziono Pythona 3. Zainstaluj go: sudo dnf install python3 / sudo apt install python3"
    fi
    WERSJA=$(python3 -c 'import sys; print(sys.version_info[0]*100+sys.version_info[1])')
    if [ "$WERSJA" -lt 309 ]; then
        blad "Wymagany Python 3.9 lub nowszy (masz: $(python3 --version))."
    fi
    info "Python OK: $(python3 --version)"
}

sprawdz_pyside() {
    if python3 -c 'import PySide6.QtWidgets' >/dev/null 2>&1; then
        info "PySide6 jest już zainstalowany."
        return
    fi
    info "Instaluję PySide6 (bibliotekę interfejsu)..."
    if [ -n "$PAKIET_PYSIDE" ]; then
        $MENEDZER $INSTALACJA $PAKIET_PYSIDE >/dev/null 2>&1 || true
    fi
    if ! python3 -c 'import PySide6.QtWidgets' >/dev/null 2>&1; then
        info "Próbuję instalacji przez pip..."
        python3 -m pip install --user PySide6 >/dev/null 2>&1 || \
        python3 -m pip install --user --break-system-packages PySide6 >/dev/null 2>&1 || \
        blad "Nie udało się zainstalować PySide6. Sprawdź połączenie z internetem."
    fi
    python3 -c 'import PySide6.QtWidgets' >/dev/null 2>&1 || blad "PySide6 nadal niedostępny."
    info "PySide6 zainstalowany."
}

sprawdz_pkexec() {
    if command -v pkexec >/dev/null 2>&1; then
        info "pkexec (polkit) jest dostępny."
    else
        info "Instaluję polkit (potrzebny do uprawnień administratora)..."
        $MENEDZER $INSTALACJA "$PAKIET_POLKIT" >/dev/null 2>&1 || \
            blad "Nie udało się zainstalować polkit. Zainstaluj go ręcznie."
    fi
}

kopiuj_pliki() {
    info "Kopiuję pliki do $KATALOG_DANYCH ..."
    rm -rf "$KATALOG_DANYCH"
    mkdir -p "$KATALOG_DANYCH"
    cp -R "$SKLADNIA/remapps" "$KATALOG_DANYCH/"
    cp "$SKLADNIA/main.py" "$KATALOG_DANYCH/"
    cp "$SKLADNIA/remapps/resources/logo.svg" "$KATALOG_DANYCH/logo.svg"
    cp "$SKLADNIA/README.md" "$KATALOG_DANYCH/" 2>/dev/null || true
    cp "$SKLADNIA/LICENSE" "$KATALOG_DANYCH/" 2>/dev/null || true
    find "$KATALOG_DANYCH" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
    find "$KATALOG_DANYCH" -name '*.pyc' -delete 2>/dev/null || true
}

utworz_launcher() {
    mkdir -p "$KATALOG_BIN"
    cat > "$KATALOG_BIN/remapps" <<EOF
#!/bin/sh
exec python3 "$KATALOG_DANYCH/main.py" "\$@"
EOF
    chmod +x "$KATALOG_BIN/remapps"
    info "Utworzono polecenie: remapps"
}

utworz_skrót() {
    mkdir -p "$KATALOG_DESKTOP"
    cat > "$KATALOG_DESKTOP/remapps.desktop" <<EOF
[Desktop Entry]
Type=Application
Version=1.0
Name=RemApps
GenericName=Uninstall Manager
Comment=Menedżer odinstalowywania i czyszczenia systemu
Comment[de]=Deinstallations- und Systembereinigungs-Manager
Comment[ru]=Менеджер удаления программ и очистки системы
Exec="$KATALOG_BIN/remapps"
Icon=$KATALOG_DANYCH/logo.svg
Terminal=false
Categories=System;Settings;PackageManager;
Keywords=uninstall;remove;clean;odinstaluj;wyczyść;
StartupNotify=true
EOF
    chmod +x "$KATALOG_DESKTOP/remapps.desktop"
    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database "$KATALOG_DESKTOP" >/dev/null 2>&1 || true
    fi
    info "Utworzono skrót w menu aplikacji."
}

zakoncz() {
    info "Gotowe! Uruchom program poleceniem: remapps"
    info "albo znajdź «RemApps» w menu aplikacji."
    if ! printf '%s' "$PATH" | grep -q "$KATALOG_BIN"; then
        info "Jeśli polecenie nie działa, dodaj do ~/.bashrc:"
        info '  export PATH="$HOME/.local/bin:$PATH"'
    fi
}
