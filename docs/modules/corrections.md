# corrections.py : tes corrections manuelles

## À quoi il sert

Crée et lit `mes_corrections.xlsx`, le fichier où tu fais avancer la réconciliation à la main. Tes corrections passent toujours
avant le rapprochement automatique. C'est la source de tout ce que le programme apprend de toi : voir
[apprentissage.md](../apprentissage.md) et le module [apprentissage](apprentissage.md).

Il écrit aussi la feuille `regles_apprises` quand tu annules ou rétablis une règle apprise dans l'onglet Apprentissage
(`annuler_regle`, `retablir_regle`).

## Ce qu'il lit

`entrees/05_mes_corrections/mes_corrections.xlsx` :

- feuille `partenaires` : `mot_dans_libelle`, `partenaire` (si le libellé bancaire contient le mot, ce partenaire est utilisé) ;
- feuille `transactions` : `id_transaction`, `date`, `montant`, `libelle`, `partenaire`, `pdf`, `explication`, `statut_force`, `compte`
  (le bon compte, lu en texte : `6600` saisi comme nombre reste `6600`) ;
- feuille `regles_apprises` : `partenaire`, `compte`, `decision` (`annulée`), `le`. Un ancien fichier sans cette feuille ni la colonne
  `compte` est lu sans erreur.

## Ce qu'il écrit

Le modèle `mes_corrections.xlsx` au premier lancement (avec un exemple `SWISSCOM`, la feuille `regles_apprises` vide et une feuille `aide`),
seulement s'il n'existe pas. Annuler une règle ajoute la feuille `regles_apprises` à un ancien fichier, sans toucher aux autres feuilles.

## Ce qui casse si on le change

- **Noms des feuilles et des colonnes** : les fichiers déjà remplis par l'utilisateur ne seraient plus lus. Tout renommage doit lire
  aussi l'ancien nom.
- **Valeurs de `statut_force`** (`Comptabilise`, `Sans piece`, `A comptabiliser`, `Ignorer`) : comparées dans [rapprochement](rapprochement.md)
  (`STATUTS_FORCES`), après normalisation.
- Les lignes commençant par `exemple` sont ignorées.
- **Colonne `compte`** : chaque ligne remplie compte pour l'apprentissage ; supprimer la ligne retire son effet au lancement suivant.

## Dépendances (automatique)

<!-- debut-auto -->
_Partie générée par `python outils/docs.py` à partir du code : ne pas la modifier à la main._

- **Fichier :** `src/reconsigliere/corrections.py` (104 lignes)
- **Dépend de :** [config](config.md), [outils](outils.md)
- **Utilisé par :** [__main__](__main__.md), [onglet_apprentissage](onglet_apprentissage.md)
- **Bibliothèques externes :** openpyxl, pandas

Fonctions et classes publiques :

- `creer_modele_si_absent`
- `charger`
- `annuler_regle` : Met de côté une règle apprise. Lève PermissionError si le fichier est ouvert dans Excel.
- `retablir_regle` : Retire la ligne d'annulation : la règle s'applique de nouveau au prochain lancement.
<!-- fin-auto -->
