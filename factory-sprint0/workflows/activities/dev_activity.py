from temporalio import activity
from agents.dev import dev_agent

@activity.defn
async def dev_activity(input_data: dict) -> dict:
    """
    Temporal activity to run the Dev Agent.
    Takes a dict with 'spec', 'mermaid', 'project_name'.
    Returns the generated files and the final message from the Dev Agent.
    """
    activity.logger.info("Starting Dev Agent activity...")

    spec = input_data.get("spec", "")
    mermaid = input_data.get("mermaid", "")
    project_name = input_data.get("project_name", "default-project")

    if not spec or not mermaid:
        raise ValueError("Missing required keys: 'spec' or 'mermaid'")

    try:
        result = dev_agent(spec, mermaid, project_name=project_name)  # Passe project_name si besoin
        if "files" in result:
            activity.logger.info(f"Fichiers générés : {list(result['files'].keys())}")
        activity.logger.info("Dev Agent activity completed.")
        return result
    except Exception as e:
        activity.logger.error(f"Dev Agent failed: {str(e)}")
        raise