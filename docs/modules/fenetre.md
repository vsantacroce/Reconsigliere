# fenetre.py : la fenêtre du programme

## À quoi il sert

L'interface que tu utilises sous Windows (tkinter, inclus dans Python ; sous Ubuntu il faut `python3-tk`). Dix onglets principaux,
un par élément, choisis dans une barre de boutons sur deux lignes (ordre, titres et phrases d'explication dans
[onglets_societe](onglets_societe.md)) :

- **Réconciliation** : choix du dossier de travail, compteurs de fichiers par dossier, bouton « Lancer la réconciliation »
  avec barre de progression et journal, boutons d'ouverture des résultats.
- **Documents** : construit par [onglet_documents](onglet_documents.md) ; « Importer les documents », réglages IA, vue d'ensemble
  des fichiers importés et un sous-onglet par type de document. La fenêtre garde la logique d'import (`_importer`, `_reglages_ia`,
  choix manuel du type de page).
- **Salaires** : construit par [onglet_salaires](onglet_salaires.md) ; exercice, lecture du classeur de paie,
  synthèse par employé, Générer, Ouvrir, Enregistrer sous….
- **Brevets** : chiffres des brevets, tableau par famille, points d'attention, journal, tableau de bord, classeur et dossier société.
- **Projets**, **Revenus**, **Plan comptable**, **Partenaires** : tableaux construits par [onglets_societe](onglets_societe.md).
- **Année comptable** : construire l'année, voir ses listes, valider et verrouiller, rouvrir, demander une modification, écarts,
  suggestions.
- **Apprentissage** : construit par [onglet_apprentissage](onglet_apprentissage.md) ; règles apprises de tes corrections, alertes,
  annuler, rétablir, reporter dans l'année ouverte.

Les petites fenêtres `Journal`, `Changement` et `Ecarts` sont dans le même fichier.

## Ce qu'il lit

Le dossier de travail mémorisé ([installation](installation.md)), les imports via [importation.catalogue](importation/catalogue.md), l'état de la société ([societe](societe.md)) et des exercices
([exercices](exercices.md)) pour les afficher.

## Ce qu'il écrit

Rien lui-même : chaque bouton appelle un autre module (réconciliation via [__main__](__main__.md), import via
[importation.pipeline](importation/pipeline.md), journal et tableau de bord via [societe](societe.md), référentiels via
[exercices](exercices.md), réglages via [installation](installation.md)).

## Ce qui casse si on le change

- **Travail en arrière-plan** : la réconciliation et l'import tournent dans un fil séparé et parlent à la fenêtre par une file de messages.
  Toucher directement aux éléments de la fenêtre depuis ce fil fait planter tkinter de façon aléatoire.
- **Barre de progression** : `NB_ETAPES = 5` doit suivre les lignes `N/5` de [__main__](__main__.md).
- **Imports tardifs** : pandas et le pipeline d'import ne sont chargés qu'au clic, pour que la fenêtre s'ouvre vite. Les remonter en
  haut du fichier ralentit l'ouverture.
- **Choix manuel du type de page** (`_demander_type`) : appelé par le pipeline quand ni les règles ni l'IA ne savent classer une page.
- **Onglets repérés par leur clé** : `self.cadres` (clé → cadre) et `self.actualisations` (clé → actualisation). Un nouvel onglet
  s'ajoute dans `ONGLETS` et `EXPLICATIONS` de [onglets_societe](onglets_societe.md), puis dans ces deux dictionnaires.
- **Barre d'onglets** : la rangée d'onglets de tkinter est cachée (style `SansOnglets.TNotebook`) car dix onglets ne tiennent pas
  sur une ligne ; les boutons `Onglet.TRadiobutton` la remplacent. Remettre la rangée d'onglets fait disparaître ceux qui dépassent.
- **Taille** : calculée par `onglets_societe.geometrie` selon l'agrandissement de Windows et bornée à l'écran. Les pages Réconciliation,
  Brevets et Année comptable sont dans un cadre qui défile (`_page_defilante`) ; la hauteur des lignes de tableau suit la police.
  Revenir à une taille fixe en pixels coupe le bas de la fenêtre à 125–150 %.
- C'est le point d'entrée de l'icône Windows (via [windows.demarrer](windows/demarrer.md)) : une erreur à l'import de ce module
  empêche le programme de s'ouvrir.

## Dépendances (automatique)

<!-- debut-auto -->
_Partie générée par `python outils/docs.py` à partir du code : ne pas la modifier à la main._

- **Fichier :** `src/reconsigliere/fenetre.py` (1137 lignes)
- **Dépend de :** [__main__](__main__.md), [config](config.md), [exercices](exercices.md), [importation.classement](importation/classement.md), [importation.ia](importation/ia.md), [importation.pipeline](importation/pipeline.md), [installation](installation.md), [onglet_apprentissage](onglet_apprentissage.md), [onglet_documents](onglet_documents.md), [onglet_salaires](onglet_salaires.md), [onglets_societe](onglets_societe.md), [societe](societe.md)
- **Utilisé par :** aucun module (point d'entrée)
- **Bibliothèques externes :** aucune

Fonctions et classes publiques :

- `Fenetre`
- `Journal` : Petite fenêtre pour ajouter un événement au journal de la société.
- `Changement` : Demande de changement : ajout, modification ou retrait d'un élément d'une liste du référentiel.
- `Ecarts` : Liste des écarts entre deux exercices.
- `lancer`
<!-- fin-auto -->
