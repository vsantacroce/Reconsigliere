# pdf_extraction.py : lecture des factures

## À quoi il sert

Lit chaque facture ou reçu (PDF, PNG, JPG) et en tire ce qui sert au rapprochement : les montants, les dates, les IBAN, les numéros
de facture ou de référence. Les images et les scans sont lus par Tesseract OCR s'il est installé.

## Ce qu'il lit

- `entrees/01_factures` (et ses sous-dossiers) : les pièces à rapprocher.
- `entrees/04_comptabilite` : les PDF déjà comptabilisés, pour reconnaître une pièce déjà passée.
- Le programme Tesseract (`CHEMIN_TESSERACT` dans [config](config.md), sinon recherché automatiquement).

## Ce qu'il écrit

Rien sur le disque. Pour chaque pièce : nom, empreinte SHA-1 (deux fichiers identiques ne comptent qu'une fois), texte, `lisible`,
`montants` (du plus grand au plus petit), `dates`, `ibans`, `numeros`.

## Ce qui casse si on le change

- **Expressions de montant et de date** (`RE_MONTANT`, `RE_DATE`) : tout montant non reconnu fait perdre 50 points au score.
  Défaut connu : `100.-` n'est pas lu.
- **Ordre des montants** : le plus grand montant est considéré comme le total ; [rapprochement](rapprochement.md) donne 5 points de plus
  quand il correspond.
- **L'empreinte** sert à reconnaître les doublons et les pièces déjà en comptabilité.
- [importation.pages](importation/pages.md) réutilise ce module pour l'OCR : un changement de l'OCR touche aussi l'import des documents.

## Dépendances (automatique)

<!-- debut-auto -->
_Partie générée par `python outils/docs.py` à partir du code : ne pas la modifier à la main._

- **Fichier :** `src/reconsigliere/pdf_extraction.py` (104 lignes)
- **Dépend de :** [config](config.md), [outils](outils.md)
- **Utilisé par :** [__main__](__main__.md), [importation.pages](importation/pages.md)
- **Bibliothèques externes :** pypdf

Fonctions et classes publiques :

- `empreinte`
- `lire_texte`
- `lire_image` : Lit le texte d'une image si Tesseract OCR est installé, sinon renvoie une chaîne vide.
- `ocr_disponible`
- `analyser_piece`
- `analyser_dossier`
<!-- fin-auto -->
