# Reconsigliere

*Le consigliere de ta compta. Il sait qui a payé qui, et il garde les preuves.*

Réconcilie les transactions bancaires avec les pièces PDF et la comptabilité.
L'outil retrouve le partenaire de chaque transaction, y attache le bon PDF, le renomme de façon logique et isole ce qui manque encore dans la comptabilité.

## Installation sur Windows (une seule fois)

1. Ouvre le menu Démarrer, tape `PowerShell` et ouvre « Windows PowerShell ».
2. Colle cette ligne puis appuie sur Entrée :

   ```powershell
   irm https://raw.githubusercontent.com/vsantacroce/reconsigliere/main/installer.ps1 | iex
   ```

3. Attends la fin (deux à cinq minutes la première fois). Reconsigliere s'ouvre tout seul.

Ensuite, double-clique sur l'icône **Reconsigliere** du bureau ou du menu Démarrer.
À chaque ouverture, Reconsigliere vérifie sur GitHub s'il existe une nouvelle version et l'installe tout seul.
Sans internet, la version déjà installée s'ouvre.

- Le programme est installé dans `%LOCALAPPDATA%\Reconsigliere`, sans droits administrateur.
- Tes relevés, factures et résultats restent dans ton dossier de travail (`Documents\Reconsigliere` par défaut). Ni la mise à jour ni la désinstallation n'y touchent.
- Pour désinstaller : menu Démarrer › Reconsigliere › Désinstaller Reconsigliere.
- En cas de souci de mise à jour, le détail est dans `%LOCALAPPDATA%\Reconsigliere\journal.txt`.

Pour développer, sans installation : `Reconsigliere.bat` (Windows) ou `./reconsigliere.sh` (Ubuntu, après `sudo apt install python3-tk python3-venv`) lancent la fenêtre depuis ce dossier.

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

## Import de documents comptables

Dépose un bilan, un compte de résultat, un grand livre, un plan comptable ou une annexe dans
`entrees/07_documents` (PDF, photo ou Excel ; un même PDF peut tout contenir), puis clique sur
« Importer les documents » ou lance `python -m reconsigliere importer`.

1. Chaque page (ou feuille Excel) est lue : texte du PDF, Tesseract pour les photos et les scans.
2. Chaque page est classée par des règles locales : titres, mots-clés, en-têtes de colonnes.
3. Une passe de continuité rattache les pages sans titre à la section en cours (report de solde,
   mêmes en-têtes, « Page 2/12 », lignes d'écritures datées).
4. Les seules pages encore indécises vont à l'IA, avec un extrait de 2000 caractères au plus.
   Sans clé API, la fenêtre te les montre et tu choisis le type.
5. Chaque section passe dans son extracteur, puis des contrôles vérifient le résultat :
   grand livre équilibré, actifs = passifs, pages illisibles ou à vérifier.

Résultats : un classeur normalisé par document dans `entrees/06_societe/imports/AAAA`
(onglets `meta`, `pages`, `controles`, `plancomptable`, `grandlivre`, `bilan`, `compteresultat`,
`annexe`), lu par l'Assistant société, et une page lisible dans `sorties/imports`.
Un document déjà importé (même contenu) n'est pas réimporté, sauf avec `--forcer`.

Le partenaire de chaque écriture n'est fiable que depuis un export Excel du grand livre : dans un PDF,
il reste dans le libellé.

### IA

- Clé et modèle : bouton « Réglages IA… », ou variables `ANTHROPIC_API_KEY` et `RECONSIGLIERE_MODELE`.
- Modèle `haiku` (par défaut, le moins cher) ou `sonnet`.
- `python -m reconsigliere banc-ia` fait classer 12 pages ambiguës fictives par les deux modèles et
  affiche le nombre de bonnes réponses, les tokens et le coût de chacun.
- `python -m reconsigliere importer --sans-ia` n'appelle jamais l'IA.

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
