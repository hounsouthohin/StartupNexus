"""
Déclenche 5 runs TodoPilot consécutifs et collecte les métriques.
Écrit un fichier de synthèse dans logs/metrics/.
"""

from __future__ import annotations

import asyncio
import argparse
import contextlib
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from temporalio.client import Client

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from config.factory_config import TEMPORAL_ADDRESS
from workflows.todo_pilot_workflow import TodoPilotWorkflow


TASK_QUEUE = "factory-task-queue"
_LOG_ROOT = os.path.join(os.getenv("FACTORY_LOG_DIR", "/app/logs"))
LEARNER_LOG_PATH = os.path.join(_LOG_ROOT, "shadow", "learner_shadow_log.json")
SORTIES_PATH = Path(PROJECT_ROOT).parent / "sorties.md"
MAX_SORTIES_STR_LEN = 1200

BATCH_PROJECTS: List[Dict[str, str]] = [
    {
        "project_name": "personal-blog",
        "phrase": (
            "Blog CMS avec Clerk (auteur unique)\n"
            "- Modele Prisma : Post { id String @id @default(cuid()), title, content, slug String @unique, published Boolean @default(false), createdAt, authorId String }\n"
            "- Pages : / (liste publique), /blog/[slug] (article), /dashboard (protege)\n"
            "- API Route : PUT /api/posts/[id] (toggle published, auth requise)"
        ),
    },
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


def _append_to_sorties(entry: Dict[str, Any]) -> None:
    """Append one JSONL record to sorties.md (best-effort)."""
    try:
        SORTIES_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(SORTIES_PATH, "a", encoding="utf-8") as f:
            # default=str évite qu'un objet non JSON-native bloque l'append.
            f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    except Exception as exc:
        # Non-bloquant: ne jamais casser le batch pour une erreur de log local.
        print(f"[WARN] Impossible d'écrire dans {SORTIES_PATH}: {exc}")


def _safe_metrics_output_path(ts: str) -> str:
    """
    Retourne un chemin de log metrics inscriptible.
    Priorité:
      1) FACTORY_LOG_DIR (ou /app/logs par défaut) si inscriptible
      2) fallback local PROJECT_ROOT/logs
    """
    primary_dir = os.path.join(_LOG_ROOT, "metrics")
    try:
        os.makedirs(primary_dir, exist_ok=True)
        return os.path.join(primary_dir, f"todo_pilot_batch_{ts}.json")
    except Exception:
        fallback_dir = os.path.join(PROJECT_ROOT, "logs", "metrics")
        os.makedirs(fallback_dir, exist_ok=True)
        return os.path.join(fallback_dir, f"todo_pilot_batch_{ts}.json")


def _truncate_str(value: Any, max_len: int = MAX_SORTIES_STR_LEN) -> Any:
    if not isinstance(value, str):
        return value
    if len(value) <= max_len:
        return value
    return value[:max_len] + f"... [truncated {len(value) - max_len} chars]"


def _compact_run_metric(metric: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(metric, dict):
        return {}
    compact = {
        "build_attempted": metric.get("build_attempted"),
        "build_attempts": metric.get("build_attempts"),
        "build_success": metric.get("build_success"),
        "iterations": metric.get("iterations"),
        "final_message": metric.get("final_message"),
        "root_cause_category": metric.get("root_cause_category"),
        "spec_coverage": metric.get("spec_coverage"),
        "requirements_met": metric.get("requirements_met"),
        "requirements_total": metric.get("requirements_total"),
        "tests_passed": metric.get("tests_passed"),
        "semantic_violations": metric.get("semantic_violations", []),
        "last_failed_command": metric.get("last_failed_command", ""),
        "last_build_error": _truncate_str(metric.get("last_build_error", "")),
        "error": _truncate_str(metric.get("error", "")),
    }
    return compact


def _compact_activity_result(activity_name: str, result: Any) -> Any:
    if not isinstance(result, dict):
        return _truncate_str(result)

    if activity_name == "architect_activity":
        return {
            "spec_validation_status": result.get("spec_validation_status"),
            "requirements_count": len(result.get("requirements", []) or []),
            "spec_unmatched_requirements": result.get("spec_unmatched_requirements", []),
        }

    if activity_name == "dev_test_activity":
        metadata = result.get("metadata", {}) if isinstance(result.get("metadata", {}), dict) else {}
        return {
            "success": result.get("success"),
            "final_message": result.get("final_message")
            or (result.get("dev_output", {}) if isinstance(result.get("dev_output", {}), dict) else {}).get("final_message"),
            "run_metric": _compact_run_metric(result.get("run_metric", {}) if isinstance(result.get("run_metric", {}), dict) else {}),
            "metadata": {
                "total_files": metadata.get("total_files"),
                "dev_files_count": metadata.get("dev_files_count"),
                "test_files_count": metadata.get("test_files_count"),
                "spec_coverage": metadata.get("spec_coverage"),
                "requirements_met": metadata.get("requirements_met"),
                "requirements_total": metadata.get("requirements_total"),
                "tests_passed": metadata.get("tests_passed"),
            },
            "semantic_violations_count": len(result.get("semantic_violations", []) or []),
        }

    if activity_name == "qa_activity":
        e2e = result.get("e2e_tests", {}) if isinstance(result.get("e2e_tests", {}), dict) else {}
        return {"tests_count": len(e2e)}

    if activity_name == "github_activity":
        return {"repo_url": result.get("repo_url", "N/A"), "pr_url": result.get("pr_url", "N/A")}

    if activity_name == "learner_activity":
        if "suggestions_generated" in result:
            return {"suggestions_generated": result.get("suggestions_generated", 0)}
        suggestions = result.get("suggestions", [])
        return {"suggestions_generated": len(suggestions) if isinstance(suggestions, list) else 0}

    # Fallback générique: trim des strings profondes.
    compact: Dict[str, Any] = {}
    for k, v in result.items():
        if isinstance(v, str):
            compact[k] = _truncate_str(v)
        elif isinstance(v, list):
            compact[k] = v[:10]
        else:
            compact[k] = v
    return compact


def _compact_activity_results_map(activity_results: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(activity_results, dict):
        return {}
    out: Dict[str, Any] = {}
    for name, payload in activity_results.items():
        out[name] = _compact_activity_result(name, payload)
    return out


def _event_time_to_iso(event: Any) -> str:
    try:
        return event.event_time.ToDatetime().isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()


async def _decode_payloads(client: Client, payloads: Any) -> Any:
    if payloads is None:
        return None
    try:
        decoded = await client.data_converter.decode_wrapper(payloads)
        if len(decoded) == 1:
            return decoded[0]
        return decoded
    except Exception:
        return None


async def _stream_activity_events_to_sorties(
    *,
    client: Client,
    handle: Any,
    workflow_id: str,
    project_name: str,
    stop_event: asyncio.Event,
) -> None:
    """
    Stream des événements d'activités depuis l'historique Temporal.
    Écrit une ligne JSONL dans sorties.md à chaque fin d'activité.
    """
    last_seen_event_id = 0
    scheduled_event_to_activity: Dict[int, str] = {}

    while True:
        try:
            history = await handle.fetch_history()
            events = list(getattr(history, "events", []))

            workflow_terminal = False
            for event in events:
                event_id = int(getattr(event, "event_id", 0))
                if event_id <= last_seen_event_id:
                    continue
                last_seen_event_id = event_id

                if event.HasField("activity_task_scheduled_event_attributes"):
                    attrs = event.activity_task_scheduled_event_attributes
                    activity_name = getattr(getattr(attrs, "activity_type", None), "name", "") or getattr(attrs, "activity_id", "")
                    if activity_name:
                        scheduled_event_to_activity[event_id] = activity_name
                    continue

                if event.HasField("activity_task_completed_event_attributes"):
                    attrs = event.activity_task_completed_event_attributes
                    scheduled_id = int(getattr(attrs, "scheduled_event_id", 0))
                    activity_name = scheduled_event_to_activity.get(scheduled_id, f"scheduled_event_{scheduled_id}")
                    result = await _decode_payloads(client, getattr(attrs, "result", None))
                    compact_result = _compact_activity_result(activity_name, result)
                    _append_to_sorties(
                        {
                            "logged_at": datetime.now(timezone.utc).isoformat(),
                            "event_time": _event_time_to_iso(event),
                            "source": "scripts/run_batch.py",
                            "event_type": "activity_completed",
                            "workflow_id": workflow_id,
                            "project_name": project_name,
                            "activity_name": activity_name,
                            "scheduled_event_id": scheduled_id,
                            "activity_result": compact_result,
                        }
                    )
                    continue

                if event.HasField("activity_task_failed_event_attributes"):
                    attrs = event.activity_task_failed_event_attributes
                    scheduled_id = int(getattr(attrs, "scheduled_event_id", 0))
                    activity_name = scheduled_event_to_activity.get(scheduled_id, f"scheduled_event_{scheduled_id}")
                    _append_to_sorties(
                        {
                            "logged_at": datetime.now(timezone.utc).isoformat(),
                            "event_time": _event_time_to_iso(event),
                            "source": "scripts/run_batch.py",
                            "event_type": "activity_failed",
                            "workflow_id": workflow_id,
                            "project_name": project_name,
                            "activity_name": activity_name,
                            "scheduled_event_id": scheduled_id,
                            "failure": str(getattr(attrs, "failure", "")),
                        }
                    )
                    continue

                if event.HasField("activity_task_timed_out_event_attributes"):
                    attrs = event.activity_task_timed_out_event_attributes
                    scheduled_id = int(getattr(attrs, "scheduled_event_id", 0))
                    activity_name = scheduled_event_to_activity.get(scheduled_id, f"scheduled_event_{scheduled_id}")
                    _append_to_sorties(
                        {
                            "logged_at": datetime.now(timezone.utc).isoformat(),
                            "event_time": _event_time_to_iso(event),
                            "source": "scripts/run_batch.py",
                            "event_type": "activity_timed_out",
                            "workflow_id": workflow_id,
                            "project_name": project_name,
                            "activity_name": activity_name,
                            "scheduled_event_id": scheduled_id,
                            "failure": str(getattr(attrs, "failure", "")),
                        }
                    )
                    continue

                if event.HasField("activity_task_canceled_event_attributes"):
                    attrs = event.activity_task_canceled_event_attributes
                    scheduled_id = int(getattr(attrs, "scheduled_event_id", 0))
                    activity_name = scheduled_event_to_activity.get(scheduled_id, f"scheduled_event_{scheduled_id}")
                    details = await _decode_payloads(client, getattr(attrs, "details", None))
                    _append_to_sorties(
                        {
                            "logged_at": datetime.now(timezone.utc).isoformat(),
                            "event_time": _event_time_to_iso(event),
                            "source": "scripts/run_batch.py",
                            "event_type": "activity_canceled",
                            "workflow_id": workflow_id,
                            "project_name": project_name,
                            "activity_name": activity_name,
                            "scheduled_event_id": scheduled_id,
                            "details": details,
                        }
                    )
                    continue

                # Terminal workflow event: on peut arrêter le streaming.
                if (
                    event.HasField("workflow_execution_completed_event_attributes")
                    or event.HasField("workflow_execution_failed_event_attributes")
                    or event.HasField("workflow_execution_timed_out_event_attributes")
                    or event.HasField("workflow_execution_terminated_event_attributes")
                    or event.HasField("workflow_execution_canceled_event_attributes")
                ):
                    workflow_terminal = True

            if workflow_terminal:
                break
            if stop_event.is_set():
                # Un dernier sweep a déjà été fait dans cette itération.
                break
            await asyncio.sleep(1.0)
        except Exception as exc:
            print(f"[WARN] Streaming activity events failed for {workflow_id}: {exc}")
            if stop_event.is_set():
                break
            await asyncio.sleep(1.0)


async def _run_one(
    client: Client,
    phrase: str,
    project_name: str,
    result_timeout_seconds: float | None = None,
    sanity_mode: bool = False,
) -> Dict[str, Any]:
    workflow_id = f"todo-pilot-{project_name}-{uuid.uuid4().hex[:8]}"
    started_at = datetime.now(timezone.utc).isoformat()
    t0 = time.perf_counter()
    learner_before = _learner_events_count()

    handle = await client.start_workflow(
        TodoPilotWorkflow.run,
        {"phrase": phrase, "project_name": project_name, "sanity_mode": bool(sanity_mode)},
        id=workflow_id,
        task_queue=TASK_QUEUE,
    )
    stream_stop_event = asyncio.Event()
    stream_task = asyncio.create_task(
        _stream_activity_events_to_sorties(
            client=client,
            handle=handle,
            workflow_id=workflow_id,
            project_name=project_name,
            stop_event=stream_stop_event,
        )
    )

    workflow_status: str | None = None
    build_status: str | None = None
    build_success: bool | None = None
    workflow_error_message: str | None = None
    activity_results: Dict[str, Any] = {}
    run_metric: Dict[str, Any] = {}

    try:
        if result_timeout_seconds and result_timeout_seconds > 0:
            result = await asyncio.wait_for(handle.result(), timeout=result_timeout_seconds)
        else:
            result = await handle.result()
        workflow_success = True
        error = None
        if isinstance(result, dict):
            workflow_status = result.get("workflow_status")
            build_status = result.get("build_status")
            workflow_error_message = result.get("error_message")
            activity_results = result.get("activity_results") or {}
        else:
            workflow_status = getattr(result, "workflow_status", None)
            build_status = getattr(result, "build_status", None)
            workflow_error_message = getattr(result, "error_message", None)
            activity_results = getattr(result, "activity_results", {}) or {}
        if workflow_status is not None:
            workflow_success = workflow_status == "COMPLETED"
        if build_status is not None:
            # strict_success : uniquement SUCCESS (spec_coverage >= 50%)
            # usable_success : SUCCESS ou PARTIAL (build fonctionnel, couverture partielle)
            build_success = build_status in ("SUCCESS", "PARTIAL")
        if isinstance(activity_results, dict):
            run_metric = activity_results.get("dev_test", {}).get("run_metric", {}) or {}
            run_metric = _compact_run_metric(run_metric)
    except TimeoutError:
        result = ""
        workflow_success = False
        error = f"timeout_after_{result_timeout_seconds}_seconds"
    except Exception as exc:
        result = ""
        workflow_success = False
        error = str(exc)
    finally:
        stream_stop_event.set()
        with contextlib.suppress(Exception):
            await asyncio.wait_for(stream_task, timeout=10.0)

    duration_seconds = round(time.perf_counter() - t0, 2)
    learner_after = _learner_events_count()

    strict_success = build_status == "SUCCESS"
    usable_success = build_status in ("SUCCESS", "PARTIAL")
    run_record = {
        "workflow_id": workflow_id,
        "run_id": getattr(handle, "first_execution_run_id", None),
        "project_name": project_name,
        "phrase": phrase,
        "started_at": started_at,
        "duration_seconds": duration_seconds,
        "workflow_success": workflow_success,
        "build_success": build_success,
        "strict_success": strict_success,
        "usable_success": usable_success,
        "workflow_status": workflow_status,
        "build_status": build_status,
        "error": error,
        "workflow_error_message": workflow_error_message,
        "learner_events_before": learner_before,
        "learner_events_after": learner_after,
        "learner_events_delta": learner_after - learner_before,
        "result_excerpt": str(result)[:400],
        "activity_results": activity_results,
        "run_metric": run_metric,
    }

    sorties_entry = {
        "logged_at": datetime.now(timezone.utc).isoformat(),
        "source": "scripts/run_batch.py",
        "workflow_id": run_record["workflow_id"],
        "run_id": run_record["run_id"],
        "project_name": run_record["project_name"],
        "workflow_status": run_record["workflow_status"],
        "build_status": run_record["build_status"],
        "error": run_record["error"],
        "workflow_error_message": run_record["workflow_error_message"],
        "activity_results": _compact_activity_results_map(activity_results),
        "run_metric": run_metric,
    }
    _append_to_sorties(sorties_entry)
    return run_record


async def run_batch(
    projects: List[Dict[str, str]],
    result_timeout_seconds: float | None = None,
    sanity_mode: bool = False,
) -> Dict[str, Any]:
    client = await Client.connect(TEMPORAL_ADDRESS)
    runs: List[Dict[str, Any]] = []

    for item in projects:
        run_data = await _run_one(
            client=client,
            phrase=item["phrase"],
            project_name=item["project_name"],
            result_timeout_seconds=result_timeout_seconds,
            sanity_mode=sanity_mode,
        )
        runs.append(run_data)

    workflow_success_count = sum(1 for r in runs if r["workflow_success"])
    workflow_failure_count = len(runs) - workflow_success_count
    build_success_count = sum(1 for r in runs if r.get("build_status") == "SUCCESS")
    build_partial_count = sum(1 for r in runs if r.get("build_status") == "PARTIAL")
    build_failure_count = sum(1 for r in runs if r.get("build_status") in ("BUILD_FAILED", "SEMANTIC_VIOLATION"))
    build_unknown_count = sum(1 for r in runs if r.get("build_status") is None)
    strict_success_count = build_success_count
    usable_success_count = build_success_count + build_partial_count
    total_duration = round(sum(r["duration_seconds"] for r in runs), 2)
    total_learner_delta = sum(r.get("learner_events_delta", 0) for r in runs)

    # ── Quality Dashboard (métriques stables par batch) ────────────────────
    # spec_validation_status : extrait du build_status proxy
    # (SEMANTIC_VIOLATION → spec dégradée détectée à l'exécution)
    semantic_violation_count = sum(1 for r in runs if r.get("build_status") == "SEMANTIC_VIOLATION")
    degraded_spec_count = sum(
        1 for r in runs
        if r.get("workflow_status") == "FAILED_UNRECOVERABLE"
        and "SPEC_INVALID" in str(r.get("workflow_error_message") or "")
    )
    # build_mutation_count : approximé par NOT_RUN vs réel (mutation strictement bloquée depuis Phase 1)
    not_run_count = sum(1 for r in runs if r.get("build_status") == "NOT_RUN")
    # usable_ratio : proxy requirements_mappable_met_ratio (avant ajout spec_coverage dans output)
    usable_ratio = round(usable_success_count / len(runs), 3) if runs else 0.0

    quality_dashboard = {
        "spec_validation_status_counts": {
            "degraded_spec_gate_blocked": degraded_spec_count,
            "semantic_violation_at_dev": semantic_violation_count,
            "ok_or_partial": len(runs) - degraded_spec_count - semantic_violation_count,
        },
        "requirements_mappable_met_ratio": usable_ratio,
        "build_not_run_count": not_run_count,
        "strict_success_rate": round(strict_success_count / len(runs), 3) if runs else 0.0,
        "usable_success_rate": usable_ratio,
    }

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "temporal_address": TEMPORAL_ADDRESS,
        "task_queue": TASK_QUEUE,
        "batch_size": len(projects),
        "result_timeout_seconds": result_timeout_seconds,
        "sanity_mode": bool(sanity_mode),
        "workflow_success_count": workflow_success_count,
        "workflow_failure_count": workflow_failure_count,
        "build_success_count": build_success_count,
        "build_partial_count": build_partial_count,
        "build_failure_count": build_failure_count,
        "build_unknown_count": build_unknown_count,
        "strict_success_count": strict_success_count,
        "usable_success_count": usable_success_count,
        # Compat legacy keys (deprecated)
        "success_count": workflow_success_count,
        "failure_count": workflow_failure_count,
        "total_duration_seconds": total_duration,
        "total_learner_events_delta": total_learner_delta,
        "quality_dashboard": quality_dashboard,
        "runs": runs,
    }

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_path = _safe_metrics_output_path(ts)
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=True, indent=2)
    except PermissionError:
        # Cas fréquent en exécution host Windows: /app/logs non inscriptible.
        fallback_dir = os.path.join(PROJECT_ROOT, "logs", "metrics")
        os.makedirs(fallback_dir, exist_ok=True)
        output_path = os.path.join(fallback_dir, f"todo_pilot_batch_{ts}.json")
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
        help="Number of runs to execute.",
    )
    parser.add_argument(
        "--sanity-mode",
        action="store_true",
        help="Active le mode sanity: arrêt du workflow après dev_test_activity (skip QA/GitHub/Learner).",
    )
    parser.add_argument(
        "--briefs",
        type=str,
        default="",
        help="Chemin vers un JSON de briefs: [{\"project_name\": \"...\", \"phrase\": \"...\"}, ...].",
    )
    return parser.parse_args()


