from __future__ import annotations

import asyncio
import os

from temporalio import activity

from agents.security_agent import run_security_supervisor

_MAX_ROUTES = 8


def _extract_prisma_schema(files: dict[str, str]) -> str:
    for key in ("prisma/schema.prisma", "schema.prisma"):
        if key in files:
            return files[key]
    for path, content in files.items():
        if path.replace("\\", "/").endswith("schema.prisma"):
            return content
    return ""


def _select_api_routes(files: dict[str, str]) -> dict[str, str]:
    """Sélectionne uniquement les routes API pour review sécurité."""
    routes: dict[str, str] = {}
    for path, content in files.items():
        norm = path.replace("\\", "/")
        if "/api/" in norm and norm.endswith("/route.ts"):
            routes[path] = content
            if len(routes) >= _MAX_ROUTES:
                break
    return routes


@activity.defn(name="security_activity")
async def security_activity(input_data: dict) -> dict:
    files = input_data.get("files")

    # ── Mode batch : files dict fourni ────────────────────────────────────
    if files and isinstance(files, dict):
        project_name: str = input_data.get("project_name", "")
        run_id: str = input_data.get("run_id", "")
        stack_id: str = input_data.get("stack_id", "nextjs-clerk-prisma")

        api_routes = _select_api_routes(files)
        prisma_schema = _extract_prisma_schema(files)

        if not api_routes:
            return {
                "status": "skipped",
                "supervisor": "security",
                "note": "no_api_routes",
                "files_reviewed": 0,
                "needs_fix_count": 0,
                "fixes": [],
                "confidence": 0.0,
            }

        tasks = [
            run_security_supervisor(
                file_path=path,
                file_content=content,
                prisma_schema=prisma_schema,
                project_name=project_name,
                run_id=run_id,
                stack_id=stack_id,
            )
            for path, content in api_routes.items()
        ]
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)

        fixes: list[dict] = []
        needs_fix_count = 0
        for path, r in zip(api_routes.keys(), raw_results):
            if isinstance(r, Exception):
                activity.logger.warning(f"[security] {path}: exception {r}")
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
            "supervisor": "security",
            "files_reviewed": len(api_routes),
            "needs_fix_count": needs_fix_count,
            "fixes": fixes,
            "confidence": avg_confidence,
        }

    # ── Mode single-file (backward compat) ────────────────────────────────
    return await run_security_supervisor(
        file_path=input_data.get("file_path", ""),
        file_content=input_data.get("file_content", ""),
        prisma_schema=input_data.get("prisma_schema", ""),
        project_name=input_data.get("project_name", ""),
        run_id=input_data.get("run_id", ""),
        stack_id=input_data.get("stack_id", "nextjs-clerk-prisma"),
    )
