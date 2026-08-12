# FactoryRunReport — mediatheque — 2026-08-01
══════════════════════════════════════════════════

🔗 APP LIVE : http://localhost:3100

CE QUE L'APP FAIT :
  L'application permet aux visiteurs de parcourir le catalogue public des ouvrages sans se connecter. Chaque ouvrage affiche son titre, auteur, résumé, genre et année de publication. Les adhérents peuvent se connecter pour gérer leur profil et demander à emprunter des ouvrages. Les emprunts passent par plusieurs états : demandé, accepté, refusé, et rendu. Les adhérents ne voient que leurs propres emprunts, tandis que le bibliothécaire peut voir et gérer tous les emprunts, y compris accepter, refuser ou marquer un emprunt comme rendu.

✓ Aucune demande du brief laissée de côté.
══════════════════════════════════════════════════
BUILD        : ✅ SUCCESS
REVIEW       : COHERENT | sec=100 | coh=100 | 0 finding(s)
CORRECTIONS  : SKIPPED (aucun finding actionnable)
TESTS        : ✗ 2 test(s) — FAIL tests/schemas.test.ts | FAIL tests/services.test.ts | T
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

RUN_ID       : 7d109068-4b36-40a8-ba1b-eec61eeca066
DURÉE        : 3min 11s