def _build_cli_projects(batch_size: int) -> List[Dict[str, str]]:
    """
    Construit une liste de projets de taille arbitraire à partir du set de référence.
    Si batch_size > len(BATCH_PROJECTS), on recycle les briefs en suffixant les noms.
    """
    if batch_size <= len(BATCH_PROJECTS):
        return BATCH_PROJECTS[:batch_size]

    out: List[Dict[str, str]] = []
    for i in range(batch_size):
        base = BATCH_PROJECTS[i % len(BATCH_PROJECTS)]
        out.append(
            {
                "project_name": f"{base['project_name']}-{i + 1:02d}",
                "phrase": base["phrase"],
            }
        )
    return out


def _load_projects_from_briefs_file(path: str) -> List[Dict[str, str]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list) or not data:
        raise ValueError("--briefs doit contenir une liste non vide d'objets")

    projects: List[Dict[str, str]] = []
    for i, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"--briefs item #{i} invalide: dict attendu")
        project_name = str(item.get("project_name", "")).strip()
        phrase = str(item.get("phrase", "")).strip()
        if not project_name or not phrase:
            raise ValueError(f"--briefs item #{i}: project_name et phrase sont obligatoires")
        projects.append({"project_name": project_name, "phrase": phrase})
    return projects


if __name__ == "__main__":
    args = _parse_args()
    if args.briefs:
        projects = _load_projects_from_briefs_file(args.briefs)
    else:
        batch_size = max(1, int(args.batch_size))
        projects = _build_cli_projects(batch_size)
    result = asyncio.run(
        run_batch(
            projects=projects,
            result_timeout_seconds=args.result_timeout_seconds,
            sanity_mode=bool(args.sanity_mode),
        )
    )
    print(json.dumps(result, ensure_ascii=True))
