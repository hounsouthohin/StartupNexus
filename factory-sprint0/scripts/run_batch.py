"""
Déclenche 5 runs TodoPilot consécutifs et collecte les métriques.
Écrit un fichier de synthèse dans logs/metrics/.
"""

from __future__ import annotations

import asyncio
import argparse
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from temporalio.client import Client

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from config.factory_config import TEMPORAL_ADDRESS
from workflows.todo_pilot_workflow import TodoPilotWorkflow


TASK_QUEUE = "factory-task-queue"
LEARNER_LOG_PATH = os.path.join("logs", "shadow", "learner_shadow_log.json")

BATCH_PROJECTS: List[Dict[str, str]] = [
    {"project_name": "todo-batch-alpha", "phrase": "Cree une Todo app Next.js avec Clerk, priorites et tags."},
    {"project_name": "todo-batch-bravo", "phrase": "Cree une Todo app collaborative avec listes partagees et reminders."},
    {"project_name": "todo-batch-charlie", "phrase": "Cree une Todo app avec calendrier hebdo et filtres avances."},
    {"project_name": "todo-batch-delta", "phrase": "Cree une Todo app orientee equipe avec tableaux Kanban."},
    {"project_name": "todo-batch-echo", "phrase": "Cree une Todo app avec analytics de productivite et objectifs."},
]


def _learner_events_count() -> int:
    if not os.path.exists(LEARNER_LOG_PATH):
        return 0
    try:
        with open(LEARNER_LOG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        suggestions = data.get("suggested_standards", [])
        if isinstance(suggestions, list):
            return len(suggestions)
        events = data.get("events", [])
        return len(events) if isinstance(events, list) else 0
    except Exception:
        return 0


async def _run_one(
    client: Client,
    phrase: str,
    project_name: str,
    result_timeout_seconds: float | None = None,
) -> Dict[str, Any]:
    workflow_id = f"todo-pilot-{project_name}-{uuid.uuid4().hex[:8]}"
    started_at = datetime.now(timezone.utc).isoformat()
    t0 = time.perf_counter()
    learner_before = _learner_events_count()

    handle = await client.start_workflow(
        TodoPilotWorkflow.run,
        {"phrase": phrase, "project_name": project_name},
        id=workflow_id,
        task_queue=TASK_QUEUE,
    )

    try:
        if result_timeout_seconds and result_timeout_seconds > 0:
            result = await asyncio.wait_for(handle.result(), timeout=result_timeout_seconds)
        else:
            result = await handle.result()
        success = True
        error = None
    except TimeoutError:
        result = ""
        success = False
        error = f"timeout_after_{result_timeout_seconds}_seconds"
    except Exception as exc:
        result = ""
        success = False
        error = str(exc)

    duration_seconds = round(time.perf_counter() - t0, 2)
    learner_after = _learner_events_count()

    return {
        "workflow_id": workflow_id,
        "run_id": getattr(handle, "first_execution_run_id", None),
        "project_name": project_name,
        "phrase": phrase,
        "started_at": started_at,
        "duration_seconds": duration_seconds,
        "success": success,
        "error": error,
        "learner_events_before": learner_before,
        "learner_events_after": learner_after,
        "learner_events_delta": learner_after - learner_before,
        "result_excerpt": str(result)[:400],
    }


async def run_batch(
    projects: List[Dict[str, str]],
    result_timeout_seconds: float | None = None,
) -> Dict[str, Any]:
    client = await Client.connect(TEMPORAL_ADDRESS)
    runs: List[Dict[str, Any]] = []

    for item in projects:
        run_data = await _run_one(
            client=client,
            phrase=item["phrase"],
            project_name=item["project_name"],
            result_timeout_seconds=result_timeout_seconds,
        )
        runs.append(run_data)

    success_count = sum(1 for r in runs if r["success"])
    failure_count = len(runs) - success_count
    total_duration = round(sum(r["duration_seconds"] for r in runs), 2)
    total_learner_delta = sum(r.get("learner_events_delta", 0) for r in runs)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "temporal_address": TEMPORAL_ADDRESS,
        "task_queue": TASK_QUEUE,
        "batch_size": len(projects),
        "result_timeout_seconds": result_timeout_seconds,
        "success_count": success_count,
        "failure_count": failure_count,
        "total_duration_seconds": total_duration,
        "total_learner_events_delta": total_learner_delta,
        "runs": runs,
    }

    metrics_dir = os.path.join("logs", "metrics")
    os.makedirs(metrics_dir, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_path = os.path.join(metrics_dir, f"todo_pilot_batch_{ts}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=True, indent=2)

    payload["metrics_log_path"] = output_path
    return payload


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch consecutive TodoPilot runs and write metrics log")
    parser.add_argument(
        "--result-timeout-seconds",
        type=float,
        default=None,
        help="Optional timeout per workflow result wait. If omitted, waits for full completion.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="Number of runs to execute (max 5 based on predefined project set).",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    batch_size = max(1, min(5, int(args.batch_size)))
    projects = BATCH_PROJECTS[:batch_size]
    result = asyncio.run(
        run_batch(
            projects=projects,
            result_timeout_seconds=args.result_timeout_seconds,
        )
    )
    print(json.dumps(result, ensure_ascii=True))
