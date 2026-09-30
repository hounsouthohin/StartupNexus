# FactoryRunReport — abo-tracker — 2026-08-24
══════════════════════════════════════════════════

🔗 APP LIVE : http://localhost:3100

CE QUE L'APP FAIT :
  L'application permet à un utilisateur de suivre ses abonnements et dépenses récurrentes de manière privée après connexion. Chaque abonnement a un nom, un prix mensuel, une date de prochain prélèvement, et appartient à une catégorie personnalisée. Les abonnements peuvent être actifs, en pause ou résiliés. Le tableau de bord affiche le total mensuel des abonnements actifs, le nombre d'abonnements par statut, et ceux dont le prélèvement est prévu dans les 7 prochains jours. L'utilisateur peut gérer ses catégories et consulter les détails de chaque abonnement.

⚠ NON COUVERT PAR LA FACTORY (1) :
  ✗ Le brief demande que chaque catégorie ait une description optionnelle ; la spécification ne mentionne pas la gestion de cette description dans les pages ou les actions.
══════════════════════════════════════════════════
BUILD        : ✅ SUCCESS
REVIEW       : COHERENT | sec=100 | coh=100 | 0 finding(s)
CORRECTIONS  : SKIPPED (aucun finding actionnable)
TESTS        : ✗ 2 test(s) — PASS tests/middleware.test.ts | FAIL tests/services.test.ts 
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

RUN_ID       : 730ee25c-69cc-42e4-9fb1-e5c168d2666f
DURÉE        : 2min 55s