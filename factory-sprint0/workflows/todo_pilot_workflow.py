# workflows/todo_pilot_workflow.py
"""
Workflow pilote Sprint 0.5 – Validation ToDo app avec DevTestAgent fusionné.

M2 : Phase de supervision parallèle (conformity || security || architecture || qa)
     après dev_test_activity, visible dans Temporal UI.
"""

from dataclasses import dataclass
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from typing import Dict, Any
from config.factory_config import (
    SPEC_COVERAGE_SUCCESS_THRESHOLD,
    SPEC_COVERAGE_PARTIAL_THRESHOLD,
    TEMPORAL_PARALLEL_MODE,
)


@dataclass
class TodoPilotRequest:
    phrase: str
    project_name: str
    stack_id: str = "nextjs-clerk-prisma"
    sanity_mode: bool = False


@dataclass
class TodoPilotOutput:
    workflow_status: str  # "COMPLETED", "FAILED_UNRECOVERABLE"
    build_status: str     # "SUCCESS", "BUILD_FAILED", "TESTS_FAILED", "NOT_RUN"
    project_name: str
    generated_files_count: int
    pr_url: str
    repo_url: str
    dev_files_count: int
    test_files_count: int
    duration_seconds: float
    error_message: str | None = None
    activity_results: Dict[str, Any] | None = None

with workflow.unsafe.imports_passed_through():
    from workflows.activities.architect_activity import architect_activity
    from workflows.activities.dev_test_activity import dev_test_activity
    from workflows.activities.github_activity import github_activity
    from workflows.activities.qa_activity import qa_activity
    from workflows.activities.learner_activity import learner_activity
    from utils.run_report import write_run_report_minimal as _write_run_report_minimal
    # M2 superviseurs post-build retirés — supervision inline dans dev.py (source unique)
    # conformity/security/architecture restent dans dev.py via supervision_manager
    # M3 — child workflow GenerationSessionWorkflow (Phase 5, non encore câblé)
    from workflows.generation_session_workflow import GenerationSessionWorkflow

