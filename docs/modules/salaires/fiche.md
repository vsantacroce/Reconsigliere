# salaires.fiche

## À quoi il sert

La fiche de salaires d'un exercice (`entrees/08_salaires/fiches/fiche_salaires_AAAA.xlsx`) : le net dû par employé et chaque virement avec l'exercice qu'il règle et sa part de salaire. C'est le seul endroit où l'on corrige un classement. À chaque relecture du classeur de paie, les corrections sont gardées : une valeur qui diffère de ce que le lecteur avait proposé (onglet masqué `auto`) est une correction ; la colonne `preuve`, les lignes ajoutées à la main et l'onglet `points` sont toujours gardés.

## Ce qu'il lit

La fiche existante de l'exercice (onglets `du`, `virements`, `points`, `auto`).

## Ce qu'il écrit

La fiche de l'exercice. Feuille `bonus` (à remplir à la main, gardée à chaque relecture) : `employe`, `brut`, `part_salariee`, `net_a_payer`, `source` ; c'est le bonus de cet exercice, payé l'année suivante. Dans la feuille `du`, deux colonnes viennent du classeur de paie et sont remplacées à chaque relecture : `reste_prec_classeur` (reste de l'année précédente selon l'onglet FRAIS, vide si l'onglet manque) et `note_classeur` (tes notes « Nom — Note »). Cases jaunes : ce que tu peux corriger (`net_du`, `exercice`, `part_salaire`, `imputation`) et `preuve`.

## Ce qui casse si on le change

- Les noms de colonnes sont le contrat avec [salaires.lecture_paie](lecture_paie.md) et [salaires.reconciliation](reconciliation.md) (voir [données](../../donnees.md)).
- L'identifiant d'un virement (`AAAAMMJJ-employé-montant-rang`) relie une correction à son virement : changer sa forme fait perdre les corrections déjà faites.
- Supprimer l'onglet `auto` fait passer chaque valeur pour une correction (rien ne serait plus mis à jour par une relecture).
- Fiche ouverte dans Excel : écriture refusée avec le message « Ferme … dans Excel ».

## Dépendances (automatique)

<!-- debut-auto -->
_Partie générée par `python outils/docs.py` à partir du code : ne pas la modifier à la main._

- **Fichier :** `src/reconsigliere/salaires/fiche.py` (213 lignes)
- **Dépend de :** [config](../config.md)
- **Utilisé par :** [onglet_salaires](../onglet_salaires.md), [salaires.lecture_paie](lecture_paie.md), [salaires.reconciliation](reconciliation.md)
- **Bibliothèques externes :** openpyxl

Fonctions et classes publiques :

- `FichierOuvert` : Le fichier est ouvert dans Excel : impossible de l'écrire.
- `vide` : Fiche d'un exercice dont le classeur de paie n'est pas encore là.
- `chemin_fiche`
- `identifiants` : Donne à chaque virement un identifiant stable : AAAAMMJJ-employé-montant-rang.
- `valeurs_auto` : Valeurs proposées par le lecteur, par identifiant de virement et par employé (net dû).
- `fusionner` : Nouvelle lecture du classeur de paie, en gardant les corrections et les preuves de l'ancienne fiche.
- `ecrire`
- `lire`
<!-- fin-auto -->
