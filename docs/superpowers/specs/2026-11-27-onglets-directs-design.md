# Onglets directs : un élément par onglet

## Pourquoi

V ne s'y retrouve pas dans la fenêtre : les sous-onglets « État de la société » et « Exercices et changements » ont des
titres qui ne disent pas ce qu'ils contiennent, et il faut ouvrir un onglet pour trouver un autre rang d'onglets.
Demande (27.11.2026) : pas de regroupement « État de la société », chaque élément en onglet direct ; l'onglet Salaires doit
avoir sa place.

## Approches envisagées

1. Menu fixe à gauche, à un seul niveau, groupé Réconciliation / Société. Écarté par V : elle veut seulement de meilleurs titres
   et des éléments directs.
2. Garder des onglets en haut, mais à un seul niveau : chaque élément (brevets, projets, revenus, plan comptable,
   partenaires, année comptable) devient un onglet principal. **Retenu.**
3. Page d'accueil à tuiles. Écarté : un clic de plus pour chaque élément.

## Conception retenue

- Onglets principaux, dans cet ordre : Réconciliation, Documents, Salaires, Brevets, Projets, Revenus, Plan comptable,
  Partenaires, Année comptable, Apprentissage. Plus d'onglet « Assistant société » ni de sous-onglets société.
- Dix onglets ne tiennent pas sur une ligne d'onglets tkinter (ceux qui dépassent disparaissent). La rangée d'onglets
  tkinter est donc cachée et remplacée par une barre de boutons sur deux lignes, de largeur égale ; l'onglet choisi est
  surligné (fond bleu, texte blanc gras). Le carnet d'onglets tkinter reste dessous, le reste du code ne change pas.
- Chaque onglet commence par une phrase qui dit ce qu'il montre et d'où viennent les données.
- **Brevets** : chiffres des brevets (familles, dépôts, coûts capitalisables, coûts en charge), tableau par famille, points
  d'attention, boutons journal, tableau de bord, classeur, dossier (contenu de l'ancien « État de la société » sans projets
  ni revenus).
- **Projets** et **Revenus** : tableau des onglets Projets et Revenus de `societe.xlsx`, bouton pour ouvrir le classeur.
- **Plan comptable** et **Partenaires** : la liste de l'année choisie dans le référentiel (`exercices/AAAA`), avec un choix
  d'année ; sans année construite, une phrase dit quoi faire.
- **Année comptable** (ancien « Exercices et changements ») : mêmes fonctions ; intitulés « Année », « Modifications demandées
  pendant l'année », « Que faire avec cette année », « Voir les listes de l'année (Excel) ».
- **Salaires** : construit par `onglet_salaires.construire(parent, fenetre)` quand ce module existe (fil Salaires) ; sinon une
  phrase indique que la partie arrive.
- Taille de la fenêtre : calculée selon l'agrandissement de Windows et bornée à l'écran (avant : 920 × 880 points fixes, qui
  coupaient le bas de la fenêtre à 125–150 %).

## Non-buts

Pas de changement des données lues ou écrites, ni des sous-onglets de Documents.

## Laissé au constructeur

Libellés exacts des phrases d'explication ; largeur des colonnes.
