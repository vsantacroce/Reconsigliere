"""Lanceur installé de Reconsigliere : met à jour le programme depuis GitHub, puis ouvre la fenêtre.

Ce fichier est copié par installer.ps1 dans %LOCALAPPDATA%\\Reconsigliere et lancé par l'icône du bureau.
À chaque ouverture :
1. il demande à GitHub le dernier commit de la branche suivie (main par défaut) ;
2. s'il est plus récent que la version installée, il télécharge le code et remplace le dossier app ;
3. il réinstalle les bibliothèques si requirements.txt a changé ;
4. il ouvre la fenêtre.

Sans internet ou en cas d'erreur, la version déjà installée s'ouvre. Le dossier de données
(Documents\\Reconsigliere par défaut) n'est jamais touché.
"""

from __future__ import annotations

import io
import os
import shutil
import subprocess
import sys
import time
import traceback
import urllib.request
import zipfile
from pathlib import Path

DEPOT = "vsantacroce/reconsigliere"
DELAI_RESEAU = 5  # secondes


def dossier_base() -> Path:
    if os.environ.get("RECONSIGLIERE_BASE"):
        return Path(os.environ["RECONSIGLIERE_BASE"])
    if sys.platform.startswith("win"):
        return Path(os.environ.get("LOCALAPPDATA", Path.home())) / "Reconsigliere"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "Reconsigliere"


BASE = dossier_base()
APP = BASE / "app"
FICHIER_VERSION = BASE / "version.txt"
FICHIER_BRANCHE = BASE / "branche.txt"
JOURNAL = BASE / "journal.txt"


def journaliser(texte: str) -> None:
    try:
        BASE.mkdir(parents=True, exist_ok=True)
        with JOURNAL.open("a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + texte.rstrip() + "\n")
    except OSError:
        pass


def lire(chemin: Path, defaut: str = "") -> str:
    try:
        return chemin.read_text(encoding="utf-8").strip()
    except OSError:
        return defaut


def requete(url: str, accept: str | None = None) -> bytes:
    entetes = {"User-Agent": "Reconsigliere-updater"}
    if accept:
        entetes["Accept"] = accept
    with urllib.request.urlopen(urllib.request.Request(url, headers=entetes), timeout=DELAI_RESEAU * 6) as r:
        return r.read()


def dernier_commit(branche: str) -> str:
    url = f"https://api.github.com/repos/{DEPOT}/commits/{urllib.request.quote(branche, safe='')}"
    with urllib.request.urlopen(urllib.request.Request(
            url, headers={"User-Agent": "Reconsigliere-updater", "Accept": "application/vnd.github.sha"}),
            timeout=DELAI_RESEAU) as r:
        return r.read().decode().strip()


def python_console() -> str:
    """pythonw.exe n'a pas de sortie : pip doit tourner avec python.exe, dans le même dossier."""
    exe = Path(sys.executable)
    if exe.name.lower() == "pythonw.exe" and (exe.parent / "python.exe").exists():
        return str(exe.parent / "python.exe")
    return sys.executable


def installer_bibliotheques(requirements: Path) -> None:
    marqueur = BASE / "requirements.installe"
    if requirements.exists() and lire(marqueur) == requirements.read_text(encoding="utf-8").strip():
        return
    subprocess.run([python_console(), "-m", "pip", "install", "-q", "--disable-pip-version-check",
                    "-r", str(requirements)],
                   check=True, capture_output=True, timeout=600,
                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    shutil.copyfile(requirements, marqueur)


def mettre_a_jour(sha: str, afficher) -> None:
    afficher("Téléchargement de la nouvelle version…")
    contenu = requete(f"https://codeload.github.com/{DEPOT}/zip/{sha}")
    temporaire = BASE / "app.nouveau"
    ancien = BASE / "app.ancien"
    for d in (temporaire, ancien):
        shutil.rmtree(d, ignore_errors=True)
    with zipfile.ZipFile(io.BytesIO(contenu)) as z:
        z.extractall(temporaire)
    racines = [p for p in temporaire.iterdir() if p.is_dir()]
    if len(racines) != 1 or not (racines[0] / "src" / "reconsigliere").is_dir():
        raise RuntimeError("archive inattendue")
    afficher("Installation des bibliothèques…")
    installer_bibliotheques(racines[0] / "requirements.txt")
    if APP.exists():
        APP.rename(ancien)
    racines[0].rename(APP)
    shutil.rmtree(temporaire, ignore_errors=True)
    shutil.rmtree(ancien, ignore_errors=True)
    FICHIER_VERSION.write_text(sha, encoding="utf-8")
    journaliser(f"mise à jour vers {sha}")
    # Le lanceur se met lui-même à jour pour la prochaine ouverture.
    nouveau_lanceur = APP / "windows" / "demarrer.pyw"
    try:
        ici = Path(__file__).resolve()
        if nouveau_lanceur.exists() and nouveau_lanceur.read_bytes() != ici.read_bytes():
            shutil.copyfile(nouveau_lanceur, ici)
    except OSError:
        pass


class Ecran:
    """Petite fenêtre « Mise à jour… », créée seulement si une mise à jour a lieu."""

    def __init__(self) -> None:
        self.tk = None
        self.label = None

    def afficher(self, texte: str) -> None:
        try:
            import tkinter as tk
            if self.tk is None:
                self.tk = tk.Tk()
                self.tk.title("Reconsigliere")
                self.tk.resizable(False, False)
                self.label = tk.Label(self.tk, padx=32, pady=24, font=("Segoe UI", 11))
                self.label.pack()
                self.tk.update_idletasks()
                x = (self.tk.winfo_screenwidth() - 360) // 2
                y = (self.tk.winfo_screenheight() - 100) // 2
                self.tk.geometry(f"360x100+{x}+{y}")
            self.label.configure(text=texte)
            self.tk.update()
        except Exception:  # noqa: BLE001 - l'écran est un confort, jamais un blocage
            pass

    def fermer(self) -> None:
        if self.tk is not None:
            try:
                self.tk.destroy()
            except Exception:  # noqa: BLE001
                pass
            self.tk = None


def verifier_mise_a_jour() -> None:
    if os.environ.get("RECONSIGLIERE_SANS_MISE_A_JOUR"):
        return
    branche = lire(FICHIER_BRANCHE, "main") or "main"
    ecran = Ecran()
    try:
        sha = dernier_commit(branche)
        if sha and sha != lire(FICHIER_VERSION):
            ecran.afficher("Mise à jour de Reconsigliere…")
            mettre_a_jour(sha, ecran.afficher)
    except Exception:  # noqa: BLE001 - hors ligne ou GitHub indisponible : on ouvre la version installée
        journaliser("mise à jour impossible :\n" + traceback.format_exc())
    finally:
        ecran.fermer()


def ouvrir() -> None:
    if not (APP / "src" / "reconsigliere").is_dir():
        import tkinter.messagebox as mb
        mb.showerror("Reconsigliere", "Le programme n'est pas installé et la mise à jour a échoué.\n"
                                      f"Vérifie la connexion internet, puis relance.\n\nDétails : {JOURNAL}")
        return
    sys.path.insert(0, str(APP / "src"))
    os.environ["RECONSIGLIERE_COMMIT"] = lire(FICHIER_VERSION)[:7]
    from reconsigliere import fenetre
    fenetre.lancer()


if __name__ == "__main__":
    verifier_mise_a_jour()
    try:
        ouvrir()
    except Exception:  # noqa: BLE001
        journaliser("erreur au lancement :\n" + traceback.format_exc())
        raise
