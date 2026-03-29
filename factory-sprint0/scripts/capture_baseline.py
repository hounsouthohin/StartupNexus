"""
T000-BL — Capture baseline KPIs avant Sprint A.

Lance 5 runs consécutifs du même brief (personal-blog) via Temporal,
lit sorties.md après chaque run pour extraire les métriques granulaires
(build_attempted, iterations, root_cause_category, final_status coherence),
et produit logs/metrics/baseline_kpis.json.

Usage :
    python scripts/capture_baseline.py
    python scripts/capture_baseline.py --runs 5 --timeout 600
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from temporalio.client import Client

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from config.factory_config import TEMPORAL_ADDRESS

TASK_QUEUE = "factory-task-queue"

# Brief identique pour les 5 runs — cohérence baseline
BASELINE_BRIEF = {
    "description": "Blog CMS avec Clerk (auteur unique), pages publiques + dashboard protégé.",
    "models": [
        "Post { id String @id @default(cuid()), title String, content String, slug String @unique, published Boolean @default(false), authorId String, createdAt DateTime @default(now()) }",
    ],
    "pages": [
        {"path": "/", "auth": False},
        {"path": "/blog/[slug]", "auth": False},
        {"path": "/dashboard", "auth": True},
    ],
    "routes": [
        {"method": "PUT", "path": "/api/posts/[id]"},
    ],
}
BASELINE_PROJECT = "personal-blog"

# Chemin sorties.md — lu après chaque run pour extraire run_metric
SORTIES_PATH = Path(PROJECT_ROOT).parent / "sorties.md"


def _read_run_metric_from_sorties() -> dict[str, Any]:
    """
    Lit sorties.md et extrait le run_metric du dernier run.
    sorties.md est un fichier JSON-Lines : chaque ligne est un objet JSON.
    On cherche la ligne qui contient 'run_metric'.
    """
    if not SORTIES_PATH.exists():
        return {}
    try:
        run_metric = {}
        with open(SORTIES_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if isinstance(obj, dict) and "run_metric" in obj:
                        run_metric = obj["run_metric"]
                except json.JSONDecodeError:
                    continue
        return run_metric
    except Exception as e:
        print(f"  [WARN] Impossible de lire sorties.md : {e}")
        return {}


def _check_final_status_coherence(run_metric: dict, workflow_build_status: str | None) -> bool:
    """
    Vérifie que final_status est cohérent avec les events tools.

    Règle :
    - Si build_attempted=false → final_message doit contenir NOT_BUILT_BY_GATE ou BuildNotAttempted
    - Si build_success=true  → workflow build_status doit être SUCCESS ou PARTIAL
    - Si build_success=false et build_attempted=true → workflow build_status doit être BUILD_FAILED
    """
    if not run_metric:
        return False

    build_attempted = run_metric.get("build_attempted", False)
    build_success = run_metric.get("build_success", False)
    final_message = run_metric.get("final_message", "")

    if not build_attempted:
        # Le message final doit indiquer que le build n'a pas été tenté
        gate_keywords = ["BuildNotAttempted", "NOT_BUILT_BY_GATE", "pre-build gate"]
        return any(kw.lower() in final_message.lower() for kw in gate_keywords)

    if build_success:
        return workflow_build_status in ("SUCCESS", "PARTIAL")

    # build_attempted=true, build_success=false
    return workflow_build_status in ("BUILD_FAILED", "FAILED", None)


async def _run_one(
    client: Client,
    run_number: int,
    timeout_seconds: float | None,
) -> dict[str, Any]:
    workflow_id = f"baseline-run-{run_number:02d}-{uuid.uuid4().hex[:6]}"
    print(f"\n  [Run {run_number}] Démarrage workflow {workflow_id}")
    started_at = datetime.now(timezone.utc).isoformat()
    t0 = time.perf_counter()

    handle = await client.start_workflow(
        "TodoPilotWorkflow",
        {"brief": BASELINE_BRIEF, "project_name": BASELINE_PROJECT},
        id=workflow_id,
        task_queue=TASK_QUEUE,
    )

    workflow_status = None
    build_status = None
    error = None

    try:
        if timeout_seconds and timeout_seconds > 0:
            result = await asyncio.wait_for(handle.result(), timeout=timeout_seconds)
        else:
            result = await handle.result()

        if isinstance(result, dict):
            workflow_status = result.get("workflow_status")
            build_status = result.get("build_status")
        else:
            workflow_status = getattr(result, "workflow_status", None)
            build_status = getattr(result, "build_status", None)

    except asyncio.TimeoutError:
        error = f"timeout_after_{timeout_seconds}s"
        workflow_status = "TIMEOUT"
    except Exception as exc:
        error = str(exc)
        workflow_status = "ERROR"

    duration = round(time.perf_counter() - t0, 2)
    print(f"  [Run {run_number}] Terminé en {duration}s — build_status={build_status}")

    # Lecture sorties.md pour métriques granulaires
    run_metric = _read_run_metric_from_sorties()
    build_attempted = run_metric.get("build_attempted", None)
    iterations = run_metric.get("iterations", None)
    root_cause = run_metric.get("root_cause_category", None)
    build_success_metric = run_metric.get("build_success", None)
    semantic_violations = run_metric.get("semantic_violations", [])

    # Cohérence final_status
    final_status_coherent = _check_final_status_coherence(run_metric, build_status)

    record = {
        "run_number": run_number,
        "workflow_id": workflow_id,
        "started_at": started_at,
        "duration_seconds": duration,
        # Workflow-level
        "workflow_status": workflow_status,
        "build_status": build_status,
        "error": error,
        # Granulaire (depuis sorties.md run_metric)
        "build_attempted": build_attempted,
        "build_success": build_success_metric,
        "iterations": iterations,
        "root_cause_category": root_cause,
        "semantic_violations_count": len(semantic_violations) if isinstance(semantic_violations, list) else 0,
        # Cohérence
        "final_status_coherent": final_status_coherent,
    }

    status_line = (
        f"  build_attempted={build_attempted} | "
        f"build_success={build_success_metric} | "
        f"iterations={iterations} | "
        f"root_cause={root_cause} | "
        f"coherent={final_status_coherent}"
    )
    print(f"  [Run {run_number}] {status_line}")
    return record


def _aggregate(runs: list[dict]) -> dict[str, Any]:
    """Calcule les métriques agrégées sur l'ensemble des runs."""
    n = len(runs)
    if n == 0:
        return {}

    # build_attempted rate
    attempted_values = [r["build_attempted"] for r in runs if r["build_attempted"] is not None]
    build_attempted_rate = round(sum(attempted_values) / len(attempted_values), 3) if attempted_values else None

    # build_success rate
    success_values = [r["build_success"] for r in runs if r["build_success"] is not None]
    build_success_rate = round(sum(success_values) / len(success_values), 3) if success_values else None

    # avg_iterations
    iter_values = [r["iterations"] for r in runs if r["iterations"] is not None]
    avg_iterations = round(sum(iter_values) / len(iter_values), 1) if iter_values else None

    # final_status coherence rate
    coherence_values = [r["final_status_coherent"] for r in runs if r["final_status_coherent"] is not None]
    final_status_coherence_rate = round(sum(coherence_values) / len(coherence_values), 3) if coherence_values else None

    # root_cause distribution
    root_cause_dist: dict[str, int] = {}
    for r in runs:
        rc = r.get("root_cause_category") or "unknown"
        root_cause_dist[rc] = root_cause_dist.get(rc, 0) + 1

    # avg duration
    avg_duration = round(sum(r["duration_seconds"] for r in runs) / n, 1)

    # semantic violations avg
    sem_values = [r["semantic_violations_count"] for r in runs]
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
        # Seuils Sprint B (pour comparaison post-Sprint A)
        "targets_sprint_b": {
            "build_attempted_rate": 0.95,
            "build_success_rate": None,   # non ciblé Sprint B
            "final_status_coherence_rate": 1.0,
            "gate_divergence_rate": 0.0,
        },
    }


