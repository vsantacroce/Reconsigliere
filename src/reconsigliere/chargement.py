"""Lecture des Excel et CSV des dossiers d'entrée."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

from . import config
from .outils import en_date, en_montant, normaliser

EXTENSIONS_TABLEUR = {".xlsx", ".xlsm", ".xls", ".csv"}


def lister_tableurs(dossier: Path) -> list[Path]:
    if not dossier.exists():
        return []
    return sorted(p for p in dossier.rglob("*")
                  if p.suffix.lower() in EXTENSIONS_TABLEUR and not p.name.startswith("~$"))


def lire_tableur(chemin: Path) -> list[pd.DataFrame]:
    """Renvoie une table par feuille."""
    if chemin.suffix.lower() == ".csv":
        for sep in (";", ",", "\t"):
            try:
                df = pd.read_csv(chemin, sep=sep, encoding="utf-8-sig")
            except UnicodeDecodeError:
                df = pd.read_csv(chemin, sep=sep, encoding="latin-1")
            if df.shape[1] > 1:
                return [df]
        return [df]
    feuilles = pd.read_excel(chemin, sheet_name=None)
    return [df for df in feuilles.values() if not df.empty]


def _trouver_ligne_entete(df: pd.DataFrame) -> pd.DataFrame:
    """Certains relevés ont des lignes de titre avant l'en-tête : on cherche la vraie ligne."""
    connus = {a for alias in config.ALIAS_COLONNES.values() for a in alias}
    if sum(normaliser(c) in connus for c in df.columns) >= 2:
        return df
    for i in range(min(20, len(df))):
        valeurs = [normaliser(v) for v in df.iloc[i].tolist()]
        if sum(v in connus for v in valeurs) >= 2:
            nouveau = df.iloc[i + 1:].copy()
            nouveau.columns = df.iloc[i].tolist()
            return nouveau.reset_index(drop=True)
    return df


def associer_colonnes(df: pd.DataFrame) -> dict[str, str]:
    """Associe chaque champ connu (date, montant...) à une colonne du tableau."""
    trouvees: dict[str, str] = {}
    for champ, alias in config.ALIAS_COLONNES.items():
        alias_norm = [normaliser(a) for a in alias]
        for col in df.columns:
            if normaliser(col) in alias_norm and col not in trouvees.values():
                trouvees[champ] = col
                break
        if champ not in trouvees:
            for col in df.columns:
                n = normaliser(col)
                if any(a in n for a in alias_norm) and col not in trouvees.values():
                    trouvees[champ] = col
                    break
    return trouvees


def _texte(ligne, col):
    if not col:
        return ""
    v = ligne.get(col)
    return "" if v is None or (isinstance(v, float) and pd.isna(v)) else str(v).strip()


def identifiant_transaction(d, montant, libelle) -> str:
    cle = f"{d}|{montant}|{normaliser(libelle)}"
    return "T" + hashlib.sha1(cle.encode("utf-8")).hexdigest()[:8].upper()


def charger_lignes(dossier: Path) -> list[dict]:
    """Lit tous les tableurs d'un dossier et renvoie des lignes normalisées."""
    lignes: list[dict] = []
    for chemin in lister_tableurs(dossier):
        for df in lire_tableur(chemin):
            df = _trouver_ligne_entete(df)
            cols = associer_colonnes(df)
            for _, ligne in df.iterrows():
                montant = en_montant(ligne.get(cols["montant"])) if "montant" in cols else None
                if montant is None and ("debit" in cols or "credit" in cols):
                    debit = en_montant(ligne.get(cols.get("debit"))) if "debit" in cols else None
                    credit = en_montant(ligne.get(cols.get("credit"))) if "credit" in cols else None
                    if debit:
                        montant = -abs(debit)
                    elif credit:
                        montant = abs(credit)
                lignes.append({
                    "date": en_date(ligne.get(cols["date"])) if "date" in cols else None,
                    "montant": montant,
                    "libelle": _texte(ligne, cols.get("libelle")),
                    "iban": _texte(ligne, cols.get("iban")).replace(" ", "").upper(),
                    "reference": _texte(ligne, cols.get("reference")),
                    "partenaire": _texte(ligne, cols.get("partenaire")),
                    "fichier": _texte(ligne, cols.get("fichier")),
                    "statut": _texte(ligne, cols.get("statut")),
                    "source": chemin.name,
                })
    return lignes


def charger_transactions() -> list[dict]:
    transactions = []
    vus = set()
    for l in charger_lignes(config.DOSSIER_TRANSACTIONS):
        if l["date"] is None or l["montant"] is None:
            continue
        tid = identifiant_transaction(l["date"], l["montant"], l["libelle"])
        if tid in vus:
            continue
        vus.add(tid)
        l["id"] = tid
        transactions.append(l)
    return sorted(transactions, key=lambda t: (t["date"], t["montant"]))


def enrichir_avec_infos_bancaires(transactions: list[dict]) -> None:
    """Complète libellé, IBAN, référence et partenaire à partir du dossier 03."""
    infos = [l for l in charger_lignes(config.DOSSIER_INFOS_BANCAIRES)
             if l["date"] is not None and l["montant"] is not None]
    for t in transactions:
        candidates = [i for i in infos
                      if abs(i["montant"] - t["montant"]) <= config.TOLERANCE_MONTANT
                      and abs((i["date"] - t["date"]).days) <= 3]
        if len(candidates) != 1:
            continue
        info = candidates[0]
        for champ in ("iban", "reference", "partenaire"):
            if not t[champ] and info[champ]:
                t[champ] = info[champ]
        if info["libelle"] and normaliser(info["libelle"]) not in normaliser(t["libelle"]):
            t["libelle"] = (t["libelle"] + " | " + info["libelle"]).strip(" |")


def charger_comptabilite() -> list[dict]:
    return charger_lignes(config.DOSSIER_COMPTABILITE)
