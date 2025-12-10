from temporalio import activity
from agents.architect import architect_agent  # maintenant OK, Activity = hors sandbox
from langchain_core.messages import HumanMessage

@activity.defn
async def architect_activity(input_data: dict) -> str:
    phrase = input_data.get("phrase", "phrase inconnue")
    activity.logger.info(f"Agent Architecte lancé pour : {phrase}")

    initial_state = {
        "messages": [HumanMessage(content=phrase)],
        "spec_md": "",
        "mermaid": ""
    }

    try:
        result = await architect_agent.ainvoke(initial_state)
        spec = result.get("spec_md", "Aucune spécification générée")
        activity.logger.info("Agent Architecte terminé avec succès")
        return f"ARCHITECTE OK !\n\n{spec}"
    except Exception as e:
        activity.logger.error(f"Erreur Agent Architecte : {str(e)}")
        raise  # Temporal retry si configuré