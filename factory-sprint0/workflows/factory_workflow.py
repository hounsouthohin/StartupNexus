from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from typing import Dict, Any

# ✅ Bonne pratique : imports des activités (modules lourds) isolés hors sandbox
# workflow.unsafe.imports_passed_through() indique explicitement au sandbox
# que ces modules viennent du monde extérieur et ne sont pas soumis
# aux restrictions de déterminisme — sans désactiver la protection globalement.
with workflow.unsafe.imports_passed_through():
    from workflows.activities.architect_activity import architect_activity
    from workflows.activities.dev_test_activity import dev_test_activity
    from workflows.activities.github_activity import github_activity
    from workflows.activities.qa_activity import qa_activity


@workflow.defn
class SaaSFactoryWorkflow:

    @workflow.run
    async def run(self, input_data: Dict[str, str]) -> str:
        phrase = input_data.get("phrase", "phrase inconnue")
        project_name = input_data.get("project_name", "default-saas-project")
        workflow.logger.info(f"Workflow démarré – phrase: {phrase}, project: {project_name}")

        common_retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=5),
            backoff_coefficient=2.0,
            maximum_attempts=3,
        )

        # Étape 1 : Architect Activity
        architect_result: Dict = await workflow.execute_activity(
            architect_activity,
            input_data,
            start_to_close_timeout=timedelta(seconds=300),
            retry_policy=common_retry_policy,
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
        return f"Workflow terminé avec succès. GitHub PR: {github_result}"