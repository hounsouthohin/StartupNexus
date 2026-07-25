# FactoryRunReport — notes-frais — 2026-07-25
══════════════════════════════════════════════════

CE QUE L'APP FAIT :
  Un employé peut créer une note de frais en indiquant un intitulé, un montant, une date, une catégorie et une description. Il peut garder la note en brouillon ou la soumettre pour examen. Une fois soumise, la note peut être approuvée ou refusée avec un motif. Les notes approuvées sont remboursées après le virement. L'employé peut voir la liste de ses notes avec leur état et le total en attente de remboursement.

⚠ NON COUVERT PAR LA FACTORY (2) :
  ✗ Le brief mentionne « mon équipe » et « elle est examinée », ce qui implique un rôle de responsable pour approuver ou refuser les notes. La spécification ne décrit qu'un seul utilisateur sans distinction de rôles.
  ✗ Le brief indique que l'utilisateur doit voir le total en attente de remboursement, mais la spécification ne mentionne pas cette fonctionnalité.
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

RUN_ID       : b6c2375e-2dbf-4f8a-8aad-ba68acc7ae38
DURÉE        : 1min 57s