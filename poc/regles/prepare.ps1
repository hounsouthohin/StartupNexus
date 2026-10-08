# Prépare un cas : code généré + base neuve + tables créées.
# Chaque version du schéma a SA base (nom = cas + empreinte du schéma) : on ne remet jamais une base
# à zéro (aucune commande destructrice ; garde-fou de Prisma respecté).
# Usage : .\prepare.ps1 notes-frais
param([Parameter(Mandatory)][string]$case)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$schema = "cases/$case/schema.zmodel"
$hash = (Get-FileHash $schema -Algorithm SHA256).Hash.Substring(0, 8).ToLower()
$db = 'poc_regles_' + ($case -replace '-', '_') + '_' + $hash
$exists = docker exec temporal-postgresql psql -U temporal -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$db'"
$env:DATABASE_URL = "postgresql://temporal:temporal@localhost:5432/$db"
npx zen generate --schema $schema -o "cases/$case/gen" --silent
if (-not $exists) {
    docker exec temporal-postgresql psql -U temporal -d postgres -c "CREATE DATABASE $db" | Out-Null
    npx zen db push --schema $schema 2>&1 | Select-String -Pattern 'sync|rror' | ForEach-Object { $_.Line }
}
Set-Content -Path "cases/$case/gen/database-url.txt" -Value $env:DATABASE_URL -Encoding ascii -NoNewline
"base : $db"
