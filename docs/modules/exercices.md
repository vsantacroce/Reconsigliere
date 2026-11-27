# exercices.py : le référentiel par exercice, validé et verrouillé

## À quoi il sert

Tient, pour chaque exercice, un référentiel de cinq listes : plan comptable, partenaires et leur compte habituel, brevets, projets,
revenus. Cycle : construire depuis les fichiers → valider et verrouiller → l'exercice suivant s'ouvre comme copie → pendant l'année,
demandes de changement datées et motivées → validation à la clôture. Il propose aussi un compte pour chaque transaction de la
réconciliation (`Proposeur`, `proposer_comptes`). C'est la deuxième façon dont le programme apprend : voir [apprentissage.md](../apprentissage.md).

## Ce qu'il lit

- `entrees/06_societe/imports/AAAA/*.xlsx` : onglets plan comptable et grand livre au format du pipeline d'import (`lire_imports`).
- Le classeur des brevets et `societe.xlsx` via [societe](societe.md).
- `entrees/06_societe/exercices/AAAA/referentiel.xlsx` et `etat.json`.

## Ce qu'il écrit

- `exercices/AAAA/referentiel.xlsx` : onglets `PlanComptable`, `Partenaires`, `Brevets`, `Projets`, `Revenus`, `Changements`
  (`date`, `action`, `liste`, `cle`, `champ`, `avant`, `apres`, `motif`, `saisi_le`).
- `exercices/AAAA/etat.json` : statut ouvert/validé, date de validation, empreinte SHA-256, historique (construction, validation, réouverture avec motif).
- À la validation : fichiers en lecture seule, et `exercices/AAAA+1` créé.
- Sur les transactions : `compte_propose`, `fiabilite_compte` et `compte_reference` (le seul numéro proposé, que
  [apprentissage](apprentissage.md) compare à tes corrections ; il remplace ensuite la proposition par ta correction ou par une règle apprise).
- Changements venant de l'onglet Apprentissage (`apprentissage.reporter`) : motif « appris de n corrections ».

## Ce qui casse si on le change

- **Compte habituel d'un partenaire** = compte le plus utilisé avec lui dans le grand livre, sans les comptes techniques
  (10xx liquidités, 110x débiteurs, 117x impôt préalable, 200x créanciers, 220x TVA). Changer cette liste change toutes les propositions.
- **Verrouillage** : l'empreinte est comparée à chaque affichage ; tout changement du format écrit (ordre des onglets, styles) après
  validation ferait signaler à tort un référentiel « modifié à la main ». Ne jamais réécrire un exercice validé.
- **Format des imports** : convenu avec [importation.sorties](importation/sorties.md). Les deux doivent changer ensemble (voir [donnees.md](../donnees.md)).
- **Exercice d'une transaction** = année civile de sa date (`exercice_pour`). Un exercice décalé demanderait de changer ce calcul.
- La proposition de compte ne doit jamais lever d'erreur vers la réconciliation ([__main__](__main__.md) la protège).

## Dépendances (automatique)

<!-- debut-auto -->
_Partie générée par `python outils/docs.py` à partir du code : ne pas la modifier à la main._

- **Fichier :** `src/reconsigliere/exercices.py` (681 lignes)
- **Dépend de :** [societe](societe.md)
- **Utilisé par :** [__main__](__main__.md), [apprentissage](apprentissage.md), [fenetre](fenetre.md), [onglet_apprentissage](onglet_apprentissage.md), [onglets_societe](onglets_societe.md)
- **Bibliothèques externes :** openpyxl

Fonctions et classes publiques :

- `ExerciceVerrouille` : L'exercice est validé : il faut le rouvrir avec un motif avant de le modifier.
- `ExerciceAbsent`
- `dossier_exercices`
- `dossier_imports`
- `dossier`
- `fichier_referentiel`
- `lister`
- `lire_etat`
- `est_valide`
- `exercice_courant` : Le dernier exercice ouvert, sinon le dernier exercice tout court.
- `exercice_pour` : L'exercice qui couvre une date, sinon le plus proche avant elle, sinon le premier.
- `empreinte`
- `lire` : Toutes les listes de l'exercice, plus « Changements ».
- `lire_imports` : Plan comptable et lignes de grand livre déposés dans imports/AAAA.
- `partenaires_depuis_grand_livre` : Pour chaque partenaire, le compte de contrepartie le plus fréquent (hors banque et tiers).
- `listes_depuis_fichiers` : Ce que disent les fichiers déposés pour l'exercice, sans rien écrire.
- `construire` : Remplit le référentiel de l'exercice à partir des fichiers déposés.
- `demander_changement` : Applique un changement à une liste de l'exercice ouvert et l'inscrit dans Changements.
- `Ecart`
- `ecarts` : Différences entre l'exercice et l'exercice de référence (par défaut le précédent existant).
- `comparer` : Écarts liste par liste. Une liste absente ou vide d'un côté est ignorée.
- `suggestions` : Ce que les fichiers déposés disent de différent du référentiel ouvert.
- `appliquer` : Applique un écart proposé par suggestions() comme une demande de changement.
- `valider` : Fige l'exercice (lecture seule + empreinte) et ouvre le suivant comme copie.
- `verifier` : Rend un message si le référentiel d'un exercice validé a été modifié depuis sa validation.
- `rouvrir`
- `Proposeur` : Propose un compte à partir du référentiel de l'exercice de chaque transaction.
- `proposer_comptes` : Ajoute compte_propose / fiabilite_compte à chaque transaction. Rend le nombre de propositions.
- `resume`
- `copier_vers` : Copie le référentiel (pour l'ouvrir dans Excel sans risquer de modifier la version verrouillée).
<!-- fin-auto -->