@workflow.defn
class TodoPilotWorkflow:
    """Workflow de validation pour le pilote ToDo Sprint 0.5."""

    @workflow.run
    async def run(self, request: "TodoPilotRequest | Dict[str, str]") -> "TodoPilotOutput":
        if isinstance(request, dict):
            request = TodoPilotRequest(
                phrase=request.get("phrase", "Crée une ToDo app Next.js avec Clerk auth"),
                project_name=request.get("project_name", "todo-pilot-sprint05"),
                stack_id=request.get("stack_id", "nextjs-clerk-prisma"),
                sanity_mode=bool(request.get("sanity_mode", False)),
            )

        phrase = request.phrase
        project_name = request.project_name
        stack_id = request.stack_id or "nextjs-clerk-prisma"
        sanity_mode = bool(request.sanity_mode)

        workflow.logger.info(f"TodoPilot démarré – Phrase: {phrase} | Stack: {stack_id}")

        start_time = workflow.now()
        run_id = str(workflow.uuid4())
        workflow.logger.info(f"TodoPilot run_id={run_id}")

        common_retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=5),
            backoff_coefficient=2.0,
            maximum_attempts=3,
        )
        architect_retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=15),
            backoff_coefficient=2.0,
            maximum_attempts=5,
        )
        qa_retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=5),
            backoff_coefficient=2.0,
            maximum_attempts=2,
        )

        try:
            activity_results: Dict[str, Any] = {}

            # ── 1. Architect ──────────────────────────────────────────────
            architect_result: Dict[str, Any] = await workflow.execute_activity(
                architect_activity,
                args=[{"phrase": phrase, "project_name": project_name, "stack_id": stack_id}, run_id],
                start_to_close_timeout=timedelta(seconds=300),
                retry_policy=architect_retry_policy,
            )

            spec_part = architect_result.get("specification", "")
            mermaid_part = architect_result.get("mermaid_diagram", "")
            requirements_part = architect_result.get("requirements", [])
            user_flows_part = architect_result.get("user_flows", [])
            spec_validation_status = architect_result.get("spec_validation_status", "OK")
            spec_unmatched_requirements = architect_result.get("spec_unmatched_requirements", [])
            ir_schema_part = architect_result.get("ir_schema", [])
            ir_pages_part = architect_result.get("ir_pages", [])
            ir_routes_part = architect_result.get("ir_routes", [])
            plan_part = architect_result.get("plan", {})
            project_spec_part = architect_result.get("project_spec", {})

            workflow.logger.info(
                f"Architect terminé — {len(requirements_part)} requirements | "
                f"spec_validation={spec_validation_status}"
            )
            activity_results["architect"] = {
                "status": "COMPLETED",
                "spec_validation_status": spec_validation_status,
                "requirements_count": len(requirements_part),
                "spec_unmatched_requirements": spec_unmatched_requirements,
            }

            if spec_validation_status == "DEGRADED" and spec_unmatched_requirements:
                workflow.logger.warning(
                    f"[SPEC_GATE] AVERTISSEMENT — spec DEGRADED, "
                    f"{len(spec_unmatched_requirements)} requirement(s) non vérifiés — "
                    f"pipeline continue"
                )

            # ── 2. DevTest (génération + supervision interne + build) ─────
            run_mode = TEMPORAL_PARALLEL_MODE  # lu une seule fois pour ce run
            workflow.logger.info(f"[PARALLEL_MODE] run_mode={run_mode}")

            dev_test_input = {
                "spec": spec_part,
                "mermaid": mermaid_part,
                "project_name": project_name,
                "stack_id": stack_id,
                "requirements": requirements_part,
                "user_flows": user_flows_part,
                "spec_validation_status": spec_validation_status,
                "spec_unmatched_requirements": spec_unmatched_requirements,
                "ir_schema": ir_schema_part,
                "ir_pages": ir_pages_part,
                "ir_routes": ir_routes_part,
                "run_mode": run_mode,  # propagé aux activités pour traçabilité
                "project_spec": project_spec_part,  # Nouvelle Base — ProjectSpec sérialisé
                "workflow_id": f"todo-pilot-{project_name}",
            }

            if run_mode == "workflow":
                # M2 — child workflow GenerationSessionWorkflow (non encore fully opérationnel)
                # Pour l'instant, fallback inline avec log d'avertissement.
                workflow.logger.warning(
                    "[PARALLEL_MODE] run_mode=workflow demandé mais GenerationSessionWorkflow "
                    "n'est pas encore pleinement câblé — fallback inline."
                )

            dev_test_result: Dict[str, Any] = await workflow.execute_activity(
                dev_test_activity,
                args=[dev_test_input, run_id],
                start_to_close_timeout=timedelta(minutes=45),
                retry_policy=common_retry_policy,
            )

            workflow.logger.info(
                f"DevTest terminé – Fichiers: {dev_test_result.get('metadata', {}).get('total_files', 0)}, "
                f"Success: {dev_test_result.get('success', False)}"
            )
            activity_results["dev_test"] = {
                "status": "COMPLETED",
                "success": bool(dev_test_result.get("success", False)),
                "run_metric": dev_test_result.get("run_metric", {}),
                "semantic_violations": dev_test_result.get("semantic_violations", []),
                "metadata": dev_test_result.get("metadata", {}),
                "final_message": (
                    dev_test_result.get("dev_output", {}).get("final_message", "")
                    if isinstance(dev_test_result.get("dev_output", {}), dict)
                    else ""
                ),
            }

            dev_phase_success = bool(
                dev_test_result.get("dev_output", {}).get("success", False)
                if isinstance(dev_test_result.get("dev_output", {}), dict)
                else False
            )
            semantic_violations = dev_test_result.get("semantic_violations", [])
            spec_coverage = dev_test_result.get("metadata", {}).get("spec_coverage", 0.0)
            combined_files: Dict[str, str] = dev_test_result.get("combined_files", {}) or {}

            if semantic_violations:
                workflow.logger.warning(
                    f"Violations sémantiques ({len(semantic_violations)}): "
                    + " | ".join(semantic_violations)
                )

            # ── Build status provisoire (avant superviseurs) ──────────────
            if semantic_violations:
                build_status = "SEMANTIC_VIOLATION"
            elif dev_phase_success:
                if spec_coverage >= SPEC_COVERAGE_SUCCESS_THRESHOLD:
                    build_status = "SUCCESS"
                elif spec_coverage >= SPEC_COVERAGE_PARTIAL_THRESHOLD:
                    build_status = "PARTIAL"
                else:
                    workflow.logger.warning(
                        f"[requirements_gate] DOWNGRADE BUILD_FAILED — "
                        f"spec_coverage={spec_coverage:.0%} < {SPEC_COVERAGE_PARTIAL_THRESHOLD:.0%}"
                    )
                    build_status = "BUILD_FAILED"
            else:
                build_status = "BUILD_FAILED"

            # Mode sanity : arrêt court après DevTest
            if sanity_mode:
                total_time = (workflow.now() - start_time).total_seconds()
                metadata = dev_test_result.get("metadata", {})
                workflow.logger.info("[SANITY_MODE] Early return after dev_test_activity")
                return TodoPilotOutput(
                    workflow_status="COMPLETED",
                    build_status=build_status,
                    project_name=project_name,
                    generated_files_count=int(metadata.get("total_files", 0)),
                    pr_url="N/A",
                    repo_url="N/A",
                    dev_files_count=int(metadata.get("dev_files_count", 0)),
                    test_files_count=int(metadata.get("test_files_count", 0)),
                    duration_seconds=float(total_time),
                    error_message=None,
                    activity_results=activity_results,
                )

            # ── 3. QA — génération tests e2e (supervision inline déjà faite dans dev.py) ──
            # Note : conformity/security/architecture superviseurs retirés de cette phase.
            # Ils s'exécutent inline dans dev.py via supervision_manager (source unique).
            workflow.logger.info("[QA] Génération tests e2e")

            qa_input = {
                "specification": spec_part,
                "project_name": project_name,
                "stack_id": stack_id,
                "generated_files": combined_files,
            }

            e2e_tests: Dict[str, str] = {}
            try:
                qa_result_raw: Dict[str, Any] = await workflow.execute_activity(
                    qa_activity,
                    args=[qa_input, run_id],
                    start_to_close_timeout=timedelta(minutes=10),
                    retry_policy=qa_retry_policy,
                )
                e2e_tests = qa_result_raw.get("e2e_tests", {})
                workflow.logger.info(f"[QA] {len(e2e_tests)} tests générés")
                activity_results["qa"] = {"status": "COMPLETED", "tests_count": len(e2e_tests)}
            except Exception as qa_err:
                workflow.logger.warning(f"[QA] échoué: {qa_err}")
                activity_results["qa"] = {"status": "FAILED", "error": str(qa_err), "tests_count": 0}

            # ── 4. GitHub ─────────────────────────────────────────────────
            github_input = {
                "files": {**combined_files, **e2e_tests},
                "project_name": project_name,
                "stack_id": stack_id,
                "build_success": dev_phase_success,
                "spec_coverage": spec_coverage,
                "spec_validation_status": dev_test_result.get("metadata", {}).get(
                    "spec_validation_status", "UNKNOWN"
                ),
            }

            github_result: Dict[str, Any] = {"pr_url": "N/A", "repo_url": "N/A"}
            try:
                github_result = await workflow.execute_activity(
                    github_activity,
                    args=[github_input, run_id],
                    start_to_close_timeout=timedelta(minutes=10),
                    retry_policy=common_retry_policy,
                )
                workflow.logger.info("GitHub terminé")
                activity_results["github"] = {
                    "status": "COMPLETED",
                    "repo_url": github_result.get("repo_url", "N/A"),
                    "pr_url": github_result.get("pr_url", "N/A"),
                }
            except Exception as github_err:
                workflow.logger.warning(f"GitHub skipped: {github_err}")
                activity_results["github"] = {
                    "status": "FAILED",
                    "error": str(github_err),
                    "repo_url": "N/A",
                    "pr_url": "N/A",
                }

            # ── 5. Learner — best-effort ───────────────────────────────────
            try:
                learner_result: Dict[str, Any] = await workflow.execute_activity(
                    learner_activity,
                    args=[run_id],
                    start_to_close_timeout=timedelta(minutes=5),
                    retry_policy=RetryPolicy(maximum_attempts=1),
                )
                workflow.logger.info(
                    f"Learner terminé — {learner_result.get('suggestions_generated', 0)} suggestion(s)"
                )
                activity_results["learner"] = {
                    "status": "COMPLETED",
                    "suggestions_generated": learner_result.get("suggestions_generated", 0),
                }
            except Exception as learner_err:
                workflow.logger.warning(f"Learner skipped: {learner_err}")
                activity_results["learner"] = {"status": "FAILED", "error": str(learner_err)}

            total_time = (workflow.now() - start_time).total_seconds()
            metadata = dev_test_result.get("metadata", {})

            return TodoPilotOutput(
                workflow_status="COMPLETED",
                build_status=build_status,
                project_name=project_name,
                generated_files_count=int(metadata.get("total_files", 0)),
                pr_url=github_result.get("pr_url", "N/A"),
                repo_url=github_result.get("repo_url", "N/A"),
                dev_files_count=int(metadata.get("dev_files_count", 0)),
                test_files_count=int(metadata.get("test_files_count", 0)),
                duration_seconds=float(total_time),
                error_message=None,
                activity_results=activity_results,
            )

        except Exception as exc:
            total_time = (workflow.now() - start_time).total_seconds()
            workflow.logger.error(f"TodoPilot unrecoverable failure: {exc}")

            # Fallback run_report minimal si DevTest n'a pas tourné (P0-C1)
            try:
                _write_run_report_minimal(
                    run_id=str(run_id),
                    workflow_id=f"todo-pilot-{project_name}",
                    project_name=project_name,
                    error=str(exc),
                )
            except Exception:
                pass  # non bloquant

            return TodoPilotOutput(
                workflow_status="FAILED_UNRECOVERABLE",
                build_status="NOT_RUN",
                project_name=project_name,
                generated_files_count=0,
                pr_url="N/A",
                repo_url="N/A",
                dev_files_count=0,
                test_files_count=0,
                duration_seconds=float(total_time),
                error_message=str(exc),
                activity_results={"workflow": {"status": "FAILED", "error": str(exc)}},
            )
