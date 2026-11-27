# Plan : onglets directs

Conception : `docs/superpowers/specs/2026-11-27-onglets-directs-design.md`.

1. Tests (`tests/test_onglets.py`, données fictives) : ordre des onglets, aucun intitulé « État de la société » ni
   « Exercices » ; lignes des projets et revenus depuis un `societe.Etat` ; lignes du plan comptable et des partenaires depuis
   un référentiel construit ; taille de fenêtre bornée à l'écran et agrandie selon l'échelle. Les voir échouer.
2. Module `onglets_societe.py` : `ONGLETS`, `lignes_projets`, `lignes_revenus`, `lignes_referentiel`, `geometrie`, et la classe
   `OngletTableau` (phrase, choix d'année facultatif, tableau, boutons). Tests au vert.
3. `fenetre.py` : barre d'onglets sur deux lignes, carnet sans rangée d'onglets, un cadre par onglet, `_onglet_change` par
   dictionnaire cadre → actualisation, Brevets sans projets ni revenus, intitulés de l'Année comptable, onglet Salaires
   facultatif, taille de fenêtre par `geometrie`.
4. Messages qui citent « Assistant société » (apprentissage) → « onglet Année comptable ».
5. Captures sous Xvfb à l'échelle normale et à 150 %.
6. Documentation vivante, `CHANGEMENTS.md` (0.9.0), README ; `outils/docs.py --verifier`.
