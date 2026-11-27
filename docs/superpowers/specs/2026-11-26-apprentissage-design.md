# Apprentissage visible : conception

Date : 26.11.2026. Validée par V (option 1 : tout est recalculé à chaque lancement depuis ses corrections).

## Intention

V ne voyait pas où le programme apprend. En 0.6.0, la seule mémoire automatique est le compte habituel de chaque partenaire tiré du
grand livre ; une correction faite en réconciliation ne vaut que pour sa transaction. V veut ne pas avoir à corriger à chaque fois :
après plusieurs corrections identiques, le programme doit corriger seul ; si les corrections continuent, il doit comprendre pourquoi,
et alerter quand quelque chose cloche ou quand sa propre analyse se trompait. Et il veut voir tout cela dans la fenêtre.

## Buts

- Corriger le compte d'une transaction dans `mes_corrections.xlsx` (nouvelle colonne `compte`).
- Après 3 corrections identiques pour un partenaire, appliquer seul ce compte aux autres transactions de ce partenaire.
- Si les corrections divergent, chercher le critère qui sépare les comptes : période (changement de compte à une date),
  mot du libellé, seuil de montant. Critère trouvé : règle conditionnelle. Sinon : règle suspendue et alerte.
- Compte unique différent du référentiel : signaler que le référentiel est faux, et lister les autres partenaires rangés sur
  le même ancien compte (même erreur possible).
- Alertes : règle contredite (l'analyse se trompait), critère introuvable, compte corrigé absent du plan comptable.
- Onglet « Apprentissage » : résumé chiffré, règles (partenaire, compte, condition, origine, fiabilité, état), alertes ;
  boutons « Annuler la règle », « Rétablir la règle », « Reporter dans l'exercice ouvert », « Ouvrir mes corrections ».
- Sortie lisible `sorties/apprentissage.xlsx` (onglets resume, regles, alertes, corrections).

## Non-buts

- Pas d'apprentissage du score de rapprochement des pièces ni du classement des pages d'import (restent dans « ce qu'il ne retient pas »).
- Pas de modification automatique du référentiel d'un exercice : le report est un bouton (changement daté et motivé).

## Anti-buts

- Aucune mémoire cachée : supprimer une correction retire son effet au lancement suivant.
- Un exercice validé n'est jamais modifié.

## Approches considérées

1. **Recalcul à chaque lancement depuis les corrections** (choisie par V). Seules ses décisions (règle annulée) sont gardées,
   dans la feuille `regles_apprises` de `mes_corrections.xlsx`.
2. Mémoire séparée qui s'enrichit : garde les règles même si les corrections disparaissent, mais peut dériver sans explication.
3. Écriture directe dans le référentiel d'exercice : versionné, mais pas de règles conditionnelles et chaque règle devient un changement.

## Règles de calcul (décisions de l'implémentation)

- Observation = une ligne de la feuille `transactions` avec un `compte` rempli et dont la transaction est présente dans les relevés.
  Le partenaire est celui retenu par la réconciliation (correction de partenaire comprise), comparé sans accents ni casse.
- `SEUIL_REGLE = 3` corrections identiques (dans `config.py`). En dessous : « en observation », rien n'est appliqué.
- Un seul compte corrigé : règle « active ». Fiabilité « n corrections sur n ».
- Plusieurs comptes, le second ayant au moins 2 corrections : recherche d'un critère, dans cet ordre :
  1. période : toutes les corrections d'un compte sont postérieures à toutes celles des autres → règle « depuis le JJ.MM.AAAA » vers le
     compte le plus récent ; il doit lui-même atteindre le seuil, sinon « en observation » ;
  2. mot du libellé : un mot (≥ 3 lettres, hors mots bancaires et nombres) présent dans toutes les corrections d'un compte et absent des
     autres → « si le libellé contient MOT » ; le compte restant (sans mot) est le compte par défaut ;
  3. montant (deux comptes seulement) : séparés par un seuil → « montant < X » / « montant ≥ X », X au milieu, arrondi au franc.
  Critère trouvé : règle « conditionnelle », alerte « mon analyse se trompait » si une règle simple aurait été active.
  Aucun critère : règle « suspendue », alerte « critère introuvable, à trancher ».
- Un compte minoritaire avec une seule correction ne casse pas la règle : fiabilité « 4 corrections sur 5 » et alerte « 1 correction
  contraire ».
- Application, pour chaque transaction : sa propre correction de compte, sinon la règle active ou conditionnelle non annulée, sinon la
  proposition du référentiel. Colonnes `compte_propose`, `fiabilite_compte`, nouvelle colonne `origine_compte`
  (`ta correction`, `appris`, `référentiel`).
- Référentiel faux : si le référentiel de l'exercice courant range le partenaire sur un autre compte que la règle, alerte avec la liste
  (10 au plus) des autres partenaires rangés sur ce même ancien compte.
- Annuler : ligne (`partenaire`, `compte`, `decision` = annulée, `le`) dans `regles_apprises` ; rétablir supprime la ligne.
  Effet au lancement suivant.
- Reporter : `exercices.demander_changement` sur l'exercice ouvert, liste Partenaires, modification du `compte`
  (ou ajout si le partenaire n'y est pas), motif « appris de n corrections ». Règles conditionnelles non reportables.

## Ce qui reste au constructeur

Mise en page de l'onglet (Treeview comme les autres onglets), textes d'aide, messages d'erreur si le fichier est ouvert dans Excel.
