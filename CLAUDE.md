# Règles pour travailler sur Reconsigliere

- Répondre et documenter en français.
- Les pièces comptables réelles ne vont jamais dans le dépôt (ni dans `tests/`, ni dans `docs/`).
- Pour une nouvelle fonctionnalité ou une planification : skills superpowers (brainstorming, writing-plans,
  test-driven-development), conception proposée avant de coder.

## Documentation vivante (obligatoire à chaque modification du code)

La documentation du programme est dans `docs/` (voir `docs/README.md`). Dans la même modification que le code :

1. Pour chaque module modifié ou ajouté (`src/reconsigliere/a/b.py` → `docs/modules/a/b.md`, `windows/demarrer.pyw`,
   gabarits `modele*.html`, `installer.ps1`), mettre à jour le texte des quatre rubriques : « À quoi il sert »,
   « Ce qu'il lit », « Ce qu'il écrit », « Ce qui casse si on le change ». Écrire pour un comptable, pas pour un développeur.
2. Lancer `python outils/docs.py` pour régénérer les parties automatiques et `docs/carte.md` (un nouveau module reçoit une page à compléter).
3. Si un fichier lu ou écrit change (dossier, onglet, colonne), mettre à jour `docs/donnees.md`.
4. Si un choix non évident est fait (seuil, format, règle comptable), ajouter une ligne à `docs/decisions.md`.
5. Si ce que le programme retient change, mettre à jour `docs/apprentissage.md`.
6. Ajouter l'entrée de version dans `CHANGEMENTS.md`.
7. Vérifier : `python outils/docs.py --verifier` et `python outils/docs.py --depuis origin/main` doivent sortir sans erreur.
   Le contrôle GitHub « Documentation » lance les mêmes commandes.

Tests : `python -m unittest discover -s tests`.
