"""
workflows/activities/learner_activity.py — Sprint 3.

Wraps agents/learner.py en Temporal activity (best-effort).
Appelé en fin de run TodoPilotWorkflow après QA et GitHub.
"""
from temporalio import activity
from typing import Dict, Any


@activity.defn(name="learner_activity")
async def learner_activity(run_id: str = "") -> Dict[str, Any]:
    """
    Analyse le shadow log et génère des StandardSuggestion.
    Best-effort : une erreur ne bloque pas le workflow.
    """
    try:
        from agents.shared_tools import set_run_id
        set_run_id(run_id)
    except Exception:
        pass

    try:
        from agents.learner import run_learner_activity
        result = run_learner_activity(run_id=run_id)
        activity.logger.info(
            f"[learner_activity] {result.get('suggestions_generated', 0)} suggestion(s) générées"
        )
        return result
    except Exception as e:
        activity.logger.warning(f"[learner_activity] Erreur (best-effort): {e}")
        return {"suggestions_generated": 0, "suggestions": [], "error": str(e)}
