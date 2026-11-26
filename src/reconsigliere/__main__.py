"""Lancement.

- Fenêtre : Reconsigliere.bat (Windows), reconsigliere.sh (Ubuntu) ou python -m reconsigliere.fenetre
- Ligne de commande : python -m reconsigliere [--dossier CHEMIN]
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Callable

from . import chargement, config, corrections, installation, pdf_extraction, rapprochement, sorties


def main(log: Callable[[str], None] = print) -> dict:
    """Exécute la réconciliation dans le dossier de travail courant (config.RACINE).

    Les lignes qui commencent par « N/5 » marquent les étapes : la fenêtre s'en sert
    pour faire avancer la barre de progression.
    """
    installation.creer_dossiers(config.RACINE)
    corrections.creer_modele_si_absent()
    corr = corrections.charger()

    log("1/5 Lecture des transactions…")
    transactions = chargement.charger_transactions()
    chargement.enrichir_avec_infos_bancaires(transactions)
    log(f"    {len(transactions)} transaction(s)")

    log("2/5 Lecture des factures (PDF et images)…")
    pdfs = pdf_extraction.analyser_dossier(config.DOSSIER_FACTURES)
    pdfs_compta = pdf_extraction.analyser_dossier(config.DOSSIER_COMPTABILITE)
    illisibles = [p["nom"] for p in pdfs if not p["lisible"]]
    log(f"    {len(pdfs)} facture(s) à traiter, {len(pdfs_compta)} pièce(s) déjà en comptabilité")
    if illisibles:
        log(f"    {len(illisibles)} pièce(s) sans texte lisible : elles ne pourront être liées que par tes corrections")
        if not pdf_extraction.ocr_disponible():
            log("    Astuce : installe Tesseract OCR pour lire le texte des images et des scans.")

    log("3/5 Lecture de la comptabilité…")
    compta = chargement.charger_comptabilite()
    log(f"    {len(compta)} ligne(s)")

    log("4/5 Rapprochement…")
    rapprochement.reconcilier(transactions, pdfs, compta, pdfs_compta, corr)
    orphelins = rapprochement.pdfs_non_lies(pdfs, transactions)

    log("5/5 Écriture des sorties…")
    sorties.copier_pdfs(transactions)
    xlsx = sorties.ecrire_excel(transactions, orphelins)
    page = sorties.ecrire_html(transactions, orphelins)

    compte = Counter(t["statut"] for t in transactions)
    for statut, n in compte.most_common():
        log(f"    {statut} : {n}")
    log(f"    PDF sans transaction : {len(orphelins)}")
    log(f"\nTerminé.\n  {xlsx}\n  {page}")
    return {"statuts": dict(compte), "orphelins": len(orphelins), "excel": xlsx, "html": page}


def _ligne_de_commande() -> None:
    parser = argparse.ArgumentParser(prog="reconsigliere")
    parser.add_argument("--dossier", type=Path,
                        help="dossier de travail qui contient entrees et sorties "
                             "(par défaut : le dossier choisi dans la fenêtre, sinon celui du programme)")
    args = parser.parse_args()
    dossier = args.dossier or installation.dossier_memorise()
    if dossier:
        config.definir_racine(dossier)
    main()


if __name__ == "__main__":
    _ligne_de_commande()
