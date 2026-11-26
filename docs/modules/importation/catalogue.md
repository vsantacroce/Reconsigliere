# importation/catalogue.py

## À quoi il sert
Relit ce qui a été importé pour l'onglet Documents, sans tkinter : liste des imports, sections trouvées,
état (OK ou à vérifier), vues par type filtrées par exercice, contrôles par type, arbre du bilan et du
compte de résultat.

## Ce qu'il lit
Les classeurs `entrees/06_societe/imports/AAAA/*.xlsx` qui ont un onglet `meta` et un onglet `pages`
(ceux du pipeline d'import). Un classeur déposé à la main sans ces onglets est ignoré.

## Ce qu'il écrit
Rien.

## Ce qui casse si on le change
- Les noms d'onglets et de colonnes viennent de `importation/sorties.py` (`COLONNES`) : les changer là change ce qui est lu ici.
- `onglet_documents.py` utilise `Import` (source, exercice, nb_pages, methodes, etat, chemin_source, html,
  resume_sections), `charger`, `exercices`, `vue` et `arbre`.
