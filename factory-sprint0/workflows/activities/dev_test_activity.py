# workflows/activities/dev_test_activity.py
from temporalio import activity
from typing import Dict, Any

@activity.defn
async def dev_test_activity(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Activity Temporal qui exécute DevTestAgent fusionné (Dev + Test).
    Input suit contrat dev_agent_contract.json.
    """
    from agents.dev_test_agent import dev_test_agent

    activity.logger.info(f"DevTestActivity démarré - Projet: {input_data.get('project_name')}")

    try:
        result = dev_test_activity(input_data)  # appel wrapper

        activity.logger.info(
            f"DevTestActivity terminé - "
            f"{result.get('metadata', {}).get('total_files', 0)} fichiers, "
            f"Success: {result.get('success', False)}"
        )
        return result

    except Exception as e:
        activity.logger.error(f"DevTestActivity échoué : {str(e)}")
        raise  # Temporal capture et retry selon policy