# salaires.lecture_paie

## À quoi il sert

Lit le classeur de paie de l'exercice (forme du classeur 2025) déposé dans `entrees/08_salaires` et en tire le contenu de la fiche : le net dû (onglet ANNEE, colonne « Net définitif ») et chaque virement de l'onglet « Bank Transactions AAAA », classé ainsi, dans l'ordre :

1. type « Prêt… » : ni salaire ni frais ;
2. type « Remboursement… » : frais ;
3. montant égal à une ligne de frais de l'onglet PAYé : frais, même si le type dit « Régularisation » ou « Salaire » ;
4. type « Régularisation AAAA » ou montant égal à une ligne « hors période » de PAYé : salaire de l'année AAAA (sinon l'année précédente) ;
5. montant = salaire de PAYé + une ou deux lignes de frais ou hors période : découpage ;
6. sinon : salaire de l'exercice.

Contrôle : la somme des parts de salaire de l'exercice par employé doit égaler « Versé selon PAYE » (onglet ANNEE) ; sinon un point à vérifier.

## Ce qu'il lit

Les `.xlsx` de `entrees/08_salaires` : exercice dans ANNEE!B1 ; onglets EMPLOYES (noms en colonne B dès la ligne 7), ANNEE (titres en ligne 5 : « Net définitif », « Versé selon PAYE » ; nom complet dans la dernière colonne remplie), PAYé (blocs « E1 — nom », codes V1–V3, PAYE FRAIS, PAYE HP, colonnes janv…déc), Bank Transactions AAAA (Date, Employé, Type, Montant (CHF), Libellé, Banque, Écriture comptable, Rapprochement fiche).

## Ce qu'il écrit

Rien : il rend les lignes à [salaires.fiche](fiche.md) (via `salaires.lire_classeur`).

## Ce qui casse si on le change

- Renommer un onglet ou un titre de colonne dans le classeur de paie : lecture refusée avec « onglet … introuvable » ou « colonne … introuvable ».
- Les règles 3 à 5 s'appuient sur l'onglet PAYé : un virement mixte non détaillé dans PAYé est compté entièrement comme salaire, et le contrôle « Versé selon PAYE » le signale.
- Chaque ligne de PAYé ne sert qu'une fois (tolérance 0.01).

## Dépendances (automatique)

<!-- debut-auto -->
_Partie générée par `python outils/docs.py` à partir du code : ne pas la modifier à la main._

- **Fichier :** `src/reconsigliere/salaires/lecture_paie.py` (280 lignes)
- **Dépend de :** [config](../config.md), [salaires.fiche](fiche.md)
- **Utilisé par :** aucun module (point d'entrée)
- **Bibliothèques externes :** openpyxl

Fonctions et classes publiques :

- `FormatInconnu` : Le classeur n'a pas la forme attendue.
- `exercice_du_classeur` : Exercice lu dans ANNEE!B1, ou None si le classeur n'a pas cette forme.
- `trouver_classeur` : Premier classeur de paie de entrees/08_salaires dont l'exercice vaut `annee`.
- `lire` : Lit le classeur de paie et rend {annee, du, virements, points, controles, verse_paye}.
<!-- fin-auto -->
