from temporalio import activity
from temporalio.exceptions import ApplicationError
import sys
import os
from typing import Dict, Any

# Validation contrats
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from scripts.validate_contracts import validate_input, validate_output


@activity.defn(name="dev_test_activity")
async def dev_test_activity(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Activity qui exécute l'agent Dev + Test fusionné.
    """
    project_name = input_data.get("project_name", "projet-sans-nom")
    activity.logger.info(f"DevTest démarré → Projet: {project_name}")

    # ── 1. Validation entrée ───────────────────────────────────────────────
    validate_input("dev_agent", input_data)          # ou "test_agent" si contrat séparé

    # ── 2. Import différé de l'agent ──────────────────────────────────────
    try:
        from agents.dev_test_agent import dev_test_agent
    except ImportError as ie:
        activity.logger.error(f"Échec import dev_test_agent : {ie}")
        raise ApplicationError("IMPORT_FAILURE", f"Impossible d'importer dev_test_agent: {ie}")

    # ── 3. Exécution ──────────────────────────────────────────────────────
    try:
        # Appel synchrone (pas d'await si c'est une fonction sync)
        result = dev_test_agent(input_data)

        if not isinstance(result, dict):
            raise ValueError(f"dev_test_agent a retourné {type(result)} au lieu d'un dict")

        # ── 4. Validation sortie ──────────────────────────────────────────
        validate_output("dev_agent", result)         # ou "test_agent" si séparé

        metadata = result.get("metadata", {})
        activity.logger.info(
            f"DevTest terminé → {metadata.get('total_files', 0)} fichiers | "
            f"Success: {result.get('success', False)}"
        )

        return result

    except Exception as e:
        activity.logger.error(f"Échec DevTest : {str(e)}", exc_info=True)
        raise ApplicationError(
            "DEV_TEST_EXECUTION_FAILED",
            f"Erreur dans dev_test_activity : {str(e)}"
        )