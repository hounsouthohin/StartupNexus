# workflows/activities/dev_test_activity.py
from temporalio import activity
from typing import Dict, Any

@activity.defn
async def dev_test_activity(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Activity Temporal qui exécute DevTestAgent fusionné (Dev + Test).
    """
    from agents.dev_test_agent import dev_test_agent

    project_name = input_data.get('project_name', 'projet-inconnu')
    activity.logger.info(f"DevTestActivity démarré - Projet: {project_name}")
    print(f"[DEVTEST ACTIVITY] Input reçu : {input_data}")

    try:
        # Appel synchrone → PAS d'await ici
        result = dev_test_agent(input_data)

        if not isinstance(result, dict):
            raise ValueError(f"dev_test_agent a retourné un type inattendu : {type(result)}")

        print(f"[DEVTEST ACTIVITY] Résultat brut : {result}")
        metadata = result.get('metadata', {})
        activity.logger.info(
            f"DevTestActivity terminé - "
            f"{metadata.get('total_files', 0)} fichiers générés, "
            f"Success: {result.get('success', False)}"
        )
        return result

    except Exception as e:
        print(f"[DEVTEST ACTIVITY] CRASH : {str(e)}")
        activity.logger.error(f"DevTestActivity échoué : {str(e)}", exc_info=True)  # ← stacktrace complet
        raise  # Laisse Temporal gérer le retry