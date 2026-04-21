"""
scripts/migrate_zone_26_transactions.py

Injecte ZONE_26 dans Qdrant factory_standards.

ZONE_26 — Transactions Prisma ($transaction séquentielle et interactive)
  Standards pour les mutations multi-tables. Couvre séquentielle vs interactive,
  la règle absolue tx vs prisma dans le callback, et le timeout serverless.
  agent_context: dev

COMMANDE :
  cd factory-sprint0
  docker compose exec factory-worker python scripts/migrate_zone_26_transactions.py
  docker compose exec factory-worker python scripts/migrate_zone_26_transactions.py --dry-run

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
    trigger_context: str = "multi-table",
) -> dict:
    return {
        "text": text.strip(),
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": zone,
            "status": "active",
            "version": "1.0",
            "category": category,
            "source": "migration-zone26-transactions",
            "agent_context": "dev",
            "rule_type": rule_type,
            "priority": priority,
            "trigger_context": trigger_context,
        },
    }


ZONE_26_TRANSACTIONS = [

    _std("26-transactions", "services", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript — lib/services/<model>.service.ts
RAISON: Les opérations multi-tables sans transaction laissent la base dans un état incohérent si une étape échoue (ex: Invoice créée mais InvoiceItems non créés). $transaction garantit le rollback automatique si une opération échoue.
DETECTION_REGEX: prisma\\.\\w+\\.create.*prisma\\.\\w+\\.create|prisma\\.\\w+\\.update.*prisma\\.\\w+
ALTERNATIVE: $transaction([]) pour les opérations indépendantes, $transaction(async tx =>) pour les opérations conditionnelles
EXEMPLE_INVALIDE:
  // Sans transaction : si createMany échoue, l'invoice existe sans items
  const invoice = await prisma.invoice.create({ data: { userId, title, amount } })
  await prisma.invoiceItem.createMany({ data: items.map(i => ({ ...i, invoiceId: invoice.id })) })
EXEMPLE_VALIDE:
  // Séquentielle : opérations indépendantes
  const [invoice, _items] = await prisma.$transaction([
    prisma.invoice.create({ data: { userId, title, amount } }),
    prisma.invoiceItem.createMany({ data: items }),
  ])

  // Interactive : quand une étape dépend du résultat de la précédente
  const invoice = await prisma.$transaction(async (tx) => {
    const inv = await tx.invoice.create({ data: { userId, title, amount } })
    await tx.invoiceItem.createMany({
      data: items.map(item => ({ ...item, invoiceId: inv.id })),
    })
    return inv
  })"""),

    _std("26-transactions", "services", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript — règle absolue dans $transaction interactive
RAISON: Dans une transaction interactive, utiliser l'instance globale prisma au lieu de tx crée un deadlock : la connexion est déjà occupée par la transaction et la requête externe attend indéfiniment jusqu'au timeout. En serverless, ce deadlock est silencieux et difficile à déboguer.
DETECTION_REGEX: \\$transaction.*async.*tx.*prisma\\.(?!\\$)
ALTERNATIVE: Toujours remplacer prisma par tx à l'intérieur du callback de $transaction
EXEMPLE_INVALIDE:
  await prisma.$transaction(async (tx) => {
    const inv = await tx.invoice.create({ data })
    await prisma.invoiceItem.createMany({ data: items })  // ← prisma au lieu de tx → DEADLOCK
  })
EXEMPLE_VALIDE:
  await prisma.$transaction(async (tx) => {
    const inv = await tx.invoice.create({ data })
    await tx.invoiceItem.createMany({ data: items })  // ← tx partout dans le callback
  })"""),
]


def run(dry_run: bool = False) -> None:
    client = QdrantClient(url=QDRANT_URL)
    standards = ZONE_26_TRANSACTIONS

    print(f"\n{'[DRY-RUN] ' if dry_run else ''}ZONE_26 — {len(standards)} standards à injecter\n")

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
    print(f"✓ {len(points)} standards ZONE_26 injectés dans '{COLLECTION_NAME}'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
