# Onglet Documents — conception (validée par V le 26.11.2026)

## Intention
V veut voir, pour chaque type de document importé, ce qui s'est passé : quel fichier, quelles pages,
comment elles ont été reconnues, les contrôles et le tableau obtenu. Le traitement reste automatique.

## Décisions
- Nouvel onglet principal « Documents », entre « Réconciliation » et « Assistant société ».
  Le bouton « Importer les documents » et « Réglages IA… » y déménagent.
- Sous-onglets : Vue d'ensemble, Plan comptable, Bilan, Compte de résultat, Grand livre, Annexe, Autres pages.
- Vue d'ensemble : un fichier par ligne (exercice, pages, sections « Bilan p.1, Grand livre p.3–4 »,
  méthodes de reconnaissance, état ✓ / ⚠).
- Onglet de type : filtre d'exercice, bloc Sources, bloc Contrôles, tableau (arbre rubrique › sous-rubrique
  › compte pour Bilan et Compte de résultat), boutons Ouvrir le document source / le classeur / la page lisible.
- Source unique : les classeurs de `entrees/06_societe/imports/AAAA` (ceux lus par l'Assistant société).
- Hors périmètre : reclasser une page à la main depuis ces onglets.

## Approches
1. Onglets tkinter dans la fenêtre, lisant les classeurs (retenue : tout au même endroit, rien à maintenir en double).
2. Page HTML à onglets : plus lisible pour les grands tableaux mais hors de la fenêtre ; les pages HTML
   existantes restent accessibles par un bouton.

## Découpage
- `importation/catalogue.py` (sans tkinter, testé) : lecture des classeurs, sections, état, vues par type, contrôles.
- `onglet_documents.py` : construction des onglets, branchée par un seul `notebook.add` dans `fenetre.py`.
- L'onglet Assistant n'est plus repéré par son index (l'insertion de « Documents » le décale).
