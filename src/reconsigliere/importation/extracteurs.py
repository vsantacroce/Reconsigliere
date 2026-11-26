"""Extracteurs spécialisés : une section typée devient des lignes normalisées.

Format convenu avec l'Assistant société : code/compte en texte, débit et crédit positifs
ou vides, partenaire vide si absent, bilan et compte de résultat gardent le signe du document.
"""

from __future__ import annotations

import re

import pandas as pd

from ..outils import en_date, en_montant, normaliser
from .classement import RE_DATE, titre
from .continuite import Section
from .pages import Page

CLES = ("plancomptable", "grandlivre", "bilan", "compteresultat", "annexe")

RE_MONTANT_FIN = re.compile(r"(\(?-?\d{1,3}(?:['’]\d{3})*[.,]\d{2}\)?|\(?-?\d+[.,]\d{2}\)?)\s*$")
RE_CODE = re.compile(r"^(\d{3,8})\s+(.*)$")
RE_DATE_DEBUT = re.compile(r"^(\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{4}-\d{2}-\d{2})\s+(.*)$")
RE_PIECE = re.compile(r"^(?=.*\d)(?=.*[A-Za-z/\-])[A-Za-z0-9][A-Za-z0-9/\-_.]{3,}$")
MOTS_IGNORES = ("report", "a reporter", "total", "solde", "sous-total", "uebertrag")
MOTS_NIVEAU_1 = ("actif", "actifs", "passif", "passifs", "produits", "charges", "revenus",
                 "assets", "liabilities", "aktiven", "passiven", "ertrag", "aufwand")
TYPES_ODOO = ["Banque et espèces", "Recevable", "Payable", "Actifs circulants", "Actifs non-circulants",
              "Immobilisations", "Prépaiements", "Passifs circulants", "Passifs non-circulants",
              "Capitaux propres", "Résultat de l'exercice", "Revenus", "Autres revenus", "Charges",
              "Amortissements", "Coût des revenus", "Hors bilan", "Carte de crédit",
              "Bank and Cash", "Receivable", "Current Assets", "Non-current Assets", "Fixed Assets",
              "Prepayments", "Current Liabilities", "Non-current Liabilities", "Equity",
              "Current Year Earnings", "Income", "Other Income", "Expenses", "Depreciation",
              "Cost of Revenue", "Off-Balance Sheet", "Credit Card"]

SYNONYMES = {
    "date": ["date", "date comptable", "date ecriture", "date de l'ecriture", "datum"],
    "compte": ["compte", "n compte", "no compte", "numero de compte", "compte comptable", "account",
               "code", "numero", "no", "konto"],
    "libelle_compte": ["nom du compte", "intitule du compte", "libelle du compte", "account name"],
    "piece": ["piece", "ecriture", "n piece", "no piece", "numero de piece", "journal entry", "entry",
              "move", "reference", "ref", "beleg"],
    "partenaire": ["partenaire", "partner", "tiers", "client/fournisseur", "contrepartie"],
    "libelle": ["libelle", "label", "description", "texte", "communication", "intitule", "text"],
    "nom": ["nom", "nom du compte", "intitule", "intitule du compte", "libelle", "name", "account name",
            "bezeichnung"],
    "type": ["type", "type de compte", "account type", "kontotyp"],
    "debit": ["debit", "soll"],
    "credit": ["credit", "haben"],
    "montant": ["montant", "amount", "betrag", "montant chf"],
}


# ------------------------------------------------------------------ utilitaires

def _source(fichier: str, page: Page) -> str:
    return f"{fichier} p.{page.numero}" + (f" ({page.nom_feuille})" if page.nom_feuille else "")


def _texte(valeur) -> str:
    if valeur is None or (isinstance(valeur, float) and pd.isna(valeur)):
        return ""
    return str(valeur).strip()


def _montant(texte: str) -> float | None:
    t = texte.strip()
    negatif = t.startswith("(") and t.endswith(")")
    m = en_montant(t.strip("()"))
    if m is None:
        return None
    return -abs(m) if negatif else m


def _montants_en_fin(ligne: str, maximum: int = 3) -> tuple[str, list[float]]:
    montants: list[float] = []
    reste = ligne.rstrip()
    while len(montants) < maximum:
        m = RE_MONTANT_FIN.search(reste)
        if not m or (m.start() > 0 and not reste[m.start() - 1].isspace()):
            break
        montants.insert(0, _montant(m.group(1)))
        reste = reste[:m.start()].rstrip()
    return reste, montants


