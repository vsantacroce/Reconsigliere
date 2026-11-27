# installer.ps1 et windows/desinstaller.ps1 : installation Windows

## À quoi il sert

`installer.ps1` installe Reconsigliere en une commande PowerShell (`irm …/installer.ps1 | iex`), sans droits administrateur :
Python 3.12 si besoin (winget, sinon python.org), code dans `%LOCALAPPDATA%\Reconsigliere\app`, bibliothèques dans un environnement
isolé, icônes du bureau et du menu Démarrer. `windows/desinstaller.ps1` retire le programme et les icônes et garde le dossier de travail.

## Ce qu'il lit

Le dépôt GitHub (`main`), `requirements.txt`, `windows/demarrer.pyw`, les icônes `windows/reconsigliere.ico|png`.

## Ce qu'il écrit

`%LOCALAPPDATA%\Reconsigliere` (code, environnement Python, lanceur) et les raccourcis. Jamais le dossier de travail.

## Ce qui casse si on le change

- Le chemin d'installation est aussi codé dans [windows.demarrer](demarrer.md) : les deux doivent rester d'accord.
- Il n'a encore jamais été exécuté sur un vrai Windows : toute modification doit être essayée sur Windows avant d'être annoncée.
- Le dépôt `vsantacroce/reconsigliere` et la branche `main` y sont écrits en dur.
