"""Réconciliation des salaires par exercice et par employé (voir docs/modules/salaires).

Classeur de paie (entrees/08_salaires) → fiche de l'exercice (entrees/08_salaires/fiches) → Excel de réconciliation
(sorties/salaires).
"""

from __future__ import annotations

import re
from pathlib import Path

from .. import config
from . import fiche, lecture_paie, reconciliation
from .fiche import FichierOuvert  # noqa: F401 - réexporté pour la fenêtre
from .lecture_paie import FormatInconnu  # noqa: F401 - réexporté pour la fenêtre


class ClasseurAbsent(Exception):
    """Ni classeur de paie ni fiche pour l'exercice demandé."""


def lire_classeur(annee: int) -> dict:
    """Lit le classeur de paie de l'exercice et met la fiche à jour. Rend le bilan de la fusion."""
    chemin = lecture_paie.trouver_classeur(annee)
    if chemin is None:
        raise ClasseurAbsent(f"Aucun classeur de paie {annee} dans {config.DOSSIER_SALAIRES} "
                             f"(l'exercice est lu dans la cellule B1 de l'onglet ANNEE).")
    lu = lecture_paie.lire(chemin)
    nouvelle = {"du": lu["du"], "virements": lu["virements"], "points": []}
    nouvelle["auto"] = fiche.valeurs_auto(nouvelle)
    resultat, bilan = fiche.fusionner(fiche.lire(annee), nouvelle)
    fiche.ecrire(annee, resultat)
    bilan.update({"classeur": chemin, "fiche": fiche.chemin_fiche(annee), "controles": lu["controles"]})
    return bilan


def generer(annee: int) -> tuple[Path, dict]:
    """Écrit l'Excel de réconciliation de l'exercice à partir des fiches N−1, N et N+1."""
    fiche_n = fiche.lire(annee)
    if fiche_n is None:
        if lecture_paie.trouver_classeur(annee) is None:
            raise ClasseurAbsent(f"Aucune fiche ni classeur de paie {annee} : dépose ton classeur de paie "
                                 f"dans {config.DOSSIER_SALAIRES}.")
        lire_classeur(annee)
        fiche_n = fiche.lire(annee)
    prec, suiv = fiche.lire(annee - 1), fiche.lire(annee + 1)
    chemin = reconciliation.ecrire(annee, fiche_n, prec, suiv)
    return chemin, reconciliation.resume(annee, fiche_n, prec, suiv)


def exercices_disponibles() -> list[int]:
    """Exercices pour lesquels une fiche ou un classeur de paie existe."""
    annees = set()
    if config.DOSSIER_FICHES_SALAIRES.is_dir():
        for f in config.DOSSIER_FICHES_SALAIRES.glob("fiche_salaires_*.xlsx"):
            m = re.search(r"(\d{4})", f.stem)
            if m:
                annees.add(int(m.group(1)))
    if config.DOSSIER_SALAIRES.is_dir():
        for f in config.DOSSIER_SALAIRES.glob("*.xlsx"):
            if not f.name.startswith("~$"):
                a = lecture_paie.exercice_du_classeur(f)
                if a:
                    annees.add(a)
    return sorted(annees)
