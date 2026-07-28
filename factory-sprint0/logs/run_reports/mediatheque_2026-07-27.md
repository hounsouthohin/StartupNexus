# FactoryRunReport — mediatheque — 2026-07-27
══════════════════════════════════════════════════

🔗 APP LIVE : http://localhost:3100

CE QUE L'APP FAIT :
  L'application permet aux visiteurs de parcourir le catalogue public des ouvrages sans se connecter. Chaque ouvrage affiche son titre, auteur, résumé, genre et année de publication. Les adhérents peuvent se connecter pour gérer leur profil et demander à emprunter des ouvrages. Ils peuvent suivre l'état de leurs emprunts, qui passent par différents états : demandé, accepté, refusé, et rendu. Les bibliothécaires ont la capacité de voir tous les emprunts et de changer leur état, en acceptant, refusant ou marquant un emprunt comme rendu.

✓ Aucune demande du brief laissée de côté.
══════════════════════════════════════════════════
BUILD        : ✅ SUCCESS
REVIEW       : COHERENT | sec=100 | coh=100 | 0 finding(s)
CORRECTIONS  : SKIPPED (aucun finding actionnable)
TESTS        : ✗ 2 test(s) — FAIL tests/services.test.ts | FAIL tests/schemas.test.ts | T
SEMGREP      : ⚠ 1 finding(s)

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

RUN_ID       : 1686fac8-7a88-4a18-b61f-815a29d3e1f7
DURÉE        : 3min 55s