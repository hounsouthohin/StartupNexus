from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from typing import Dict

# Import the new activities
from workflows.activities.test_coverage_activity import test_coverage_activity
from workflows.activities.qa_activity import qa_activity

# Logger pour Temporal UI
workflow.logger = workflow.logger

@workflow.defn
class SaaSFactoryWorkflow:
    @workflow.run
    async def run(self, input_data: Dict[str, str]) -> str:
        phrase = input_data.get("phrase", "phrase inconnue")
        project_name = input_data.get("project_name", "default-saas-project")
        workflow.logger.info(f"Workflow démarré – phrase: {phrase}, Project: {project_name}")

        common_retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=5),
            backoff_coefficient=2.0,
            maximum_attempts=3,
        )

        # Étape 1 : Architect Activity
        architect_result: Dict = await workflow.execute_activity(
            "architect_activity",
            input_data,
            start_to_close_timeout=timedelta(seconds=300),
            retry_policy=common_retry_policy,
        )
        spec_part = architect_result.get("specification", "")
        mermaid_part = architect_result.get("mermaid_diagram", "")

        # Add a more robust check for a valid specification
        if not spec_part or not mermaid_part or "I'm sorry" in spec_part:
            workflow.logger.error(f"Architecte terminé – sortie invalide ou incomplète. Spec: '{spec_part}'")
            raise ValueError("Architect Agent produced an invalid or incomplete specification.")
            
        workflow.logger.info("Architecte terminé – sortie structurée OK")

        # Étape 2 : Dev Activity
        dev_input = {"spec": spec_part, "mermaid": mermaid_part, "project_name": project_name}
        dev_result: Dict = await workflow.execute_activity(
            "dev_activity",
            dev_input,
            start_to_close_timeout=timedelta(minutes=30),
            retry_policy=common_retry_policy,
        )
        workflow.logger.info("Dev terminé – code généré")

        # Étape 3 : TestCoverage Activity
        test_result: Dict = await workflow.execute_activity(
            "test_coverage_activity",
            dev_result.get("files", {}),
            start_to_close_timeout=timedelta(minutes=15),
            retry_policy=common_retry_policy,
        )
        generated_tests = test_result.get("tests", {})
        if not generated_tests:
            workflow.logger.warning("TestCoverage Agent did not generate any tests.")
        else:
            workflow.logger.info(f"TestCoverage terminé – {len(generated_tests)} tests générés")

        # Étape 4 : QA Activity
        qa_result: Dict = await workflow.execute_activity(
            "qa_activity",
            {"specification": spec_part, "project_name": project_name}, # Input for QA agent
            start_to_close_timeout=timedelta(minutes=20),
            retry_policy=common_retry_policy,
        )
        generated_e2e_tests = qa_result.get("e2e_tests", {})
        if not generated_e2e_tests:
            workflow.logger.warning("QA Agent did not generate any E2E tests.")
        else:
            workflow.logger.info(f"QA terminé – {len(generated_e2e_tests)} E2E tests générés")


        # Étape 5 : GitHub Activity
        all_files = dev_result.get("files", {})
        all_files.update(generated_tests)
        all_files.update(generated_e2e_tests) # Include E2E tests for GitHub

        github_input = {
            "files": all_files,
            "project_name": project_name,
        }
        github_result: str = await workflow.execute_activity(
            "github_activity",
            github_input,
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=common_retry_policy,
        )
        workflow.logger.info("GitHub terminé")

        return f"Workflow terminé avec succès. GitHub PR: {github_result}"