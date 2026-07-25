<#
.SYNOPSIS
  PREVIEW LOCAL (Scène-B, Option A) — fait tourner une app générée, peuplée, en local.

.DESCRIPTION
  Tout tourne DANS le conteneur factory-worker (l'app et ses node_modules y sont déjà —
  ZÉRO extraction). Le script orchestre : base dédiée → schéma → données → serveur.
  Enchaîne les 4 gestes, puis lance `next dev` exposé sur http://localhost:<Port>.

  Le serveur reste au premier plan (c'est la « porte humaine » : tu regardes, tu cliques).
  Ctrl-C pour l'arrêter.

.PARAMETER Project
  Nom du projet généré (ex: notes-frais). Doit exister dans /app/generated-projects.

.PARAMETER SeedUserId
  TON id utilisateur Clerk (ex: user_2ab...). Les données semées t'appartiendront → visibles
  une fois connecté. Défaut 'user_demo' = données invisibles pour toi (utile juste pour tester
  que ça tourne).

.PARAMETER Port
  Port local (défaut 3100 — doit être exposé dans docker-compose.override.yml).

.EXAMPLE
  ./scripts/preview.ps1 -Project notes-frais -SeedUserId user_2abcXYZ

.NOTES
  PRÉREQUIS (une fois) :
   1. Renseigne tes clés Clerk de DEV dans  scripts/.preview.clerk.env  (gitignoré) :
        NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
        CLERK_SECRET_KEY=sk_test_...
   2. Port exposé : `docker compose up -d factory-worker` (une fois, après l'ajout du port 3100).
#>
param(
  [Parameter(Mandatory = $true)][string]$Project,
  [string]$SeedUserId = "user_demo",
  [int]$Port = 3100
)

$ErrorActionPreference = "Stop"
$FactoryDir = Split-Path -Parent $PSScriptRoot
$Compose = @("compose", "-f", (Join-Path $FactoryDir "docker-compose.yml"), "-f", (Join-Path $FactoryDir "docker-compose.override.yml"))
$AppPath = "/app/generated-projects/$Project"
$DbName = "preview_" + ($Project -replace '[^a-zA-Z0-9]', '')
$DbUrl = "postgresql://temporal:temporal@temporal-postgresql:5432/$DbName"

Write-Host "== PREVIEW : $Project  (base $DbName, port $Port) ==" -ForegroundColor Cyan

# ── Clés Clerk (lues depuis le fichier local de l'opérateur) ─────────────────
$ClerkFile = Join-Path $PSScriptRoot ".preview.clerk.env"
$EnvArgs = @()
if (Test-Path $ClerkFile) {
  foreach ($line in Get-Content $ClerkFile) {
    $t = $line.Trim()
    if ($t -and -not $t.StartsWith("#") -and $t.Contains("=")) {
      $EnvArgs += @("-e", $t)
    }
  }
} else {
  Write-Host "⚠ scripts/.preview.clerk.env absent — l'auth Clerk ne marchera pas." -ForegroundColor Red
  Write-Host "  Crée-le avec NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=... et CLERK_SECRET_KEY=..." -ForegroundColor Red
}

# ── 1. Base de données dédiée (jetable) ──────────────────────────────────────
Write-Host "[1/4] Base $DbName ..." -ForegroundColor Yellow
& docker @Compose exec -T postgresql dropdb -U temporal --if-exists $DbName | Out-Null
& docker @Compose exec -T postgresql createdb -U temporal $DbName

# ── 2. Schéma (prisma db push) ───────────────────────────────────────────────
Write-Host "[2/4] Schéma (prisma db push)..." -ForegroundColor Yellow
& docker @Compose exec -T factory-worker sh -c "cd $AppPath && npx prisma db push --url $DbUrl --accept-data-loss"

# ── 3. Données de démonstration (seed) ───────────────────────────────────────
Write-Host "[3/4] Seed (SEED_USER_ID=$SeedUserId)..." -ForegroundColor Yellow
& docker @Compose exec -T -e "DATABASE_URL=$DbUrl" -e "SEED_USER_ID=$SeedUserId" `
  factory-worker sh -c "cd $AppPath && node prisma/seed.mjs"

# ── 4. Serveur (porte humaine) ───────────────────────────────────────────────
Write-Host "[4/4] Lancement → http://localhost:$Port" -ForegroundColor Green
Write-Host "  Connecte-toi avec le compte Clerk dont l'id est $SeedUserId pour voir les données." -ForegroundColor Green
Write-Host "  (Ctrl-C pour arrêter le serveur)" -ForegroundColor DarkGray
& docker @Compose exec `
  -e "DATABASE_URL=$DbUrl" -e "DIRECT_DATABASE_URL=$DbUrl" `
  -e "NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in" -e "NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up" `
  -e "NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/dashboard" -e "NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/dashboard" `
  @EnvArgs `
  factory-worker sh -c "cd $AppPath && npx next dev -H 0.0.0.0 -p $Port"
