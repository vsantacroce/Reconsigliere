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
| `entrees/05_mes_corrections/mes_corrections.xlsx` | Feuilles `partenaires`, `transactions` (dont la colonne `compte`) et `regles_apprises` (règles apprises annulées) | [corrections](modules/corrections.md) (modèle, annulations), puis toi | [corrections](modules/corrections.md) |
| `entrees/06_societe/*.xlsx` | Classeur des brevets tel que tenu | toi | [societe](modules/societe.md) |
| `entrees/06_societe/societe.xlsx` | Onglets `Projets`, `Revenus`, `Journal` | [societe](modules/societe.md) (modèle, journal), toi | [societe](modules/societe.md), [exercices](modules/exercices.md) |
| `entrees/06_societe/imports/AAAA/*.xlsx` | Classeurs normalisés d'un exercice (format ci-dessous) | [importation.sorties](modules/importation/sorties.md), ou toi | [exercices](modules/exercices.md), [importation.catalogue](modules/importation/catalogue.md) (onglet Documents, seulement les classeurs avec onglets `meta` et `pages`) |
| `entrees/06_societe/exercices/AAAA/referentiel.xlsx` | Référentiel de l'exercice | [exercices](modules/exercices.md) seulement | [exercices](modules/exercices.md) |
| `entrees/06_societe/exercices/AAAA/etat.json` | Statut, empreinte, historique | [exercices](modules/exercices.md) seulement | [exercices](modules/exercices.md) |
| `entrees/07_documents/` | Documents à importer (PDF, photo, Excel) | toi | [importation.pipeline](modules/importation/pipeline.md) |
| `entrees/08_salaires/*.xlsx` | Classeur de paie au format 2025 : onglets `EMPLOYES` (noms en colonne B dès la ligne 7), `ANNEE` (exercice en B1, colonnes `Net définitif` et `Versé selon PAYE` en ligne 5), `PAYé` (lignes V1–V3, PAYE FRAIS, PAYE HP par mois), `FRAIS` facultatif (lignes HP : le reste dû de l'année précédente ; lignes « Nom — Note »), `Bank Transactions AAAA` (colonnes `Date`, `Employé`, `Type`, `Montant (CHF)`, `Libellé`, `Banque`, `Écriture comptable`, `Rapprochement fiche`) | toi | [salaires.lecture_paie](modules/salaires/lecture_paie.md) |
| `entrees/08_salaires/fiches/fiche_salaires_AAAA.xlsx` | Fiche de l'exercice : feuilles `du` (`employe`, `net_du`, `source`, `remarque`, `reste_prec_classeur`, `note_classeur`), `virements` (`id`, `employe`, `date`, `banque`, `montant`, `exercice`, `part_salaire`, `type`, `libelle`, `piece`, `imputation`, `controle`, `preuve`), `points` (`employe`, `point`), `auto` cachée (valeurs calculées, pour reconnaître tes corrections) | [salaires.fiche](modules/salaires/fiche.md), puis toi (`exercice`, `part_salaire`, `imputation`, `preuve`, lignes ajoutées) | [salaires.fiche](modules/salaires/fiche.md) |

## Sorties

| Chemin | Contenu | Écrit par |
|---|---|---|
| `sorties/reconciliation.xlsx` | Feuilles `reconciliation` (dont `compte_propose`, `fiabilite_compte`, `origine_compte`), `pdf_sans_transaction`, `resume` | [sorties](modules/sorties.md) |
| `sorties/apprentissage.xlsx` | Onglets `resume`, `regles`, `alertes`, `corrections` : ce que le programme a appris de tes corrections de compte | [apprentissage](modules/apprentissage.md) ; relu par [onglet_apprentissage](modules/onglet_apprentissage.md) |
| `sorties/reconciliation.html` | Page interactive (gabarit `modele.html`) | [sorties](modules/sorties.md) |
| `sorties/pdf_renommes/` | Pièces renommées `AAAA-MM-JJ_Partenaire_MontantCHF_Numero` (vidé à chaque lancement) | [sorties](modules/sorties.md) |
| `sorties/a_comptabiliser/` | Pièces « À comptabiliser » et « À confirmer » (vidé à chaque lancement) | [sorties](modules/sorties.md) |
| `sorties/societe.html` | Tableau de bord de la société (gabarit `modele_societe.html`) | [societe](modules/societe.md) |
| `sorties/imports/<document>.html` | Relecture d'un document importé | [importation.sorties](modules/importation/sorties.md) |
| `sorties/salaires/Reconciliation_salaires_AAAA.xlsx` | Feuilles `Synthèse` (formules SOMME.SI.ENS), `Dû AAAA`, `Reste AAAA−1` (si la fiche précédente existe), `Payé en AAAA`, `Payé en AAAA+1`, `Points à vérifier` | [salaires.reconciliation](modules/salaires/reconciliation.md) |
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
