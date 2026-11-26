"""Fichier mes_corrections.xlsx : c'est là que tu fais avancer la réconciliation."""

from __future__ import annotations

import pandas as pd

from . import config
from .outils import normaliser

COLONNES_PARTENAIRES = ["mot_dans_libelle", "partenaire"]
COLONNES_TRANSACTIONS = ["id_transaction", "date", "montant", "libelle",
                         "partenaire", "pdf", "explication", "statut_force"]


def creer_modele_si_absent() -> None:
    if config.FICHIER_CORRECTIONS.exists():
        return
    config.FICHIER_CORRECTIONS.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(config.FICHIER_CORRECTIONS, engine="openpyxl") as w:
        pd.DataFrame([{"mot_dans_libelle": "exemple: SWISSCOM", "partenaire": "Swisscom"}],
                     columns=COLONNES_PARTENAIRES).to_excel(w, sheet_name="partenaires", index=False)
        pd.DataFrame(columns=COLONNES_TRANSACTIONS).to_excel(w, sheet_name="transactions", index=False)
        pd.DataFrame({"aide": [
            "Feuille partenaires : si le libellé bancaire contient le mot, ce partenaire est utilisé.",
            "Feuille transactions : copie l'id_transaction depuis sorties/reconciliation.xlsx.",
            "partenaire : remplace le nom trouvé automatiquement.",
            "pdf : nom du fichier d'origine (PDF ou image) à lier de force, tel qu'il est dans entrees/01_factures.",
            "explication : ton commentaire, par exemple frais bancaires ou salaire.",
            "statut_force : Comptabilise, Sans piece, A comptabiliser ou Ignorer.",
        ]}).to_excel(w, sheet_name="aide", index=False)


def _feuille(nom: str) -> pd.DataFrame:
    try:
        return pd.read_excel(config.FICHIER_CORRECTIONS, sheet_name=nom).fillna("")
    except (FileNotFoundError, ValueError):
        return pd.DataFrame()


def charger() -> dict:
    regles = []
    for _, l in _feuille("partenaires").iterrows():
        mot = normaliser(l.get("mot_dans_libelle", ""))
        if mot and not mot.startswith("exemple"):
            regles.append((mot, str(l.get("partenaire", "")).strip()))
    par_transaction = {}
    for _, l in _feuille("transactions").iterrows():
        tid = str(l.get("id_transaction", "")).strip()
        if tid:
            par_transaction[tid] = {k: str(l.get(k, "")).strip() for k in
                                    ("partenaire", "pdf", "explication", "statut_force")}
    return {"regles_partenaires": regles, "transactions": par_transaction}
