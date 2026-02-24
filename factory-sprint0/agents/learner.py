"""
Learner agent (shadow mode): analyse un run et propose des standards sans ecriture Qdrant.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def _load_shadow_events() -> List[Dict[str, Any]]:
    path = Path("logs/shadow/learner_shadow_log.json")
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    events = data.get("suggested_standards", [])
    return events if isinstance(events, list) else []


def _normalize_event(raw: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "run_id": raw.get("run_id", ""),
        "event_type": raw.get("event_type") or raw.get("metric") or "",
        "payload": raw.get("payload") or raw.get("value") or {},
        "timestamp": raw.get("timestamp") or "",
    }


def _load_rag_events_for_run(run_id: str) -> List[Dict[str, Any]]:
    migrated = Path("logs/metrics/rag_usage.migrated.jsonl")
    path = migrated if migrated.exists() else Path("logs/metrics/rag_usage.jsonl")
    if not path.exists() or not run_id:
        return []
    events = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                evt = json.loads(line)
            except Exception:
                continue
            if evt.get("run_id") == run_id:
                events.append(evt)
    except Exception:
        return []
    return events


def _guess_category(text: str) -> str:
    t = text.lower()
    if "clerk" in t:
        return "clerk"
    if "prisma" in t:
        return "prisma"
    if "jest" in t or "test" in t:
        return "testing"
    if "next" in t or "middleware" in t:
        return "nextjs"
    return "pattern"


def _extract_patch_keywords(patch_payload: Dict[str, Any]) -> List[str]:
    keywords: List[str] = []
    for k, v in (patch_payload or {}).items():
        if isinstance(v, str):
            keywords.extend([v.lower(), k.lower()])
    return [kw for kw in keywords if kw]


def _rag_event_text(evt: Dict[str, Any]) -> str:
    parts: List[str] = []
    for key in ("snippet", "query"):
        val = evt.get(key)
        if isinstance(val, str):
            parts.append(val.lower())
    # Legacy docs field support
    legacy_docs = evt.get("docs")
    if isinstance(legacy_docs, list):
        for d in legacy_docs:
            if isinstance(d, dict):
                for k in ("category", "tech", "snippet", "source"):
                    val = d.get(k)
                    if isinstance(val, str):
                        parts.append(val.lower())
    return " ".join(parts)


def _classify_trigger_context(patch_payload: Dict[str, Any], rag_events: List[Dict[str, Any]]) -> str:
    if not rag_events:
        return "tool_guardrail"
    keywords = _extract_patch_keywords(patch_payload)
    if not keywords:
        return "tool_guardrail"
    for evt in rag_events:
        text = _rag_event_text(evt)
        if any(kw in text for kw in keywords):
            return "rag_retrieved"
    return "tool_guardrail"


def _suggestion_from_patch(
    project_name: str,
    patch_payload: Dict[str, Any],
    trigger_context: str,
    confidence: float,
) -> Dict[str, Any]:
    patch_type = str(patch_payload.get("patch") or patch_payload.get("type") or "patch").lower()
    target = str(
        patch_payload.get("package_name")
        or patch_payload.get("from")
        or patch_payload.get("file")
        or patch_payload.get("field")
        or "unknown"
    )
    action = "INTERDIT" if any(x in patch_type for x in ("removed", "invalid", "conflict", "deprecated")) else "OBLIGATOIRE"
    text = (
        f"{action}: Corriger automatiquement '{target}' lorsque '{patch_type}' est détecté. "
        f"Contexte: {trigger_context}. Impact: éviter échec build ou test."
    )
    return {
        "text": text,
        "metadata": {
            "category": _guess_category(text),
            "source": project_name,
            "outcome": "observed",
            "trigger_context": trigger_context,
            "patch_type": patch_type,
            "target": target,
        },
        "confidence_score": round(confidence, 3),
        "rationale": f"Patch appliqué par tool ({patch_type}) sur {target}.",
        "human_review": "PENDING",
    }


def _suggestion_from_build_failure(project_name: str, error_signature: str) -> Dict[str, Any]:
    text = (
        f"INTERDIT: Générer du code déclenchant l'erreur build '{error_signature}'. "
        f"Ajouter un anti-pattern si la signature réapparaît sur plusieurs runs."
    )
    return {
        "text": text,
        "metadata": {
            "category": "pattern",
            "source": project_name,
            "outcome": "observed",
            "error_signature": error_signature,
        },
        "confidence_score": 0.7,
        "rationale": f"Build failed with signature: {error_signature}.",
        "human_review": "PENDING",
    }


def _write_suggestions_file(suggestions: List[Dict[str, Any]]) -> None:
    path = Path("logs/shadow/learner_suggestions.json")
    try:
        existing: List[Dict[str, Any]] = []
        if path.exists():
            existing = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(existing, list):
                existing = []
        existing.extend(suggestions)
        path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        return


def learner_agent(input_data: Dict[str, Any]) -> Dict[str, Any]:
    project_name = str(input_data.get("project_name", "unknown-project"))
    run_metrics = input_data.get("run_metrics", {}) if isinstance(input_data.get("run_metrics"), dict) else {}
    generated_files = input_data.get("generated_files", {}) if isinstance(input_data.get("generated_files"), dict) else {}
    run_id = str(input_data.get("run_id", "") or "")

    total_files = len(generated_files)
    build_status = str(run_metrics.get("status", "PARTIAL")).upper()
    duration = float(run_metrics.get("total_duration_seconds", 0.0) or 0.0)

    raw_events = [_normalize_event(e) for e in _load_shadow_events()]
    run_events = [e for e in raw_events if run_id and e.get("run_id") == run_id] if run_id else []
    rag_events = _load_rag_events_for_run(run_id) if run_id else []

    patch_events = [e for e in run_events if e.get("event_type") == "tool_patch_applied"]
    build_failures = [e for e in run_events if e.get("event_type") == "build_failed"]

    patch_type_counts: Dict[str, int] = {}
    for e in patch_events:
        payload = e.get("payload", {}) if isinstance(e.get("payload", {}), dict) else {}
        pt = str(payload.get("patch") or payload.get("type") or "patch").lower()
        patch_type_counts[pt] = patch_type_counts.get(pt, 0) + 1

    suggestions: List[Dict[str, Any]] = []
    for e in patch_events:
        payload = e.get("payload", {}) if isinstance(e.get("payload", {}), dict) else {}
        trigger = _classify_trigger_context(payload, rag_events)
        pt = str(payload.get("patch") or payload.get("type") or "patch").lower()
        confidence = 0.75 if patch_type_counts.get(pt, 0) >= 2 else 0.6
        suggestions.append(_suggestion_from_patch(project_name, payload, trigger, confidence))

    for e in build_failures:
        payload = e.get("payload", {}) if isinstance(e.get("payload", {}), dict) else {}
        error_sig = str(payload.get("error_signature", "unknown"))
        suggestions.append(_suggestion_from_build_failure(project_name, error_sig))

    # Fallback: si aucune suggestion, conserver un signal faible sans casser le schema.
    if not suggestions and total_files < 8:
        suggestions.append(
            {
                "text": (
                    "OBLIGATOIRE: En runs à faible nombre de fichiers, générer au minimum "
                    "package.json, app/layout.tsx, middleware.ts, schema.prisma et un endpoint API."
                ),
                "metadata": {
                    "category": "pattern",
                    "source": project_name,
                    "outcome": "observed",
                },
                "confidence_score": 0.55,
                "rationale": "Sorties faibles en fichiers corrèlent avec build incomplets.",
                "human_review": "PENDING",
            }
        )

    avg_confidence = round(
        sum(float(s.get("confidence_score", 0.0)) for s in suggestions) / len(suggestions), 3
    ) if suggestions else 0.0

    _write_suggestions_file(suggestions)

    return {
        "mode": "shadow",
        "project_name": project_name,
        "suggested_standards": suggestions,
        "analysis_summary": {
            "patterns_detected": len(suggestions),
            "total_suggestions": len(suggestions),
            "avg_confidence": avg_confidence,
            "categories_covered": sorted(
                {str(s.get("metadata", {}).get("category", "pattern")) for s in suggestions}
            ) if suggestions else [],
        },
        "shadow_log_entry": {
            "run_timestamp": datetime.now(timezone.utc).isoformat(),
            "project_name": project_name,
            "suggestions_count": len(suggestions),
        },
        "metadata": {
            "total_files": total_files,
            "build_status": build_status,
            "duration_seconds": duration,
        },
    }
