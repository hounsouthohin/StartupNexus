# FactoryRunReport — notes-frais — 2026-07-24
══════════════════════════════════════════════════

CE QUE L'APP FAIT :
  L'application permet à un employé de créer une note de frais avec un intitulé, un montant, une date, une catégorie et une description. L'employé peut garder la note en brouillon ou la soumettre pour examen. Une fois soumise, la note peut être approuvée ou refusée avec un motif. Les notes approuvées sont remboursées après le virement. L'employé peut voir la liste de ses notes avec leur état et le total en attente de remboursement.

⚠ NON COUVERT PAR LA FACTORY (2) :
  ✗ Le brief mentionne que « Une note refusée est définitive », mais la spécification ne précise pas que l'état 'refused' empêche toute modification ou action ultérieure.
  ✗ Le brief indique « Je veux voir le total en attente de remboursement », mais la spécification ne mentionne pas cette fonctionnalité.
══════════════════════════════════════════════════
BUILD        : ✅ SUCCESS
REVIEW       : COHERENT | sec=100 | coh=100 | 0 finding(s)
CORRECTIONS  : SKIPPED (aucun finding actionnable)
TESTS        : ✗ 2 test(s) — PASS tests/schemas.test.ts | PASS tests/middleware.test.ts |
SEMGREP      : ⚠ 1 finding(s)

PATTERNS DÉTECTÉS :
  ⚠ Violation sémantique récurrente: PRISMA_VALIDATE_FAILED: schema invalide selon prisma validat
  → Suggestion standard — DÉCISION REQUISE
  🔴 Erreur de build récurrente (10×): failed (exit 1)
> writer-pad@0.1.0 build
> next build

⚠ no 
  → Suggestion standard — DÉCISION REQUISE
  🔴 Erreur de build récurrente (2×): failed (exit 1)
> event-board@0.1.0 build
> next build

⚠ no
  → Suggestion standard — DÉCISION REQUISE
  🔴 Erreur de build récurrente (2×): pre_run_failed (npx prisma generate): loaded prisma config f
  → Suggestion standard — DÉCISION REQUISE
  🔴 Erreur de build récurrente (2×): failed (exit 1)
> app-simple@0.1.0 build
> next build

⚠ no 
  → Suggestion standard — DÉCISION REQUISE
  🔴 Erreur de build récurrente (2×): generation_error: <FILE>x importe '<ID>' mais <FILE>x absent
  → Suggestion standard — DÉCISION REQUISE

RUN_ID       : f27e1f16-ff5d-4b9d-8d1e-d1f58b5f9d79
DURÉE        : 1min 48s