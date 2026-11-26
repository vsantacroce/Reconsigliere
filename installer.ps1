# Installe Reconsigliere sur Windows, une seule fois.
# Dans PowerShell :
#   irm https://raw.githubusercontent.com/vsantacroce/reconsigliere/main/installer.ps1 | iex
#
# Ce que fait ce script :
#  1. installe Python 3.12 pour ton compte s'il manque (sans droits administrateur) ;
#  2. télécharge Reconsigliere dans %LOCALAPPDATA%\Reconsigliere ;
#  3. installe les bibliothèques dans un environnement isolé ;
#  4. crée une icône sur le bureau et dans le menu Démarrer ;
#  5. ouvre Reconsigliere.
# Ensuite, l'icône met le programme à jour toute seule à chaque ouverture.
# Tes relevés et tes factures restent dans ton dossier de travail (Documents\Reconsigliere), jamais touché.

param([string]$Branche = "main")

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"   # accélère fortement Invoke-WebRequest
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$Depot = "vsantacroce/reconsigliere"
$Base = Join-Path $env:LOCALAPPDATA "Reconsigliere"
$VersionPython = "3.12.10"

function Etape($texte) { Write-Host "`n» $texte" -ForegroundColor Cyan }

function Trouver-Python {
    $candidats = @()
    if (Get-Command py -ErrorAction SilentlyContinue) { $candidats += ,@("py", "-3") }
    if (Get-Command python -ErrorAction SilentlyContinue) { $candidats += ,@("python") }
    $candidats += ,@((Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe"))
    foreach ($c in $candidats) {
        $exe = $c[0]; $args_ = @($c | Select-Object -Skip 1)
        if (-not (Get-Command $exe -ErrorAction SilentlyContinue) -and -not (Test-Path $exe)) { continue }
        try {
            $chemin = & $exe @args_ -c "import sys, tkinter; assert sys.version_info >= (3, 10); print(sys.executable)" 2>$null
            if ($LASTEXITCODE -eq 0 -and $chemin -and (Test-Path $chemin.Trim())) { return $chemin.Trim() }
        } catch { }
    }
    return $null
}

Write-Host "Installation de Reconsigliere" -ForegroundColor Green

Etape "Recherche de Python"
$Python = Trouver-Python
if (-not $Python) {
    Write-Host "Python est absent : installation de Python $VersionPython pour ton compte…"
    $installe = $false
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        winget install --id Python.Python.3.12 -e --scope user --silent `
            --accept-package-agreements --accept-source-agreements | Out-Host
        $Python = Trouver-Python
        $installe = [bool]$Python
    }
    if (-not $installe) {
        $exe = Join-Path $env:TEMP "python-$VersionPython-amd64.exe"
        Invoke-WebRequest "https://www.python.org/ftp/python/$VersionPython/python-$VersionPython-amd64.exe" -OutFile $exe
        Start-Process $exe -Wait -ArgumentList "/quiet", "InstallAllUsers=0", "PrependPath=1", "Include_tcltk=1", "Include_launcher=1"
        Remove-Item $exe -ErrorAction SilentlyContinue
        $Python = Trouver-Python
    }
    if (-not $Python) { throw "Python n'a pas pu être installé. Installe-le depuis python.org puis relance ce script." }
}
Write-Host "Python : $Python"

Etape "Téléchargement de Reconsigliere ($Branche)"
New-Item -ItemType Directory -Force -Path $Base | Out-Null
$Sha = (Invoke-WebRequest "https://api.github.com/repos/$Depot/commits/$([uri]::EscapeDataString($Branche))" `
        -Headers @{ Accept = "application/vnd.github.sha"; "User-Agent" = "Reconsigliere-installer" } -UseBasicParsing).Content
if ($Sha -is [byte[]]) { $Sha = [Text.Encoding]::ASCII.GetString($Sha) }
$Sha = $Sha.Trim()
$Zip = Join-Path $env:TEMP "reconsigliere-$Sha.zip"
Invoke-WebRequest "https://codeload.github.com/$Depot/zip/$Sha" -OutFile $Zip -UseBasicParsing
$Temp = Join-Path $Base "app.nouveau"
Remove-Item $Temp -Recurse -Force -ErrorAction SilentlyContinue
Expand-Archive $Zip -DestinationPath $Temp -Force
Remove-Item $Zip
$Racine = Get-ChildItem $Temp -Directory | Select-Object -First 1
$App = Join-Path $Base "app"
Remove-Item $App -Recurse -Force -ErrorAction SilentlyContinue
Move-Item $Racine.FullName $App
Remove-Item $Temp -Recurse -Force
Set-Content (Join-Path $Base "version.txt") $Sha -NoNewline -Encoding ASCII
Set-Content (Join-Path $Base "branche.txt") $Branche -NoNewline -Encoding ASCII

Etape "Installation des bibliothèques (une à deux minutes)"
$Venv = Join-Path $Base "venv"
if (-not (Test-Path (Join-Path $Venv "Scripts\pythonw.exe"))) { & $Python -m venv $Venv }
$PyVenv = Join-Path $Venv "Scripts\python.exe"
& $PyVenv -m pip install -q --disable-pip-version-check -r (Join-Path $App "requirements.txt")
if ($LASTEXITCODE -ne 0) { throw "L'installation des bibliothèques a échoué." }
Copy-Item (Join-Path $App "requirements.txt") (Join-Path $Base "requirements.installe") -Force

Etape "Création des icônes"
Copy-Item (Join-Path $App "windows\demarrer.pyw") $Base -Force
Copy-Item (Join-Path $App "windows\reconsigliere.ico") $Base -Force
Copy-Item (Join-Path $App "windows\desinstaller.ps1") $Base -Force
$Shell = New-Object -ComObject WScript.Shell
$Icone = Join-Path $Base "reconsigliere.ico"
$PyW = Join-Path $Venv "Scripts\pythonw.exe"
$Menu = Join-Path ([Environment]::GetFolderPath("Programs")) "Reconsigliere"
New-Item -ItemType Directory -Force -Path $Menu | Out-Null

function Raccourci($chemin, $cible, $arguments, $description) {
    $r = $Shell.CreateShortcut($chemin)
    $r.TargetPath = $cible
    $r.Arguments = $arguments
    $r.WorkingDirectory = $Base
    $r.IconLocation = $Icone
    $r.Description = $description
    $r.Save()
}
$Demarrer = '"' + (Join-Path $Base "demarrer.pyw") + '"'
Raccourci (Join-Path ([Environment]::GetFolderPath("Desktop")) "Reconsigliere.lnk") $PyW $Demarrer "Le consigliere de ta compta"
Raccourci (Join-Path $Menu "Reconsigliere.lnk") $PyW $Demarrer "Le consigliere de ta compta"
Raccourci (Join-Path $Menu "Désinstaller Reconsigliere.lnk") "powershell.exe" `
    ('-NoProfile -ExecutionPolicy Bypass -File "' + (Join-Path $Base "desinstaller.ps1") + '"') "Retire le programme, garde tes données"

Etape "Ouverture de Reconsigliere"
Start-Process $PyW -ArgumentList $Demarrer -WorkingDirectory $Base
Write-Host "`nC'est installé. La prochaine fois, double-clique sur l'icône Reconsigliere du bureau." -ForegroundColor Green
