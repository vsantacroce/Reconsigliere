# installation.py : le dossier de travail et les réglages mémorisés

## À quoi il sert

Gère le dossier de travail (celui qui contient `entrees` et `sorties`), séparé du code : le crée avec tous ses sous-dossiers et leurs
fichiers `LISEZMOI.md`, mémorise le choix, compte les fichiers déposés, ouvre un dossier ou un fichier dans l'explorateur.
Il garde aussi les réglages personnels : dossier, clé API, modèle d'IA.

## Ce qu'il lit

- `reglages.json` : `%APPDATA%\Reconsigliere\reglages.json` sous Windows, `~/.config/Reconsigliere/reglages.json` sous Linux.
  Clés connues : `dossier_travail`, `cle_api_anthropic`, `modele_ia`.

## Ce qu'il écrit

- Les dossiers `entrees/01_factures` à `entrees/07_documents`, `entrees/06_societe/imports`, `sorties`, et un `LISEZMOI.md`
  dans chacun, sans jamais écraser un fichier existant.
- `reglages.json` (`ecrire_reglage` change une clé sans effacer les autres).

## Ce qui casse si on le change

- **La liste `DOSSIERS`** doit correspondre aux chemins de [config](config.md) et à ceux lus par [societe](societe.md),
  [exercices](exercices.md) et [importation.pipeline](importation/pipeline.md).
- **L'emplacement ou le nom de `reglages.json`** : changer fait oublier le dossier de travail et la clé API à chaque installation existante.
- **`resoudre`** décide si un dossier choisi est déjà un dossier de travail (il contient `entrees`) ou s'il faut y créer `Reconsigliere`.
  Le modifier peut créer un second dossier de travail vide à côté de l'ancien.
- La clé API y est stockée en clair, dans le profil de l'utilisateur, jamais dans le dépôt.

## Dépendances (automatique)

<!-- debut-auto -->
_Partie générée par `python outils/docs.py` à partir du code : ne pas la modifier à la main._

- **Fichier :** `src/reconsigliere/installation.py` (148 lignes)
- **Dépend de :** aucun autre module du programme
- **Utilisé par :** [__main__](__main__.md), [fenetre](fenetre.md), [importation.ia](importation/ia.md), [societe](societe.md)
- **Bibliothèques externes :** aucune

Fonctions et classes publiques :

- `resoudre` : Le dossier choisi par l'utilisateur devient le dossier de travail s'il en est déjà un
- `est_installe`
- `creer_dossiers` : Crée les dossiers manquants et leur LISEZMOI. Ne touche jamais aux fichiers existants.
- `compter_fichiers`
- `lire_reglages`
- `ecrire_reglage` : Change un réglage sans effacer les autres (dossier, clé API, modèle IA…).
- `dossier_memorise`
- `memoriser`
- `dossier_propose`
- `ouvrir` : Ouvre un dossier dans l'explorateur ou un fichier avec son programme habituel.
<!-- fin-auto -->
