"""Fichier mes_corrections.xlsx : c'est là que tu fais avancer la réconciliation."""

from __future__ import annotations

from datetime import date

import openpyxl
import pandas as pd

from . import config
from .outils import code_compte, normaliser

COLONNES_PARTENAIRES = ["mot_dans_libelle", "partenaire"]
COLONNES_TRANSACTIONS = ["id_transaction", "date", "montant", "libelle",
                         "partenaire", "pdf", "explication", "statut_force", "compte"]
# Règles apprises que tu as annulées (voir apprentissage.py) : une ligne = une règle mise de côté.
FEUILLE_REGLES = "regles_apprises"
COLONNES_REGLES = ["partenaire", "compte", "decision", "le"]
ANNULEE = "annulée"


def creer_modele_si_absent() -> None:
    if config.FICHIER_CORRECTIONS.exists():
        return
    config.FICHIER_CORRECTIONS.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(config.FICHIER_CORRECTIONS, engine="openpyxl") as w:
        pd.DataFrame([{"mot_dans_libelle": "exemple: SWISSCOM", "partenaire": "Swisscom"}],
                     columns=COLONNES_PARTENAIRES).to_excel(w, sheet_name="partenaires", index=False)
        pd.DataFrame(columns=COLONNES_TRANSACTIONS).to_excel(w, sheet_name="transactions", index=False)
        pd.DataFrame(columns=COLONNES_REGLES).to_excel(w, sheet_name=FEUILLE_REGLES, index=False)
        pd.DataFrame({"aide": [
            "Feuille partenaires : si le libellé bancaire contient le mot, ce partenaire est utilisé.",
            "Feuille transactions : copie l'id_transaction depuis sorties/reconciliation.xlsx.",
            "partenaire : remplace le nom trouvé automatiquement.",
            "pdf : nom du fichier d'origine (PDF ou image) à lier de force, tel qu'il est dans entrees/01_factures.",
            "explication : ton commentaire, par exemple frais bancaires ou salaire.",
            "statut_force : Comptabilise, Sans piece, A comptabiliser ou Ignorer.",
            "compte : le bon compte pour cette transaction (ex. 6600). Après 3 corrections identiques pour un "
            "partenaire, le programme applique seul ce compte aux transactions suivantes (onglet Apprentissage).",
            "Feuille regles_apprises : les règles apprises que tu as annulées. Supprime la ligne pour rétablir la règle.",
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
            par_transaction[tid]["compte"] = code_compte(l.get("compte", ""))
    annulees = set()
    for _, l in _feuille(FEUILLE_REGLES).iterrows():
        if normaliser(l.get("decision", "")) == normaliser(ANNULEE):
            annulees.add((normaliser(l.get("partenaire", "")), code_compte(l.get("compte", ""))))
    return {"regles_partenaires": regles, "transactions": par_transaction, "annulees": annulees}


def _classeur_regles():
    """Ouvre mes_corrections.xlsx (créé au besoin) et rend (classeur, feuille regles_apprises)."""
    creer_modele_si_absent()
    wb = openpyxl.load_workbook(config.FICHIER_CORRECTIONS)
    if FEUILLE_REGLES not in wb.sheetnames:
        wb.create_sheet(FEUILLE_REGLES).append(COLONNES_REGLES)
    return wb, wb[FEUILLE_REGLES]


def _meme_regle(ws, ligne, partenaire: str, compte: str) -> bool:
    entete = [c.value for c in ws[1]]
    valeurs = dict(zip(entete, ligne))
    return (normaliser(valeurs.get("partenaire")) == normaliser(partenaire)
            and code_compte(valeurs.get("compte")) == code_compte(compte))


def annuler_regle(partenaire: str, compte: str) -> None:
    """Met de côté une règle apprise. Lève PermissionError si le fichier est ouvert dans Excel."""
    wb, ws = _classeur_regles()
    if not any(_meme_regle(ws, l, partenaire, compte) for l in ws.iter_rows(min_row=2, values_only=True)):
        entete = [c.value for c in ws[1]]
        valeurs = {"partenaire": partenaire, "compte": code_compte(compte), "decision": ANNULEE,
                   "le": date.today().strftime("%d.%m.%Y")}
        ws.append([valeurs.get(c, "") for c in entete])
    wb.save(config.FICHIER_CORRECTIONS)


def retablir_regle(partenaire: str, compte: str) -> None:
    """Retire la ligne d'annulation : la règle s'applique de nouveau au prochain lancement."""
    wb, ws = _classeur_regles()
    for i in range(ws.max_row, 1, -1):
        if _meme_regle(ws, [c.value for c in ws[i]], partenaire, compte):
            ws.delete_rows(i)
    wb.save(config.FICHIER_CORRECTIONS)
