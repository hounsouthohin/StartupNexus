"""
Learner agent (shadow mode): analyse un run et propose des standards sans ecriture Qdrant.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List


def learner_agent(input_data: Dict[str, Any]) -> Dict[str, Any]:
    project_name = str(input_data.get("project_name", "unknown-project"))
    run_metrics = input_data.get("run_metrics", {}) if isinstance(input_data.get("run_metrics"), dict) else {}
    generated_files = input_data.get("generated_files", {}) if isinstance(input_data.get("generated_files"), dict) else {}

    total_files = len(generated_files)
    build_status = str(run_metrics.get("status", "PARTIAL")).upper()
    duration = float(run_metrics.get("total_duration_seconds", 0.0) or 0.0)

    suggestions: List[Dict[str, Any]] = []
    if total_files < 8:
        suggestions.append(
            {
                "text": (
                    "For low-file runs, enforce a minimum artifact checklist: package.json, middleware.ts, "
                    "app/layout.tsx, prisma/schema.prisma, at least one API route, and base test scaffold."
                ),
                "metadata": {
                    "category": "pattern",
                    "source": project_name,
                    "outcome": "observed",
                },
                "confidence_score": 0.72,
                "rationale": "Recurring low-file outputs correlate with incomplete delivery scope.",
                "human_review": "PENDING",
            }
        )

    if build_status != "SUCCESS":
        suggestions.append(
            {
                "text": (
                    "When build_status is not SUCCESS, require one mandatory remediation loop with explicit "
                    "readback of failing command stderr before marking run complete."
                ),
                "metadata": {
                    "category": "pattern",
                    "source": project_name,
                    "outcome": "inferred",
                },
                "confidence_score": 0.68,
                "rationale": "Build failures are frequent and often lack standardized recovery behavior.",
                "human_review": "PENDING",
            }
        )

    avg_confidence = round(
        sum(float(s.get("confidence_score", 0.0)) for s in suggestions) / len(suggestions), 3
    ) if suggestions else 0.0

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

