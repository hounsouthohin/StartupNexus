from temporalio import activity
from temporalio.exceptions import ApplicationError
import re
import sys
import os
import shutil
import subprocess
import tempfile
import json
from datetime import datetime, timezone
from typing import Dict, Any, List

# Validation contrats
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from scripts.validate_contracts import validate_input, validate_output


def _classify_root_cause(
    last_build_error: str,
    last_test_error: str,
    semantic_violations: list,
    spec_validation_status: str,
    iterations: int,
) -> str:
    """
    Catégorise la cause racine d'un run en échec ou partiel.
    Retourne une chaîne parmi :
      semantic_violation | missing_template | client_directive
      | prisma_import | spec_drift | max_iterations | test_failure | unknown
    """
    err = (last_build_error or "").lower()
    if "error code: p1012" in err and "datasource property `url`" in err:
        return "prisma_schema_config"
    if "cannot resolve environment variable: database_url" in err:
        return "prisma_env"
    if "no exported member 'prismaclient'" in err:
        return "prisma_client_api"
    if semantic_violations:
        return "semantic_violation"
    if "module not found" in err or "can't resolve" in err or "cannot find module" in err:
        if "lib/prisma" in err or "prisma" in err:
            return "prisma_import"
        return "missing_template"
    if "use client" in err or "hooks can only be used" in err or "useclient" in err:
        return "client_directive"
    if "prisma" in err:
        return "prisma_import"
    if spec_validation_status == "DEGRADED":
        return "spec_drift"
    if iterations >= 10:
        return "max_iterations"
    if last_test_error:
        return "test_failure"
    return "unknown"


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


def _find_schema_in_combined_files(combined_files: dict) -> tuple[str, str]:
    """
    Retourne (schema_path, schema_content) depuis combined_files.
    Tolère les variantes de clés legacy et App Router.
    """
    preferred = ("prisma/schema.prisma", "schema.prisma")
    for key in preferred:
        if key in combined_files:
            return key, str(combined_files.get(key, ""))
    for key, content in (combined_files or {}).items():
        norm = str(key).replace("\\", "/").lower()
        if norm.endswith("schema.prisma"):
            return str(key), str(content)
    return "", ""


def _run_prisma_validate(combined_files: dict) -> tuple[list[str], dict]:
    """
    Exécute `prisma validate` sur un schema généré.

    Comportement:
    - Si pas de schema: skip (pas de violation).
    - Si Prisma CLI absente:
        - mode non bloquant par défaut (warning de qualité)
        - mode bloquant si PRISMA_VALIDATE_ENFORCE=1 (violation)
    - Si validate échoue: violation.
    """
    violations: list[str] = []
    details: dict[str, Any] = {
        "enabled": os.getenv("PRISMA_VALIDATE_ENABLED", "1") == "1",
        "enforced": os.getenv("PRISMA_VALIDATE_ENFORCE", "0") == "1",
        "schema_path": "",
        "cli_found": False,
        "ran": False,
        "ok": None,
        "stdout": "",
        "stderr": "",
    }

    if not details["enabled"]:
        return violations, details

    schema_path, schema_content = _find_schema_in_combined_files(combined_files)
    details["schema_path"] = schema_path
    if not schema_path or not schema_content.strip():
        return violations, details

    prisma_bin = shutil.which("prisma")
    details["cli_found"] = bool(prisma_bin)
    if not prisma_bin:
        msg = "PRISMA_VALIDATE_UNAVAILABLE: prisma CLI introuvable dans le runtime"
        if details["enforced"]:
            violations.append(msg)
        return violations, details

    try:
        with tempfile.TemporaryDirectory(prefix="prisma_validate_") as tmpdir:
            schema_disk_path = os.path.join(tmpdir, "prisma", "schema.prisma")
            os.makedirs(os.path.dirname(schema_disk_path), exist_ok=True)
            with open(schema_disk_path, "w", encoding="utf-8") as f:
                f.write(schema_content)

            details["ran"] = True
            result = subprocess.run(
                [prisma_bin, "validate", "--schema", schema_disk_path],
                capture_output=True,
                text=True,
                timeout=30,
            )
            details["stdout"] = (result.stdout or "")[:1200]
            details["stderr"] = (result.stderr or "")[:1200]
            details["ok"] = result.returncode == 0
            if result.returncode != 0:
                violations.append(
                    "PRISMA_VALIDATE_FAILED: schema invalide selon prisma validate"
                )
    except Exception as e:
        details["ok"] = False
        details["stderr"] = str(e)[:1200]
        if details["enforced"]:
            violations.append(f"PRISMA_VALIDATE_ERROR: {str(e)[:200]}")

    return violations, details


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
                extra["spec_validation_status"] = meta.get("spec_validation_status", "OK")
                extra["spec_unmatched_count"] = meta.get("spec_unmatched_count", 0)
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
        extra["root_cause_category"] = payload.get("root_cause_category", "unknown")
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


