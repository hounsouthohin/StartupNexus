from datetime import timedelta
from dataclasses import dataclass
from temporalio import workflow
from temporalio.common import RetryPolicy
from typing import Dict, Any


@dataclass
class SaaSFactoryRequest:
    phrase: str
    project_name: str


@dataclass
class SaaSFactoryOutput:
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

# ✅ Bonne pratique : imports des activités (modules lourds) isolés hors sandbox
# workflow.unsafe.imports_passed_through() indique explicitement au sandbox
# que ces modules viennent du monde extérieur et ne sont pas soumis
# aux restrictions de déterminisme — sans désactiver la protection globalement.
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
            )

        phrase = request.phrase
        project_name = request.project_name
        workflow.logger.info(f"Workflow démarré – phrase: {phrase}, project: {project_name}")

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
                {"phrase": phrase, "project_name": project_name},
                start_to_close_timeout=timedelta(seconds=300),
                retry_policy=architect_retry_policy,
            )

            spec_part = architect_result.get("specification", "")
            mermaid_part = architect_result.get("mermaid_diagram", "")

            if not spec_part.strip() or not mermaid_part.strip():
                workflow.logger.error(
                    f"Architecte terminé – sortie invalide. Spec: '{spec_part[:100]}...'"
                )
                raise ValueError("Architect Agent produced an invalid or incomplete specification.")

            workflow.logger.info("Architecte terminé – sortie structurée OK")

            # Étape 2 : DevTest fusionné
            dev_test_input = {
                "spec": spec_part,
                "mermaid": mermaid_part,
                "project_name": project_name,
            }

            dev_test_result: Dict[str, Any] = await workflow.execute_activity(
                dev_test_activity,
                dev_test_input,
                start_to_close_timeout=timedelta(minutes=45),
                retry_policy=common_retry_policy,
            )

            workflow.logger.info(
                f"DevTest terminé – "
                f"{dev_test_result.get('metadata', {}).get('total_files', 0)} fichiers générés"
            )

            test_output = dev_test_result.get("test_output", {})
            if not isinstance(test_output, dict):
                test_output = {}
            tests_payload = test_output.get("tests", {})
            tests_generated = isinstance(tests_payload, dict) and len(tests_payload) > 0
            dev_phase_success = bool(
                dev_test_result.get("dev_output", {}).get("success", False)
                if isinstance(dev_test_result.get("dev_output", {}), dict)
                else False
            )

            if dev_test_result.get("success", False):
                build_status = "SUCCESS"
            elif dev_phase_success and (bool(test_output.get("error")) or not tests_generated):
                build_status = "TESTS_FAILED"
            else:
                build_status = "BUILD_FAILED"

            all_files = dev_test_result.get("combined_files", {})
            if not all_files:
                workflow.logger.warning("DevTest n'a retourné aucun fichier combiné")

            # Étape 3 : QA Activity
            qa_result: Dict = await workflow.execute_activity(
                qa_activity,
                {"specification": spec_part, "project_name": project_name},
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=common_retry_policy,
            )

            generated_e2e_tests = qa_result.get("e2e_tests", {})
            if not generated_e2e_tests:
                workflow.logger.warning("QA Agent did not generate any E2E tests.")
            else:
                workflow.logger.info(f"QA terminé – {len(generated_e2e_tests)} E2E tests générés")

            # Étape 4 : GitHub Activity
            all_files.update(generated_e2e_tests)

            github_result: Dict = await workflow.execute_activity(
                github_activity,
                {"files": all_files, "project_name": project_name},
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=common_retry_policy,
            )
            workflow.logger.info("GitHub terminé")

            # Étape 5 : Learner Activity (shadow mode)
            learner_input = {
                "project_name": project_name,
                "specification": spec_part,
                "generated_files": all_files,
                "run_metrics": {
                    "total_duration_seconds": float((workflow.now() - start_time).total_seconds()),
                    "status": "SUCCESS" if build_status == "SUCCESS" else "PARTIAL",
                },
                "e2e_tests": generated_e2e_tests,
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
