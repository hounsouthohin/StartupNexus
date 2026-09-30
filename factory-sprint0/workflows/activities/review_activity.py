"""
workflows/activities/review_activity.py
────────────────────────────────────────
Temporal Activity — Revue post-build.

Délègue à agents.reviewer.run_reviewer : contrôles DÉTERMINISTES sur les fichiers réels
(authentification des pages, données personnelles sur pages publiques). La couche LLM
(gpt-4o + standards Qdrant) a été retirée le 30 sept 2026 : elle notait « COHERENT
100/100 » des apps absurdes — un faux juge est pire qu'aucun juge (USINE.md §5).

Ne s'exécute que si build_status == "BUILD_SUCCESS".
"""
from __future__ import annotations

import os
import sys
from typing import Any, Dict

from temporalio import activity
from temporalio.exceptions import ApplicationError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


@activity.defn(name="review_activity")
async def review_activity(input_data: Dict[str, Any], run_id: str = "") -> Dict[str, Any]:
    """
    Revue post-build.

    Input attendu :
        project_name    : str
        spec            : dict  (ProjectSpec : pages et régime d'authentification)
        generated_files : dict[str, str]
        build_status    : str
        (brief, user_flows, stack_id : acceptés, non utilisés)

    Output :
        review_report   : dict  (verdict, security_score, summary, findings, targeted_fixes)
        review_verdict  : str   ("COHERENT" | "DEGRADED" | "SKIPPED")
        review_skipped  : bool
    """
    project_name = input_data.get("project_name", "projet-sans-nom")
    build_status = str(input_data.get("build_status", ""))

    # Ne pas reviewer si le build a échoué
    if build_status != "BUILD_SUCCESS":
        activity.logger.info(
            f"[review_activity] Revue ignorée — build_status={build_status!r}"
        )
        return {
            "review_report": {},
            "review_verdict": "SKIPPED",
            "review_skipped": True,
        }

    spec = input_data.get("spec", {}) or {}
    generated_files = input_data.get("generated_files", {}) or {}
    activity.logger.info(
        f"[review_activity] Démarrage — projet={project_name} "
        f"fichiers_totaux={len(generated_files)}"
    )

    try:
        from agents.reviewer import run_reviewer
        report = run_reviewer(spec=spec, generated_files=generated_files, run_id=run_id)
    except Exception as e:
        activity.logger.error(f"[review_activity] run_reviewer échoué: {e}", exc_info=True)
        raise ApplicationError("REVIEW_EXECUTION_FAILED", str(e))

    verdict = report.get("verdict", "COHERENT")
    activity.logger.info(
        f"[review_activity] Revue terminée — verdict={verdict} "
        f"sec={report.get('security_score')} findings={len(report.get('findings', []))}"
    )

    return {
        "review_report": report,
        "review_verdict": verdict,
        "review_skipped": False,
    }