def _append_guard_rule_metrics(run_id: str, dev_meta: dict, run_metric: dict, stack_id: str) -> None:
    """
    Persist des signaux de qualité par règle de guard pour suivi precision/recall.
    Ce logger est additif et non-bloquant.
    """
    try:
        log_root = os.getenv("FACTORY_LOG_DIR", "/app/logs")
        metrics_dir = os.path.join(log_root, "metrics")
        os.makedirs(metrics_dir, exist_ok=True)
        path = os.path.join(metrics_dir, "guard_rule_events.jsonl")

        guard_warning_hits = dev_meta.get("guard_warning_hits", {})
        if not isinstance(guard_warning_hits, dict):
            guard_warning_hits = {}

        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "run_id": run_id,
            "stack_id": stack_id,
            "blocking_guard_id": str(dev_meta.get("blocking_guard_id", "") or ""),
            "gate_source": str(dev_meta.get("gate_source", "") or ""),
            "guard_warning_hits": guard_warning_hits,
            "guard_warning_count": int(dev_meta.get("guard_warning_count", 0) or 0),
            "build_success": bool(run_metric.get("build_success", False)),
            "build_attempted": bool(run_metric.get("build_attempted", False)),
            "root_cause_category": str(run_metric.get("root_cause_category", "unknown")),
            # Proxies exploitables offline pour précision/rappel
            "precision_proxy_tp": bool(
                str(dev_meta.get("blocking_guard_id", "") or "")
                and not bool(run_metric.get("build_success", False))
            ),
            "precision_proxy_fp": bool(
                str(dev_meta.get("blocking_guard_id", "") or "")
                and bool(run_metric.get("build_success", False))
            ),
        }
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception as e:
        activity.logger.warning(f"guard_rule_metrics logging failed (non-bloquant): {e}")


