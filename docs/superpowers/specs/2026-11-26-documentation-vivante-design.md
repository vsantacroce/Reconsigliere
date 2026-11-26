# Documentation vivante — conception

## Intention

V veut pouvoir revenir sur Reconsigliere des mois plus tard et comprendre chaque module : ce qu'il fait,
ce qu'il lit et écrit, de qui il dépend, et ce qu'un changement implique. La documentation doit suivre
chaque modification du code sans dépendre de la mémoire de qui que ce soit.

## Objectifs

- `docs/` en français, lisible par un comptable : vue d'ensemble avec schéma du flux, une page par module,
  les fichiers de données, le journal des décisions, et où le programme apprend.
- Mise à jour forcée : un contrôle GitHub échoue si la documentation ne suit pas le code.
- Règle écrite dans `CLAUDE.md` pour toute future session.

## Non-objectifs

- Pas de documentation d'API générée en entier (illisible pour V, n'explique pas le pourquoi).
- Pas d'outil externe (Sphinx, MkDocs) : du Markdown lu directement sur GitHub, schémas Mermaid.

## Approches

1. **Pages écrites à la main + bloc généré + contrôle CI (retenue).** Le texte (rôle, implications)
   est écrit à la main ; un script génère dans chaque page un bloc entre marqueurs (dépendances,
   utilisé par, fonctions) et la carte des modules. CI : bloc périmé = échec ; module modifié sans
   sa page = échec.
2. Tout générer depuis les docstrings : toujours juste, mais n'explique ni le rôle métier ni les
   implications.
3. Pages à la main seulement + règle CLAUDE.md : simple, mais rien n'empêche l'oubli.

## Conception

- `outils/docs.py` (bibliothèque standard seulement, `ast`) :
  - surveille `src/reconsigliere/**/*.py` (sauf `__init__.py`), `windows/demarrer.pyw`, et des
    fichiers associés (`modele.html` → page `sorties`, `modele_societe.html` → page `societe`,
    `installer.ps1` et `windows/desinstaller.ps1` → page `windows/installer`) ;
  - page de `src/reconsigliere/a/b.py` = `docs/modules/a/b.md` ;
  - `python outils/docs.py` régénère les blocs `<!-- debut-auto -->…<!-- fin-auto -->` et `docs/carte.md` ;
  - `--verifier` : échoue si une page manque, s'il lui manque une rubrique obligatoire
    (« À quoi il sert », « Ce qu'il lit », « Ce qu'il écrit », « Ce qui casse si on le change »)
    ou si un bloc généré n'est pas à jour ;
  - `--depuis REF` : échoue si un fichier surveillé a changé depuis REF sans que sa page change.
- CI (`.github/workflows/tests.yml`) : job « documentation » qui lance `--verifier` à chaque envoi et
  `--depuis` la base de la PR sur les pull requests.
- `CHANGEMENTS.md` reste le journal des versions ; `docs/decisions.md` garde le pourquoi des choix.

## Laissé au constructeur

La présentation exacte du bloc généré, l'ordre des pages dans l'index.
