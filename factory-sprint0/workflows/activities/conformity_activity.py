from __future__ import annotations

import asyncio
import os
from typing import Any

from temporalio import activity

from agents.conformity_agent import run_conformity_supervisor

# Fichiers template : jamais reviewés par conformité
_TEMPLATE_PATHS = frozenset({
    "middleware.ts",
    "jest.config.js",
    "jest.setup.js",
    "tsconfig.json",
    "next.config.js",
    "tests/middleware.test.ts",
    ".env.local",
})
_BUSINESS_EXTS = frozenset({".ts", ".tsx", ".js", ".jsx"})
_MAX_FILES = 10


def _is_business_file(path: str) -> bool:
    norm = path.replace("\\", "/")
    basename = norm.split("/")[-1]
    if basename in _TEMPLATE_PATHS or norm in _TEMPLATE_PATHS:
        return False
    _, ext = os.path.splitext(basename)
    return ext in _BUSINESS_EXTS


def _select_files(files: dict[str, str]) -> dict[str, str]:
    """Prioritise routes API, pages, puis autres fichiers business."""
    api_routes = {}
    pages = {}
    others = {}
    for path, content in files.items():
        norm = path.replace("\\", "/")
        if not _is_business_file(norm):
            continue
        if "/api/" in norm and norm.endswith("/route.ts"):
            api_routes[path] = content
        elif norm.endswith("/page.tsx") or norm.endswith("/page.ts"):
            pages[path] = content
        else:
            others[path] = content

    selected: dict[str, str] = {}
    for bucket in (api_routes, pages, others):
        for k, v in bucket.items():
            if len(selected) >= _MAX_FILES:
                break
            selected[k] = v
        if len(selected) >= _MAX_FILES:
            break
    return selected


@activity.defn(name="conformity_activity")
async def conformity_activity(input_data: dict) -> dict:
    files: Any = input_data.get("files")

    # ── Mode batch : files dict fourni ────────────────────────────────────
    if files and isinstance(files, dict):
        requirements: list = input_data.get("requirements", [])
        plan: dict = input_data.get("plan", {})
        project_name: str = input_data.get("project_name", "")
        run_id: str = input_data.get("run_id", "")
        stack_id: str = input_data.get("stack_id", "nextjs-clerk-prisma")

        selected = _select_files(files)
        if not selected:
            return {
                "status": "skipped",
                "supervisor": "conformity",
                "note": "no_business_files",
                "files_reviewed": 0,
                "needs_fix_count": 0,
                "fixes": [],
                "confidence": 0.0,
            }

        tasks = [
            run_conformity_supervisor(
                file_path=path,
                file_content=content,
                requirements=requirements,
                plan=plan,
                files_so_far=files,
                project_name=project_name,
                run_id=run_id,
                stack_id=stack_id,
            )
            for path, content in selected.items()
        ]
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)

        fixes: list[dict] = []
        needs_fix_count = 0
        for path, r in zip(selected.keys(), raw_results):
            if isinstance(r, Exception):
                activity.logger.warning(f"[conformity] {path}: exception {r}")
                continue
            if not isinstance(r, dict):
                continue
            if r.get("status") == "needs_fix":
                needs_fix_count += 1
                fix = r.get("fix_instruction", {})
                if fix:
                    fixes.append({
                        "file": path,
                        "problem": fix.get("problem", ""),
                        "fix": fix.get("fix", ""),
                        "confidence": round(float(r.get("confidence", 0.0)), 3),
                    })

        overall_status = "needs_fix" if needs_fix_count > 0 else "ok"
        avg_confidence = (
            round(sum(f["confidence"] for f in fixes) / len(fixes), 3) if fixes else 0.0
        )
        return {
            "status": overall_status,
            "supervisor": "conformity",
            "files_reviewed": len(selected),
            "needs_fix_count": needs_fix_count,
            "fixes": fixes,
            "confidence": avg_confidence,
        }

    # ── Mode single-file (backward compat) ────────────────────────────────
    return await run_conformity_supervisor(
        file_path=input_data.get("file_path", ""),
        file_content=input_data.get("file_content", ""),
        requirements=input_data.get("requirements", []),
        plan=input_data.get("plan", {}),
        files_so_far=input_data.get("files_so_far", {}),
        project_name=input_data.get("project_name", ""),
        run_id=input_data.get("run_id", ""),
        stack_id=input_data.get("stack_id", "nextjs-clerk-prisma"),
    )
