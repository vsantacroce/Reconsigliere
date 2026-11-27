# config.py : les réglages du programme

## À quoi il sert

Tient les réglages communs : où se trouve le dossier de travail et ses sous-dossiers, la devise (`CHF`),
les tolérances et les seuils du rapprochement, et les noms de colonnes reconnus dans les Excel des banques
et de la comptabilité. C'est le seul endroit où ces valeurs sont écrites.

## Ce qu'il lit

Rien. Ses valeurs sont dans le code. `definir_racine(dossier)` est appelée au démarrage avec le dossier
de travail mémorisé (voir [installation](installation.md)) et recalcule tous les chemins `entrees/…` et `sorties/…`.

## Ce qu'il écrit

Rien sur le disque. Il fournit aux autres modules :

- les chemins : `RACINE`, `DOSSIER_FACTURES`, `DOSSIER_TRANSACTIONS`, `DOSSIER_INFOS_BANCAIRES`,
  `DOSSIER_COMPTABILITE`, `FICHIER_CORRECTIONS`, `DOSSIER_SORTIES`, `DOSSIER_PDF_RENOMMES`, `DOSSIER_A_COMPTABILISER` ;
- `DEVISE = "CHF"` ;
- `TOLERANCE_MONTANT = 0.01`, `TOLERANCE_JOURS = 15`, `SEUIL_SUR = 60`, `SEUIL_A_CONFIRMER = 40` ;
- `SEUIL_REGLE = 3` : corrections identiques de compte avant qu'une règle apprise s'applique seule ([apprentissage](apprentissage.md)) ;
- `ALIAS_COLONNES` : pour chaque champ (date, montant, débit, crédit, libellé, IBAN, référence, partenaire, fichier, statut),
  les en-têtes de colonnes acceptés ;
- les chemins des salaires : `DOSSIER_SALAIRES` (`entrees/08_salaires`), `DOSSIER_FICHES_SALAIRES` (`entrees/08_salaires/fiches`),
  `DOSSIER_SORTIES_SALAIRES` (`sorties/salaires`) ;
- `CHEMIN_TESSERACT` et `LANGUES_OCR` pour la lecture des images.

## Ce qui casse si on le change

- **Seuils et tolérances** : changent directement les statuts de la réconciliation. Monter `SEUIL_SUR` fait passer des
  transactions de « À comptabiliser » à « À confirmer » ; baisser `SEUIL_A_CONFIRMER` propose plus de PDF, avec plus d'erreurs.
  `TOLERANCE_JOURS` sert aussi à reconnaître une ligne déjà comptabilisée. Voir [rapprochement](rapprochement.md) et la décision D2 de
  [decisions.md](../decisions.md).
- **ALIAS_COLONNES** : retirer un nom fait disparaître la colonne correspondante d'un relevé (montant ou date absents = la ligne est ignorée).
  Ajouter un nom trop général (par exemple `compte` pour l'IBAN) peut mal associer une colonne.
- **Noms des dossiers** dans `definir_racine` : doivent rester identiques à ceux de [installation](installation.md) (`DOSSIERS`),
  sinon les fichiers déposés ne sont plus trouvés. Un dossier de travail existant garde ses anciens noms : renommer casse les installations existantes.
- **DEVISE** : écrite dans les noms de PDF renommés, les rapports et le classeur d'import. Le programme ne convertit aucune devise.
- Presque tous les modules l'importent : voir la liste « Utilisé par » ci-dessous.

## Dépendances (automatique)

<!-- debut-auto -->
_Partie générée par `python outils/docs.py` à partir du code : ne pas la modifier à la main._

- **Fichier :** `src/reconsigliere/config.py` (69 lignes)
- **Dépend de :** aucun autre module du programme
- **Utilisé par :** [__main__](__main__.md), [apprentissage](apprentissage.md), [chargement](chargement.md), [corrections](corrections.md), [fenetre](fenetre.md), [importation.pages](importation/pages.md), [importation.pipeline](importation/pipeline.md), [onglet_apprentissage](onglet_apprentissage.md), [onglet_salaires](onglet_salaires.md), [pdf_extraction](pdf_extraction.md), [rapprochement](rapprochement.md), [salaires.fiche](salaires/fiche.md), [salaires.lecture_paie](salaires/lecture_paie.md), [salaires.reconciliation](salaires/reconciliation.md), [societe](societe.md), [sorties](sorties.md)
- **Bibliothèques externes :** aucune

Fonctions et classes publiques :

- `definir_racine` : Change le dossier de travail (celui qui contient entrees et sorties).
<!-- fin-auto -->
