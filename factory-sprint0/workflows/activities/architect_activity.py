# workflows/activities/architect_activity.py
from temporalio import activity
from agents.architect import create_architect_agent
from langchain_core.messages import HumanMessage
import os
from dotenv import load_dotenv
import re
import json

@activity.defn
async def architect_activity(input_data: dict) -> dict:
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
        "architect_output": {}
    }

    try:
        final_state = await architect_agent.ainvoke(initial_state)
        architect_output = final_state.get("architect_output", {})

        # 1. Primary path: agent returns valid, complete JSON in architect_output
        if isinstance(architect_output, dict) and architect_output.get("specification") and architect_output.get("mermaid_diagram"):
            activity.logger.info("Extraction réussie : JSON structuré fourni par l'agent.")
            return {
                'specification': str(architect_output['specification']),
                'mermaid_diagram': str(architect_output['mermaid_diagram'])
            }

        # 2. Fallback path: Regex extraction from raw agent response
        activity.logger.warning("JSON direct invalide ou manquant. Tentative d'extraction par regex sur la sortie brute.")

        raw_content = ""
        # Find the last message from the AI to parse it
        if final_state.get("messages"):
            for msg in reversed(final_state["messages"]):
                if msg.type == 'ai': # AIMessage from langchain
                    raw_content = msg.content
                    break
        
        if not raw_content:
            activity.logger.error("L'agent n'a retourné aucun contenu brut.")
            raise ValueError("L'agent Architecte n'a retourné aucun contenu.")

        # Try to find a JSON block in the raw content first
        json_match = re.search(r"```json\s*(\{.*?\})\s*```", raw_content, re.DOTALL)
        if json_match:
            try:
                parsed_json = json.loads(json_match.group(1))
                if parsed_json.get("specification") and parsed_json.get("mermaid_diagram"):
                    activity.logger.info("Extraction réussie : JSON trouvé dans un bloc de code.")
                    return {
                        'specification': str(parsed_json['specification']),
                        'mermaid_diagram': str(parsed_json['mermaid_diagram'])
                    }
            except json.JSONDecodeError:
                activity.logger.warning("Bloc JSON trouvé mais invalide. Poursuite avec regex.")

        # Regex for Mermaid diagram
        mermaid_match = re.search(r"```mermaid\s*\n(.*?)\n\s*```", raw_content, re.DOTALL)
        mermaid_diagram = mermaid_match.group(1).strip() if mermaid_match else ""

        # Regex for Specification (assuming it's the text part)
        # We'll take the content, remove the mermaid part and any JSON wrapper
        specification = raw_content
        if mermaid_match:
            specification = specification.replace(mermaid_match.group(0), "").strip()
        
        # Clean up potential markdown code blocks for JSON
        specification = re.sub(r"```json\s*", "", specification).strip()
        specification = re.sub(r"```", "", specification).strip()

        if not specification and not mermaid_diagram:
            activity.logger.error(f"Échec de l'extraction par Regex sur le contenu brut: {raw_content}")
            raise ValueError("Impossible d'extraire la spécification ou le diagramme via Regex.")

        activity.logger.info(f"Extraction par Regex terminée. Spec trouvé: {bool(specification)}, Mermaid trouvé: {bool(mermaid_diagram)}")

        return {
            'specification': specification,
            'mermaid_diagram': mermaid_diagram
        }

    except Exception as e:
        activity.logger.error(f"Erreur lors de l'exécution de l'activité Architecte : {str(e)}")
        raise