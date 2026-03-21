from __future__ import annotations

import json
import os
import re
from typing import Any, Dict

from temporalio import activity


def _workdir() -> str:
    return os.path.normpath(os.getenv("FACTORY_WORKDIR", "."))


def _resolve_artifact_path(path_value: str) -> str:
    p = str(path_value or "").strip()
    if not p:
        return ""
    if os.path.isabs(p):
        return os.path.normpath(p)
    return os.path.normpath(os.path.join(_workdir(), p))


def _read_json(path_value: str, default: Any) -> Any:
    path = _resolve_artifact_path(path_value)
    if not path or not os.path.isfile(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _write_json(path: str, payload: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def _page_to_file(page: str) -> str:
    p = str(page or "").strip()
    if not p:
        return ""
    if p.startswith("app/"):
        return p if p.endswith("/page.tsx") else os.path.join(p, "page.tsx").replace("\\", "/")
    if p.startswith("/"):
        if p == "/":
            return "app/page.tsx"
        seg = p.lstrip("/")
        return f"app/{seg}/page.tsx"
    return ""


def _route_to_file(route: str) -> str:
    r = str(route or "").strip()
    if not r:
        return ""
    if r.startswith("app/") and r.endswith("/route.ts"):
        return r
    # Ex: "GET /api/products" -> app/api/products/route.ts
    m = re.match(r"^(GET|POST|PUT|PATCH|DELETE)\s+(.+)$", r, re.IGNORECASE)
    if m:
        path = m.group(2).strip()
        if path.startswith("/api/"):
            return f"app{path}/route.ts"
    if r.startswith("/api/"):
        return f"app{r}/route.ts"
    return ""


def _placeholder_content(path: str, plan: dict) -> str:
    p = path.replace("\\", "/")
    if p.endswith("prisma/schema.prisma"):
        models = plan.get("data_models", []) if isinstance(plan, dict) else []
        body = "\n\n".join(str(m) for m in models) if models else "model Example {\n  id String @id @default(cuid())\n}"
        return (
            "generator client {\n  provider = \"prisma-client-js\"\n}\n\n"
            "datasource db {\n  provider = \"postgresql\"\n}\n\n"
            f"{body}\n"
        )
    if p.endswith("/route.ts"):
        return (
            "import { NextResponse } from 'next/server'\n\n"
            "export async function GET() {\n"
            "  return NextResponse.json({ ok: true })\n"
            "}\n"
        )
    if p.endswith("/page.tsx"):
        return (
            "export default function Page() {\n"
            "  return <main>TODO</main>\n"
            "}\n"
        )
    if p.endswith(".ts"):
        return "export {}\n"
    return ""


def _collect_target_files(plan: dict) -> list[str]:
    targets: list[str] = []
    if not isinstance(plan, dict):
        return targets
    pages = plan.get("pages", []) or []
    routes = plan.get("api_routes", []) or []
    models = plan.get("data_models", []) or []

    for page in pages:
        f = _page_to_file(str(page))
        if f:
            targets.append(f)
    for route in routes:
        f = _route_to_file(str(route))
        if f:
            targets.append(f)
    if models:
        targets.append("prisma/schema.prisma")

    dedup: list[str] = []
    seen = set()
    for t in targets:
        n = t.replace("\\", "/")
        if n not in seen:
            dedup.append(n)
            seen.add(n)
    return dedup


@activity.defn(name="generate_batch_activity")
async def generate_batch_activity(input_data: Dict[str, Any]) -> Dict[str, Any]:
    run_id = str(input_data.get("run_id", "")).strip()
    stack_id = str(input_data.get("stack_id", "nextjs-clerk-prisma")).strip() or "nextjs-clerk-prisma"
    requirements_ref = str(input_data.get("requirements_ref", "")).strip()
    plan_ref = str(input_data.get("plan_ref", "")).strip()
    batch_cursor = int(input_data.get("batch_cursor", 0) or 0)
    completed_files = {
        str(p).replace("\\", "/")
        for p in (input_data.get("completed_files", []) or [])
    }

    batch_size = 3
    try:
        from agents.stack_config import load_stack_config

        stack_cfg = load_stack_config(stack_id) or {}
        batch_size = int((stack_cfg.get("supervision", {}) or {}).get("batch_size", 3))
        if batch_size < 1:
            batch_size = 1
    except Exception:
        batch_size = 3

    plan = _read_json(plan_ref, {})
    _ = _read_json(requirements_ref, [])
    target_files = [p for p in _collect_target_files(plan) if p not in completed_files]

    start = max(0, batch_cursor * batch_size)
    batch_paths = target_files[start:start + batch_size]
    no_more_files = len(batch_paths) == 0
    batch_id = f"batch_{batch_cursor:03d}"

    batch_dir = os.path.join(_workdir(), run_id, "batches", batch_id)
    files_path = os.path.join(batch_dir, "files.json")
    files_payload = {
        path: _placeholder_content(path, plan)
        for path in batch_paths
    }
    _write_json(files_path, files_payload)

    result = {
        "run_id": run_id,
        "batch_id": batch_id,
        "artifact_ref": {
            "run_id": run_id,
            "batch_id": batch_id,
            "path": files_path,
        },
        "stack_id": stack_id,
        "requirements_ref": requirements_ref,
        "plan_ref": plan_ref,
        "files_count": len(batch_paths),
        "batch_index": batch_cursor,
        "no_more_files": no_more_files,
    }

    # M4 — Learner event
    if not no_more_files:
        try:
            from agents.observability import _write_learner_event
            _write_learner_event(
                event_type="batch_generated",
                payload={
                    "batch_id": batch_id,
                    "batch_index": batch_cursor,
                    "files_count": len(batch_paths),
                    "files": batch_paths,
                    "stack_id": stack_id,
                },
                run_id=run_id,
            )
        except Exception:
            pass

    return result


@activity.defn(name="aggregate_corrections_activity")
async def aggregate_corrections_activity(input_data: Dict[str, Any]) -> Dict[str, Any]:
    run_id = str(input_data.get("run_id", "")).strip()
    batch_id = str(input_data.get("batch_id", "")).strip() or "batch_000"
    supervisor_results = input_data.get("supervisor_results", []) or []

    must_fix: list[dict] = []
    should_fix: list[dict] = []
    files_impacted: set[str] = set()

    for raw in supervisor_results:
        result = raw if isinstance(raw, dict) else {}
        supervisor = str(result.get("supervisor", "") or result.get("source", "") or "unknown")
        conf = float(result.get("confidence", 0.0) or 0.0)
        status = str(result.get("status", "")).lower()

        fix_items: list[dict] = []
        if isinstance(result.get("fixes"), list):
            fix_items = [f for f in result.get("fixes", []) if isinstance(f, dict)]
        elif isinstance(result.get("fix_instruction"), dict):
            fix_items = [result.get("fix_instruction")]

        if status != "needs_fix":
            continue

        for fix in fix_items:
            file_path = str(fix.get("file", "")).replace("\\", "/").strip()
            if not file_path:
                continue
            entry = {
                "file": file_path,
                "supervisor": supervisor,
                "fix": str(fix.get("fix", "")).strip(),
                "confidence": round(conf, 3),
            }
            files_impacted.add(file_path)
            if conf >= 0.8:
                must_fix.append(entry)
            elif conf >= 0.5:
                should_fix.append(entry)

    bundle = {
        "run_id": run_id,
        "batch_id": batch_id,
        "must_fix": must_fix,
        "should_fix": should_fix,
        "files_impacted": sorted(files_impacted),
        "total_fixes": len(must_fix) + len(should_fix),
    }

    out_path = os.path.join(_workdir(), run_id, "corrections", f"bundle_{batch_id}.json")
    _write_json(out_path, bundle)

    # M4 — Learner event
    try:
        from agents.observability import _write_learner_event
        _write_learner_event(
            event_type="supervisor_batch_reviewed",
            payload={
                "batch_id": batch_id,
                "must_fix_count": len(must_fix),
                "should_fix_count": len(should_fix),
                "total_fixes": bundle["total_fixes"],
                "files_impacted": bundle["files_impacted"],
                "supervisors": list({item["supervisor"] for item in must_fix + should_fix}),
            },
            run_id=run_id,
        )
    except Exception:
        pass

    return bundle


@activity.defn(name="apply_corrections_activity")
async def apply_corrections_activity(input_data: Dict[str, Any]) -> Dict[str, Any]:
    batch_id = str(input_data.get("batch_id", "")).strip() or "batch_000"
    artifact_ref = input_data.get("artifact_ref", {}) or {}
    files_path = _resolve_artifact_path(str(artifact_ref.get("path", "")).strip())
    corrections_bundle = input_data.get("corrections_bundle", {}) or {}

    files_payload = _read_json(files_path, {})
    if not isinstance(files_payload, dict):
        files_payload = {}

    must_fix = corrections_bundle.get("must_fix", []) or []
    applied_count = 0

    for item in must_fix:
        if not isinstance(item, dict):
            continue
        fp = str(item.get("file", "")).replace("\\", "/").strip()
        fix_txt = str(item.get("fix", "")).strip()
        if not fp or not fix_txt:
            continue
        current = str(files_payload.get(fp, ""))
        marker = f"/* AUTO_FIX:{batch_id} */"
        patch = f"\n{marker}\n{fix_txt}\n"
        if patch not in current:
            files_payload[fp] = current + patch
            applied_count += 1

    if files_path:
        _write_json(files_path, files_payload)

    completed_files = sorted(str(k).replace("\\", "/") for k in files_payload.keys())

    # M4 — Learner event
    run_id_apply = str(input_data.get("run_id", "")).strip()
    try:
        from agents.observability import _write_learner_event
        _write_learner_event(
            event_type="corrections_applied",
            payload={
                "batch_id": batch_id,
                "applied_count": applied_count,
                "completed_files_count": len(completed_files),
            },
            run_id=run_id_apply,
        )
    except Exception:
        pass

    return {"completed_files": completed_files, "applied_count": applied_count}


@activity.defn(name="build_activity")
async def build_activity(input_data: Dict[str, Any]) -> Dict[str, Any]:
    run_id = str(input_data.get("run_id", "")).strip()
    project_dir = os.path.join(_workdir(), run_id) if run_id else _workdir()

    try:
        from agents.shared_tools import run_build

        build_out = str(run_build.invoke({"project_dir": project_dir}))
    except Exception as e:
        err = str(e)
        return {"success": False, "stderr": err, "build_result": {"output": err}}

    success = "Build successful" in build_out
    stderr = ""
    if not success:
        marker = "STDERR:\n"
        stderr = build_out.split(marker, 1)[1] if marker in build_out else build_out

    return {
        "success": bool(success),
        "stderr": str(stderr),
        "build_result": {"output": build_out},
    }
