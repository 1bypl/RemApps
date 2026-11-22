# Folder przygotowawczy do GitHuba

Ten folder jest przeznaczony na finalną wersję projektu, którą wrzucisz
na https://github.com/1bypl/RemApps.

## Jak przygotować paczkę

1. Uruchom skrypt (z folderu projektu):

   ```sh
   sh github/przygotuj.sh
   ```

2. Powstanie folder `github/RemApps_do_wgrania/` z kompletnym kodem.

3. **Zrzuty ekranu już są** w folderze `github/screenshots/`:
   - `programy.png` – zakładka z listą programów,
   - `czyszczenie.png` – zakładka czyszczenia,
   - `ustawienia.png` – zakładka ustawień,
   - `oprogramie.png` – zakładka „O programie" z krokodylem.

   Skrypt sam skopiuje je do paczki jako `github/screenshots/`.

4. Skopiuj zawartość `github/RemApps_do_wgrania/` do repozytorium GitHub
   i zatwierdź zmiany (`git add . && git commit -m "RemApps 1.0.0" && git push`).

## Uwaga

Zrzuty ekranu dodajesz Ty – autor projektu nie ma dostępu do Twojego
pulpitu. Dopiero po nich README będzie zawierał prawdziwe obrazy.
