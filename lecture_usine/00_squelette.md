# 00 — Squelette de l'usine (30 Sept 2026)

## Points d'entrée
- `scripts/start.sh` (commande du conteneur factory-worker) : attend Qdrant+Temporal → `init_qdrant.py` → lance `api/flask_api.py` en fond (**CASSÉ** : importe `workflows.factory_workflow` inexistant) → `run/worker.py`.
- `run/worker.py` : worker Temporal, file `factory-task-queue`, 1 workflow (`TodoPilotWorkflow`) + 9 activités.
- `scripts/run_batch.py --briefs x.json` : client Temporal qui lance des runs (seule voie qui marche aujourd'hui). `docker exec factory-worker python scripts/run_batch.py --briefs scripts/<f>.json`.
- Infra Docker : postgres, temporal, temporal-ui (:8080), n8n (:5678, inutile tant que Flask est cassé), qdrant (:6333), factory-worker (:5000 API, :3100 preview).

## Les 7 grandes parties et leurs liens
```
run_batch ─► Temporal ─► worker ─► TodoPilotWorkflow (workflows/)
   1 architect_activity ─► agents/architect.py (LangGraph 7 nœuds)
        └ domain_interpreter, page_planner, spec_enricher (+ project_spec, semantic_spec)
   2 dev_test_activity ─► agents/stacks/base.py (StackAdapter) ─► nextjs_clerk_prisma/adapter ─► dev_graph.py
        dev_graph = chef d'orchestre : dev_model_context + ~20 générateurs dev_*.py
        + service_modules/ + feature_modules/ + templates/*.j2 + planner.py + executor LLM
        (dev_context, dev_prompts, dev_tools, rag_client, shared_tools)
   3 review_activity ─► agents/reviewer.py      (+ correction_pass_activity)
   4 qa_activity ─► agents/qa.py
   5 preview_activity ─► run/preview.py
   6 learner_activity ─► agents/learner.py ─► utils/run_report.py
   7 export_zip, github (désactivé)
```
- `agents/core/` : utilitaires agnostiques (requirements_engine/spec_coverage, journey_validator, quality_validator, error_parser, design_resolver).
- `config/stacks/nextjs-clerk-prisma.json` + `config/stacks/.../templates/` : Stack-as-Config (fichiers fixes, règles).
- `prompts/` : rules_dev, rules_reviewer, factory_capabilities, qa, reviewer.
- `scripts/` : lanceurs de runs, création des standards Qdrant (create_full_standards_v1.py = 4 813 lignes), test_generators.py (non lancé).

## Taille
~23 000 lignes .py/.j2 dans agents+workflows. Plus gros : dev_graph 1478, architect 1105, dev_test_activity 981, prebuild_pipeline 808, dev_form_generator 747, shared_tools 687, dev_pages_generator 692, dev_model_context 682, planner 658, learner 643.

## Code mort probable (aucun import dans la chaîne)
- `agents/prebuild_pipeline.py` (808 l.) — seulement cité par core/pipeline_types & quality_validator.
- `dev_page_composer.py`, `dev_navigation_generator.py` — importés par personne.
- `api/flask_api.py` — cassé.
- `agents/planner.py` ≠ `planner_node` : c'est le planificateur du LLM executor (Plan-and-Execute), pas celui de l'architect.
