from datetime import timedelta
from dataclasses import dataclass
from temporalio import workflow
from temporalio.common import RetryPolicy
from typing import Dict, Any
from agents.stack_config import _DEFAULT_STACK_ID
from config.factory_config import SPEC_COVERAGE_SUCCESS_THRESHOLD


@dataclass
class SaaSFactoryRequest:
    phrase: str
    project_name: str
    stack_id: str = _DEFAULT_STACK_ID


@dataclass
class SaaSFactoryOutput:
    workflow_status: str  # "COMPLETED", "FAILED_UNRECOVERABLE"
    build_status: str     # "SUCCESS", "BUILD_FAILED", "TESTS_FAILED", "SEMANTIC_VIOLATION", "NOT_RUN"
    project_name: str
    generated_files_count: int
    pr_url: str
    repo_url: str
    dev_files_count: int
    test_files_count: int
    duration_seconds: float
    error_message: str | None = None

with workflow.unsafe.imports_passed_through():
    from workflows.activities.architect_activity import architect_activity
    from workflows.activities.dev_test_activity import dev_test_activity
    from workflows.activities.github_activity import github_activity
    from workflows.activities.qa_activity import qa_activity
    from workflows.activities.learner_activity import learner_activity


@workflow.defn
class SaaSFactoryWorkflow:

    @workflow.run
    async def run(self, request: "SaaSFactoryRequest | Dict[str, str]") -> "SaaSFactoryOutput":
        if isinstance(request, dict):
            request = SaaSFactoryRequest(
                phrase=request.get("phrase", "phrase inconnue"),
                project_name=request.get("project_name", "default-saas-project"),
                stack_id=request.get("stack_id", _DEFAULT_STACK_ID),
            )

        phrase = request.phrase
        project_name = request.project_name
        stack_id = request.stack_id or _DEFAULT_STACK_ID
        workflow.logger.info(f"Workflow démarré – phrase: {phrase}, project: {project_name}")
        run_id = str(workflow.uuid4())
        workflow.logger.info(f"Workflow run_id={run_id}")

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

        start_time = workflow.now()
        try:
            # Étape 1 : Architect Activity
            architect_result: Dict = await workflow.execute_activity(
                architect_activity,
                args=[{"phrase": phrase, "project_name": project_name, "stack_id": stack_id}, run_id],
                start_to_close_timeout=timedelta(seconds=300),
                retry_policy=architect_retry_policy,
            )

            spec_part = architect_result.get("specification", "")
            mermaid_part = architect_result.get("mermaid_diagram", "")
            requirements_part = architect_result.get("requirements", [])
            spec_validation_status = architect_result.get("spec_validation_status", "OK")
            spec_unmatched_requirements = architect_result.get("spec_unmatched_requirements", [])
            # IR canonique — source de vérité typée (parser déterministe, P1)
            ir_schema_part = architect_result.get("ir_schema", [])
            ir_pages_part = architect_result.get("ir_pages", [])
            ir_routes_part = architect_result.get("ir_routes", [])

            if not spec_part.strip():
                workflow.logger.error(
                    f"Architecte terminé – sortie invalide. Spec: '{spec_part[:100]}...'"
                )
                raise ValueError("Architect Agent produced an invalid or incomplete specification.")

            workflow.logger.info(
                f"Architecte terminé – sortie structurée OK | "
                f"spec_validation={spec_validation_status}"
            )

            # ── SPEC GATE — observation uniquement (non-bloquant) ────────────
            # Voir commentaire identique dans todo_pilot_workflow.py.
            if spec_validation_status == "DEGRADED" and spec_unmatched_requirements:
                workflow.logger.warning(
                    f"[SPEC_GATE] AVERTISSEMENT — spec DEGRADED, {len(spec_unmatched_requirements)} "
                    f"requirement(s) non vérifiés par le validator : {spec_unmatched_requirements} "
                    f"— pipeline continue vers DevAgent"
                )

            # Étape 2 : DevTest fusionné
            dev_test_input = {
                "spec": spec_part,
                "mermaid": mermaid_part,
                "project_name": project_name,
                "stack_id": stack_id,
                "requirements": requirements_part,
                "spec_validation_status": spec_validation_status,
                "spec_unmatched_requirements": spec_unmatched_requirements,
                # IR canonique — coexiste avec requirements: list[str] jusqu'en P4
                "ir_schema": ir_schema_part,
                "ir_pages": ir_pages_part,
                "ir_routes": ir_routes_part,
            }

            dev_test_result: Dict[str, Any] = await workflow.execute_activity(
                dev_test_activity,
                args=[dev_test_input, run_id],
                start_to_close_timeout=timedelta(minutes=45),
                retry_policy=common_retry_policy,
            )

            semantic_violations = dev_test_result.get("semantic_violations", [])
            if semantic_violations:
                workflow.logger.warning(
                    f"Violations sémantiques détectées ({len(semantic_violations)}): "
                    + " | ".join(semantic_violations)
                )

            workflow.logger.info(
                f"DevTest terminé – "
                f"{dev_test_result.get('metadata', {}).get('total_files', 0)} fichiers générés"
            )

            test_output = dev_test_result.get("test_output", {})
            if not isinstance(test_output, dict):
                test_output = {}
            dev_phase_success = bool(
                dev_test_result.get("dev_output", {}).get("success", False)
                if isinstance(dev_test_result.get("dev_output", {}), dict)
                else False
            )
            tests_phase_success = bool(test_output.get("success", False))

            spec_coverage = dev_test_result.get("metadata", {}).get("spec_coverage", 0.0)
            if semantic_violations:
                build_status = "SEMANTIC_VIOLATION"
            elif dev_phase_success:
                # Aligné sur TodoPilotWorkflow : build réussi = SUCCESS.
                # Si spec_coverage < 50%, le build est fonctionnel mais incomplet.
                build_status = "SUCCESS" if spec_coverage >= SPEC_COVERAGE_SUCCESS_THRESHOLD else "PARTIAL"
            else:
                build_status = "BUILD_FAILED"

            all_files = dev_test_result.get("combined_files", {})
            if not all_files:
                workflow.logger.warning("DevTest n'a retourné aucun fichier combiné")

            # Étape 3 : QA Activity (best-effort — un échec ne bloque pas le run)
            e2e_tests: Dict = {}
            try:
                qa_result: Dict = await workflow.execute_activity(
                    qa_activity,
                    args=[{
                        "specification": spec_part,
                        "project_name": project_name,
                        "stack_id": stack_id,
                        "generated_files": all_files,
                    }, run_id],
                    start_to_close_timeout=timedelta(minutes=10),
                    retry_policy=common_retry_policy,
                )
                e2e_tests = qa_result.get("e2e_tests", {})
                workflow.logger.info(f"QA terminé – {len(e2e_tests)} E2E tests générés")
            except Exception as qa_err:
                workflow.logger.warning(f"QA skipped due to error: {qa_err}")

            # Étape 4 : GitHub Activity (best-effort)
            github_result: Dict = {"pr_url": "N/A", "repo_url": "N/A"}
            try:
                github_result = await workflow.execute_activity(
                    github_activity,
                    args=[{"files": {**all_files, **e2e_tests}, "project_name": project_name, "stack_id": stack_id}, run_id],
                    start_to_close_timeout=timedelta(minutes=10),
                    retry_policy=common_retry_policy,
                )
                workflow.logger.info("GitHub terminé")
            except Exception as github_err:
                workflow.logger.warning(f"GitHub skipped due to error: {github_err}")

            # Étape 5 : Learner (best-effort — aligné sur TodoPilotWorkflow)
            try:
                learner_result: Dict = await workflow.execute_activity(
                    learner_activity,
                    args=[run_id],
                    start_to_close_timeout=timedelta(minutes=5),
                    retry_policy=RetryPolicy(maximum_attempts=1),
                )
                workflow.logger.info(
                    f"Learner terminé — {learner_result.get('suggestions_generated', 0)} suggestion(s)"
                )
            except Exception as learner_err:
                workflow.logger.warning(f"Learner skipped due to error: {learner_err}")

            total_time = (workflow.now() - start_time).total_seconds()
            metadata = dev_test_result.get("metadata", {})
            return SaaSFactoryOutput(
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
            )
        except Exception as exc:
            total_time = (workflow.now() - start_time).total_seconds()
            workflow.logger.error(f"SaaSFactory unrecoverable failure: {exc}")
            return SaaSFactoryOutput(
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
            )
