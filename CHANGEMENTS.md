# Changements

## 0.5.0 — import de documents comptables

- Nouveau dossier `entrees/07_documents` et bouton « Importer les documents » : bilan, compte de résultat,
  grand livre, plan comptable, annexe, en PDF, photo ou Excel, plusieurs états dans un même document.
- Classement page par page par règles locales, passe de continuité, IA seulement pour les pages indécises
  (extrait court, Haiku par défaut, Sonnet en option), choix manuel sans clé.
- Classeur normalisé par document dans `entrees/06_societe/imports/AAAA` pour l'Assistant société,
  page lisible dans `sorties/imports`, contrôles (grand livre équilibré, actifs = passifs).
- `python -m reconsigliere importer` et `python -m reconsigliere banc-ia` (comparaison Haiku / Sonnet).
- Les dates AAAA-MM-JJ ne sont plus lues avec le jour et le mois inversés.
- Les réglages (dossier, clé API, modèle) sont conservés ensemble.

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
