# onglets_societe.py : les onglets, un élément par onglet

## À quoi il sert

Donne l'ordre des dix onglets de la fenêtre (Réconciliation, Documents, Salaires, Brevets, Projets, Revenus, Plan comptable,
Partenaires, Année comptable, Apprentissage) et la phrase qui explique chacun. Construit les onglets simples à tableau :

- **Projets** et **Revenus** : les lignes des onglets Projets et Revenus de `societe.xlsx`, avec un bouton pour ouvrir le classeur.
- **Plan comptable** et **Partenaires** : la liste de l'année choisie dans le référentiel de l'année (compte habituel de chaque
  partenaire, nombre d'écritures, part). Sans année construite, une phrase renvoie vers l'onglet « Année comptable ».

Calcule aussi la taille de la fenêtre : 1040 × 900 à 100 %, agrandie avec l'affichage de Windows, jamais plus grande que l'écran.

## Ce qu'il lit

`societe.xlsx` via [societe](societe.md) et le référentiel de l'année via [exercices](exercices.md). Rien d'autre.

## Ce qu'il écrit

Rien.

## Ce qui casse si on le change

- `ONGLETS` fixe l'ordre et les titres ; chaque clé doit avoir sa phrase dans `EXPLICATIONS` et son cadre dans [fenetre](fenetre.md).
  Les tests vérifient l'ordre et l'absence des anciens titres (« État de la société », « Exercices », « Assistant »).
- Les colonnes lues (`code`, `nom`, `type`, `partenaire`, `compte`, `libelle_compte`, `occurrences`, `part`) sont celles du
  référentiel écrit par [exercices](exercices.md) ; les renommer là-bas vide ces tableaux.
- `ONGLETS_PAR_LIGNE = 5` : la barre fait deux lignes ; plus d'onglets ajoutent une ligne.

## Dépendances (automatique)

<!-- debut-auto -->
_Partie générée par `python outils/docs.py` à partir du code : ne pas la modifier à la main._

- **Fichier :** `src/reconsigliere/onglets_societe.py` (194 lignes)
- **Dépend de :** [exercices](exercices.md), [societe](societe.md)
- **Utilisé par :** [fenetre](fenetre.md)
- **Bibliothèques externes :** aucune

Fonctions et classes publiques :

- `lignes_projets`
- `lignes_revenus`
- `lignes_referentiel` : Lignes d'une liste (PlanComptable ou Partenaires) du référentiel de l'année, et une phrase d'état.
- `geometrie` : Taille de la fenêtre en pixels : 1040 × 900 à 100 %, agrandie avec l'affichage de Windows, bornée à l'écran.
- `OngletTableau` : Un onglet simple : phrase d'état, choix d'année facultatif, tableau, boutons.
- `remplir_projets`
- `remplir_revenus`
<!-- fin-auto -->
