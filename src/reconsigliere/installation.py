"""Dossier de travail : création des dossiers, mémorisation du choix, ouverture dans l'explorateur."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

NOM_PAR_DEFAUT = "Reconsigliere"

# (chemin relatif, titre court affiché dans la fenêtre, contenu du LISEZMOI)
DOSSIERS = [
    ("entrees/01_factures", "Factures et reçus",
     "Dépose ici toutes tes factures, reçus et notes de frais, en vrac.\n"
     "Formats acceptés : PDF, PNG, JPG. Les sous-dossiers sont lus aussi.\n\n"
     "Les images et les scans ne sont lus automatiquement que si Tesseract OCR est installé.\n"
     "Sans lui, ils sont quand même renommés, mais il faut les lier à la main dans mes_corrections.xlsx.\n"),
    ("entrees/02_transactions_a_reconcilier", "Transactions bancaires",
     "Dépose ici les Excel (.xlsx, .xls) ou CSV des transactions bancaires à réconcilier.\n"
     "Colonnes attendues : date, montant (ou débit/crédit), libellé. IBAN, référence et partenaire sont optionnels.\n"),
    ("entrees/03_infos_bancaires", "Relevés détaillés",
     "Dépose ici les relevés et les Excel qui détaillent les transactions (libellé complet, IBAN, référence, partenaire).\n"
     "Ils sont rapprochés des transactions par date et montant pour les enrichir.\n"),
    ("entrees/04_comptabilite", "Comptabilité",
     "Dépose ici la liste Excel des pièces de ta comptabilité (colonnes : fichier, partenaire, date, montant, statut).\n"
     "Mets les PDF déjà comptabilisés dans le sous-dossier pdf.\n"),
    ("entrees/04_comptabilite/pdf", None,
     "Mets ici les PDF déjà présents dans ta comptabilité.\n"),
    ("entrees/05_mes_corrections", "Mes corrections",
     "Le fichier mes_corrections.xlsx est créé au premier lancement. Tu le modifies pour corriger l'outil :\n\n"
     "- Feuille partenaires : un mot du libellé bancaire et le nom de partenaire à utiliser.\n"
     "- Feuille transactions : pour un id de transaction, le partenaire, le PDF à lier, une explication ou un statut forcé.\n\n"
     "Tes corrections passent toujours avant le rapprochement automatique.\n"),
    ("entrees/06_societe", "Société (brevets, projets, revenus)",
     "Dépose ici ton classeur des brevets (liste des brevets et onglets de coûts, tel que tu le tiens déjà).\n"
     "Reconsigliere reconnaît les colonnes ID, Title/Titre, Patent number, Filing date, Approved date, Abandon date,\n"
     "Patent owner, puis pour les coûts : Brevet, Classification (Capitalisable/Charge), Montant HT CHF, Date facture.\n\n"
     "Le classeur societe.xlsx est créé au premier lancement : tiens-y les onglets Projets, Revenus et Journal.\n"
     "L'onglet Société de la fenêtre et la page sorties/societe.html montrent l'état de la société.\n"),
    ("sorties", "Résultats",
     "Recréé à chaque lancement : reconciliation.xlsx, reconciliation.html, pdf_renommes et a_comptabiliser.\n"
     "societe.html est recréé par le bouton « Tableau de bord » de l'onglet Société.\n"),
]

EXTENSIONS_UTILES = {".pdf", ".png", ".jpg", ".jpeg", ".xlsx", ".xlsm", ".xls", ".csv"}


# ---------------------------------------------------------------- dossier de travail

def resoudre(choix: Path) -> Path:
    """Le dossier choisi par l'utilisateur devient le dossier de travail s'il en est déjà un
    (il contient entrees) ou s'il s'appelle Reconsigliere. Sinon on crée Reconsigliere dedans."""
    choix = Path(choix).expanduser().resolve()
    if (choix / "entrees").is_dir() or choix.name.lower() == NOM_PAR_DEFAUT.lower():
        return choix
    return choix / NOM_PAR_DEFAUT


def est_installe(racine: Path) -> bool:
    return all((Path(racine) / rel).is_dir() for rel, _, _ in DOSSIERS)


def creer_dossiers(racine: Path) -> list[Path]:
    """Crée les dossiers manquants et leur LISEZMOI. Ne touche jamais aux fichiers existants."""
    crees = []
    for rel, _, texte in DOSSIERS:
        dossier = Path(racine) / rel
        if not dossier.exists():
            crees.append(dossier)
        dossier.mkdir(parents=True, exist_ok=True)
        lisezmoi = dossier / "LISEZMOI.md"
        if not lisezmoi.exists():
            lisezmoi.write_text(f"# {dossier.name}\n\n{texte}", encoding="utf-8")
    return crees


def compter_fichiers(dossier: Path) -> int:
    if not dossier.exists():
        return 0
    return sum(1 for p in dossier.rglob("*")
               if p.is_file() and p.suffix.lower() in EXTENSIONS_UTILES and not p.name.startswith("~$"))


# ---------------------------------------------------------------- mémorisation

def _fichier_reglages() -> Path:
    if sys.platform.startswith("win"):
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / NOM_PAR_DEFAUT / "reglages.json"


def dossier_memorise() -> Path | None:
    try:
        donnees = json.loads(_fichier_reglages().read_text(encoding="utf-8"))
        chemin = Path(donnees.get("dossier_travail", ""))
        return chemin if str(chemin) not in ("", ".") else None
    except (OSError, ValueError):
        return None


def memoriser(racine: Path) -> None:
    fichier = _fichier_reglages()
    fichier.parent.mkdir(parents=True, exist_ok=True)
    fichier.write_text(json.dumps({"dossier_travail": str(racine)}, ensure_ascii=False, indent=2),
                       encoding="utf-8")


def dossier_propose() -> Path:
    documents = Path.home() / "Documents"
    return (documents if documents.is_dir() else Path.home()) / NOM_PAR_DEFAUT


# ---------------------------------------------------------------- ouverture

def ouvrir(chemin: Path) -> None:
    """Ouvre un dossier dans l'explorateur ou un fichier avec son programme habituel."""
    chemin = str(chemin)
    if sys.platform.startswith("win"):
        os.startfile(chemin)  # noqa: S606
    elif sys.platform == "darwin":
        subprocess.Popen(["open", chemin])
    else:
        subprocess.Popen(["xdg-open", chemin], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
