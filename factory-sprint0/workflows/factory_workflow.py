from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from typing import Dict

# Logger pour Temporal UI
workflow.logger = workflow.logger

@workflow.defn
class SaaSFactoryWorkflow:
    @workflow.run
    async def run(self, input_data: Dict[str, str]) -> str:
        phrase = input_data.get("phrase", "phrase inconnue")
        project_name = input_data.get("project_name", "default-saas-project")
        workflow.logger.info(f"Workflow démarré – phrase: {phrase}, Project: {project_name}")

        # Politique de retry commune (réutilisée pour Dev & GitHub)
        common_retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=5),
            backoff_coefficient=2.0,
            maximum_attempts=3,
        )

        # Étape 1 : Architect Activity → retourne un dict structuré
        architect_result: Dict = await workflow.execute_activity(
            "architect_activity",
            input_data,
            start_to_close_timeout=timedelta(seconds=300),
            retry_policy=common_retry_policy,
        )

        # Accès direct aux sorties structurées
        spec_part = architect_result.get("specification", "")
        mermaid_part = architect_result.get("mermaid_diagram", "")

        if not spec_part or not mermaid_part:
            workflow.logger.error("Architecte terminé – sortie structurée incomplète.")
            raise ValueError("Architect Agent did not return complete structured output.")

        workflow.logger.info("Architecte terminé – sortie structurée OK")

        # Étape 2 : Dev Activity → on passe un dict
        dev_input = {
            "spec": spec_part,
            "mermaid": mermaid_part,
            "project_name": project_name,
        }
        dev_result: Dict = await workflow.execute_activity(
            "dev_activity",
            dev_input,
            start_to_close_timeout=timedelta(minutes=30),
            retry_policy=common_retry_policy,  # ← corrigé ici
        )

        workflow.logger.info("Dev terminé – code généré")

        # Étape 3 : GitHub Activity
        github_input = {
            "files": dev_result.get("files", {}),
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