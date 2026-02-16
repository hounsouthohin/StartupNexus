"""
Lit patterns_report.json et enrichit la collection Qdrant factory_standards.
Écrit un log d'enrichissement dans logs/metrics/.
"""

from __future__ import annotations

import argparse
import json
import os
import hashlib
from datetime import datetime, timezone
from uuid import UUID

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct


DEFAULT_PATTERNS_REPORT = os.path.join("logs", "shadow", "patterns_report.json")
QDRANT_COLLECTION_NAME = "factory_standards"
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")


def text_to_uuid(text: str) -> str:
    hash_bytes = hashlib.md5(text.encode("utf-8")).digest()
    return str(UUID(bytes=hash_bytes))


def _load_patterns(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _standard_text_from_pattern(pattern: dict) -> str:
    signature = pattern.get("signature", "unknown_signature")
    occurrences = pattern.get("occurrences", 0)
    recommendation = pattern.get("recommendation", "")
    return (
        "Factory standard learned from recurring failures. "
        f"Pattern: {signature}. "
        f"Observed occurrences: {occurrences}. "
        f"Recommended action: {recommendation}"
    )


def _write_metrics_log(payload: dict) -> str:
    metrics_dir = os.path.join("logs", "metrics")
    os.makedirs(metrics_dir, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join(metrics_dir, f"qdrant_enrichment_{ts}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=True, indent=2)
    return path


def enrich_qdrant(patterns_report_path: str = DEFAULT_PATTERNS_REPORT) -> dict:
    load_dotenv(dotenv_path=".env")
    report = _load_patterns(patterns_report_path)
    patterns = report.get("patterns", [])

    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    client = QdrantClient(url=QDRANT_URL)

    inserted = []
    failed = []

    for pattern in patterns:
        try:
            text = _standard_text_from_pattern(pattern)
            vector = embeddings.embed_query(text)
            point_id = text_to_uuid(text)

            payload = {
                "text": text,
                "metadata": {
                    "category": "learner_pattern",
                    "tech": "cross-agent",
                    "version": "dynamic",
                    "source": "evaluator_agent",
                    "outcome": "learned_standard",
                    "pattern_id": pattern.get("pattern_id"),
                    "signature": pattern.get("signature"),
                    "occurrences": pattern.get("occurrences"),
                },
            }

            client.upsert(
                collection_name=QDRANT_COLLECTION_NAME,
                points=[PointStruct(id=point_id, vector=vector, payload=payload)],
                wait=True,
            )

            inserted.append(
                {
                    "point_id": point_id,
                    "pattern_id": pattern.get("pattern_id"),
                    "signature": pattern.get("signature"),
                }
            )
        except Exception as exc:
            failed.append(
                {
                    "pattern_id": pattern.get("pattern_id"),
                    "signature": pattern.get("signature"),
                    "error": str(exc),
                }
            )

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "patterns_report_path": patterns_report_path,
        "collection": QDRANT_COLLECTION_NAME,
        "total_patterns": len(patterns),
        "inserted_count": len(inserted),
        "failed_count": len(failed),
        "inserted": inserted,
        "failed": failed,
    }
    metrics_log_path = _write_metrics_log(result)
    result["metrics_log_path"] = metrics_log_path
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Enrich Qdrant with learned standards from patterns_report.json")
    parser.add_argument(
        "--patterns-report",
        default=DEFAULT_PATTERNS_REPORT,
        help="Path to patterns_report.json",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    output = enrich_qdrant(patterns_report_path=args.patterns_report)
    print(json.dumps(output, ensure_ascii=True))
