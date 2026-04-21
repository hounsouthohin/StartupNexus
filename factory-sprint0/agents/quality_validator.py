"""
quality_validator.py

Détecteur de violations qualité TypeScript via AST.
Utilise quality_check.mjs (@typescript-eslint/parser) exécuté dans le répertoire
du projet généré — où les dépendances Node.js sont disponibles après npm install.

Violations détectées :
  Z21 — findMany() sans take (pagination manquante)
  Z24 — findUnique() dans .map() (N+1)
  Z25 — findMany() sans select dans les services
  Z26 — 2+ mutations Prisma consécutives sans $transaction

Intégré dans prebuild_pipeline.py comme stage "quality_rules".
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from agents.prebuild_pipeline import StageResult, Violation

STAGE_QUALITY_RULES = "quality_rules"
CHECKER_SCRIPT = Path(__file__).resolve().parents[1] / "quality_checker" / "quality_check.mjs"

# Fichiers à analyser (seulement le code applicatif LLM)
ANALYSED_GLOBS = ["app/api/**/*.ts", "app/api/**/*.tsx", "lib/services/**/*.ts"]
EXCLUDED_PREFIXES = [
    "middleware", "lib/prisma", "lib/logger", "lib/prisma-errors",
    "app/api/health", "jest", "next.config",
]

_RAG_QUERY_BY_RULE = {
    "Z21-pagination-missing":   "pagination findMany skip take PaginatedResponse",
    "Z24-n1-pattern":           "N+1 prevention include select imbriqué findUnique loop Prisma",
    "Z25-select-missing":       "select minimal findMany performance Prisma GetPayload",
    "Z26-missing-transaction":  "transaction prisma $transaction séquentielle rollback multi-table",
}


def _collect_files(project_dir: str) -> list[str]:
    """Collecte les fichiers TypeScript applicatifs générés par le LLM."""
    targets: list[str] = []
    for root, _dirs, files in os.walk(project_dir):
        for fname in files:
            if not fname.endswith((".ts", ".tsx")):
                continue
            abs_path = os.path.join(root, fname)
            rel = os.path.relpath(abs_path, project_dir).replace("\\", "/")
            # Exclure les templates protégés et node_modules/.next
            if any(x in rel for x in ["node_modules", ".next", "__tests__", "jest", ".test."]):
                continue
            if any(rel.startswith(p) or rel == p + ".ts" for p in EXCLUDED_PREFIXES):
                continue
            targets.append(abs_path)
    return targets


async def run_quality_check(project_dir: str) -> StageResult:
    """
    Lance quality_check.mjs dans le contexte du projet généré.
    Retourne un StageResult compatible avec prebuild_pipeline.
    """
    started = time.perf_counter()
    tool = f"node quality_check.mjs (AST — @typescript-eslint/parser)"

    if not CHECKER_SCRIPT.exists():
        return StageResult(
            STAGE_QUALITY_RULES, tool, "error",
            int((time.perf_counter() - started) * 1000),
            evidence="quality_check.mjs introuvable dans factory/quality_checker/",
        )

    # Vérifier que @typescript-eslint/parser est installé dans le projet
    parser_path = os.path.join(project_dir, "node_modules", "@typescript-eslint", "parser")
    if not os.path.exists(parser_path):
        return StageResult(
            STAGE_QUALITY_RULES, tool, "skipped",
            int((time.perf_counter() - started) * 1000),
            evidence="@typescript-eslint/parser absent — npm install non encore exécuté",
        )

    files = _collect_files(project_dir)
    if not files:
        return StageResult(
            STAGE_QUALITY_RULES, tool, "ok",
            int((time.perf_counter() - started) * 1000),
            evidence="Aucun fichier applicatif à analyser",
        )

    # Copie du script dans le projet pour l'exécution locale
    tmp_script = os.path.join(project_dir, "_quality_check_tmp.mjs")
    try:
        shutil.copy2(str(CHECKER_SCRIPT), tmp_script)
        proc = subprocess.run(
            ["node", "_quality_check_tmp.mjs"] + files,
            capture_output=True,
            text=True,
            cwd=project_dir,
            timeout=30,
        )
        raw = proc.stdout.strip()
    except subprocess.TimeoutExpired:
        return StageResult(
            STAGE_QUALITY_RULES, tool, "error",
            int((time.perf_counter() - started) * 1000),
            evidence="Timeout (30s) — quality checker trop lent",
        )
    except Exception as e:
        return StageResult(
            STAGE_QUALITY_RULES, tool, "error",
            int((time.perf_counter() - started) * 1000),
            evidence=str(e)[:300],
        )
    finally:
        if os.path.exists(tmp_script):
            os.unlink(tmp_script)

    # Parse violations JSON
    try:
        violations_raw = json.loads(raw) if raw else []
    except json.JSONDecodeError:
        return StageResult(
            STAGE_QUALITY_RULES, tool, "error",
            int((time.perf_counter() - started) * 1000),
            evidence=f"JSON invalide depuis quality checker:\n{raw[:200]}",
        )

    if not violations_raw:
        return StageResult(
            STAGE_QUALITY_RULES, tool, "ok",
            int((time.perf_counter() - started) * 1000),
        )

    # Convertir en objets Violation + formater l'evidence pour le LLM
    violations: list[Violation] = []
    lines = []
    for v in violations_raw:
        rel = os.path.relpath(v.get("file", ""), project_dir).replace("\\", "/")
        line_no = v.get("line", 0) or None
        rule = v.get("rule", "")
        msg = v.get("message", "")
        rag = _RAG_QUERY_BY_RULE.get(rule, v.get("rag_query", ""))
        fix_hint = (
            f"Recherche standard : rag_search('{rag}') puis corriger {rel}"
            if rag else f"Corriger la violation {rule} dans {rel}"
        )
        violations.append(Violation(
            rule_id=rule,
            file=rel,
            line=line_no,
            reason=msg,
            fix_hint=fix_hint,
        ))
        lines.append(f"  [{rule}] {rel}:{line_no or 0} — {msg}")
        if rag:
            lines.append(f"    → Recherche standard : rag_search('{rag}')")

    evidence = "\n".join(lines)
    duration_ms = int((time.perf_counter() - started) * 1000)

    return StageResult(
        STAGE_QUALITY_RULES, tool, "failed",
        duration_ms,
        evidence=evidence,
        violations=violations,
    )
