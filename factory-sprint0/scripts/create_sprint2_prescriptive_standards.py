"""
Create 3 Sprint 2 prescriptive standards in Qdrant.

Usage:
  python scripts/create_sprint2_prescriptive_standards.py
"""

from __future__ import annotations

import os
import uuid
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct
from langchain_openai import OpenAIEmbeddings

load_dotenv(dotenv_path=".env")

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "factory_standards")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")

EMBEDDINGS = OpenAIEmbeddings(model=EMBEDDING_MODEL)


STANDARDS = [
    {
        "text": """ACTION: INTERDIT
STACK: nextjs-clerk-prisma
TECHNOLOGIE: pages/ directory
RAISON: Conflit App Router/Pages Router cause build failure.
DETECTION_REGEX: ^pages/.*\\.(tsx?|jsx?)$
ALTERNATIVE: Utiliser app/ directory uniquement.
EXEMPLE_INVALIDE: pages/index.tsx + app/page.tsx coexistent.
EXEMPLE_VALIDE: app/page.tsx seulement.
ERREUR_ATTENDUE: Conflicting app and page file.
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "status": "active",
            "version": "1.0",
            "category": "nextjs",
        },
    },
    {
        "text": """ACTION: INTERDIT
STACK: nextjs-clerk-prisma
TECHNOLOGIE: @clerk/nextjs/api
RAISON: Import déprécié Clerk v5/v6, cause erreurs runtime.
DETECTION_REGEX: from\\s+['"]@clerk/nextjs/api['"]
ALTERNATIVE: import { ... } from '@clerk/nextjs/server'
EXEMPLE_INVALIDE: import { auth } from '@clerk/nextjs/api'
EXEMPLE_VALIDE: import { auth } from '@clerk/nextjs/server'
ERREUR_ATTENDUE: Module not found: @clerk/nextjs/api
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "status": "active",
            "version": "1.0",
            "category": "clerk",
        },
    },
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: node-mocks-http
RAISON: Requis pour tester les API Routes Next.js.
DETECTION_REGEX: devDependencies.*jest.*(?!node-mocks-http)
ALTERNATIVE: Ajouter "node-mocks-http": "^1.14.0" dans devDependencies.
EXEMPLE_INVALIDE: package.json sans node-mocks-http.
EXEMPLE_VALIDE: "node-mocks-http": "^1.14.0" présent.
ERREUR_ATTENDUE: Tests API routes échouent sans mock.
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "status": "active",
            "version": "1.0",
            "category": "testing",
        },
    },
]


def main() -> int:
    client = QdrantClient(url=QDRANT_URL)
    points = []
    for std in STANDARDS:
        vector = EMBEDDINGS.embed_query(std["text"])
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={"text": std["text"], "metadata": std["metadata"]},
            )
        )
    client.upsert(collection_name=COLLECTION_NAME, points=points, wait=True)
    print(f"Inserted {len(points)} prescriptive standards into '{COLLECTION_NAME}'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
