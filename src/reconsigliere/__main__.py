"""Lancement.

- Fenêtre : Reconsigliere.bat (Windows), reconsigliere.sh (Ubuntu) ou python -m reconsigliere.fenetre
- Ligne de commande : python -m reconsigliere [--dossier CHEMIN]
- Import de documents : python -m reconsigliere importer [FICHIER ...] [--sans-ia] [--modele haiku|sonnet]
- Banc d'essai IA : python -m reconsigliere banc-ia [--modeles haiku sonnet]
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


def _ligne_de_commande(arguments: list[str] | None = None) -> None:
    import sys
    arguments = sys.argv[1:] if arguments is None else arguments
    commande = arguments[0] if arguments and arguments[0] in ("importer", "banc-ia") else "reconcilier"
    if commande != "reconcilier":
        arguments = arguments[1:]
    parser = argparse.ArgumentParser(prog=f"reconsigliere {commande}".replace(" reconcilier", ""))
    parser.add_argument("--dossier", type=Path,
                        help="dossier de travail qui contient entrees et sorties "
                             "(par défaut : le dossier choisi dans la fenêtre, sinon celui du programme)")
    if commande == "importer":
        parser.add_argument("fichiers", nargs="*", type=Path,
                            help="documents à importer (par défaut : tout entrees/07_documents)")
        parser.add_argument("--sans-ia", action="store_true", help="ne jamais appeler l'IA")
        parser.add_argument("--modele", help="haiku ou sonnet (ou identifiant complet)")
        parser.add_argument("--forcer", action="store_true", help="réimporter les documents déjà importés")
    if commande == "banc-ia":
        parser.add_argument("--modeles", nargs="+", default=["haiku", "sonnet"])
    args = parser.parse_args(arguments)
    dossier = args.dossier or installation.dossier_memorise()
    if dossier:
        config.definir_racine(dossier)
    if commande == "reconcilier":
        main()
        return
    from .importation import banc, ia, pipeline
    cle = ia.cle_api()
    if commande == "banc-ia":
        if not cle:
            raise SystemExit("Aucune clé API : définis ANTHROPIC_API_KEY ou enregistre-la dans les réglages IA.")
        print(banc.rapport(banc.comparer(args.modeles, cle)))
        return
    installation.creer_dossiers(config.RACINE)
    options = {"cle": None if args.sans_ia else cle,
               "modele_id": ia.MODELES.get(args.modele, args.modele) if args.modele else None}
    if args.fichiers:
        for f in args.fichiers:
            pipeline.importer(f, config.RACINE, **options)
    else:
        resultats = pipeline.importer_dossier(config.RACINE, forcer=args.forcer, **options)
        print(f"{len(resultats)} document(s) importé(s).")


if __name__ == "__main__":
    _ligne_de_commande()
