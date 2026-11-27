# __main__.py : le lancement en ligne de commande et l'enchaînement de la réconciliation

## À quoi il sert

Enchaîne les cinq étapes de la réconciliation (`main`) et répond aux commandes :

- `python -m reconsigliere [--dossier CHEMIN]` : réconciliation ;
- `python -m reconsigliere importer [FICHIERS] [--sans-ia] [--modele haiku|sonnet] [--forcer]` : import de documents ;
- `python -m reconsigliere banc-ia [--modeles …]` : comparaison des modèles d'IA.

La fenêtre ([fenetre](fenetre.md)) appelle la même fonction `main` quand on clique sur « Lancer la réconciliation ».

## Ce qu'il lit

Le dossier de travail mémorisé (ou `--dossier`), puis tout ce que lisent les modules appelés.

## Ce qu'il écrit

Les sorties de [sorties](sorties.md) et `sorties/apprentissage.xlsx` ([apprentissage](apprentissage.md)) ; en mode `importer`, celles de [importation.pipeline](importation/pipeline.md).
Il écrit aussi le journal des étapes : les lignes `1/5` à `5/5`.

## Ce qui casse si on le change

- **Les préfixes `N/5`** font avancer la barre de progression de la fenêtre (`NB_ETAPES = 5` dans fenetre.py). Ajouter une étape
  impose de changer les deux.
- **L'ordre des étapes** : le rapprochement a besoin des transactions, des pièces et de la comptabilité déjà chargées ; la proposition
  de compte a besoin du partenaire trouvé.
- **La proposition de compte** est entourée d'un `try` : une erreur dans [exercices](exercices.md) ne bloque jamais la réconciliation.
  Garder cette protection. Même chose pour l'apprentissage ([apprentissage](apprentissage.md)), appelé juste après la proposition
  de compte, dans l'étape 4/5 ; une ligne « Apprentissage : … » résume les règles appliquées.

## Dépendances (automatique)

<!-- debut-auto -->
_Partie générée par `python outils/docs.py` à partir du code : ne pas la modifier à la main._

- **Fichier :** `src/reconsigliere/__main__.py` (127 lignes)
- **Dépend de :** [apprentissage](apprentissage.md), [chargement](chargement.md), [config](config.md), [corrections](corrections.md), [exercices](exercices.md), [importation.banc](importation/banc.md), [importation.ia](importation/ia.md), [importation.pipeline](importation/pipeline.md), [installation](installation.md), [pdf_extraction](pdf_extraction.md), [rapprochement](rapprochement.md), [sorties](sorties.md)
- **Utilisé par :** [fenetre](fenetre.md)
- **Bibliothèques externes :** aucune

Fonctions et classes publiques :

- `main` : Exécute la réconciliation dans le dossier de travail courant (config.RACINE).
<!-- fin-auto -->
