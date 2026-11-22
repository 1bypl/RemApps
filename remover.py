"""Bezpieczne odinstalowywanie oprogramowania.

Każde działanie jest poprzedzone planem, który użytkownik widzi
i musi potwierdzić.program nie usuwa niczego „po cichu".
"""

from __future__ import annotations

import os
import shlex
import subprocess
from dataclasses import dataclass, field

from .detector import DistroInfo, has_command
from .packages import Package

CHRONIONE_RPM = {
    "glibc", "glibc-common", "kernel", "kernel-core", "systemd", "bash",
    "coreutils", "rpm", "dnf", "yum", "selinux-policy", "dbus", "filesystem",
    "openssl", "zlib", "libgcc", "device-mapper", "dracut",
}
CHRONIONE_DEB = {
    "libc6", "systemd", "bash", "coreutils", "dpkg", "apt", "apt-utils",
    "base-files", "debianutils", "libgcc-s1", "openssl", "zlib1g", "dbus",
    "procps", "sudo", "init",
}
CHRONIONE_ARCH = {
    "glibc", "systemd", "bash", "coreutils", "pacman", "linux", "linux-lts",
    "filesystem", "openssl", "zlib", "gcc-libs", "dbus", "sudo", "shadow",
    "pamd", "device-mapper", "mkinitcpio", "networkmanager",
}


@dataclass
class RemovalPlan:
    package_name: str
    command: list[str]
    description: str
    simulation_command: list[str] = field(default_factory=list)
    config_files: list[str] = field(default_factory=list)
    needs_root: bool = True
    extra_files: list[str] = field(default_factory=list)
    alternatywa: list[str] = field(default_factory=list)

    def preview(self) -> str:
        return " ".join(shlex.quote(c) for c in self.command)


def jest_chroniony(nazwa: str, distro: DistroInfo) -> bool:
    if distro.family == "rpm":
        zestaw = CHRONIONE_RPM
    elif distro.family == "arch":
        zestaw = CHRONIONE_ARCH
    else:
        zestaw = CHRONIONE_DEB
    return nazwa.lower() in zestaw


def _config_files_rpm(nazwa: str) -> list[str]:
    if not has_command("rpm"):
        return []
    wyjscie = subprocess.run(
        ["rpm", "-qc", nazwa], capture_output=True, text=True, errors="replace"
    ).stdout
    return [l.strip() for l in wyjscie.splitlines() if l.strip() and os.path.exists(l.strip())]


def _config_files_deb(nazwa: str) -> list[str]:
    sciezka = f"/var/lib/dpkg/info/{nazwa}.conffiles"
    wynik = []
    if not os.path.exists(sciezka):
        return wynik
    try:
        with open(sciezka, encoding="utf-8", errors="replace") as plik:
            for linia in plik:
                p = linia.strip()
                if p and os.path.exists(p):
                    wynik.append(p)
    except OSError:
        pass
    return wynik


def _config_files_arch(nazwa: str, wersja: str = "") -> list[str]:
    """Pliki w /etc zainstalowane przez pakiet pacman."""
    katalog = ""
    baza = "/var/lib/pacman/local"
    if wersja and os.path.isdir(os.path.join(baza, f"{nazwa}-{wersja}")):
        katalog = os.path.join(baza, f"{nazwa}-{wersja}")
    else:
        for wpis in os.listdir(baza) if os.path.isdir(baza) else []:
            if wpis.startswith(nazwa + "-"):
                katalog = os.path.join(baza, wpis)
                break
    plik_listy = os.path.join(katalog, "files") if katalog else ""
    wynik = []
    if not plik_listy or not os.path.exists(plik_listy):
        return wynik
    try:
        with open(plik_listy, encoding="utf-8", errors="replace") as f:
            for linia in f:
                p = linia.strip()
                if p.startswith("/etc/") and os.path.exists(p) and p not in wynik:
                    wynik.append(p)
    except OSError:
        pass
    return wynik


def config_files(nazwa: str, distro: DistroInfo, wersja: str = "") -> list[str]:
    if distro.family == "rpm":
        pliki = _config_files_rpm(nazwa)
    elif distro.family == "arch":
        pliki = _config_files_arch(nazwa, wersja)
    else:
        pliki = _config_files_deb(nazwa)
    # dodaj typowe pozostałości
    rezultat = list(pliki)
    for p in pliki:
        for sufiks in (".rpmsave", ".rpmnew", ".dpkg-old", ".dpkg-new",
                       ".dpkg-dist", ".ucf-dist", ".pacnew", ".pacsave", ".pacorig"):
            kandydat = p + sufiks
            if os.path.exists(kandydat) and kandydat not in rezultat:
                rezultat.append(kandydat)
    return rezultat


