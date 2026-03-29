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
from utils.run_report import write_run_report as _write_run_report

MAX_ACTIVITY_TSC_FEEDBACK_RETRIES = 1


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
      | prisma_import | prisma_schema_config | prisma_env | prisma_client_api
      | typescript_implicit_any | typescript_property_error | typescript_type_mismatch
      | typescript_missing_import | typescript_error
      | spec_drift | max_iterations | test_failure | workflow_execution_error | unknown
    """
    err = (last_build_error or "").lower()
    # ── Prisma schema errors ──────────────────────────────────────────────────
    if "error code: p1012" in err and "datasource property `url`" in err:
        return "prisma_schema_config"
    if "cannot resolve environment variable: database_url" in err:
        return "prisma_env"
    if "no exported member 'prismaclient'" in err:
        return "prisma_client_api"
    # ── Semantic violations ───────────────────────────────────────────────────
    if semantic_violations:
        return "semantic_violation"
    # ── TypeScript errors (P1-C2) — avant les checks module génériques ────────
    if "ts7006" in err or "ts7031" in err or "implicitly has an 'any' type" in err:
        return "typescript_implicit_any"
    if "ts2339" in err or ("property" in err and "does not exist on type" in err):
        return "typescript_property_error"
    if "ts2345" in err or "is not assignable to parameter of type" in err:
        return "typescript_type_mismatch"
    if "ts2552" in err or "ts2305" in err or (
        "cannot find name" in err and ("nextresponse" in err or "response" in err)
    ):
        return "typescript_missing_import"
    if re.search(r"ts\d{4}", err):
        return "typescript_error"
    # ── Module / import errors ────────────────────────────────────────────────
    if "module not found" in err or "can't resolve" in err or "cannot find module" in err:
        if "lib/prisma" in err or "prisma" in err:
            return "prisma_import"
        return "missing_template"
    if "use client" in err or "hooks can only be used" in err or "useclient" in err:
        return "client_directive"
    if "prisma" in err:
        return "prisma_import"
    # ── Workflow-level failure (aucun build atteint) ───────────────────────────
    if "workflow execution failed" in err:
        return "workflow_execution_error"
    # ── Fallbacks ─────────────────────────────────────────────────────────────
    if spec_validation_status == "DEGRADED":
        return "spec_drift"
    if iterations >= 10:
        return "max_iterations"
    if last_test_error:
        return "test_failure"
    return "unknown"


def _validate_run_metric_consistency(run_metric: dict) -> list:
    """
    Vérifie la cohérence interne d'un run_metric.
    Retourne une liste de contradiction_flags (strings).
    Non bloquant : les flags sont loggés en WARNING et inclus dans run_metric/run_report.

    Règles :
    - INVALIDE : build_success=True ET build_attempted=False
    - INVALIDE : build_success=True ET last_build_error non vide
    - VALIDE   : build_success=True ET tests_passed=False (tests non bloquants)
    - VALIDE   : build_success=True ET build_attempts=0 (build au premier coup)
    - WARNING  : build_success=False ET root_cause_category=unknown (pas de contradiction, signal de qualité)
    """
    flags = []
    build_success = bool(run_metric.get("build_success", False))
    build_attempted = bool(run_metric.get("build_attempted", False))
    last_build_error = str(run_metric.get("last_build_error", "") or "")
    root_cause = str(run_metric.get("root_cause_category", "") or "")

    if build_success and not build_attempted:
        flags.append("CONTRADICTION: build_success=True mais build_attempted=False")

    if build_success and last_build_error:
        flags.append(f"CONTRADICTION: build_success=True mais last_build_error non vide: {last_build_error[:80]}")

    if not build_success and root_cause == "unknown":
        flags.append("WARNING: build_success=False avec root_cause_category=unknown (diagnostic incomplet)")

    return flags


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

    # 3. schema.prisma ne doit pas contenir de champ password (chemin réel : prisma/schema.prisma)
    schema = combined_files.get("prisma/schema.prisma", "") or combined_files.get("schema.prisma", "")
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


def _scan_workdir_files(base_dir: str | None = None) -> dict:
    """
    Lit tous les fichiers source du répertoire projet après exécution du dev agent.
    base_dir: répertoire à scanner (défaut: FACTORY_WORKDIR).
    Retourne un dict {chemin_relatif: contenu} utilisé pour combined_files.
    Ignore node_modules, .next, .git et fichiers binaires.
    """
    workdir = base_dir or os.getenv("FACTORY_WORKDIR", "/app/generated-projects")
    files: dict = {}
    if not os.path.isdir(workdir):
        return files
    EXTENSIONS = {".ts", ".tsx", ".js", ".jsx", ".json", ".prisma", ".css", ".md"}
    NAMED_FILES = {".env.local", ".env", ".gitignore"}
    IGNORE_DIRS = {"node_modules", ".next", ".git", "dist", "build", ".turbo", "snapshots"}
    for root, dirs, filenames in os.walk(workdir):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for filename in filenames:
            _, ext = os.path.splitext(filename)
            if ext in EXTENSIONS or filename in NAMED_FILES:
                abs_path = os.path.join(root, filename)
                rel_path = os.path.relpath(abs_path, workdir).replace("\\", "/")
                try:
                    with open(abs_path, encoding="utf-8", errors="replace") as f:
                        files[rel_path] = f.read()
                except Exception:
                    pass
    return files


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


async def _run_tsc_by_activity(project_workdir: str) -> Dict[str, Any]:
    """
    Exécute un check TypeScript post-run (observabilité activité).

    Important: ce check est indépendant des checks tsc potentiellement exécutés
    par le LLM pendant sa boucle. Il représente l'état final du disque au moment
    de la fin de dev_test_activity.
    """
    details: Dict[str, Any] = {
        "ran": False,
        "skipped": True,
        "ok": None,
        "errors_count": 0,
        "errors": [],
        "error": "",
    }
    if not project_workdir or not os.path.isdir(project_workdir):
        details["error"] = "project_workdir_absent"
        return details
    try:
        from agents.shared_tools import run_tsc_check

        result = await run_tsc_check(project_workdir)
        skipped = bool(result.get("skipped", False))
        raw_errors = result.get("errors", [])
        errors = raw_errors if isinstance(raw_errors, list) else []
        ran = not skipped
        ok = bool(result.get("success", False)) and len(errors) == 0 if ran else None

        details.update(
            {
                "ran": ran,
                "skipped": skipped,
                "ok": ok,
                "errors_count": len(errors),
                "errors": errors[:5],
                "error": "",
            }
        )
        return details
    except Exception as e:
        details["error"] = str(e)[:200]
        return details


def _build_tsc_feedback_prompt(errors: list) -> str:
    """
    Construit un feedback court et actionnable a reinjecter dans le prochain passage Dev.
    """
    if not isinstance(errors, list) or not errors:
        return ""
    lines: List[str] = []
    for item in errors[:5]:
        if not isinstance(item, dict):
            continue
        file_path = str(item.get("file", "") or "")
        line = int(item.get("line", 0) or 0)
        col = int(item.get("col", 0) or 0)
        code = str(item.get("code", "") or "")
        message = str(item.get("message", "") or "")
        loc = file_path if file_path else "<unknown>"
        if line > 0:
            loc += f":{line}:{col if col > 0 else 1}"
        marker = f" [{code}]" if code else ""
        lines.append(f"- {loc}{marker} {message}".strip())
    if not lines:
        return ""
    return (
        "[POST_BUILD_TSC_FEEDBACK]\n"
        "Le check tsc post-mortem a detecte des erreurs TypeScript bloquantes.\n"
        "Corrige d'abord ces erreurs ciblees, puis relance tsc avant le build.\n"
        "Erreurs prioritaires:\n"
        + "\n".join(lines)
    )


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
        "build_attempted": False,
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
        "tsc_ran_by_activity": False,
        "tsc_ok_by_activity": None,
        "tsc_skipped_by_activity": True,
        "tsc_errors_count_by_activity": 0,
        "tsc_error_samples_by_activity": [],
        "prisma_validate": {"cli_found": False, "ran": False, "ok": None, "schema_path": ""},
        "error": "run_not_started",
    }

    # ── 1. Validation entrée ───────────────────────────────────────────────
    # Le workflow peut enrichir le payload avec des champs non contractuels
    # (ex: workflow_id) utilisés uniquement pour l'observabilité.
    # On valide contre le contrat sur une copie normalisée.
    _contract_input = dict(input_data)
    _contract_input.pop("workflow_id", None)
    validate_input("dev_test_agent", _contract_input)

    # ── 3. Exécution ──────────────────────────────────────────────────────
    _activity_start = datetime.now(timezone.utc)
    try:
        # ── Nouvelle Base — dev_graph (LangGraph + outils Python natifs) ────
        from agents.dev_graph import run_dev_agent
        from langgraph.errors import GraphRecursionError
        spec_dict = input_data.get("project_spec") or {}
        try:
            dev_result = await run_dev_agent(
                spec=spec_dict,
                project_name=project_name,
                run_id=run_id,
            )
        except GraphRecursionError as gre:
            activity.logger.warning(
                f"[dev_graph] GraphRecursionError — recursion_limit atteint, "
                f"traité comme BUILD_FAILED : {gre}"
            )
            dev_result = {
                "success": False,
                "build_attempts": 0,
                "last_build_error": f"GraphRecursionError: {str(gre)[:200]}",
                "error_signatures": [],
            }

        success = bool(dev_result.get("success", False))
        build_attempts = int(dev_result.get("build_attempts", 0))
        last_build_error = dev_result.get("last_build_error", "") or ""
        final_message = "BUILD_SUCCESS" if success else "BUILD_FAILED"

        # ── Scan disque → combined_files réels ──────────────────────────────
        # Le workdir est isolé par projet dans FACTORY_WORKDIR/<project_name>
        _factory_workdir = os.getenv("FACTORY_WORKDIR", "/app/generated-projects")
        project_workdir = os.path.join(_factory_workdir, project_name)
        combined_files = _scan_workdir_files(project_workdir)
        activity.logger.info(f"[dev_graph] {len(combined_files)} fichiers lus depuis {project_workdir}")

        # ── Check déterministe TypeScript (observabilité activité) ────────────
        tsc_activity_details = await _run_tsc_by_activity(project_workdir)
        if tsc_activity_details.get("ran"):
            activity.logger.info(
                "[TSC_ACTIVITY] ran=%s ok=%s errors=%s",
                tsc_activity_details.get("ran"),
                tsc_activity_details.get("ok"),
                tsc_activity_details.get("errors_count"),
            )
        elif tsc_activity_details.get("error"):
            activity.logger.warning(
                "[TSC_ACTIVITY] non exécuté: %s",
                tsc_activity_details.get("error"),
            )
        else:
            activity.logger.info("[TSC_ACTIVITY] skipped=true (tsconfig/tsc indisponible)")

        # ── Phase 1 X2: retry unique avec feedback tsc post-mortem ────────────
        tsc_feedback_retry_triggered = False
        tsc_feedback_prompt_preview = ""
        if (
            not success
            and MAX_ACTIVITY_TSC_FEEDBACK_RETRIES > 0
            and bool(tsc_activity_details.get("ran"))
            and not bool(tsc_activity_details.get("ok"))
            and int(tsc_activity_details.get("errors_count", 0) or 0) > 0
        ):
            tsc_feedback_prompt = _build_tsc_feedback_prompt(tsc_activity_details.get("errors", []))
            if tsc_feedback_prompt:
                tsc_feedback_retry_triggered = True
                tsc_feedback_prompt_preview = tsc_feedback_prompt[:400]
                activity.logger.info(
                    "[TSC_FEEDBACK] retry unique active (errors=%s)",
                    tsc_activity_details.get("errors_count", 0),
                )
                retry_result = await run_dev_agent(
                    spec=spec_dict,
                    project_name=project_name,
                    run_id=run_id,
                    extra_feedback=tsc_feedback_prompt,
                )

                first_pass_attempts = build_attempts
                dev_result = retry_result
                success = bool(dev_result.get("success", False))
                build_attempts = first_pass_attempts + int(dev_result.get("build_attempts", 0) or 0)
                last_build_error = dev_result.get("last_build_error", "") or ""
                final_message = "BUILD_SUCCESS" if success else "BUILD_FAILED"

                # Rescan + tsc après le retry pour refléter l'état final réel.
                combined_files = _scan_workdir_files(project_workdir)
                activity.logger.info(
                    f"[dev_graph] retry tsc_feedback -> {len(combined_files)} fichiers lus depuis {project_workdir}"
                )
                tsc_activity_details = await _run_tsc_by_activity(project_workdir)
                if tsc_activity_details.get("ran"):
                    activity.logger.info(
                        "[TSC_ACTIVITY][after_retry] ran=%s ok=%s errors=%s",
                        tsc_activity_details.get("ran"),
                        tsc_activity_details.get("ok"),
                        tsc_activity_details.get("errors_count"),
                    )

        # ── Métriques réelles via spec_coverage ─────────────────────────────
        requirements = input_data.get("requirements", []) or []
        try:
            from agents.spec_coverage import compute_spec_coverage
            cov = compute_spec_coverage(requirements, combined_files)
            spec_coverage = float(cov.get("spec_coverage", 0.0))
            requirements_met = int(cov.get("requirements_met", 0))
            requirements_total = int(cov.get("requirements_total", len(requirements)))
            requirements_unmet = cov.get("unmet", requirements)
        except Exception as cov_err:
            activity.logger.warning(f"[dev_graph] compute_spec_coverage échoué : {cov_err}")
            spec_coverage = 0.0
            requirements_met = 0
            requirements_total = len(requirements)
            requirements_unmet = requirements

        dev_files_count = len(combined_files)
        result = {
            "dev_output": {
                "files": combined_files,
                "final_message": final_message,
                "success": success,
                "metadata": {
                    "build_attempts": build_attempts,
                    "build_attempted": build_attempts > 0,
                    "iterations": build_attempts,
                    "last_build_error": last_build_error[:500],
                    "last_build_error_full": last_build_error,
                    "last_test_error": "",
                    "last_test_error_full": "",
                    "last_failed_command": "",
                    "error_signatures": dev_result.get("error_signatures", []),
                },
            },
            "test_output": {"tests": {}, "success": False},
            "combined_files": combined_files,
            "success": success,
            "metadata": {
                "total_files": dev_files_count,
                "mode": "dev_graph",
                "dev_files_count": dev_files_count,
                "test_files_count": 0,
                "tests_passed": False,
                "spec_coverage": spec_coverage,
                "requirements_met": requirements_met,
                "requirements_total": requirements_total,
                "requirements_unmet": requirements_unmet,
                "requirements_unmet_by_category": {},
                "spec_validation_status": input_data.get("spec_validation_status", "OK"),
                "spec_unmatched_count": len(input_data.get("spec_unmatched_requirements", [])),
                "user_flows_total": 0,
                "user_flows_covered": 0,
                "user_flows_coverage": 0.0,
                "is_useful_app": success and spec_coverage >= 0.8,
                "supervisor_files_reviewed": 0,
                "supervisor_corrections_count": 0,
                "conformity_score": 0.0,
                "security_score": 0.0,
                "architecture_score": 0.0,
                "build_corrections_count": build_attempts,
            },
        }

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
            "build_attempted": bool(_build_attempted),  # normalisé depuis _compute_build_outcome
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
            "tsc_ran_by_activity": bool(tsc_activity_details.get("ran", False)),
            "tsc_ok_by_activity": tsc_activity_details.get("ok", None),
            "tsc_skipped_by_activity": bool(tsc_activity_details.get("skipped", True)),
            "tsc_errors_count_by_activity": int(tsc_activity_details.get("errors_count", 0)),
            "tsc_error_samples_by_activity": tsc_activity_details.get("errors", []),
            "tsc_feedback_retry_triggered": tsc_feedback_retry_triggered,
            "tsc_feedback_prompt_preview": tsc_feedback_prompt_preview,
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
        # ── Cohérence métrique (P0-C2) ────────────────────────────────────
        contradiction_flags = _validate_run_metric_consistency(run_metric)
        run_metric["contradiction_flags"] = contradiction_flags
        if contradiction_flags:
            for flag in contradiction_flags:
                activity.logger.warning(f"[METRIC_CONSISTENCY] {flag}")

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

        # ── run_report.json (P0-C1) ───────────────────────────────────────
        try:
            _write_run_report(
                run_id=run_id,
                workflow_id=str(input_data.get("workflow_id", "")),
                project_name=project_name,
                run_metric=run_metric,
                metadata=dict(metadata),
                duration_seconds=(datetime.now(timezone.utc) - _activity_start).total_seconds(),
            )
        except Exception as _rr_err:
            activity.logger.warning(f"[run_report] non bloquant : {_rr_err}")

        return {**result, "run_metric": run_metric, "semantic_violations": semantic_violations}

    except Exception as e:
        run_metric = {
            "build_success": False,
            "build_attempted": False,
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
            "tsc_ran_by_activity": False,
            "tsc_ok_by_activity": None,
            "tsc_skipped_by_activity": True,
            "tsc_errors_count_by_activity": 0,
            "tsc_error_samples_by_activity": [],
            "prisma_validate": {"cli_found": False, "ran": False, "ok": None, "schema_path": ""},
            "error": f"{type(e).__name__}: {str(e)[:200]}",
        }
        activity.logger.error(f"Échec DevTest : {str(e)}", exc_info=True)

        # run_report minimal même en cas d'exception (P0-C1)
        try:
            run_metric["contradiction_flags"] = []
            _write_run_report(
                run_id=run_id,
                workflow_id=str(input_data.get("workflow_id", "")) if "input_data" in locals() else "",
                project_name=project_name if "project_name" in locals() else "unknown",
                run_metric=run_metric,
            )
        except Exception as _rr_exc:
            pass  # double non-bloquant

        raise ApplicationError(
            "DEV_TEST_EXECUTION_FAILED",
            f"Erreur dans dev_test_activity : {str(e)}"
        )
    finally:
        _log_run_metric(project_name, run_metric, run_id, result=locals().get("result"))
