"""
scripts/migrate_zone_29_soft_delete.py

Injecte ZONE_29 dans Qdrant factory_standards.

ZONE_29 — Soft delete (deletedAt + $extends)
  Standards pour l'archivage des entités critiques au lieu de les supprimer.
  Couvre le champ deletedAt, l'index composite, l'ownership check avant soft delete,
  et la règle de décision (quels modèles méritent un soft delete).
  agent_context: dev

COMMANDE :
  cd factory-sprint0
  docker compose exec factory-worker python scripts/migrate_zone_29_soft_delete.py
  docker compose exec factory-worker python scripts/migrate_zone_29_soft_delete.py --dry-run

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
    rule_type: str = "architecture",
    priority: str = "low",
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
            "source": "migration-zone29-soft-delete",
            "agent_context": "dev",
            "rule_type": rule_type,
            "priority": priority,
            "trigger_context": trigger_context,
        },
    }


ZONE_29_SOFT_DELETE = [

    _std("29-soft-delete", "services", """ACTION: RECOMMANDÉ (entités critiques)
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript — prisma/schema.prisma + lib/services/<model>.service.ts
RAISON: Un hard delete sur une facture ou commande détruit la traçabilité métier (TVA, litiges). Le soft delete archive l'entité — elle reste requêtable pour l'audit mais invisible dans les listes normales. Appliquer uniquement aux entités critiques : invoices, orders, projects, contacts — pas aux logs ou sessions.
DETECTION_REGEX: deletedAt|soft.delete|softDelete
ALTERNATIVE: Ajouter deletedAt DateTime? au modèle + @@index([userId, deletedAt]) + ownership check avant soft delete
EXEMPLE_VALIDE:
  // prisma/schema.prisma
  model Invoice {
    id        String    @id @default(cuid())
    userId    String
    title     String
    deletedAt DateTime?
    createdAt DateTime  @default(now())
    @@index([userId])
    @@index([userId, deletedAt])
  }

  // lib/services/invoice.service.ts
  softDelete: async (id: string, userId: string) => {
    // Ownership check AVANT soft delete
    const invoice = await prisma.invoice.findFirst({
      where: { id, userId, deletedAt: null },
      select: { id: true },
    })
    if (!invoice) throw new Error('Forbidden')
    return prisma.invoice.update({
      where: { id },
      data: { deletedAt: new Date() },
    })
  },

  // findMany filtre les soft-deleted par défaut
  findMany: (userId: string) =>
    prisma.invoice.findMany({
      where: { userId, deletedAt: null },
      orderBy: { createdAt: 'desc' },
    })"""),

    _std("29-soft-delete", "infrastructure", """ACTION: INFORMATIF
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript — Prisma Client Extension $extends pour soft delete automatique
RAISON: $extends intercepte automatiquement tous les findMany/delete pour filtrer/rediriger — plus robuste que de filtrer manuellement dans chaque service. Non déprécié contrairement au middleware Prisma.
DETECTION_REGEX: \\$extends.*query|baseClient\\.\\$extends
ALTERNATIVE: Utiliser $extends si tous les modèles du brief ont un soft delete — sinon, filtrer manuellement dans le service (plus explicite)
EXEMPLE_VALIDE:
  // lib/prisma.ts — extension pour soft delete global sur Invoice
  export const prisma = baseClient.$extends({
    query: {
      invoice: {
        async findMany({ args, query }) {
          args.where = { deletedAt: null, ...args.where }
          return query(args)
        },
        async delete({ args }) {
          return baseClient.invoice.update({
            where: args.where,
            data: { deletedAt: new Date() },
          })
        },
      },
    },
  })
  // ⚠️ lib/prisma.ts est un fichier pré-généré — ne PAS utiliser $extends sauf si le brief le demande explicitement"""),
]


def run(dry_run: bool = False) -> None:
    client = QdrantClient(url=QDRANT_URL)
    standards = ZONE_29_SOFT_DELETE

    print(f"\n{'[DRY-RUN] ' if dry_run else ''}ZONE_29 — {len(standards)} standards à injecter\n")

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
    print(f"✓ {len(points)} standards ZONE_29 injectés dans '{COLLECTION_NAME}'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
