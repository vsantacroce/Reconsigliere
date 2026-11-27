# Changements

## 0.9.0 — salaires

- Nouvel onglet principal « Salaires », juste après « Documents » : choisir l'exercice, lire le classeur de paie, voir la synthèse
  par employé (dû, payé dans l'année, reporté, payé l'année suivante, écart) et les restes de l'année précédente ;
  boutons Générer, Ouvrir, Enregistrer sous….
- Nouveaux dossiers `entrees/08_salaires` (classeur de paie au format 2025) et `entrees/08_salaires/fiches` (une fiche par exercice).
- La fiche garde tes corrections (exercice, part de salaire, imputation, preuve, lignes ajoutées) quand le classeur est relu.
- Nouvelle sortie `sorties/salaires/Reconciliation_salaires_AAAA.xlsx` : synthèse à formules, feuilles des virements N et N+1,
  reste N−1, points à vérifier.
- Nouvelle commande `python -m reconsigliere salaires AAAA [--lire]`.
- 36 tests ajoutés (`tests/test_salaires.py`).

## 0.8.0 — apprentissage visible

- Nouvelle colonne `compte` dans la feuille transactions de `mes_corrections.xlsx` : corriger le compte d'une transaction.
- Après 3 corrections identiques pour un partenaire, le programme applique seul ce compte aux transactions suivantes
  (`SEUIL_REGLE` dans `config.py`). Si les corrections divergent, il cherche le critère qui sépare les comptes (date du changement,
  mot du libellé, seuil de montant) ; sans critère, la règle est suspendue et une alerte demande de trancher.
- Alertes : référentiel d'exercice qui range le partenaire sur un autre compte (avec les autres partenaires sur ce même compte),
  compte absent du plan comptable, correction contraire, « mon analyse se trompait ».
- Nouvel onglet « Apprentissage » : résumé, règles (condition, état, fiabilité, compte du référentiel), alertes ; boutons
  Annuler la règle, Rétablir la règle, Reporter dans l'exercice ouvert.
- Nouvelle sortie `sorties/apprentissage.xlsx` ; nouvelle colonne `origine_compte` dans `sorties/reconciliation.xlsx`.
- Tout est recalculé à chaque réconciliation ; les annulations sont gardées dans la feuille `regles_apprises`.
- 25 tests ajoutés (`tests/test_apprentissage.py`).

## 0.7.0 — onglet Documents

- Nouvel onglet principal « Documents » entre « Réconciliation » et « Assistant société » ; le bouton
  « Importer les documents » et « Réglages IA… » y déménagent.
- Vue d'ensemble : chaque fichier importé avec son exercice, ses pages, les sections trouvées
  (« Bilan p.1 · Grand livre p.3–4 »), comment chaque page a été reconnue et un état ✓ / ⚠.
- Un sous-onglet par type (Plan comptable, Bilan, Compte de résultat, Grand livre, Annexe, Autres pages) :
  sources et pages, contrôles (équilibre du grand livre, actifs = passifs, codes en double, lignes sans compte,
  partenaires lus), tableau du résultat ; bilan et compte de résultat en arbre avec l'exercice précédent.
- Filtre par exercice ; boutons pour ouvrir le document source, le classeur et la page lisible.
- L'onglet Assistant société n'est plus repéré par sa position.

## Documentation vivante (sans changement du programme)

- Nouveau dossier `docs/` : vue d'ensemble avec schéma du flux, une page par module (à quoi il sert, ce qu'il lit, ce qu'il écrit,
  ce qui casse si on le change), carte des modules, fichiers lus et écrits, journal des décisions, où le programme apprend.
- `outils/docs.py` régénère la partie automatique de chaque page depuis le code et vérifie que la documentation suit le code.
- Contrôle GitHub « Documentation » : une modification d'un module sans mise à jour de sa page ne passe pas.
- `CLAUDE.md` : la règle pour toute session de Claude qui travaille sur le dépôt.
- 12 tests ajoutés (`tests/test_docs.py`).

## 0.6.0 — import de documents comptables

- Nouveau dossier `entrees/07_documents` et bouton « Importer les documents » : bilan, compte de résultat,
  grand livre, plan comptable, annexe, en PDF, photo ou Excel, plusieurs états dans un même document.
- Classement page par page par règles locales, passe de continuité, IA seulement pour les pages indécises
  (extrait court, Haiku par défaut, Sonnet en option), choix manuel sans clé.
- Classeur normalisé par document dans `entrees/06_societe/imports/AAAA` pour l'Assistant société,
  page lisible dans `sorties/imports`, contrôles (grand livre équilibré, actifs = passifs).
- `python -m reconsigliere importer` et `python -m reconsigliere banc-ia` (comparaison Haiku / Sonnet).
- Les dates AAAA-MM-JJ ne sont plus lues avec le jour et le mois inversés.
- Les réglages (dossier, clé API, modèle) sont conservés ensemble.

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
