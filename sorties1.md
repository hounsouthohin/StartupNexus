SPRINT R1 — Stop the bleeding
  ✅ GraphRecursionError fix (no_build_iterations)
  ✅ RAG threshold 0.40 → 0.25

ÉTAPE 1 — Fondation types
  ✅ lib/types.ts déterministe (dev_types_generator.py)
  ✅ Intégration dev_graph.py + dev_prompts.py

ÉTAPE 2 — Progressive Validation file-par-file    ← PAS ENCORE FAIT
  ▷ tsc --noEmit <fichier> après chaque write_file
  ▷ injection contexte ciblé si échec

ÉTAPE 3 — Scaffold complet                        ← PAS ENCORE FAIT
  ▷ scaffold_node (zones [[LLM_IMPORTS_ZONE]] / [[LLM_LOGIC_ZONE]])
  ▷ FileMap avec types_exported
  ▷ shared_utils_node (fichiers émergents)

ÉTAPE 4 — IR Blueprints dans Qdrant              ← PAS ENCORE FAIT
  ▷ Migration Qdrant vers IR Templates
  ▷ Architect assemble des fragments pré-validés
