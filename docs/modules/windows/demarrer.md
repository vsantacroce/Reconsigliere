# windows/demarrer.pyw : le lanceur installé, qui se met à jour

## À quoi il sert

Lancé par l'icône du bureau. À chaque ouverture : demande à GitHub le dernier commit de `main`, télécharge le code s'il est plus récent,
réinstalle les bibliothèques si `requirements.txt` a changé, puis ouvre la fenêtre ([fenetre](../fenetre.md)). Sans internet ou en cas
d'erreur, la version installée s'ouvre.

## Ce qu'il lit

- `api.github.com` (dernier commit) et `codeload.github.com` (zip du code), avec un délai réseau de 5 secondes.
- Dans `%LOCALAPPDATA%\Reconsigliere` : `version.txt`, `branche.txt` (branche suivie, `main` par défaut), `requirements.installe`.

## Ce qu'il écrit

Dans `%LOCALAPPDATA%\Reconsigliere` : le dossier `app` (remplacé à chaque mise à jour), `version.txt`, `requirements.installe`,
`journal.txt`. Il ne touche jamais au dossier de travail.

## Ce qui casse si on le change

- **Tout ce qui est poussé sur `main` arrive chez l'utilisateur à l'ouverture suivante.** Une erreur fusionnée dans `main` est
  installée sans contrôle : d'où l'importance des tests GitHub avant fusion.
- Il est copié par [installer.ps1](installer.md) : une modification de ce fichier n'atteint les installations existantes que par
  la mise à jour elle-même ; une erreur qui l'empêche de démarrer oblige à relancer l'installateur.
- Nouvelle bibliothèque dans `requirements.txt` : installée automatiquement à la prochaine ouverture (connexion requise).

## Dépendances (automatique)

<!-- debut-auto -->
_Partie générée par `python outils/docs.py` à partir du code : ne pas la modifier à la main._

- **Fichier :** `windows/demarrer.pyw` (196 lignes)
- **Dépend de :** aucun autre module du programme
- **Utilisé par :** aucun module (point d'entrée)
- **Bibliothèques externes :** aucune

Fonctions et classes publiques :

- `dossier_base`
- `journaliser`
- `lire`
- `requete`
- `dernier_commit`
- `python_console` : pythonw.exe n'a pas de sortie : pip doit tourner avec python.exe, dans le même dossier.
- `installer_bibliotheques`
- `mettre_a_jour`
- `Ecran` : Petite fenêtre « Mise à jour… », créée seulement si une mise à jour a lieu.
- `verifier_mise_a_jour`
- `ouvrir`
<!-- fin-auto -->
