"""
Phase 1 helper: cartographie des causes d'echec et erreurs TypeScript.

Analyse:
- logs/metrics/todo_pilot_batch_*.json
- logs/metrics/run_reports/run_report_*.json
- snapshots/*.json (optionnel, best-effort)

Sortie:
- logs/metrics/phase1_error_map.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
METRICS_DIR = PROJECT_ROOT / "logs" / "metrics"
RUN_REPORTS_DIR = METRICS_DIR / "run_reports"
OUTPUT_PATH = METRICS_DIR / "phase1_error_map.json"

TS_ERROR_WITH_FILE_RE = re.compile(
    r"(?P<file>[^\s\n()]+?\.(?:ts|tsx|js|jsx))\((?P<line>\d+),(?P<col>\d+)\):\s*error\s*TS(?P<code>\d{4,5}):\s*(?P<msg>[^\n\r]+)",
    re.IGNORECASE,
)
TS_CODE_RE = re.compile(r"\bTS(?P<code>\d{4,5})\b")


@dataclass
class RunSignal:
    source: str
    source_file: str
    project_name: str
    run_id: str
    workflow_id: str
    build_status: str
    build_success: bool
    root_cause_category: str
    last_build_error: str
    tsc_ran: bool | None
    tsc_ok: bool | None
    tsc_errors_count: int | None


def _safe_load_json(path: Path) -> dict[str, Any] | None:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception:
        return None
    return None


def _extract_ts_errors(error_text: str) -> list[dict[str, Any]]:
    if not error_text:
        return []

    items: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()

    for match in TS_ERROR_WITH_FILE_RE.finditer(error_text):
        code = str(match.group("code"))
        file_path = str(match.group("file"))
        line = str(match.group("line"))
        message = str(match.group("msg")).strip()
        key = (code, file_path, line, message[:120])
        if key in seen:
            continue
        seen.add(key)
        items.append(
            {
                "code": code,
                "file": file_path,
                "line": int(line),
                "message": message,
            }
        )

    # Fallback: TS code present without file(line,col) pattern.
    if not items:
        for match in TS_CODE_RE.finditer(error_text):
            code = str(match.group("code"))
            key = (code, "<unknown>", "0", "")
            if key in seen:
                continue
            seen.add(key)
            items.append(
                {
                    "code": code,
                    "file": "<unknown>",
                    "line": 0,
                    "message": "",
                }
            )

    return items


def _collect_from_batch(batch_path: Path) -> list[RunSignal]:
    payload = _safe_load_json(batch_path)
    if not payload:
        return []

    out: list[RunSignal] = []
    runs = payload.get("runs", [])
    if not isinstance(runs, list):
        return out

    for run in runs:
        if not isinstance(run, dict):
            continue
        run_metric = run.get("run_metric", {})
        if not isinstance(run_metric, dict):
            run_metric = {}

        last_build_error = str(run_metric.get("last_build_error", "") or "")
        if not last_build_error:
            last_build_error = str(run.get("error", "") or "")

        build_success = bool(run_metric.get("build_success", False))
        if "build_success" in run and run.get("build_success") is not None:
            build_success = bool(run.get("build_success"))

        tsc_errors_count = run_metric.get("tsc_errors_count_by_activity")
        if tsc_errors_count is not None:
            try:
                tsc_errors_count = int(tsc_errors_count)
            except Exception:
                tsc_errors_count = None

        out.append(
            RunSignal(
                source="batch",
                source_file=batch_path.name,
                project_name=str(run.get("project_name", "") or ""),
                run_id=str(run.get("run_id", "") or ""),
                workflow_id=str(run.get("workflow_id", "") or ""),
                build_status=str(run.get("build_status", "") or ""),
                build_success=build_success,
                root_cause_category=str(run_metric.get("root_cause_category", "unknown") or "unknown"),
                last_build_error=last_build_error,
                tsc_ran=(
                    bool(run_metric.get("tsc_ran_by_activity"))
                    if run_metric.get("tsc_ran_by_activity") is not None
                    else None
                ),
                tsc_ok=(
                    bool(run_metric.get("tsc_ok_by_activity"))
                    if run_metric.get("tsc_ok_by_activity") is not None
                    else None
                ),
                tsc_errors_count=tsc_errors_count,
            )
        )
    return out


def _collect_from_run_report(report_path: Path) -> RunSignal | None:
    payload = _safe_load_json(report_path)
    if not payload:
        return None

    tsc_errors_count = payload.get("tsc_errors_count")
    if tsc_errors_count is not None:
        try:
            tsc_errors_count = int(tsc_errors_count)
        except Exception:
            tsc_errors_count = None

    return RunSignal(
        source="run_report",
        source_file=report_path.name,
        project_name=str(payload.get("project_name", "") or ""),
        run_id=str(payload.get("run_id", "") or ""),
        workflow_id=str(payload.get("workflow_id", "") or ""),
        build_status="SUCCESS" if bool(payload.get("build_success", False)) else "BUILD_FAILED",
        build_success=bool(payload.get("build_success", False)),
        root_cause_category=str(payload.get("root_cause_category", "unknown") or "unknown"),
        last_build_error=str(payload.get("last_build_error", "") or payload.get("error", "") or ""),
        tsc_ran=bool(payload.get("tsc_ran")) if payload.get("tsc_ran") is not None else None,
        tsc_ok=bool(payload.get("tsc_ok")) if payload.get("tsc_ok") is not None else None,
        tsc_errors_count=tsc_errors_count,
    )


def _count_snapshot_files() -> tuple[int, list[str]]:
    candidates = [
        PROJECT_ROOT / "snapshots",
        PROJECT_ROOT / "logs" / "snapshots",
    ]
    found: list[str] = []
    count = 0
    for folder in candidates:
        if not folder.exists() or not folder.is_dir():
            continue
        files = list(folder.glob("*.json"))
        if files:
            found.append(str(folder))
            count += len(files)
    return count, found


def _summarize(signals: list[RunSignal], max_examples: int = 25) -> dict[str, Any]:
    total_runs = len(signals)
    if total_runs == 0:
        return {
            "summary": {
                "total_runs": 0,
                "build_success_rate": 0.0,
            },
            "examples": [],
        }

    failed = [s for s in signals if not s.build_success]
    root_cause_counter: Counter[str] = Counter(s.root_cause_category for s in failed)
    unknown_failed = sum(1 for s in failed if s.root_cause_category == "unknown")

    ts_code_counter: Counter[str] = Counter()
    ts_file_counter: Counter[str] = Counter()
    ts_project_counter: Counter[str] = Counter()
    anomaly_count = 0
    examples: list[dict[str, Any]] = []

    for s in failed:
        ts_errors = _extract_ts_errors(s.last_build_error)
        has_ts_code = len(ts_errors) > 0
        if has_ts_code:
            for item in ts_errors:
                code = str(item["code"])
                file_path = str(item["file"])
                ts_code_counter[code] += 1
                if file_path and file_path != "<unknown>":
                    ts_file_counter[file_path] += 1
                ts_project_counter[s.project_name or "<unknown_project>"] += 1

        # Signal anomaly: build logs carry TS code but post-mortem tsc says 0.
        if has_ts_code and s.tsc_ran and (s.tsc_errors_count == 0):
            anomaly_count += 1

        if len(examples) < max_examples:
            examples.append(
                {
                    "project_name": s.project_name,
                    "run_id": s.run_id,
                    "workflow_id": s.workflow_id,
                    "source": s.source,
                    "source_file": s.source_file,
                    "build_status": s.build_status,
                    "root_cause_category": s.root_cause_category,
                    "ts_codes": sorted({f"TS{e['code']}" for e in ts_errors}),
                    "ts_files": sorted({str(e["file"]) for e in ts_errors if str(e["file"]) != "<unknown>"}),
                    "tsc_ran": s.tsc_ran,
                    "tsc_ok": s.tsc_ok,
                    "tsc_errors_count": s.tsc_errors_count,
                    "last_build_error_excerpt": (s.last_build_error or "")[:500],
                }
            )

    build_success_count = total_runs - len(failed)
    build_success_rate = round(build_success_count / total_runs, 3)
    unknown_rate_on_failed = round((unknown_failed / len(failed)), 3) if failed else 0.0

    return {
        "summary": {
            "total_runs": total_runs,
            "failed_runs": len(failed),
            "build_success_count": build_success_count,
            "build_success_rate": build_success_rate,
            "unknown_root_cause_count": unknown_failed,
            "unknown_root_cause_rate_on_failed": unknown_rate_on_failed,
            "root_cause_distribution": dict(root_cause_counter.most_common()),
            "ts_error_codes_distribution": {f"TS{k}": v for k, v in ts_code_counter.most_common()},
            "top_failing_files": dict(ts_file_counter.most_common(15)),
            "projects_with_most_ts_errors": dict(ts_project_counter.most_common(15)),
            "signal_anomaly_tsc_zero_with_ts_logs": anomaly_count,
        },
        "examples": examples,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyse les echecs Phase 1 depuis les logs metrics/run_reports.")
    parser.add_argument(
        "--max-batches",
        type=int,
        default=12,
        help="Nombre max de fichiers todo_pilot_batch_*.json a analyser (les plus recents).",
    )
    parser.add_argument(
        "--max-examples",
        type=int,
        default=25,
        help="Nombre max d'exemples d'echec a inclure dans le JSON de sortie.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    batch_files = sorted(METRICS_DIR.glob("todo_pilot_batch_*.json"))
    if args.max_batches > 0:
        batch_files = batch_files[-args.max_batches :]

    run_reports = sorted(RUN_REPORTS_DIR.glob("run_report_*.json")) if RUN_REPORTS_DIR.exists() else []

    signals: list[RunSignal] = []
    for path in batch_files:
        signals.extend(_collect_from_batch(path))

    # Add run_report records only if run_id not already present in batch signals.
    existing_run_ids = {s.run_id for s in signals if s.run_id}
    for path in run_reports:
        signal = _collect_from_run_report(path)
        if not signal:
            continue
        if signal.run_id and signal.run_id in existing_run_ids:
            continue
        signals.append(signal)

    summary_payload = _summarize(signals, max_examples=max(1, args.max_examples))
    snapshot_count, snapshot_dirs = _count_snapshot_files()

    output_payload: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "phase": "phase1",
        "inputs": {
            "metrics_dir": str(METRICS_DIR),
            "batch_files_analyzed": [p.name for p in batch_files],
            "run_reports_analyzed_count": len(run_reports),
            "snapshot_files_detected": snapshot_count,
            "snapshot_dirs": snapshot_dirs,
            "total_signals_analyzed": len(signals),
        },
        "analysis": summary_payload["summary"],
        "examples": summary_payload["examples"],
        "recommendations": [
            "Prioriser les regles prompt pour TS7006/TS2339/TS2345 sur les fichiers les plus frequents.",
            "Corriger _classify_root_cause pour reduire unknown_root_cause_rate.",
            "Injecter les erreurs tsc post-mortem dans la tentative suivante si build echoue encore.",
        ],
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(output_payload, f, ensure_ascii=False, indent=2)

    print(f"[phase1] signals={len(signals)}")
    print(f"[phase1] output={OUTPUT_PATH}")
    print(
        "[phase1] build_success_rate=",
        output_payload["analysis"].get("build_success_rate", 0.0),
        "| unknown_rate_failed=",
        output_payload["analysis"].get("unknown_root_cause_rate_on_failed", 0.0),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
