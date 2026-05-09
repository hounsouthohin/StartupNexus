╔══════════════════════════════════════════════════════════════════════════════╗
║          SOFTWARE AGENT FACTORY — PIPELINE ARCHITECT + DEV (état réel)     ║
╚══════════════════════════════════════════════════════════════════════════════╝

INPUT
─────
  brief.json
  {
    project_name, description, architecture,
    models[]  ← strings Prisma DSL  ex: "Expense { amount Float, ... }"
    pages[]   ← [{path, auth}]
    routes[]  ← [{method, path}]
    user_flows[], pages_detail{}
  }
         │
         ▼
╔══════════════════════════════════════════════════════════╗
║               ARCHITECT ACTIVITY                         ║
║  (LangGraph — 2 nœuds actifs au 20 Avril 2026)          ║
║                                                          ║
║  START                                                   ║
║    │                                                     ║
║    ▼                                                     ║
║  ┌─────────────────────────────────────────────────┐    ║
║  │  retrieval_node                                 │    ║
║  │                                                 │    ║
║  │  • Query = brief.description                    │    ║
║  │  • Qdrant similarity_search (k=10)              │    ║
║  │    filtre : status=active + stack               │    ║
║  │    seuil score : ARCHITECT_RAG_SCORE_THRESHOLD  │    ║
║  │  • Produit rag_context (standards sélectionnés) │    ║
║  └──────────────────┬──────────────────────────────┘    ║
║                     │                                    ║
║                     ▼                                    ║
║  ┌─────────────────────────────────────────────────┐    ║
║  │  planner_node  (déterministe — 0 LLM si brief   │    ║
║  │                complet avec models+pages+routes)│    ║
║  │                                                 │    ║
║  │  1. Parse les models[] (Prisma DSL → PrismaModel│    ║
║  │  2. _inject_prisma_relations() :                │    ║
║  │       détecte xxxId → injecte @relation des     │    ║
║  │       deux côtés (child+parent) automatiquement │    ║
║  │  3. Construit pages[], routes[]                 │    ║
║  │  4. Auto-ajoute page "/" si absente             │    ║
║  │  5. user_flows depuis brief ou fallback         │    ║
║  │  6. architecture hint → injecté en tête flows   │    ║
║  │  7. ProjectSpec.with_fingerprint()              │    ║
║  │                                                 │    ║
║  │  ⚠️  Si models/pages/routes absents du brief    │    ║
║  │       → ApplicationError non-retryable (arrêt)  │    ║
║  │                                                 │    ║
║  │  ⚠️  spec_writer_node RETIRÉ du graph (28 Mars) │    ║
║  │       Le LLM spec_writer ne tourne PLUS         │    ║
║  │       planner produit directement ProjectSpec   │    ║
║  └──────────────────┬──────────────────────────────┘    ║
║                     │                                    ║
║                    END                                   ║
║                                                          ║
║  OUTPUT : ProjectSpec (sérialisé en dict)                ║
║  {                                                       ║
║    models[], pages[], routes[], user_flows[],            ║
║    pages_detail{}, description, stack_id,                ║
║    spec_fingerprint (hash)                               ║
║  }                                                       ║
╚══════════════════════════════════════════════════════════╝
         │
         │  ProjectSpec dict transmis au Dev
         ▼
╔══════════════════════════════════════════════════════════════════════════════╗
║                   DEV ACTIVITY (dev_graph.py)                               ║
║                                                                             ║
║  ┌──────────────────────────────────────────────────────────────────────┐  ║
║  │  PHASE PRÉ-LLM  (Python pur — infrastructure, avant démarrage LLM)  │  ║
║  │                                                                      │  ║
║  │  1. Nettoyage workdir isolé : shutil.rmtree + makedirs               │  ║
║  │     + suppression des résidus stale à la racine FACTORY_WORKDIR      │  ║
║  │  2. write_template_files() — stack templates écrits sur disque :     │  ║
║  │       package.json, middleware.ts, app/layout.tsx, tsconfig.json,    │  ║
║  │       jest.config.js, lib/prisma.ts, next.config.js,                 │  ║
║  │       .env.local, .eslintrc.stack.json                               │  ║
║  │  3. ProjectSpec → prisma/schema.prisma matérialisé sur disque        │  ║
║  │     (modèles exacts, relations injectées, User auto)                  │  ║
║  │  4. generate_loading_files() — app/**/loading.tsx (skeleton Tailwind)│  ║
║  │     uniquement les pages auth_required=True                           │  ║
║  │  5. npm install  (subprocess, timeout 300s, hors LLM)                │  ║
║  │  6. npx prisma generate  (subprocess, timeout 120s, hors LLM)        │  ║
║  │     → @prisma/client typé disponible dès le 1er fichier LLM          │  ║
║  │                                                                      │  ║
║  │  Fichiers protégés (LLM bloqué en écriture) :                        │  ║
║  │    lib/prisma.ts · prisma.config.ts                                  │  ║
║  │    prisma/schema.prisma · .eslintrc.stack.json                       │  ║
║  └──────────────────────────────────────────────────────────────────────┘  ║
║                          │                                                  ║
║                          ▼                                                  ║
║  ┌──────────────────────────────────────────────────────────────────────┐  ║
║  │  SYSTEM PROMPT (dev_prompts.py — injecté en messages[0])            │  ║
║  │                                                                      │  ║
║  │  • rules_dev.md (26 règles stack)                                    │  ║
║  │  • Schéma Prisma exact (copié depuis ProjectSpec)                    │  ║
║  │  • Services DAL à créer : Expense→expenseService, Board→boardService │  ║
║  │  • Liste fichiers pré-générés (ne pas réécrire)                      │  ║
║  │  • Pages + routes à créer                                            │  ║
║  │  • Workflow ordonné :                                                │  ║
║  │      a) lib/types.ts  b) lib/services/  c) app/api/  d) app/pages   │  ║
║  └──────────────────────────────────────────────────────────────────────┘  ║
║                          │                                                  ║
║                         START                                               ║
║                          │                                                  ║
║  ╔═══════════════════════▼════════════════════════════════════════════╗     ║
║  ║  BOUCLE LANGGRAPH  (recursion_limit=80, MAX_BUILD_ATTEMPTS=3)     ║     ║
║  ║                                                                    ║     ║
║  ║    ┌──────────────────────────────────────┐                        ║     ║
║  ║    │  dev_node  (LLM gpt-4o-mini)        │                        ║     ║
║  ║    │                                      │                        ║     ║
║  ║    │  Injections contextuelles avant LLM :│                        ║     ║
║  ║    │  • _prune_messages() — élagage :    │                        ║     ║
║  ║    │    garde System + 1er Human +        │                        ║     ║
║  ║    │    3 derniers rounds + dernier Human │                        ║     ║
║  ║    │  • Si phase=correction → rappel      │                        ║     ║
║  ║    │    "ne réécris pas depuis zéro"      │                        ║     ║
║  ║    │  • A1 : si validated_files≥1 et      │                        ║     ║
║  ║    │    pas encore de build → "lance      │                        ║     ║
║  ║    │    prisma generate puis npm build"   │                        ║     ║
║  ║    │  • file_validation_errors → injecté  │                        ║     ║
║  ║    │    (tentative N/MAX_RETRIES)         │                        ║     ║
║  ║    │  • last_build_error → correction     │                        ║     ║
║  ║    │    ciblée (tsc_error_catalog)        │                        ║     ║
║  ║    │    + RAG bridge auto si rag_query    │                        ║     ║
║  ║    │    + escalade si même erreur ×3      │                        ║     ║
║  ║    │                                      │                        ║     ║
║  ║    │  Outils disponibles au LLM :         │                        ║     ║
║  ║    │   write_file, read_file,             │                        ║     ║
║  ║    │   list_directory, shell_exec,        │                        ║     ║
║  ║    │   file_exists, rag_search←Qdrant     │                        ║     ║
║  ║    └──────────────┬───────────────────────┘                        ║     ║
║  ║                   │ tool_calls ?                                    ║     ║
║  ║          ┌────────┴────────┐                                       ║     ║
║  ║          │ non             │ oui                                    ║     ║
║  ║         END       ┌────────▼────────────────┐                      ║     ║
║  ║                   │  prebuild_gate_node     │                      ║     ║
║  ║                   │                         │                      ║     ║
║  ║                   │  Appel = npm run build? │                      ║     ║
║  ║                   │  Non → pass-through     │                      ║     ║
║  ║                   │  Oui → prebuild_pipeline│                      ║     ║
║  ║                   │    tsc + eslint +        │                      ║     ║
║  ║                   │    ast_use_client        │                      ║     ║
║  ║                   │                         │                      ║     ║
║  ║                   │  blocking=True ?         │                      ║     ║
║  ║                   │  ToolMessage ACK +       │                      ║     ║
║  ║                   │  bundle correction →dev  │                      ║     ║
║  ║                   │  (max 6 blocages puis    │                      ║     ║
║  ║                   │   PREBUILD_BLOCK_LIMIT)  │                      ║     ║
║  ║                   │  blocking=False → tools  │                      ║     ║
║  ║                   └────────┬────────────────┘                      ║     ║
║  ║                            │ autorisé                               ║     ║
║  ║                   ┌────────▼──────────┐                            ║     ║
║  ║                   │  tools (ToolNode) │                            ║     ║
║  ║                   │  exécute les      │                            ║     ║
║  ║                   │  tool_calls LLM   │                            ║     ║
║  ║                   └────────┬──────────┘                            ║     ║
║  ║                            │ toujours                               ║     ║
║  ║                   ┌────────▼────────────────────────┐              ║     ║
║  ║                   │  file_validate_node (NOUVEAU)   │              ║     ║
║  ║                   │  Progressive Validation         │              ║     ║
║  ║                   │                                 │              ║     ║
║  ║                   │  1. Détecte .ts/.tsx écrits     │              ║     ║
║  ║                   │     ce tour (via ToolMessages)  │              ║     ║
║  ║                   │  2. npx tsc --noEmit            │              ║     ║
║  ║                   │  3. Filtre erreurs sur ces       │              ║     ║
║  ║                   │     fichiers uniquement          │              ║     ║
║  ║                   │  4. A2 : lit les lignes fautives │              ║     ║
║  ║                   │     (snippet 7 lignes injecté)  │              ║     ║
║  ║                   │  5. Catalogue → context_hint    │              ║     ║
║  ║                   │     par code d'erreur           │              ║     ║
║  ║                   │                                 │              ║     ║
║  ║                   │  erreurs ET retries≤2 → dev     │              ║     ║
║  ║                   │  clean OU retries>2  → next     │              ║     ║
║  ║                   └────────┬────────────────────────┘              ║     ║
║  ║                            │ clean                                  ║     ║
║  ║                   ┌────────▼───────────────────────┐               ║     ║
║  ║                   │  extract_build_error_node      │               ║     ║
║  ║                   │                                │               ║     ║
║  ║                   │  Scanne les ToolMessages :      │               ║     ║
║  ║                   │  • "OK\n" + marqueurs next.js  │               ║     ║
║  ║                   │    → success=True, EXIT=0      │               ║     ║
║  ║                   │  • "Type error / FAILED"       │               ║     ║
║  ║                   │    → last_build_error, EXIT=N  │               ║     ║
║  ║                   │  • build_attempts++            │               ║     ║
║  ║                   │  • phase → "correction"        │               ║     ║
║  ║                   └────────┬───────────────────────┘               ║     ║
║  ║                            │                                        ║     ║
║  ║            ┌───────────────┼───────────────┐                       ║     ║
║  ║            │ success=True  │ error+         │ attempts≥3            ║     ║
║  ║           END         dev_node            END                      ║     ║
║  ╚════════════════════════════════════════════════════════════════════╝     ║
║                          │                                                  ║
║           OUTPUT : workdir complet (~30 fichiers)                           ║
║           success=True/False, build_exit_code, build_attempts              ║
╚══════════════════════════════════════════════════════════════════════════════╝

