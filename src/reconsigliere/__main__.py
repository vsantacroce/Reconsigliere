"""Lancement.

- Fenêtre : Reconsigliere.bat (Windows), reconsigliere.sh (Ubuntu) ou python -m reconsigliere.fenetre
- Ligne de commande : python -m reconsigliere [--dossier CHEMIN]
- Import de documents : python -m reconsigliere importer [FICHIER ...] [--sans-ia] [--modele haiku|sonnet]
- Banc d'essai IA : python -m reconsigliere banc-ia [--modeles haiku sonnet]
- Salaires : python -m reconsigliere salaires AAAA [--lire]
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Callable

from . import (apprentissage, chargement, config, corrections, exercices, installation, pdf_extraction,
               rapprochement, sorties)


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
    try:
        n_comptes = exercices.proposer_comptes(transactions)
        if n_comptes:
            log(f"    Compte proposé pour {n_comptes} transaction(s), selon le référentiel de leur exercice")
    except Exception as e:  # noqa: BLE001 - la proposition de compte ne doit jamais bloquer la réconciliation
        log(f"    Comptes non proposés : {e}")
    analyse = None
    try:
        analyse = apprentissage.executer(transactions, corr)
        r = analyse.resume
        if r["corrections"]:
            log(f"    Apprentissage : {r['corrections']} correction(s) de compte, {r['actives'] + r['conditionnelles']} "
                f"règle(s) appliquée(s) à {r['appliquees']} transaction(s), {r['alertes']} alerte(s)")
    except Exception as e:  # noqa: BLE001 - l'apprentissage ne doit jamais bloquer la réconciliation
        log(f"    Apprentissage non calculé : {e}")

    log("5/5 Écriture des sorties…")
    sorties.copier_pdfs(transactions)
    xlsx = sorties.ecrire_excel(transactions, orphelins)
    page = sorties.ecrire_html(transactions, orphelins)
    fichier_apprentissage = apprentissage.ecrire(analyse) if analyse is not None else None

    compte = Counter(t["statut"] for t in transactions)
    for statut, n in compte.most_common():
        log(f"    {statut} : {n}")
    log(f"    PDF sans transaction : {len(orphelins)}")
    log(f"\nTerminé.\n  {xlsx}\n  {page}")
    return {"statuts": dict(compte), "orphelins": len(orphelins), "excel": xlsx, "html": page,
            "apprentissage": fichier_apprentissage}


def _ligne_de_commande(arguments: list[str] | None = None) -> None:
    import sys
    arguments = sys.argv[1:] if arguments is None else arguments
    commande = arguments[0] if arguments and arguments[0] in ("importer", "banc-ia", "salaires") else "reconcilier"
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
    if commande == "salaires":
        parser.add_argument("annee", type=int, help="exercice à réconcilier, par exemple 2025")
        parser.add_argument("--lire", action="store_true",
                            help="relire d'abord le classeur de paie de entrees/08_salaires (met la fiche à jour)")
    args = parser.parse_args(arguments)
    dossier = args.dossier or installation.dossier_memorise()
    if dossier:
        config.definir_racine(dossier)
    if commande == "reconcilier":
        main()
        return
    if commande == "salaires":
        _salaires(args.annee, args.lire)
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


def _salaires(annee: int, lire: bool) -> None:
    from . import salaires
    installation.creer_dossiers(config.RACINE)
    try:
        if lire:
            b = salaires.lire_classeur(annee)
            print(f"{b['classeur'].name} lu : {b['ajoutes']} nouveau(x), {b['retires']} retiré(s), "
                  f"{b['gardees']} correction(s) gardée(s), {b['manuels']} ligne(s) à la main.")
        chemin, r = salaires.generer(annee)
    except (salaires.ClasseurAbsent, salaires.FormatInconnu, salaires.FichierOuvert) as e:
        raise SystemExit(str(e)) from e
    t = r["total"]
    print(f"Salaires {annee} : dû {t['du']:.2f}, payé {t['paye']:.2f}, reporté {t['reporte']:.2f}, "
          f"payé en {annee + 1} {t['paye_suivant']:.2f}, écart {t['ecart']:.2f}, {len(r['points'])} point(s) à vérifier.")
    print(chemin)


if __name__ == "__main__":
    _ligne_de_commande()
