# onglet_documents.py

## À quoi il sert
Construit l'onglet principal « Documents » de la fenêtre : bouton d'import, réglages IA, filtre d'exercice,
une Vue d'ensemble des fichiers importés et un sous-onglet par type (Plan comptable, Bilan, Compte de résultat,
Grand livre, Annexe, Autres pages) avec sources, contrôles et tableau.

## Ce qu'il lit
Rien directement sur le disque : tout passe par `importation.catalogue.charger(dossier)`, donc par les classeurs
de `entrees/06_societe/imports/AAAA`.

## Ce qu'il écrit
Rien. Il ouvre les fichiers (document source, classeur, page lisible) avec le programme habituel.

## Ce qui casse si on le change
- `fenetre.py` appelle `construire(parent, fenetre)` et s'attend à `fenetre.btn_importer` créé ici, ainsi qu'à
  `actualiser()` et `lbl_etat` sur l'objet renvoyé.
- Il utilise `fenetre._importer`, `fenetre._reglages_ia`, `fenetre._ouvrir` et `fenetre.dossier`.
