# 01 — Orchestration (workflow + activités)

## Flux (TodoPilotWorkflow)
1. **architect_activity** : valide le brief (JSON Schema `validate_contracts`), lance le graphe LangGraph, récupère `project_spec` (dict ProjectSpec+enriched_spec+summary_fr+unsupported), l'écrit dans `FACTORY_WORKDIR/project_spec_<projet>.json`. Contrôles : patterns auth interdits dans le brief (bcrypt, jwt…), `spec_validation_status` (OK/DEGRADED/UNKNOWN — DEGRADED seulement si le brief fournit des modèles absents du spec), mots interdits. Retry 5x.
2. **Gate** : DEGRADED → arrêt FAILED_UNRECOVERABLE.
3. **dev_test_activity** : `get_adapter_for_stack(stack_id).run_dev_agent(spec)` → dev_graph. Puis : scan disque → `combined_files`, `tsc` post-mortem, **retry unique** si tsc KO = relance COMPLÈTE de `run_dev_agent` (qui efface le workdir et régénère tout) avec feedback tsc → inutile quand le bug est dans un fichier déterministe protégé. Puis métriques : `spec_coverage` (requirements = liste « Modèle X / Page Y » → preuve d'existence de fichiers, pas de sens), `journey_validator` (user_flows), `is_useful_app`, `prisma validate`, `_classify_root_cause` (classement textuel des erreurs), cohérence des métriques, snapshot JSON, run_report.
4. **build_status** : SUCCESS si build OK et spec_coverage ≥ seuil (sinon PARTIAL/BUILD_FAILED).
5. **review_activity** (si build OK) : sélectionne ≤14 fichiers (middleware, page.tsx, page-client, actions, services), récupère 5 requêtes de standards Qdrant (agent_context=reviewer), `run_reviewer` (L1 déterministe auth/PII + L2 LLM gpt-4o).
6. **correction_pass_activity** si findings WRONG_AUTH/MISSING_AUTH/BRIEF_CONFORMITY : ne touche QUE les page.tsx non protégées (regex pour auth, 1 appel LLM pour conformité), max 3, rebuild sans npm install. Puis re-review.
7. **qa_activity** : LLM génère des tests Jest (schemas/services), `npx jest`, Semgrep. Non bloquant (échoue en routine).
8. **preview_activity** (si PREVIEW_ENABLED) : `run/preview.py` crée une base postgres via SDK Docker, `prisma db push`, `node prisma/seed.mjs`, lance `next dev :3100` détaché (ORACLE_ENABLED=1, ADMIN_EMAILS). Personne n'appelle `/api/oracle`.
9. github (désactivé), **learner_activity** (suggestions + FactoryRunReport .md), export_zip.

## StackAdapter (`agents/stacks/base.py`)
Interface abstraite : `run_dev_agent`, `pre_run_commands`, `protected_files`, `role_rag_queries` (lus depuis la config JSON). Registre à 1 entrée (nextjs-clerk-prisma). Prévu pour le multi-stack.

## Techniques
Temporal (activités async, retry policies, timeouts), contrats JSON Schema (`schemas/contracts/*`), subprocess (tsc, npm, prisma, jest, semgrep), SDK Docker.

## Points notables
- Les métriques de tête (spec_coverage, requirements, user_flows) mesurent l'EXISTENCE de fichiers/routes, pas le sens — d'où « 17/17 » sur une app qui ne build pas.
- Le retry tsc double la durée sans pouvoir corriger un bug de générateur (tout est régénéré à l'identique).
- Beaucoup de code de métriques/diagnostic (≈ la moitié de dev_test_activity) autour d'un seul signal fiable : le build.
- correction_pass ne peut agir que sur les pages LLM → aveugle aux défauts d'âme (qui viennent de la déclaration ou des générateurs).
