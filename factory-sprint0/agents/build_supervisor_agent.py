"""Build supervisor inline (Sprint 4.6 v2)."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from utils.prompt_loader import load_base_prompt, load_stack_rules_only

logger = logging.getLogger(__name__)

_FILE_HINT_RE = re.compile(r"([A-Za-z0-9_./\\-]+\.(?:ts|tsx|js|jsx|json|prisma))")
_TS_FILE_LINE_RE = re.compile(r"(?P<file>.+?)\((?P<line>\d+),(?P<col>\d+)\):\s+error\s+TS\d+:")


def _strip_json_fences(content: str) -> str:
    text = (content or "").strip()
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else text


def _load_system_prompt(stack_id: str) -> str:
    try:
        base = load_base_prompt("build_supervisor")
    except Exception:
        return ""
    rules = load_stack_rules_only("build_supervisor", stack_id)
    return f"{base}\n\n---\n\n{rules}" if rules.strip() else base


def _extract_failing_paths(stderr_text: str, combined_files: dict[str, str]) -> list[str]:
    candidates: list[str] = []
    normalized_map = {k.replace("\\", "/"): k for k in combined_files.keys()}
    for match in _TS_FILE_LINE_RE.finditer(stderr_text or ""):
        raw = match.group("file").strip().replace("\\", "/")
        if raw in normalized_map:
            candidates.append(normalized_map[raw])
    for token in _FILE_HINT_RE.findall(stderr_text or ""):
        raw = token.strip().replace("\\", "/")
        if raw in normalized_map:
            candidates.append(normalized_map[raw])
    out: list[str] = []
    seen: set[str] = set()
    for path in candidates:
        if path not in seen:
            out.append(path)
            seen.add(path)
    return out


def _normalize_lines_concerned(value: Any) -> list[int]:
    if not isinstance(value, list):
        return []
    out: list[int] = []
    for item in value:
        try:
            out.append(int(item))
        except Exception:
            continue
    return out


def _normalize_fix_instruction(raw: Any, default_file: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {}
    out = {
        "file": str(raw.get("file", "") or default_file),
        "problem": str(raw.get("problem", "") or ""),
        "fix": str(raw.get("fix", "") or ""),
    }
    lines = _normalize_lines_concerned(raw.get("lines_concerned", []))
    if lines:
        out["lines_concerned"] = lines
    if not out["problem"] or not out["fix"]:
        return {}
    return out


def _normalize_result(payload: Any, default_file: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {"status": "skipped"}
    status = str(payload.get("status", "skipped") or "skipped").strip().lower()
    if status not in {"ok", "needs_fix", "skipped"}:
        status = "skipped"
    out: dict[str, Any] = {"status": status}
    failing_file = str(payload.get("failing_file", "") or default_file)
    if failing_file:
        out["failing_file"] = failing_file
    if status == "needs_fix":
        fix = _normalize_fix_instruction(payload.get("fix_instruction", {}), failing_file or default_file)
        if fix:
            out["fix_instruction"] = fix
    return out


async def run_build_supervisor(
    build_stderr: str,
    combined_files: dict[str, str],
    run_id: str = "",
    stack_id: str = "nextjs-clerk-prisma",
) -> dict:
    """
    Analyse un stderr de build et propose une correction minimale.
    Retourne toujours un dict. Jamais d'exception.
    """
    try:
        if not build_stderr or not combined_files:
            return {"status": "skipped"}
        system_prompt = _load_system_prompt(stack_id)
        if not system_prompt.strip():
            return {"status": "skipped"}

        failing_paths = _extract_failing_paths(build_stderr, combined_files)
        failing_file = failing_paths[0] if failing_paths else ""
        file_snippets: list[str] = []
        for path in failing_paths[:3]:
            file_snippets.append(f"### {path}\n```text\n{combined_files.get(path, '')}\n```")

        stderr_clipped = build_stderr[:2000]
        human_prompt = (
            f"run_id={run_id or 'unknown'}\n"
            f"stack_id={stack_id}\n\n"
            "BUILD STDERR:\n"
            "```text\n"
            f"{stderr_clipped}\n"
            "```\n\n"
            "FAILING FILES CONTENT:\n"
            f"{chr(10).join(file_snippets) if file_snippets else '[none detected]'}\n\n"
            "Give only a minimal surgical fix. Never suggest full-file rewrites.\n"
            "Return strict JSON: status, failing_file, optional fix_instruction."
        )
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0, max_retries=2).bind(
            response_format={"type": "json_object"}
        )
        response = await llm.ainvoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=human_prompt)]
        )
        payload = json.loads(_strip_json_fences(str(getattr(response, "content", "") or "")))
        return _normalize_result(payload, failing_file)
    except Exception as e:
        logger.warning(f"[build_supervisor] skipped (non bloquant): {e}")
        return {"status": "skipped"}

