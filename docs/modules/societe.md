# societe.py : l'état de la société (brevets, projets, revenus, journal)

## À quoi il sert

Lit le classeur des brevets tel que tu le tiens et `societe.xlsx`, puis calcule le tableau de bord : familles de brevets actives,
dépôts par pays, coûts capitalisables et en charge par année, projets capitalisables, sources de revenus, journal, points d'attention.
Associé au gabarit `src/reconsigliere/modele_societe.html`.

## Ce qu'il lit

Tout classeur Excel de `entrees/06_societe` (sauf les sous-dossiers `exercices` et `imports`) :

- un onglet de liste de brevets, reconnu par ses colonnes (`ID`, `Title`, `Patent number`, `Filing date`, `Approved date`,
  `Abandon date`, `Patent owner`…) ; la famille vient de l'identifiant (`PAT01-03` → `PAT01`), le pays du numéro ;
- des onglets de coûts (`Brevet`, `Classification` Capitalisable/Charge, `Montant HT CHF`, `Date facture`) ;
- `societe.xlsx`, onglets `Projets`, `Revenus`, `Journal`.

## Ce qu'il écrit

- `entrees/06_societe/societe.xlsx` au premier lancement (s'il n'existe pas) ; une ligne dans `Journal` via « Ajouter au journal… ».
- `sorties/societe.html` : le tableau de bord.

## Ce qui casse si on le change

- **Reconnaissance des colonnes** (`ALIAS_…`) : le classeur des brevets n'est pas modifié pour le programme ; si une colonne n'est plus
  reconnue, les brevets ou les coûts disparaissent du tableau de bord sans erreur.
- **Règle capitalisable / charge** : lue telle quelle dans la colonne Classification. Un coût qui cite deux familles va dans « à répartir ».
- **[exercices](exercices.md) réutilise** ses fonctions de lecture (`_texte`, `_norm`, `lire_brevets`, `charger`) pour construire la liste
  Brevets d'un exercice : changer leur comportement change les référentiels construits ensuite.
- **Ne lit pas** `exercices/` ni `imports/` : retirer cette exclusion ferait compter des référentiels comme des classeurs de brevets.
- Les champs envoyés à `modele_societe.html` (`synthese`) doivent rester ceux que le gabarit attend.

## Dépendances (automatique)

<!-- debut-auto -->
_Partie générée par `python outils/docs.py` à partir du code : ne pas la modifier à la main._

- **Fichier :** `src/reconsigliere/societe.py` (648 lignes)
- **Dépend de :** [config](config.md), [installation](installation.md)
- **Utilisé par :** [exercices](exercices.md), [fenetre](fenetre.md)
- **Bibliothèques externes :** openpyxl

Fonctions et classes publiques :

- `dossier_societe`
- `fichier_classeur`
- `Depot`
- `Cout`
- `Etat`
- `famille_de`
- `familles_citees`
- `lire_brevets`
- `lire_couts`
- `creer_modele_si_absent` : Crée societe.xlsx avec ses onglets vides. Ne touche jamais à un fichier existant.
- `ajouter_au_journal` : Ajoute une ligne à l'onglet Journal de societe.xlsx.
- `charger`
- `synthese` : Chiffres du tableau de bord, prêts à afficher.
- `points_d_attention`
- `format_chf`
- `ecrire_html`
- `actualiser` : Crée le classeur si besoin, relit tout et réécrit sorties/societe.html.
<!-- fin-auto -->
