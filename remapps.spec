Name:           remapps
Version:        1.0.0
Release:        10%{?dist}
Summary:        Menedżer odinstalowywania i czyszczenia systemu

License:        GPL-3.0-or-later
URL:            https://github.com/1bypl/RemApps
Source0:        remapps-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3
Requires:       python3
Requires:       python3-pyside6
Requires:       polkit

%description
RemApps to graficzne narzędzie do znajdowania i odinstalowywania
wszystkich zainstalowanych programów wraz z plikami konfiguracyjnymi.
Obsługuje pakiety RPM/DEB, Flatpak, Snap, AppImage oraz skróty .desktop.
Posiada również czyszczenie kosza, pamięci podręcznych, historii
przeglądarek i starych logów. Dostępne jest 8 języków interfejsu.

Użytkownik korzysta z programu wyłącznie na własną odpowiedzialność.

%prep
%setup -q -n remapps-%{version}

%build
# Projekt jest w czystym Pythonie - nie ma czego kompilować.

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}%{_datadir}/remapps
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_datadir}/applications
mkdir -p %{buildroot}%{_datadir}/icons/hicolor/scalable/apps

cp -a remapps %{buildroot}%{_datadir}/remapps/
install -m 644 main.py %{buildroot}%{_datadir}/remapps/main.py
install -m 644 remapps/resources/logo.svg \
    %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/remapps.svg

cat > %{buildroot}%{_bindir}/remapps <<'EOF'
#!/bin/sh
exec python3 %{_datadir}/remapps/main.py "$@"
EOF
chmod 755 %{buildroot}%{_bindir}/remapps

cat > %{buildroot}%{_datadir}/applications/remapps.desktop <<'EOF'
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
chmod 644 %{buildroot}%{_datadir}/applications/remapps.desktop

find %{buildroot} -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || :
find %{buildroot} -name '*.pyc' -delete 2>/dev/null || :

%files
%license LICENSE
%doc README.md
%{_bindir}/remapps
%{_datadir}/remapps/
%{_datadir}/applications/remapps.desktop
%{_datadir}/icons/hicolor/scalable/apps/remapps.svg

%post
update-desktop-database %{_datadir}/applications >/dev/null 2>&1 || :
gtk-update-icon-cache -f -t %{_datadir}/icons/hicolor >/dev/null 2>&1 || :

%postun
update-desktop-database %{_datadir}/applications >/dev/null 2>&1 || :
gtk-update-icon-cache -f -t %{_datadir}/icons/hicolor >/dev/null 2>&1 || :

%changelog
* Sun Nov 22 2026 1bypl <1bypl@users.noreply.github.com> - 1.0.0-10
- Optymalizacja: motyw systemowy wykrywany raz, bez odpytywania gsettings
- Zmiana języka nie przebudowuje już całej listy programów
- Usunięcie programu aktualizuje tylko jeden wiersz i cache (bez pełnego skanu)
- Stabilniejsze wątki robocze — brak ryzykownego terminate() przy wyjściu

* Sun Nov 22 2026 1bypl <1bypl@users.noreply.github.com> - 1.0.0-9
- Lepsze wykrywanie motywu systemowego (KDE, GNOME, GTK)
- Informacja o wykrytym motywie w ustawieniach
- Podpis pod logo zmienia się razem z wybranym językiem

* Sun Nov 22 2026 1bypl <1bypl@users.noreply.github.com> - 1.0.0-8
- Lista programów odświeżana na świeżo po każdym usunięciu
- Przycisk „Odśwież listę" zawsze wykonuje prawdziwy skan

* Sat Nov 21 2026 1bypl <1bypl@users.noreply.github.com> - 1.0.0-7
- Rozpoznawanie pełnego ID Flatpak także ze starej pamięci podręcznej
- Unieważnienie starej pamięci podręcznej (wersja formatu)
- Poprawka kolorów zakładki „O programie" po zmianie na jasną skórkę

* Sat Nov 21 2026 1bypl <1bypl@users.noreply.github.com> - 1.0.0-6
- Usuwanie Flatpak używa pełnego identyfikatora (np. de.haeckerfelix.Shortwave)
- Wyszukiwanie przeniesione do modelu Qt — znacznie szybsze
- Poprawka aktualizacji listy przy aktywnym wyszukiwaniu

* Sat Nov 21 2026 1bypl <1bypl@users.noreply.github.com> - 1.0.0-5
- Wszystkie źródła (Flatpak/Flathub, Snap, AppImage) skanowane domyślnie
- Wyniki skanowania zapamiętywane — lista pojawia się od razu przy starcie
- Bezpieczne zamykanie programu w czasie pracy wątku skanowania

* Sat Nov 21 2026 1bypl <1bypl@users.noreply.github.com> - 1.0.0-4
- Prawidłowe usuwanie Flatpak/Flathub, Snap i AppImage
- Sprawdzanie, czy aplikacja naprawdę zniknęła po usunięciu
- Obsługa Arch Linux / Manjaro (pacman)
- Płynniejsze wyszukiwanie i wyraźniejsza ikona krokodyla

* Sat Nov 21 2026 1bypl <1bypl@users.noreply.github.com> - 1.0.0-3
- Poprawka błędu uruchomienia (zły import klasy Qt w delegacie przycisku)
- Błędy startu zapisywane są do ~/.local/share/remapps/error.log

* Sat Nov 21 2026 1bypl <1bypl@users.noreply.github.com> - 1.0.0-2
- Poprawka zawieszania się listy przy ponad 2000 pakietach
- Animacja i komunikat „Skanowanie systemu — proszę czekać"
- Nowa, czytelna ikona krokodyla z narzędziami

* Sat Nov 21 2026 1bypl <1bypl@users.noreply.github.com> - 1.0.0-1
- Pierwsze wydanie RemApps
