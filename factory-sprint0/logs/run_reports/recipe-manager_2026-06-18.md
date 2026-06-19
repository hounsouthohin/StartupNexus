# FactoryRunReport — recipe-manager — 2026-06-18
══════════════════════════════════════════════════
BUILD        : ❌ SUCCESS
REVIEW       : COHERENT | sec=100 | coh=100 | 0 finding(s)
CORRECTIONS  : SKIPPED (NOT_RUN)
TESTS        : ✗ 2 test(s) — FAIL tests/schemas.test.ts | FAIL tests/post.service.test.ts
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

RUN_ID       : c1f59da9-1966-45e3-b4db-484fcc0f769f
DURÉE        : 4min 49s