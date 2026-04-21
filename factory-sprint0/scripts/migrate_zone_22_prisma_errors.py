"""
scripts/migrate_zone_22_prisma_errors.py

Injecte ZONE_22 dans Qdrant factory_standards.

ZONE_22 — Gestion des erreurs Prisma (P2002, P2025, P2003, P2014)
  Standards pour l'utilisation de handlePrismaError() depuis lib/prisma-errors.ts
  dans les routes API. Couvre le mapping code Prisma → HTTP et le pattern catch.
  agent_context: dev

COMMANDE :
  cd factory-sprint0
  docker compose exec factory-worker python scripts/migrate_zone_22_prisma_errors.py
  docker compose exec factory-worker python scripts/migrate_zone_22_prisma_errors.py --dry-run

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
    trigger_context: str = "error-correction",
) -> dict:
    return {
        "text": text.strip(),
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": zone,
            "status": "active",
            "version": "1.0",
            "category": category,
            "source": "migration-zone22-prisma-errors",
            "agent_context": "dev",
            "rule_type": rule_type,
            "priority": priority,
            "trigger_context": trigger_context,
        },
    }


ZONE_22_PRISMA_ERRORS = [

    _std("22-prisma-errors", "error-handling", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript — app/api/**/route.ts
RAISON: Sans catch des erreurs Prisma connues, un conflit P2002 retourne une 500 générique au lieu d'un 409 clair. Le client ne peut pas distinguer "doublon" de "panne serveur". lib/prisma-errors.ts est pré-généré par le pipeline — toujours l'importer.
DETECTION_REGEX: catch.*error.*500|catch.*e.*Internal.server
ALTERNATIVE: Importer handlePrismaError et déléguer le catch Prisma
EXEMPLE_INVALIDE:
  } catch (e) {
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
EXEMPLE_VALIDE:
  import { handlePrismaError } from '@/lib/prisma-errors'

  } catch (error) {
    const { status, message } = handlePrismaError(error)
    return NextResponse.json({ error: message }, { status })
  }"""),

    _std("22-prisma-errors", "error-handling", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript — lib/prisma-errors.ts
RAISON: Toujours importer Prisma depuis '@prisma/client' pour instanceof check. Depuis Prisma v4, importer depuis '@prisma/client/runtime/library' fait échouer silencieusement le instanceof — les erreurs connues tombent dans le fallback 500.
DETECTION_REGEX: from '@prisma/client/runtime
ALTERNATIVE: import { Prisma } from '@prisma/client' — jamais depuis le runtime
EXEMPLE_INVALIDE:
  import { Prisma } from '@prisma/client/runtime/library'
  if (error instanceof Prisma.PrismaClientKnownRequestError) { ... }
  // instanceof retourne false → tous les codes Prisma tombent en 500
EXEMPLE_VALIDE:
  import { Prisma } from '@prisma/client'
  if (error instanceof Prisma.PrismaClientKnownRequestError) {
    // P2002 → 409, P2025 → 404, P2003 → 400, P2014 → 400
  }"""),

    _std("22-prisma-errors", "error-handling", """ACTION: INFORMATIF
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript — mapping codes Prisma → HTTP
RAISON: Référence des codes Prisma fréquents dans les apps SaaS Palier 1 — à utiliser dans les catch.
MAPPING:
  P2002 → 409 Conflict (unique constraint violated — ex: email déjà utilisé)
  P2025 → 404 Not Found (record to update/delete does not exist)
  P2003 → 400 Bad Request (foreign key constraint failed — parent introuvable)
  P2014 → 400 Bad Request (required relation violation)
  autres → 500 Internal Server Error
EXEMPLE_VALIDE:
  switch (error.code) {
    case 'P2002': return { status: 409, message: 'A record with this value already exists' }
    case 'P2025': return { status: 404, message: 'Record not found' }
    case 'P2003': return { status: 400, message: 'Foreign key constraint failed' }
    case 'P2014': return { status: 400, message: 'Relation violation' }
    default:      return { status: 500, message: 'Internal server error' }
  }"""),
]


def run(dry_run: bool = False) -> None:
    client = QdrantClient(url=QDRANT_URL)
    standards = ZONE_22_PRISMA_ERRORS

    print(f"\n{'[DRY-RUN] ' if dry_run else ''}ZONE_22 — {len(standards)} standards à injecter\n")

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
    print(f"✓ {len(points)} standards ZONE_22 injectés dans '{COLLECTION_NAME}'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
