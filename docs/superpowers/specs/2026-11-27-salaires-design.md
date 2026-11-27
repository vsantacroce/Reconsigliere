# Réconciliation des salaires : conception

Date : 27.11.2026. Approche validée par V (option 1 : une fiche intermédiaire par exercice).

## Intention

V doit remettre à sa fiduciaire, pour chaque exercice et chaque employé, la preuve que le salaire net dû a été payé : ce qui
était dû, ce qui a été payé pendant l'année, ce qui est resté dû et quand ce reste a été payé, avec la liste des virements et
de leurs preuves. Ses classeurs de paie actuels contiennent tout, mais sont trop compliqués pour la fiduciaire. Deux classeurs
de réconciliation (2024 et 2025) ont été produits à la main avec V, puis validés : le programme doit les reproduire, les ouvrir
et les enregistrer où V veut.

## Buts

- Onglet « Salaires » dans la fenêtre : choix de l'exercice, boutons **Lire le classeur de paie**, **Générer**, **Ouvrir**,
  **Ouvrir la fiche**, **Enregistrer sous…**, résumé (dû, payé, reporté, payé l'année suivante, reste, points à vérifier).
- Commande `python -m reconsigliere salaires AAAA [--lire]`.
- Une **fiche intermédiaire par exercice**, `entrees/08_salaires/fiches/fiche_salaires_AAAA.xlsx`, que V peut corriger ;
  ses corrections sont gardées quand le classeur de paie est relu.
- Un lecteur du **classeur de paie au format 2025** (onglets EMPLOYES, ANNEE, PAYé, Bank Transactions AAAA) qui remplit la fiche.
- Un générateur qui écrit `sorties/salaires/Reconciliation_salaires_AAAA.xlsx`, de même forme que les deux fichiers validés.

## Non-buts

- Pas de calcul du salaire (brut, cotisations, impôt à la source) : le net dû vient du classeur de paie de V.
- Pas de lecteur pour l'ancien classeur 2024 : sa fiche est fournie une fois, hors dépôt (elle contient des données réelles).
- Pas de lien avec le verrouillage des exercices (`exercices.py`) dans cette version.
- Pas de rapprochement automatique avec les relevés de `02_transactions_a_reconcilier` : les virements viennent du classeur de paie.

## Anti-buts

- Aucune donnée réelle dans le dépôt : tests sur un classeur de paie fictif construit par les tests.
- Une correction de V dans la fiche n'est jamais écrasée en silence.
- La synthèse ne contient que des formules qui renvoient aux feuilles de virements : la fiduciaire doit pouvoir remonter
  de chaque total à chaque virement.

## Approches considérées

1. **Fiche intermédiaire par exercice** (choisie par V) : lecteur du format 2025 → fiche → Excel. Les découpages
   (frais mêlés au salaire, prêt, achat classé « régularisation ») sont des données que V corrige, pas du code.
2. Un lecteur spécial par classeur, sans intermédiaire : moins de fichiers, mais chaque correction demande de changer le programme.
3. Saisie normalisée seule, remplie à la main : simple à coder, mais V devrait tout recopier. Écartée.

## Dossiers et fichiers

```
entrees/08_salaires/                       classeur(s) de paie au format 2025 (n'importe quel nom .xlsx)
entrees/08_salaires/fiches/fiche_salaires_AAAA.xlsx   fiche par exercice (écrite par le lecteur, corrigeable)
sorties/salaires/Reconciliation_salaires_AAAA.xlsx    résultat
```

L'exercice d'un classeur de paie est lu dans la cellule `B1` de l'onglet ANNEE (`2025`).

## La fiche (contrat entre le lecteur et le générateur)

Onglets :

- `du` : `employe`, `net_du`, `source`, `remarque`.
- `virements` : `id`, `employe`, `date`, `banque`, `montant`, `exercice`, `part_salaire`, `type`, `libelle`, `piece`,
  `imputation`, `controle`, `preuve`.
  - `montant` : montant viré ; `part_salaire` : ce qui règle le salaire de `exercice` ; la différence est « autre »
    (frais, prêt, hors salaire).
  - `id` : `AAAAMMJJ-<employé>-<montant>-<n>` (n = rang parmi les virements identiques), stable d'une lecture à l'autre.
  - `preuve` : nom du fichier de preuve, rempli par V.
- `points` : `employe`, `point` ; points à vérifier écrits à la main par V, repris dans le résultat.
- `auto` (masqué) : pour chaque `id`, les valeurs proposées par le lecteur pour `exercice`, `part_salaire`, `imputation`.

**Garder les corrections.** À la relecture du classeur de paie, pour chaque `id` déjà présent : une valeur qui diffère de
celle de `auto` est une correction de V et elle est gardée ; sinon la nouvelle valeur du lecteur la remplace. `preuve` est
toujours gardée. Les lignes ajoutées à la main par V (id vide ou absent du classeur) sont gardées et signalées. Un virement
disparu du classeur est retiré et signalé dans le résumé de lecture. Le net dû suit la même règle (colonne `net_du`).

## Lecteur du classeur de paie (format 2025)

- Employés : onglet EMPLOYES, colonne B, lignes non vides.
- Net dû : onglet ANNEE, colonne « Net définitif » (repérée par son titre en ligne 5), employé par la colonne du nom complet
  (dernière colonne remplie de la ligne) ; source notée « ANNEE, AXn ».
- Virements : premier onglet dont le nom commence par « Bank Transactions », colonnes repérées par leur titre (Date, Employé,
  Type, Montant (CHF), Libellé, Banque, Écriture comptable, Rapprochement fiche). Lignes sans date ou sans employé connu ignorées.
- Montants de référence : onglet PAYé, pour chaque employé, les lignes « Frais » (code `PAYE FRAIS`) et « hors période »
  (code `PAYE HP`) mois par mois, et les lignes de salaire (code `V1` à `V3`).

Imputation de chaque virement, dans cet ordre (premier cas qui s'applique) :

1. Type « Prêt… » : `part_salaire` 0, imputation « Prêt à l'employé : ni salaire ni frais ».
2. Type « Remboursement… » : `part_salaire` 0, « Remboursement de frais ».
3. Montant égal à une ligne de frais PAYé de l'employé non encore utilisée : `part_salaire` 0, « Frais (PAYé, mois) », même si le
   type dit « Régularisation » ou « Salaire » (cas de l'achat Odoo à 1'838.01 et des 7.00 de port).
4. Type « Régularisation AAAA » ou montant égal à une ligne hors période PAYé : exercice AAAA (sinon exercice − 1),
   `part_salaire` = montant.
5. Montant = une ligne de salaire PAYé + une ou deux lignes de frais ou hors période non utilisées : découpage. Part hors période →
   exercice précédent si elle est la seule part de salaire ; part de salaire de l'année sinon. Imputation qui détaille le découpage.
   Si un virement mêle salaire de l'année et solde de l'année précédente, il est rangé dans l'année et signalé « à vérifier ».
6. Sinon : salaire de l'exercice, `part_salaire` = montant.

Tolérance de comparaison : 0.01. Chaque ligne PAYé ne sert qu'une fois.

Contrôle : la somme des `part_salaire` de l'exercice par employé est comparée au « Versé selon PAYE » de l'onglet ANNEE ; un
écart est ajouté aux points à vérifier (sur le classeur 2025 réel, l'écart est nul pour les 10 employés).

## Générateur

Entrées : fiche N (obligatoire), fiche N−1 et fiche N+1 (si présentes).

Feuilles du résultat :

- **Synthèse** (formules) : par employé de la fiche N, Dû N, Payé en N (`SUMIFS` sur « Payé en N », exercice = N), Reporté à N+1
  (`ROUND(Dû − Payé, 2)`), Payé en N+1 (`SUMIFS` sur « Payé en N+1 », exercice = N), Écart ; ligne Total.
  En bas, si la fiche N−1 existe : bloc « Restes N−1 payés en N » (Reporté de N−1, Payé en N avec exercice = N−1, Écart).
- **Dû N** : la feuille `du` de la fiche, avec source et remarque.
- **Reste N−1** (si fiche N−1) : par employé, dû N−1 − virements de la fiche N−1 avec exercice N−1.
- **Payé en N** : tous les virements de la fiche N, groupés par employé avec sous-totaux ; colonnes Montant viré, Exercice,
  Part salaire, Autre (formule), type, libellé, pièce, imputation, contrôle, Preuve (fond jaune) ; lignes d'un autre exercice en vert.
- **Payé en N+1** : virements de la fiche N+1 dont l'exercice est N ; feuille vide avec une note si la fiche N+1 n'existe pas.
- **Points à vérifier** : écarts non nuls par employé, prêts, découpages, virements « Régularisation » classés en frais,
  fiche N+1 absente, contrôle du lecteur, puis les points écrits par V.

Mise en forme reprise des fichiers validés (titres, en-têtes bleu clair, totaux gris, format `#,##0.00`).

Écart attendu sur les données réelles (vérification manuelle, hors tests) : 2024 → synthèse identique au fichier validé ;
2025 → synthèse identique, reporté total 2'277.89, bloc 2024 avec Xiang 2'105.81.

## Fenêtre

Nouvel onglet « Salaires » (module `onglet_salaires.py`), entre « Documents » et « Assistant société » :

- liste déroulante des exercices (années des fiches présentes et des classeurs de paie déposés) ;
- **Lire le classeur de paie** : lit le classeur de l'exercice dans `08_salaires`, met la fiche à jour, affiche le résumé de lecture
  (virements ajoutés, retirés, corrections gardées) ;
- **Générer** : écrit le résultat et affiche le résumé chiffré ; **Ouvrir** ; **Ouvrir la fiche** ;
  **Enregistrer sous…** (`filedialog.asksaveasfilename`, nom proposé `Reconciliation_salaires_AAAA.xlsx`, copie du fichier) ;
- tableau de la synthèse (employé, dû, payé, reporté, payé l'année suivante, écart), écarts non nuls en orange.

Fichier ouvert dans Excel au moment d'écrire : message « Ferme … dans Excel » (comme pour `mes_corrections.xlsx`).

## Code

Paquet `src/reconsigliere/salaires/` :

- `fiche.py` : lire et écrire la fiche, fusion avec les corrections (`auto`), identifiants.
- `lecture_paie.py` : lecteur du format 2025 → lignes de fiche.
- `reconciliation.py` : calcul du résumé (valeurs) et écriture du classeur résultat.
- `__init__.py` : `lire_classeur(annee)`, `generer(annee)`, `exercices_disponibles()`.

`config.py` : `DOSSIER_SALAIRES`, `DOSSIER_FICHES_SALAIRES`, `DOSSIER_SORTIES_SALAIRES`. `installation.py` : dossier
`entrees/08_salaires` et son LISEZMOI. Version 0.9.0.

## Tests (données fictives)

- Un classeur de paie fictif au format 2025 construit par les tests (3 employés, virements mêlés, prêt, régularisation, frais).
- Lecteur : chaque règle d'imputation ; contrôle « Versé selon PAYE ».
- Fiche : relecture sans correction = identique ; correction gardée ; preuve gardée ; ligne ajoutée gardée ; virement disparu retiré.
- Générateur : formules présentes (pas de valeurs) dans la synthèse ; valeurs recalculées égales au résumé calculé en Python
  (recalcul par LibreOffice si présent, sinon test ignoré) ; bloc N−1 présent seulement avec fiche N−1 ; feuille N+1 vide sans fiche.
- Commande `salaires`.

## Documentation

Pages `docs/modules/salaires/*.md` et `onglet_salaires.md`, `donnees.md` (dossier 08 et contrat de la fiche), `README.md`
(flux), `decisions.md` (D21 fiche intermédiaire et corrections gardées par comparaison à `auto` ; D22 payés calculés depuis les
virements et non repris des totaux de V ; D23 années séparées, le reste N−1 n'est pas mêlé au solde N).

## Laissé au développeur

Noms internes, découpage des fonctions, aspect exact de l'onglet.
