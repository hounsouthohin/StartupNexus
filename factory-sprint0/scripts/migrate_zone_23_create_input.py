"""
scripts/migrate_zone_23_create_input.py

Injecte ZONE_23 dans Qdrant factory_standards.

ZONE_23 — CreateXxxInput sans userId (lib/types.ts)
  Standards pour la génération de types d'entrée qui excluent structurellement
  les champs d'ownership (userId, authorId) — ces champs viennent de auth().
  agent_context: dev

COMMANDE :
  cd factory-sprint0
  docker compose exec factory-worker python scripts/migrate_zone_23_create_input.py
  docker compose exec factory-worker python scripts/migrate_zone_23_create_input.py --dry-run

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
    rule_type: str = "security",
    priority: str = "critical",
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
            "source": "migration-zone23-create-input",
            "agent_context": "dev",
            "rule_type": rule_type,
            "priority": priority,
            "trigger_context": trigger_context,
        },
    }


ZONE_23_CREATE_INPUT = [

    _std("23-create-input", "types", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript — lib/types.ts
RAISON: CreateXxxInput ne doit jamais contenir userId/authorId — c'est une faille de sécurité (le client contrôlerait l'ownership) et une erreur TS2322 au build (type incompatible avec Prisma input). Le champ owner vient toujours de auth() et est passé séparément au service.
DETECTION_REGEX: CreateInput.*userId|type Create.*\\{[^}]*userId
ALTERNATIVE: Déclarer CreateXxxInput avec seulement les champs métier, passer ownerId séparément
EXEMPLE_INVALIDE:
  export type CreateExpenseInput = {
    amount: number
    category: string
    userId: string  // ← INTERDIT : TS2322 + faille sécurité
  }
EXEMPLE_VALIDE:
  export type CreateExpenseInput = {
    amount: number
    category: string
    description: string
    date: string
  }
  // Dans le service : prisma.expense.create({ data: { ...data, userId: ownerId } })"""),

    _std("23-create-input", "types", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript — lib/types.ts (pattern Zod .omit())
RAISON: Zod .omit() garantit à la fois la validation runtime ET le type statique sans userId. Si le client envoie userId dans le body, Zod le strip silencieusement (mode strip par défaut).
DETECTION_REGEX: z\\.object.*userId|zodSchema.*userId
ALTERNATIVE: Utiliser .omit({ userId: true, id: true, createdAt: true }) sur le schéma complet
EXEMPLE_VALIDE:
  import { z } from 'zod'

  const ExpenseSchema = z.object({
    id: z.string(),
    userId: z.string(),
    createdAt: z.date(),
    amount: z.number().positive(),
    category: z.string().min(1),
    description: z.string(),
    date: z.string(),
  })

  export const CreateExpenseBodySchema = ExpenseSchema.omit({
    id: true,
    userId: true,
    createdAt: true,
  })
  export type CreateExpenseInput = z.infer<typeof CreateExpenseBodySchema>
  // => { amount: number; category: string; description: string; date: string }"""),

    _std("23-create-input", "types", """ACTION: RECOMMANDÉ
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript — lib/types.ts (pattern Omit<Prisma.UncheckedCreateInput>)
RAISON: Omit<Prisma.ModelUncheckedCreateInput, 'id'|'userId'|'createdAt'> est une garantie statique : TypeScript refuse à la compilation si userId est présent dans data. Plus robuste que les types manuels car il suit automatiquement les changements de schema Prisma.
DETECTION_REGEX: Omit<Prisma\\.\\w+UncheckedCreateInput
ALTERNATIVE: Utiliser ce pattern pour les services DAL quand le schema Prisma est stable
EXEMPLE_VALIDE:
  import { Prisma } from '@prisma/client'

  export type CreateExpenseInput = Omit<
    Prisma.ExpenseUncheckedCreateInput,
    'id' | 'userId' | 'createdAt'
  >
  // TypeScript error si on essaie de passer userId dans data — garantie statique"""),
]


def run(dry_run: bool = False) -> None:
    client = QdrantClient(url=QDRANT_URL)
    standards = ZONE_23_CREATE_INPUT

    print(f"\n{'[DRY-RUN] ' if dry_run else ''}ZONE_23 — {len(standards)} standards à injecter\n")

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
    print(f"✓ {len(points)} standards ZONE_23 injectés dans '{COLLECTION_NAME}'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
