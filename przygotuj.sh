#!/bin/sh
# Przygotowuje kompletny folder do wgrania na GitHub.

set -e
SKRYPT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJEKT=$(CDPATH= cd -- "$SKRYPT/.." && pwd)
CEL="$SKRYPT/RemApps_do_wgrania"

printf '[RemApps] Przygotowuje paczke...\n'
rm -rf "$CEL"
mkdir -p "$CEL"

cp -R "$PROJEKT/remapps" "$CEL/"
cp "$PROJEKT/main.py" "$CEL/"
cp "$PROJEKT/README.md" "$CEL/"
cp "$PROJEKT/LICENSE" "$CEL/"
cp "$PROJEKT/INFO.md" "$CEL/"
cp "$PROJEKT/AUDIT.md" "$CEL/"
cp "$PROJEKT/CONTRIBUTING.md" "$CEL/"
cp "$PROJEKT/requirements.txt" "$CEL/"
cp "$PROJEKT/.gitignore" "$CEL/"
cp -R "$PROJEKT/install" "$CEL/"
cp -R "$PROJEKT/packaging" "$CEL/"
cp -R "$PROJEKT/DOKUMENTACJA" "$CEL/"
cp -R "$PROJEKT/.github" "$CEL/"
mkdir -p "$CEL/github/screenshots"
cp "$SKRYPT/screenshots/"*.png "$CEL/github/screenshots/" 2>/dev/null || true

find "$CEL" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
find "$CEL" -name '*.pyc' -delete 2>/dev/null || true

printf '[RemApps] Gotowe: %s\n' "$CEL"
printf '[RemApps] Zrzuty ekranu: %s/github/screenshots/\n' "$CEL"
