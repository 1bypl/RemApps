# Instrukcja użytkownika — RemApps

Ilustracje wszystkich zakładek znajdują się w folderze
`github/screenshots/` oraz w głównym `README.md`.

## Uruchomienie

Po instalacji wpisz w terminalu:

```sh
remapps
```

albo otwórz menu aplikacji i wybierz **RemApps**.
W oknie uwierzytelnienia (pkexec) podaj hasło swojego użytkownika —
tylko wtedy, gdy program faktycznie coś usuwa.

---

## Zakładka „Programy" — krok po kroku

1. Poczekaj, aż lista się wypełni (program skanuje system w tle).
2. Wpisz fragment nazwy w pole wyszukiwania, jeśli szukasz czegoś konkretnego.
3. Wybierz tryb wyszukiwania:
   - **Standardowy** — najszybszy, czyta tylko bazę pakietów systemu,
   - **Dokładny** — dodaje Flatpak, Snap, AppImage i skróty `.desktop`,
   - **Po katalogach** — przeszukuje foldery, w których instaluje się
     oprogramowanie poza repozytoriami.
4. Kliknij przycisk **Usuń** przy wybranym programie.
5. W oknie potwierdzenia zdecyduj:
   - czy usunąć nieużywane zależności,
   - czy usunąć pliki konfiguracyjne („rejestr") programu.
6. Sprawdź **podgląd polecenia** — to dokładnie to, co zostanie wykonane.
7. Kliknij **Tak, usuń**. Pojawi się systemowe okno hasła.
8. Po zakończeniu zobaczysz komunikat, a lista zostanie odświeżona.

💡 **Podwójne kliknięcie** na wiersz pokazuje szczegóły programu.

---

## Zakładka „Czyszczenie" — krok po kroku

1. Zaznacz kategorie, które Cię interesują (kosz, resztki, cache,
   historia przeglądarek, logi).
2. Kliknij **Skanuj**.
3. W drzewie wyników odznacz elementy, których nie chcesz usuwać.
4. Kliknij **Wykonaj czyszczenie**.
5. Przeczytaj ostrzeżenie (szczególnie o zamknięciu przeglądarek)
   i potwierdź.
6. Raport pokaże, co udało się usunąć.

---

## Zakładka „Ustawienia"

- **Język interfejsu** — zmiana jest natychmiastowa.
- **Wygląd** — jasny, ciemny albo taki jak w systemie.
- **Domyślny tryb wyszukiwania** — ustawiany przy starcie programu.
- **Tryb symulacji** — zalecany na początek. Pokazuje, co program
  zrobiłby, ale nic nie zmienia.
- **Zawsze pytaj o pliki konfiguracyjne** — domyślnie włączone.
- **Przywróć ustawienia domyślne** — powrót do stanu początkowego.

---

## Częste pytania

**Czy RemApps usunie programy zainstalowane ręcznie (np. AppImage)?**  
Tak, w trybie „Dokładnym" lub „Po katalogach" znajdzie pliki AppImage
i skróty `.desktop`. Usunięcie wymaga potwierdzenia.

**Dlaczego nie widzę programu w trybie standardowym?**  
Bo tryb standardowy czyta tylko bazę pakietów. Użyj trybu „Dokładnego".

**Czy usunięcie historii Firefoxa usunie zakładki?**  
Nie. RemApps czyści tylko tabele historii w bazie SQLite.

**Dlaczego pojawia się okno hasła?**  
Bo usuwanie pakietów wymaga uprawnień administratora. RemApps nie zna
Twojego hasła — wyświetla je systemowe okno `pkexec`.

**Czy mogę cofnąć usunięcie?**  
Nie. Dlatego warto najpierw użyć trybu symulacji i zrobić kopię danych.

---

## Kontakt

https://github.com/1bypl/RemApps/issues
