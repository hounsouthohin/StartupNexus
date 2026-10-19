# Un LOT de briefs lus par la session Claude isolée (boîte aux lettres), puis fabriqués et jugés.
# Usage : powershell -NoProfile -ExecutionPolicy Bypass -File usine/outils/lot.ps1 <nom du lot> <apprentissage|corpus> <brief> <brief> …
# Journal : runs/lots/lot-<nom>.log (se termine par « == LOT <nom> — FIN »). Lancer de préférence détaché (Start-Process),
# puis ouvrir la session isolée (C:\Users\BAMBARA Arthur\lecteur-isole) avec : « Lis le fichier DEMARRAGE.md de ce dossier
# et suis-le exactement. »
param([string]$lot, [string]$source, [Parameter(ValueFromRemainingArguments = $true)][string[]]$briefs)
$racine = "C:\Users\BAMBARA Arthur\Desktop\StartupNexus"
New-Item -ItemType Directory -Force "$racine\runs\lots" | Out-Null
$log = "$racine\runs\lots\lot-$lot.log"
$ecrire = { param($t) [IO.File]::AppendAllText($log, "$t`r`n", (New-Object Text.UTF8Encoding $false)) }
# pas de mise en veille TANT QUE ce script tourne (aucun réglage de Windows n'est changé)
Add-Type -Namespace Usine -Name Veille -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint f);'
[Usine.Veille]::SetThreadExecutionState([uint32]"0x80000001") | Out-Null
Set-Location $racine
$env:PYTHONPATH = $racine
$env:PYTHONIOENCODING = "utf-8"
if (Test-Path $log) { Remove-Item $log }
& $ecrire "== LOT $lot — début $(Get-Date -Format s)"
cmd /c "docker exec temporal-postgresql psql -U temporal -d postgres -c ""select 1"" >nul 2>&1"
if ($LASTEXITCODE -ne 0) { & $ecrire "== ARRÊT : la base de données ne répond pas (Docker démarré ?)"; & $ecrire "== LOT $lot — FIN"; exit 1 }
$seul = ($briefs | % { "--seulement $_" }) -join " "
$corpus = if ($source -eq "corpus") { "--corpus usine/corpus" } else { "" }
cmd /c "python -m usine.repetition --chaine-reelle --modele boite --client-simule $corpus $seul >> ""$log"" 2>&1"
& $ecrire "== LOT $lot — FIN $(Get-Date -Format s)"
