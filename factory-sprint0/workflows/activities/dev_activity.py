from temporalio import activity
from agents.dev import dev_agent

@activity.defn
async def dev_activity(input_data: dict) -> dict:
    """
    Temporal activity to run the Dev Agent.
    Takes a dict with 'spec' and 'mermaid' keys.
    Returns the generated files and the final message from the Dev Agent.
    """
    activity.logger.info("Starting Dev Agent activity...")
    
    spec = input_data.get("spec", "")
    mermaid = input_data.get("mermaid", "")
    
    if not spec or not mermaid:
        raise ValueError("Missing required keys: 'spec' or 'mermaid'")
    
    result = dev_agent(spec, mermaid)
    activity.logger.info("Dev Agent activity completed.")
    return result