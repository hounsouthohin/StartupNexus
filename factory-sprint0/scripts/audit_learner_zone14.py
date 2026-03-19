"""
Audit des standards Learner (ZONE_14 / learner_pattern) dans Qdrant.

Objectif:
- Lister les standards potentiellement pollués pendant la période regex-instable.
- Optionnellement les marquer `metadata.status=inactive` (mode apply).

Usage:
  python scripts/audit_learner_zone14.py --dry-run
  python scripts/audit_learner_zone14.py --apply --reason "regex false positives pre-IR"
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from qdrant_client import QdrantClient


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_suspect(payload: dict) -> tuple[bool, str]:
    """
    Heuristique conservative:
    - cible d'abord les points Learner dynamiques (category=learner_pattern)
    - ignore les hard-rules manuelles.
    """
    metadata = payload.get("metadata", {}) if isinstance(payload, dict) else {}
    if not isinstance(metadata, dict):
        metadata = {}
    category = str(metadata.get("category", "")).strip().lower()
    source = str(metadata.get("source", "")).strip().lower()
    outcome = str(metadata.get("outcome", "")).strip().lower()
    status = str(metadata.get("status", "active")).strip().lower()

    if status != "active":
        return False, "already_inactive"
    if category == "learner_pattern":
        return True, "category=learner_pattern"
    if source == "evaluator_agent" and outcome in {"learned_standard", "dynamic"}:
        return True, "evaluator_dynamic"
    return False, "not_targeted"


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit learner standards in Qdrant")
    parser.add_argument("--collection", default=os.getenv("QDRANT_COLLECTION_NAME", "factory_standards"))
    parser.add_argument("--qdrant-url", default=os.getenv("QDRANT_URL", "http://localhost:6333"))
    parser.add_argument("--apply", action="store_true", help="Applique metadata.status=inactive")
    parser.add_argument("--dry-run", action="store_true", help="Force mode simulation (par défaut)")
    parser.add_argument("--reason", default="regex false positives pre-IR migration")
    args = parser.parse_args()

    load_dotenv(dotenv_path=".env")
    dry_run = (not args.apply) or args.dry_run
    client = QdrantClient(url=args.qdrant_url)

    suspects: list[dict] = []
    scanned = 0
    offset = None
    while True:
        points, offset = client.scroll(
            collection_name=args.collection,
            limit=200,
            offset=offset,
            with_payload=True,
        )
        if not points:
            break
        for p in points:
            scanned += 1
            payload = p.payload or {}
            suspect, why = _is_suspect(payload)
            if not suspect:
                continue
            meta = payload.get("metadata", {}) if isinstance(payload, dict) else {}
            text = str(payload.get("text", ""))[:180]
            suspects.append(
                {
                    "id": str(p.id),
                    "reason": why,
                    "metadata": meta,
                    "category": meta.get("category"),
                    "source": meta.get("source"),
                    "outcome": meta.get("outcome"),
                    "status": meta.get("status", "active"),
                    "text_excerpt": text,
                }
            )
        if offset is None:
            break

    updated = 0
    if not dry_run and suspects:
        for s in suspects:
            existing_meta = s.get("metadata") if isinstance(s.get("metadata"), dict) else {}
            new_meta = {
                **existing_meta,
                "status": "inactive",
                "inactive_reason": args.reason,
                "inactive_at": _utc_now(),
                "audited_by": "audit_learner_zone14.py",
            }
            client.set_payload(
                collection_name=args.collection,
                points=[s["id"]],
                payload={"metadata": new_meta},
            )
            updated += 1

    report = {
        "timestamp": _utc_now(),
        "collection": args.collection,
        "qdrant_url": args.qdrant_url,
        "dry_run": dry_run,
        "scanned": scanned,
        "suspects": len(suspects),
        "updated": updated,
        "reason": args.reason,
        "items": suspects,
    }
    os.makedirs("logs/metrics", exist_ok=True)
    out_path = f"logs/metrics/learner_zone14_audit_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    mode = "DRY-RUN" if dry_run else "APPLY"
    print(f"[{mode}] scanned={scanned} suspects={len(suspects)} updated={updated}")
    print(f"report={out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
