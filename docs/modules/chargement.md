# chargement.py : lecture des relevés bancaires et de la comptabilité

## À quoi il sert

Lit tous les Excel et CSV des dossiers d'entrée et les transforme en lignes uniformes : date, montant signé, libellé, IBAN,
référence, partenaire, fichier, statut. Il trouve tout seul la ligne d'en-tête et associe les colonnes grâce aux noms de
`ALIAS_COLONNES` ([config](config.md)).

## Ce qu'il lit

- `entrees/02_transactions_a_reconcilier` : les transactions à réconcilier (`charger_transactions`).
- `entrees/03_infos_bancaires` : relevés détaillés, qui complètent libellé, IBAN, référence et partenaire d'une transaction
  quand une seule ligne a le même montant à 3 jours près (`enrichir_avec_infos_bancaires`).
- `entrees/04_comptabilite` : la liste des pièces comptabilisées (`charger_comptabilite`).

Formats : `.xlsx`, `.xlsm`, `.xls` (avec `xlrd`), `.csv` ; les fichiers temporaires Excel `~$…` sont ignorés.

## Ce qu'il écrit

Rien sur le disque. Il rend des listes de dictionnaires. Chaque transaction reçoit un identifiant `T` + 8 caractères,
calculé sur `date | montant | libellé normalisé`.

## Ce qui casse si on le change

- **L'identifiant de transaction** relie la sortie à `mes_corrections.xlsx`. Le changer rend toutes les corrections par transaction orphelines.
- **Débit / crédit** : un débit devient un montant négatif, un crédit un montant positif. Inverser casse le rapprochement avec la comptabilité.
- **Doublons** : deux transactions avec la même date, le même montant et le même libellé n'en font qu'une (défaut connu).
- **Enrichissement** : la fenêtre de 3 jours et l'exigence d'une seule candidate sont écrites dans le code, pas dans config.

## Dépendances (automatique)

<!-- debut-auto -->
_Partie générée par `python outils/docs.py` à partir du code : ne pas la modifier à la main._

- **Fichier :** `src/reconsigliere/chargement.py` (146 lignes)
- **Dépend de :** [config](config.md), [outils](outils.md)
- **Utilisé par :** [__main__](__main__.md)
- **Bibliothèques externes :** pandas

Fonctions et classes publiques :

- `lister_tableurs`
- `lire_tableur` : Renvoie une table par feuille.
- `associer_colonnes` : Associe chaque champ connu (date, montant...) à une colonne du tableau.
- `identifiant_transaction`
- `charger_lignes` : Lit tous les tableurs d'un dossier et renvoie des lignes normalisées.
- `charger_transactions`
- `enrichir_avec_infos_bancaires` : Complète libellé, IBAN, référence et partenaire à partir du dossier 03.
- `charger_comptabilite`
<!-- fin-auto -->
