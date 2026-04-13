"""
Patch ciblé Zone 1 — Standard TypeScript pour les params de routes dynamiques Next.js 14.

Problème observé (batch 14) :
  app/blog/[slug]/page.tsx:7:46 — Binding element 'params' implicitly has an 'any' type
  LLM génère : async function BlogPostPage({ params })
  Correct     : async function BlogPostPage({ params }: { params: { slug: string } })

Ce standard enseigne au LLM le typage correct des props de pages dynamiques Next.js.

Usage (depuis factory-sprint0/) :
  python scripts/patch_zone1_dynamic_params.py
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


STANDARD_TEXT = """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Next.js 14 App Router — typage TypeScript des props de pages dynamiques
ZONE: 1-nextjs-patterns

PROBLEME: Le LLM omet le typage des props destructurées — TypeScript strict mode génère :
  Binding element 'params' implicitly has an 'any' type
  (tsconfig.json: "strict": true → tout binding non typé = erreur de compilation)

RAISON_TYPESCRIPT: Next.js 14 App Router utilise des Server Components. Les props (params, searchParams)
sont des objets typés. Sous TypeScript strict, toute déstructuration sans type explicite provoque :
  "Binding element 'X' implicitly has an 'any' type"
  Ce n'est PAS un warning — c'est une erreur de build qui termine avec exit code 1.

PATTERN_CORRECT — props de page dynamique avec segment [slug] :
  interface Props { params: { slug: string } }
  export default async function Page({ params }: Props) { ... }

  OU inline :
  export default async function Page({ params }: { params: { slug: string } }) { ... }

PATTERN_CORRECT — props avec searchParams :
  export default async function Page({ params, searchParams }: {
    params: { slug: string };
    searchParams: { [key: string]: string | string[] | undefined };
  }) { ... }

PATTERN_CORRECT — props avec segment [id] :
  export default async function TaskPage({ params }: { params: { id: string } }) {
    const { userId } = await auth();
    if (!userId) redirect('/sign-in');
    const task = await prisma.task.findFirst({ where: { id: params.id, authorId: userId } });
    ...
  }

EXEMPLE_INVALIDE:
  // ERREUR : Binding element 'params' implicitly has an 'any' type
  export default async function BlogPostPage({ params }) {
    const post = await prisma.post.findUnique({ where: { slug: params.slug } });
    return <div>{post?.title}</div>;
  }

EXEMPLE_VALIDE:
  // CORRECT : typage explicite des props
  export default async function BlogPostPage({ params }: { params: { slug: string } }) {
    const post = await prisma.post.findUnique({ where: { slug: params.slug } });
    if (!post) notFound();
    return (
      <article>
        <h1 className="text-3xl font-bold">{post.title}</h1>
        <p>{post.content}</p>
      </article>
    );
  }

REGLE_ABSOLUE: Toute fonction composant de page dynamique (app/[...]/page.tsx) DOIT typer
ses props avec une interface ou un type inline. Ne jamais laisser ({ params }) non typé.

ERREUR_ATTENDUE: Binding element 'params' implicitly has an 'any' type (TypeScript build error)
STATUS: active
VERSION: 1.0"""

METADATA = {
    "stack": "nextjs-clerk-prisma",
    "zone": "1-nextjs-patterns",
    "status": "active",
    "version": "1.0",
    "category": "typescript",
    "source": "factory_standards_v1",
    "agent_context": "dev",
}


def main() -> None:
    standard_id = _uuid(STANDARD_TEXT)
    print(f"Standard UUID : {standard_id}")

    client = QdrantClient(url=QDRANT_URL)
    embeddings = get_embeddings(EMBEDDING_MODEL)

    vector = embeddings.embed_query(STANDARD_TEXT)
    point = PointStruct(
        id=standard_id,
        vector=vector,
        payload={"text": STANDARD_TEXT, "metadata": METADATA},
    )
    client.upsert(collection_name=COLLECTION, points=[point])
    print(f"✓ Standard Zone 1 inséré ({standard_id})")
    print("  Thème : typage props pages dynamiques Next.js 14 (params: { slug: string })")
    print("  Fix : Binding element 'params' implicitly has an 'any' type")


if __name__ == "__main__":
    main()
