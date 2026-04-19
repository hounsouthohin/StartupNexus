╔══════════════════════════════════════════════════════════════════════════════════╗
║              TOILE DES FONCTIONS — SOFTWARE AGENT FACTORY                        ║
║              (Architect + Dev — état réel 17 Avril 2026)                         ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║  LÉGENDE : [D] Déterministe  [L] LLM  [R] Routage  [T] Template  [V] Validation  ║
╚══════════════════════════════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COUCHE 0 — ENTRÉE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  run_dev_agent()                                          [D] dev_graph.py:161
  ├── Isole le workdir (shutil.rmtree + makedirs)
  ├── Nettoie les résidus de l'ancien run
  ├── Appelle write_template_files()        ──────────────────────────────────┐
  ├── Appelle ProjectSpec(**spec)                                             │
  ├── Appelle generate_types_file()         ──────────────────────────────────┤
  ├── Lance npm install (pre-run)                                             │
  ├── Lance prisma generate (pre-run)                                         │
  ├── Appelle build_system_prompt()         ──────────────────────────────────┤
  └── Appelle create_dev_graph()            → assemble le graph LangGraph     │
                                                                               │
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                            │
COUCHE 1 — PRÉPARATION DÉTERMINISTE (avant LLM)                               │
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                            │
                                                                               │
  write_template_files()    [D] dev_file_ops.py  ◀─────────────────────────────┘
  │  Écrit 14 fichiers depuis templates stack JSON
  │  package.json, middleware.ts, app/layout.tsx, tsconfig.json...
  └── → template_written{} (dict path→content)

  generate_types_file()     [D] dev_types_generator.py
  │  Lit ProjectSpec → génère lib/types.ts avec noms EXACTS
  │  Task, CreateTaskInput, UpdateTaskInput, ApiResponse<T>...
  └── → TypesFileResult(model_names, input_types)

  build_system_prompt()     [D] dev_prompts.py
  │  Reçoit : ProjectSpec + pre_written_files + types_exported
  │  Construit : spec JSON + types exacts + checklist fichiers
  │              + règles stack (rules_dev.md) + protected files
  └── → string (system prompt complet)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COUCHE 2 — GRAPH LANGGRAPH (boucle LLM)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ┌─────────────────────────────────────────────────────────────────────────┐
  │                          dev_node()  [L]  :360                          │
  │                                                                         │
  │  RESPONSABILITÉ : préparer le contexte LLM + appeler gpt-4o-mini       │
  │                                                                         │
  │  Consomme ces fonctions helpers AVANT l'appel LLM :                    │
  │  ┌─────────────────────────────────────────────────────────────────┐   │
  │  │ _prune_messages()  [D]  :94                                      │   │
  │  │  Élagage sémantique : garde SystemMsg + premier HumanMsg        │   │
  │  │  + 3 derniers rounds + dernier HumanMsg                         │   │
  │  │  → évite que le contexte explose sur les runs longs             │   │
  │  └─────────────────────────────────────────────────────────────────┘   │
  │  ┌─────────────────────────────────────────────────────────────────┐   │
  │  │ Injection A1  [D]  :375                                          │   │
  │  │  Si fichiers validés ET pas encore de build                     │   │
  │  │  → "Lance prisma generate puis npm run build MAINTENANT"        │   │
  │  └─────────────────────────────────────────────────────────────────┘   │
  │  ┌─────────────────────────────────────────────────────────────────┐   │
  │  │ Injection file_validation_errors  [D]  :393                      │   │
  │  │  Si file_validate_node a trouvé des erreurs TS ce tour          │   │
  │  │  → injecte les erreurs enrichies + étapes de correction         │   │
  │  └─────────────────────────────────────────────────────────────────┘   │
  │  ┌─────────────────────────────────────────────────────────────────┐   │
  │  │ _build_targeted_correction()  [D]  :74          ← PROBLÈME      │   │
  │  │  Si last_build_error (erreur de npm run build)                  │   │
  │  │  → remet l'erreur brute en contexte + 5 étapes génériques       │   │
  │  │  LIMITE : pas d'analyse, pas d'orientation Qdrant               │   │
  │  │  ↳ _error_signature()  :66 → détecte si même erreur ×2         │   │
  │  └─────────────────────────────────────────────────────────────────┘   │
  │                                                                         │
  │  → appel llm_with_tools.invoke(messages) → AIMessage                   │
  └──────────────────────────────┬──────────────────────────────────────────┘
                                  │
                [route_from_dev()]  [R]  :662
                  LLM a des tool_calls ?
                  ┌────── OUI ──────┐────── NON ──────┐
                  ▼                                    ▼
  ┌───────────────────────────┐                      END
  │  prebuild_gate_node()  [V]:442                   (LLM a fini ou ne sait
  │                           │                       plus quoi faire)
  │  LLM appelle npm build ?  │
  │  → vérifie required_files │
  │  blocking=True → dev      │
  │  blocking=False → tools   │
  └─────────────┬─────────────┘
  [route_after_prebuild()]  [R]  :667
                  │
                  ▼
  ┌───────────────────────────────────────────────────┐
  │  tools_node()  [D]  (LangGraph ToolNode)          │
  │                                                   │
  │  Exécute les outils que le LLM a demandés :       │
  │  write_file()    → écrit sur disque               │
  │                    vérifie PROTECTED_FILES        │
  │  read_file()     → lit un fichier (+ start/end)   │
  │  shell_exec()    → npm/prisma/tsc/build           │
  │  rag_search()    → Qdrant (68 standards)          │
  │  file_exists()   → vérifie présence               │
  │  list_directory()→ liste un dossier               │
  └─────────────────────────┬─────────────────────────┘
                             │ (toujours)
                             ▼
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  file_validate_node()  [V]  :740                                         │
  │                                                                          │
  │  RESPONSABILITÉ : attraper les erreurs TypeScript PENDANT la génération │
  │  (avant le build) — sur les fichiers écrits CE TOUR UNIQUEMENT          │
  │                                                                          │
  │  1. _extract_written_ts_files() → quels .ts/.tsx écrits ce tour ?       │
  │  2. tsc --noEmit → erreurs dans tout le projet                          │
  │  3. _parse_tsc_errors_for_files() → filtre : erreurs de CE tour seul    │
  │  4. Boucle d'enrichissement :                                            │
  │     A2 : lit lignes N±4 du fichier fautif → snippet de code             │
  │     E1 : si TS2307 + local → "crée le fichier manquant"                 │
  │     (MANQUE : catalogue pour TS2339, TS2322, TS2304...)                 │
  │  5. Retourne errors_enriched dans le state                               │
  └────────────────────┬───────────────────────────────────────────────────-┘
  [route_after_file_validate()]  [R]  :862
              ┌──── Erreurs TS ? ────┐
              │ OUI (retries ≤ 2)    │ NON
              ▼                      ▼
           dev_node         extract_build_error_node()  [D]  :560
           (correction)     │
                            │  Analyse le dernier shell_exec :
                            │  → BUILD SUCCESS → state.success=True
                            │  → BUILD FAILED  → last_build_error
                            │  → Pas de build  → rien
                            └──── [route_after_tools()]  [R]  :639
                                   ┌── success → END ✅
                                   ├── last_error + attempts<3 → dev_node
                                   └── attempts≥3 → END ❌

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
POURQUOI file_validate_node ET _build_targeted_correction COEXISTENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Ils N'OPÈRENT PAS au même moment ni sur la même erreur :

  file_validate_node          _build_targeted_correction
  ────────────────────        ──────────────────────────
  QUAND : après write_file    QUAND : après npm run build
  ERREUR : tsc --noEmit       ERREUR : next build (compilateur Next.js)
  NIVEAU : TypeScript pur     NIVEAU : build complet (tsc + webpack + next)
  AVANT le build              APRÈS le build
  Erreurs des fichiers écrits Erreurs de tout le projet assemblé
  ce tour seulement           (peut inclure d'anciens fichiers)

  Ils sont complémentaires, pas redondants.
  file_validate = ligne de défense 1 (pendant génération)
  _build_targeted_correction = ligne de défense 2 (après build)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COUCHE 3 — ARCHITECT (séparé, avant le dev graph)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  retrieval_node()   [D+RAG]  architect.py
  └── Qdrant query → 10 standards filtrés (stack + status=active)

  planner_node()     [D]      architect.py
  ├── Lit brief.models / .pages / .routes
  ├── _parse_model_str() → PrismaModel par modèle DSL
  └── → ProjectSpec (fingerprint SHA256)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ZONES D'AMÉLIORATION IDENTIFIÉES (à intégrer dans le plan)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ⚠️  _build_targeted_correction()
      → Doit brancher sur le catalogue d'erreurs
      → Actuellement : générique pour tout code d'erreur
      → Cible : diagnostique précis + rag_query injectée

  ⚠️  file_validate_node enrichissement
      → A2 + E1 hardcodés dans la boucle
      → Cible : moteur générique branché sur tsc_error_catalog

  ⚠️  rules_dev.md
      → 190 lignes avec exemples de code = dilution attention
      → Cible : 30 lignes de contraintes pures

  ⚠️  Qdrant
      → 68 standards existants, préventifs uniquement
      → Cible : + standards correctifs (patterns d'implémentation
        sortis de rules_dev.md + un standard par entrée catalogue)
