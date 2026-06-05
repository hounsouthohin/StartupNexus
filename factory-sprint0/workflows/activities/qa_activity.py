"""
workflows/activities/qa_activity.py
─────────────────────────────────────
Temporal Activity — QA Agent (Sprint 4.8B).

Couche 1 — Jest smoke tests :
  gpt-4o génère des tests Zod + services, les exécute via npm test.
  Signal : tests_passed + tests_summary + semgrep_findings.

Couche 2 — E2E visuel (Sprint 4.9) :
  Playwright MCP contre l'URL Vercel réelle.
  Non implémenté ici — nécessite github_activity + déploiement Vercel.
"""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys
from typing import Any, Dict

from temporalio import activity

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

_SUBPROCESS_TIMEOUT = 120


# ══════════════════════════════════════════════════════════════════════════
# Helpers Jest + Semgrep
# ══════════════════════════════════════════════════════════════════════════

def _write_test_files(test_files: Dict[str, str], project_workdir: str) -> list[str]:
    written: list[str] = []
    base = pathlib.Path(project_workdir)
    for rel_path, content in test_files.items():
        abs_path = base / rel_path
        try:
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            abs_path.write_text(content, encoding="utf-8")
            written.append(rel_path)
            activity.logger.info(f"[qa] ✓ Fichier de test écrit : {rel_path}")
        except Exception as e:
            activity.logger.warning(f"[qa] Impossible d'écrire {rel_path}: {e}")
    return written


def _run_jest(project_workdir: str) -> tuple[bool, str]:
    if not os.path.isfile(os.path.join(project_workdir, "package.json")):
        return False, "package.json introuvable — jest non lancé"
    try:
        result = subprocess.run(
            ["npx", "jest", "--passWithNoTests", "--no-coverage", "--forceExit"],
            cwd=project_workdir,
            capture_output=True,
            text=True,
            timeout=_SUBPROCESS_TIMEOUT,
            env={**os.environ, "NODE_ENV": "test", "NEXT_TELEMETRY_DISABLED": "1"},
        )
        combined = (result.stdout + "\n" + result.stderr).strip()
        passed = result.returncode == 0
        summary_lines = [
            line for line in combined.splitlines()
            if any(kw in line for kw in ("Tests:", "Test Suites:", "PASS", "FAIL"))
        ]
        summary = " | ".join(summary_lines[-4:]) if summary_lines else combined[:200]
        return passed, summary
    except subprocess.TimeoutExpired:
        return False, f"jest timeout ({_SUBPROCESS_TIMEOUT}s)"
    except Exception as e:
        return False, f"jest exception: {e}"


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
    QA Activity — Sprint 4.8B.

    Input :
        project_name     : str
        stack_id         : str
        specification    : str
        generated_files  : dict[str, str]
        user_flows       : list  (réservé Sprint 4.9 — Playwright MCP)

    Output :
        e2e_tests        : dict[str, str]
        tests_passed     : bool
        tests_summary    : str
        semgrep          : dict
    """
    try:
        from agents.shared_tools import set_run_id, set_stack_id
        set_run_id(run_id)
        set_stack_id(str(input_data.get("stack_id", "nextjs-clerk-prisma")))
    except Exception:
        pass

    project_name = input_data.get("project_name", "projet-sans-nom")
    stack_id = str(input_data.get("stack_id", "nextjs-clerk-prisma"))
    generated_files: Dict[str, str] = input_data.get("generated_files", {}) or {}

    factory_workdir = os.getenv("FACTORY_WORKDIR", "/app/generated-projects")
    project_workdir = os.path.join(factory_workdir, project_name)

    activity.logger.info(f"[qa] Démarrage — projet={project_name} workdir_exists={os.path.isdir(project_workdir)}")

    # ── Jest smoke tests ──────────────────────────────────────────────────
    test_files: Dict[str, str] = {}
    tests_passed = False
    tests_summary = "Non exécuté"
    semgrep_result: Dict[str, Any] = {"ran": False}

    try:
        from agents.qa import generate_qa_tests
        test_files = await generate_qa_tests(
            project_name=project_name,
            generated_files=generated_files,
            stack_id=stack_id,
        )
    except Exception as e:
        activity.logger.warning(f"[qa] generate_qa_tests échoué (non-bloquant): {e}")

    if test_files and os.path.isdir(project_workdir):
        written = _write_test_files(test_files, project_workdir)
        activity.logger.info(f"[qa] {len(written)} fichier(s) Jest écrits")
        tests_passed, tests_summary = _run_jest(project_workdir)
        activity.logger.info(f"[qa] Jest → {'PASS' if tests_passed else 'FAIL'} | {tests_summary[:100]}")
        semgrep_result = _run_semgrep(project_workdir)
        if semgrep_result.get("ran"):
            activity.logger.info(f"[qa] Semgrep → {semgrep_result.get('findings_count', 0)} finding(s)")
    else:
        activity.logger.info("[qa] Skippé — pas de tests générés ou workdir absent")

    return {
        "e2e_tests": test_files,
        "tests_passed": tests_passed,
        "tests_summary": tests_summary,
        "semgrep": semgrep_result,
    }