async def capture_baseline(runs_count: int = 5, timeout_seconds: float | None = None) -> dict[str, Any]:
    print("\n" + "=" * 60)
    print("T000-BL — CAPTURE BASELINE KPIs")
    print(f"Brief : {BASELINE_PROJECT} x{runs_count} runs identiques")
    print("=" * 60)

    client = await Client.connect(TEMPORAL_ADDRESS)
    runs: list[dict] = []

    for i in range(1, runs_count + 1):
        record = await _run_one(client, i, timeout_seconds)
        runs.append(record)

    aggregated = _aggregate(runs)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sprint_context": "baseline_avant_sprint_a",
        "project_name": BASELINE_PROJECT,
        "brief": BASELINE_BRIEF,
        "temporal_address": TEMPORAL_ADDRESS,
        "aggregated": aggregated,
        "runs": runs,
    }

    # Sauvegarde
    metrics_dir = Path(PROJECT_ROOT) / "logs" / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    out_path = metrics_dir / "baseline_kpis.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print("BASELINE CAPTURÉE")
    print("=" * 60)
    agg = aggregated
    print(f"  build_attempted_rate      : {agg.get('build_attempted_rate')}")
    print(f"  build_success_rate        : {agg.get('build_success_rate')}")
    print(f"  avg_iterations            : {agg.get('avg_iterations')}")
    print(f"  final_status_coherence    : {agg.get('final_status_coherence_rate')}")
    print(f"  avg_duration_seconds      : {agg.get('avg_duration_seconds')}")
    print(f"  root_cause_distribution   : {agg.get('root_cause_distribution')}")
    print(f"\n  Fichier : {out_path}")
    print("=" * 60 + "\n")

    return payload


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="T000-BL — Capture baseline KPIs sur N runs identiques (personal-blog)"
    )
    parser.add_argument("--runs", type=int, default=5, help="Nombre de runs (défaut: 5)")
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Timeout par run en secondes (défaut: sans limite)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    asyncio.run(capture_baseline(runs_count=args.runs, timeout_seconds=args.timeout))
