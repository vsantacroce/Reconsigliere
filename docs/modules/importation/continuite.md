# importation/continuite.py : rattacher les pages qui se suivent

## À quoi il sert

Un grand livre de 12 pages n'a souvent un titre que sur la première. Cette passe rattache une page sans titre à la section en cours
quand un signe le montre : « report » ou « à reporter » en haut, « Page 2/12 » qui suit « Page 1/12 », mêmes en-têtes de colonnes,
lignes d'écritures datées dans un grand livre, lignes de comptes dans un plan comptable. Elle regroupe ensuite les pages consécutives
de même type en sections.

## Ce qu'il lit

Les pages et leur classement ([importation.classement](classement.md)).

## Ce qu'il écrit

Rien. Rend pour chaque page `(page, type, méthode)` avec méthode `regles`, `continuite` ou `indecis`, puis des `Section`.

## Ce qui casse si on le change

- Un signe de continuité trop large colle une annexe à la fin d'un grand livre ; trop strict, chaque page suivante part à l'IA.
- Une page illisible ne casse pas la chaîne : la comparaison se fait avec la dernière page lisible.
- L'extracteur reçoit une section entière : couper une section en deux perd le report de solde du grand livre.

## Dépendances (automatique)

<!-- debut-auto -->
_Partie générée par `python outils/docs.py` à partir du code : ne pas la modifier à la main._

- **Fichier :** `src/reconsigliere/importation/continuite.py` (93 lignes)
- **Dépend de :** [importation.classement](classement.md), [importation.pages](pages.md), [outils](../outils.md)
- **Utilisé par :** [importation.extracteurs](extracteurs.md), [importation.pipeline](pipeline.md)
- **Bibliothèques externes :** aucune

Fonctions et classes publiques :

- `Section`
- `signe_continuite`
- `regrouper` : Renvoie (page, type ou None, méthode) ; méthode = regles | continuite | indecis.
- `en_sections` : Regroupe les pages consécutives de même type (un titre répété sur chaque page ne coupe pas).
<!-- fin-auto -->
