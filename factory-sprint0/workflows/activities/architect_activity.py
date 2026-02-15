from temporalio import activity
from temporalio.exceptions import ApplicationError
import os
import sys
from dotenv import load_dotenv
from typing import Dict

# Ajout des validations de contrat (doit être au niveau module)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from scripts.validate_contracts import validate_input, validate_output

FORBIDDEN_PATTERNS = [
    "bcrypt",
    "jwt",
    "jsonwebtoken",
    "password_hash",
    "next-auth",
    "nextauth",
    "/api/auth/register",
    "/api/auth/login",
    "password field",
]


def _validate_clerk_compliance(spec: str, mermaid: str) -> list:
    violations = []
    content = (spec + " " + mermaid).lower()
    for pattern in FORBIDDEN_PATTERNS:
        if pattern.lower() in content:
            violations.append(pattern)
    return violations


@activity.defn(name="architect_activity")
async def architect_activity(input_data: Dict) -> Dict:
    """
    Activity qui exécute l'Architect Agent (génération de spec + diagramme Mermaid).
    """
    load_dotenv(override=True)

    # Vérification minimale de la clé API (avant même la validation contrat)
    if not os.getenv("OPENAI_API_KEY"):
        raise ApplicationError("MISSING_CONFIGURATION", "OPENAI_API_KEY manquante")

    # ── 1. Validation du contrat d'entrée ────────────────────────────────
    validate_input("architect_agent", input_data)

    phrase = input_data.get("phrase", "").strip()
    project_name = input_data.get("project_name", "projet-sans-nom")

    activity.logger.info(f"Architect démarré → Projet: {project_name} | Phrase: {phrase[:80]}...")

    # ── 2. Imports différés (pour éviter les problèmes de circularité ou de worker startup) ──
    try:
        from agents.architect import create_architect_agent
        from langchain_core.messages import HumanMessage
    except ImportError as import_err:
        activity.logger.error(f"Échec import modules Architect : {import_err}")
        raise ApplicationError("IMPORT_FAILURE", f"Impossible d'importer l'agent Architect: {import_err}")

    # ── 3. Création et exécution de l'agent ───────────────────────────────
    try:
        architect_agent = create_architect_agent()
    except Exception as e:
        activity.logger.error(f"Échec création du graph Architect : {str(e)}", exc_info=True)
        raise ApplicationError("AGENT_INIT_FAILED", f"Impossible de créer l'agent Architect: {str(e)}")

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

        if not architect_output:
            raise ValueError("architect_output manquant dans l'état final")

        # On suppose que l'agent retourne déjà un dict / Pydantic → on extrait
        output_dict = {
            "specification": architect_output.specification
                if hasattr(architect_output, "specification")
                else architect_output.get("specification", ""),
            "mermaid_diagram": architect_output.mermaid_diagram
                if hasattr(architect_output, "mermaid_diagram")
                else architect_output.get("mermaid_diagram", ""),
        }

        violations = _validate_clerk_compliance(
            output_dict.get("specification", ""),
            output_dict.get("mermaid_diagram", ""),
        )
        if violations:
            raise ApplicationError(
                "SPEC_NOT_CLERK_COMPLIANT",
                f"Spec rejetee - patterns interdits detectes : {violations}. "
                f"L'architect doit utiliser Clerk exclusivement."
            )

        # ── 4. Validation stricte du contrat de sortie ───────────────────────
        validate_output("architect_agent", output_dict)

        activity.logger.info(f"Architect terminé → {len(output_dict['specification'])} caractères de spec générés")
        return output_dict

    except Exception as e:
        activity.logger.error(f"Échec exécution Architect : {str(e)}", exc_info=True)
        if isinstance(e, Exception):  # on attrape tout, mais on relance typed
            raise ApplicationError("ARCHITECT_EXECUTION_FAILED", str(e))
        raise
