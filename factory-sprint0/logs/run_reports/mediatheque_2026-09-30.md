# FactoryRunReport — mediatheque — 2026-09-30
══════════════════════════════════════════════════

🔗 APP LIVE : http://localhost:3100

CE QUE L'APP FAIT :
  L'application permet aux visiteurs de parcourir le catalogue des ouvrages de la médiathèque sans avoir besoin de se connecter. Chaque ouvrage présente des informations détaillées telles que le titre, l'auteur, le résumé, le genre et l'année de publication. Les adhérents peuvent se connecter pour gérer leur profil et demander à emprunter des ouvrages. Ils peuvent suivre l'état de leurs emprunts, qui passent par différents statuts : demandé, accepté, refusé, et rendu. Les bibliothécaires ont la possibilité de voir tous les emprunts et de gérer leur statut, en acceptant, refusant ou marquant les emprunts comme rendus.

✓ Aucune demande du brief laissée de côté.
══════════════════════════════════════════════════
BUILD        : ✅ SUCCESS
REVIEW       : COHERENT | sec=100 | 0 finding(s)
CORRECTIONS  : SKIPPED (aucun finding actionnable)
TESTS        : Aucun — tests Jest retirés (30 sept 2026), oracles prévus en phase 5
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

RUN_ID       : 8b72ac10-f3d9-4684-a5e4-02eed8707a02
DURÉE        : 3min 54s