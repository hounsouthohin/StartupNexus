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
)


@dataclass
class TodoPilotRequest:
    brief: dict
    project_name: str
    stack_id: str = "nextjs-clerk-prisma"
    sanity_mode: bool = False
    review_mode: bool = False  # arrêt après review+correction_pass, avant QA/GitHub/Learner


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
    from workflows.activities.review_activity import review_activity
    from workflows.activities.correction_pass_activity import correction_pass_activity
    from workflows.activities.github_activity import github_activity
    from workflows.activities.qa_activity import qa_activity
    from workflows.activities.learner_activity import learner_activity
    from utils.run_report import write_run_report_minimal as _write_run_report_minimal
@workflow.defn
class TodoPilotWorkflow:
    """Workflow de validation pour le pilote ToDo Sprint 0.5."""

    @workflow.run
    async def run(self, request: "TodoPilotRequest | Dict[str, str]") -> "TodoPilotOutput":
        if isinstance(request, dict):
            request = TodoPilotRequest(
                brief=request.get("brief", {}),
                project_name=request.get("project_name", "todo-pilot-sprint05"),
                stack_id=request.get("stack_id", "nextjs-clerk-prisma"),
                sanity_mode=bool(request.get("sanity_mode", False)),
                review_mode=bool(request.get("review_mode", False)),
            )

        brief = request.brief if isinstance(request.brief, dict) else {}
        project_name = request.project_name
        stack_id = request.stack_id or "nextjs-clerk-prisma"
        sanity_mode = bool(request.sanity_mode)
        review_mode = bool(request.review_mode)

        workflow.logger.info(f"TodoPilot démarré – Projet: {project_name} | Brief: {brief.get('description', '')[:80]} | Stack: {stack_id}")

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
                args=[{"brief": brief, "project_name": project_name, "stack_id": stack_id}, run_id],
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

            if spec_validation_status == "DEGRADED":
                workflow.logger.error(
                    f"[SPEC_GATE] BLOQUANT — spec DEGRADED, "
                    f"modèle(s) absent(s) de ProjectSpec : {spec_unmatched_requirements}"
                )
                # En sanity_mode : arrêt immédiat — la spec est invalide, inutile de générer.
                # En mode normal : même chose — un ProjectSpec incomplet produira un build corrompu.
                total_time = (workflow.now() - start_time).total_seconds()
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
                    error_message=f"SPEC_DEGRADED: modèles absents {spec_unmatched_requirements}",
                    activity_results=activity_results,
                )
            elif spec_validation_status == "UNKNOWN":
                workflow.logger.warning(
                    "[SPEC_GATE] AVERTISSEMENT — spec_validation=UNKNOWN (ProjectSpec sans modèles) — pipeline continue"
                )

            # ── 2. DevTest (génération + supervision interne + build) ─────
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
                "project_spec": project_spec_part,
                "workflow_id": f"todo-pilot-{project_name}",
            }

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

            # ── 3. Review sémantique post-build ──────────────────────────────
            # Skippé si BUILD_FAILED ou SEMANTIC_VIOLATION — un build cassé ne mérite pas une revue.
            # Logique : COHERENT → continue | DEGRADED/INCOHERENT → correction_pass → re-review.
            review_verdict = "SKIPPED"
            if build_status in ("SUCCESS", "PARTIAL"):
                review_input: Dict[str, Any] = {
                    "project_name": project_name,
                    "stack_id": stack_id,
                    "brief": brief.get("description", "") if isinstance(brief, dict) else str(brief),
                    "spec": project_spec_part,
                    "user_flows": user_flows_part,
                    "generated_files": combined_files,
                    "build_status": "BUILD_SUCCESS",
                }
                try:
                    review_result: Dict[str, Any] = await workflow.execute_activity(
                        review_activity,
                        args=[review_input, run_id],
                        start_to_close_timeout=timedelta(minutes=10),
                        retry_policy=RetryPolicy(maximum_attempts=1),
                    )
                    review_verdict = review_result.get("review_verdict", "SKIPPED")
                    review_report: Dict[str, Any] = review_result.get("review_report", {})

                    workflow.logger.info(
                        f"[REVIEW] verdict={review_verdict} "
                        f"sec={review_report.get('security_score')} "
                        f"coh={review_report.get('coherence_score')} "
                        f"findings={len(review_report.get('findings', []))}"
                    )
                    activity_results["review"] = {
                        "status": "COMPLETED",
                        "verdict": review_verdict,
                        "security_score": review_report.get("security_score"),
                        "coherence_score": review_report.get("coherence_score"),
                        "findings_count": len(review_report.get("findings", [])),
                        "summary": review_report.get("summary", ""),
                    }

                    # ── Correction pass si DEGRADED ou INCOHERENT ─────────────
                    if review_verdict in ("DEGRADED", "INCOHERENT"):
                        targeted_fixes = review_report.get("targeted_fixes", []) or []
                        if targeted_fixes:
                            correction_input: Dict[str, Any] = {
                                "project_name": project_name,
                                "stack_id": stack_id,
                                "targeted_fixes": targeted_fixes,
                                "review_verdict": review_verdict,
                            }
                            try:
                                correction_result: Dict[str, Any] = await workflow.execute_activity(
                                    correction_pass_activity,
                                    args=[correction_input, run_id],
                                    start_to_close_timeout=timedelta(minutes=15),
                                    retry_policy=RetryPolicy(maximum_attempts=1),
                                )
                                correction_applied = bool(correction_result.get("correction_applied", False))
                                new_build_status = str(correction_result.get("new_build_status", ""))
                                updated_files: Dict[str, str] = correction_result.get("updated_files", {}) or {}

                                if correction_applied and updated_files:
                                    combined_files = {**combined_files, **updated_files}

                                activity_results["correction_pass"] = {
                                    "status": "COMPLETED",
                                    "applied": correction_applied,
                                    "files_modified": correction_result.get("files_modified", []),
                                    "new_build_status": new_build_status,
                                }

                                # Re-review après correction (max 1 fois)
                                if correction_applied and new_build_status == "BUILD_SUCCESS":
                                    try:
                                        review_input2 = {**review_input, "generated_files": combined_files}
                                        review_result2: Dict[str, Any] = await workflow.execute_activity(
                                            review_activity,
                                            args=[review_input2, run_id],
                                            start_to_close_timeout=timedelta(minutes=10),
                                            retry_policy=RetryPolicy(maximum_attempts=1),
                                        )
                                        review_verdict = review_result2.get("review_verdict", review_verdict)
                                        review_report2: Dict[str, Any] = review_result2.get("review_report", {})
                                        workflow.logger.info(
                                            f"[REVIEW] post-correction verdict={review_verdict} "
                                            f"sec={review_report2.get('security_score')}"
                                        )
                                        activity_results["review"]["post_correction_verdict"] = review_verdict
                                        activity_results["review"]["post_correction_security_score"] = review_report2.get("security_score")
                                        activity_results["review"]["post_correction_coherence_score"] = review_report2.get("coherence_score")
                                    except Exception as rev2_err:
                                        workflow.logger.warning(f"[REVIEW] Re-review post-correction échoué (non-bloquant): {rev2_err}")
                                elif correction_applied and new_build_status != "BUILD_SUCCESS":
                                    workflow.logger.warning(
                                        f"[CORRECTION_PASS] Re-build échoué après correction — "
                                        f"status={new_build_status[:80]}"
                                    )

                            except Exception as corr_err:
                                workflow.logger.warning(f"[CORRECTION_PASS] échoué (non-bloquant): {corr_err}")
                                activity_results["correction_pass"] = {"status": "FAILED", "error": str(corr_err)}
                        else:
                            workflow.logger.warning(
                                f"[REVIEW] verdict={review_verdict} mais targeted_fixes vide — correction ignorée"
                            )
                            activity_results["correction_pass"] = {"status": "SKIPPED_NO_FIXES"}

                    # Downgrade build_status si INCOHERENT persistant après correction
                    if review_verdict == "INCOHERENT":
                        workflow.logger.warning(
                            "[REVIEW] App INCOHERENT après correction — build_status downgradé"
                        )
                        build_status = "REVIEW_INCOHERENT"

                except Exception as review_err:
                    workflow.logger.warning(f"[REVIEW] échoué (non-bloquant): {review_err}")
                    activity_results["review"] = {"status": "FAILED", "error": str(review_err)}
            else:
                workflow.logger.info(f"[REVIEW] Skippé — build_status={build_status}")
                activity_results["review"] = {"status": f"SKIPPED_{build_status}"}

            # Mode review : arrêt après review+correction_pass, avant QA/GitHub/Learner
            if review_mode:
                total_time = (workflow.now() - start_time).total_seconds()
                metadata = dev_test_result.get("metadata", {})
                workflow.logger.info("[REVIEW_MODE] Early return after review+correction_pass")
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

            # ── 4. QA — génération tests e2e (uniquement si build success) ──
            # Skippé si BUILD_FAILED ou REVIEW_INCOHERENT : app trop dégradée pour générer des tests utiles.
            e2e_tests: Dict[str, str] = {}
            if build_status not in ("BUILD_FAILED", "SEMANTIC_VIOLATION", "REVIEW_INCOHERENT"):
                workflow.logger.info("[QA] Génération tests e2e")
                qa_input = {
                    "specification": spec_part,
                    "project_name": project_name,
                    "stack_id": stack_id,
                    "generated_files": combined_files,
                }
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
            else:
                workflow.logger.info(f"[QA] Skippé — build_status={build_status} (0 token dépensé)")
                activity_results["qa"] = {"status": f"SKIPPED_{build_status}", "tests_count": 0}

            # ── 5. GitHub ─────────────────────────────────────────────────
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

            # ── 6. Learner — best-effort ───────────────────────────────────
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
