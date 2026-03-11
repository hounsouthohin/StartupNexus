param(
  [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,
  [switch]$ExportQdrant
)

$manifestPath = Join-Path $PSScriptRoot "pack_manifest.txt"
if (-not (Test-Path $manifestPath)) {
  throw "Manifest introuvable: $manifestPath"
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outDir = Join-Path $PSScriptRoot ("out\" + $timestamp)
$filesDir = Join-Path $outDir "files"
New-Item -ItemType Directory -Path $filesDir -Force | Out-Null

$manifest = Get-Content $manifestPath | Where-Object { $_.Trim() -ne "" -and -not $_.Trim().StartsWith("#") }
$copied = 0
$missing = @()

foreach ($rel in $manifest) {
  $src = Join-Path $ProjectRoot $rel
  if (-not (Test-Path $src)) {
    $missing += $rel
    continue
  }
  $dst = Join-Path $filesDir $rel
  $dstParent = Split-Path $dst -Parent
  New-Item -ItemType Directory -Path $dstParent -Force | Out-Null
  Copy-Item -Path $src -Destination $dst -Force
  $copied++
}

Copy-Item -Path (Join-Path $PSScriptRoot "README.md") -Destination (Join-Path $outDir "README.md") -Force
Copy-Item -Path (Join-Path $PSScriptRoot "AUDIT_CHECKLIST.md") -Destination (Join-Path $outDir "AUDIT_CHECKLIST.md") -Force
Copy-Item -Path (Join-Path $PSScriptRoot "REQUEST_TEMPLATE.md") -Destination (Join-Path $outDir "REQUEST_TEMPLATE.md") -Force
Copy-Item -Path $manifestPath -Destination (Join-Path $outDir "pack_manifest.txt") -Force

$qdrantExportStatus = "skipped"
if ($ExportQdrant) {
  $qdrantOut = Join-Path $outDir "qdrant_standards_snapshot.json"
  $exportScript = Join-Path $PSScriptRoot "export_qdrant_snapshot.py"
  try {
    python $exportScript --output $qdrantOut | Out-Host
    if (Test-Path $qdrantOut) {
      $qdrantExportStatus = "ok"
    } else {
      $qdrantExportStatus = "failed-no-file"
    }
  } catch {
    $qdrantExportStatus = "failed-exception"
  }
}

$summary = @()
$summary += "External audit pack generated"
$summary += "Timestamp: $timestamp"
$summary += "ProjectRoot: $ProjectRoot"
$summary += "Copied files: $copied"
$summary += "Missing files: $($missing.Count)"
$summary += "Qdrant export: $qdrantExportStatus"
if ($missing.Count -gt 0) {
  $summary += ""
  $summary += "Missing entries:"
  $summary += $missing
}
$summaryPath = Join-Path $outDir "BUILD_SUMMARY.txt"
$summary | Set-Content -Path $summaryPath -Encoding UTF8

Write-Host "Pack generated:"
Write-Host "  $outDir"
Write-Host "Copied: $copied | Missing: $($missing.Count)"
