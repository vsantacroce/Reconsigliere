# corrections.py : tes corrections manuelles

## À quoi il sert

Crée et lit `mes_corrections.xlsx`, le fichier où tu fais avancer la réconciliation à la main. Tes corrections passent toujours
avant le rapprochement automatique. C'est aujourd'hui la principale façon dont le programme « apprend » de toi : voir
[apprentissage.md](../apprentissage.md).

## Ce qu'il lit

`entrees/05_mes_corrections/mes_corrections.xlsx` :

- feuille `partenaires` : `mot_dans_libelle`, `partenaire` (si le libellé bancaire contient le mot, ce partenaire est utilisé) ;
- feuille `transactions` : `id_transaction`, `date`, `montant`, `libelle`, `partenaire`, `pdf`, `explication`, `statut_force`.

## Ce qu'il écrit

Le modèle `mes_corrections.xlsx` au premier lancement (avec un exemple `SWISSCOM` et une feuille `aide`), seulement s'il n'existe pas.

## Ce qui casse si on le change

- **Noms des feuilles et des colonnes** : les fichiers déjà remplis par l'utilisateur ne seraient plus lus. Tout renommage doit lire
  aussi l'ancien nom.
- **Valeurs de `statut_force`** (`Comptabilise`, `Sans piece`, `A comptabiliser`, `Ignorer`) : comparées dans [rapprochement](rapprochement.md)
  (`STATUTS_FORCES`), après normalisation.
- Les lignes commençant par `exemple` sont ignorées.

## Dépendances (automatique)

<!-- debut-auto -->
_Partie générée par `python outils/docs.py` à partir du code : ne pas la modifier à la main._

- **Fichier :** `src/reconsigliere/corrections.py` (52 lignes)
- **Dépend de :** [config](config.md), [outils](outils.md)
- **Utilisé par :** [__main__](__main__.md)
- **Bibliothèques externes :** pandas

Fonctions et classes publiques :

- `creer_modele_si_absent`
- `charger`
<!-- fin-auto -->
