"""
Upsert des standards prescriptifs "pending" dans Qdrant.

Usage:
  python scripts/upsert_pending_standards.py
  python scripts/upsert_pending_standards.py --file scripts/pending_prescriptive_standards.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from uuid import UUID

from dotenv import load_dotenv
from agents.embedding_provider import get_embeddings, resolve_embedding_model
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct


def _text_to_uuid(text: str) -> str:
    return str(UUID(bytes=hashlib.md5(text.encode("utf-8")).digest()))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Upsert pending prescriptive standards into Qdrant")
    parser.add_argument(
        "--file",
        default="scripts/pending_prescriptive_standards.json",
        help="Path to pending standards JSON",
    )
    parser.add_argument(
        "--collection",
        default=os.getenv("QDRANT_COLLECTION_NAME", "factory_standards"),
        help="Qdrant collection name",
    )
    parser.add_argument(
        "--qdrant-url",
        default=os.getenv("QDRANT_URL", "http://localhost:6333"),
        help="Qdrant URL",
    )
    parser.add_argument(
        "--embedding-model",
        default=os.getenv("EMBEDDING_MODEL", "text-embedding-3-large"),
        help="Embedding model (provider-aware)",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    load_dotenv(dotenv_path=".env")

    path = Path(args.file)
    if not path.exists():
        raise SystemExit(f"File not found: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit("Invalid format: expected a JSON array")

    embedding_model = resolve_embedding_model(args.embedding_model)
    embeddings = get_embeddings(embedding_model)
    client = QdrantClient(url=args.qdrant_url)

    inserted = 0
    skipped_empty = 0
    skipped_duplicate_in_file = 0
    seen_ids: set[str] = set()
    for item in data:
        text = str(item.get("text", "")).strip()
        metadata = item.get("metadata", {})
        if not text:
            skipped_empty += 1
            continue
        point_id = _text_to_uuid(text)
        if point_id in seen_ids:
            skipped_duplicate_in_file += 1
            continue
        seen_ids.add(point_id)
        vec = embeddings.embed_query(text)
        point = PointStruct(
            id=point_id,
            vector=vec,
            payload={"text": text, "metadata": metadata},
        )
        client.upsert(collection_name=args.collection, points=[point], wait=True)
        inserted += 1

    print(
        f"Upserted {inserted} standards into '{args.collection}' "
        f"(skipped_empty={skipped_empty}, skipped_duplicate_in_file={skipped_duplicate_in_file})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
