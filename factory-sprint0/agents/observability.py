"""
Observability helpers: logger, RAG usage metrics, learner shadow log.
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

LOG_ROOT = Path(os.getenv("FACTORY_LOG_DIR", "/app/logs"))
SHADOW_DIR = LOG_ROOT / "shadow"


# --- Logger ---

class Logger:
    def info(self, message):
        print(f"[INFO] {message}")

    def warning(self, message):
        print(f"[WARNING] {message}")

    def error(self, message):
        print(f"[ERROR] {message}")


logger = Logger()


# --- RAG usage metrics ---


# --- Web search usage metrics ---


# --- Learner shadow log ---

def _write_learner_event(event_type: str, payload: dict, run_id: str = "") -> None:
    log_path = SHADOW_DIR / "learner_shadow_log.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        log = json.loads(log_path.read_text(encoding="utf-8"))
    except Exception:
        log = {"total_suggestions": 0, "suggested_standards": []}

    log.setdefault("suggested_standards", [])
    log.setdefault("total_suggestions", 0)

    log["suggested_standards"].append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "run_id": run_id,
            "event_type": event_type,
            "payload": payload,
        }
    )
    log["total_suggestions"] += 1

    log_path.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")
