# importation/pages.py : découper un document en pages

## À quoi il sert

Première étape de l'import : transforme un document en une liste de pages, chacune avec son texte. Une page PDF, une image, ou une
feuille Excel/CSV (alors la page garde aussi son tableau, avec l'en-tête retrouvé). Une page PDF avec moins de 40 caractères de texte
est considérée comme scannée et passe par l'OCR Tesseract.

## Ce qu'il lit

Le document importé (`.pdf`, images `.png .jpg .jpeg .tif .tiff .bmp`, tableurs `.xlsx .xlsm .xls .csv`) et Tesseract via
[pdf_extraction](../pdf_extraction.md).

## Ce qu'il écrit

Rien sur le disque (une image temporaire pour l'OCR, effacée). Rend des `Page(numero, texte, tableau, lisible…)`.

## Ce qui casse si on le change

- **`EXTENSIONS`** décide quels fichiers de `entrees/07_documents` sont importés.
- **`SEUIL_TEXTE`** : trop haut, des pages texte partent à l'OCR (lent, moins fiable) ; trop bas, des scans restent sans texte.
- **`MOTS_ENTETE`** sert à trouver la ligne d'en-tête d'une feuille Excel : une feuille dont l'en-tête n'est pas reconnu est lue de travers
  par les extracteurs.

## Dépendances (automatique)

<!-- debut-auto -->
_Partie générée par `python outils/docs.py` à partir du code : ne pas la modifier à la main._

- **Fichier :** `src/reconsigliere/importation/pages.py` (147 lignes)
- **Dépend de :** [config](../config.md), [outils](../outils.md), [pdf_extraction](../pdf_extraction.md)
- **Utilisé par :** [importation.classement](classement.md), [importation.continuite](continuite.md), [importation.extracteurs](extracteurs.md), [importation.pipeline](pipeline.md)
- **Bibliothèques externes :** pandas, pypdf

Fonctions et classes publiques :

- `Page`
- `ocr_defaut` : Image : Tesseract direct. Page PDF scannée : Tesseract sur les images de la page.
- `lire_pages`
<!-- fin-auto -->
