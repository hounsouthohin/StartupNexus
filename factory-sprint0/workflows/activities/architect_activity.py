# workflows/activities/architect_activity.py
from temporalio import activity
import os
from dotenv import load_dotenv
import re
import json

@activity.defn
async def architect_activity(input_data: dict) -> dict:
    # Imports moved inside the activity function
    from agents.architect import create_architect_agent
    from langchain_core.messages import HumanMessage
    
    load_dotenv(override=True)

    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY manquante dans les variables d'environnement")

    phrase = input_data.get("phrase", "").strip()
    if not phrase:
        raise ValueError("Le champ 'phrase' est requis et ne peut pas être vide")

    activity.logger.info(f"Agent Architecte démarré – Requête : {phrase}")

    try:
        architect_agent = create_architect_agent()
    except Exception as e:
        activity.logger.error(f"Échec création du graph Architecte : {str(e)}")
        raise

    initial_state = {
        "messages": [HumanMessage(content=phrase)],
        "rag_context": "",
        "plan": {},
        "specification": "",
        "mermaid_diagram": "",
    }

    try:
        final_state = await architect_agent.ainvoke(initial_state)
        architect_output = final_state.get("architect_output")

        # The agent now returns a validated Pydantic object.
        # If the agent failed, it will have raised an exception internally.
        if architect_output and hasattr(architect_output, 'specification') and hasattr(architect_output, 'mermaid_diagram'):
            activity.logger.info("Extraction réussie : Pydantic model fourni par l'agent.")
            return {
                'specification': architect_output.specification,
                'mermaid_diagram': architect_output.mermaid_diagram
            }
        else:
            # This case should ideally not be reached if the agent is robust.
            activity.logger.error("L'agent n'a pas retourné l'objet Pydantic attendu.")
            raise ValueError("Architect Agent did not return the expected Pydantic output.")

    except Exception as e:
        activity.logger.error(f"Erreur lors de l'exécution de l'activité Architecte : {str(e)}")
        raise