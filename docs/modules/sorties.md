# sorties.py : les rapports de réconciliation

## À quoi il sert

Produit ce que tu ouvres après une réconciliation : le classeur Excel, la page interactive, les PDF renommés et le dossier des pièces
à comptabiliser. Associé au gabarit `src/reconsigliere/modele.html` (la page interactive : recherche, filtres, liens vers les PDF).

## Ce qu'il lit

Les transactions complétées par [rapprochement](rapprochement.md) et [exercices](exercices.md) ; le gabarit `modele.html`.

## Ce qu'il écrit

- `sorties/reconciliation.xlsx` : feuilles `reconciliation` (une ligne par transaction : `id_transaction`, `date`, `montant`, `libelle`,
  `partenaire`, `origine_partenaire`, `statut`, `compte_propose`, `fiabilite_compte`, `pdf_renomme`, `pdf_original`, `score`, `raisons`,
  `explication`, `source`), `pdf_sans_transaction`, `resume`.
- `sorties/reconciliation.html` : la même chose en page, données insérées à la place de `__DONNEES__`.
- `sorties/pdf_renommes` : chaque pièce retrouvée, nommée `AAAA-MM-JJ_Partenaire_MontantCHF_Numero`. Le dossier est vidé à chaque lancement.
- `sorties/a_comptabiliser` : seulement les pièces « À comptabiliser » et « À confirmer ». Vidé à chaque lancement.

## Ce qui casse si on le change

- **Colonnes de `reconciliation.xlsx`** : `id_transaction` est la colonne que l'utilisateur copie dans `mes_corrections.xlsx`.
  Le gabarit `modele.html` lit les mêmes noms de champs : changer l'un sans l'autre casse la page.
- **Le nom logique des PDF** : un nom différent à chaque version fait perdre les liens dans `mes_corrections.xlsx` (colonne `pdf`
  qui cite le nom original, pas le renommé : à garder ainsi).
- **Vider les dossiers de sortie** : tout fichier ajouté à la main dans `sorties/pdf_renommes` est effacé au lancement suivant.

## Dépendances (automatique)

<!-- debut-auto -->
_Partie générée par `python outils/docs.py` à partir du code : ne pas la modifier à la main._

- **Fichier :** `src/reconsigliere/sorties.py` (99 lignes)
- **Dépend de :** [config](config.md), [outils](outils.md), [rapprochement](rapprochement.md)
- **Utilisé par :** [__main__](__main__.md)
- **Bibliothèques externes :** pandas

Fonctions et classes publiques :

- `nom_logique`
- `vider`
- `copier_pdfs`
- `ecrire_excel`
- `ecrire_html`
<!-- fin-auto -->
