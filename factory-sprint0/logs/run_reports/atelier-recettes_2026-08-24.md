# FactoryRunReport — atelier-recettes — 2026-08-24
══════════════════════════════════════════════════

🔗 APP LIVE : http://localhost:3100

CE QUE L'APP FAIT :
  Les visiteurs peuvent consulter les recettes publiées sans avoir besoin de créer un compte. Chaque recette a une adresse unique dérivée de son titre. Les recettes incluent un titre, des instructions, un temps de préparation, une difficulté et des tags. Les utilisateurs connectés peuvent gérer leurs recettes et tags depuis un tableau de bord privé. Ils peuvent publier des recettes ou les garder en brouillon, et rechercher des recettes par titre. La page d'accueil affiche les dernières recettes publiées.

⚠ NON COUVERT PAR LA FACTORY (1) :
  ✗ Le brief demande une recherche de recette par titre ; aucune page ni action de la spec ne mentionne cette fonctionnalité.
══════════════════════════════════════════════════
BUILD        : ✅ SUCCESS
REVIEW       : COHERENT | sec=100 | coh=100 | 0 finding(s)
CORRECTIONS  : SKIPPED (aucun finding actionnable)
TESTS        : ✗ 2 test(s) — PASS tests/schemas.test.ts | FAIL tests/services.test.ts | T
SEMGREP      : ⚠ 2 finding(s)

PATTERNS DÉTECTÉS :
  ⚠ Violation sémantique récurrente: PRISMA_VALIDATE_FAILED: schema invalide selon prisma validat
  → Suggestion standard — DÉCISION REQUISE
  🔴 Erreur de build récurrente (10×): failed (exit 1)
> writer-pad@0.1.0 build
> next build

⚠ no 
  → Suggestion standard — DÉCISION REQUISE
  🔴 Erreur de build récurrente (3×): pre_run_failed (npx prisma generate): loaded prisma config f
  → Suggestion standard — DÉCISION REQUISE
  🔴 Erreur de build récurrente (3×): failed (exit 1)
> coworking-hub@0.1.0 build
> next build

⚠ 
  → Suggestion standard — DÉCISION REQUISE
  🔴 Erreur de build récurrente (2×): failed (exit 1)
> event-board@0.1.0 build
> next build

⚠ no
  → Suggestion standard — DÉCISION REQUISE
  🔴 Erreur de build récurrente (2×): failed (exit 1)
> app-simple@0.1.0 build
> next build

⚠ no 
  → Suggestion standard — DÉCISION REQUISE

RUN_ID       : e05afbcf-3de2-4044-9317-f9a84322616a
DURÉE        : 3min 1s