# Współtworzenie RemApps

Wszyscy są mile widziani — także osoby, które dopiero zaczynają przygodę
z kodem.

## Jak pomóc

1. **Zgłoś błąd** lub pomysł przez zakładkę
   [Issues](https://github.com/1bypl/RemApps/issues).
2. **Przetłumacz** interfejs — plik `remapps/i18n.py` zawiera słowniki
   dla wszystkich języków. Dodaj brakujące klucze we własnym języku.
3. **Popraw kod** — wyślij pull request z krótkim opisem zmian.
4. **Dodaj testy** na Fedorze lub Debianie/Ubuntu i opisz wyniki.

## Zasady

- Kod powinien być czytelny i komentowany po polsku lub angielsku.
- Żadna operacja usuwania nie może odbywać się bez potwierdzenia użytkownika.
- Nowe funkcje muszą mieć obsługę w `i18n.py` dla wszystkich języków.
- Zachowuj licencję GPL-3.0-or-later.

## Uruchomienie w wersji developerskiej

```sh
python3 -m pip install --user PySide6
python3 main.py
```

Sprawdzenie składni:

```sh
python3 -m compileall -q remapps main.py
```

---

Autor projektu: **1bypl**
