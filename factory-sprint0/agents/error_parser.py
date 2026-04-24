"""
error_parser.py — Parsing centralisé des sorties d'outils de build.

Source unique pour parser les erreurs TSC et ESLint.
Remplace les deux regex divergentes dans shared_tools.py et dev_graph.py.

R1 (Avril 2026) — ts-morph structured diagnostics :
  run_tsc_structured()        : appelle tsc_check.mjs via subprocess, retourne list[dict]
  filter_tsc_errors_structured(): filtre les diagnostics par fichiers cibles, retourne str LLM-ready

Règle : ce module n'importe rien des autres agents (zéro dépendance interne).
"""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

# ── Regex canonique TSC ───────────────────────────────────────────────────────
# Format : "path/to/file.ts(line,col): error TSxxxx: message"
# \s* (zéro ou plus) entre "error" et "TS" — plus permissif que \s+ pour couvrir
# les variantes de formatage tsc (espacement ou non en sortie CI).
_TSC_LINE_RE = re.compile(
    r"^(?P<file>.+?)\((?P<line>\d+),(?P<col>\d+)\):\s*error\s+(?P<code>TS\d+):\s*(?P<message>.+)$",
    re.MULTILINE,
)

# Regex légère pour détecter si une ligne EST une erreur TSC (sans parser tout le contenu)
_TSC_LINE_DETECT = re.compile(r"^[^(]+\(\d+,\d+\):\s*error\s+TS\d+")


def parse_tsc_errors(output: str) -> list[dict[str, Any]]:
    """
    Parse la sortie complète de `tsc --noEmit` en liste de dicts structurés.
    Retourne [] si output vide ou aucune erreur.
    """
    if not output:
        return []
    errors: list[dict[str, Any]] = []
    for match in _TSC_LINE_RE.finditer(output):
        try:
            errors.append({
                "file":    match.group("file").strip().replace("\\", "/"),
                "line":    int(match.group("line")),
                "col":     int(match.group("col")),
                "code":    match.group("code").strip(),
                "message": match.group("message").strip(),
            })
        except Exception:
            continue
    return errors


def filter_tsc_errors_for_files(tsc_output: str, target_files: list[str], max_lines: int = 20) -> str:
    """
    Filtre la sortie tsc pour ne garder que les erreurs sur les fichiers cibles.
    Retourne un string lisible par le LLM, vide si aucune erreur pertinente.
    """
    if not tsc_output or not target_files:
        return ""
    targets_norm = {f.lstrip("./").replace("\\", "/") for f in target_files}
    relevant: list[str] = []
    for line in tsc_output.splitlines():
        if not _TSC_LINE_DETECT.match(line):
            continue
        file_raw = line.split("(")[0].strip().replace("\\", "/").lstrip("./")
        if any(file_raw.endswith(t) or t.endswith(file_raw) for t in targets_norm):
            relevant.append(line)
    if not relevant:
        return ""
    return "\n".join(relevant[:max_lines])


# ── ts-morph structured diagnostics (R1) ─────────────────────────────────────
_TOOLS_TS_DIR = Path(__file__).resolve().parent.parent / "tools" / "ts"
_TSC_CHECK_MJS = _TOOLS_TS_DIR / "tsc_check.mjs"


def run_tsc_structured(project_dir: str, timeout_s: int = 120) -> list[dict[str, Any]] | None:
    """
    Appelle tools/ts/tsc_check.mjs et retourne les diagnostics structurés TypeScript.
    Chaque dict : {file: str|None, line: int|None, col: int|None, code: str, message: str}

    Retourne None si le script ou Node.js est indisponible — le caller doit
    alors tomber sur le fallback npx tsc + regex.
    Exit 0 = aucune erreur, exit 1 = erreurs TS (liste non vide), exit 2 = tsconfig absent.
    """
    script = str(_TSC_CHECK_MJS)
    if not Path(script).exists():
        return None
    if not shutil.which("node"):
        return None

    try:
        result = subprocess.run(
            ["node", script, project_dir],
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        if result.returncode == 2:
            # tsconfig absent / projet non chargeable — signal pour fallback
            return None
        import json as _json
        return _json.loads(result.stdout or "[]")
    except (subprocess.TimeoutExpired, ValueError, Exception):
        return None


def filter_tsc_errors_structured(
    diagnostics: list[dict[str, Any]],
    target_files: list[str],
    project_dir: str = "",
    max_errors: int = 20,
) -> str:
    """
    Filtre les diagnostics ts-morph sur les fichiers cibles et retourne un string LLM-ready.
    Format aligné sur filter_tsc_errors_for_files :
      app/page.tsx(12,5): error TS2345: message
    """
    if not diagnostics or not target_files:
        return ""

    targets_norm = {f.lstrip("./").replace("\\", "/") for f in target_files}

    def _rel(file_path: str | None) -> str | None:
        if not file_path:
            return None
        norm = str(file_path).replace("\\", "/")
        if project_dir:
            try:
                norm = str(Path(norm).relative_to(project_dir)).replace("\\", "/")
            except Exception:
                pass
        return norm.lstrip("./")

    lines: list[str] = []
    for d in diagnostics:
        rel = _rel(d.get("file"))
        if not rel:
            continue
        if not any(rel.endswith(t) or t.endswith(rel) for t in targets_norm):
            continue
        line = d.get("line") or ""
        col  = d.get("col") or ""
        code = d.get("code") or "TSxxxx"
        msg  = d.get("message") or ""
        lines.append(f"{rel}({line},{col}): error {code}: {msg}")
        if len(lines) >= max_errors:
            break

    return "\n".join(lines)


def parse_eslint_errors_json(output: str) -> list[dict[str, Any]]:
    """
    Parse la sortie JSON d'ESLint (`eslint --format=json`).
    Retourne [] si output invalide ou vide.
    """
    import json
    if not output:
        return []
    try:
        data = json.loads(output)
    except Exception:
        return []
    errors: list[dict[str, Any]] = []
    for file_result in data if isinstance(data, list) else []:
        file_path = str(file_result.get("filePath", "")).replace("\\", "/")
        for msg in file_result.get("messages", []):
            if msg.get("severity", 0) >= 2:
                errors.append({
                    "file":    file_path,
                    "line":    msg.get("line"),
                    "col":     msg.get("column"),
                    "rule":    msg.get("ruleId", ""),
                    "message": msg.get("message", ""),
                })
    return errors
