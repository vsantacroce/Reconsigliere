# Les fichiers lus et écrits

Chemins relatifs au dossier de travail. « Lu par » et « écrit par » renvoient aux pages des modules.
Aucun de ces fichiers n'est dans le dépôt GitHub : `.gitignore` exclut `entrees/` et `sorties/` (sauf les `LISEZMOI.md`).

## Entrées

| Chemin | Contenu | Écrit par | Lu par |
|---|---|---|---|
| `entrees/01_factures/` | Factures, reçus, notes de frais (PDF, PNG, JPG) | toi | [pdf_extraction](modules/pdf_extraction.md) |
| `entrees/02_transactions_a_reconcilier/` | Excel ou CSV de la banque : date, montant ou débit/crédit, libellé ; IBAN, référence, partenaire facultatifs | toi | [chargement](modules/chargement.md) |
| `entrees/03_infos_bancaires/` | Relevés détaillés (mêmes colonnes) | toi | [chargement](modules/chargement.md) |
| `entrees/04_comptabilite/` | Liste Excel des pièces comptabilisées, PDF dans `pdf/` | toi | [chargement](modules/chargement.md), [pdf_extraction](modules/pdf_extraction.md) |
| `entrees/05_mes_corrections/mes_corrections.xlsx` | Feuilles `partenaires` et `transactions` | [corrections](modules/corrections.md) (modèle), puis toi | [corrections](modules/corrections.md) |
| `entrees/06_societe/*.xlsx` | Classeur des brevets tel que tenu | toi | [societe](modules/societe.md) |
| `entrees/06_societe/societe.xlsx` | Onglets `Projets`, `Revenus`, `Journal` | [societe](modules/societe.md) (modèle, journal), toi | [societe](modules/societe.md), [exercices](modules/exercices.md) |
| `entrees/06_societe/imports/AAAA/*.xlsx` | Classeurs normalisés d'un exercice (format ci-dessous) | [importation.sorties](modules/importation/sorties.md), ou toi | [exercices](modules/exercices.md), [importation.catalogue](modules/importation/catalogue.md) (onglet Documents, seulement les classeurs avec onglets `meta` et `pages`) |
| `entrees/06_societe/exercices/AAAA/referentiel.xlsx` | Référentiel de l'exercice | [exercices](modules/exercices.md) seulement | [exercices](modules/exercices.md) |
| `entrees/06_societe/exercices/AAAA/etat.json` | Statut, empreinte, historique | [exercices](modules/exercices.md) seulement | [exercices](modules/exercices.md) |
| `entrees/07_documents/` | Documents à importer (PDF, photo, Excel) | toi | [importation.pipeline](modules/importation/pipeline.md) |

## Sorties

| Chemin | Contenu | Écrit par |
|---|---|---|
| `sorties/reconciliation.xlsx` | Feuilles `reconciliation`, `pdf_sans_transaction`, `resume` | [sorties](modules/sorties.md) |
| `sorties/reconciliation.html` | Page interactive (gabarit `modele.html`) | [sorties](modules/sorties.md) |
| `sorties/pdf_renommes/` | Pièces renommées `AAAA-MM-JJ_Partenaire_MontantCHF_Numero` (vidé à chaque lancement) | [sorties](modules/sorties.md) |
| `sorties/a_comptabiliser/` | Pièces « À comptabiliser » et « À confirmer » (vidé à chaque lancement) | [sorties](modules/sorties.md) |
| `sorties/societe.html` | Tableau de bord de la société (gabarit `modele_societe.html`) | [societe](modules/societe.md) |
| `sorties/imports/<document>.html` | Relecture d'un document importé | [importation.sorties](modules/importation/sorties.md) |
| `sorties/imports/index.json` | Documents déjà importés (empreinte → classeur) | [importation.pipeline](modules/importation/pipeline.md) |

## Hors du dossier de travail

| Chemin | Contenu | Module |
|---|---|---|
| `%APPDATA%\Reconsigliere\reglages.json` (Linux : `~/.config/Reconsigliere/`) | `dossier_travail`, `cle_api_anthropic`, `modele_ia` | [installation](modules/installation.md) |
| `%LOCALAPPDATA%\Reconsigliere\` | `app/`, `version.txt`, `branche.txt`, `requirements.installe`, `journal.txt` | [windows.demarrer](modules/windows/demarrer.md), [installer](modules/windows/installer.md) |

## Contrat entre l'import et l'Assistant société

Le classeur écrit par l'import et lu par les exercices est le seul format partagé entre deux parties du programme.
Changer une colonne demande de changer [importation.sorties](modules/importation/sorties.md) (`COLONNES`) et
[exercices](modules/exercices.md) (`lire_imports`) dans la même modification.

| Onglet | Colonnes |
|---|---|
| `meta` | `cle`, `valeur` (société, dates, devise, fichier source, empreinte, modèle IA, appels et tokens) |
| `pages` | `page`, `type`, `methode` (regles, continuite, ia, manuel, a_verifier, illisible), `score`, `source` |
| `controles` | `controle`, `resultat` (ok, ecart), `detail` |
| `plancomptable` | `code`, `nom`, `type`, `exercice`, `source` |
| `grandlivre` | `date`, `compte`, `libelle_compte`, `piece`, `partenaire`, `libelle`, `debit`, `credit`, `exercice`, `source` |
| `bilan`, `compteresultat` | `rubrique`, `compte`, `libelle`, `montant`, `colonne_exercice_precedent`, `niveau`, `exercice`, `source` |
| `annexe` | `page`, `texte`, `source` |

Règles : `exercice` entier (pour le grand livre, l'année de la date) ; `code` et `compte` en texte ; `debit` et `credit` positifs ou vides ;
`partenaire` vide si absent ; bilan et compte de résultat gardent le signe du document.
Les exercices ne lisent aujourd'hui que `plancomptable` et `grandlivre`.
