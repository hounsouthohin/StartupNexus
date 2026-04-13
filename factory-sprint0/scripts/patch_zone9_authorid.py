"""
Patch ciblé Zone 9 — enrichissement causal TypeScript du standard auth guard.

Ajoute l'explication profonde :
  - Clerk V6 : auth() retourne { userId: string | null } (breaking change v5→v6)
  - Prisma : authorId String (non-nullable) → incompatible avec string | null
  - TypeScript narrowing : if (!userId) réduit string | null → string
  - Erreur exacte à la compilation si guard absent

Usage (depuis factory-sprint0/) :
  python scripts/patch_zone9_authorid.py
"""

from __future__ import annotations

import hashlib
import os
from uuid import UUID

from dotenv import load_dotenv
from agents.embedding_provider import get_embeddings
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct

load_dotenv(dotenv_path=".env")

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION = os.getenv("QDRANT_COLLECTION_NAME", "factory_standards")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")


def _uuid(text: str) -> str:
    return str(UUID(bytes=hashlib.md5(text.encode("utf-8")).digest()))


# Texte PRÉCÉDENT (corrigé mais sans explication causale) — UUID à écraser
OLD_TEXT = """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: API Routes — vérification userId Clerk sur chaque route protégée
RAISON: Sans vérification userId, les routes API sont accessibles sans authentification.
DETECTION_REGEX: export async function (GET|POST|PUT|DELETE|PATCH)(?![\\s\\S]{0,400}await auth\\(\\))
ALTERNATIVE: const { userId } = await auth(); if (!userId) return 401; au début de chaque handler
EXEMPLE_INVALIDE:
  export async function GET(req: Request) {
    const data = await prisma.task.findMany();
    return NextResponse.json(data);  // Pas d'auth check
  }
EXEMPLE_VALIDE:
  export async function GET(req: Request) {
    const { userId } = await auth();
    if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    const data = await prisma.task.findMany({ where: { authorId: userId } });
    return NextResponse.json(data);
  }
ERREUR_ATTENDUE: Données exposées sans authentification
STATUS: active
VERSION: 1.0"""

# Texte ENRICHI — explication causale TypeScript complète
NEW_TEXT = """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: API Routes — null check userId obligatoire avant toute opération Prisma avec authorId
RAISON_TYPESCRIPT: Clerk V6 auth() retourne { userId: string | null } — breaking change depuis Clerk V5 où userId était string. Prisma schema : authorId String (non-nullable). Passer string | null à un champ String Prisma = ERREUR TypeScript à la compilation, pas au runtime. Le null check if (!userId) effectue un TypeScript type narrowing : string | null devient string garanti — Prisma accepte. SANS ce narrowing, TypeScript refuse de compiler.
RAISON_SECURITE: Sans vérification userId, les routes API sont accessibles sans authentification.
ERREUR_TYPESCRIPT_EXACTE: Type 'string | null' is not assignable to type 'string'. Type 'null' is not assignable to type 'string'.
NULL_CHECK_VALIDES:
  if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  if (userId === null) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
PATTERN_AUTHORID_CORRECT:
  GET/DELETE : where: { authorId: userId }   — userId narrowé = string garanti
  POST/PUT   : data: { authorId: userId, ... } — userId narrowé = string garanti
  INTERDIT   : where: { userId }              — champ userId n'existe pas dans le modèle Prisma
EXEMPLE_INVALIDE:
  export async function POST(req: Request) {
    const { userId } = await auth();
    // userId est string | null ici — pas de narrowing
    const body = await req.json();
    await prisma.task.create({ data: { ...body, authorId: userId } });
    // ERREUR TypeScript: string | null n'est pas assignable à String (Prisma)
  }
EXEMPLE_VALIDE:
  import { auth } from '@clerk/nextjs/server';
  export async function GET(req: Request) {
    const { userId } = await auth();
    if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    // userId est string ici (narrowé) — Prisma accepte authorId: userId
    const data = await prisma.task.findMany({ where: { authorId: userId } });
    return NextResponse.json(data);
  }
  export async function POST(req: Request) {
    const { userId } = await auth();
    if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    const body = await req.json();
    await prisma.task.create({ data: { ...body, authorId: userId } });
    return NextResponse.json({ success: true }, { status: 201 });
  }
ERREUR_ATTENDUE: Type error: Type 'string | null' is not assignable to type 'string' (compilation Next.js build)
STATUS: active
VERSION: 2.0"""

METADATA = {
    "stack": "nextjs-clerk-prisma",
    "zone": "9-security",
    "status": "active",
    "version": "1.0",
    "category": "security",
    "source": "factory_standards_v2",
    "agent_context": "dev",
}


def main() -> None:
    old_id = _uuid(OLD_TEXT)
    new_id = _uuid(NEW_TEXT)
    print(f"Old UUID : {old_id}")
    print(f"New UUID : {new_id}")

    client = QdrantClient(url=QDRANT_URL)
    embeddings = get_embeddings(EMBEDDING_MODEL)

    # 1. Supprimer l'ancien point (texte erroné)
    try:
        client.delete(
            collection_name=COLLECTION,
            points_selector=[old_id],
        )
        print(f"✓ Ancien standard supprimé ({old_id})")
    except Exception as e:
        print(f"⚠ Suppression ancien : {e} (peut-être déjà absent)")

    # 2. Upsert le nouveau point (texte corrigé)
    vector = embeddings.embed_query(NEW_TEXT)
    point = PointStruct(
        id=new_id,
        vector=vector,
        payload={"text": NEW_TEXT, "metadata": METADATA},
    )
    client.upsert(collection_name=COLLECTION, points=[point])
    print(f"✓ Standard Zone 9 enrichi upsert ({new_id})")
    print("  Enrichissements : RAISON_TYPESCRIPT, ERREUR_TYPESCRIPT_EXACTE, NULL_CHECK_VALIDES, PATTERN_AUTHORID_CORRECT")


if __name__ == "__main__":
    main()
