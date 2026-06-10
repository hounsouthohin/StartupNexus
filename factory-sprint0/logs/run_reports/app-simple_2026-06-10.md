# FactoryRunReport — app-simple — 2026-06-10
══════════════════════════════════════════════════
BUILD        : ❌ SUCCESS
REVIEW       : COHERENT | sec=100 | coh=100 | 0 finding(s)
CORRECTIONS  : SKIPPED (NOT_RUN)
TESTS        : ✗ 2 test(s) — PASS tests/schemas.test.ts | PASS tests/middleware.test.ts |
SEMGREP      : ⚠ 1 finding(s)

PATTERNS DÉTECTÉS :
  ⚠ Violation sémantique récurrente: PRISMA_VALIDATE_FAILED: schema invalide selon prisma validat
  → Suggestion standard — DÉCISION REQUISE
  🔴 Erreur de build récurrente (2×): failed (exit 1)
> event-board@0.1.0 build
> next build

⚠ no
  → Suggestion standard — DÉCISION REQUISE
  🔴 Erreur de build récurrente (2×): pre_run_failed (npx prisma generate): loaded prisma config f
  → Suggestion standard — DÉCISION REQUISE

RUN_ID       : 48295c7f-3041-4e09-8b59-cd47b2da6994
DURÉE        : 2min 37s