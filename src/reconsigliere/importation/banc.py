"""Banc d'essai : fait classer les mêmes pages ambiguës fictives par plusieurs modèles.

python -m reconsigliere banc-ia [--modeles haiku sonnet]
Chaque page est volontairement sans titre : c'est le cas où l'IA est appelée.
"""

from __future__ import annotations

from . import ia

PAGES = [
    {"attendu": "bilan", "texte": "Liquidités 45'210.30 38'100.00\nCréances résultant de ventes 12'400.00 9'800.00\n"
                                  "Actifs de régularisation 1'250.00 900.00\nTotal actifs circulants 58'860.30 48'800.00"},
    {"attendu": "bilan", "texte": "Dettes résultant d'achats 8'300.00 7'150.00\nCapital-actions 100'000.00 100'000.00\n"
                                  "Réserve légale issue du bénéfice 5'000.00 5'000.00\nPerte reportée -54'139.70 -63'350.00"},
    {"attendu": "compte_resultat", "texte": "Ventes de prestations 182'400.00 150'200.00\nCharges de matériel -12'300.00 -9'800.00\n"
                                            "Salaires -96'000.00 -90'000.00\nCharges sociales -14'500.00 -13'200.00"},
    {"attendu": "compte_resultat", "texte": "Loyers -24'000.00\nFrais de brevets -17'288.64\nAmortissements -8'819.10\n"
                                            "Produits financiers 12.40\nImpôts directs -350.00"},
    {"attendu": "grand_livre", "texte": "03.04.2024 BILL/2024/04/0002 André Roland Annuité EP 0.00 1'830.00 -12'430.00\n"
                                        "15.04.2024 INV/2024/0007 Client Alpha SA Prestation avril 5'400.00 0.00 -7'030.00\n"
                                        "30.04.2024 BNK1/2024/0041 Frais bancaires 0.00 12.50 -7'042.50"},
    {"attendu": "grand_livre", "texte": "1020 UBS compte courant\n02.01.2024 Solde d'ouverture 38'100.00\n"
                                        "05.01.2024 Loyer janvier 2'000.00\n31.01.2024 Salaires 8'000.00"},
    {"attendu": "plan_comptable", "texte": "1000 Caisse\n1020 Banque\n1100 Créances clients\n1170 TVA récupérable\n"
                                           "1300 Charges payées d'avance\n1500 Machines"},
    {"attendu": "plan_comptable", "texte": "6000 Loyers Charges\n6500 Frais de bureau Charges\n6570 Informatique Charges\n"
                                           "6800 Amortissements Amortissements\n3400 Ventes de prestations Revenus"},
    {"attendu": "annexe", "texte": "La société n'a pas plus de 10 emplois à plein temps en moyenne annuelle.\n"
                                   "Il n'existe aucun engagement conditionnel au bénéfice de tiers.\n"
                                   "Aucun événement important n'est survenu après la date du bilan."},
    {"attendu": "annexe", "texte": "Les brevets sont portés à l'actif au coût d'acquisition et amortis sur leur durée d'utilité.\n"
                                   "La licence exclusive EPFL est présentée hors bilan.\nDettes envers les institutions de prévoyance : 1'240.00"},
    {"attendu": "autre", "texte": "Madame, Monsieur,\nNous vous remercions de votre commande du 12 mars.\n"
                                  "Veuillez trouver ci-joint notre offre pour la maintenance annuelle.\nMeilleures salutations"},
    {"attendu": "autre", "texte": "Relevé de compte UBS\nIBAN CH93 0076 2011 6238 5295 7\nSolde au 31.03.2024 45'210.30\n"
                                  "Ordre permanent loyer 2'000.00 mensuel"},
]


def comparer(modeles: list[str], cle: str, envoyer: ia.Envoyer | None = None) -> list[dict]:
    resultats = []
    for nom in modeles:
        modele_id = nom if nom.startswith("claude-") else ia.MODELES.get(nom, nom)
        envoi = envoyer or ia.envoyeur_sdk(cle)
        justes, entree, sortie, erreurs = 0, 0, 0, []
        for page in PAGES:
            type_, usage = ia.classer_par_ia(page["texte"], cle, modele_id, envoyer=envoi)
            entree += usage["entree"]
            sortie += usage["sortie"]
            if type_ == page["attendu"]:
                justes += 1
            else:
                erreurs.append(f"attendu {page['attendu']}, reçu {type_} : {page['texte'][:50]!r}")
        resultats.append({"modele": modele_id, "justes": justes, "total": len(PAGES),
                          "justesse": justes / len(PAGES), "entree": entree, "sortie": sortie,
                          "cout_usd": ia.cout_usd(modele_id, entree, sortie), "erreurs": erreurs})
    return resultats


def rapport(resultats: list[dict]) -> str:
    lignes = ["Modèle                 Justes   Tokens entrée/sortie   Coût total     Coût par page"]
    for r in resultats:
        lignes.append(f"{r['modele']:<22} {r['justes']:>2}/{r['total']:<4} {r['entree']:>9} / {r['sortie']:<9} "
                      f"{r['cout_usd']:>9.5f} $   {r['cout_usd'] / r['total']:.6f} $")
        lignes += [f"    - {e}" for e in r["erreurs"]]
    return "\n".join(lignes)
