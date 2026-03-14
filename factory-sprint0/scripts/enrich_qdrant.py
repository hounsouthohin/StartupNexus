"""
Lit patterns_report.json et enrichit la collection Qdrant factory_standards.
Écrit un log d'enrichissement dans logs/metrics/.
"""

from __future__ import annotations

import argparse
import json
import os
import hashlib
from datetime import datetime, timezone
from uuid import UUID

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct


DEFAULT_PATTERNS_REPORT = os.path.join("logs", "shadow", "patterns_report.json")
QDRANT_COLLECTION_NAME = "factory_standards"


def _get_qdrant_url() -> str:
    return os.getenv("QDRANT_URL", "http://qdrant:6333")

# Standard Clerk — hard rule injectée manuellement dans la couche RAG.
# La version "^5.0.0" est portée par le texte RAG uniquement (pas dans shared_tools.py).
CLERK_STANDARD = {
    "category": "clerk",
    "text": (
        "Le seul package npm correct pour Clerk avec Next.js est @clerk/nextjs "
        "version ^6.0.0. Les packages @clerk/clerk-sdk, @clerk/clerk-js, "
        "@clerk/sdk, @clerk/react n'existent pas ou sont obsolètes et ne doivent "
        "jamais apparaître dans package.json. "
        "Import server-side : from '@clerk/nextjs/server'. "
        "Import client-side : from '@clerk/nextjs'. "
        "Ne jamais inventer de variante du nom du package Clerk. "
        "CRITIQUE Clerk v6 : auth() retourne une Promise, toujours await. "
        "Dans clerkMiddleware, auth est un OBJET (pas une fonction) : await auth.protect() (INTERDIT: auth().protect())."
    ),
    "tags": ["clerk", "npm", "package", "install", "nextjs", "dependency", "version", "v6"],
    "priority": "HIGH",
}


def text_to_uuid(text: str) -> str:
    hash_bytes = hashlib.md5(text.encode("utf-8")).digest()
    return str(UUID(bytes=hash_bytes))


