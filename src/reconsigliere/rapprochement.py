"""Cœur de l'outil : relier chaque transaction bancaire à un partenaire et à un PDF."""

from __future__ import annotations

import re

from . import config
from .outils import normaliser

MOTS_BANCAIRES = {
    "ordre", "e-banking", "ebanking", "paiement", "payment", "debit", "credit", "lsv", "dd",
    "achat", "carte", "card", "twint", "virement", "transfert", "transfer", "qr", "facture",
    "bill", "versement", "maestro", "visa", "mastercard", "debitcard", "no", "ref", "sepa",
    "date", "chf", "eur", "permanent", "standing", "order", "achat", "retrait", "bancomat",
    "recurrent", "prelevement", "e-bill", "ebill", "twint", "post", "postfinance", "de", "du", "la", "le", "les", "a", "au", "en", "pour",
}

STATUT_COMPTABILISE = "Comptabilisé"
STATUT_A_COMPTABILISER = "À comptabiliser"
STATUT_A_CONFIRMER = "À confirmer"
STATUT_EXPLIQUE = "Expliqué sans pièce"
STATUT_MANQUANT = "PDF manquant"
STATUT_IGNORE = "Ignoré"

STATUTS_FORCES = {
    "comptabilise": STATUT_COMPTABILISE,
    "a comptabiliser": STATUT_A_COMPTABILISER,
    "sans piece": STATUT_EXPLIQUE,
    "ignorer": STATUT_IGNORE,
}


def deviner_partenaire(t: dict, regles: list[tuple[str, str]]) -> tuple[str, str]:
    """Renvoie (partenaire, origine de l'information)."""
    libelle = normaliser(t["libelle"])
    for mot, partenaire in regles:
        if mot in libelle:
            return partenaire, "règle"
    if t.get("partenaire"):
        return t["partenaire"], "banque"
    mots = [m for m in re.split(r"[\s,;:/|]+", t["libelle"])
            if m and normaliser(m) not in MOTS_BANCAIRES and not re.search(r"\d", m)]
    return (" ".join(mots[:3]).title() if mots else "Inconnu"), "libellé"


def _mots_significatifs(texte: str) -> list[str]:
    return [m for m in re.split(r"[^a-z0-9]+", normaliser(texte))
            if len(m) >= 3 and m not in MOTS_BANCAIRES and not m.isdigit()]


def score(t: dict, pdf: dict) -> tuple[int, list[str]]:
    points, raisons = 0, []
    montant = abs(t["montant"])
    if any(abs(m - montant) <= config.TOLERANCE_MONTANT for m in pdf["montants"]):
        points += 50
        raisons.append("montant")
        if pdf["montants"] and abs(pdf["montants"][0] - montant) <= config.TOLERANCE_MONTANT:
            points += 5
    if pdf["dates"]:
        ecart = min(abs((d - t["date"]).days) for d in pdf["dates"])
        if ecart <= 3:
            points += 20
            raisons.append("date")
        elif ecart <= config.TOLERANCE_JOURS:
            points += 12
            raisons.append("date proche")
        elif ecart <= 60:
            points += 5
    if t.get("iban") and t["iban"] in pdf["ibans"]:
        points += 25
        raisons.append("IBAN")
    refs = [normaliser(t.get("reference", ""))] + [
        normaliser(n) for n in re.findall(r"[A-Za-z0-9\-/]{5,}", t["libelle"]) if re.search(r"\d", n)]
    if any(r and len(r) >= 5 and r in pdf["texte_norm"] for r in refs):
        points += 25
        raisons.append("référence")
    mots = _mots_significatifs(t.get("partenaire_trouve", ""))
    if mots and any(m in pdf["texte_norm"] for m in mots):
        points += 20
        raisons.append("partenaire")
    return min(points, 100), raisons


def _correspond_compta(t: dict, ligne: dict) -> bool:
    if ligne["montant"] is None or abs(abs(ligne["montant"]) - abs(t["montant"])) > config.TOLERANCE_MONTANT:
        return False
    if ligne["date"] is None:
        return True
    return abs((ligne["date"] - t["date"]).days) <= config.TOLERANCE_JOURS


def reconcilier(transactions: list[dict], pdfs: list[dict], compta: list[dict],
                pdfs_compta: list[dict], corrections: dict) -> list[dict]:
    corr = corrections["transactions"]
    empreintes_compta = {p["empreinte"] for p in pdfs_compta}
    noms_compta = {normaliser(l["fichier"]) for l in compta if l["fichier"]}
    tous_pdfs = pdfs + [p for p in pdfs_compta if p["empreinte"] not in {x["empreinte"] for x in pdfs}]
    par_nom = {normaliser(p["nom"]): p for p in tous_pdfs}

    for t in transactions:
        c = corr.get(t["id"], {})
        partenaire, origine = deviner_partenaire(t, corrections["regles_partenaires"])
        if c.get("partenaire"):
            partenaire, origine = c["partenaire"], "ta correction"
        t.update(partenaire_trouve=partenaire, origine_partenaire=origine,
                 explication=c.get("explication", ""), pdf=None, score=0, raisons="")

    # 1. Liens imposés dans mes_corrections.xlsx
    utilises: set[str] = set()
    for t in transactions:
        nom = normaliser(corr.get(t["id"], {}).get("pdf", ""))
        if nom and nom in par_nom:
            t.update(pdf=par_nom[nom], score=100, raisons="ta correction")
            utilises.add(par_nom[nom]["empreinte"])

    # 2. Rapprochement automatique, meilleurs scores d'abord, un PDF par transaction
    paires = []
    for t in transactions:
        if t["pdf"] is not None:
            continue
        for p in tous_pdfs:
            if p["empreinte"] in utilises:
                continue
            s, r = score(t, p)
            if s >= config.SEUIL_A_CONFIRMER:
                paires.append((s, t["id"], p["empreinte"], t, p, r))
    paires.sort(key=lambda x: -x[0])
    lies: set[str] = set()
    for s, tid, emp, t, p, r in paires:
        if tid in lies or emp in utilises:
            continue
        t.update(pdf=p, score=s, raisons=", ".join(r))
        lies.add(tid)
        utilises.add(emp)

    # 3. Statuts
    for t in transactions:
        force = normaliser(corr.get(t["id"], {}).get("statut_force", ""))
        p = t["pdf"]
        dans_compta = any(_correspond_compta(t, l) for l in compta) or (
            p is not None and (p["empreinte"] in empreintes_compta or normaliser(p["nom"]) in noms_compta))
        if force in STATUTS_FORCES:
            t["statut"] = STATUTS_FORCES[force]
        elif dans_compta:
            t["statut"] = STATUT_COMPTABILISE
        elif p is not None and t["score"] >= config.SEUIL_SUR:
            t["statut"] = STATUT_A_COMPTABILISER
        elif p is not None:
            t["statut"] = STATUT_A_CONFIRMER
        elif t["explication"]:
            t["statut"] = STATUT_EXPLIQUE
        else:
            t["statut"] = STATUT_MANQUANT
    return transactions


def pdfs_non_lies(pdfs: list[dict], transactions: list[dict]) -> list[dict]:
    lies = {t["pdf"]["empreinte"] for t in transactions if t["pdf"] is not None}
    return [p for p in pdfs if p["empreinte"] not in lies]
