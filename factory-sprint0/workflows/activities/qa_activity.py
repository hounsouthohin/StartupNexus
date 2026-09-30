"""
workflows/activities/qa_activity.py
─────────────────────────────────────
Temporal Activity — QA post-build : Semgrep (règles de sécurité critiques).

Les tests Jest écrits par gpt-4o ont été retirés le 30 sept 2026 : ils testaient le code
déterministe de nos propres générateurs (le harnais s'en charge) et échouaient en routine
sur des mocks Prisma. Le test du comportement réel viendra des oracles (USINE.md phase 5).
"""
from __future__ import annotations

import os
import subprocess
import sys
from typing import Any, Dict

from temporalio import activity

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

_TESTS_SUMMARY = "Aucun — tests Jest retirés (30 sept 2026), oracles prévus en phase 5"


# ══════════════════════════════════════════════════════════════════════════
# Semgrep
# ══════════════════════════════════════════════════════════════════════════

def _run_semgrep(project_workdir: str) -> Dict[str, Any]:
    rules_path = os.getenv("SEMGREP_RULES_PATH", "")
    if not rules_path or not os.path.exists(rules_path):
        return {"ran": False, "reason": "SEMGREP_RULES_PATH absent"}
    try:
        result = subprocess.run(
            ["semgrep", "--config", rules_path, "--json", "--quiet", "."],
            cwd=project_workdir,
            capture_output=True,
            text=True,
            timeout=60,
        )
        import json
        output = json.loads(result.stdout) if result.stdout.strip() else {}
        findings = output.get("results", [])
        return {
            "ran": True,
            "findings_count": len(findings),
            "findings": [
                {"rule": f.get("check_id", ""), "file": f.get("path", ""), "line": f.get("start", {}).get("line", 0)}
                for f in findings[:10]
            ],
        }
    except Exception as e:
        return {"ran": False, "reason": str(e)}


# ══════════════════════════════════════════════════════════════════════════
# Temporal Activity
# ══════════════════════════════════════════════════════════════════════════

@activity.defn(name="qa_activity")
async def qa_activity(input_data: Dict[str, Any], run_id: str = "") -> Dict[str, Any]:
    """
    QA post-build : Semgrep sur le projet généré.

    Input :
        project_name     : str
        (stack_id, specification, generated_files, user_flows : acceptés, non utilisés)

    Output (clés conservées pour le workflow et le rapport) :
        e2e_tests        : {} (plus de tests générés)
        tests_passed     : False
        tests_summary    : str
        semgrep          : dict
    """
    project_name = input_data.get("project_name", "projet-sans-nom")
    factory_workdir = os.getenv("FACTORY_WORKDIR", "/app/generated-projects")
    project_workdir = os.path.join(factory_workdir, project_name)

    activity.logger.info(f"[qa] Démarrage — projet={project_name} workdir_exists={os.path.isdir(project_workdir)}")

    semgrep_result: Dict[str, Any] = {"ran": False, "reason": "workdir absent"}
    if os.path.isdir(project_workdir):
        semgrep_result = _run_semgrep(project_workdir)
        if semgrep_result.get("ran"):
            activity.logger.info(f"[qa] Semgrep → {semgrep_result.get('findings_count', 0)} finding(s)")

    return {
        "e2e_tests": {},
        "tests_passed": False,
        "tests_summary": _TESTS_SUMMARY,
        "semgrep": semgrep_result,
    }
