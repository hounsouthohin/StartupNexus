"""
scripts/migrate_zone_21_pagination.py

Injecte ZONE_21 dans Qdrant factory_standards.
N'efface PAS les zones existantes (ZONE_1-20 restent intactes).

ZONE_21 — Pagination (offset + PaginatedResponse<T>)
  Standards pour la génération de routes API paginées avec skip/take,
  le type générique PaginatedResponse<T>, et le pattern $transaction([findMany, count]).
  agent_context: dev

COMMANDE :
  cd factory-sprint0
  docker compose exec factory-worker python scripts/migrate_zone_21_pagination.py
  docker compose exec factory-worker python scripts/migrate_zone_21_pagination.py --dry-run

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
            "source": "migration-zone21-pagination",
            "agent_context": "dev",
            "rule_type": rule_type,
            "priority": priority,
            "trigger_context": trigger_context,
        },
    }


ZONE_21_PAGINATION = [

    _std("21-pagination", "routes", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript — app/api/**/route.ts + lib/types.ts
RAISON: Tout findMany() sans skip/take est un bottleneck de scalabilité. Même un MVP doit paginer ses listes dès le départ — corriger après coup casse l'API frontend.
DETECTION_REGEX: prisma\\.\\w+\\.findMany\\(\\{\\s*where
ALTERNATIVE: Utiliser skip/take avec pageSize=20 par défaut, plafonné à 100. Toujours retourner { data, total, page, pageSize }.
EXEMPLE_INVALIDE:
  const items = await prisma.item.findMany({ where: { userId } })
  return NextResponse.json(items)
EXEMPLE_VALIDE:
  // lib/types.ts
  export type PaginatedResponse<T> = { data: T[]; total: number; page: number; pageSize: number }

  // app/api/items/route.ts
  export async function GET(req: Request) {
    const { userId } = await auth()
    if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    const url = new URL(req.url)
    const page = Math.max(1, parseInt(url.searchParams.get('page') ?? '1'))
    const pageSize = Math.min(100, parseInt(url.searchParams.get('pageSize') ?? '20'))
    const skip = (page - 1) * pageSize
    const [data, total] = await prisma.$transaction([
      prisma.item.findMany({ where: { userId }, skip, take: pageSize, orderBy: { createdAt: 'desc' } }),
      prisma.item.count({ where: { userId } }),
    ])
    return NextResponse.json({ data, total, page, pageSize } satisfies PaginatedResponse<typeof data[0]>)
  }"""),

    _std("21-pagination", "types", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript — lib/types.ts
RAISON: PaginatedResponse<T> doit être défini dans lib/types.ts pour être importé dans toutes les routes API paginées. Sans ce type, chaque route réinvente sa propre structure de réponse.
DETECTION_REGEX: PaginatedResponse|\\{ data:.*total:.*page:
ALTERNATIVE: Définir une seule fois dans lib/types.ts et importer partout
EXEMPLE_VALIDE:
  export type PaginatedResponse<T> = {
    data: T[]
    total: number
    page: number
    pageSize: number
  }"""),

    _std("21-pagination", "routes", """ACTION: RECOMMANDÉ
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript — pagination cursor pour infinite scroll
RAISON: Pour les listes de type infinite scroll (dashboard avec scroll infini), la pagination curseur évite les doublons quand des items sont insérés entre deux appels.
DETECTION_REGEX: infinite.scroll|cursor.*pagination
ALTERNATIVE: Utiliser cursor uniquement pour infinite scroll — garder offset pour les pages numérotées
EXEMPLE_VALIDE:
  // GET /api/items?cursor=<id>&pageSize=20
  export async function GET(req: Request) {
    const { userId } = await auth()
    if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    const url = new URL(req.url)
    const cursor = url.searchParams.get('cursor')
    const pageSize = Math.min(50, parseInt(url.searchParams.get('pageSize') ?? '20'))
    const items = await prisma.item.findMany({
      where: { userId },
      take: pageSize + 1,
      ...(cursor && { cursor: { id: cursor }, skip: 1 }),
      orderBy: { createdAt: 'desc' },
    })
    const hasMore = items.length > pageSize
    return NextResponse.json({ data: items.slice(0, pageSize), hasMore, nextCursor: hasMore ? items[pageSize - 1].id : null })
  }"""),
]


def run(dry_run: bool = False) -> None:
    client = QdrantClient(url=QDRANT_URL)
    standards = ZONE_21_PAGINATION

    print(f"\n{'[DRY-RUN] ' if dry_run else ''}ZONE_21 — {len(standards)} standards à injecter\n")

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
    print(f"✓ {len(points)} standards ZONE_21 injectés dans '{COLLECTION_NAME}'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
