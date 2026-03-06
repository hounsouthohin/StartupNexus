from temporalio import activity
from temporalio.exceptions import ApplicationError
import re
import sys
import os
from typing import Dict, Any, List

# Validation contrats
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from scripts.validate_contracts import validate_input, validate_output


def _persist_snapshot(project_name: str, run_id: str, files: dict) -> None:
    """
    Sauvegarde un snapshot JSON des fichiers générés avant le push GitHub.
    Non-bloquant : un échec de persistance ne doit pas interrompre le pipeline.
    """
    try:
        import json
        # Snapshots dans FACTORY_WORKDIR/snapshots (volume Docker) ou fallback local
        workdir = os.getenv("FACTORY_WORKDIR", os.path.join(os.path.dirname(__file__), '../..'))
        snapshot_dir = os.path.join(workdir, 'snapshots')
        os.makedirs(snapshot_dir, exist_ok=True)
        snap_name = f"{project_name}_{run_id[:8]}.json"
        snap_path = os.path.normpath(os.path.join(snapshot_dir, snap_name))
        with open(snap_path, "w", encoding="utf-8") as f:
            json.dump(
                {"project_name": project_name, "run_id": run_id, "files": files},
                f, ensure_ascii=False, indent=2,
            )
        activity.logger.info(f"Snapshot persisté → {snap_path}")
    except Exception as e:
        activity.logger.warning(f"Snapshot persistence failed (non-bloquant): {e}")


def _check_semantic_invariants(combined_files: dict, stack_id: str = "nextjs-clerk-prisma") -> List[str]:
    """
    Vérifie les invariants sémantiques sur les fichiers générés.
    Retourne une liste de violations ([] = tout bon).

    Ces assertions remplacent les sanitizers supprimés : au lieu de corriger
    silencieusement une erreur du LLM, on la signale explicitement pour
    forcer la correction des prompts/RAG à la source.
    """
    violations = []

    # 0. package.json doit exister (ENOENT guard)
    if "package.json" not in combined_files:
        violations.append("MISSING package.json — dev agent a appelé run_build avant d'écrire les fichiers critiques")

    # 1. app/layout.tsx doit exister et contenir ClerkProvider
    layout = combined_files.get("app/layout.tsx", "")
    if not layout:
        violations.append("MISSING app/layout.tsx")
    elif "ClerkProvider" not in layout:
        violations.append("MISSING ClerkProvider in app/layout.tsx")

    # 2. middleware.ts doit exister
    if "middleware.ts" not in combined_files:
        violations.append("MISSING middleware.ts")

    # 3. schema.prisma ne doit pas contenir de champ password
    schema = combined_files.get("schema.prisma", "")
    if schema and re.search(r'\bpassword\b', schema, re.IGNORECASE):
        violations.append("FORBIDDEN field 'password' detected in schema.prisma")

    # 4. env_validation — regex branchée depuis stack_config (Governance Sprint 4)
    try:
        from agents.stack_config import load_stack_config
        env_cfg = load_stack_config(stack_id).get("env_validation", {})
        required_vars = env_cfg.get("required_vars", [])
        regex_map = env_cfg.get("regex", {})
        env_content = combined_files.get(".env.local", "")
        if required_vars and not env_content:
            violations.append("MISSING .env.local — variables requises non générées")
        elif env_content:
            for var in required_vars:
                if var not in env_content:
                    violations.append(f"MISSING env var {var} in .env.local")
            for var, pattern in regex_map.items():
                for line in env_content.splitlines():
                    if line.startswith(f"{var}="):
                        value = line.split("=", 1)[1].strip()
                        if not re.match(pattern, value):
                            violations.append(
                                f"INVALID env var {var}='{value[:40]}' — "
                                f"attendu: {pattern}"
                            )
                        break
    except Exception:
        pass  # env_validation non bloquant si stack_config inaccessible

    return violations


