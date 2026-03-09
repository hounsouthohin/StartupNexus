"""
T011 — Determinism Harness (20 runs)

Lance N runs identiques, calcule les KPI bloquants et compare aux baseline_kpis.json.
Sort un rapport JSON dans logs/metrics/ et retourne un code non-zero si les seuils
formels ne sont pas atteints.

Usage:
    python scripts/determinism_harness.py
    python scripts/determinism_harness.py --runs 20 --timeout 900
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_batch import run_batch, BATCH_PROJECTS  # noqa: E402


def _check_final_status_coherence(run_metric: dict[str, Any], workflow_build_status: str | None) -> bool:
    """
    Cohérence final_status <-> events tools.
    Règles alignées avec scripts/capture_baseline.py.
    """
    if not run_metric:
        return False

    build_attempted = bool(run_metric.get("build_attempted", False))
    build_success = bool(run_metric.get("build_success", False))
    final_message = str(run_metric.get("final_message", ""))

    if not build_attempted:
        return "NOT_BUILT_BY_GATE" in final_message or "BuildNotAttempted" in final_message
    if build_success:
        return workflow_build_status in ("SUCCESS", "PARTIAL")
    return workflow_build_status in ("BUILD_FAILED", "FAILED", "SEMANTIC_VIOLATION", None)


def _is_legitimate_gate(run: dict[str, Any]) -> bool:
    """
    Approximation opérationnelle de "gate légitime" (plan.md) avec les données runtime.
    """
    metric = run.get("run_metric") or {}
    build_attempted = bool(metric.get("build_attempted", False))
    final_message = str(metric.get("final_message", ""))
    iterations = int(metric.get("iterations", 0) or 0)
    requirements_unmet = metric.get("requirements_unmet") or []

    if build_attempted:
        return False
    if "NOT_BUILT_BY_GATE" not in final_message:
        return False
    if iterations < 3:
        return False
    return isinstance(requirements_unmet, list) and len(requirements_unmet) > 0


def _compute_metrics(runs: list[dict[str, Any]]) -> dict[str, Any]:
    if not runs:
        return {}

    n = len(runs)
    coherent = 0
    raw_attempted = 0
    adj_n = 0
    adj_attempted = 0
    divergences = 0
    successes = 0
    iter_values: list[int] = []

    for run in runs:
        metric = run.get("run_metric") or {}
        build_attempted = bool(metric.get("build_attempted", False))
        build_success = bool(metric.get("build_success", False))
        iterations = int(metric.get("iterations", 0) or 0)
        spec_coverage = float(metric.get("spec_coverage", 0.0) or 0.0)
        requirements_unmet = metric.get("requirements_unmet") or []
        final_message = str(metric.get("final_message", ""))

        if _check_final_status_coherence(metric, run.get("build_status")):
            coherent += 1
        if build_attempted:
            raw_attempted += 1
            adj_attempted += 1
        if build_success:
            successes += 1
        iter_values.append(iterations)

        # Exclusion "gate légitime" du dénominateur ajusté
        if not _is_legitimate_gate(run):
            adj_n += 1

        # Proxy divergence: gate bloque mais requirements_unmet vide alors que coverage > 0
        if (
            not build_attempted
            and "NOT_BUILT_BY_GATE" in final_message
            and (not isinstance(requirements_unmet, list) or len(requirements_unmet) == 0)
            and spec_coverage > 0.0
        ):
            divergences += 1

    return {
        "runs_count": n,
        "build_attempted_rate_raw": round(raw_attempted / n, 3),
        "build_attempted_rate_adjusted": round(adj_attempted / max(adj_n, 1), 3),
        "build_success_rate": round(successes / n, 3),
        "avg_iterations": round(sum(iter_values) / n, 2),
        "final_status_coherence_rate": round(coherent / n, 3),
        "gate_divergence_rate": round(divergences / n, 3),
        "excluded_legitimate_gates": n - adj_n,
    }


def _load_baseline(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _evaluate_thresholds(metrics: dict[str, Any], baseline_agg: dict[str, Any]) -> tuple[bool, list[str], dict[str, Any]]:
    failures: list[str] = []
    deltas: dict[str, Any] = {}

    if metrics.get("build_attempted_rate_adjusted", 0.0) < 0.95:
        failures.append("build_attempted_rate_adjusted < 0.95")
    if metrics.get("final_status_coherence_rate", 0.0) < 1.0:
        failures.append("final_status_coherence_rate < 1.0")
    if metrics.get("gate_divergence_rate", 1.0) > 0.0:
        failures.append("gate_divergence_rate > 0.0")

    # Delta vs baseline (si baseline exploitable)
    baseline_attempt = baseline_agg.get("build_attempted_rate")
    baseline_coherence = baseline_agg.get("final_status_coherence_rate")
    baseline_avg_iter = baseline_agg.get("avg_iterations")

    if baseline_attempt is not None:
        deltas["build_attempted_rate_delta"] = round(
            metrics["build_attempted_rate_raw"] - float(baseline_attempt), 3
        )
        if deltas["build_attempted_rate_delta"] <= 0:
            failures.append("delta build_attempted_rate <= 0 vs baseline")
    else:
        failures.append("baseline build_attempted_rate manquant (null)")

    if baseline_coherence is not None:
        deltas["final_status_coherence_rate_delta"] = round(
            metrics["final_status_coherence_rate"] - float(baseline_coherence), 3
        )
        if deltas["final_status_coherence_rate_delta"] <= 0:
            failures.append("delta final_status_coherence_rate <= 0 vs baseline")
    else:
        failures.append("baseline final_status_coherence_rate manquant (null)")

    if baseline_avg_iter is not None:
        deltas["avg_iterations_delta"] = round(
            float(baseline_avg_iter) - metrics["avg_iterations"], 3
        )
        if deltas["avg_iterations_delta"] <= 0:
            failures.append("delta avg_iterations <= 0 vs baseline (pas d'amélioration)")
    else:
        failures.append("baseline avg_iterations manquant (null)")

    return len(failures) == 0, failures, deltas


def _build_projects(runs: int) -> list[dict[str, str]]:
    reference = BATCH_PROJECTS[0]
    return [
        {
            "project_name": f"determinism-{i:02d}",
            "phrase": reference["phrase"],
        }
        for i in range(1, runs + 1)
    ]


async def run_harness(runs: int, timeout_seconds: float | None) -> dict[str, Any]:
    projects = _build_projects(runs)
    batch = await run_batch(projects=projects, result_timeout_seconds=timeout_seconds)
    runs_data = batch.get("runs", [])
    metrics = _compute_metrics(runs_data)

    baseline_path = PROJECT_ROOT / "logs" / "metrics" / "baseline_kpis.json"
    baseline = _load_baseline(baseline_path)
    baseline_agg = baseline.get("aggregated", {}) if isinstance(baseline, dict) else {}

    ok, failures, deltas = _evaluate_thresholds(metrics, baseline_agg)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "harness": {
            "runs_requested": runs,
            "timeout_seconds": timeout_seconds,
        },
        "metrics": metrics,
        "baseline_path": str(baseline_path),
        "baseline_aggregated": baseline_agg,
        "deltas_vs_baseline": deltas,
        "pass": ok,
        "failures": failures,
        "batch_metrics_log_path": batch.get("metrics_log_path"),
    }

    out_dir = PROJECT_ROOT / "logs" / "metrics"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = out_dir / f"determinism_harness_{ts}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    payload["harness_log_path"] = str(out_path)
    return payload


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="T011 — Determinism Harness bloquant")
    parser.add_argument("--runs", type=int, default=20, help="Nombre de runs identiques (défaut: 20)")
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Timeout par run (secondes). Par défaut: sans limite.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    result = asyncio.run(run_harness(runs=max(1, int(args.runs)), timeout_seconds=args.timeout))
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit(0 if result.get("pass") else 1)
