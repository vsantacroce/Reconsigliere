# Pipeline d'import de documents — conception

## Intention
V veut déposer n'importe quel document comptable (PDF, photo, Excel) et obtenir, sans ressaisie, des tableaux propres utilisés par l'« Assistant société » (référentiel par exercice : plan comptable, partenaires → comptes). Un même document peut contenir plusieurs états (bilan, compte de résultat, grand livre…). Contrainte forte : coût en tokens minimal.

## Objectifs
- Accepter `.pdf`, `.png/.jpg/.jpeg/.tif/.tiff`, `.xlsx/.xls/.csv`.
- Classer chaque page (ou feuille Excel) : `bilan`, `compte_resultat`, `grand_livre`, `plan_comptable`, `annexe`, `autre`.
- Regrouper les pages consécutives d'une même section (passe de continuité).
- Envoyer chaque section à un extracteur spécialisé qui produit un tableau normalisé.
- Écrire un classeur normalisé + une page HTML lisible ; contrôles de cohérence.

## Non-objectifs
- Versionnage, validation, verrouillage des exercices (fil « Assistant société »).
- Rapprochement bancaire (inchangé).

## Anti-objectifs
- Envoyer un document entier à l'IA. Envoyer quoi que ce soit à l'IA quand les règles suffisent.
- Écrire dans `exercices/AAAA` (réservé au versionnage).

## Approches considérées
1. **Déterministe d'abord, IA en secours (retenue).** Texte local (pypdf, Tesseract pour images et pages scannées, pandas pour Excel), classement par mots-clés et en-têtes, continuité par règles ; IA uniquement sur les pages restées ambiguës, extrait ≤ 2 000 caractères, Haiku, réponse d'un mot.
2. Tout par IA (vision sur chaque page) : simple mais coûteux, rejeté par la contrainte tokens.
3. Sans IA du tout : zéro coût mais oblige V à choisir à la main chaque page ambiguë. Conservé comme repli quand aucune clé n'est configurée.

Choix d'accès à l'IA (carte, option recommandée retenue) : **IA si une clé API est présente** (`ANTHROPIC_API_KEY` ou réglage `cle_api_anthropic`), sinon choix manuel dans la fenêtre (ou type `a_verifier` en ligne de commande).

## Fonctionnement
1. **Pages** : chaque page PDF devient une `Page(numero, texte, tableau=None)`. Page PDF avec < 40 caractères de texte : OCR (pdftoppm + Tesseract) si disponibles, sinon page marquée illisible. Image : OCR. Excel/CSV : une page par feuille, avec `tableau` (DataFrame).
2. **Classement par règles** : score par type = somme des poids des mots-clés trouvés (titres forts : « bilan », « compte de résultat », « grand livre », « plan comptable », « annexe » ; indices : « total des actifs », « passifs », « produits », « charges », « solde reporté », « débit/crédit »…), plus indices de structure (en-têtes Excel). Décision si meilleur score ≥ 3 et ≥ 1,5 × le deuxième. Sinon : `None` (indécis).
3. **Continuité** : une page indécise ou sans titre fort hérite du type de la section précédente si un signe de continuité existe : « report / solde reporté / à reporter », mêmes en-têtes de colonnes, numérotation « Page n/m » qui suit, ou densité de lignes date+montant pour un grand livre. Un titre fort d'un autre type ouvre une nouvelle section.
4. **IA** : seules les pages encore indécises après la continuité ; un appel par page, extrait court, `max_tokens` 5. Réponse hors liste → `autre`.
5. **Extracteurs** : un par type. Excel : correspondance d'en-têtes par synonymes. Texte : expressions régulières ligne par ligne. Annexe/autre : texte conservé.
6. **Contrôles** : grand livre équilibré (Σ débit = Σ crédit à 0,01 près), bilan (total actifs = total passifs quand les deux totaux sont lus), pages illisibles, pages classées par IA ou à la main signalées.
7. **Sorties** : `entrees/06_societe/imports/AAAA/<nom>.xlsx` et `sorties/imports/<nom>.html`.

## Format de sortie (convenu avec le fil société)
Onglets : `meta(cle, valeur)` avec societe, date_debut, date_fin, devise, fichier_source ; `plancomptable(code, nom, type, exercice, source)` ; `grandlivre(date, compte, libelle_compte, piece, partenaire, libelle, debit, credit, exercice, source)` ; `bilan` et `compteresultat(rubrique, compte, libelle, montant, colonne_exercice_precedent, niveau, exercice, source)` ; `annexe(page, texte, source)` ; `pages(page, type, methode, score, source)` ; `controles(controle, resultat, detail)`.
Règles : exercice entier ; code/compte en texte ; débit et crédit positifs ou vides ; partenaire vide si absent ; bilan/PNL gardent le signe du document ; niveau 1/2/3 si déductible ; dates ISO ; `source` = « fichier p.N ».
Exercice : année majoritaire des dates trouvées (« 31.12.2024 », « exercice 2024 », dates du grand livre), sinon année en cours.

## Décisions laissées au constructeur
Poids exacts des mots-clés, liste des synonymes d'en-têtes, présentation HTML.
