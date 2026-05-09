"""
utils/run_report.py — Artefact JSON par run (Phase 0).

Écrit un fichier run_report_{run_id}.json dans /app/logs/metrics/run_reports/
(bind-mounté côté host via ./logs:/app/logs).

Critère Phase 0 : 100% des runs ont un report écrit, succès ET échec.
Non bloquant : si l'écriture échoue, le run continue.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_LOG_ROOT = os.getenv("FACTORY_LOG_DIR", "/app/logs")
_REPORT_DIR = os.path.join(_LOG_ROOT, "metrics", "run_reports")


def write_run_report(
    run_id: str,
    workflow_id: str,
    project_name: str,
    run_metric: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None,
    duration_seconds: Optional[float] = None,
) -> Optional[str]:
    """
    Écrit le run_report JSON pour un run terminé (succès ou échec).

    Args:
        run_id: Identifiant unique du run
        workflow_id: Identifiant Temporal du workflow
        project_name: Nom du projet
        run_metric: Dict run_metric complet depuis dev_test_activity
        metadata: Dict metadata depuis dev_test_activity (optionnel)
        duration_seconds: Durée du run en secondes (optionnel)

    Returns:
        Chemin du fichier écrit, ou None si échec.
    """
    try:
        os.makedirs(_REPORT_DIR, exist_ok=True)
        report_path = os.path.join(_REPORT_DIR, f"run_report_{run_id}.json")

        metadata = metadata or {}
        report = {
            "run_id": run_id,
            "workflow_id": workflow_id,
            "project_name": project_name,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": duration_seconds,
            # ── Build ──────────────────────────────────────────────────────
            "build_success": bool(run_metric.get("build_success", False)),
            "build_attempted": bool(run_metric.get("build_attempted", False)),
            "build_attempts": int(run_metric.get("build_attempts", 0)),
            "final_message": str(run_metric.get("final_message", "") or ""),
            "root_cause_category": str(run_metric.get("root_cause_category", "unknown") or "unknown"),
            "last_build_error": str(run_metric.get("last_build_error", "") or ""),
            # ── Spec ───────────────────────────────────────────────────────
            "spec_coverage": float(run_metric.get("spec_coverage", 0.0)),
            "requirements_met": int(run_metric.get("requirements_met", 0)),
            "requirements_unmet": int(run_metric.get("requirements_unmet", 0)),
            "requirements_unknown": int(run_metric.get("requirements_unknown", 0)),
            "requirements_total": int(run_metric.get("requirements_total", 0)),
            "requirements_unmet_list": run_metric.get("requirements_unmet_list", []),
            "requirements_unknown_list": run_metric.get("requirements_unknown_list", []),
            # ── Fichiers ───────────────────────────────────────────────────
            "files_generated": int(metadata.get("total_files", run_metric.get("files_count", 0))),
            "dev_files_count": int(metadata.get("dev_files_count", run_metric.get("dev_files_count", 0))),
            # ── Prisma validate (champs Codex P0-X1) ───────────────────────
            "prisma_validate": run_metric.get("prisma_validate", {
                "enabled": False, "cli_found": False, "ran": False, "ok": None,
            }),
            # ── TypeScript (champs Codex P0-X2) ────────────────────────────
            "tsc_ran": bool(run_metric.get("tsc_ran_by_activity", False)),
            "tsc_ok": run_metric.get("tsc_ok_by_activity", None),
            "tsc_errors_count": int(run_metric.get("tsc_errors_count_by_activity", 0)),
            "tsc_skipped": bool(run_metric.get("tsc_skipped_by_activity", True)),
            # ── Cohérence (P0-C2) ───────────────────────────────────────────
            "contradiction_flags": run_metric.get("contradiction_flags", []),
            # ── Qualité ────────────────────────────────────────────────────
            "semantic_violations_count": len(run_metric.get("semantic_violations", [])),
            "quality_violations_count": int(run_metric.get("quality_violations_count", 0)),
            "quality_violations": run_metric.get("quality_violations", []),
            "tests_passed": bool(run_metric.get("tests_passed", False)),
            "user_flows_total": int(metadata.get("user_flows_total", 0)),
            "user_flows_covered": int(metadata.get("user_flows_covered", 0)),
            "user_flows_coverage": float(metadata.get("user_flows_coverage", 0.0)),
            "is_useful_app": bool(metadata.get("is_useful_app", False)),
            "clerk_compliant": bool(run_metric.get("clerk_compliant", False)),
            "error": str(run_metric.get("error", "") or ""),
        }

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"[run_report] écrit → {report_path}")
        return report_path

    except Exception as exc:
        logger.warning(f"[run_report] écriture non bloquante échouée : {exc}")
        return None


def write_run_report_minimal(
    run_id: str,
    workflow_id: str,
    project_name: str,
    error: str = "DevTest not reached",
) -> Optional[str]:
    """
    Fallback minimal écrit depuis le workflow si DevTest n'a pas tourné.
    Contient uniquement les champs disponibles au niveau workflow.
    """
    try:
        os.makedirs(_REPORT_DIR, exist_ok=True)
        report_path = os.path.join(_REPORT_DIR, f"run_report_{run_id}.json")

        report = {
            "run_id": run_id,
            "workflow_id": workflow_id,
            "project_name": project_name,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": None,
            "build_success": False,
            "build_attempted": False,
            "build_attempts": 0,
            "final_message": "WORKFLOW_FAILED_BEFORE_DEVTEST",
            "root_cause_category": "workflow_error",
            "error": error,
            "contradiction_flags": [],
            # Champs absents — non disponibles à ce niveau
            "prisma_validate": {"enabled": False, "cli_found": False, "ran": False, "ok": None},
            "tsc_ran": False,
            "tsc_ok": None,
            "tsc_errors_count": 0,
        }

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"[run_report] fallback minimal écrit → {report_path}")
        return report_path

    except Exception as exc:
        logger.warning(f"[run_report] fallback minimal non bloquant échoué : {exc}")
        return None
