# Où le programme apprend

« Apprendre », dans Reconsigliere, veut dire : réutiliser ce que tu as corrigé ou validé une fois pour mieux proposer la fois suivante.
Il n'y a pas d'apprentissage caché : tout ce que le programme retient est dans un fichier que tu peux ouvrir.
État au 26.11.2026 (version 0.6.0).

## Ce qu'il retient aujourd'hui

### 1. Les règles de partenaires (`mes_corrections.xlsx`, feuille `partenaires`)

Tu écris « si le libellé bancaire contient `SWISSCOM`, le partenaire est `Swisscom` ». À chaque réconciliation, cette règle passe
avant tout le reste ([rapprochement](modules/rapprochement.md), étape partenaire), puis le partenaire compte pour 20 points
dans le score qui choisit la pièce. Une règle écrite une fois sert pour toutes les transactions futures.

### 2. Le compte habituel de chaque partenaire (référentiel de l'exercice, onglet `Partenaires`)

Quand un exercice est construit depuis le grand livre ([exercices](modules/exercices.md)), le programme note, pour chaque partenaire,
le compte le plus souvent utilisé avec lui (sans les comptes de banque, débiteurs, créanciers et TVA) et la part des écritures qui l'ont
utilisé. À la réconciliation, chaque transaction reçoit un « Compte proposé » d'après le référentiel de son exercice, avec cette fiabilité
(« 92 % sur 25 écritures, selon partenaire, référentiel 2024 »). L'exercice validé l'an passé sert donc de mémoire pour l'année en cours ;
les demandes de changement de l'année la corrigent.

### 3. Les liens imposés (`mes_corrections.xlsx`, feuille `transactions`)

Un PDF, un statut ou une explication donnés pour une transaction sont réappliqués à chaque lancement. Mais ils ne valent que pour
**cette** transaction (identifiée par date, montant et libellé) : ils n'améliorent pas les propositions pour les autres.

## Ce qu'il ne retient pas encore

- Une pièce liée à la main n'apprend rien au score : le même fournisseur sera de nouveau proposé avec le même score le mois suivant.
- Un compte proposé que tu corriges dans ta comptabilité ne revient dans le référentiel qu'au prochain grand livre importé,
  ou par une demande de changement.
- Le type de page que tu choisis à la main pendant un import n'est pas mémorisé : un document de même forme reposera la question.
- Les règles de classement des pages ([importation.classement](modules/importation/classement.md)) sont fixes, dans le code.

Un écran « Apprentissage » qui montre ces mémoires dans la fenêtre est en préparation ; cette page sera mise à jour avec lui.