def _sans_zero(x: float | None) -> float | None:
    return None if x is None or abs(x) < 0.005 else abs(x)


def _date_iso(texte: str) -> str:
    d = en_date(texte)
    return d.isoformat() if d else ""


def _associer(colonnes: list[str], champs: list[str]) -> dict[str, str]:
    """Associe chaque champ voulu à une colonne : correspondance exacte d'abord, puis préfixe."""
    norm = {c: normaliser(c).replace("°", "").replace(".", "").strip() for c in colonnes}
    pris: dict[str, str] = {}
    for strict in (True, False):
        for champ in champs:
            if champ in pris:
                continue
            for syn in SYNONYMES[champ]:
                trouve = next((c for c, n in norm.items() if c not in pris.values()
                               and (n == syn if strict else n.startswith(syn + " ") or n.startswith(syn))), None)
                if trouve:
                    pris[champ] = trouve
                    break
    return pris


def _partenaire(texte: str) -> str:
    return "" if texte.strip() in {"", "/", "-", "—", "nan", "None"} else texte.strip()


# ------------------------------------------------------------------ plan comptable

def _plan(section: Section, exercice: int, fichier: str) -> list[dict]:
    res = []
    for page in section.pages:
        src = _source(fichier, page)
        if page.tableau is not None:
            cols = _associer(list(page.tableau.columns), ["compte", "nom", "type"])
            for _, r in page.tableau.iterrows():
                code = _texte(r.get(cols.get("compte")))
                nom = _texte(r.get(cols.get("nom")))
                m = RE_CODE.match(code)
                if m and not nom:
                    code, nom = m.group(1), m.group(2)
                if code:
                    res.append({"code": code, "nom": nom, "type": _texte(r.get(cols.get("type"))),
                                "exercice": exercice, "source": src})
            continue
        for ligne in page.texte.splitlines():
            m = RE_CODE.match(ligne.strip())
            if not m or _montants_en_fin(ligne)[1]:
                continue
            code, reste, type_ = m.group(1), m.group(2).strip(), ""
            for t in sorted(TYPES_ODOO, key=len, reverse=True):
                if normaliser(reste).endswith(normaliser(t)) and len(reste) > len(t):
                    type_, reste = t, reste[:-len(t)].strip()
                    break
            res.append({"code": code, "nom": reste, "type": type_, "exercice": exercice, "source": src})
    return res


# ------------------------------------------------------------------ grand livre

def _ligne_gl(compte, libelle_compte, date, piece, partenaire, libelle, debit, credit, exercice, src):
    return {"date": date, "compte": compte, "libelle_compte": libelle_compte, "piece": piece,
            "partenaire": _partenaire(partenaire), "libelle": libelle, "debit": _sans_zero(debit),
            "credit": _sans_zero(credit), "exercice": exercice, "source": src}


def _gl_tableau(page: Page, exercice: int, src: str, etat: dict) -> list[dict]:
    df = page.tableau
    cols = _associer(list(df.columns), ["date", "compte", "libelle_compte", "piece", "partenaire",
                                        "libelle", "debit", "credit", "montant"])
    lire = lambda r, k: _texte(r.get(cols[k])) if k in cols else ""  # noqa: E731
    res = []
    for _, r in df.iterrows():
        compte, nom = lire(r, "compte"), lire(r, "libelle_compte")
        m = RE_CODE.match(compte)
        if m:
            compte, nom = m.group(1), nom or m.group(2)
        if compte:
            etat["compte"], etat["nom"] = compte, nom
        date = _date_iso(lire(r, "date"))
        if not date:
            continue
        debit, credit = _montant(lire(r, "debit")), _montant(lire(r, "credit"))
        if "montant" in cols and debit is None and credit is None:
            m_ = _montant(lire(r, "montant"))
            if m_ is not None:
                debit, credit = (m_, None) if m_ >= 0 else (None, -m_)
        res.append(_ligne_gl(etat["compte"], etat["nom"], date, lire(r, "piece"), lire(r, "partenaire"),
                             lire(r, "libelle"), debit, credit, exercice, src))
    return res


