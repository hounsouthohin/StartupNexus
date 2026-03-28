"""
DÉPRÉCIÉ — Phase C (27 Mars 2026).
LLM supervisors retirés du pipeline. Conservé pour ne pas casser les imports.
Non appelé en production. À supprimer en Sprint 6 si non réintégré.

Superviseur Architecture inline (Sprint 4.6 v2).
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from utils.prompt_loader import load_base_prompt, load_stack_rules_only

logger = logging.getLogger(__name__)


def _strip_json_fences(content: str) -> str:
    text = (content or "").strip()
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else text


def _load_system_prompt(stack_id: str) -> str:
    try:
        base = load_base_prompt("architecture")
    except Exception:
        return ""
    rules = load_stack_rules_only("architecture", stack_id)
    return f"{base}\n\n---\n\n{rules}" if rules.strip() else base


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


def _normalize_result(payload: Any, file_path: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {"status": "skipped", "confidence": 0.0, "note": "invalid_payload"}
    status = str(payload.get("status", "skipped") or "skipped").strip().lower()
    if status not in {"ok", "needs_fix", "skipped"}:
        status = "skipped"
    try:
        confidence = float(payload.get("confidence", 0.0) or 0.0)
    except Exception:
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))
    note = str(payload.get("note", "") or "")
    out: dict[str, Any] = {"status": status, "confidence": round(confidence, 3)}
    if note:
        out["note"] = note
    if status == "needs_fix":
        fix = _normalize_fix_instruction(payload.get("fix_instruction", {}), file_path)
        if fix:
            out["fix_instruction"] = fix
    return out


async def run_architecture_supervisor(
    file_path: str,
    file_content: str,
    prisma_schema: str = "",
    plan: dict | None = None,
    files_so_far: dict[str, str] | None = None,
    project_name: str = "",
    run_id: str = "",
    stack_id: str = "nextjs-clerk-prisma",
    det_tool_result: str = "",
) -> dict:
    """
    Vérifie la cohérence inter-fichiers.
    Retourne toujours un dict. Jamais d'exception.
    """
    try:
        if not file_path or not file_content:
            return {"status": "skipped", "confidence": 0.0, "note": "empty_file"}
        system_prompt = _load_system_prompt(stack_id)
        if not system_prompt.strip():
            return {"status": "skipped", "confidence": 0.0, "note": "missing_prompt"}

        files_so_far = files_so_far or {}
        paths = sorted(str(p).replace("\\", "/") for p in files_so_far.keys())
        plan = plan or {}
        plan_summary = {
            "data_models": list(plan.get("data_models", []) or []),
            "pages": list(plan.get("pages", []) or []),
            "api_routes": list(plan.get("api_routes", []) or []),
            "key_features": list(plan.get("key_features", []) or []),
        }

        human_prompt = (
            f"project_name={project_name or 'unknown'}\n"
            f"run_id={run_id or 'unknown'}\n"
            f"stack_id={stack_id}\n\n"
            "FILE TO REVIEW:\n"
            f"path: {file_path}\n"
            "```text\n"
            f"{file_content}\n"
            "```\n\n"
            "PLAN SUMMARY:\n"
            f"{json.dumps(plan_summary, ensure_ascii=False, indent=2)}\n\n"
            "FILES SO FAR (paths):\n"
            f"{json.dumps(paths, ensure_ascii=False)}\n\n"
            "PRISMA SCHEMA:\n"
            f"{prisma_schema or '[none]'}\n\n"
            + (f"DETERMINISTIC TOOL RESULT:\n{det_tool_result}\n\n" if det_tool_result else "")
            + "Return strictly JSON with keys: status, confidence, optional fix_instruction, optional note."
        )

        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0, max_retries=2).bind(
            response_format={"type": "json_object"}
        )
        response = await llm.ainvoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=human_prompt)]
        )
        payload = json.loads(_strip_json_fences(str(getattr(response, "content", "") or "")))
        return _normalize_result(payload, file_path)
    except Exception as e:
        logger.warning(f"[architecture_supervisor] skipped (non bloquant): {e}")
        return {"status": "skipped", "confidence": 0.0}

