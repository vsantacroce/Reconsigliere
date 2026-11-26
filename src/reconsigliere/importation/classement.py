"""Classement d'une page par règles locales (zéro token)."""

from __future__ import annotations

import re

from ..outils import normaliser
from .pages import Page

TYPES = ("bilan", "compte_resultat", "grand_livre", "plan_comptable", "annexe", "autre")

LIBELLES = {
    "bilan": "Bilan", "compte_resultat": "Compte de résultat", "grand_livre": "Grand livre",
    "plan_comptable": "Plan comptable", "annexe": "Annexe", "autre": "Autre",
}

# Titres forts (texte normalisé : minuscules, sans accents)
TITRES = {
    "compte_resultat": [r"compte de resultats?", r"compte de pertes et profits", r"income statement",
                        r"profit and loss", r"erfolgsrechnung", r"conto economico"],
    "grand_livre": [r"grand[ -]livre", r"general ledger", r"hauptbuch", r"extrait de compte comptable"],
    "plan_comptable": [r"plan comptable", r"plan des comptes", r"chart of accounts", r"kontenplan"],
    "annexe": [r"annexe", r"notes to the (?:financial|accounts)", r"\banhang\b"],
    "bilan": [r"\bbilan\b", r"balance sheet", r"\bbilanz\b"],
}

INDICES = {
    "bilan": ["total des actifs", "total actifs", "total de l'actif", "total des passifs", "total passifs",
              "total du passif", "actifs circulants", "actifs immobilises", "capitaux propres",
              "fonds propres", "capital-actions", "capital social", "dettes a court terme", "passifs"],
    "compte_resultat": ["chiffre d'affaires", "produits d'exploitation", "charges d'exploitation",
                        "resultat de l'exercice", "resultat d'exploitation", "benefice de l'exercice",
                        "perte de l'exercice", "charges de personnel", "amortissements", "produits",
                        "charges"],
    "grand_livre": ["debit", "credit", "solde", "report", "solde reporte", "piece", "contrepartie"],
    "plan_comptable": ["code", "type de compte", "classe", "intitule du compte"],
    "annexe": ["principes comptables", "methodes d'evaluation", "art. 959", "art. 957", " co)",
               "engagements conditionnels", "evenements posterieurs", "emplois a plein temps",
               "dissolution nette de reserves", "dettes envers les institutions de prevoyance"],
}

RE_DATE = re.compile(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b|\b\d{4}-\d{2}-\d{2}\b")
RE_MONTANT = re.compile(r"-?\d{1,3}(?:['’ ]\d{3})*[.,]\d{2}\b")
RE_LIGNE_PLAN = re.compile(r"^\s*\d{3,8}\s+[^\d\s][^\d]{2,}$")

SEUIL = 3.0
ECART = 1.5
LIGNES_TITRE = 4


def lignes(texte: str) -> list[str]:
    return [l for l in (x.strip() for x in texte.splitlines()) if l]


def lignes_ecritures(texte: str) -> int:
    """Nombre de lignes qui portent une date et au moins un montant (typique du grand livre)."""
    return sum(1 for l in lignes(texte) if RE_DATE.search(l) and RE_MONTANT.search(l))


def lignes_plan(texte: str) -> int:
    return sum(1 for l in lignes(texte) if RE_LIGNE_PLAN.match(l))


def titre(texte: str) -> str | None:
    """Type annoncé par un titre dans les premières lignes de la page."""
    for l in lignes(texte)[:LIGNES_TITRE]:
        n = normaliser(l)
        for type_, motifs in TITRES.items():
            if any(re.search(m, n) for m in motifs):
                return type_
    return None


def _score_tableau(colonnes: list[str]) -> dict[str, float]:
    cols = {normaliser(c) for c in colonnes}
    a = lambda *mots: any(any(c == m or c.startswith(m + " ") for c in cols) for m in mots)  # noqa: E731
    scores = {}
    if a("date") and a("debit", "credit", "montant", "solde"):
        scores["grand_livre"] = 6.0
    elif a("code", "numero", "no", "compte", "account") and a("nom", "libelle", "intitule", "name", "description") \
            and not a("debit", "credit", "montant", "solde", "date"):
        scores["plan_comptable"] = 6.0
    return scores


def classer(page: Page) -> tuple[str | None, float, bool]:
    """Renvoie (type ou None si indécis, score du meilleur type, titre fort trouvé)."""
    t = titre(page.texte)
    scores = {k: 0.0 for k in TYPES}
    if page.tableau is not None:
        for k, v in _score_tableau(list(page.tableau.columns)).items():
            scores[k] += v
    if t:
        scores[t] += 10
    n = normaliser(page.texte)
    for type_, mots in INDICES.items():
        scores[type_] += sum(1.0 for m in mots if m in n)
    scores["grand_livre"] += min(4.0, lignes_ecritures(page.texte) / 2)
    if lignes_plan(page.texte) >= 3 and lignes_ecritures(page.texte) == 0:
        scores["plan_comptable"] += 3.0
    ordre = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    (meilleur, s1), (_, s2) = ordre[0], ordre[1]
    if t:
        return t, scores[t], True
    if s1 >= SEUIL and s1 >= ECART * s2:
        return meilleur, s1, False
    return None, s1, False
