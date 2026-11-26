# importation/sorties.py : le classeur normalisé et la page lisible

## À quoi il sert

Écrit le résultat d'un import : un classeur Excel normalisé pour l'Assistant société et une page HTML pour le relire.

## Ce qu'il lit

Les tableaux et les métadonnées préparés par [importation.pipeline](pipeline.md).

## Ce qu'il écrit

- `entrees/06_societe/imports/AAAA/<document>.xlsx` avec les onglets `meta`, `pages`, `controles`, `plancomptable`, `grandlivre`,
  `bilan`, `compteresultat`, `annexe` (colonnes dans `COLONNES`). Si le fichier est ouvert dans Excel, écrit à côté avec l'heure.
- `sorties/imports/<document>.html`.

## Ce qui casse si on le change

- **`COLONNES`** est le contrat avec [exercices](../exercices.md) (`lire_imports`) : renommer un onglet ou une colonne vide le plan
  comptable ou le grand livre de l'exercice sans erreur visible.
- **Le dossier `imports/AAAA`** : l'année vient de l'exercice détecté. Ne jamais écrire dans `exercices/AAAA`, réservé aux référentiels versionnés.

## Dépendances (automatique)

<!-- debut-auto -->
_Partie générée par `python outils/docs.py` à partir du code : ne pas la modifier à la main._

- **Fichier :** `src/reconsigliere/importation/sorties.py` (125 lignes)
- **Dépend de :** [importation.classement](classement.md), [outils](../outils.md)
- **Utilisé par :** [importation.pipeline](pipeline.md)
- **Bibliothèques externes :** pandas

Fonctions et classes publiques :

- `ecrire_excel`
- `ecrire_html`
<!-- fin-auto -->
