"""
scripts/reset_qdrant.py — reset collection Qdrant avec dimension alignée
sur le provider d'embedding actif (OpenAI ou Ollama).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

try:
    from agents.embedding_provider import detect_embedding_dimension, resolve_embedding_model
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from agents.embedding_provider import detect_embedding_dimension, resolve_embedding_model


def main() -> None:
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    collection = os.getenv("QDRANT_COLLECTION_NAME", "factory_standards")
    embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
    resolved_model = resolve_embedding_model(embedding_model)
    vector_size = int(os.getenv("QDRANT_VECTOR_SIZE", "0") or "0") or detect_embedding_dimension(embedding_model)

    client = QdrantClient(url=qdrant_url)
    client.delete_collection(collection)
    client.create_collection(
        collection_name=collection,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )
    print(
        f"Collection réinitialisée — 0 points | collection={collection} "
        f"| embedding={resolved_model} | dim={vector_size}"
    )


if __name__ == "__main__":
    main()