def _check_clerk_compliant(result: dict) -> bool:
    """
    Vérifie réellement la conformité Clerk au lieu de retourner True.

    Critères:
    - ClerkProvider présent dans le code
    - Middleware Clerk configuré
    - Pas d'auth custom (bcrypt, jwt, password_hash)
    """
    files = result.get("dev_output", {}).get("files", {})
    if not files:
        return False

    all_content = " ".join(str(v) for v in files.values()).lower()

    # Vérifications positives
    has_clerk_provider = "clerkprovider" in all_content
    has_middleware = "clerk" in all_content and "middleware" in all_content

    # Vérifications négatives (custom auth interdit)
    forbidden = ["bcrypt", "jsonwebtoken", "password_hash", "passport"]
    no_custom_auth = not any(term in all_content for term in forbidden)

    return has_clerk_provider and has_middleware and no_custom_auth


def _log_run_metric(project_name: str, payload: Dict[str, Any], run_id: str = "", result: Any = None) -> None:
    try:
        from agents.shared_tools import _write_learner_event
        # Enrichit le payload avec spec_coverage depuis result.metadata (sinon invisible au learner)
        extra: Dict[str, Any] = {}
        if isinstance(result, dict):
            meta = result.get("metadata", {})
            if isinstance(meta, dict):
                extra["spec_coverage"] = meta.get("spec_coverage", 0.0)
                extra["requirements_met"] = meta.get("requirements_met", 0)
                extra["requirements_total"] = meta.get("requirements_total", 0)
                extra["requirements_unmet"] = meta.get("requirements_unmet", [])
        # delivery_status distingue un build fonctionnel complet (SUCCESS)
        # d'un build fonctionnel incomplet (PARTIAL) pour le Learner.
        # Un run PARTIAL ne doit pas être compté comme succès plein dans P001.
        build_success = bool(payload.get("build_success", False))
        spec_coverage = extra.get("spec_coverage", 0.0)
        if not build_success:
            delivery_status = "failed"
        elif spec_coverage >= 0.5:
            delivery_status = "success"
        else:
            delivery_status = "partial"
        extra["delivery_status"] = delivery_status
        _write_learner_event(
            event_type="dev_test_run",
            payload={
                "project_name": project_name,
                "success": build_success,
                **payload,
                **extra,
            },
            run_id=run_id,
        )
    except Exception as log_err:
        activity.logger.warning(f"Impossible de logger dev_test_run vers Learner: {log_err}")


