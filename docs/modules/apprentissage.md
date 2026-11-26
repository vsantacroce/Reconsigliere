# apprentissage.py : ce que le programme apprend de tes corrections de compte

## À quoi il sert

Transforme tes corrections de compte en règles. Quand tu corriges le compte d'une transaction dans `mes_corrections.xlsx`
(feuille `transactions`, colonne `compte`), cette correction devient une « observation » pour le partenaire de la transaction.
À chaque réconciliation, tout est recalculé depuis ces observations (rien n'est gardé ailleurs) :

1. **En observation** : moins de 3 corrections identiques (`config.SEUIL_REGLE`). Rien n'est appliqué.
2. **Active** : 3 corrections identiques ou plus. Le compte est appliqué seul aux autres transactions du partenaire.
   Une correction isolée contraire ne casse pas la règle (« 4 corrections sur 5 ») mais donne une alerte.
3. **Plusieurs comptes** (au moins deux comptes corrigés deux fois chacun) : le programme cherche ce qui les sépare, dans cet ordre :
   - la **période** : tu es passé d'un compte à l'autre à une date → règle « depuis le JJ.MM.AAAA » ;
   - un **mot du libellé** présent dans toutes les corrections d'un compte et dans aucune des autres (« si le libellé contient carburant ») ;
   - un **seuil de montant** (deux comptes seulement) : « si le montant < 468 CHF ».
   Critère trouvé : règle **conditionnelle**. Sinon : règle **suspendue** et alerte « critère introuvable ».
4. **Annulée** : tu l'as mise de côté dans l'onglet Apprentissage (feuille `regles_apprises`).

Il lève aussi des **alertes** : le référentiel de l'exercice range le partenaire sur un autre compte que tes corrections (avec la liste
des autres partenaires rangés sur ce même ancien compte, « même erreur possible ») ; le compte corrigé n'existe pas dans le plan comptable ;
« mon analyse se trompait » quand une règle simple avait été active et que tes corrections montrent autre chose.

Enfin, il fixe le compte final de chaque transaction : ta correction, sinon la règle apprise, sinon la proposition du référentiel
([exercices](exercices.md)). `reporter()` inscrit une règle active dans le référentiel de l'exercice ouvert (changement daté et motivé).

## Ce qu'il lit

- Les transactions après le rapprochement et la proposition de compte : `partenaire_trouve`, `date`, `montant`, `libelle`,
  `compte_reference` (le compte proposé par le référentiel).
- Les corrections chargées par [corrections](corrections.md) : colonne `compte` et règles annulées.
- Le référentiel du dernier exercice ouvert ([exercices](exercices.md)) : onglets `Partenaires` et `PlanComptable`. Sans exercice,
  l'apprentissage marche quand même, sans les alertes de référentiel et de plan comptable.

## Ce qu'il écrit

- Sur les transactions : `compte_propose`, `fiabilite_compte` et `origine_compte` (`ta correction`, `appris`, `référentiel`).
- `sorties/apprentissage.xlsx` : onglets `resume` (compteurs, date du calcul), `regles` (`partenaire`, `compte`, `condition`, `etat`,
  `fiabilite`, `corrections`, `compte_reference`, `explication`), `alertes` (`niveau`, `partenaire`, `message`),
  `corrections` (une ligne par correction prise en compte). Relu par [onglet_apprentissage](onglet_apprentissage.md).
- Avec `reporter()` : une modification (ou un ajout) dans l'onglet `Partenaires` du référentiel ouvert, motif
  « appris de n corrections dans mes_corrections.xlsx ».

## Ce qui casse si on le change

- **Le seuil** (`config.SEUIL_REGLE = 3`) : plus bas, une faute de frappe devient vite une règle ; plus haut, il faut corriger plus
  longtemps avant que le programme prenne le relais.
- **L'identité d'un partenaire** : comparaison sans accents ni majuscules du partenaire retenu par la réconciliation. Si une règle de
  partenaire change de nom (feuille `partenaires`), les corrections passées comptent pour le nouveau nom seulement si la réconciliation le retrouve.
- **L'ordre des critères** (période, mot, montant) : changer l'ordre change la règle retenue quand plusieurs critères conviennent.
- **Les mots ignorés** viennent de `MOTS_BANCAIRES` dans [rapprochement](rapprochement.md) : y ajouter un mot l'empêche de servir de critère.
- **Annulation** : la clé est (partenaire, compte affiché). Si les corrections changent le compte d'une règle annulée, la nouvelle règle
  n'est plus annulée : c'est voulu (nouvelle information), mais à savoir.
- L'appel dans [__main__](__main__.md) est protégé : une erreur ici ne bloque jamais la réconciliation.
- Le format de `sorties/apprentissage.xlsx` est relu par [onglet_apprentissage](onglet_apprentissage.md) : changer les colonnes ensemble.

## Dépendances (automatique)

<!-- debut-auto -->
_Partie générée par `python outils/docs.py` à partir du code : ne pas la modifier à la main._

- **Fichier :** `src/reconsigliere/apprentissage.py` (474 lignes)
- **Dépend de :** [config](config.md), [exercices](exercices.md), [outils](outils.md), [rapprochement](rapprochement.md)
- **Utilisé par :** [__main__](__main__.md), [onglet_apprentissage](onglet_apprentissage.md)
- **Bibliothèques externes :** openpyxl

Fonctions et classes publiques :

- `Observation` : Une transaction dont tu as corrigé le compte.
- `Branche` : « compte si condition ». nature : toujours, depuis (date), mot (du libellé), montant_inf, montant_sup.
- `Regle`
- `Alerte`
- `Analyse`
- `observations` : Les transactions présentes dans les relevés dont la feuille transactions donne un compte.
- `analyser` : Règles et alertes tirées des corrections. referentiel : {"exercice", "Partenaires", "PlanComptable"} ou None.
- `appliquer` : Compte final de chaque transaction : ta correction, sinon la règle apprise, sinon le référentiel.
- `referentiel_courant` : Le référentiel du dernier exercice ouvert (sinon du dernier exercice), ou None s'il n'y en a pas.
- `executer` : Appelé par la réconciliation, après exercices.proposer_comptes.
- `reporter` : Inscrit la règle dans le référentiel de l'exercice ouvert (changement daté et motivé).
- `fichier_sortie`
- `ecrire` : sorties/apprentissage.xlsx : resume, regles, alertes, corrections. Relu par l'onglet Apprentissage.
- `lire_sortie` : Relit sorties/apprentissage.xlsx, ou None s'il n'existe pas encore.
<!-- fin-auto -->
