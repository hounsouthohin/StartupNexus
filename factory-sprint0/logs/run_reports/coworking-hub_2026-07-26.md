# FactoryRunReport — coworking-hub — 2026-07-26
══════════════════════════════════════════════════

CE QUE L'APP FAIT :
  La plateforme permet aux visiteurs de parcourir le catalogue des espaces de coworking sans se connecter. Chaque espace a un nom, une description, un type, une capacité, un tarif horaire et une adresse. Les membres peuvent gérer leur profil et réserver des espaces après connexion. Les réservations passent par plusieurs états : demandée, confirmée, refusée, terminée ou annulée. Les factures sont générées pour les réservations confirmées et peuvent être payées ou en retard. Un tableau de bord affiche le chiffre d'affaires du mois, le nombre de réservations en attente et le total des factures impayées. Seuls les administrateurs peuvent confirmer ou refuser les réservations et marquer les factures comme payées.

⚠ NON COUVERT PAR LA FACTORY (1) :
  ✗ Le brief mentionne que seul un administrateur doit pouvoir confirmer ou refuser les réservations et marquer les factures comme payées. La spécification ne décrit pas de rôle d'administrateur distinct ni de permissions spécifiques pour ces actions.
══════════════════════════════════════════════════
BUILD        : ❌ BUILD_FAILED
REVIEW       : SKIPPED (SKIPPED_BUILD_FAILED)
CORRECTIONS  : SKIPPED (NOT_RUN)
TESTS        : Non exécuté
SEMGREP      : Non exécuté

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

RUN_ID       : 4a9dd827-0927-4c4e-b49b-a439e488ca58
DURÉE        : 2min 10s