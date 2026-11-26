# importation/banc.py : comparer Haiku et Sonnet

## À quoi il sert

`python -m reconsigliere banc-ia` fait classer les mêmes pages fictives, volontairement sans titre, par plusieurs modèles, et rend un
tableau : justesse, tokens, coût estimé. Sert à décider si Haiku suffit.

## Ce qu'il lit

Ses propres pages d'exemple (fictives) et la clé API via [importation.ia](ia.md).

## Ce qu'il écrit

Rien sur le disque ; le rapport est affiché.

## Ce qui casse si on le change

Les pages d'exemple doivent rester fictives (aucune pièce réelle dans le dépôt) et sans titre, sinon le banc ne mesure plus le cas où
l'IA est réellement appelée.

## Dépendances (automatique)

<!-- debut-auto -->
_Partie générée par `python outils/docs.py` à partir du code : ne pas la modifier à la main._

- **Fichier :** `src/reconsigliere/importation/banc.py` (67 lignes)
- **Dépend de :** [importation.ia](ia.md)
- **Utilisé par :** [__main__](../__main__.md)
- **Bibliothèques externes :** aucune

Fonctions et classes publiques :

- `comparer`
- `rapport`
<!-- fin-auto -->
