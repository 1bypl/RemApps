#!/bin/sh
# Usuwa RemApps zainstalowany w katalogu użytkownika.
# Użycie: sh install/uninstall.sh

set -e
KATALOG_DANYCH="$HOME/.local/share/remapps"
KATALOG_BIN="$HOME/.local/bin"
KATALOG_DESKTOP="$HOME/.local/share/applications"

printf '[RemApps] Usuwam program...\n'
rm -rf "$KATALOG_DANYCH"
rm -f "$KATALOG_BIN/remapps"
rm -f "$KATALOG_DESKTOP/remapps.desktop"
rm -rf "$HOME/.config/remapps"
printf '[RemApps] Gotowe. Ustawienia programu również zostały usunięte.\n'
