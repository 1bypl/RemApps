# RemApps 🐊

**Menedżer odinstalowywania i czyszczenia systemu dla Linuksa**

RemApps to prosty w obsłudze program z nowoczesnym interfejsem, który znajduje
**wszystkie zainstalowane programy** — niezależnie od tego, skąd pochodzą —
i pozwala usunąć je razem z plikami konfiguracyjnymi i pozostałościami.

Działa na **Fedorze**, **Debianie / Ubuntu** oraz **Arch Linux / Manjaro**.
Potrafi też usuwać aplikacje **Flatpak (także z Flathub)**, **Snap** i **AppImage**.

> ⚠️ **Ważne:** Program jest narzędziem zaawansowanym. Używasz go wyłącznie
> na własną odpowiedzialność. Zawsze czytaj okna potwierdzenia i wykonuj
> kopię ważnych danych. Dostępny jest też **tryb symulacji**, który nic nie usuwa.

---

## Wygląd i ikona

Logo to zielony, uśmiechnięty krokodyl trzymający w łapkach narzędzia
(klucz i śrubokręt) – symbol naprawy i porządku w systemie. Ikona znajduje
się w pliku [`remapps/resources/logo.svg`](https://github.com/logo.svg)
oraz w interfejsie programu i w zakładce „O programie".

---

## Zrzuty ekranu

### Programy

![Lista zainstalowanych programów](https://github.com/programy.png)

### Czyszczenie i pielęgnacja systemu

![Zakładka czyszczenia](https://github.com/czyszczenie.png)

### Ustawienia

![Zakładka ustawień](https://github.com/ustawienia.png)

### O programie

![Zakładka o programie z logo krokodyla](https://github.com/oprogramie.png)

Zrzuty wykonano na **Fedorze 45 (KDE Plasma)**. Na pierwszym widać m.in.
2779 wykrytych programów oraz czasy skanowania w pasku stanu
(`rpm: 0.75s, flatpak: 0.02s, snap: 0.0s, appimage: 0.0s, desktop: 0.02s`).

---

## Co potrafi RemApps

### Zakładka „Programy"
- jednym kliknięciem skanuje całą bazę zainstalowanego oprogramowania
  (w czasie skanowania widać animację i komunikat „Proszę czekać"),
- lista wypełnia się partiami, więc nawet 2000+ pakietów nie zawiesza okna,
- pokazuje listę z **nazwą, wersją, rozmiarem, ikoną i źródłem** programu,
- wyszukuje programy niezależnie od pochodzenia:
  - pakiety **RPM** (Fedora) i **DEB** (Debian/Ubuntu),
  - **Flatpak** (również z Flathub), **Snap**, **AppImage**,
  - pakiety **pacman** (Arch Linux, Manjaro),
  - aplikacje z plików **.desktop** (także spoza repozytoriów),
- dla Flatpak/Snap używa właściwych poleceń (`flatpak uninstall`,
  `snap remove`) zamiast poleceń systemowych,
- po usunięciu **sprawdza, czy program naprawdę zniknął** i nie pokazuje
  fałszywego komunikatu o sukcesie,
- po kliknięciu „Usuń" pyta, czy usunąć też:
  - nieużywane **zależności**,
  - **pliki konfiguracyjne i „rejestr"** programu,
- pokazuje **podgląd polecenia** przed zatwierdzeniem,
- chroni pakiety systemowe (np. `glibc`, `bash`, `systemd`) ostrzeżeniem.

### Zakładka „Czyszczenie"
- usuwa zawartość **kosza** (także na innych dyskach),
- znajduje **osierocone resztki** po programach (`.rpmsave`, `.rpmnew`,
  `.dpkg-old`, `.dpkg-dist` itp.),
- czyści **pamięci podręczne** (cache) użytkownika i systemu,
- czyści **historię przeglądarek** Firefox, Chrome, Chromium, Brave, Vivaldi
  (historię Firefoxa czyści bez usuwania zakładek),
- usuwa stare **logi** i ogranicza dziennik systemowy do 7 dni,
- każdy element można zaznaczyć lub odznaczyć przed czyszczeniem.

### Zakładka „Ustawienia"
- **8 języków**: polski, angielski, niemiecki, rosyjski, francuski,
  włoski, hiszpański, czeski,
- motyw **jasny / ciemny / zgodny z systemem**,
- trzy tryby wyszukiwania:
  - **Standardowy** – szybki odczyt bazy pakietów,
  - **Dokładny** – baza pakietów + Flatpak, Snap, AppImage + pliki .desktop,
  - **Po katalogach** – skanowanie folderów instalacji i skrótów .desktop,
- **tryb symulacji** – bezpieczny test bez usuwania czegokolwiek,
- przywracanie ustawień domyślnych.

### Zakładka „O programie"
Przeznaczenie, sposób działania na Fedorze i Debian/Ubuntu, licencja
**GPL 3**, ostrzeżenie o odpowiedzialności użytkownika, autor **1bypl**
oraz odnośnik do GitHuba: <https://github.com/1bypl/>.

---

## Instalacja

### ⚠️ Najpierw wejdź do folderu projektu

Terminal zawsze szuka plików **tam, gdzie aktualnie jesteś**. Jeśli jesteś
w folderze domowym (`~`), wpisz najpierw:

```sh
cd ~/Pulpit/RemApps
```

Możesz też z dowolnego miejsca użyć pełnej ścieżki:

```sh
sh ~/Pulpit/RemApps/install/install_fedora.sh
```

---

### Sposób 1: gotowy pakiet `.rpm` (Fedora)

Pakiet to najwygodniejsza metoda – system sam pilnuje zależności i potrafi
program odinstalować.

**Zbudowanie pakietu** (raz):

```sh
sudo dnf install rpm-build
sh packaging/rpm/build_rpm.sh
```

Skrypt tworzy plik w `~/rpmbuild/RPMS/noarch/remapps-1.0.0-1.*.noarch.rpm`.

**Instalacja:**

```sh
sudo dnf install ~/rpmbuild/RPMS/noarch/remapps-*.rpm
```

**Odinstalowanie:**

```sh
sudo dnf remove remapps
```

### Sposób 2: gotowy pakiet `.deb` (Debian / Ubuntu)

**Zbudowanie pakietu** (raz):

```sh
sudo apt install dpkg-dev
sh packaging/deb/build_deb.sh
```

Skrypt tworzy plik `remapps_1.0.0_all.deb` w folderze projektu.

**Instalacja:**

```sh
sudo apt install ./remapps_1.0.0_all.deb
```

**Odinstalowanie:**

```sh
sudo apt remove remapps
```

### Sposób 3: szybka instalacja do folderu użytkownika

Jeśli nie chcesz budować pakietu:

- Fedora: `sh install/install_fedora.sh`
- Debian/Ubuntu: `sh install/install_debian.sh`

Instalator:
1. sprawdza wersję Pythona,
2. instaluje PySide6 (jeśli potrzeba),
3. instaluje `polkit`/`pkexec` (potrzebne do uprawnień administratora),
4. kopiuje pliki do `~/.local/share/remapps`,
5. tworzy polecenie `remapps` i skrót w menu aplikacji.

Nie potrzebujesz roota do samej instalacji (poza doinstalowaniem pakietów).
Odinstalowanie: `sh install/uninstall.sh`.

### Uruchomienie

```sh
remapps
```

albo wybierz **RemApps** w menu aplikacji.

> Jeśli po instalacji polecenie `remapps` nie działa, otwórz nowe okno
> terminala albo dodaj do `~/.bashrc` linię:
> `export PATH="$HOME/.local/bin:$PATH"`

### Uruchomienie bez instalacji (z folderu projektu)

```sh
python3 -m pip install --user PySide6
python3 main.py
```

---

## Jak to działa „po ludzku"

W Linuksie nie ma rejestru w wersji z Windows. Informacje o programach
są zapisane w:

- **bazie pakietów** – `rpm -qa` na Fedorze, `dpkg-query` na Debianie/Ubuntu,
  `pacman -Q` na Archu, `flatpak list` i `snap list` dla aplikacji z zewnątrz,
- **plistach konfiguracyjnych** w `/etc` i w katalogu użytkownika,
- **plikach skrótów** `.desktop` i resztkach po odinstalowaniu.

RemApps czyta te źródła, pokazuje wyniki i — dopiero po Twoim potwierdzeniu —
wywołuje `dnf remove`, `apt-get remove/purge` albo usuwa wskazane pliki.
Uprawnienia administratora są uzyskiwane przez okno systemowe `pkexec`,
więc program nie prosi Cię o hasło w swoim oknie.

---

## Bezpieczeństwo

- Domyślnie nic nie jest usuwane bez Twojego potwierdzenia.
- Przed usunięciem zobaczysz dokładne polecenie i listę plików.
- Pakiety krytyczne dla systemu są oznaczone czerwonym ostrzeżeniem.
- Tryb symulacji pozwala sprawdzić działanie bez ryzyka.
- historia Firefoxa jest czyszczona przez bazę SQLite — zakładki zostają.

Mimo to usuwanie oprogramowania zawsze może coś zepsuć. **Rób kopie zapasowe.**

---

## Dokumentacja

- [`INFO.md`](INFO.md) – krótka informacja o projekcie,
- [`AUDIT.md`](AUDIT.md) – audyt bezpieczeństwa i jakości kodu,
- [`DOKUMENTACJA/`](DOKUMENTACJA/) – instrukcja użytkownika i info o licencji.

---

## Autor i licencja

**Twórca:** 1bypl — <https://github.com/1bypl/>

**Licencja:** GNU GPL wersja 3 lub nowsza (GPL-3.0-or-later).

Program dostarczany jest **bez żadnej gwarancji**. Używasz go na własną
odpowiedzialność.
