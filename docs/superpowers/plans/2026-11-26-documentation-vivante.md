# Documentation vivante — plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans. Steps use `- [ ]`.

**Goal:** docs/ par module, tenue à jour par un script et un contrôle CI.
**Architecture:** `outils/docs.py` lit le code avec `ast`, réécrit les blocs générés, vérifie pages et diff git.
**Tech Stack:** Python 3.12 stdlib, unittest, GitHub Actions, Markdown + Mermaid.
**Spec:** docs/superpowers/specs/2026-11-26-documentation-vivante-design.md

## Global Constraints
- Français ; aucune pièce comptable réelle dans le dépôt ; pas de nouvelle dépendance.
- Marqueurs exacts : `<!-- debut-auto -->` et `<!-- fin-auto -->`.

## Review Focus
- Import tardif dans une fonction (`from .__main__ import main` dans fenetre.py) : doit compter comme dépendance.
- Import relatif à deux points (`from .. import config`) depuis `importation/` : résolu vers `config`.
- Fichier surveillé supprimé : sa page ne doit plus être exigée.
- Fin de ligne Windows (CRLF) dans une page : le bloc ne doit pas être vu comme périmé.
- `--depuis` sur une REF inconnue : message clair, code de sortie 2.

### Task 1: outils/docs.py + tests
**Files:** Create `outils/docs.py`, `tests/test_docs.py`
**Interfaces (produit):**
- `modules(racine: Path) -> dict[str, Module]` (clé `config`, `importation.pipeline`, `windows.demarrer`)
- `Module(nom, source: Path, page: Path, imports: set[str], externes: set[str], publics: list[tuple[str, str]], lignes: int)`
- `bloc(module, tous) -> str`, `carte(tous) -> str`
- `regenerer(racine) -> list[Path]` (fichiers réécrits), `verifier(racine) -> list[str]` (problèmes)
- `pages_oubliees(racine, ref) -> list[str]`
- `main(argv) -> int` : 0 ok, 1 problèmes, 2 erreur d'usage
- [ ] tests : imports tardifs et `..` résolus ; bloc périmé signalé puis corrigé par `regenerer` ;
      page manquante et rubrique manquante signalées ; CRLF toléré ; `pages_oubliees` dans un dépôt git
      temporaire (source modifiée seule → signalée ; avec sa page → rien ; source supprimée → rien).
- [ ] lancer `python -m unittest tests.test_docs` : échec, puis implémenter, puis succès ; commit.

### Task 2: pages docs/
**Files:** `docs/README.md`, `docs/carte.md` (généré), `docs/modules/**.md`, `docs/donnees.md`,
`docs/decisions.md`, `docs/apprentissage.md`
- [ ] écrire chaque page avec les quatre rubriques ; `python outils/docs.py` ; `--verifier` = 0 ; commit.

### Task 3: règle et CI
**Files:** `CLAUDE.md`, `.github/workflows/tests.yml`, `README.md`, `CHANGEMENTS.md`
- [ ] job documentation (fetch-depth 0, `--verifier`, `--depuis origin/${{ github.base_ref }}` en PR) ; commit, PR.