def id_flatpak(pakiet: Package) -> str:
    """Zwraca pełny identyfikator Flatpak (np. de.haeckerfelix.Shortwave).

    Działa też dla stary, nieaktualnych wpisów w pamięci podręcznej,
    które nie miały jeszcze pola package_id.
    """
    kandydat = (pakiet.package_id or "").strip()
    if "." not in kandydat:
        kandydat = (pakiet.description or "").strip()
    if "." in kandydat:
        return kandydat
    # Ostatnia deska ratunku: Find ID po nazwie wyświetlanej
    try:
        wynik = subprocess.run(
            ["flatpak", "list", "--app", "--columns=application,name"],
            capture_output=True, text=True, errors="replace", timeout=60,
        )
        for linia in wynik.stdout.splitlines():
            czesci = linia.split("\t")
            if len(czesci) >= 2 and czesci[1].strip().lower() == pakiet.name.lower():
                return czesci[0].strip()
    except Exception:
        pass
    return pakiet.name


def build_plan(
    pakiet: Package,
    distro: DistroInfo,
    zalezności: bool = False,
    konfiguracja: bool = False,
    symulacja: bool = False,
) -> RemovalPlan:
    if pakiet.source in ("desktop", "appimage"):
        return _build_file_plan(pakiet, symulacja)

    nazwa = pakiet.name

    # Flatpak i Snap mają własne polecenia — nie można ich usuwać przez dnf/apt
    if pakiet.source == "flatpak":
        # Flatpak wymaga pełnego ID (np. de.haeckerfelix.Shortwave),
        # nie nazwy wyświetlanej użytkownikowi.
        ident = id_flatpak(pakiet)
        if symulacja:
            cmd = ["flatpak", "uninstall", "--assumeno", ident]
            return RemovalPlan(ident, cmd, "Symulacja usunięcia Flatpak", cmd, [], False)
        plan = RemovalPlan(
            ident, ["flatpak", "uninstall", "-y", "--noninteractive", ident],
            "Usunięcie aplikacji Flatpak", [], [], False,
        )
        # instalacja systemowa wymaga uprawnień — spróbuj w razie potrzeby
        plan.alternatywa = ["pkexec", "flatpak", "uninstall", "-y", ident]
        return plan

    if pakiet.source == "snap":
        if symulacja:
            cmd = ["snap", "remove", "--assumeno", nazwa]
            return RemovalPlan(nazwa, cmd, "Symulacja usunięcia Snap", cmd, [], False)
        return RemovalPlan(
            nazwa, ["pkexec", "snap", "remove", nazwa],
            "Usunięcie aplikacji Snap", [], [],
        )

    if distro.family == "arch":
        if symulacja:
            cmd = ["pacman", "-Qi", nazwa]
            return RemovalPlan(nazwa, cmd, "Symulacja usunięcia pacman", cmd, [], False)
        # -Rns usuwa też nieużywane zależności i zapisy konfiguracji
        cmd = (["pkexec", "pacman", "-Rns", "--noconfirm", nazwa] if zalezności
               else ["pkexec", "pacman", "-Rn", "--noconfirm", nazwa])
        cfg = config_files(nazwa, distro, pakiet.version) if konfiguracja else []
        return RemovalPlan(nazwa, cmd, "Usunięcie pakietu Arch (pacman)", [], cfg)

    if distro.family == "rpm":
        if symulacja:
            cmd = [distro.package_manager, "--assumeno", "remove", nazwa]
            return RemovalPlan(nazwa, cmd, "Symulacja usunięcia (nic nie zostanie zmienione)",
                               cmd, [], False)
        cmd = ["pkexec", distro.package_manager, "-y", "remove", nazwa]
        if zalezności:
            cmd = ["pkexec", distro.package_manager, "-y",
                   "--setopt=clean_requirements_on_remove=True", "remove", nazwa]
        cfg = config_files(nazwa, distro) if konfiguracja else []
        return RemovalPlan(nazwa, cmd, "Usunięcie pakietu RPM", [], cfg)

    if symulacja:
        cmd = ["apt-get", "-s", "remove", nazwa]
        return RemovalPlan(nazwa, cmd, "Symulacja usunięcia (nic nie zostanie zmienione)",
                           cmd, [], False)

    if konfiguracja:
        cmd = ["pkexec", "apt-get", "-y", "purge", nazwa]
    else:
        cmd = ["pkexec", "apt-get", "-y", "remove", nazwa]
    cfg = config_files(nazwa, distro) if konfiguracja else []
    plan = RemovalPlan(nazwa, cmd, "Usunięcie pakietu DEB", [], cfg)
    if zalezności:
        plan.description += " + automatyczne usunięcie nieużywanych zależności"
        plan.extra_files = ["AUTOREMOVE"]
    return plan


