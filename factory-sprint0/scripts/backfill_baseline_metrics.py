"""
Backfill baseline_kpis.json sans relancer les runs.

Lit les workflow_id déjà présents dans logs/metrics/baseline_kpis.json,
récupère run_metric depuis l'historique Temporal (dev_test_activity),
et recalcule les agrégats.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

from temporalio.client import Client

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.factory_config import TEMPORAL_ADDRESS  # noqa: E402


def _check_final_status_coherence(run_metric: dict[str, Any], workflow_build_status: str | None) -> bool:
    if not run_metric:
        return False
    build_attempted = bool(run_metric.get("build_attempted", False))
    build_success = bool(run_metric.get("build_success", False))
    final_message = str(run_metric.get("final_message", ""))
    if not build_attempted:
        gate_keywords = ["BuildNotAttempted", "NOT_BUILT_BY_GATE", "pre-build gate"]
        return any(kw.lower() in final_message.lower() for kw in gate_keywords)
    if build_success:
        return workflow_build_status in ("SUCCESS", "PARTIAL")
    return workflow_build_status in ("BUILD_FAILED", "FAILED", "SEMANTIC_VIOLATION", None)


def _aggregate(runs: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(runs)
    if n == 0:
        return {}

    attempted_values = [r["build_attempted"] for r in runs if r.get("build_attempted") is not None]
    build_attempted_rate = round(sum(attempted_values) / len(attempted_values), 3) if attempted_values else None

    success_values = [r["build_success"] for r in runs if r.get("build_success") is not None]
    build_success_rate = round(sum(success_values) / len(success_values), 3) if success_values else None

    iter_values = [r["iterations"] for r in runs if r.get("iterations") is not None]
    avg_iterations = round(sum(iter_values) / len(iter_values), 1) if iter_values else None

    coherence_values = [r["final_status_coherent"] for r in runs if r.get("final_status_coherent") is not None]
    final_status_coherence_rate = round(sum(coherence_values) / len(coherence_values), 3) if coherence_values else None

    root_cause_dist: dict[str, int] = {}
    for r in runs:
        rc = r.get("root_cause_category") or "unknown"
        root_cause_dist[rc] = root_cause_dist.get(rc, 0) + 1

    avg_duration = round(sum(float(r.get("duration_seconds", 0.0)) for r in runs) / n, 1)
    sem_values = [int(r.get("semantic_violations_count", 0)) for r in runs]
    avg_semantic_violations = round(sum(sem_values) / n, 1)

    return {
        "runs_count": n,
        "build_attempted_rate": build_attempted_rate,
        "build_success_rate": build_success_rate,
        "avg_iterations": avg_iterations,
        "final_status_coherence_rate": final_status_coherence_rate,
        "root_cause_distribution": root_cause_dist,
        "avg_duration_seconds": avg_duration,
        "avg_semantic_violations": avg_semantic_violations,
        "targets_sprint_b": {
            "build_attempted_rate": 0.95,
            "build_success_rate": None,
            "final_status_coherence_rate": 1.0,
            "gate_divergence_rate": 0.0,
        },
    }


async def _extract_run_metric(client: Client, workflow_id: str) -> dict[str, Any]:
    """
    Cherche dev_test_activity dans l'historique et extrait run_metric.
    """
    handle = client.get_workflow_handle(workflow_id=workflow_id)
    history = await handle.fetch_history()
    events = list(getattr(history, "events", []))

    scheduled_names: dict[int, str] = {}
    for event in events:
        if event.HasField("activity_task_scheduled_event_attributes"):
            attrs = event.activity_task_scheduled_event_attributes
            name = getattr(getattr(attrs, "activity_type", None), "name", "")
            scheduled_names[int(event.event_id)] = name

        if event.HasField("activity_task_completed_event_attributes"):
            attrs = event.activity_task_completed_event_attributes
            scheduled_id = int(getattr(attrs, "scheduled_event_id", 0))
            activity_name = scheduled_names.get(scheduled_id, "")
            if activity_name != "dev_test_activity":
                continue
            decoded = await client.data_converter.decode_wrapper(getattr(attrs, "result", None))
            if not decoded:
                return {}
            result = decoded[0]
            if isinstance(result, dict):
                return result.get("run_metric", {}) or {}
            return {}
    return {}


async def backfill(path: Path) -> tuple[int, int]:
    if not path.exists():
        raise FileNotFoundError(path)

    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    runs = payload.get("runs", [])
    if not isinstance(runs, list) or not runs:
        return 0, 0

    client = await Client.connect(TEMPORAL_ADDRESS)
    updated = 0

    for run in runs:
        wf_id = run.get("workflow_id")
        if not wf_id:
            continue
        metric = await _extract_run_metric(client, wf_id)
        if not metric:
            continue
        run["build_attempted"] = metric.get("build_attempted")
        run["build_success"] = metric.get("build_success")
        run["iterations"] = metric.get("iterations")
        run["root_cause_category"] = metric.get("root_cause_category")
        sem = metric.get("semantic_violations", [])
        run["semantic_violations_count"] = len(sem) if isinstance(sem, list) else 0
        run["final_status_coherent"] = _check_final_status_coherence(metric, run.get("build_status"))
        updated += 1

    payload["aggregated"] = _aggregate(runs)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return updated, len(runs)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backfill baseline_kpis.json depuis Temporal history")
    parser.add_argument(
        "--path",
        default=str(PROJECT_ROOT / "logs" / "metrics" / "baseline_kpis.json"),
        help="Chemin du baseline_kpis.json",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    p = Path(args.path)
    u, t = asyncio.run(backfill(p))
    print(f"Backfill terminé: {u}/{t} runs enrichis -> {p}")
