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


def fiches(annee: int) -> dict:
    """Fiches N, N−1, N+1 et N−2. Sans fiche ni classeur N, une fiche vide si la fiche N−1 existe (année en cours)."""
    f = {"n": fiche.lire(annee), "prec": fiche.lire(annee - 1), "suiv": fiche.lire(annee + 1),
         "prec2": fiche.lire(annee - 2)}
    if f["n"] is None and f["prec"] is not None and lecture_paie.trouver_classeur(annee) is None:
        f["n"] = fiche.vide()
    return f


def generer(annee: int) -> tuple[Path, dict]:
    """Écrit l'Excel de réconciliation de l'exercice à partir des fiches N−2, N−1, N et N+1."""
    if fiche.lire(annee) is None and lecture_paie.trouver_classeur(annee) is not None:
        lire_classeur(annee)
    f = fiches(annee)
    if f["n"] is None:
        raise ClasseurAbsent(f"Aucune fiche ni classeur de paie {annee} : dépose ton classeur de paie "
                             f"dans {config.DOSSIER_SALAIRES}.")
    chemin = reconciliation.ecrire(annee, f["n"], f["prec"], f["suiv"], f["prec2"])
    return chemin, reconciliation.resume(annee, f["n"], f["prec"], f["suiv"], f["prec2"])


def exercices_disponibles() -> list[int]:
    """Exercices pour lesquels une fiche ou un classeur de paie existe, plus l'année qui suit la dernière fiche."""
    annees, fiches_lues = set(), set()
    if config.DOSSIER_FICHES_SALAIRES.is_dir():
        for f in config.DOSSIER_FICHES_SALAIRES.glob("fiche_salaires_*.xlsx"):
            m = re.search(r"(\d{4})", f.stem)
            if m:
                fiches_lues.add(int(m.group(1)))
    annees |= fiches_lues
    if config.DOSSIER_SALAIRES.is_dir():
        for f in config.DOSSIER_SALAIRES.glob("*.xlsx"):
            if not f.name.startswith("~$"):
                a = lecture_paie.exercice_du_classeur(f)
                if a:
                    annees.add(a)
    if fiches_lues:
        annees.add(max(fiches_lues) + 1)
    return sorted(annees)
