# importation/classement.py : reconnaître le type d'une page

## À quoi il sert

Classe chaque page par des règles locales, sans IA ni coût : bilan, compte de résultat, grand livre, plan comptable, annexe ou autre.
Un titre fort (« Bilan », « Grand livre », « Erfolgsrechnung »…) décide seul. Sinon un score additionne les mots-clés, les en-têtes de
colonnes et le nombre de lignes d'écritures datées ; la page est classée si le meilleur score dépasse `SEUIL` et devance assez le second
(`ECART`), sinon elle reste indécise.

## Ce qu'il lit

Le texte et le tableau d'une page ([importation.pages](pages.md)).

## Ce qu'il écrit

Rien. Rend `(type ou None, score, titre fort trouvé)`. Fournit aussi `TYPES` et `LIBELLES`.

## Ce qui casse si on le change

- **Titres, indices, `SEUIL`, `ECART`** : plus de pages indécises = plus d'appels à l'IA (coût) ou de choix manuels ; moins = plus
  d'erreurs de type. Tester avec `tests/test_importation_classement.py`.
- **`TYPES`** est la liste des réponses acceptées de l'IA ([importation.ia](ia.md)) et des choix proposés dans la fenêtre.
  Ajouter un type demande un extracteur ([importation.extracteurs](extracteurs.md)) et un onglet de sortie.
- `lignes_ecritures` et `lignes_plan` servent aussi à la passe de continuité.

## Dépendances (automatique)

<!-- debut-auto -->
_Partie générée par `python outils/docs.py` à partir du code : ne pas la modifier à la main._

- **Fichier :** `src/reconsigliere/importation/classement.py` (107 lignes)
- **Dépend de :** [importation.pages](pages.md), [outils](../outils.md)
- **Utilisé par :** [fenetre](../fenetre.md), [importation.continuite](continuite.md), [importation.extracteurs](extracteurs.md), [importation.ia](ia.md), [importation.pipeline](pipeline.md), [importation.sorties](sorties.md)
- **Bibliothèques externes :** aucune

Fonctions et classes publiques :

- `lignes`
- `lignes_ecritures` : Nombre de lignes qui portent une date et au moins un montant (typique du grand livre).
- `lignes_plan`
- `titre` : Type annoncé par un titre dans les premières lignes de la page.
- `classer` : Renvoie (type ou None si indécis, score du meilleur type, titre fort trouvé).
<!-- fin-auto -->