@activity.defn(name="dev_test_activity")
async def dev_test_activity(input_data: Dict[str, Any], run_id: str = "") -> Dict[str, Any]:
    """
    Activity qui exécute l'agent Dev + Test fusionné.
    """
    try:
        from agents.shared_tools import set_run_id, set_stack_id
        set_run_id(run_id)
        set_stack_id(str(input_data.get("stack_id", "nextjs-clerk-prisma")))
    except Exception:
        pass
    input_data["run_id"] = run_id
    project_name = input_data.get("project_name", "projet-sans-nom")
    activity.logger.info(f"DevTest démarré → Projet: {project_name}")
    run_metric: Dict[str, Any] = {
        "build_success": False,
        "files_count": 0,
        "clerk_compliant": False,
        "dev_files_count": 0,
        "build_attempts": 0,
        "iterations": 0,
        "final_message": "",
        "last_build_error": "",
        "last_build_error_full": "",
        "last_test_error": "",
        "last_test_error_full": "",
        "last_failed_command": "",
        "error": "run_not_started",
    }

    # ── 1. Validation entrée ───────────────────────────────────────────────
    validate_input("dev_test_agent", input_data)

    # ── 2. Import différé de l'agent ──────────────────────────────────────
    try:
        from agents.dev_test_agent import dev_test_agent
    except ImportError as ie:
        activity.logger.error(f"Échec import dev_test_agent : {ie}")
        raise ApplicationError("IMPORT_FAILURE", f"Impossible d'importer dev_test_agent: {ie}")

    # ── 3. Exécution ──────────────────────────────────────────────────────
    try:
        # Appel synchrone (pas d'await si c'est une fonction sync)
        result = dev_test_agent(input_data)

        if not isinstance(result, dict):
            raise ValueError(f"dev_test_agent a retourné {type(result)} au lieu d'un dict")

        # ── 4. Validation sortie ──────────────────────────────────────────
        validate_output("dev_test_agent", result)

        # ── 5. Assertions sémantiques ─────────────────────────────────────
        combined_files = result.get("combined_files", {})
        semantic_violations = _check_semantic_invariants(
            combined_files, stack_id=str(input_data.get("stack_id", "nextjs-clerk-prisma"))
        )
        if semantic_violations:
            for v in semantic_violations:
                activity.logger.warning(f"[SEMANTIC_VIOLATION] {v}")

        # ── 6. Persistance locale du snapshot ─────────────────────────────
        _persist_snapshot(project_name, run_id, combined_files)

        metadata = result.get("metadata", {})
        dev_output = result.get("dev_output", {}) if isinstance(result.get("dev_output", {}), dict) else {}
        dev_meta = dev_output.get("metadata", {}) if isinstance(dev_output.get("metadata", {}), dict) else {}
        top_error = result.get("error", {})
        top_error_message = ""
        if isinstance(top_error, dict):
            phase = str(top_error.get("phase", "") or "").strip()
            msg = str(top_error.get("message", "") or "").strip()
            if phase and msg:
                top_error_message = f"{phase}: {msg}"
            elif msg:
                top_error_message = msg
        elif top_error:
            top_error_message = str(top_error)
        final_message = str(dev_output.get("final_message", ""))[:200]
        last_build_error = str(dev_meta.get("last_build_error", "") or "")[:200]
        last_build_error_full = str(dev_meta.get("last_build_error_full", "") or "")
        last_test_error = str(dev_meta.get("last_test_error", "") or "")[:200]
        last_test_error_full = str(dev_meta.get("last_test_error_full", "") or "")
        last_failed_command = str(dev_meta.get("last_failed_command", "") or "")
        build_success = bool(result.get("success", False))

        # Capture explicite de la cause d'echec métier si pas d'exception levée.
        runtime_error = None
        if not build_success:
            if last_build_error:
                runtime_error = f"BuildFailed: {last_build_error}"
            elif last_test_error:
                runtime_error = f"TestsFailed: {last_test_error}"
            elif final_message:
                runtime_error = f"BuildFailed: {final_message}"
            elif top_error_message:
                runtime_error = f"BuildFailed: {top_error_message[:200]}"
            else:
                runtime_error = "BuildFailed: DevTest returned success=False without exception"

        run_metric = {
            "build_success": build_success,
            "build_attempted": bool(dev_meta.get("build_attempted", False)),
            "files_count": int(metadata.get("total_files", 0)),
            "clerk_compliant": _check_clerk_compliant(result),
            "dev_files_count": int(metadata.get("dev_files_count", 0)),
            "build_attempts": int(dev_meta.get("build_attempts", 0)),
            "iterations": int(dev_meta.get("iterations", 0)),
            "final_message": final_message,
            "last_build_error": last_build_error,
            "last_build_error_full": last_build_error_full,
            "last_test_error": last_test_error,
            "last_test_error_full": last_test_error_full,
            "last_failed_command": last_failed_command,
            "semantic_violations": semantic_violations,
            "error": runtime_error,
        }
        activity.logger.info(
            f"DevTest terminé → {metadata.get('total_files', 0)} fichiers | "
            f"Success: {result.get('success', False)} | "
            f"Violations: {len(semantic_violations)}"
        )

        return {**result, "run_metric": run_metric, "semantic_violations": semantic_violations}

    except Exception as e:
        run_metric = {
            "build_success": False,
            "files_count": 0,
            "clerk_compliant": _check_clerk_compliant(result) if "result" in locals() else False,
            "dev_files_count": 0,
            "build_attempts": 0,
            "iterations": 0,
            "final_message": "",
            "last_build_error": "",
            "last_build_error_full": "",
            "last_test_error": "",
            "last_test_error_full": "",
            "last_failed_command": "",
            "error": f"{type(e).__name__}: {str(e)[:200]}",
        }
        activity.logger.error(f"Échec DevTest : {str(e)}", exc_info=True)
        raise ApplicationError(
            "DEV_TEST_EXECUTION_FAILED",
            f"Erreur dans dev_test_activity : {str(e)}"
        )
    finally:
        _log_run_metric(project_name, run_metric, run_id, result=locals().get("result"))
