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
            )

        phrase = request.phrase
        project_name = request.project_name

        workflow.logger.info(f"TodoPilot démarré – Phrase: {phrase}")

        start_time = workflow.now()  # déterministe !

        common_retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=5),
            backoff_coefficient=2.0,
            maximum_attempts=3,
        )

        try:
            # 1. Architect
            architect_result: Dict[str, Any] = await workflow.execute_activity(
                architect_activity,
                {"phrase": phrase, "project_name": project_name},
                start_to_close_timeout=timedelta(seconds=300),
                retry_policy=common_retry_policy,
            )

            spec_part = architect_result.get("specification", "")
            mermaid_part = architect_result.get("mermaid_diagram", "")

            workflow.logger.info("Architect terminé")

            # 2. DevTest fusionné
            dev_test_input = {
                "spec": spec_part,
                "mermaid": mermaid_part,
                "project_name": project_name
            }

            dev_test_result: Dict[str, Any] = await workflow.execute_activity(
                dev_test_activity,
                dev_test_input,
                start_to_close_timeout=timedelta(minutes=45),
                retry_policy=common_retry_policy,
            )

            workflow.logger.info(
                f"DevTest terminé – Fichiers: {dev_test_result.get('metadata', {}).get('total_files', 0)}, "
                f"Success: {dev_test_result.get('success', False)}"
            )

            if dev_test_result.get("success", False):
                build_status = "SUCCESS"
            elif dev_test_result.get("test_output", {}).get("error"):
                build_status = "TESTS_FAILED"
            else:
                build_status = "BUILD_FAILED"

            # Le workflow continue même si build échoue.
            qa_result: Dict[str, Any] = await workflow.execute_activity(
                qa_activity,
                {"specification": spec_part, "project_name": project_name},
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=common_retry_policy,
            )
            e2e_tests = qa_result.get("e2e_tests", {})
            workflow.logger.info(f"QA terminé – {len(e2e_tests)} tests générés")

            github_input = {
                "files": {**dev_test_result.get("combined_files", {}), **e2e_tests},
                "project_name": project_name,
            }

            github_result: Dict[str, Any] = await workflow.execute_activity(
                github_activity,
                github_input,
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=common_retry_policy,
            )

            workflow.logger.info("GitHub terminé")

            # 5. Learner (shadow mode)
            learner_input = {
                "project_name": project_name,
                "specification": spec_part,
                "generated_files": github_input["files"],
                "run_metrics": {
                    "total_duration_seconds": float((workflow.now() - start_time).total_seconds()),
                    "status": "SUCCESS" if build_status == "SUCCESS" else "PARTIAL",
                },
                "e2e_tests": e2e_tests,
                "pr_url": github_result.get("pr_url", ""),
            }
            try:
                await workflow.execute_activity(
                    learner_activity,
                    learner_input,
                    start_to_close_timeout=timedelta(minutes=5),
                    retry_policy=common_retry_policy,
                )
            except Exception as learner_err:
                workflow.logger.warning(f"Learner shadow skipped due to error: {learner_err}")

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
