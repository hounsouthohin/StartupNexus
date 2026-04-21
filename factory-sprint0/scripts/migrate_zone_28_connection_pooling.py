"""
scripts/migrate_zone_28_connection_pooling.py

Injecte ZONE_28 dans Qdrant factory_standards.

ZONE_28 — Connection pooling Prisma (serverless)
  Standards pour la configuration de connection_limit=1 dans DATABASE_URL
  et le pattern singleton globalThis dans lib/prisma.ts.
  agent_context: dev

COMMANDE :
  cd factory-sprint0
  docker compose exec factory-worker python scripts/migrate_zone_28_connection_pooling.py
  docker compose exec factory-worker python scripts/migrate_zone_28_connection_pooling.py --dry-run

IDEMPOTENCE : UUID déterministe (MD5 du texte) — relancer = upsert silencieux.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path
from uuid import UUID

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.embedding_provider import get_embeddings, resolve_embedding_model
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct

load_dotenv(dotenv_path=ROOT / ".env")

QDRANT_URL      = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "factory_standards")
EMBEDDING_MODEL = resolve_embedding_model(os.getenv("EMBEDDING_MODEL", "text-embedding-3-large"))
EMBEDDINGS      = get_embeddings(EMBEDDING_MODEL)


def _uuid(text: str) -> str:
    return str(UUID(bytes=hashlib.md5(text.encode()).digest()))


def _std(
    zone: str,
    category: str,
    text: str,
    rule_type: str = "reliability",
    priority: str = "high",
    trigger_context: str = "always",
) -> dict:
    return {
        "text": text.strip(),
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": zone,
            "status": "active",
            "version": "1.0",
            "category": category,
            "source": "migration-zone28-connection-pooling",
            "agent_context": "dev",
            "rule_type": rule_type,
            "priority": priority,
            "trigger_context": trigger_context,
        },
    }


ZONE_28_CONNECTION_POOLING = [

    _std("28-connection-pooling", "infrastructure", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript — .env.local DATABASE_URL
RAISON: Sans connection_limit=1, chaque instance serverless crée son propre pool. Avec 10 instances × pool par défaut (num_cpus*2+1 ≈ 10) = 100 connexions simultanées → épuisement PostgreSQL. connection_limit=1 + pool_timeout=20 est le minimum viable pour Vercel/serverless.
DETECTION_REGEX: DATABASE_URL.*postgresql://(?!.*connection_limit)
ALTERNATIVE: Ajouter ?connection_limit=1&pool_timeout=20 à la fin de DATABASE_URL
EXEMPLE_INVALIDE:
  DATABASE_URL=postgresql://user:password@localhost:5432/mydb
EXEMPLE_VALIDE:
  DATABASE_URL=postgresql://user:password@localhost:5432/mydb?connection_limit=1&pool_timeout=20"""),

    _std("28-connection-pooling", "infrastructure", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript — lib/prisma.ts
RAISON: Le hot reload Next.js en dev crée une nouvelle instance PrismaClient à chaque modification de fichier. Sans globalThis singleton, on accumule des connexions jusqu'à "too many clients" en dev. En prod, le singleton garantit la réutilisation des connexions entre invocations warm.
DETECTION_REGEX: new PrismaClient\\(\\)|globalForPrisma
ALTERNATIVE: Pattern globalThis pour dev hot reload — lib/prisma.ts est pré-généré, ne pas le réécrire
EXEMPLE_INVALIDE:
  // Chaque import crée une nouvelle instance en dev
  export const prisma = new PrismaClient()
EXEMPLE_VALIDE:
  const globalForPrisma = globalThis as unknown as { prisma?: PrismaClient }
  export const prisma = globalForPrisma.prisma ?? new PrismaClient({ log: ['error'] })
  if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = prisma
  // Ne JAMAIS appeler prisma.$disconnect() après chaque requête — détruit la connexion réutilisable"""),
]


def run(dry_run: bool = False) -> None:
    client = QdrantClient(url=QDRANT_URL)
    standards = ZONE_28_CONNECTION_POOLING

    print(f"\n{'[DRY-RUN] ' if dry_run else ''}ZONE_28 — {len(standards)} standards à injecter\n")

    points: list[PointStruct] = []
    for std in standards:
        text = std["text"]
        uid  = _uuid(text)
        if dry_run:
            print(f"  [{uid[:8]}] {text[:80].replace(chr(10), ' ')}...")
            continue
        vec = EMBEDDINGS.embed_query(text)
        points.append(PointStruct(id=uid, vector=vec, payload=std["metadata"] | {"text": text}))

    if dry_run:
        print(f"\n{len(standards)} points seraient injectés (dry-run — rien écrit).")
        return

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    print(f"✓ {len(points)} standards ZONE_28 injectés dans '{COLLECTION_NAME}'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
