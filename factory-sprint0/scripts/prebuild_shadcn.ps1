# prebuild_shadcn.ps1
# Génère les composants shadcn/ui officiels dans factory-sprint0/assets/shadcn/
#
# Usage (depuis la racine du repo StartupNexus) :
#   cd factory-sprint0
#   powershell -ExecutionPolicy Bypass -File scripts\prebuild_shadcn.ps1
#
# Prérequis : Node.js 22+, npm 10+
# Durée estimée : ~3-5 minutes (téléchargement npm one-time)

$ErrorActionPreference = "Stop"
$SCRIPT_DIR  = Split-Path -Parent $MyInvocation.MyCommand.Path
$FACTORY_DIR = Split-Path -Parent $SCRIPT_DIR
$ASSETS_DIR  = Join-Path $FACTORY_DIR "assets\shadcn"
$TEMP_DIR    = Join-Path $env:TEMP "shadcn_prebuild"

Write-Host ""
Write-Host "=== prebuild_shadcn.ps1 ===" -ForegroundColor Cyan
Write-Host "Factory : $FACTORY_DIR"
Write-Host "Assets  : $ASSETS_DIR"
Write-Host "Temp    : $TEMP_DIR"
Write-Host ""

# Nettoyage préalable du temp si relancé
if (Test-Path $TEMP_DIR) { Remove-Item $TEMP_DIR -Recurse -Force }

try {
    # ── 1. Créer le projet Next.js temporaire ─────────────────────────────────
    Write-Host "[1/4] Création du projet Next.js temporaire..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $TEMP_DIR -Force | Out-Null
    Set-Location $TEMP_DIR

    & npx create-next-app@latest app `
        --typescript `
        --tailwind `
        --app `
        --no-git `
        --yes
    if ($LASTEXITCODE -ne 0) { throw "create-next-app a échoué (code $LASTEXITCODE)" }

    Set-Location (Join-Path $TEMP_DIR "app")

    # ── 2. Initialiser shadcn ─────────────────────────────────────────────────
    Write-Host ""
    Write-Host "[2/4] Initialisation shadcn (defaults)..." -ForegroundColor Yellow
    & npx shadcn@latest init --defaults --yes
    if ($LASTEXITCODE -ne 0) { throw "shadcn init a échoué (code $LASTEXITCODE)" }

    # ── 3. Ajouter les composants nécessaires aux apps Type A/D ───────────────
    Write-Host ""
    Write-Host "[3/4] Ajout des composants : button, input, textarea, select, card, table, badge, label..." -ForegroundColor Yellow
    & npx shadcn@latest add button input textarea select card table badge label --yes
    if ($LASTEXITCODE -ne 0) { throw "shadcn add a échoué (code $LASTEXITCODE)" }

    # ── 4. Copier vers assets/shadcn/ ────────────────────────────────────────
    Write-Host ""
    Write-Host "[4/4] Copie vers assets/shadcn/..." -ForegroundColor Yellow

    # Nettoyer et recréer le répertoire assets
    if (Test-Path $ASSETS_DIR) { Remove-Item $ASSETS_DIR -Recurse -Force }
    New-Item -ItemType Directory -Path "$ASSETS_DIR\components\ui" -Force | Out-Null
    New-Item -ItemType Directory -Path "$ASSETS_DIR\lib"            -Force | Out-Null

    # Copier components/ui/
    $ui_src = Join-Path $TEMP_DIR "app\components\ui"
    if (Test-Path $ui_src) {
        Get-ChildItem $ui_src -File | ForEach-Object {
            Copy-Item $_.FullName (Join-Path "$ASSETS_DIR\components\ui" $_.Name)
            Write-Host "  ✓ components/ui/$($_.Name)"
        }
    } else {
        Write-Warning "  ⚠ Répertoire components/ui introuvable — vérifier la structure shadcn"
    }

    # Copier lib/utils.ts
    $utils_src = Join-Path $TEMP_DIR "app\lib\utils.ts"
    if (Test-Path $utils_src) {
        Copy-Item $utils_src "$ASSETS_DIR\lib\utils.ts"
        Write-Host "  ✓ lib/utils.ts"
    } else {
        Write-Warning "  ⚠ lib/utils.ts introuvable"
    }

    $count = (Get-ChildItem $ASSETS_DIR -Recurse -File).Count
    Write-Host ""
    Write-Host "=== Terminé : $count fichiers dans assets/shadcn/ ===" -ForegroundColor Green
    Write-Host ""
    Write-Host "Prochaines étapes :" -ForegroundColor Cyan
    Write-Host "  1. Vérifier les fichiers dans factory-sprint0/assets/shadcn/"
    Write-Host "  2. git add assets/shadcn/ && git commit -m 'feat: add shadcn/ui assets'"
    Write-Host "  3. Rebuild Docker pour inclure les assets dans l'image"
    Write-Host ""
    Write-Host "Mise à jour future shadcn : relancer ce script." -ForegroundColor Gray

} catch {
    Write-Host ""
    Write-Host "ERREUR : $_" -ForegroundColor Red
    exit 1
} finally {
    Set-Location $FACTORY_DIR
    if (Test-Path $TEMP_DIR) {
        Remove-Item $TEMP_DIR -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "Répertoire temporaire nettoyé."
    }
}
