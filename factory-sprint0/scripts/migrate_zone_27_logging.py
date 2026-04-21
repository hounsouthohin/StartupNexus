"""
scripts/migrate_zone_27_logging.py

Injecte ZONE_27 dans Qdrant factory_standards.

ZONE_27 — Logging structuré (Pino)
  Standards pour l'utilisation de lib/logger.ts dans les routes API.
  Couvre le child logger par module, les champs structurés obligatoires,
  et le pattern complet succès/Zod/Prisma/inattendu.
  agent_context: dev

COMMANDE :
  cd factory-sprint0
  docker compose exec factory-worker python scripts/migrate_zone_27_logging.py
  docker compose exec factory-worker python scripts/migrate_zone_27_logging.py --dry-run

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
            "source": "migration-zone27-logging",
            "agent_context": "dev",
            "rule_type": rule_type,
            "priority": priority,
            "trigger_context": trigger_context,
        },
    }


ZONE_27_LOGGING = [

    _std("27-logging", "routes", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript — app/api/**/route.ts
RAISON: console.log en production ne porte aucun contexte (userId, route, durée). Sans logging structuré, déboguer une erreur en production revient à chercher une aiguille dans une botte de foin. lib/logger.ts est pré-généré — toujours l'importer.
DETECTION_REGEX: console\\.log|console\\.error|console\\.warn
ALTERNATIVE: Importer logger depuis @/lib/logger et utiliser child logger par route
EXEMPLE_INVALIDE:
  } catch (error) {
    console.error('Erreur:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
EXEMPLE_VALIDE:
  import logger from '@/lib/logger'

  const log = logger.child({ route: 'POST /api/invoices' })

  export async function POST(req: Request) {
    const { userId } = await auth()
    if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    try {
      const body = await req.json()
      const result = CreateInvoiceBodySchema.safeParse(body)
      if (!result.success) {
        log.warn({ userId, issues: result.error.issues }, 'Validation failed')
        return NextResponse.json({ error: 'Validation error' }, { status: 400 })
      }
      const invoice = await invoiceService.create(result.data, userId)
      log.info({ userId, invoiceId: invoice.id }, 'Invoice created')
      return NextResponse.json(invoice, { status: 201 })
    } catch (error) {
      const { status, message } = handlePrismaError(error)
      log.error({ userId, error }, 'Unexpected error creating invoice')
      return NextResponse.json({ error: message }, { status })
    }
  }"""),

    _std("27-logging", "routes", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript — champs structurés de log
RAISON: Un log sans userId ne permet pas de tracer l'historique d'un utilisateur en production. Un log sans route ne permet pas de filtrer par endpoint. Ces champs minimaux suffisent pour le debugging Palier 1.
DETECTION_REGEX: log\\.error\\(|log\\.warn\\(|log\\.info\\(
ALTERNATIVE: Toujours inclure userId et le contexte de l'opération dans l'objet de log
EXEMPLE_VALIDE:
  // Champs minimaux pour chaque log structuré :
  log.error({ userId, error, route: 'POST /api/invoices' }, 'Description de l\\'erreur')
  log.warn({ userId, issues }, 'Validation échouée')
  log.info({ userId, resourceId: invoice.id }, 'Ressource créée')

  // Ne jamais loguer de données sensibles :
  // ❌ log.info({ body }) — peut contenir des mots de passe
  // ❌ log.info({ env: process.env }) — expose les secrets"""),
]


def run(dry_run: bool = False) -> None:
    client = QdrantClient(url=QDRANT_URL)
    standards = ZONE_27_LOGGING

    print(f"\n{'[DRY-RUN] ' if dry_run else ''}ZONE_27 — {len(standards)} standards à injecter\n")

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
    print(f"✓ {len(points)} standards ZONE_27 injectés dans '{COLLECTION_NAME}'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
