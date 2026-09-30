# 09 — Configuration de stack, templates fixes, infra

## `config/stacks/nextjs-clerk-prisma.json` (Stack-as-Config, PRINCIPE 1)
Sections réellement lues par le code : `llm_models`, `packages/dev_packages/version_pins` (via templates), `forbidden_imports`, `forbidden_auth_patterns`, `spec_validation`, `code_role_hints` (règles par rôle pour l'executor), `templated_files` + `conditional_templates` (fichiers fixes copiés), `blueprint` (prompt), `qdrant_filter`, `role_rag_queries`, `pre_run_commands`, `protected_files`, `feature_modules`, `testing`.
Sections apparemment **non lues** (aucune référence trouvée dans agents/workflows/utils) : `iteration_policy`, `generation_order`, `token_budgets`, `technology_categories`, `scaffold_extends`, `prompt_rules`, `toolchain`, `test_import_rules`, `supervision`, `mandatory_rag_queries`, `architect_qdrant_filter`, `env_validation` → vestiges d'anciennes architectures.

## Templates fixes (`config/stacks/nextjs-clerk-prisma/templates/`)
package.json, tsconfig, next.config.js, middleware (remplacé par le générateur), layout (remplacé), prisma config/schema de base, lib/prisma.ts (driver adapter pg), lib/logger, lib/prisma-errors, env templates, route webhook Clerk, health, sign-in/up, jest config, test middleware. Copiés par `dev_file_ops.write_template_files`.

## `stack_config.py` / `StackAdapter`
Chargement du JSON + registre d'adaptateurs (1 seul). Base prévue pour le multi-stack, mais toute la logique de génération est dans `agents/stacks/nextjs_clerk_prisma/` (≈ 9 000 lignes spécifiques à cette stack) : ajouter une stack = réécrire presque tous les générateurs.

## Prompts (`prompts/`)
`stacks/nextjs-clerk-prisma/rules_dev.md` (21 règles pour l'executor), `rules_reviewer.md`, `factory_capabilities.md` ; `base/reviewer.md`, `base/qa.md`.

## Infra
Docker compose : postgres (Temporal + bases preview), Temporal + UI, n8n (inutile : Flask cassé), Qdrant (150 standards, RAG gelé mais encore interrogé par l'executor et le reviewer), factory-worker (Python 3.11 + Node, volumes generated-projects, bind-mounts du code en dev). Preview : `next dev` sur :3100 dans le worker.

## Scripts
`run_batch.py` (lanceur), `create_full_standards_v1.py` (4 813 l. de standards Qdrant), `enrich_qdrant.py`, `test_generators.py` (408 l., jamais lancé, importe les générateurs directement — base naturelle du harnais), `validate_contracts.py` (JSON Schema des activités), `preview.ps1`, `prebuild_shadcn.ps1`.