def _gl_texte(page: Page, exercice: int, src: str, etat: dict) -> list[dict]:
    res = []
    for brute in page.texte.splitlines():
        ligne = brute.strip()
        n = normaliser(ligne)
        if not ligne or n.startswith(MOTS_IGNORES) or titre(ligne):
            continue
        m = RE_DATE_DEBUT.match(ligne)
        if not m:
            c = RE_CODE.match(ligne)
            if c and not _montants_en_fin(ligne)[1]:
                etat["compte"], etat["nom"] = c.group(1), c.group(2).strip()
            continue
        date = _date_iso(m.group(1))
        reste, montants = _montants_en_fin(m.group(2))
        if not montants or not date:
            continue
        mots = reste.split()
        compte, nom = etat["compte"], etat["nom"]
        if mots and re.fullmatch(r"\d{3,8}", mots[0]) and len(mots) > 1:
            compte, nom = mots.pop(0), ""
        piece = mots.pop(0) if mots and RE_PIECE.match(mots[0]) else ""
        if len(montants) >= 2:
            debit, credit = montants[0], montants[1]
        else:
            debit, credit = (montants[0], None) if montants[0] >= 0 else (None, -montants[0])
        res.append(_ligne_gl(compte, nom, date, piece, "", " ".join(mots), debit, credit, exercice, src))
    return res


def _grand_livre(section: Section, exercice: int, fichier: str) -> list[dict]:
    etat = {"compte": "", "nom": ""}
    res = []
    for page in section.pages:
        src = _source(fichier, page)
        res += _gl_tableau(page, exercice, src, etat) if page.tableau is not None \
            else _gl_texte(page, exercice, src, etat)
    return res


# ------------------------------------------------------------------ bilan et compte de résultat

def _lignes_etat(page: Page) -> list[tuple[str, str, list[float]]]:
    """(code, libellé, montants) pour chaque ligne de la page, texte ou tableau."""
    sortie = []
    if page.tableau is not None:
        for _, r in page.tableau.iterrows():
            textes, montants = [], []
            for v in r.tolist():
                t = _texte(v)
                if not t:
                    continue
                m = _montant(t) if re.fullmatch(r"\(?-?[\d'’ ]+([.,]\d+)?\)?", t) else None
                (montants.append(m) if m is not None else textes.append(t))
            code = textes.pop(0) if textes and re.fullmatch(r"\d{3,8}", textes[0]) else ""
            sortie.append((code, " ".join(textes), montants[:2]))
        return sortie
    for i, brute in enumerate(page.texte.splitlines()):
        ligne = RE_DATE.sub(" ", brute).strip() if i < 4 and titre(brute) else brute.strip()
        if not ligne or (i < 4 and titre(brute)) or re.fullmatch(r"[\d\s./\-]+", ligne):
            continue
        reste, montants = _montants_en_fin(ligne, 2)
        m = RE_CODE.match(reste)
        code, libelle = (m.group(1), m.group(2).strip()) if m else ("", reste)
        sortie.append((code, libelle, montants))
    return sortie


def _etat(section: Section, exercice: int, fichier: str) -> list[dict]:
    res, rub1, rub2 = [], "", ""
    for page in section.pages:
        src = _source(fichier, page)
        for code, libelle, montants in _lignes_etat(page):
            n = normaliser(libelle)
            if not montants:
                if not libelle:
                    continue
                if n in MOTS_NIVEAU_1:
                    rub1, rub2 = libelle, ""
                else:
                    rub2 = libelle
                continue
            if code:
                niveau = 3
            elif n.startswith(("resultat", "benefice", "perte de l'exercice", "total du bilan")):
                niveau, rub1, rub2 = 1, "", ""
            elif n.startswith("total") and any(re.search(rf"\b{m}\b", n) for m in MOTS_NIVEAU_1):
                niveau = 1
            else:
                niveau = 2
            res.append({"rubrique": " / ".join(x for x in (rub1, rub2) if x), "compte": code,
                        "libelle": libelle, "montant": montants[0],
                        "colonne_exercice_precedent": montants[1] if len(montants) > 1 else None,
                        "niveau": niveau, "exercice": exercice, "source": src})
    return res


def _annexe(section: Section, fichier: str) -> list[dict]:
    return [{"page": p.numero, "texte": p.texte.strip(), "source": _source(fichier, p)}
            for p in section.pages]


def extraire(section: Section, exercice: int, fichier: str) -> dict[str, list[dict]]:
    res: dict[str, list[dict]] = {k: [] for k in CLES}
    if section.type == "plan_comptable":
        res["plancomptable"] = _plan(section, exercice, fichier)
    elif section.type == "grand_livre":
        res["grandlivre"] = _grand_livre(section, exercice, fichier)
    elif section.type == "bilan":
        res["bilan"] = _etat(section, exercice, fichier)
    elif section.type == "compte_resultat":
        res["compteresultat"] = _etat(section, exercice, fichier)
    else:
        res["annexe"] = _annexe(section, fichier)
    return res
