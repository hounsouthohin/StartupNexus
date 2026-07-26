# FactoryRunReport — it-requests — 2026-07-26
══════════════════════════════════════════════════

🔗 APP LIVE : http://localhost:3100

CE QUE L'APP FAIT :
  L'application permet aux employés de soumettre des demandes informatiques avec un titre, une description et une priorité. Chaque employé peut voir et suivre uniquement ses propres demandes. Les administrateurs ont accès à toutes les demandes de l'entreprise et peuvent changer leur statut de 'nouvelle' à 'en cours', puis à 'résolue'. Seuls les administrateurs peuvent modifier le statut des demandes. L'interface est conçue pour être sobre et professionnelle.

⚠ NON COUVERT PAR LA FACTORY (2) :
  ✗ Le brief mentionne que les employés doivent se connecter pour soumettre une demande, mais la spécification ne précise pas de mécanisme de connexion ou d'authentification.
  ✗ Le brief indique que les employés peuvent suivre l'avancement de leurs demandes, mais la spécification ne décrit pas comment les employés sont informés des changements de statut.
══════════════════════════════════════════════════
BUILD        : ✅ SUCCESS
REVIEW       : COHERENT | sec=100 | coh=100 | 0 finding(s)
CORRECTIONS  : SKIPPED (aucun finding actionnable)
TESTS        : ✗ 2 test(s) — PASS tests/schemas.test.ts | FAIL tests/request.service.test
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
  🔴 Erreur de build récurrente (2×): generation_error: <FILE>x importe '<ID>' mais <FILE>x absent
  → Suggestion standard — DÉCISION REQUISE

RUN_ID       : 6a020c3c-58a6-4779-8260-fdda3a059e7d
DURÉE        : 1min 15s