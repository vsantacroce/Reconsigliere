# Reconsigliere

*Le consigliere de ta compta. Il sait qui a payé qui, et il garde les preuves.*

Réconcilie les transactions bancaires avec les pièces PDF et la comptabilité.
L'outil retrouve le partenaire de chaque transaction, y attache le bon PDF, le renomme de façon logique et isole ce qui manque encore dans la comptabilité.

## Installation sur Windows

1. Installe Python 3.12 depuis https://www.python.org/downloads/ en cochant « Add python.exe to PATH ».
   Ou, dans un terminal : `winget install --id Python.Python.3.12 -e`.
2. Décompresse ce dossier où tu veux, par exemple dans `Documents`.
3. Double-clique sur `Reconsigliere.bat`. Le premier lancement installe les bibliothèques (une minute), puis la fenêtre s'ouvre.

Sous Ubuntu : `sudo apt install python3-tk python3-venv` une fois, puis `./reconsigliere.sh`.

## Utilisation avec la fenêtre

1. Au premier lancement, la fenêtre propose de créer le dossier de travail dans `Documents\Reconsigliere`.
   Le bouton « Choisir l'emplacement… » permet d'en choisir un autre. Les dossiers d'entrée et de sortie y sont créés automatiquement, et le choix est mémorisé.
2. Clique sur « Ouvrir » à côté de chaque dossier et dépose tes fichiers. Le nombre de fichiers s'affiche à côté.
3. Clique sur « Lancer la réconciliation ». La barre de progression montre les 5 étapes.
4. Ouvre les résultats avec les boutons du bas : rapport en page, rapport Excel, pièces à comptabiliser.
5. Corrige ce qui doit l'être avec « Mes corrections », puis relance.

Le code et tes données sont séparés : le dossier de travail peut être n'importe où, hors du dossier du programme et hors de GitHub.
Si tu avais déjà des fichiers dans le dossier `entrees` du programme, choisis le dossier du programme lui-même comme emplacement : il est reconnu et utilisé tel quel.

## Utilisation sans fenêtre

```bash
python -m reconsigliere --dossier "C:\Users\moi\Documents\Reconsigliere"
```

Sans `--dossier`, le dossier choisi dans la fenêtre est utilisé.

## Dossiers d'entrée

Chemins relatifs au dossier de travail.

| Dossier | Contenu |
|---|---|
| `entrees/01_factures` | Toutes les factures, reçus et notes de frais, en PDF, PNG ou JPG |
| `entrees/02_transactions_a_reconcilier` | Excel ou CSV des transactions bancaires à réconcilier |
| `entrees/03_infos_bancaires` | Relevés et Excel qui détaillent les transactions |
| `entrees/04_comptabilite` | Liste Excel des pièces comptabilisées, et leurs PDF dans `pdf` |
| `entrees/05_mes_corrections` | Ton fichier de corrections, créé au premier lancement |

## Sorties

| Fichier | Contenu |
|---|---|
| `sorties/reconciliation.xlsx` | Une ligne par transaction, les PDF sans transaction et un résumé |
| `sorties/reconciliation.html` | La même chose en page interactive, avec recherche, filtres et liens vers les PDF |
| `sorties/pdf_renommes` | Chaque pièce retrouvée, nommée `AAAA-MM-JJ_Partenaire_Montant_Numero` avec son extension d'origine |
| `sorties/a_comptabiliser` | Seulement les pièces absentes de la comptabilité |

## Statuts

- **Comptabilisé** : la transaction est déjà dans la comptabilité.
- **À comptabiliser** : le PDF est trouvé avec certitude, il reste à le comptabiliser.
- **À confirmer** : un PDF est proposé, mais le lien est incertain.
- **PDF manquant** : aucune pièce trouvée.
- **Expliqué sans pièce** : tu as expliqué la transaction, par exemple des frais bancaires.

## Corriger et faire avancer

Dans `mes_corrections.xlsx` :

- **Feuille partenaires** : un mot du libellé bancaire et le partenaire à utiliser. Exemple : `SWISSCOM` donne `Swisscom`.
- **Feuille transactions** : l'`id_transaction` copié depuis la sortie, puis le partenaire, le PDF à lier, une explication ou un statut forcé (`Comptabilise`, `Sans piece`, `A comptabiliser`, `Ignorer`).

Tes corrections passent toujours avant le rapprochement automatique.

## Images et scans

Les PNG, JPG et PDF scannés ne contiennent pas de texte lisible directement.
Pour qu'ils soient lus automatiquement, installe Tesseract OCR :

```bash
winget install --id UB-Mannheim.TesseractOCR -e
```

Sans Tesseract, ces pièces sont quand même renommées, mais il faut les lier à la main dans `mes_corrections.xlsx`.

## Réglages

Les tolérances de date et de montant, la devise et les noms de colonnes reconnus sont dans `src/reconsigliere/config.py`.

## Confidentialité

Les dossiers `entrees` et `sorties` sont exclus de Git par `.gitignore`. Seuls les scripts vont sur GitHub.

## Tests

```bash
python -m unittest discover -s tests -v
```
