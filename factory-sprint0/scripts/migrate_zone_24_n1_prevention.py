"""
scripts/migrate_zone_24_n1_prevention.py

Injecte ZONE_24 dans Qdrant factory_standards.

ZONE_24 — Prévention N+1 (include + select imbriqué)
  Standards pour éviter les boucles findUnique dans findMany.
  Couvre include vs select, select imbriqué dans include, et les chaînes profondes.
  agent_context: dev

COMMANDE :
  cd factory-sprint0
  docker compose exec factory-worker python scripts/migrate_zone_24_n1_prevention.py
  docker compose exec factory-worker python scripts/migrate_zone_24_n1_prevention.py --dry-run

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
    rule_type: str = "performance",
    priority: str = "high",
    trigger_context: str = "relation-models",
) -> dict:
    return {
        "text": text.strip(),
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": zone,
            "status": "active",
            "version": "1.0",
            "category": category,
            "source": "migration-zone24-n1-prevention",
            "agent_context": "dev",
            "rule_type": rule_type,
            "priority": priority,
            "trigger_context": trigger_context,
        },
    }


ZONE_24_N1_PREVENTION = [

    _std("24-n1-prevention", "services", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript — lib/services/<model>.service.ts
RAISON: Une boucle findUnique dans un findMany = N+1 requêtes. Avec 100 factures, ça fait 101 requêtes au lieu de 1. Exemple réel production : 1 848 requêtes → 8,9s latence. Après fix include : 2 requêtes → 38ms.
DETECTION_REGEX: findMany.*\\.map.*findUnique|Promise\\.all.*findUnique
ALTERNATIVE: Utiliser include pour charger les relations en une seule requête
EXEMPLE_INVALIDE:
  const invoices = await prisma.invoice.findMany({ where: { userId } })
  const enriched = await Promise.all(
    invoices.map(inv => prisma.client.findUnique({ where: { id: inv.clientId } }))
  )  // ← N+1 : 1 + N requêtes
EXEMPLE_VALIDE:
  const invoices = await prisma.invoice.findMany({
    where: { userId },
    include: {
      client: { select: { id: true, name: true, email: true } },
    },
    orderBy: { createdAt: 'desc' },
  })  // ← 1 requête avec JOIN"""),

    _std("24-n1-prevention", "services", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript — Prisma include vs select
RAISON: include et select ne peuvent pas être utilisés au même niveau simultanément — Prisma retourne une erreur. Pour sélectionner des champs spécifiques dans une relation, utiliser select imbriqué dans include.
DETECTION_REGEX: include.*select.*\\{|select.*include.*\\{
ALTERNATIVE: select imbriqué dans include pour les champs de relation — jamais les deux au niveau racine
EXEMPLE_INVALIDE:
  prisma.invoice.findMany({
    select: { id: true, title: true },
    include: { client: true },  // ← Erreur Prisma : cannot use both
  })
EXEMPLE_VALIDE:
  // Option A — include + select imbriqué (relation avec champs limités)
  prisma.invoice.findMany({
    where: { userId },
    include: {
      client: { select: { id: true, name: true } },
    },
  })

  // Option B — select complet (contrôle total des champs retournés)
  prisma.invoice.findMany({
    where: { userId },
    select: {
      id: true,
      title: true,
      amount: true,
      client: { select: { id: true, name: true } },
    },
  })"""),
]


def run(dry_run: bool = False) -> None:
    client = QdrantClient(url=QDRANT_URL)
    standards = ZONE_24_N1_PREVENTION

    print(f"\n{'[DRY-RUN] ' if dry_run else ''}ZONE_24 — {len(standards)} standards à injecter\n")

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
    print(f"✓ {len(points)} standards ZONE_24 injectés dans '{COLLECTION_NAME}'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
