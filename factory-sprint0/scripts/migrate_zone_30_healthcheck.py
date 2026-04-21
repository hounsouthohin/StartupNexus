"""
scripts/migrate_zone_30_healthcheck.py

Injecte ZONE_30 dans Qdrant factory_standards.

ZONE_30 — Healthcheck endpoint (/api/health)
  Standards pour l'utilisation du template app/api/health/route.ts pré-généré.
  Couvre force-dynamic, $queryRaw SELECT 1 avec timeout 3s, HTTP 503 si dégradé.
  agent_context: dev

COMMANDE :
  cd factory-sprint0
  docker compose exec factory-worker python scripts/migrate_zone_30_healthcheck.py
  docker compose exec factory-worker python scripts/migrate_zone_30_healthcheck.py --dry-run

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
    priority: str = "medium",
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
            "source": "migration-zone30-healthcheck",
            "agent_context": "dev",
            "rule_type": rule_type,
            "priority": priority,
            "trigger_context": trigger_context,
        },
    }


ZONE_30_HEALTHCHECK = [

    _std("30-healthcheck", "routes", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript — app/api/health/route.ts
RAISON: app/api/health/route.ts est pré-généré par le pipeline — ne pas le réécrire. Il implémente : force-dynamic, $queryRaw SELECT 1 avec Promise.race timeout 3s, retour { status: 'ok', db: 'ok' } en 200 ou { status: 'degraded', db: 'unreachable' } en 503.
DETECTION_REGEX: app/api/health|healthcheck|health.route
ALTERNATIVE: Ne PAS écrire app/api/health/route.ts avec write_file — ce fichier est déjà présent dans les fichiers pré-générés
EXEMPLE_VALIDE:
  // Fichier pré-généré — structure de référence :
  export const dynamic = 'force-dynamic'

  export async function GET() {
    try {
      await Promise.race([
        prisma.$queryRaw\`SELECT 1\`,
        new Promise((_, reject) => setTimeout(() => reject(new Error('DB timeout')), 3000)),
      ])
      return NextResponse.json({ status: 'ok', db: 'ok' })
    } catch {
      return NextResponse.json({ status: 'degraded', db: 'unreachable' }, { status: 503 })
    }
  }"""),

    _std("30-healthcheck", "routes", """ACTION: INFORMATIF
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript — règles de design healthcheck
RAISON: Un healthcheck mal conçu peut exposer des informations sensibles ou rester bloqué en cas de panne DB.
RÈGLES:
  1. Toujours public (pas d'auth Clerk) — requis pour les health checks Vercel/Kubernetes
  2. force-dynamic obligatoire — sinon Next.js met en cache la réponse 200 statiquement
  3. Timeout 3s max sur $queryRaw — une DB morte ne doit pas bloquer le load balancer
  4. HTTP 503 si DB inaccessible — permet au load balancer de dérouter le trafic
  5. Ne jamais exposer : version DB, chaînes de connexion, stack traces, détails infra
  6. $queryRaw\`SELECT 1\` est le pattern standard Prisma pour tester la connectivité"""),
]


def run(dry_run: bool = False) -> None:
    client = QdrantClient(url=QDRANT_URL)
    standards = ZONE_30_HEALTHCHECK

    print(f"\n{'[DRY-RUN] ' if dry_run else ''}ZONE_30 — {len(standards)} standards à injecter\n")

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
    print(f"✓ {len(points)} standards ZONE_30 injectés dans '{COLLECTION_NAME}'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