def sprawdz_czy_istnieje(pakiet: Package) -> bool:
    """Sprawdza, czy aplikacja naprawdę zniknęła z systemu po usunięciu."""
    nazwa = pakiet.name
    try:
        if pakiet.source == "flatpak":
            ident = id_flatpak(pakiet)
            wynik = subprocess.run(
                ["flatpak", "list", "--app", "--columns=application"],
                capture_output=True, text=True, errors="replace", timeout=60,
            )
            return any(ident == l.strip() for l in wynik.stdout.splitlines())
        if pakiet.source == "snap":
            wynik = subprocess.run(
                ["snap", "list"], capture_output=True, text=True,
                errors="replace", timeout=60,
            )
            return any(l.split() and l.split()[0] == nazwa
                       for l in wynik.stdout.splitlines()[1:])
        if pakiet.source == "pacman":
            return subprocess.run(
                ["pacman", "-Q", nazwa], capture_output=True, timeout=60
            ).returncode == 0
        if pakiet.source == "rpm":
            return subprocess.run(
                ["rpm", "-q", nazwa], capture_output=True, timeout=60
            ).returncode == 0
        if pakiet.source == "deb":
            return subprocess.run(
                ["dpkg", "-s", nazwa], capture_output=True, timeout=60
            ).returncode == 0
        if pakiet.source in ("desktop", "appimage"):
            return bool(pakiet.origin_path and os.path.exists(pakiet.origin_path))
    except Exception:
        return False
    return False


def _build_file_plan(pakiet: Package, symulacja: bool) -> RemovalPlan:
    pliki = []
    if pakiet.origin_path and os.path.exists(pakiet.origin_path):
        pliki.append(pakiet.origin_path)
        dom = os.path.expanduser("~")
        if pakiet.source == "desktop":
            # spróbuj znaleźć plik, który uruchamia skrót
            from .packages import _parse_desktop
            _, _, polecenie, _ = _parse_desktop(pakiet.origin_path)
            pierwsze = polecenie.split()[0] if polecenie else ""
            if pierwsze and not pierwsze.startswith("-"):
                kandydat = pierwsze if os.path.isabs(pierwsze) else shutil_which(pierwsze)
                if kandydat and os.path.isfile(kandydat):
                    real = os.path.realpath(kandydat)
                    if real.startswith(dom + os.sep) or real.startswith("/opt" + os.sep):
                        if real not in pliki:
                            pliki.append(real)
    root = any(not p.startswith(os.path.expanduser("~")) for p in pliki)
    cmd = ([
        "pkexec", "rm", "-rf", "--",
    ] + pliki) if (root and not symulacja) else (["rm", "-rf", "--"] + pliki)
    if symulacja:
        cmd = ["echo", "SIMULACJA: usunięto by: " + ", ".join(pliki)]
    return RemovalPlan(pakiet.name, cmd, "Usunięcie aplikacji spoza baz pakietów",
                       cmd, [], root, pliki)


def shutil_which(nazwa: str) -> str:
    from .detector import has_command
    import shutil
    return shutil.which(nazwa) or ""


def wykonaj(plan: RemovalPlan) -> tuple[bool, str]:
    """Wykonuje plan. Zwraca (powodzenie, pełny log)."""
    try:
        wynik = subprocess.run(
            plan.command, capture_output=True, text=True,
            errors="replace", timeout=600,
        )
        log = (wynik.stdout or "") + "\n" + (wynik.stderr or "")
        if wynik.returncode == 0:
            return True, log.strip()
        # Flatpak zainstalowany systemowo wymaga uprawnień — spróbuj drugiej metody
        if plan.alternatywa:
            log += "\n[RemApps] Próbuję z uprawnieniami administratora..."
            try:
                drugi = subprocess.run(
                    plan.alternatywa, capture_output=True, text=True,
                    errors="replace", timeout=600,
                )
                log += "\n" + (drugi.stdout or "") + "\n" + (drugi.stderr or "")
                if drugi.returncode == 0:
                    return True, log.strip()
            except Exception as exc:  # noqa: BLE001
                log += f"\n[RemApps] Druga próba nie udała się: {exc}"
        if "pkexec" in plan.command:
            log += ("\n[RemApps] Nie udało się uzyskać uprawnień administratora. "
                    "Sprawdź, czy pkexec (polkit) jest zainstalowany.")
        return False, log.strip()
    except FileNotFoundError:
        return False, "Nie znaleziono polecenia: " + plan.command[0]
    except subprocess.TimeoutExpired:
        return False, "Przekroczono czas oczekiwania na zakończenie operacji."
    except Exception as exc:  # noqa: BLE001
        return False, f"Nieoczekiwany błąd: {exc}"


def aftercare(plan: RemovalPlan, distro: DistroInfo, symulacja: bool) -> list[str]:
    """Dodatkowe czynności po usunięciu (konfiguracja, autoremove)."""
    wykonane = []
    if symulacja:
        return wykonane
    for sciezka in plan.config_files:
        try:
            if os.path.isdir(sciezka):
                continue
            os.remove(sciezka)
            wykonane.append(sciezka)
        except OSError:
            pass
    if "AUTOREMOVE" in plan.extra_files:
        cmd = (["pkexec", "apt-get", "-y", "autoremove"] if distro.family == "deb"
               else [distro.package_manager, "-y", "autoremove"])
        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            wykonane.append("autoremove")
        except Exception:
            pass
    return wykonane
