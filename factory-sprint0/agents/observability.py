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

def _append_rag_usage_event(
    *,
    query: str,
    k: int,
    cache_hit: bool,
    run_id: str = "",
    doc_ids: list | None = None,
    scores: list | None = None,
    snippet: str = "",
    error: str | None = None,
) -> None:
    """
    Ecrit une trace d'usage RAG exploitable en audit (jsonl).
    Inclut les IDs Qdrant réels, les scores et un snippet du premier résultat.
    """
    try:
        metrics_dir = LOG_ROOT / "metrics"
        metrics_dir.mkdir(parents=True, exist_ok=True)
        path = metrics_dir / "rag_usage.jsonl"

        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "run_id": run_id,
            "agent": "dev_tool_rag_search",
            "query": query,
            "k": int(k),
            "cache_hit": bool(cache_hit),
            "result_count": len(doc_ids or []),
            "doc_ids": doc_ids or [],
            "scores": scores or [],
            "snippet": snippet,
            "error": error,
        }
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception as log_err:
        logger.warning(f"RAG metrics logging failed: {log_err}")


# --- Web search usage metrics ---

def _append_web_search_event(
    *,
    run_id: str = "",
    context: str,
    trigger_error: str = "",
    query: str,
    found: bool,
    snippet: str = "",
    retry_count: int = 0,
    error: str | None = None,
) -> None:
    """
    Écrit une trace d'usage web search dans logs/metrics/web_search_usage.jsonl.

    Permet de corréler a posteriori :
      trigger_error → query → found → snippet → retry_count
    Et de juger si la recherche a aidé : si found=True et que l'erreur disparaît
    au tour suivant (plus dans stale_error_keys), elle a probablement aidé.
    """
    try:
        metrics_dir = LOG_ROOT / "metrics"
        metrics_dir.mkdir(parents=True, exist_ok=True)
        path = metrics_dir / "web_search_usage.jsonl"

        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "run_id": run_id,
            "context": context,
            "trigger_error": trigger_error[:200],
            "query": query,
            "found": found,
            "snippet": snippet[:300] if snippet else "",
            "retry_count": retry_count,
            "error": error,
        }
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception as log_err:
        logger.warning(f"Web search metrics logging failed: {log_err}")


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
