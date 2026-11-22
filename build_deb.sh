#!/bin/sh
# Buduje pakiet .deb (Debian, Ubuntu i pochodne).
# Użycie: sh packaging/deb/build_deb.sh
# Wymagania: sudo apt install dpkg-dev

set -e

SKRYPT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJEKT=$(CDPATH= cd -- "$SKRYPT/../.." && pwd)
WERSJA="1.0.0"
BUDOWANY="$PROJEKT/build-deb/remapps_${WERSJA}_all"
WYNIK="$PROJEKT/remapps_${WERSJA}_all.deb"

info() { printf '\033[1;32m[RemApps DEB]\033[0m %s\n' "$1"; }
blad() { printf '\033[1;31m[BŁĄD]\033[0m %s\n' "$1" >&2; exit 1; }

if ! command -v dpkg-deb >/dev/null 2>&1; then
    blad "Brak dpkg-deb. Zainstaluj: sudo apt install dpkg-dev"
fi

info "Przygotowuję strukturę pakietu..."
rm -rf "$PROJEKT/build-deb"
mkdir -p "$BUDOWANY/DEBIAN"
mkdir -p "$BUDOWANY/usr/bin"
mkdir -p "$BUDOWANY/usr/share/remapps"
mkdir -p "$BUDOWANY/usr/share/applications"
mkdir -p "$BUDOWANY/usr/share/icons/hicolor/scalable/apps"

cp -a "$PROJEKT/remapps" "$BUDOWANY/usr/share/remapps/"
cp "$PROJEKT/main.py" "$BUDOWANY/usr/share/remapps/main.py"
cp "$PROJEKT/remapps/resources/logo.svg" \
    "$BUDOWANY/usr/share/icons/hicolor/scalable/apps/remapps.svg"
cp "$SKRYPT/control" "$BUDOWANY/DEBIAN/control"

cat > "$BUDOWANY/usr/bin/remapps" <<'EOF'
#!/bin/sh
exec python3 /usr/share/remapps/main.py "$@"
EOF
chmod 755 "$BUDOWANY/usr/bin/remapps"

cat > "$BUDOWANY/usr/share/applications/remapps.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Version=1.0
Name=RemApps
GenericName=Uninstall Manager
Comment=Menedżer odinstalowywania i czyszczenia systemu
Comment[de]=Deinstallations- und Systembereinigungs-Manager
Comment[ru]=Менеджер удаления программ и очистки системы
Exec=remapps
Icon=remapps
Terminal=false
Categories=System;Settings;PackageManager;
Keywords=uninstall;remove;clean;odinstaluj;wyczyść;
StartupNotify=true
EOF
chmod 644 "$BUDOWANY/usr/share/applications/remapps.desktop"

cat > "$BUDOWANY/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/share/applications >/dev/null 2>&1 || :
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor >/dev/null 2>&1 || :
fi
exit 0
EOF
cp "$BUDOWANY/DEBIAN/postinst" "$BUDOWANY/DEBIAN/postrm"
chmod 755 "$BUDOWANY/DEBIAN/postinst" "$BUDOWANY/DEBIAN/postrm"

find "$BUDOWANY" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || :
find "$BUDOWANY" -name '*.pyc' -delete 2>/dev/null || :

info "Buduję pakiet DEB..."
rm -f "$WYNIK"
dpkg-deb --build "$BUDOWANY" "$WYNIK"

rm -rf "$PROJEKT/build-deb"
info "Gotowe! Pakiet: $WYNIK"
info "Zainstaluj poleceniem:"
info "  sudo apt install $WYNIK"
