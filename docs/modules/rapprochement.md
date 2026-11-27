# rapprochement.py : le cœur de la réconciliation

## À quoi il sert

Relie chaque transaction bancaire à un partenaire et à une pièce, puis lui donne un statut.

1. **Partenaire** : d'abord les règles de `mes_corrections.xlsx`, sinon le partenaire donné par la banque, sinon les trois premiers
   mots significatifs du libellé.
2. **Pièce** : les liens imposés dans tes corrections, puis un score de 0 à 100 pour chaque couple transaction–PDF :
   montant 50 (+5 si c'est le total), date à 3 jours 20 / à 15 jours 12 / à 60 jours 5, IBAN 25, référence 25, partenaire 20.
   Les meilleurs scores sont servis d'abord ; un PDF ne va qu'à une transaction.
3. **Statut** : statut forcé, sinon « Comptabilisé » si la comptabilité a une ligne de même montant à 15 jours ou le même PDF,
   sinon « À comptabiliser » (score ≥ 60), « À confirmer » (score ≥ 40), « Expliqué sans pièce », « PDF manquant ».

## Ce qu'il lit

Les listes déjà chargées par [chargement](chargement.md), [pdf_extraction](pdf_extraction.md) et [corrections](corrections.md).
Aucun fichier directement.

## Ce qu'il écrit

Rien sur le disque. Il complète chaque transaction : `partenaire_trouve`, `origine_partenaire`, `pdf`, `score`, `raisons`,
`explication`, `statut`. `pdfs_non_lies` rend les PDF sans transaction.

## Ce qui casse si on le change

- **Les points du score** et les seuils de [config](config.md) décident des statuts : tout changement modifie le rapport de
  réconciliation existant. Tester avec `tests/test_rapprochement.py`.
- **Les libellés de statut** (`STATUT_…`) sont affichés et filtrés tels quels dans [sorties](sorties.md) et `modele.html`.
- **`MOTS_BANCAIRES`** : mots ignorés pour deviner le partenaire ; en retirer un fait apparaître « Paiement » ou « Twint » comme partenaire.
- **Appariement glouton** : un PDF ne sert qu'une fois ; une facture payée en deux fois n'est liée qu'à un paiement (défaut connu).
- Le partenaire trouvé sert ensuite à [exercices](exercices.md) pour proposer un compte.

## Dépendances (automatique)

<!-- debut-auto -->
_Partie générée par `python outils/docs.py` à partir du code : ne pas la modifier à la main._

- **Fichier :** `src/reconsigliere/rapprochement.py` (159 lignes)
- **Dépend de :** [config](config.md), [outils](outils.md)
- **Utilisé par :** [__main__](__main__.md), [apprentissage](apprentissage.md), [sorties](sorties.md)
- **Bibliothèques externes :** aucune

Fonctions et classes publiques :

- `deviner_partenaire` : Renvoie (partenaire, origine de l'information).
- `score`
- `reconcilier`
- `pdfs_non_lies`
<!-- fin-auto -->
