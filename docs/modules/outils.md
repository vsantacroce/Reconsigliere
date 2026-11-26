# outils.py : lecture des textes, montants et dates

## À quoi il sert

Petites fonctions partagées : mettre un texte en minuscules sans accents (`normaliser`), lire un montant écrit à la suisse
(`en_montant` : `1'234.50`, `1 234,50`, `-12.00`…), lire une date (`en_date` : `31.12.2024`, `2024-12-31`, date Excel),
fabriquer un nom de fichier sûr (`nom_de_fichier_sur`).

## Ce qu'il lit

Des valeurs passées par les autres modules. Aucun fichier.

## Ce qu'il écrit

Rien sur le disque.

## Ce qui casse si on le change

Ces fonctions sont utilisées partout : la reconnaissance des colonnes, le score du rapprochement, le classement des pages importées,
les identifiants de transaction.

- `normaliser` : une transaction est identifiée par `date | montant | libellé normalisé` (voir [chargement](chargement.md)).
  Changer la normalisation change les identifiants : les lignes de `mes_corrections.xlsx` (feuille transactions) ne retrouvent plus leur transaction.
- `en_montant` et `en_date` : une erreur de lecture (jour et mois inversés, séparateur de milliers mal compris) se propage dans le
  rapprochement, l'import des documents et les exercices. La 0.6.0 a corrigé l'inversion jour/mois des dates `AAAA-MM-JJ`.
- `nom_de_fichier_sur` : détermine le nom des PDF renommés et des classeurs importés.

## Dépendances (automatique)

<!-- debut-auto -->
_Partie générée par `python outils/docs.py` à partir du code : ne pas la modifier à la main._

- **Fichier :** `src/reconsigliere/outils.py` (69 lignes)
- **Dépend de :** aucun autre module du programme
- **Utilisé par :** [chargement](chargement.md), [corrections](corrections.md), [importation.classement](importation/classement.md), [importation.continuite](importation/continuite.md), [importation.extracteurs](importation/extracteurs.md), [importation.ia](importation/ia.md), [importation.pages](importation/pages.md), [importation.pipeline](importation/pipeline.md), [importation.sorties](importation/sorties.md), [pdf_extraction](pdf_extraction.md), [rapprochement](rapprochement.md), [sorties](sorties.md)
- **Bibliothèques externes :** pandas

Fonctions et classes publiques :

- `sans_accents`
- `normaliser` : Minuscules, sans accents, espaces simples.
- `en_montant` : Convertit 1'234.50, 1 234,50, -89.90 CHF, etc. en nombre.
- `en_date`
- `nom_de_fichier_sur` : Rend un texte utilisable dans un nom de fichier Windows.
<!-- fin-auto -->
