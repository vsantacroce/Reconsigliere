@echo off
rem Double-clique sur ce fichier pour ouvrir la fenêtre de Reconsigliere.
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONPATH=%~dp0src

where py >nul 2>nul && (set PY=py -3) || (set PY=python)
%PY% --version >nul 2>nul
if errorlevel 1 (
  echo Python n'est pas installe.
  echo Installe-le depuis https://www.python.org/downloads/ en cochant "Add python.exe to PATH",
  echo ou dans un terminal : winget install --id Python.Python.3.12 -e
  pause
  exit /b 1
)

rem Installe les bibliotheques une seule fois, puis a chaque changement de requirements.txt
if not exist ".installe" goto installer
fc /b requirements.txt .installe >nul 2>nul || goto installer
goto ouvrir

:installer
echo Premiere installation des bibliotheques, une minute...
%PY% -m pip install -q -r requirements.txt
if errorlevel 1 (
  echo L'installation a echoue. Verifie la connexion internet puis relance.
  pause
  exit /b 1
)
copy /y requirements.txt .installe >nul

:ouvrir
rem pythonw ouvre la fenetre sans console noire
where pyw >nul 2>nul && (start "" pyw -3 -m reconsigliere.fenetre & exit /b 0)
where pythonw >nul 2>nul && (start "" pythonw -m reconsigliere.fenetre & exit /b 0)
%PY% -m reconsigliere.fenetre
