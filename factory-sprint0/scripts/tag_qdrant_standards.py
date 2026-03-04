"""
Tag existing Qdrant standards with stack/status/version (Sprint 3 Phase C).

Usage:
  python scripts/tag_qdrant_standards.py
"""

from __future__ import annotations

import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient

load_dotenv(dotenv_path=".env")

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "factory_standards")


def _infer_stack(text: str) -> str:
    t = (text or "").lower()
    if any(k in t for k in ("clerk", "nextjs", "next.js", "prisma")):
        return "nextjs-clerk-prisma"
    return "global"


def main() -> int:
    client = QdrantClient(url=QDRANT_URL)
    tagged = 0
    total = 0

    offset = None
    while True:
        points, offset = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=200,
            offset=offset,
            with_payload=True,
        )
        if not points:
            break
        for p in points:
            total += 1
            payload = p.payload or {}
            text = payload.get("text") or payload.get("page_content") or ""
            stack = _infer_stack(text)

            # Merger dans le dict metadata imbriqué (fiable quelle que soit la version Qdrant)
            existing_metadata = payload.get("metadata", {})
            if not isinstance(existing_metadata, dict):
                existing_metadata = {}
            new_metadata = {
                **existing_metadata,
                "stack": stack,
                "status": "active",
                "version": "1.0",
            }
            client.set_payload(
                collection_name=COLLECTION_NAME,
                payload={"metadata": new_metadata},
                points=[p.id],
            )
            tagged += 1
            print(f"  [{total}] stack={stack!r} — {text[:70].strip()!r}")
        if offset is None:
            break

    print(f"\nTagged {tagged}/{total} standards in '{COLLECTION_NAME}'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
