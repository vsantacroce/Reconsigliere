# Changements

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
