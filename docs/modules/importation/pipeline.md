# importation/pipeline.py : l'enchaînement de l'import

## À quoi il sert

Enchaîne l'import d'un document : pages → classement → continuité → IA ou choix manuel pour les pages indécises → extraction →
contrôles → classeur et page. Détecte l'exercice (année la plus citée, ou « exercice 2024 », « au 31.12.2024 ») et le nom de la société.
`importer_dossier` traite `entrees/07_documents` et saute les documents déjà importés (même contenu).

## Ce qu'il lit

- `entrees/07_documents` (ou les fichiers donnés) ;
- `sorties/imports/index.json` : empreinte de chaque document déjà importé et classeur produit.

## Ce qu'il écrit

Via [importation.sorties](sorties.md) : le classeur et la page. Met à jour `sorties/imports/index.json`.
Contrôles inscrits dans l'onglet `controles` : grand livre équilibré, lignes sans compte, actifs = passifs, pages illisibles, pages à vérifier.

## Ce qui casse si on le change

- **Exercice d'une écriture de grand livre** = année de sa date (exercice civil), pas l'exercice du document.
- **`index.json`** évite de réimporter : le supprimer réimporte tout (et peut rappeler l'IA). `--forcer` fait de même volontairement.
- **Un document abîmé n'arrête pas les autres** (erreur journalisée) : garder ce comportement.
- `choisir` est fourni par la fenêtre ; en ligne de commande, une page indécise sans IA devient « autre » et figure dans « Pages à vérifier ».

## Dépendances (automatique)

<!-- debut-auto -->
_Partie générée par `python outils/docs.py` à partir du code : ne pas la modifier à la main._

- **Fichier :** `src/reconsigliere/importation/pipeline.py` (179 lignes)
- **Dépend de :** [config](../config.md), [importation.classement](classement.md), [importation.continuite](continuite.md), [importation.extracteurs](extracteurs.md), [importation.ia](ia.md), [importation.pages](pages.md), [importation.sorties](sorties.md), [outils](../outils.md)
- **Utilisé par :** [__main__](../__main__.md), [fenetre](../fenetre.md)
- **Bibliothèques externes :** aucune

Fonctions et classes publiques :

- `detecter_exercice`
- `detecter_societe`
- `importer`
- `importer_dossier` : Importe chaque document de entrees/07_documents qui ne l'a pas encore été (même contenu).
<!-- fin-auto -->