def _load_patterns(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _standard_text_from_pattern(pattern: dict) -> str:
    signature = pattern.get("signature", "unknown_signature")
    occurrences = pattern.get("occurrences", 0)
    recommendation = pattern.get("recommendation", "")
    return (
        "Factory standard learned from recurring failures. "
        f"Pattern: {signature}. "
        f"Observed occurrences: {occurrences}. "
        f"Recommended action: {recommendation}"
    )


def _write_metrics_log(payload: dict) -> str:
    metrics_dir = os.path.join("logs", "metrics")
    os.makedirs(metrics_dir, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join(metrics_dir, f"qdrant_enrichment_{ts}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=True, indent=2)
    return path


def enrich_qdrant(patterns_report_path: str = DEFAULT_PATTERNS_REPORT) -> dict:
    load_dotenv(dotenv_path=".env")
    qdrant_url = _get_qdrant_url()
    report = _load_patterns(patterns_report_path)
    patterns = report.get("patterns", [])

    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    client = QdrantClient(url=qdrant_url)

    inserted = []
    failed = []

    for pattern in patterns:
        try:
            text = _standard_text_from_pattern(pattern)
            vector = embeddings.embed_query(text)
            point_id = text_to_uuid(text)

            payload = {
                "text": text,
                "metadata": {
                    "category": "learner_pattern",
                    "tech": "cross-agent",
                    "version": "dynamic",
                    "source": "evaluator_agent",
                    "outcome": "learned_standard",
                    "pattern_id": pattern.get("pattern_id"),
                    "signature": pattern.get("signature"),
                    "occurrences": pattern.get("occurrences"),
                },
            }

            client.upsert(
                collection_name=QDRANT_COLLECTION_NAME,
                points=[PointStruct(id=point_id, vector=vector, payload=payload)],
                wait=True,
            )

            inserted.append(
                {
                    "point_id": point_id,
                    "pattern_id": pattern.get("pattern_id"),
                    "signature": pattern.get("signature"),
                }
            )
        except Exception as exc:
            failed.append(
                {
                    "pattern_id": pattern.get("pattern_id"),
                    "signature": pattern.get("signature"),
                    "error": str(exc),
                }
            )

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "patterns_report_path": patterns_report_path,
        "collection": QDRANT_COLLECTION_NAME,
        "total_patterns": len(patterns),
        "inserted_count": len(inserted),
        "failed_count": len(failed),
        "inserted": inserted,
        "failed": failed,
    }
    metrics_log_path = _write_metrics_log(result)
    result["metrics_log_path"] = metrics_log_path
    return result


PRISMA7_STANDARD = {
    "category": "prisma",
    "text": (
        "Prisma 7 breaking change : la propriété url dans datasource de schema.prisma "
        "est supprimée. La connexion DATABASE_URL doit être dans prisma.config.ts. "
        "Schema.prisma ne contient plus url. "
        "Créer prisma.config.ts avec defineConfig({ datasource: { url: process.env.DATABASE_URL } }). "
        "Ne jamais écrire url = env('DATABASE_URL') dans schema.prisma avec Prisma 7+."
    ),
    "tags": ["prisma", "prisma7", "datasource", "url", "config", "migration", "breaking"],
    "priority": "HIGH",
}


def inject_clerk_standard(client: QdrantClient, embeddings: OpenAIEmbeddings) -> dict:
    """Insère directement le standard Clerk dans la collection Qdrant (pas de patterns_report requis)."""
    text = CLERK_STANDARD["text"]
    vector = embeddings.embed_query(text)
    point_id = text_to_uuid(text)

    payload = {
        "text": text,
        "metadata": {
            "category": CLERK_STANDARD["category"],
            "tags": CLERK_STANDARD["tags"],
            "priority": CLERK_STANDARD["priority"],
            "source": "manual_injection",
            "tech": "nextjs,clerk",
            "version": "static",
            "outcome": "hard_rule",
        },
    }

    client.upsert(
        collection_name=QDRANT_COLLECTION_NAME,
        points=[PointStruct(id=point_id, vector=vector, payload=payload)],
        wait=True,
    )
    return {
        "point_id": point_id,
        "category": CLERK_STANDARD["category"],
        "priority": CLERK_STANDARD["priority"],
        "text_excerpt": text[:100] + "...",
    }


def inject_prisma7_standard(client: QdrantClient, embeddings: OpenAIEmbeddings) -> dict:
    """Insère directement le standard Prisma 7 dans la collection Qdrant (pas de patterns_report requis)."""
    text = PRISMA7_STANDARD["text"]
    vector = embeddings.embed_query(text)
    point_id = text_to_uuid(text)

    payload = {
        "text": text,
        "metadata": {
            "category": PRISMA7_STANDARD["category"],
            "tags": PRISMA7_STANDARD["tags"],
            "priority": PRISMA7_STANDARD["priority"],
            "source": "manual_injection",
            "tech": "prisma,nextjs",
            "version": "static",
            "outcome": "hard_rule",
        },
    }

    client.upsert(
        collection_name=QDRANT_COLLECTION_NAME,
        points=[PointStruct(id=point_id, vector=vector, payload=payload)],
        wait=True,
    )
    return {
        "point_id": point_id,
        "category": PRISMA7_STANDARD["category"],
        "priority": PRISMA7_STANDARD["priority"],
        "text_excerpt": text[:100] + "...",
    }


GENERIC_LISTING_STANDARD = {
    "category": "nextjs",
    "text": (
        "Pattern générique pour une page de listing Next.js App Router (Server Component). "
        "Ce pattern fonctionne pour tout modèle Prisma (Post, Task, Product, Order, etc.). "
        "Règles absolues : pas de 'use client', pas de hooks React (useState/useEffect), "
        "export const dynamic = 'force-dynamic', typage explicite du tableau, try/catch avec fallback []. "
        "Exemple générique applicable à tout modèle : "
        "type ItemSummary = { id: string; title: string; createdAt: Date }; "
        "let items: ItemSummary[] = []; "
        "try { items = await prisma.<model>.findMany({ "
        "where: { published: true }, orderBy: { createdAt: 'desc' }, "
        "select: { id: true, title: true, createdAt: true } }); } catch { items = []; } "
        "Remplacer <model> par le nom du modèle Prisma en camelCase (post, task, product...). "
        "Remplacer ItemSummary et les champs select par ceux du modèle réel. "
        "Ne jamais utiliser 'any' pour le type du tableau. "
        "Ne jamais appeler prisma sans try/catch dans un Server Component (pas de DB en CI)."
    ),
    "tags": ["nextjs", "server-component", "prisma", "listing", "tailwind", "generic", "app-router"],
    "priority": "HIGH",
}

AUTH_NULL_GUARD_STANDARD = {
    "category": "clerk",
    "text": (
        "Règle absolue pour tout route handler app/api/**/route.ts qui utilise userId dans une opération Prisma. "
        "Pattern mandatory : const { userId } = await auth(); "
        "if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 }); "
        "Ce guard DOIT précéder tout appel Prisma utilisant userId (create, update, delete, findUnique avec userId). "
        "Ce pattern s'applique à TOUS les modèles avec ownership utilisateur, quel que soit le nom du champ : "
        "authorId, userId, ownerId, createdBy — toujours vérifier userId avant de l'utiliser. "
        "TypeScript strict : userId peut être null si l'utilisateur n'est pas authentifié. "
        "Sans ce guard, TypeScript lève : 'Argument of type string | null is not assignable to parameter of type string'. "
        "Signature correcte complète : "
        "export async function PUT(request: Request, { params }: { params: { id: string } }) { "
        "const { userId } = await auth(); "
        "if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 }); "
        "const body = await request.json(); "
        "// Valider body avec Zod avant toute écriture Prisma. "
        "const result = await prisma.<model>.update({ where: { id: params.id }, data: { ...body, userId } }); "
        "return NextResponse.json(result); }"
    ),
    "tags": ["clerk", "auth", "userId", "null-guard", "route-handler", "prisma", "typescript", "security"],
    "priority": "CRITICAL",
}


def inject_generic_listing_standard(client: QdrantClient, embeddings: OpenAIEmbeddings) -> dict:
    """Insère le standard de listing générique Server Component dans Qdrant."""
    text = GENERIC_LISTING_STANDARD["text"]
    vector = embeddings.embed_query(text)
    point_id = text_to_uuid(text)
    payload = {
        "text": text,
        "metadata": {
            "category": GENERIC_LISTING_STANDARD["category"],
            "tags": GENERIC_LISTING_STANDARD["tags"],
            "priority": GENERIC_LISTING_STANDARD["priority"],
            "source": "manual_injection",
            "tech": "nextjs,prisma,tailwind",
            "version": "static",
            "outcome": "hard_rule",
            "stack": "nextjs-clerk-prisma",
            "status": "active",
            "zone": "15-generic-patterns",
        },
    }
    client.upsert(
        collection_name=QDRANT_COLLECTION_NAME,
        points=[PointStruct(id=point_id, vector=vector, payload=payload)],
        wait=True,
    )
    return {"point_id": point_id, "category": GENERIC_LISTING_STANDARD["category"],
            "priority": GENERIC_LISTING_STANDARD["priority"], "text_excerpt": text[:100] + "..."}


def inject_auth_null_guard_standard(client: QdrantClient, embeddings: OpenAIEmbeddings) -> dict:
    """Insère le standard auth null guard dans Qdrant."""
    text = AUTH_NULL_GUARD_STANDARD["text"]
    vector = embeddings.embed_query(text)
    point_id = text_to_uuid(text)
    payload = {
        "text": text,
        "metadata": {
            "category": AUTH_NULL_GUARD_STANDARD["category"],
            "tags": AUTH_NULL_GUARD_STANDARD["tags"],
            "priority": AUTH_NULL_GUARD_STANDARD["priority"],
            "source": "manual_injection",
            "tech": "nextjs,clerk,typescript",
            "version": "static",
            "outcome": "hard_rule",
            "stack": "nextjs-clerk-prisma",
            "status": "active",
            "zone": "15-generic-patterns",
        },
    }
    client.upsert(
        collection_name=QDRANT_COLLECTION_NAME,
        points=[PointStruct(id=point_id, vector=vector, payload=payload)],
        wait=True,
    )
    return {"point_id": point_id, "category": AUTH_NULL_GUARD_STANDARD["category"],
            "priority": AUTH_NULL_GUARD_STANDARD["priority"], "text_excerpt": text[:100] + "..."}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Enrich Qdrant with learned standards from patterns_report.json")
    parser.add_argument(
        "--patterns-report",
        default=DEFAULT_PATTERNS_REPORT,
        help="Path to patterns_report.json",
    )
    parser.add_argument(
        "--inject-clerk-standard",
        action="store_true",
        default=False,
        help="Injecte le standard Clerk hard rule directement dans Qdrant (sans patterns_report).",
    )
    parser.add_argument(
        "--inject-prisma7-standard",
        action="store_true",
        default=False,
        help="Injecte le standard Prisma 7 breaking change directement dans Qdrant (sans patterns_report).",
    )
    parser.add_argument(
        "--inject-generic-listing",
        action="store_true",
        default=False,
        help="Injecte le standard de listing générique Server Component dans Qdrant.",
    )
    parser.add_argument(
        "--inject-auth-null-guard",
        action="store_true",
        default=False,
        help="Injecte le standard auth null guard (userId check avant Prisma) dans Qdrant.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    load_dotenv(dotenv_path=".env")
    qdrant_url = _get_qdrant_url()

    if args.inject_clerk_standard or args.inject_prisma7_standard or args.inject_generic_listing or args.inject_auth_null_guard:
        _embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        _client = QdrantClient(url=qdrant_url)
        results = []
        if args.inject_clerk_standard:
            r = inject_clerk_standard(_client, _embeddings)
            r["generated_at"] = datetime.now(timezone.utc).isoformat()
            r["collection"] = QDRANT_COLLECTION_NAME
            results.append(r)
        if args.inject_prisma7_standard:
            r = inject_prisma7_standard(_client, _embeddings)
            r["generated_at"] = datetime.now(timezone.utc).isoformat()
            r["collection"] = QDRANT_COLLECTION_NAME
            results.append(r)
        if args.inject_generic_listing:
            r = inject_generic_listing_standard(_client, _embeddings)
            r["generated_at"] = datetime.now(timezone.utc).isoformat()
            r["collection"] = QDRANT_COLLECTION_NAME
            results.append(r)
        if args.inject_auth_null_guard:
            r = inject_auth_null_guard_standard(_client, _embeddings)
            r["generated_at"] = datetime.now(timezone.utc).isoformat()
            r["collection"] = QDRANT_COLLECTION_NAME
            results.append(r)
        combined = {"injected": results, "count": len(results)}
        metrics_log_path = _write_metrics_log(combined)
        combined["metrics_log_path"] = metrics_log_path
        print(json.dumps(combined, ensure_ascii=True))
    else:
        output = enrich_qdrant(patterns_report_path=args.patterns_report)
        print(json.dumps(output, ensure_ascii=True))
