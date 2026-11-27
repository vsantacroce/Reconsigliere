# onglet_apprentissage.py : l'onglet « Apprentissage » de la fenêtre

## À quoi il sert

Montre ce que le programme a appris de tes corrections de compte, calculé par [apprentissage](apprentissage.md) lors de la dernière
réconciliation :

- une ligne de résumé (corrections, règles actives, conditionnelles, en observation, suspendues, annulées, transactions où une règle
  a été appliquée, propositions du référentiel que tu as corrigées) et un court texte qui explique le fonctionnement ;
- le tableau **Règles apprises** (partenaire, compte, condition, état en couleur, fiabilité, compte du référentiel, pourquoi) ; un clic
  affiche le détail complet ;
- le tableau **Alertes** ; un clic affiche le message en entier ;
- les boutons **Annuler la règle**, **Rétablir la règle**, **Reporter dans l'exercice ouvert**, **Mes corrections**, **Détail (Excel)**.

## Ce qu'il lit

`sorties/apprentissage.xlsx` (via `apprentissage.lire_sortie`). Si le fichier n'existe pas encore, l'onglet invite à lancer une réconciliation.

## Ce qu'il écrit

- Annuler / rétablir : une ligne ajoutée ou retirée dans la feuille `regles_apprises` de `mes_corrections.xlsx`
  ([corrections](corrections.md)). L'effet arrive au lancement suivant ; la ligne est marquée « annulée au prochain lancement ».
- Sans année construite, le bouton Reporter explique qu'il faut d'abord la construire dans l'onglet « Année comptable ».
- Reporter : un changement dans le référentiel de l'exercice ouvert ([exercices](exercices.md)), après confirmation. Seules les règles
  actives à un seul compte peuvent être reportées.

## Ce qui casse si on le change

- Les noms de colonnes lus dans `sorties/apprentissage.xlsx` doivent suivre ceux écrits par [apprentissage](apprentissage.md).
- Si `mes_corrections.xlsx` est ouvert dans Excel, l'écriture échoue : l'onglet affiche « Ferme mes_corrections.xlsx dans Excel ».
- L'onglet est actualisé par `_onglet_change` de [fenetre](fenetre.md), repéré par son widget.
- Hauteur des tableaux (6 et 4 lignes) choisie pour tenir dans la fenêtre de 920 × 880.

## Dépendances (automatique)

<!-- debut-auto -->
_Partie générée par `python outils/docs.py` à partir du code : ne pas la modifier à la main._

- **Fichier :** `src/reconsigliere/onglet_apprentissage.py` (208 lignes)
- **Dépend de :** [apprentissage](apprentissage.md), [config](config.md), [corrections](corrections.md), [exercices](exercices.md)
- **Utilisé par :** [fenetre](fenetre.md)
- **Bibliothèques externes :** aucune

Fonctions et classes publiques :

- `OngletApprentissage`
- `construire`
<!-- fin-auto -->
