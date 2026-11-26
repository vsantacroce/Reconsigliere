# importation/ia.py : l'IA en secours

## À quoi il sert

Pour les seules pages restées indécises, demande à Claude (Haiku par défaut, Sonnet en option) de répondre par un mot parmi les types
connus. Envoie un extrait court (2'000 caractères au plus) et le type de la section précédente. Sans clé API, rien n'est envoyé.

## Ce qu'il lit

- La clé API : variable `ANTHROPIC_API_KEY`, sinon `cle_api_anthropic` dans `reglages.json` ([installation](../installation.md)).
- Le modèle : `RECONSIGLIERE_MODELE`, sinon `modele_ia` dans les réglages, sinon `haiku`.

## Ce qu'il écrit

Rien sur le disque. Envoie l'extrait à l'API Anthropic (bibliothèque `anthropic`). Rend le type et les tokens consommés.

## Ce qui casse si on le change

- **Ce qui part chez Anthropic** : seulement l'extrait de la page indécise. Allonger `EXTRAIT_MAX` augmente le coût et la quantité de
  données comptables envoyées.
- **`MODELES` et `PRIX`** : identifiants et tarifs à tenir à jour ; un identifiant retiré par Anthropic fait échouer les appels
  (la page passe alors au choix manuel, sans planter).
- **`interpreter`** n'accepte qu'une réponse de `TYPES` : une réponse hors liste compte comme un échec.

## Dépendances (automatique)

<!-- debut-auto -->
_Partie générée par `python outils/docs.py` à partir du code : ne pas la modifier à la main._

- **Fichier :** `src/reconsigliere/importation/ia.py` (108 lignes)
- **Dépend de :** [importation.classement](classement.md), [installation](../installation.md), [outils](../outils.md)
- **Utilisé par :** [__main__](../__main__.md), [fenetre](../fenetre.md), [importation.banc](banc.md), [importation.pipeline](pipeline.md)
- **Bibliothèques externes :** anthropic

Fonctions et classes publiques :

- `cle_api`
- `modele`
- `extrait`
- `requete`
- `envoyeur_sdk`
- `interpreter`
- `classer_par_ia` : (type, {entree, sortie}) ; type None si l'appel échoue ou est refusé.
- `cout_usd`
<!-- fin-auto -->
