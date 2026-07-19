"""
utils/run_report.py — Artefacts par run.

Deux types :
  - run_report_{run_id}.json  : données machine (logs/metrics/run_reports/)
  - <projet>_<date>.md        : rapport humain lisible (logs/run_reports/) — Sprint 4.8C
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

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


def write_factory_run_report(
    run_context: Dict[str, Any],
    suggestions: List[Dict[str, Any]],
    run_id: str,
) -> Optional[str]:
    """
    Écrit le FactoryRunReport lisible (.md) dans logs/run_reports/<projet>_<date>.md.
    Non bloquant.
    """
    try:
        report_dir = os.path.join(_LOG_ROOT, "run_reports")
        os.makedirs(report_dir, exist_ok=True)

        project_name = run_context.get("project_name", "unknown")
        build_status = run_context.get("build_status", "UNKNOWN")
        activity_results = run_context.get("activity_results", {})
        duration_seconds = run_context.get("duration_seconds")

        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        report_path = os.path.join(report_dir, f"{project_name}_{date_str}.md")

        # ── Build ─────────────────────────────────────────────────────────────
        build_icon = "✅" if build_status in ("BUILD_SUCCESS", "SUCCESS", "PARTIAL") else "❌"
        build_line = f"{build_icon} {build_status}"

        # ── Review ────────────────────────────────────────────────────────────
        review = activity_results.get("review", {})
        if review.get("status") == "COMPLETED":
            verdict = review.get("verdict", "UNKNOWN")
            sec = review.get("security_score", "?")
            coh = review.get("coherence_score", "?")
            findings = review.get("findings_count", 0)
            post = ""
            if review.get("post_correction_verdict"):
                post = f" → post-correction: {review['post_correction_verdict']}"
            review_line = f"{verdict} | sec={sec} | coh={coh} | {findings} finding(s){post}"
        else:
            review_line = f"SKIPPED ({review.get('status', 'N/A')})"

        # ── Correction pass ───────────────────────────────────────────────────
        correction = activity_results.get("correction_pass", {})
        corr_status = correction.get("status", "NOT_RUN")
        if corr_status == "COMPLETED":
            applied = correction.get("applied", False)
            files = correction.get("files_modified", [])
            new_build = correction.get("new_build_status", "?")
            corr_line = f"{'✅' if applied else '⚠'} {len(files)} fichier(s) — new_build: {new_build}"
        elif corr_status == "SKIPPED_NO_FIXABLE_FINDINGS":
            corr_line = "SKIPPED (aucun finding actionnable)"
        else:
            corr_line = f"SKIPPED ({corr_status})"

        # ── Tests / Semgrep ───────────────────────────────────────────────────
        qa = activity_results.get("qa", {})
        if qa.get("status") == "COMPLETED":
            tests_icon = "✓" if qa.get("tests_passed") else "✗"
            tests_count = qa.get("tests_count", 0)
            summary = (qa.get("tests_summary") or "")[:60]
            tests_line = f"{tests_icon} {tests_count} test(s) — {summary}"
            sf = qa.get("semgrep_findings")
            semgrep_line = f"{'✓' if sf == 0 else '⚠'} {sf} finding(s)" if sf is not None else "Non exécuté"
        else:
            tests_line = "Non exécuté"
            semgrep_line = "Non exécuté"

        # ── Duration ──────────────────────────────────────────────────────────
        if duration_seconds:
            mins = int(duration_seconds // 60)
            secs = int(duration_seconds % 60)
            duration_line = f"{mins}min {secs}s"
        else:
            duration_line = "N/A"

        # ── Patterns / suggestions ────────────────────────────────────────────
        patterns_lines: List[str] = []
        if suggestions:
            patterns_lines.append("")
            patterns_lines.append("PATTERNS DÉTECTÉS :")
            for s in suggestions[:10]:
                title = s.get("title", "?") if isinstance(s, dict) else str(s)
                sev = s.get("severity", "") if isinstance(s, dict) else ""
                icon = "🔴" if sev == "high" else "⚠"
                patterns_lines.append(f"  {icon} {title}")
                patterns_lines.append(f"  → Suggestion standard — DÉCISION REQUISE")

        # ── SCÈNE-A : miroir + limites déclarées ──────────────────────────────
        # Placé EN TÊTE : « ce que l'app fait » et surtout « ce que le client a demandé
        # sans que ça atterrisse » comptent plus que n'importe quelle métrique verte.
        mirror_lines: List[str] = []
        _summary = (run_context.get("summary_fr") or "").strip()
        _unsupported = run_context.get("unsupported") or []
        if _summary:
            mirror_lines += ["", "CE QUE L'APP FAIT :", *[f"  {l}" for l in _summary.splitlines() if l.strip()]]
        if _unsupported:
            mirror_lines += ["", f"⚠ NON COUVERT PAR LA FACTORY ({len(_unsupported)}) :"]
            mirror_lines += [f"  ✗ {u}" for u in _unsupported[:10]]
        elif _summary:
            mirror_lines += ["", "✓ Aucune demande du brief laissée de côté."]

        sep = "═" * 50
        content_lines = [
            f"# FactoryRunReport — {project_name} — {date_str}",
            sep,
            *mirror_lines,
            *([sep] if mirror_lines else []),
            f"BUILD        : {build_line}",
            f"REVIEW       : {review_line}",
            f"CORRECTIONS  : {corr_line}",
            f"TESTS        : {tests_line}",
            f"SEMGREP      : {semgrep_line}",
            *patterns_lines,
            "",
            f"RUN_ID       : {run_id}",
            f"DURÉE        : {duration_line}",
        ]

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(content_lines))

        logger.info(f"[factory_run_report] écrit → {report_path}")
        return report_path

    except Exception as exc:
        logger.warning(f"[factory_run_report] écriture non bloquante échouée : {exc}")
        return None
