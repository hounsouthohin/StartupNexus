# Prépare l'E6 : code généré + base neuve (une par version du schéma, jamais de remise à zéro).
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$schema = "zenstack/schema.zmodel"
$hash = (Get-FileHash $schema -Algorithm SHA256).Hash.Substring(0, 8).ToLower()
$db = "poc_ecrans_$hash"
$exists = docker exec temporal-postgresql psql -U temporal -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$db'"
$env:DATABASE_URL = "postgresql://temporal:temporal@localhost:5432/$db"
npx zen generate --schema $schema -o zenstack --silent
if (-not $exists) {
    docker exec temporal-postgresql psql -U temporal -d postgres -c "CREATE DATABASE $db" | Out-Null
    npx zen db push --schema $schema 2>&1 | Select-String -Pattern 'sync|rror' | ForEach-Object { $_.Line }
}
Set-Content -Path ".env.local" -Value "DATABASE_URL=$env:DATABASE_URL" -Encoding ascii
"base : $db"
