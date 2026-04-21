"""
scripts/migrate_zone_25_select_minimal.py

Injecte ZONE_25 dans Qdrant factory_standards.

ZONE_25 — Select minimal (Prisma.ModelGetPayload + satisfies)
  Standards pour retourner seulement les champs nécessaires dans les listes.
  Couvre le pattern satisfies Prisma.ModelSelect + GetPayload pour le typage.
  agent_context: dev

COMMANDE :
  cd factory-sprint0
  docker compose exec factory-worker python scripts/migrate_zone_25_select_minimal.py
  docker compose exec factory-worker python scripts/migrate_zone_25_select_minimal.py --dry-run

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
    priority: str = "medium",
    trigger_context: str = "list-routes",
) -> dict:
    return {
        "text": text.strip(),
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": zone,
            "status": "active",
            "version": "1.0",
            "category": category,
            "source": "migration-zone25-select-minimal",
            "agent_context": "dev",
            "rule_type": rule_type,
            "priority": priority,
            "trigger_context": trigger_context,
        },
    }


ZONE_25_SELECT_MINIMAL = [

    _std("25-select-minimal", "services", """ACTION: RECOMMANDÉ
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript — lib/services/<model>.service.ts
RAISON: Retourner tous les champs par défaut expose des données potentiellement sensibles et alourdit la sérialisation JSON. Pour les listes, sélectionner uniquement les champs affichés dans le UI. Pour le détail, retourner tous les champs utiles.
DETECTION_REGEX: findMany\\(\\{\\s*where.*\\}\\s*\\)|findMany\\(\\{\\s*orderBy
ALTERNATIVE: Utiliser select pour les méthodes findMany des services — garder le findUnique complet
EXEMPLE_INVALIDE:
  findMany: (userId: string) =>
    prisma.invoice.findMany({ where: { userId }, orderBy: { createdAt: 'desc' } })
  // ← retourne tous les champs dont content (texte long), items (JSON lourd)
EXEMPLE_VALIDE:
  findMany: (userId: string) =>
    prisma.invoice.findMany({
      where: { userId },
      orderBy: { createdAt: 'desc' },
      select: {
        id: true,
        title: true,
        amount: true,
        status: true,
        createdAt: true,
        client: { select: { id: true, name: true } },
      },
    })"""),

    _std("25-select-minimal", "types", """ACTION: RECOMMANDÉ
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript — lib/types.ts (Prisma.ModelGetPayload)
RAISON: satisfies Prisma.ModelSelect garantit que les clés du select existent dans le modèle (erreur TS si champ inexistant). GetPayload extrait le type TypeScript exact correspondant — le type de retour du service est toujours précis.
DETECTION_REGEX: satisfies Prisma\\.\\w+Select|Prisma\\.\\w+GetPayload
ALTERNATIVE: Pattern satisfies + GetPayload pour typer les résultats de select minimal
EXEMPLE_VALIDE:
  import { Prisma } from '@prisma/client'

  const invoiceListSelect = {
    id: true,
    title: true,
    amount: true,
    status: true,
    createdAt: true,
  } satisfies Prisma.InvoiceSelect

  export type InvoiceListItem = Prisma.InvoiceGetPayload<{
    select: typeof invoiceListSelect
  }>
  // => { id: string; title: string; amount: number; status: string; createdAt: Date }

  // Alternative simple si la fonction est déjà définie :
  type InvoiceListItem = Awaited<ReturnType<typeof invoiceService.findMany>>[number]"""),
]


def run(dry_run: bool = False) -> None:
    client = QdrantClient(url=QDRANT_URL)
    standards = ZONE_25_SELECT_MINIMAL

    print(f"\n{'[DRY-RUN] ' if dry_run else ''}ZONE_25 — {len(standards)} standards à injecter\n")

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
    print(f"✓ {len(points)} standards ZONE_25 injectés dans '{COLLECTION_NAME}'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
