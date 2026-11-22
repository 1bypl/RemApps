# AUDYT — RemApps 1.0.0

Data audytu: 2026-11-21 / aktualizacja: 2026-11-22  
Zakres: kod źródłowy, instalatory, dokumentacja  
Metoda: przegląd statyczny kodu, test składni `python3 -m compileall`,
analiza ścieżek usuwania danych oraz **testy rzeczywiste na Fedorze 45
(KDE Plasma)** wykonane przez użytkownika.

---

## 1. Podsumowanie

| Obszar | Ocena | Uwagi |
|---|---|---|
| Składnia kodu | ✅ OK | `compileall` bez błędów dla wszystkich modułów |
| Struktura projektu | ✅ OK | logiczny podział na `core`, `ui`, `resources`, `install` |
| Potwierdzenia przed usunięciem | ✅ OK | każde usunięcie wymaga akceptacji w oknie dialogowym |
| Podgląd polecenia | ✅ OK | użytkownik widzi dokładne polecenie i listę plików |
| Ochrona pakietów systemowych | ✅ OK | lista chronionych pakietów + dodatkowe potwierdzenie |
| Uprawnienia administratora | ⚠️ Akceptowalne | przez `pkexec` (polkit), nie przez hasło w aplikacji |
| Tryb symulacji | ✅ OK | dostępny; nie wykonuje destrukcyjnych poleceń |
| Testy interfejsu GUI | ✅ Wykonane | 4 zrzuty ekranu w `github/screenshots/` |
| Testy na realnej Fedorze 45 | ✅ Wykonane | instalacja RPM, skan 2779 programów, usuwanie RPM i Flatpak |
| Testy na Debian/Ubuntu i Arch | ⚠️ Nie wykonane | ścieżka kodu sprawdzona statycznie |

---

## 2. Analiza ryzyk

### 2.1 Usuwanie pakietów (RYZYKO: wysokie)
**Co może pójść źle:** usunięcie pakietu systemowego może uszkodzić system.  
**Zabezpieczenia:**
- lista `CHRONIONE_RPM` / `CHRONIONE_DEB` (glibc, bash, systemd, dnf, apt itd.),
- czerwone ostrzeżenie i dodatkowe pole wyboru „Rozumiem ryzyko",
- podgląd polecenia i pełna lista plików konfiguracyjnych przed kliknięciem,
- brak domyślnego zaznaczenia „usuń zależności".

**Pozostałe ryzyko:** użytkownik może świadomie potwierdzić usunięcie
ważnego pakietu. To zamierzona decyzja „na własną odpowiedzialność".

### 2.2 Usuwanie plików (RYZYKO: średnie)
**Co może pójść źle:** skrót `.desktop` może wskazywać na plik systemowy.  
**Zabezpieczenia:** program usuwa plik wykonywalny tylko wtedy, gdy znajduje
się w katalogu domowym użytkownika lub w `/opt`; sprawdzany jest
`os.path.realpath` (chroni przed symlinkami do `/usr`).

**Pozostałe ryzyko:** pliki w `/opt` wymagają `pkexec` i są pokazywane
w podglądzie przed usunięciem.

### 2.3 Czyszczenie historii przeglądarek (RYZYKO: średnie)
**Zabezpieczenia:**
- Firefox: usuwanie jest wykonywane przez SQLite (tylko tabele historii),
  zakładki pozostają nienaruszone,
- Chrome/Chromium: usuwany jest tylko plik `History` (zakładki są w osobnym
  pliku `Bookmarks`),
- ostrzeżenie o konieczności zamknięcia przeglądarki,
- zamknięcie bazy z `timeout=5` i obsługa błędów SQLite.

**Pozostałe ryzyko:** przeglądarka może zapisać historię ponownie po
uruchomieniu (synchronizacja konta). To normalne zachowanie usługi, nie błąd.

### 2.4 Podnoszenie uprawnień (RYZYKO: średnie)
Program używa `pkexec`, czyli standardowego mechanizmu polkit.
- Nie prosi o hasło w swoim interfejsie.
- Nie zapisuje haseł.
- Nie uruchamia powłoki (`shell=False` w `subprocess.run`).
- Nazwy pakietów pochodzą z bazy systemowej, a nie z wolnego tekstu
  użytkownika (zmniejsza ryzyko wstrzyknięcia polecenia).

### 2.5 Instalatory (RYZYKO: niskie)
- Instalują do `~/.local/share/remapps` (bez `sudo` dla plików programu).
- Nie modyfikują plików systemowych poza instalacją brakujących pakietów.
- `install/uninstall.sh` czyści tylko katalogi RemApps.

---

## 3. Uwagi o jakości kodu

- ✅ Wszystkie długie operacje (skanowanie, usuwanie, czyszczenie) działają
  w wątku `QThread`, więc okno się nie zawiesza.
- ✅ Interfejs jest w pełni przetłumaczony na 8 języków (94 klucze na język).
- ✅ Lista programów jest wypełniana partiami po 150 wierszy, przyciski „Usuń"
  są rysowane przez delegata (bez tysięcy widgetów), a ikony są buforowane
  — dzięki temu interfejs nie blokuje się na systemach z 2000+ pakietami.
- ✅ W czasie skanowania wyświetlany jest animowany wskaźnik i komunikat
  „Skanowanie systemu — proszę czekać" (przeciwdziałanie wrażeniu zawieszenia).
- ✅ Ustawienia zapisywane są w `~/.config/remapps/settings.json`.
- ⚠️ Wykrywanie dystrybucji opiera się na `/etc/os-release`; w środowiskach
  kontenerowanych (np. Flatpak) może zwrócić `unknown` — wtedy program
  próbuje wykryć `rpm`/`dpkg` po dostępności poleceń.
- ⚠️ Lista chronionych pakietów jest skrócona i może wymagać rozszerzenia
  o pakiety specyficzne dla danej dystrybucji.

---

## 4. Rekomendacje przed pierwszym użyciem

1. W ustawieniach włączyć **tryb symulacji** i przejść przez cały proces
   (wybór programu → podgląd → potwierdzenie).
2. Wyłączyć tryb symulacji dopiero po sprawdzeniu, że polecenia są poprawne.
3. Przy czyszczeniu historii przeglądarek zamknąć przeglądarki.
4. Zrobić migawkę systemu (Snapshot w Btrfs/Timeshift) przed czyszczeniem
   pakietów systemowych.
5. Przetestować na maszynie wirtualnej przed użyciem na komputerze
   produkcyjnym.

---

## 5. Wniosek

Projekt jest bezpieczny do użytku **z zastrzeżeniami** wymienionymi powyżej.
Największym ryzykiem nie są błędy kodu, lecz świadome działania użytkownika.
Dlatego program konsekwentnie pokazuje podgląd, pyta o potwierdzenie
i oferuje tryb symulacji.

Wersja 1.0.0 (RPM release 10) została **przetestowana w praktyce na Fedorze 45**:
program zbudował i zainstalował pakiet, wykrył 2779 aplikacji, poprawnie
usunął oprogramowanie RPM oraz Flatpak z Discover (Shortwave, Strawberry),
a także narzędzia konsolowe (fastfetch, duf, btop). Po usunięciu aplikacje
zniknęły z menu, paska i z listy RemApps. Interfejs i tłumaczenia sprawdzono
wizualnie – zrzuty znajdują się w `github/screenshots/`.

**Odpowiedzialność za użycie programu ponosi użytkownik.**