def _compute_build_outcome(result_success: bool, final_message: str, dev_meta: Dict[str, Any]) -> tuple[bool, int, bool]:
    """
    Calcule un triplet cohérent (build_success, build_attempts, build_attempted).
    Règle importante: BUILD_SUCCESS est autoritaire même si build_attempts est mal remonté (0).
    """
    build_attempted = bool(dev_meta.get("build_attempted", False))
    build_attempts = int(dev_meta.get("build_attempts", 0) or 0)
    if final_message == "BUILD_SUCCESS":
        return True, (build_attempts if build_attempts > 0 else (1 if build_attempted else 0)), build_attempted
    if bool(result_success) and (build_attempted or build_attempts > 0):
        return True, (build_attempts if build_attempts > 0 else 1), build_attempted
    return False, build_attempts, build_attempted


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
        prisma_violations, prisma_validate_details = _run_prisma_validate(combined_files)
        if prisma_violations:
            semantic_violations.extend(prisma_violations)
        if prisma_validate_details.get("ran"):
            activity.logger.info(
                "[PRISMA_VALIDATE] ran=%s ok=%s schema=%s",
                prisma_validate_details.get("ran"),
                prisma_validate_details.get("ok"),
                prisma_validate_details.get("schema_path", ""),
            )
        elif prisma_validate_details.get("enabled") and prisma_validate_details.get("schema_path"):
            if prisma_validate_details.get("cli_found"):
                activity.logger.warning("[PRISMA_VALIDATE] non exécuté malgré CLI présente")
            else:
                activity.logger.warning(
                    "[PRISMA_VALIDATE] CLI absente (enforce=%s) — voir Dockerfile/runtime",
                    prisma_validate_details.get("enforced"),
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
        gate_source = str(dev_meta.get("gate_source", "") or "")
        blocking_guard_id = str(dev_meta.get("blocking_guard_id", "") or "")
        gate_message = str(dev_meta.get("gate_message", "") or "")
        missing_required_files = dev_meta.get("missing_required_files", [])
        if not isinstance(missing_required_files, list):
            missing_required_files = []
        last_build_error = str(dev_meta.get("last_build_error", "") or "")[:200]
        last_build_error_full = str(dev_meta.get("last_build_error_full", "") or "")
        last_test_error = str(dev_meta.get("last_test_error", "") or "")[:200]
        last_test_error_full = str(dev_meta.get("last_test_error_full", "") or "")
        last_failed_command = str(dev_meta.get("last_failed_command", "") or "")
        build_success, build_attempts, _build_attempted = _compute_build_outcome(
            bool(result.get("success", False)),
            final_message,
            dev_meta,
        )

        # Capture explicite de la cause d'echec métier si pas d'exception levée.
        # T005 — préfixe cohérent avec l'état réel : pas de "BuildFailed" si build non tenté.
        _GATE_STATUSES = {"NOT_BUILT_BY_GATE", "MAX_ITER_REACHED"}
        runtime_error = None
        if not build_success:
            if last_build_error:
                runtime_error = f"BuildFailed: {last_build_error}"
            elif last_test_error:
                runtime_error = f"TestsFailed: {last_test_error}"
            elif final_message in _GATE_STATUSES or not _build_attempted:
                # Gate a bloqué ou build non tenté — pas un BuildFailed
                runtime_error = f"GateBlocked: {final_message}" if final_message else "GateBlocked: build not attempted"
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
            "build_attempts": build_attempts,
            "iterations": int(dev_meta.get("iterations", 0)),
            "spec_coverage": float(metadata.get("spec_coverage", 0.0)),
            "requirements_met": int(metadata.get("requirements_met", 0)),
            "requirements_total": int(metadata.get("requirements_total", 0)),
            "requirements_unmet": metadata.get("requirements_unmet", []),
            "tests_passed": bool(metadata.get("tests_passed", False)),
            "final_message": final_message,
            "gate_source": gate_source,
            "blocking_guard_id": blocking_guard_id,
            "gate_message": gate_message,
            "missing_required_files": missing_required_files,
            "last_build_error": last_build_error,
            "last_build_error_full": last_build_error_full,
            "last_test_error": last_test_error,
            "last_test_error_full": last_test_error_full,
            "last_failed_command": last_failed_command,
            "semantic_violations": semantic_violations,
            "prisma_validate": prisma_validate_details,
            "error": runtime_error,
            "root_cause_category": _classify_root_cause(
                last_build_error=last_build_error,
                last_test_error=last_test_error,
                semantic_violations=semantic_violations,
                spec_validation_status=str(result.get("metadata", {}).get("spec_validation_status", "OK")),
                iterations=int(dev_meta.get("iterations", 0)),
            ),
        }
        activity.logger.info(
            f"DevTest terminé → {metadata.get('total_files', 0)} fichiers | "
            f"Success: {result.get('success', False)} | "
            f"Violations: {len(semantic_violations)}"
        )
        _append_guard_rule_metrics(
            run_id=run_id,
            dev_meta=dev_meta,
            run_metric=run_metric,
            stack_id=str(input_data.get("stack_id", "nextjs-clerk-prisma")),
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
