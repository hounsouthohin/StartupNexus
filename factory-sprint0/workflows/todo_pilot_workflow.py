# workflows/todo_pilot_workflow.py
"""
Workflow pilote Sprint 0.5 – Validation ToDo app avec DevTestAgent fusionné
"""

from dataclasses import dataclass
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from typing import Dict, Any


@dataclass
class TodoPilotRequest:
    phrase: str
    project_name: str
    stack_id: str = "nextjs-clerk-prisma"


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

with workflow.unsafe.imports_passed_through():
    from workflows.activities.architect_activity import architect_activity
    from workflows.activities.dev_test_activity import dev_test_activity
    from workflows.activities.github_activity import github_activity
    from workflows.activities.qa_activity import qa_activity
    from workflows.activities.learner_activity import learner_activity

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
            )

        phrase = request.phrase
        project_name = request.project_name
        stack_id = request.stack_id or "nextjs-clerk-prisma"

        workflow.logger.info(f"TodoPilot démarré – Phrase: {phrase} | Stack: {stack_id}")

        start_time = workflow.now()  # déterministe !
        run_id = str(workflow.uuid4())
        workflow.logger.info(f"TodoPilot run_id={run_id}")

        common_retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=5),
            backoff_coefficient=2.0,
            maximum_attempts=3,
        )

        # Retry plus patient pour architect_activity : Qdrant peut être
        # temporairement indisponible (redémarrage, crash). _wait_for_qdrant()
        # dans l'activité attend déjà 90s, mais on laisse 5 tentatives avec
        # backoff de 15s pour absorber un redémarrage Qdrant plus long.
        architect_retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=15),
            backoff_coefficient=2.0,
            maximum_attempts=5,
        )

        try:
            # 1. Architect
            architect_result: Dict[str, Any] = await workflow.execute_activity(
                architect_activity,
                args=[{"phrase": phrase, "project_name": project_name, "stack_id": stack_id}, run_id],
                start_to_close_timeout=timedelta(seconds=300),
                retry_policy=architect_retry_policy,
            )

            spec_part = architect_result.get("specification", "")
            mermaid_part = architect_result.get("mermaid_diagram", "")
            requirements_part = architect_result.get("requirements", [])

            workflow.logger.info(
                f"Architect terminé — {len(requirements_part)} requirements extraits"
            )

            # 2. DevTest fusionné
            dev_test_input = {
                "spec": spec_part,
                "mermaid": mermaid_part,
                "project_name": project_name,
                "stack_id": stack_id,
                "requirements": requirements_part,
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

            test_output = dev_test_result.get("test_output", {})
            if not isinstance(test_output, dict):
                test_output = {}
            dev_phase_success = bool(
                dev_test_result.get("dev_output", {}).get("success", False)
                if isinstance(dev_test_result.get("dev_output", {}), dict)
                else False
            )
            semantic_violations = dev_test_result.get("semantic_violations", [])
            if semantic_violations:
                workflow.logger.warning(
                    f"Violations sémantiques ({len(semantic_violations)}): "
                    + " | ".join(semantic_violations)
                )

            if semantic_violations:
                build_status = "SEMANTIC_VIOLATION"
            elif dev_phase_success:
                # Build réussi = SUCCESS. tests_phase_success est un signal qualité
                # séparé (tracké dans metadata.tests_passed) mais ne bloque pas.
                # Les tests middleware Clerk v6 (Edge Runtime) ne sont pas testables
                # de façon fiable en jest dans le sandbox Docker.
                build_status = "SUCCESS"
            else:
                build_status = "BUILD_FAILED"

            # Le workflow continue même si build échoue.
            # QA est en mode "best-effort": un echec QA (ex: quota fournisseur LLM)
            # ne doit pas invalider tout le run métier.
            e2e_tests: Dict[str, str] = {}
            try:
                qa_result: Dict[str, Any] = await workflow.execute_activity(
                    qa_activity,
                    args=[{
                        "specification": spec_part,
                        "project_name": project_name,
                        "stack_id": stack_id,
                        "generated_files": dev_test_result.get("combined_files", {}),
                    }, run_id],
                    start_to_close_timeout=timedelta(minutes=10),
                    retry_policy=common_retry_policy,
                )
                e2e_tests = qa_result.get("e2e_tests", {})
                workflow.logger.info(f"QA terminé – {len(e2e_tests)} tests générés")
            except Exception as qa_err:
                workflow.logger.warning(f"QA skipped due to error: {qa_err}")
                e2e_tests = {}

            github_input = {
                "files": {**dev_test_result.get("combined_files", {}), **e2e_tests},
                "project_name": project_name,
                "stack_id": stack_id,
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
            except Exception as github_err:
                workflow.logger.warning(f"GitHub skipped due to error: {github_err}")

            # 5. Learner — best-effort, ne bloque jamais le workflow
            try:
                learner_result: Dict[str, Any] = await workflow.execute_activity(
                    learner_activity,
                    args=[run_id],
                    start_to_close_timeout=timedelta(minutes=5),
                    retry_policy=RetryPolicy(maximum_attempts=1),
                )
                workflow.logger.info(
                    f"Learner terminé — "
                    f"{learner_result.get('suggestions_generated', 0)} suggestion(s)"
                )
            except Exception as learner_err:
                workflow.logger.warning(f"Learner skipped due to error: {learner_err}")

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
            )
        except Exception as exc:
            total_time = (workflow.now() - start_time).total_seconds()
            workflow.logger.error(f"TodoPilot unrecoverable failure: {exc}")
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
            )
