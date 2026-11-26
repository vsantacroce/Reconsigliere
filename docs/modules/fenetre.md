# fenetre.py : la fenêtre du programme

## À quoi il sert

L'interface que tu utilises sous Windows (tkinter, inclus dans Python ; sous Ubuntu il faut `python3-tk`). Deux parties :

- **Réconciliation** : choix du dossier de travail, compteurs de fichiers par dossier, bouton « Lancer la réconciliation »
  avec barre de progression et journal, boutons d'ouverture des résultats, « Importer les documents », réglages IA.
- **Assistant société** : sous-onglet « État de la société » (brevets, coûts, projets, revenus, journal, tableau de bord) et
  sous-onglet « Exercices et changements » (construire, voir, valider et verrouiller, rouvrir, demander un changement, écarts, suggestions).

Les petites fenêtres `Journal`, `Changement` et `Ecarts` sont dans le même fichier.

## Ce qu'il lit

Le dossier de travail mémorisé ([installation](installation.md)), l'état de la société ([societe](societe.md)) et des exercices
([exercices](exercices.md)) pour les afficher.

## Ce qu'il écrit

Rien lui-même : chaque bouton appelle un autre module (réconciliation via [__main__](__main__.md), import via
[importation.pipeline](importation/pipeline.md), journal et tableau de bord via [societe](societe.md), référentiels via
[exercices](exercices.md), réglages via [installation](installation.md)).

## Ce qui casse si on le change

- **Travail en arrière-plan** : la réconciliation et l'import tournent dans un fil séparé et parlent à la fenêtre par une file de messages.
  Toucher directement aux éléments de la fenêtre depuis ce fil fait planter tkinter de façon aléatoire.
- **Barre de progression** : `NB_ETAPES = 5` doit suivre les lignes `N/5` de [__main__](__main__.md).
- **Imports tardifs** : pandas et le pipeline d'import ne sont chargés qu'au clic, pour que la fenêtre s'ouvre vite. Les remonter en
  haut du fichier ralentit l'ouverture.
- **Choix manuel du type de page** (`_demander_type`) : appelé par le pipeline quand ni les règles ni l'IA ne savent classer une page.
- La fenêtre fait 920 × 880 ; ajouter un onglet ou des boutons peut dépasser l'écran d'un portable.
- C'est le point d'entrée de l'icône Windows (via [windows.demarrer](windows/demarrer.md)) : une erreur à l'import de ce module
  empêche le programme de s'ouvrir.

## Dépendances (automatique)

<!-- debut-auto -->
_Partie générée par `python outils/docs.py` à partir du code : ne pas la modifier à la main._

- **Fichier :** `src/reconsigliere/fenetre.py` (1041 lignes)
- **Dépend de :** [__main__](__main__.md), [config](config.md), [exercices](exercices.md), [importation.classement](importation/classement.md), [importation.ia](importation/ia.md), [importation.pipeline](importation/pipeline.md), [installation](installation.md), [societe](societe.md)
- **Utilisé par :** aucun module (point d'entrée)
- **Bibliothèques externes :** aucune

Fonctions et classes publiques :

- `Fenetre`
- `Journal` : Petite fenêtre pour ajouter un événement au journal de la société.
- `Changement` : Demande de changement : ajout, modification ou retrait d'un élément d'une liste du référentiel.
- `Ecarts` : Liste des écarts entre deux exercices.
- `lancer`
<!-- fin-auto -->
