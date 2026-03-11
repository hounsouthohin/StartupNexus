"""
Export des standards Qdrant pour audit externe.

Usage:
  python docs/external_audit_pack/export_qdrant_snapshot.py \
    --output docs/external_audit_pack/out/qdrant_standards_snapshot.json
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from qdrant_client import QdrantClient


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export active standards from Qdrant")
    parser.add_argument(
        "--output",
        required=True,
        help="Output JSON file path",
    )
    parser.add_argument(
        "--stack",
        default="nextjs-clerk-prisma",
        help="Stack filter value (metadata.stack)",
    )
    parser.add_argument(
        "--include-global",
        action="store_true",
        default=True,
        help="Include metadata.stack=global",
    )
    parser.add_argument(
        "--collection",
        default=os.getenv("QDRANT_COLLECTION_NAME", "factory_standards"),
        help="Qdrant collection name",
    )
    parser.add_argument(
        "--url",
        default=os.getenv("QDRANT_URL", "http://localhost:6333"),
        help="Qdrant URL",
    )
    return parser.parse_args()


def _is_active_for_stack(payload: dict, stack: str, include_global: bool) -> bool:
    meta = payload.get("metadata") if isinstance(payload, dict) else {}
    if not isinstance(meta, dict):
        return False
    if str(meta.get("status", "")).lower() != "active":
        return False
    point_stack = str(meta.get("stack", "")).strip()
    if point_stack == stack:
        return True
    if include_global and point_stack == "global":
        return True
    return False


def main() -> int:
    load_dotenv(dotenv_path=".env")
    args = _parse_args()

    client = QdrantClient(url=args.url)
    offset = None
    exported = []

    while True:
        points, offset = client.scroll(
            collection_name=args.collection,
            limit=256,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        if not points:
            break

        for p in points:
            payload = p.payload or {}
            if not _is_active_for_stack(payload, args.stack, args.include_global):
                continue
            exported.append(
                {
                    "id": str(p.id),
                    "text": payload.get("text") or payload.get("page_content") or "",
                    "metadata": payload.get("metadata", {}),
                }
            )

        if offset is None:
            break

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qdrant_url": args.url,
        "collection": args.collection,
        "stack": args.stack,
        "include_global": args.include_global,
        "count": len(exported),
        "standards": exported,
    }
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Exported {len(exported)} standards -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
