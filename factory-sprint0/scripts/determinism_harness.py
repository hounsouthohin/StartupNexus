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
import copy
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# run_batch importé en lazy dans _build_projects / run_harness pour éviter
# de tirer temporalio au niveau module (empêche l'import des fonctions pures en tests).


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


def _get_effective_metric(run: dict[str, Any]) -> dict[str, Any]:
    """
    Source de vérité métriques:
    1) run_metric top-level (historique ancien),
    2) activity_results.dev_test.run_metric (payload activity complet).
    On fusionne en priorité sur le top-level pour préserver la rétro-compat.
    """
    top_metric = run.get("run_metric") or {}
    nested_metric = ((run.get("activity_results") or {}).get("dev_test") or {}).get("run_metric") or {}
    if not isinstance(top_metric, dict):
        top_metric = {}
    if not isinstance(nested_metric, dict):
        nested_metric = {}
    return {**nested_metric, **top_metric}


def _is_legitimate_gate(run: dict[str, Any]) -> bool:
    """
    Approximation opérationnelle de "gate légitime" (plan.md) avec les données runtime.
    """
    metric = _get_effective_metric(run)
    build_attempted = bool(metric.get("build_attempted", False))
    final_message = str(metric.get("final_message", ""))
    iterations = int(metric.get("iterations", 0) or 0)
    # Même source de vérité que _compute_metrics : metadata > run_metric
    _meta = (run.get("activity_results") or {}).get("dev_test", {}).get("metadata") or {}
    requirements_unmet = (
        _meta.get("requirements_unmet")
        or metric.get("requirements_unmet")
        or []
    )

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
    blocking_guard_counts: dict[str, int] = {}

    for run in runs:
        metric = _get_effective_metric(run)
        build_attempted = bool(metric.get("build_attempted", False))
        build_success = bool(metric.get("build_success", False))
        iterations = int(metric.get("iterations", 0) or 0)
        spec_coverage = float(metric.get("spec_coverage", 0.0) or 0.0)
        # Source de vérité : activity_results.dev_test.metadata (champs non exposés dans run_metric top-level).
        # Fallback run_metric pour rétrocompatibilité avec les anciens logs.
        _meta = (run.get("activity_results") or {}).get("dev_test", {}).get("metadata") or {}
        requirements_unmet = (
            _meta.get("requirements_unmet")
            or metric.get("requirements_unmet")
            or []
        )
        # gate_source : "content_guard" | "requirements" | "no_files" | ""
        # Tracé dans dev.py à chaque émission de NOT_BUILT_BY_GATE. Plus fiable que final_message
        # qui ne contient que l'enum, pas l'identité du gate.
        gate_source = (
            _meta.get("gate_source")
            or metric.get("gate_source")
            or ""
        )
        blocking_guard_id = (
            _meta.get("blocking_guard_id")
            or metric.get("blocking_guard_id")
            or ""
        )
        if blocking_guard_id:
            blocking_guard_counts[blocking_guard_id] = blocking_guard_counts.get(blocking_guard_id, 0) + 1
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

        # Divergence requirements : gate bloque (NOT_BUILT_BY_GATE) sans que ce soit un gate
        # structurel (content_guard) ni un gate requirements justifié (requirements_unmet non vide).
        # gate_source == "content_guard" ou "no_files" → gate légitime, pas une divergence.
        _is_structural_gate = gate_source in ("content_guard", "no_files")
        if (
            not build_attempted
            and "NOT_BUILT_BY_GATE" in final_message
            and not _is_structural_gate
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
        "blocking_guard_counts": blocking_guard_counts,
    }


def _load_baseline(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _to_host_metrics_path(raw_path: str | None) -> str | None:
    """
    Convertit un chemin de métriques potentiellement conteneur (/app/...) vers
    un chemin host lisible depuis PROJECT_ROOT.
    """
    if not raw_path:
        return None
    normalized = str(raw_path).replace("\\", "/")
    if normalized.startswith("/app/"):
        rel = normalized[len("/app/") :]
        return str((PROJECT_ROOT / rel).resolve())
    return str(Path(raw_path).resolve())


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
        baseline_coherence_f = float(baseline_coherence)
        deltas["final_status_coherence_rate_delta"] = round(
            metrics["final_status_coherence_rate"] - baseline_coherence_f, 3
        )
        # Si la baseline est déjà parfaite (1.0), un delta strictement positif est impossible.
        # On exige alors "pas de régression" au lieu de "amélioration stricte".
        if baseline_coherence_f >= 1.0:
            if metrics["final_status_coherence_rate"] < 1.0:
                failures.append("final_status_coherence_rate regressed below 1.0")
        elif deltas["final_status_coherence_rate_delta"] <= 0:
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


def _build_projects(runs: int) -> list[dict[str, Any]]:
    from scripts.run_batch import BATCH_PROJECTS  # lazy — évite temporalio hors conteneur
    reference = BATCH_PROJECTS[0]
    reference_brief = reference.get("brief", {})
    if not isinstance(reference_brief, dict) or not str(reference_brief.get("description", "")).strip():
        # Compat legacy (anciens catalogues en phrase)
        phrase = str(reference.get("phrase", "")).strip()
        reference_brief = {
            "description": phrase,
            "models": [],
            "pages": [],
            "routes": [],
        }
    return [
        {
            "project_name": f"determinism-{i:02d}",
            "brief": copy.deepcopy(reference_brief),
        }
        for i in range(1, runs + 1)
    ]


async def run_harness(runs: int, timeout_seconds: float | None) -> dict[str, Any]:
    from scripts.run_batch import run_batch  # lazy — évite temporalio hors conteneur
    projects = _build_projects(runs)
    batch = await run_batch(projects=projects, result_timeout_seconds=timeout_seconds)
    runs_data = batch.get("runs", [])
    metrics = _compute_metrics(runs_data)

    baseline_path = PROJECT_ROOT / "logs" / "metrics" / "baseline_kpis.json"
    baseline = _load_baseline(baseline_path)
    baseline_agg = baseline.get("aggregated", {}) if isinstance(baseline, dict) else {}

    ok, failures, deltas = _evaluate_thresholds(metrics, baseline_agg)
    _batch_metrics_log_path = batch.get("metrics_log_path")
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
        "batch_metrics_log_path": _batch_metrics_log_path,
        "batch_metrics_log_path_host": _to_host_metrics_path(_batch_metrics_log_path),
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
