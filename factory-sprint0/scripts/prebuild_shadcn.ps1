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

    # ── 5. Extraire les versions des dépendances shadcn depuis package.json ─────
    Write-Host ""
    Write-Host "[5/5] Extraction des versions de dépendances shadcn..." -ForegroundColor Yellow
    $pkg_json = Join-Path $TEMP_DIR "app\package.json"
    if (Test-Path $pkg_json) {
        $pkg = Get-Content $pkg_json -Raw | ConvertFrom-Json
        $deps = @{}
        $all_deps = @{}
        if ($pkg.dependencies) {
            $pkg.dependencies.PSObject.Properties | ForEach-Object { $all_deps[$_.Name] = $_.Value }
        }
        if ($pkg.devDependencies) {
            $pkg.devDependencies.PSObject.Properties | ForEach-Object { $all_deps[$_.Name] = $_.Value }
        }
        # Extraire les deps pertinentes pour la factory
        $keys_to_track = @("@base-ui/react", "radix-ui", "@radix-ui/react-slot", "class-variance-authority", "clsx", "tailwind-merge", "lucide-react", "tailwindcss-animate")
        $keys_to_track | ForEach-Object {
            if ($all_deps.ContainsKey($_)) {
                $deps[$_] = $all_deps[$_]
                Write-Host "  $_ : $($all_deps[$_])"
            }
        }
        # Sauvegarder dans assets/shadcn/deps.json pour référence
        $deps | ConvertTo-Json | Out-File -FilePath "$ASSETS_DIR\deps.json" -Encoding utf8
        Write-Host "  → Sauvegardé dans assets/shadcn/deps.json"

        # Avertir si @base-ui/react présent et factory template diverge
        if ($deps.ContainsKey("@base-ui/react")) {
            Write-Host ""
            Write-Host "⚠  shadcn utilise @base-ui/react $($deps['@base-ui/react'])" -ForegroundColor Yellow
            Write-Host "   Vérifier que factory-sprint0/config/stacks/nextjs-clerk-prisma/templates/package.json" -ForegroundColor Yellow
            Write-Host "   inclut : `"@base-ui/react`": `"$($deps['@base-ui/react'])`"" -ForegroundColor Yellow
        }
    }

    $count = (Get-ChildItem $ASSETS_DIR -Recurse -File).Count
    Write-Host ""
    Write-Host "=== Terminé : $count fichiers dans assets/shadcn/ ===" -ForegroundColor Green
    Write-Host ""
    Write-Host "Prochaines étapes :" -ForegroundColor Cyan
    Write-Host "  1. Vérifier les fichiers dans factory-sprint0/assets/shadcn/"
    Write-Host "  2. Vérifier que package.json template contient toutes les deps de assets/shadcn/deps.json"
    Write-Host "  3. git add assets/shadcn/ && git commit -m 'feat: add shadcn/ui assets'"
    Write-Host "  4. Rebuild Docker pour inclure les assets dans l'image"
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
