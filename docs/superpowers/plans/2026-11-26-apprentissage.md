# Apprentissage visible : plan

> Exécution : dans cette session, tâche par tâche (TDD).

**But :** transformer les corrections de compte en règles appliquées seules, analysées et visibles dans un onglet.
**Architecture :** module pur `apprentissage.py` (calcul depuis les observations), branché dans `__main__.main` après
`exercices.proposer_comptes` ; sortie `sorties/apprentissage.xlsx` ; onglet `onglet_apprentissage.py` qui la lit.
**Conception :** `docs/superpowers/specs/2026-11-26-apprentissage-design.md`.

## Contraintes globales

- Tout en français (code, messages, docs). Données de test fictives.
- `python outils/docs.py --verifier` et `--depuis origin/main` sans erreur ; version 0.8.0 dans `CHANGEMENTS.md`.

## Points de vigilance

- Ancien `mes_corrections.xlsx` sans colonne `compte` ni feuille `regles_apprises` : lu sans erreur.
- Compte saisi comme nombre dans Excel (6600.0) : lu « 6600 ».
- `mes_corrections.xlsx` ouvert dans Excel au moment d'annuler : message clair, pas de plantage.
- Aucun exercice construit : l'apprentissage fonctionne quand même (sans alerte de référentiel).
- Exercice ouvert absent ou validé lors du report : message clair.

## Tâches

1. `corrections.py` : colonne `compte`, feuille `regles_apprises`, `charger()` rend `annulees`, `annuler_regle()`, `retablir_regle()`.
   Tests : `tests/test_apprentissage.py::TestCorrections`.
2. `apprentissage.py` : `observations()`, `analyser()` → `Analyse(regles, alertes, resume)`, `appliquer()`. Tests : règle à 3,
   observation à 2, période, mot, montant, critère introuvable, correction contraire isolée, annulation, référentiel faux,
   compte absent du plan.
3. `exercices.proposer_comptes` : `compte_reference` et `origine_compte`. `sorties.py` : colonne `origine_compte`,
   `ecrire_apprentissage()`. `__main__` : appel. Test de bout en bout dans un dossier temporaire.
4. `apprentissage.reporter()` vers l'exercice ouvert. Test avec un référentiel fictif.
5. `onglet_apprentissage.py` + `fenetre.py` (`_onglet_change`). Vérification : lancement sous Xvfb et capture.
6. Docs : `docs/apprentissage.md`, pages modules, `donnees.md`, `decisions.md`, `CHANGEMENTS.md`, version, `outils/docs.py`.
