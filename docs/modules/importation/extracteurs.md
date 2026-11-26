# importation/extracteurs.py : transformer une section en lignes

## À quoi il sert

Pour chaque section typée, extrait des lignes normalisées :

- plan comptable : `code`, `nom`, `type` (types Odoo reconnus) ;
- grand livre : `date`, `compte`, `libelle_compte`, `piece`, `partenaire`, `libelle`, `debit`, `credit`, depuis un tableau Excel ou
  depuis le texte d'un PDF (le compte en cours est repris de la ligne de titre du compte) ;
- bilan et compte de résultat : `rubrique`, `compte`, `libelle`, `montant`, `colonne_exercice_precedent`, `niveau` ;
- annexe : le texte de chaque page.

Chaque ligne garde sa `source` (fichier et page).

## Ce qu'il lit

Les sections de [importation.continuite](continuite.md).

## Ce qu'il écrit

Rien sur le disque. Rend un dictionnaire de listes par onglet (`CLES`).

## Ce qui casse si on le change

- **Format convenu avec l'Assistant société** : code et compte en texte ; débit et crédit positifs ou vides ; partenaire vide si absent ;
  bilan et compte de résultat gardent le signe du document. [exercices](../exercices.md) compte sur ce format.
- **Partenaire dans un PDF** : séparé du libellé seulement sur « Partenaire - libellé ». Le deviner autrement fausserait les comptes
  habituels des partenaires.
- **`MOTS_IGNORES`** : les lignes « report », « total », « solde » ne sont pas des écritures ; en retirer un double des montants.

## Dépendances (automatique)

<!-- debut-auto -->
_Partie générée par `python outils/docs.py` à partir du code : ne pas la modifier à la main._

- **Fichier :** `src/reconsigliere/importation/extracteurs.py` (302 lignes)
- **Dépend de :** [importation.classement](classement.md), [importation.continuite](continuite.md), [importation.pages](pages.md), [outils](../outils.md)
- **Utilisé par :** [importation.pipeline](pipeline.md)
- **Bibliothèques externes :** pandas

Fonctions et classes publiques :

- `extraire`
<!-- fin-auto -->
