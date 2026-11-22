#!/bin/sh
# Buduje pakiet .rpm (Fedora i pochodne).
# Użycie: sh packaging/rpm/build_rpm.sh
# Wymagania: sudo dnf install rpm-build

set -e

SKRYPT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJEKT=$(CDPATH= cd -- "$SKRYPT/../.." && pwd)
WERSJA="1.0.0"

info() { printf '\033[1;32m[RemApps RPM]\033[0m %s\n' "$1"; }
blad() { printf '\033[1;31m[BŁĄD]\033[0m %s\n' "$1" >&2; exit 1; }

if ! command -v rpmbuild >/dev/null 2>&1; then
    blad "Brak rpmbuild. Zainstaluj: sudo dnf install rpm-build"
fi

KATALOG_RPM="$HOME/rpmbuild"
mkdir -p "$KATALOG_RPM"/{SOURCES,SPECS,BUILD,RPMS,SRPMS}

info "Przygotowuję archiwum źródłowe..."
NAZWA_KATALOGU=$(basename "$PROJEKT")
KATALOG_NADRZEDNY=$(dirname "$PROJEKT")
rm -f "$KATALOG_RPM/SOURCES/remapps-$WERSJA.tar.gz"
tar -C "$KATALOG_NADRZEDNY" \
    --transform="s|^$NAZWA_KATALOGU|remapps-$WERSJA|" \
    -czf "$KATALOG_RPM/SOURCES/remapps-$WERSJA.tar.gz" "$NAZWA_KATALOGU"

info "Kopiuję specyfikację..."
cp "$SKRYPT/remapps.spec" "$KATALOG_RPM/SPECS/remapps.spec"

info "Usuwam stare wersje pakietu z folderu RPMS..."
rm -f "$KATALOG_RPM"/RPMS/*/remapps-*.rpm 2>/dev/null || :

info "Buduję pakiet RPM..."
rpmbuild -bb "$KATALOG_RPM/SPECS/remapps.spec"

info "Gotowe! Pakiet znajdziesz tutaj:"
ls -lh "$KATALOG_RPM"/RPMS/*/remapps-*.rpm 2>/dev/null || :
PLIK_RPM=$(find "$KATALOG_RPM/RPMS" -name 'remapps-*.rpm' -print -quit 2>/dev/null)
if [ -n "$PLIK_RPM" ]; then
    info "Zainstaluj dokładnie tym poleceniem:"
    printf '  sudo dnf install %s\n' "$PLIK_RPM"
fi
