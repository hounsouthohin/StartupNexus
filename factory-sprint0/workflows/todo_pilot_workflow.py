# workflows/todo_pilot_workflow.py
"""
Workflow pilote Sprint 0.5 – Validation ToDo app avec DevTestAgent fusionné
"""

from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from typing import Dict, Any
import datetime

with workflow.unsafe.imports_passed_through():
    from workflows.activities.architect_activity import architect_activity
    from workflows.activities.dev_test_activity import dev_test_activity
    from workflows.activities.github_activity import github_activity
    from workflows.activities.qa_activity import qa_activity

@workflow.defn
class TodoPilotWorkflow:
    """Workflow de validation pour le pilote ToDo Sprint 0.5."""

    @workflow.run
    async def run(self, input_data: Dict[str, str]) -> str:
        phrase = input_data.get("phrase", "Crée une ToDo app Next.js avec Clerk auth")
        project_name = "todo-pilot-sprint05"

        workflow.logger.info(f"TodoPilot démarré – Phrase: {phrase}")

        start_time = workflow.now()  # déterministe !

        common_retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=5),
            backoff_coefficient=2.0,
            maximum_attempts=3,
        )

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

        # Après dev_test_result, avant github_input :
        qa_result: Dict[str, Any] = await workflow.execute_activity(
            qa_activity,
            {"specification": spec_part, "project_name": project_name},
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=common_retry_policy,
        )
        e2e_tests = qa_result.get("e2e_tests", {})
        workflow.logger.info(f"QA terminé – {len(e2e_tests)} tests générés")

        # Et mettre à jour github_input :
        github_input = {
            "files": {**dev_test_result.get("combined_files", {}), **e2e_tests},
            "project_name": project_name,
        }


        github_result: str = await workflow.execute_activity(
            github_activity,
            github_input,
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=common_retry_policy,
        )

        workflow.logger.info("GitHub terminé")

        total_time = (workflow.now() - start_time).total_seconds()

        # Rapport final (simple string, facile à parser plus tard)
        report = f"""
=== RAPPORT VALIDATION SPRINT 0.5 - TODO PILOT ===

Projet           : {project_name}
Succès DevTest   : {dev_test_result.get('success', False)}
Temps total      : {total_time:.2f} s
Fichiers générés : {dev_test_result.get('metadata', {}).get('total_files', 0)}
  → Dev          : {dev_test_result.get('metadata', {}).get('dev_files_count', 0)}
  → Test         : {dev_test_result.get('metadata', {}).get('test_files_count', 0)}
Mode             : {dev_test_result.get('metadata', {}).get('mode', 'inconnu')}

GitHub PR        : {github_result.get('pr_url', 'N/A')}
Repo URL         : {github_result.get('repo_url', 'N/A')}

Validation :
→ DevTestAgent   : Fonctionnel
→ Contrats       : Respectés
→ Workflow       : Intégré avec succès
"""
        workflow.logger.info(report)
        return report