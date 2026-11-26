# Changements

## 0.5.0 — exercices validés et verrouillés

- Deux parties dans la fenêtre : « Réconciliation » et « Assistant société » (sous-onglets État de la société, Exercices et changements).
- Nouveau module `exercices.py` : un référentiel par exercice (plan comptable, partenaires et compte habituel, brevets, projets, revenus) dans `entrees/06_societe/exercices/AAAA`.
- Construire depuis les fichiers (`imports/AAAA` au format du pipeline d'import, classeur des brevets au 31.12, `societe.xlsx`), valider et verrouiller (lecture seule + empreinte SHA-256), ouverture automatique de l'exercice suivant, réouverture avec motif obligatoire.
- Demandes de changement datées et motivées (ajout, modification, retrait), gardées dans l'onglet Changements ; écarts avec l'exercice précédent ; suggestions depuis les fichiers déposés, applicables ligne par ligne.
- Détection d'un référentiel validé modifié à la main.
- Réconciliation : colonne « Compte proposé » selon le référentiel de l'exercice de chaque transaction (par partenaire, sinon par le libellé).
- 9 tests ajoutés (`tests/test_exercices.py`), sur des données fictives.

## 0.4.0 — état de la société

- Nouvel onglet « Société » dans la fenêtre : familles de brevets actives, dépôts par pays, coûts capitalisables et en charge, projets capitalisables, sources de revenus, points d'attention.
- Nouveau dossier `entrees/06_societe` : Reconsigliere lit le classeur des brevets tel qu'il est tenu (onglet de la liste et onglets de coûts par année), sans ressaisie.
- `societe.xlsx` créé au premier lancement avec les onglets Projets, Revenus et Journal ; bouton « Ajouter au journal… ».
- Page `sorties/societe.html` : tableau de bord complet (brevets par famille, coûts par année, projets, revenus, journal).
- Ligne de commande : `python -m reconsigliere.societe`.
- 7 tests ajoutés (`tests/test_societe.py`), sur des données fictives.
- La fenêtre passe à 920 × 880 pour loger les onglets. La réconciliation n'a pas changé.

## 0.3.0 — installé une fois, mis à jour tout seul

- `installer.ps1` : installation Windows en une commande PowerShell, sans droits administrateur. Installe Python 3.12 si besoin (winget, sinon python.org), télécharge le programme dans `%LOCALAPPDATA%\Reconsigliere`, installe les bibliothèques dans un environnement isolé, crée les icônes du bureau et du menu Démarrer.
- `windows/demarrer.pyw` : lancé par l'icône. À chaque ouverture, il compare la version installée au dernier commit de `main` sur GitHub, télécharge la nouvelle version si besoin, réinstalle les bibliothèques si `requirements.txt` a changé, puis ouvre la fenêtre. Hors ligne, la version installée s'ouvre.
- `windows/desinstaller.ps1` : retire le programme et les icônes, garde le dossier de travail.
- Icône Reconsigliere pour la fenêtre, le bureau et le menu Démarrer.
- La fenêtre affiche le commit installé.

## 0.2.1 — nouveau nom : Reconsigliere

- Le logiciel s'appelle Reconsigliere partout : fenêtre, rapport HTML, README, dossier du programme.
- Le lanceur Windows s'appelle `Reconsigliere.bat`, celui d'Ubuntu `reconsigliere.sh`.
- Le module Python s'appelle `reconsigliere` : `python -m reconsigliere --dossier ...`.
- Le dossier de travail et ses réglages ne changent pas.

## 0.2.0 — interface en fenêtre

- Nouvelle fenêtre (`src/reconsigliere/fenetre.py`, tkinter, inclus dans Python pour Windows) : choix du dossier de travail, création automatique des dossiers, compteurs de fichiers, bouton Lancer avec barre de progression et journal, boutons d'ouverture des résultats.
- Le dossier de travail (entrees + sorties) est séparé du code et mémorisé dans `%APPDATA%\Reconsigliere\reglages.json` (Windows) ou `~/.config/Reconsigliere/reglages.json` (Linux).
- `config.definir_racine()` permet de changer de dossier de travail ; `installation.py` crée les dossiers et leurs LISEZMOI sans jamais écraser un fichier existant.
- `Reconsigliere.bat` vérifie Python, installe les bibliothèques une seule fois, puis ouvre la fenêtre sans console noire. Nouveau `reconsigliere.sh` pour Ubuntu.
- Message clair quand `reconciliation.xlsx` est ouvert dans Excel, au lieu d'un plantage.
- OCR Tesseract sous Windows : plus de fenêtre noire qui clignote pour chaque image.
- `xlrd` ajouté aux dépendances : les fichiers `.xls` ne font plus planter le programme.
- 4 tests ajoutés (`tests/test_installation.py`).
- La logique de rapprochement n'a pas changé.