SOURCES DE CONNAISSANCE DU LLM DEV
────────────────────────────────────
  rules_dev.md (26 règles)     → system prompt, présent à chaque appel
  Qdrant factory_standards     → rag_search() (à la demande) + RAG bridge auto
    ZONE_1–14 : standards fondamentaux
    ZONE_19   : patterns SaaS senior
    ZONE_20   : DAL service pattern (à injecter)
  tsc_error_catalog.py         → auto-injecté à chaque erreur build + file_validate
    TS2307 → fichier manquant
    TS2305 → mauvais import service
    TS2322 → string|null Clerk non gardé
    TS2339 → champ absent du schema
    TS2345 → type mismatch

OPTION B — SÉPARATION INFRASTRUCTURE / CODE APPLICATIF
────────────────────────────────────────────────────────
  PRÉ-ÉCRIT (Python, avant LLM)      GÉNÉRÉ PAR LE LLM
  ─────────────────────────────      ─────────────────────────────
  package.json                       lib/types.ts
  middleware.ts                      lib/services/<model>.service.ts
  app/layout.tsx                     app/api/**/route.ts
  lib/prisma.ts                      app/**/page.tsx
  prisma/schema.prisma (depuis spec) app/page.tsx
  app/**/loading.tsx
  tsconfig.json, jest.*, next.config

CHANGEMENTS MAJEURS vs SESSION PRÉCÉDENTE
──────────────────────────────────────────
  Architect : spec_writer_node RETIRÉ du graph
              → planner seul, déterministe, 0 LLM si brief complet
              → spec_writer reste dans le code (tests) mais ne tourne plus

  Dev       : file_validate_node AJOUTÉ (Progressive Validation)
              → tsc après chaque batch d'écriture, correction immédiate
              → A1 : injection "lance le build" quand fichiers validés
              → A2 : snippet source injecté avec chaque erreur tsc
