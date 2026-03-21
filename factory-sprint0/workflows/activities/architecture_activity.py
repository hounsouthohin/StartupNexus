from __future__ import annotations

import asyncio
import os

from temporalio import activity

from agents.architecture_agent import run_architecture_supervisor

_MAX_FILES = 8
_TEMPLATE_PATHS = frozenset({
    "middleware.ts",
    "jest.config.js",
    "jest.setup.js",
    "tsconfig.json",
    "next.config.js",
    "tests/middleware.test.ts",
    ".env.local",
})
_ARCH_EXTS = frozenset({".ts", ".tsx", ".prisma"})


def _select_files_for_architecture(files: dict[str, str]) -> dict[str, str]:
    """
    Sélectionne les fichiers les plus pertinents pour review architecturale :
    priorité schema.prisma, app/layout.tsx, pages, routes API, lib/.
    """
    priority: dict[str, str] = {}
    secondary: dict[str, str] = {}

    for path, content in files.items():
        norm = path.replace("\\", "/")
        basename = norm.split("/")[-1]
        if basename in _TEMPLATE_PATHS or norm in _TEMPLATE_PATHS:
            continue
        _, ext = os.path.splitext(basename)
        if ext not in _ARCH_EXTS:
            continue

        is_priority = (
            norm.endswith("schema.prisma")
            or norm == "app/layout.tsx"
            or (norm.endswith("/page.tsx") and norm.count("/") <= 3)
            or ("/api/" in norm and norm.endswith("/route.ts"))
            or norm.startswith("lib/")
        )
        if is_priority:
            priority[path] = content
        else:
            secondary[path] = content

    selected: dict[str, str] = {}
    for bucket in (priority, secondary):
        for k, v in bucket.items():
            if len(selected) >= _MAX_FILES:
                break
            selected[k] = v
        if len(selected) >= _MAX_FILES:
            break
    return selected


@activity.defn(name="architecture_activity")
async def architecture_activity(input_data: dict) -> dict:
    files = input_data.get("files")

    # ── Mode batch : files dict fourni ────────────────────────────────────
    if files and isinstance(files, dict):
        plan: dict = input_data.get("plan", {})
        project_name: str = input_data.get("project_name", "")
        run_id: str = input_data.get("run_id", "")
        stack_id: str = input_data.get("stack_id", "nextjs-clerk-prisma")

        selected = _select_files_for_architecture(files)
        if not selected:
            return {
                "status": "skipped",
                "supervisor": "architecture",
                "note": "no_files",
                "files_reviewed": 0,
                "needs_fix_count": 0,
                "fixes": [],
                "confidence": 0.0,
            }

        tasks = [
            run_architecture_supervisor(
                file_path=path,
                file_content=content,
                prisma_schema=files.get("prisma/schema.prisma", files.get("schema.prisma", "")),
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
                activity.logger.warning(f"[architecture] {path}: exception {r}")
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
            "supervisor": "architecture",
            "files_reviewed": len(selected),
            "needs_fix_count": needs_fix_count,
            "fixes": fixes,
            "confidence": avg_confidence,
        }

    # ── Mode single-file (backward compat) ────────────────────────────────
    return await run_architecture_supervisor(
        file_path=input_data.get("file_path", ""),
        file_content=input_data.get("file_content", ""),
        prisma_schema=input_data.get("prisma_schema", ""),
        plan=input_data.get("plan", {}),
        files_so_far=input_data.get("files_so_far", {}),
        project_name=input_data.get("project_name", ""),
        run_id=input_data.get("run_id", ""),
        stack_id=input_data.get("stack_id", "nextjs-clerk-prisma"),
    )
