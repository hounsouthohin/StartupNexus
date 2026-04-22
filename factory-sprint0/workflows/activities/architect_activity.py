from temporalio import activity
from temporalio.exceptions import ApplicationError
import os
import sys
from dotenv import load_dotenv
from typing import Dict

# Ajout des validations de contrat (doit être au niveau module)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from scripts.validate_contracts import validate_input, validate_output
from agents.llm_provider import validate_llm_env

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

    # Vérification provider-aware (OpenAI ou Ollama selon le mode).
    ok, llm_env_msg = validate_llm_env()
    if not ok:
        raise ApplicationError("MISSING_CONFIGURATION", llm_env_msg)

    # ── 1. Validation du contrat d'entrée (JSON Schema jsonschema) ──────
    try:
        validate_input("architect_agent", input_data)
    except Exception as ve:
        raise ApplicationError("BRIEF_VALIDATION_ERROR", str(ve))

    brief = input_data.get("brief", {})
    if not isinstance(brief, dict):
        brief = {}
    project_name = input_data.get("project_name", "projet-sans-nom")

    activity.logger.info(f"Architect démarré → Projet: {project_name} | Brief: {brief.get('description', '')[:80]}...")

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
        "messages": [HumanMessage(content=brief.get("description", ""))],
        "brief": brief,           # Brief structuré JSON — source de vérité (description, models, pages, routes)
        "rag_context": "",
        "plan": {},
        "specification": "",
        "mermaid_diagram": "",
        "requirements": [],
        "user_flows": [],
        "ir_schema": [],
        "ir_pages": [],
        "ir_routes": [],
        "spec_structured": None,
        "project_spec": {},
        "stack_id": str(input_data.get("stack_id", "nextjs-clerk-prisma")),
        "run_id": run_id,
        "project_name": project_name,
    }

    try:
        from agents.spec_validator import validate_spec_requirements

        final_state = await architect_agent.ainvoke(initial_state)
        architect_output = final_state.get("architect_output")
        if not architect_output:
            raise ValueError("architect_output manquant dans l'état final")

        output_dict = _extract_output_dict(architect_output)

        # ── 4. Récupération du ProjectSpec (Nouvelle Base — Phase 1) ─────────
        # planner_node retourne project_spec dans le state (dict sérialisé de ProjectSpec).
        # Si absent (fallback ancien pipeline), on reconstruit depuis requirements.
        project_spec_dict = final_state.get("project_spec") or {}

        # ── 5. Vérification Clerk compliance sur la description du brief ──────
        # On vérifie la description textuelle — ProjectSpec structuré ne peut pas contenir ces patterns.
        violations = _validate_clerk_compliance(
            brief.get("description", ""),
            "",
            stack_id=str(input_data.get("stack_id", "nextjs-clerk-prisma")),
        )
        if violations:
            raise ApplicationError(
                "SPEC_NOT_CLERK_COMPLIANT",
                f"Brief contient des patterns interdits : {violations}. "
                f"Utiliser Clerk exclusivement."
            )

        # ── 6. Écriture de project_spec.json (artefact officiel) ─────────────
        # Toujours écrit — utilisé par le dev agent (Phase 3) comme source de vérité.
        if project_spec_dict:
            import json as _json
            _workdir = os.getenv("FACTORY_WORKDIR", "/tmp")
            _spec_path = os.path.join(_workdir, f"project_spec_{project_name}.json")
            try:
                os.makedirs(_workdir, exist_ok=True)
                with open(_spec_path, "w", encoding="utf-8") as _f:
                    _json.dump(project_spec_dict, _f, indent=2, ensure_ascii=False)
                activity.logger.info(
                    f"[architect] project_spec.json écrit — "
                    f"fingerprint={project_spec_dict.get('spec_fingerprint', 'n/a')} "
                    f"| {len(project_spec_dict.get('models', []))} modèles "
                    f"| {len(project_spec_dict.get('pages', []))} pages "
                    f"| {len(project_spec_dict.get('routes', []))} routes"
                )
            except Exception as _e:
                activity.logger.warning(f"[architect] project_spec.json non écrit (non bloquant) : {_e}")
        else:
            activity.logger.warning("[architect] project_spec absent du state — ancien pipeline actif ?")

        # ── 7. Construction de l'output final ────────────────────────────────
        requirements = list(output_dict.get("requirements", []) or [])
        if not requirements:
            requirements = list(input_data.get("requirements", []) or [])

        output_dict["requirements"] = requirements
        output_dict["project_spec"] = project_spec_dict
        output_dict["spec_fingerprint"] = project_spec_dict.get("spec_fingerprint", "")

        # ── 7b. Validation ProjectSpec vs brief (déterministe, honnête) ──────
        # Vérifie que chaque modèle déclaré dans le brief est présent dans ProjectSpec.
        # Ne force plus "OK" — le statut réel est propagé au workflow.
        brief_model_names = []
        for m in brief.get("models", []):
            # Extraire le nom : "Task { ... }" → "Task"
            name = str(m).strip().split()[0].rstrip("{").strip()
            if name:
                brief_model_names.append(name.lower())

        spec_model_names = [
            str(m.get("name", "") if isinstance(m, dict) else m).lower()
            for m in project_spec_dict.get("models", [])
        ]

        unmatched = [n for n in brief_model_names if n not in spec_model_names]
        if unmatched:
            spec_validation_status = "DEGRADED"
            activity.logger.warning(
                f"[architect] spec_validation=DEGRADED — "
                f"{len(unmatched)} modèle(s) du brief absent(s) de ProjectSpec : {unmatched}"
            )
        elif not project_spec_dict.get("models"):
            spec_validation_status = "UNKNOWN"
            activity.logger.warning("[architect] spec_validation=UNKNOWN — ProjectSpec sans modèles")
        else:
            spec_validation_status = "OK"

        output_dict["spec_validation_status"] = spec_validation_status
        output_dict["spec_unmatched_requirements"] = unmatched

        # ── 8. Validation contrat de sortie ──────────────────────────────────
        validate_output("architect_agent", output_dict)

        activity.logger.info(
            f"Architect terminé → ProjectSpec | "
            f"{len(requirements)} requirements | "
            f"spec_validation={spec_validation_status} | "
            f"fingerprint={output_dict.get('spec_fingerprint', 'n/a')}"
        )
        return output_dict

    except ApplicationError:
        raise
    except Exception as e:
        activity.logger.error(f"Échec exécution Architect : {str(e)}", exc_info=True)
        raise ApplicationError("ARCHITECT_EXECUTION_FAILED", str(e))
