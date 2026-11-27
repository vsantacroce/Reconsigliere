# onglet_salaires

## À quoi il sert

L'onglet « Salaires » de la fenêtre : 1. choisir l'année, **Lire le classeur de paie** (met la fiche à jour et dit combien de virements sont nouveaux, retirés, et combien de corrections sont gardées), **Ouvrir la fiche**, **Ouvrir le dossier** ; 2. **Générer** l'Excel pour la fiduciaire, **Ouvrir**, **Enregistrer sous…** (copie où tu veux). En dessous : le reste à régler, le nombre de points à vérifier, la synthèse par employé (écarts en orange) et les restes de l'année précédente.

## Ce qu'il lit

Les fiches via [salaires.fiche](salaires/fiche.md), la liste des exercices via `salaires.exercices_disponibles`.

## Ce qu'il écrit

La fiche (bouton Lire), l'Excel de réconciliation (Générer), une copie choisie par toi (Enregistrer sous…).

## Ce qui casse si on le change

- Construit par `construire(parent, fenetre)` et actualisé par `_onglet_change` de [fenetre](fenetre.md) (repéré par son widget).
- Les messages d'erreur viennent des exceptions `ClasseurAbsent`, `FormatInconnu`, `FichierOuvert` du paquet salaires.

## Dépendances (automatique)

<!-- debut-auto -->
_Partie générée par `python outils/docs.py` à partir du code : ne pas la modifier à la main._

- **Fichier :** `src/reconsigliere/onglet_salaires.py` (219 lignes)
- **Dépend de :** [config](config.md), [installation](installation.md), [salaires.fiche](salaires/fiche.md), [salaires.reconciliation](salaires/reconciliation.md)
- **Utilisé par :** [fenetre](fenetre.md)
- **Bibliothèques externes :** aucune

Fonctions et classes publiques :

- `OngletSalaires`
- `construire`
<!-- fin-auto -->
