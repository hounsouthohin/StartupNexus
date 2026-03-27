from temporalio import activity
from temporalio.exceptions import ApplicationError
import os
import sys
from dotenv import load_dotenv
from typing import Dict

# Ajout des validations de contrat (doit être au niveau module)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from scripts.validate_contracts import validate_input, validate_output

def _wait_for_qdrant(timeout_seconds: int = 90) -> None:
    """
    Attend que Qdrant réponde sur /healthz.
    Lève ApplicationError("QDRANT_UNAVAILABLE") si timeout atteint,
    ce qui déclenche le architect_retry_policy (5 tentatives, backoff 15s).
    """
    import time
    import urllib.request
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"{qdrant_url}/healthz", timeout=3)
            return
        except Exception:
            time.sleep(5)
    raise ApplicationError(
        "QDRANT_UNAVAILABLE",
        f"Qdrant non disponible après {timeout_seconds}s à {qdrant_url}"
    )



DEFAULT_FORBIDDEN_PATTERNS = [
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


def _load_forbidden_patterns(stack_id: str) -> list[str]:
    try:
        from agents.stack_config import load_stack_config
        stack_cfg = load_stack_config(stack_id) or {}
        patterns = stack_cfg.get("forbidden_auth_patterns", [])
        if isinstance(patterns, list) and patterns:
            return [str(p) for p in patterns]
    except Exception:
        pass
    return DEFAULT_FORBIDDEN_PATTERNS


def _extract_output_dict(architect_output) -> dict:
    """Extrait output_dict depuis architect_output (Pydantic ou dict)."""
    def _get(obj, attr, default):
        if hasattr(obj, attr):
            return getattr(obj, attr)
        if isinstance(obj, dict):
            return obj.get(attr, default)
        return default

    spec_structured_raw = _get(architect_output, "spec_structured", None)
    if spec_structured_raw and hasattr(spec_structured_raw, "model_dump"):
        spec_structured = spec_structured_raw.model_dump()
    elif spec_structured_raw and hasattr(spec_structured_raw, "dict"):
        spec_structured = spec_structured_raw.dict()
    else:
        spec_structured = spec_structured_raw or {}

    return {
        "specification": _get(architect_output, "specification", ""),
        "mermaid_diagram": _get(architect_output, "mermaid_diagram", ""),
        "requirements": _get(architect_output, "requirements", []) or [],
        "user_flows": _get(architect_output, "user_flows", []) or [],
        "ir_schema": _get(architect_output, "ir_schema", []) or [],
        "ir_pages": _get(architect_output, "ir_pages", []) or [],
        "ir_routes": _get(architect_output, "ir_routes", []) or [],
        "spec_structured": spec_structured,
    }


def _validate_clerk_compliance(spec: str, mermaid: str, stack_id: str = "nextjs-clerk-prisma") -> list:
    forbidden_patterns = _load_forbidden_patterns(stack_id)
    violations = []
    spec = spec or ""
    mermaid = mermaid or ""
    content = f"{spec} {mermaid}".lower()
    for pattern in forbidden_patterns:
        if pattern.lower() in content:
            violations.append(pattern)
    return sorted(set(violations))


@activity.defn(name="architect_activity")
async def architect_activity(input_data: Dict, run_id: str = "") -> Dict:
    """
    Activity qui exécute l'Architect Agent (génération de spec + diagramme Mermaid).
    """
    try:
        from agents.shared_tools import set_run_id, set_stack_id
        set_run_id(run_id)
        stack_id = str(input_data.get("stack_id", "nextjs-clerk-prisma"))
        set_stack_id(stack_id)
    except Exception:
        pass
    input_data["run_id"] = run_id
    load_dotenv()

    # Vérification minimale de la clé API (avant même la validation contrat)
    if not os.getenv("OPENAI_API_KEY"):
        raise ApplicationError("MISSING_CONFIGURATION", "OPENAI_API_KEY manquante")

    # ── 0. Health check Qdrant ────────────────────────────────────────────
    _wait_for_qdrant()

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
        "normalized_brief": "",   # Rempli par brief_normalizer_node
        "parsed_brief": {},       # Rempli par brief_normalizer_node (parser déterministe)
        "rag_context": "",
        "plan": {},
        "specification": "",
        "mermaid_diagram": "",
        "requirements": [],
        "user_flows": [],
        "ir_schema": [],          # IR canonique — Prisma models (rempli par formatter_node)
        "ir_pages": [],           # IR canonique — pages (rempli par formatter_node)
        "ir_routes": [],          # IR canonique — API routes (rempli par formatter_node)
        "spec_structured": None,  # Dual-output P2 (rempli par formatter_node)
        "stack_id": str(input_data.get("stack_id", "nextjs-clerk-prisma")),
        "run_id": run_id,
        "project_name": project_name,  # Injecté dans le planner pour briser le cache OpenAI
    }

    try:
        from agents.spec_validator import validate_spec_requirements

        final_state = await architect_agent.ainvoke(initial_state)
        architect_output = final_state.get("architect_output")
        if not architect_output:
            raise ValueError("architect_output manquant dans l'état final")

        output_dict = _extract_output_dict(architect_output)
        # Figer la cible de validation sur le premier set de requirements.
        # Évite qu'une tentative corrective "réussisse" en modifiant les requirements
        # au lieu de corriger réellement la spec.
        baseline_requirements = list(output_dict.get("requirements", []) or [])
        if not baseline_requirements:
            baseline_requirements = list(input_data.get("requirements", []) or [])

        violations = _validate_clerk_compliance(
            output_dict.get("specification", ""),
            output_dict.get("mermaid_diagram", ""),
            stack_id=str(input_data.get("stack_id", "nextjs-clerk-prisma")),
        )
        if violations:
            raise ApplicationError(
                "SPEC_NOT_CLERK_COMPLIANT",
                f"Spec rejetee - patterns interdits detectes : {violations}. "
                f"L'architect doit utiliser Clerk exclusivement."
            )

        # ── 4. Spec Validator — observation (non bloquant) ───────────────────
        # La correction loop (re-invoke du même pipeline) a été supprimée :
        # elle re-invoquait le même pipeline avec les mêmes biais → résultat identique.
        # La cause racine (requirements en bas du contexte spec_writer) est corrigée en amont
        # dans spec_writer_node (architect.py). DEGRADED ici = signal d'alerte, pas d'échec.
        # Le pipeline continue — le dev_agent travaille avec la spec disponible.
        spec_validation: dict = {"status": "UNKNOWN", "unmatched_requirements": [], "matched_count": 0, "total_mappable": 0}

        try:
            spec_validation = validate_spec_requirements(
                output_dict.get("specification", ""),
                baseline_requirements,
            )
        except Exception as sv_err:
            activity.logger.warning(f"[SpecValidator] Erreur non bloquante : {sv_err}")

        if spec_validation["status"] == "DEGRADED":
            unmatched = spec_validation["unmatched_requirements"]
            activity.logger.critical(
                f"[SpecValidator] DEGRADED — "
                f"{len(unmatched)}/{spec_validation.get('total_mappable', '?')} "
                f"requirement(s) absents : {unmatched} — pipeline continue (non bloquant)"
            )
        else:
            activity.logger.info(
                f"[SpecValidator] OK — "
                f"{spec_validation.get('matched_count', '?')}/{spec_validation.get('total_mappable', '?')} "
                f"requirement(s) vérifiés dans la spec"
            )

        # Garantit la cohérence downstream avec la cible de validation figée.
        output_dict["requirements"] = baseline_requirements
        output_dict["spec_validation_status"] = spec_validation.get("status", "UNKNOWN")
        output_dict["spec_unmatched_requirements"] = spec_validation.get("unmatched_requirements", [])

        # ── 5. Validation stricte du contrat de sortie (après enrichissement) ──
        # Les champs spec_validation_status et spec_unmatched_requirements sont
        # maintenant déclarés dans architect_agent_contract.json et validés ici.
        validate_output("architect_agent", output_dict)

        activity.logger.info(f"Architect terminé → {len(output_dict['specification'])} caractères de spec générés")
        return output_dict

    except ApplicationError:
        raise
    except Exception as e:
        activity.logger.error(f"Échec exécution Architect : {str(e)}", exc_info=True)
        raise ApplicationError("ARCHITECT_EXECUTION_FAILED", str(e))
