# Désinstalle Reconsigliere. Ton dossier de travail (relevés, factures, résultats) est conservé.
$ErrorActionPreference = "Continue"
Add-Type -AssemblyName PresentationFramework
$reponse = [System.Windows.MessageBox]::Show(
    "Retirer Reconsigliere de cet ordinateur ?`n`nTon dossier de travail (relevés, factures, résultats) est conservé.",
    "Reconsigliere", "YesNo", "Question")
if ($reponse -ne "Yes") { exit }

$Base = Join-Path $env:LOCALAPPDATA "Reconsigliere"
Remove-Item (Join-Path ([Environment]::GetFolderPath("Desktop")) "Reconsigliere.lnk") -ErrorAction SilentlyContinue
Remove-Item (Join-Path ([Environment]::GetFolderPath("Programs")) "Reconsigliere") -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item (Join-Path $env:APPDATA "Reconsigliere") -Recurse -Force -ErrorAction SilentlyContinue
Set-Location $env:TEMP
Remove-Item $Base -Recurse -Force -ErrorAction SilentlyContinue
[System.Windows.MessageBox]::Show("Reconsigliere a été retiré. Ton dossier de travail est toujours là.", "Reconsigliere") | Out-Null
