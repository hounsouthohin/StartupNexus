from temporalio import activity
from temporalio.exceptions import ApplicationError
import sys
import os
import json
from typing import Dict, Any

# Validation contrats
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from scripts.validate_contracts import validate_input, validate_output


def _looks_like_typescript(content: str) -> bool:
    if not isinstance(content, str):
        return False
    lowered = content.lower()
    has_module_syntax = ("import " in lowered) or ("export " in lowered)
    has_test_semantics = ("test(" in lowered) or ("it(" in lowered) or ("expect(" in lowered)
    return has_module_syntax and has_test_semantics


def _log_run_metric(project_name: str, payload: Dict[str, Any], run_id: str = "") -> None:
    try:
        from agents.shared_tools import _write_learner_event
        _write_learner_event(
            event_type="qa_run",
            payload={"project_name": project_name, "success": bool(payload.get("qa_e2e_coverage", False)), **payload},
            run_id=run_id,
        )
    except Exception as log_err:
        activity.logger.warning(f"Impossible de logger qa_run vers Learner: {log_err}")


@activity.defn(name="qa_activity")
async def qa_activity(input_data: Dict[str, Any], run_id: str = "") -> Dict[str, Dict[str, str]]:
    """
    Exécute le QA Agent pour générer des tests E2E (Playwright/Jest).
    Retourne un dictionnaire {chemin_fichier: contenu_test}
    """
    try:
        from agents.shared_tools import set_run_id, set_stack_id
        set_run_id(run_id)
        set_stack_id(str(input_data.get("stack_id", "nextjs-clerk-prisma")))
    except Exception:
        pass
    input_data["run_id"] = run_id

    # 1. Validation entrée
    validate_input("qa_agent", input_data)

    project_name = input_data.get("project_name", "projet-sans-nom")
    spec_summary = input_data.get("specification", "Application SaaS générique")
    stack_id = str(input_data.get("stack_id", "nextjs-clerk-prisma"))
    try:
        from agents.stack_config import load_stack_config
        stack_cfg = load_stack_config(stack_id) or {}
    except Exception:
        stack_cfg = {}
    qa_rules = stack_cfg.get("prompt_rules", {}).get("qa_rules", []) if isinstance(stack_cfg.get("prompt_rules"), dict) else []
    qa_rules_block = "\n".join(f"- {r}" for r in qa_rules if isinstance(r, str))
    generated_files = input_data.get("generated_files", {}) if isinstance(input_data.get("generated_files"), dict) else {}
    run_metric: Dict[str, Any] = {
        "qa_e2e_coverage": False,
        "generated_tests_count": 0,
        "error": "run_not_started",
    }

    activity.logger.info(f"QA activity démarrée → Projet: {project_name}")

    # 2. Imports différés
    try:
        from agents.qa import create_qa_agent
        from langchain_core.messages import HumanMessage
    except ImportError as ie:
        raise ApplicationError("IMPORT_FAILURE", f"Échec import QA agent: {ie}")

    try:
        qa_agent = create_qa_agent()
        file_hints = "\n".join(list(generated_files.keys())[:30]) if generated_files else "N/A"
        initial_message = HumanMessage(
            content=(
                f"Projet : {project_name}\n"
                f"Specs : {spec_summary[:1200]}\n"
                f"Fichiers générés (aperçu):\n{file_hints}\n"
                f"Règles QA stack:\n{qa_rules_block if qa_rules_block else 'N/A'}\n"
                "Génère des tests E2E TypeScript cohérents avec ces fichiers."
            )
        )

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
                # Fallback strict: accepter uniquement du TypeScript plausible.
                if not _looks_like_typescript(raw_output):
                    raise ValueError(
                        "QA output rejected: fallback raw output is not valid TypeScript-like content "
                        "(expected at least one of: import/export/const)."
                    )
                e2e_tests = {"tests/e2e/generated_e2e.spec.ts": raw_output}
        elif isinstance(raw_output, dict):
            e2e_tests = raw_output
        else:
            raise ValueError(f"Format inattendu retourné par QA agent: {type(raw_output)}")

        # Validation stricte du contenu: chaque fichier doit ressembler à du TypeScript.
        for test_path, test_content in e2e_tests.items():
            if not _looks_like_typescript(test_content):
                raise ValueError(
                    f"QA output rejected for '{test_path}': not valid TypeScript-like content "
                    "(expected at least one of: import/export/const)."
                )

        # 4. Validation sortie stricte
        output = {"e2e_tests": e2e_tests}
        validate_output("qa_agent", output)

        run_metric = {
            "qa_e2e_coverage": len(e2e_tests) > 0,
            "generated_tests_count": len(e2e_tests),
            "error": None,
        }
        activity.logger.info(f"QA terminé → {len(e2e_tests)} fichiers de tests générés")
        return output

    except Exception as e:
        run_metric = {
            "qa_e2e_coverage": False,
            "generated_tests_count": 0,
            "error": str(e),
        }
        activity.logger.error(f"Échec QA activity: {str(e)}", exc_info=True)
        raise ApplicationError("QA_EXECUTION_FAILED", str(e))
    finally:
        _log_run_metric(project_name, run_metric, run_id)
