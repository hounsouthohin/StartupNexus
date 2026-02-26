"""
KPI validation script — mesure stack_fallback_used == 0 par run_id.
Usage:
  python scripts/validate_stack_health.py
  python scripts/validate_stack_health.py <run_id>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def check_stack_fallback_kpi(run_id: str = "") -> dict:
    """
    Lit les events learner et compte les stack_fallback_used.
    run_id vide = analyse globale.
    """
    log_path = Path("logs/shadow/learner_shadow_log.json")
    if not log_path.exists():
        return {"status": "NO_DATA", "fallback_count": 0, "details": []}

    try:
        data = json.loads(log_path.read_text(encoding="utf-8"))
        events = data.get("suggested_standards", []) if isinstance(data, dict) else data
        if not isinstance(events, list):
            events = []
    except Exception as e:
        return {"status": "ERROR", "error": str(e), "fallback_count": 0}

    fallback_events = [
        e for e in events
        if isinstance(e, dict)
        and e.get("event_type") == "stack_fallback_used"
        and (not run_id or e.get("run_id") == run_id)
    ]

    return {
        "kpi_stack_fallback_used": len(fallback_events),
        "status": "OK" if len(fallback_events) == 0 else "FAIL",
        "run_id_filter": run_id or "all",
        "details": fallback_events,
    }


if __name__ == "__main__":
    run_id = sys.argv[1] if len(sys.argv) > 1 else ""
    result = check_stack_fallback_kpi(run_id)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result["status"] in ("OK", "NO_DATA") else 1)
