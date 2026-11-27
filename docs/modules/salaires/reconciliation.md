# salaires.reconciliation

## À quoi il sert

Calcule et écrit la réconciliation des salaires d'un exercice N pour la fiduciaire, `sorties/salaires/Reconciliation_salaires_N.xlsx` :

- **Synthèse** (formules seulement) : par employé Dû N, Payé en N, Reporté à N+1, Payé en N+1, Écart ; en bas, si la fiche N−1 existe, le bloc « Restes N−1 payés en N » (Reporté de N−1 selon la fiche N−1, Selon votre classeur (FRAIS) si l'onglet FRAIS a été lu, Payé en N, Écart = Reporté − Payé) ;
- **Dû N**, **Reste N−1**, **Payé en N** (tous les virements de l'année, lignes d'un autre exercice en vert, colonne Preuve), **Payé en N+1** (virements de N+1 qui règlent N) ;
- **Dû N** montre aussi le reste N−1 selon ton classeur et tes notes ;
- **Points à vérifier** : écarts, reste N−1 différent entre la fiche N−1 et ton classeur, tes notes du classeur, prêts, découpages, régularisations classées en frais, fiche N+1 absente, contrôles du lecteur, puis tes propres points.

## Ce qu'il lit

Les fiches N−1, N et N+1 ([salaires.fiche](fiche.md)).

## Ce qu'il écrit

`sorties/salaires/Reconciliation_salaires_N.xlsx` (remplacé à chaque génération).

## Ce qui casse si on le change

- Les formules `SUMIFS` de la synthèse visent les colonnes A (employé), E (exercice) et F (part salaire) des feuilles de virements : changer l'ordre des colonnes casse la synthèse.
- La colonne « Selon votre classeur (FRAIS) » vise la colonne E de la feuille Dû N : déplacer cette colonne casse le bloc du bas.
- Le reste N−1 est recalculé depuis la fiche N−1 : corriger la fiche N−1 change le bloc du bas de N.
- Fichier ouvert dans Excel : écriture refusée avec « Ferme … dans Excel ».

## Dépendances (automatique)

<!-- debut-auto -->
_Partie générée par `python outils/docs.py` à partir du code : ne pas la modifier à la main._

- **Fichier :** `src/reconsigliere/salaires/reconciliation.py` (313 lignes)
- **Dépend de :** [config](../config.md), [salaires.fiche](fiche.md)
- **Utilisé par :** [onglet_salaires](../onglet_salaires.md)
- **Bibliothèques externes :** openpyxl

Fonctions et classes publiques :

- `chemin_sortie`
- `resume`
- `points`
- `ecrire`
<!-- fin-auto -->
