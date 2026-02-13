from temporalio import activity
from temporalio.exceptions import ApplicationError
import sys
import os
import json
from typing import Dict, Any

# Validation contrats
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from scripts.validate_contracts import validate_input, validate_output


@activity.defn(name="qa_activity")
async def qa_activity(input_data: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    """
    Exécute le QA Agent pour générer des tests E2E (Playwright/Jest).
    Retourne un dictionnaire {chemin_fichier: contenu_test}
    """
    # 1. Validation entrée
    validate_input("qa_agent", input_data)

    project_name = input_data.get("project_name", "projet-sans-nom")
    spec_summary = input_data.get("specification_summary", "Application SaaS générique")

    activity.logger.info(f"QA activity démarrée → Projet: {project_name}")

    # 2. Imports différés
    try:
        from agents.qa import create_qa_agent
        from langchain_core.messages import HumanMessage
    except ImportError as ie:
        raise ApplicationError("IMPORT_FAILURE", f"Échec import QA agent: {ie}")

    # 3. Préparation prompt riche
    prompt = f"""
Tu es un expert QA E2E pour applications SaaS Next.js.
Génère des tests Playwright complets et réalistes pour le projet suivant :

Nom projet : {project_name}
Description : {spec_summary[:500]}...

Objectifs des tests :
- Couvrir login / signup via Clerk
- CRUD principal (ex: tâches si gestion de tâches)
- Navigation et UI responsive
- Gestion erreurs 401/403/404
- Tests asynchrones avec waitFor

Retourne uniquement un dictionnaire JSON :
{{
  "tests/e2e/login.spec.ts": "code complet du test",
  "tests/e2e/tasks.spec.ts": "...",
  ...
}}
"""

    try:
        qa_agent = create_qa_agent()
        initial_message = HumanMessage(content=prompt)

        final_state = await qa_agent.ainvoke({"messages": [initial_message]})

        # Extraction du dernier message (supposé être le JSON ou le code)
        last_msg = final_state.get("messages", [])[-1]
        if not hasattr(last_msg, "content"):
            raise ValueError("Pas de contenu dans le dernier message du QA agent")

        raw_output = last_msg.content

        # On suppose que l'agent retourne un dict JSON stringifié ou direct
        if isinstance(raw_output, str):
            try:
                e2e_tests = json.loads(raw_output)
            except json.JSONDecodeError:
                # Fallback : on considère que c'est un seul fichier
                e2e_tests = {"tests/e2e/generated_e2e.spec.ts": raw_output}
        elif isinstance(raw_output, dict):
            e2e_tests = raw_output
        else:
            raise ValueError(f"Format inattendu retourné par QA agent: {type(raw_output)}")

        # 4. Validation sortie stricte
        output = {"e2e_tests": e2e_tests}
        validate_output("qa_agent", output)

        activity.logger.info(f"QA terminé → {len(e2e_tests)} fichiers de tests générés")
        return output

    except Exception as e:
        activity.logger.error(f"Échec QA activity: {str(e)}", exc_info=True)
        raise ApplicationError("QA_EXECUTION_FAILED", str(e))