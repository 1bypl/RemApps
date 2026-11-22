# INFO — RemApps

**Nazwa:** RemApps  
**Wersja:** 1.0.0 (pakiet RPM: release 10)  
**Twórca:** 1bypl  
**Repozytorium:** https://github.com/1bypl/RemApps  
**Licencja:** GPL-3.0-or-later  
**Język implementacji:** Python 3 + PySide6 (Qt for Python)  
**Systemy:** Fedora (RPM/dnf), Debian/Ubuntu (DEB/apt), Arch Linux/Manjaro (pacman)
**Źródła aplikacji:** repozytoria, Flatpak/Flathub, Snap, AppImage, pliki .desktop

---

## W skrócie

RemApps to graficzne narzędzie, które:

1. jednym kliknięciem skanuje zainstalowane oprogramowanie
   (RPM, DEB, Flatpak, Snap, AppImage, pliki .desktop),
2. wyświetla listę z nazwą, wersją, rozmiarem i ikoną,
3. pozwala usunąć wybrany program wraz z zależnościami i plikami
   konfiguracyjnymi po potwierdzeniu,
4. czyści resztki po programach, kosz, cache, historię przeglądarek i logi,
5. oferuje 8 języków, trzy tryby wyszukiwania i tryb symulacji.

## Dlaczego powstał

Discover i podobne centra oprogramowania często pokazują tylko to, co
znajduje się w ich bazie. Programy doinstalowane ręcznie, z Internetu
(AppImage), z Flatpak/Snap albo starsze resztki konfiguracji bywają
niewidoczne. RemApps łączy wszystkie te źródła w jednym oknie i pokazuje
dokładnie, co zostanie usunięte.

## Struktura folderu

```
RemApps/
├── main.py                  – uruchomienie aplikacji
├── remapps/
│   ├── app.py               – start Qt
│   ├── i18n.py              – 8 języków
│   ├── core/
│   │   ├── detector.py      – wykrywanie dystrybucji
│   │   ├── packages.py      – skanowanie programów
│   │   ├── remover.py       – plan i wykonanie usunięcia
│   │   ├── cleaner.py       – czyszczenie systemu
│   │   └── settings.py      – ustawienia użytkownika
│   ├── ui/                  – okna, style, ikony, wątki
│   └── resources/logo.svg   – logo krokodyla z narzędziami
├── install/                 – szybkie instalatory i deinstalator
├── packaging/
│   ├── rpm/                 – specyfikacja i builder pakietu .rpm
│   └── deb/                 – control i builder pakietu .deb
├── DOKUMENTACJA/            – poradnik i info o licencji
├── github/                  – paczka do wgrania na GitHub + zrzuty ekranu
│   ├── screenshots/         – 4 obrazy PNG użyte w README
│   └── przygotuj.sh         – skrypt tworzący RemApps_do_wgrania/
├── README.md
├── AUDIT.md
├── CONTRIBUTING.md
└── LICENSE
```

## Status testów

Wersja 1.0.0 została przetestowana na **Fedorze 45 (KDE Plasma)**:
zbudowanie i instalacja pakietu `.rpm`, wykrycie 2779 programów,
usuwanie pakietów RPM, aplikacji Flatpak z Discover oraz narzędzi
konsolowych (fastfetch, duf, btop). Zrzuty czterech zakładek znajdują
się w `github/screenshots/` i są wstawione do `README.md`.

## Kontakt

Zgłoszenia, pomysły i poprawki: https://github.com/1bypl/RemApps/issues
