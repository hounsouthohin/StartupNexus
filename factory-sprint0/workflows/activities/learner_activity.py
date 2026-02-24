from __future__ import annotations

import os
import sys
from typing import Any, Dict

from temporalio import activity
from temporalio.exceptions import ApplicationError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from scripts.validate_contracts import validate_input, validate_output


@activity.defn(name="learner_activity")
async def learner_activity(input_data: Dict[str, Any], run_id: str = "") -> Dict[str, Any]:
    """
    Activity dediee Learner (shadow mode).
    Analyse le run, genere des suggestions et logue en shadow.
    """
    try:
        from agents.shared_tools import set_run_id, set_stack_id
        set_run_id(run_id)
        set_stack_id(str(input_data.get("stack_id", "nextjs-clerk-prisma")))
    except Exception:
        pass
    input_data["run_id"] = run_id
    try:
        validate_input("learner_agent", input_data)
    except Exception as exc:
        raise ApplicationError("LEARNER_INPUT_VALIDATION_FAILED", str(exc))

    try:
        from agents.learner import learner_agent
        from agents.shared_tools import _write_learner_event
    except Exception as exc:
        raise ApplicationError("LEARNER_IMPORT_FAILURE", str(exc))

    try:
        result = learner_agent(input_data)
        validate_output("learner_agent", result)

        summary = result.get("analysis_summary", {}) if isinstance(result, dict) else {}
        _write_learner_event(
            event_type="learner_analysis",
            payload={
                "project_name": str(input_data.get("project_name", "unknown-project")),
                "success": True,
                "patterns_detected": int(summary.get("patterns_detected", 0) or 0),
                "total_suggestions": int(summary.get("total_suggestions", 0) or 0),
                "avg_confidence": float(summary.get("avg_confidence", 0.0) or 0.0),
            },
            run_id=input_data.get("run_id", ""),
        )
        return result
    except ApplicationError:
        raise
    except Exception as exc:
        activity.logger.error(f"Learner activity failed: {exc}", exc_info=True)
        raise ApplicationError("LEARNER_EXECUTION_FAILED", str(exc))
