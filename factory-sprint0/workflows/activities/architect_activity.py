# workflows/activities/architect_activity.py
# Version finale – Production-ready Temporal Activity (décembre 2025 standards)
from temporalio import activity
from agents.architect import create_architect_agent
from langchain_core.messages import HumanMessage
import os
from dotenv import load_dotenv

@activity.defn
async def architect_activity(input_data: dict) -> str:
    # 1. Chargement env (dev local) – toujours en premier
    load_dotenv(override=True)

    # 2. Vérification clé OpenAI (fail fast)
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY manquante dans les variables d'environnement")

    phrase = input_data.get("phrase", "").strip()
    if not phrase:
        raise ValueError("Le champ 'phrase' est requis et ne peut pas être vide")

    activity.logger.info(f"Agent Architecte démarré – Requête : {phrase}")

    # 3. Création du graph (après vérifs env)
    try:
        architect_agent = create_architect_agent()
    except Exception as e:
        activity.logger.error(f"Échec création du graph Architecte : {str(e)}")
        raise

    initial_state = {
        "messages": [HumanMessage(content=phrase)],
        "rag_context": ""  # Le retrieval_node remplira ça
    }

    try:
        result = await architect_agent.ainvoke(initial_state)
        
        # Extraction sécurisée de la réponse finale
        final_messages = result.get("messages", [])
        if not final_messages:
            raise ValueError("Aucune réponse générée par l'agent Architecte")
        
        final_content = final_messages[-1].content.strip()
        
        activity.logger.info("Agent Architecte terminé avec succès")
        return f"ARCHITECTE OK !\n\n{final_content}"

    except Exception as e:
        activity.logger.error(f"Erreur lors de l'exécution de l'agent Architecte : {str(e)}")
        # On re-raise pour que Temporal gère le retry
        raise