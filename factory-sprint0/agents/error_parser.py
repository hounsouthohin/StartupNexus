"""
error_parser.py — Parsing centralisé des sorties d'outils de build.

Source unique pour parser les erreurs TSC et ESLint.
Remplace les deux regex divergentes dans shared_tools.py et dev_graph.py.

Règle : ce module n'importe rien des autres agents (zéro dépendance interne).
"""
from __future__ import annotations

import re
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
