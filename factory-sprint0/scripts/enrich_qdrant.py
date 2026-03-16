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


UNTYPED_ARRAY_STANDARD = {
    "category": "typescript",
    "text": (
        "TypeScript strict — tableau non typé INTERDIT dans les Server Components et API Routes (OBLIGATOIRE). "
        "Le pattern `let data = []` suivi d'une réassignation dans try/catch est invalide en TypeScript strict : "
        "le compilateur infère `any[]` et rejette le build avec 'implicitly has type any[]'. "
        "PATTERN INTERDIT : "
        "  let books = [];  // ← TypeScript strict refuse — any[] implicite "
        "  try { books = await prisma.book.findMany(...) } catch { } "
        "PATTERN OBLIGATOIRE — 2 formes autorisées : "
        "Forme 1 (préférée) : const data = await prisma.<model>.findMany({...}).catch(() => []); "
        "Forme 2 (si try/catch explicite requis) : "
        "  import type { Book } from '@prisma/client'; "
        "  let books: Book[] = []; "
        "  try { books = await prisma.book.findMany({...}); } catch { books = []; } "
        "La Forme 1 est plus concise et évite la variable mutable. "
        "Toujours typer explicitement si une variable tableau est déclarée avant son assignation Prisma."
    ),
    "tags": ["typescript", "strict", "array", "prisma", "any", "type-inference", "server-component"],
    "priority": "HIGH",
}


def inject_untyped_array_standard(client: QdrantClient, embeddings: OpenAIEmbeddings) -> dict:
    """Injecte le standard TypeScript strict — tableau non typé interdit."""
    text = UNTYPED_ARRAY_STANDARD["text"]
    vector = embeddings.embed_query(text)
    point_id = text_to_uuid(text)
    payload = {
        "text": text,
        "metadata": {
            "category": UNTYPED_ARRAY_STANDARD["category"],
            "tags": UNTYPED_ARRAY_STANDARD["tags"],
            "priority": UNTYPED_ARRAY_STANDARD["priority"],
            "source": "manual_injection",
            "tech": "typescript,prisma,nextjs",
            "version": "static",
            "outcome": "hard_rule",
            "stack": "nextjs-clerk-prisma",
            "status": "active",
            "zone": "ZONE_16-typescript-strict",
        },
    }
    client.upsert(
        collection_name=QDRANT_COLLECTION_NAME,
        points=[PointStruct(id=point_id, vector=vector, payload=payload)],
        wait=True,
    )
    return {
        "point_id": point_id,
        "category": UNTYPED_ARRAY_STANDARD["category"],
        "priority": UNTYPED_ARRAY_STANDARD["priority"],
        "text_excerpt": text[:100] + "...",
    }


APP_ROUTER_ROUTING_STANDARD = {
    "category": "nextjs",
    "text": (
        "Next.js 14 App Router — convention de routing URL vers fichier (OBLIGATOIRE). "
        "Chaque segment d'URL correspond à un dossier dans app/, la page est page.tsx dans ce dossier. "
        "MAPPING EXACT : "
        "route '/' → app/page.tsx (page d'accueil — OBLIGATOIRE pour tout projet). "
        "route '/dashboard' → app/dashboard/page.tsx. "
        "route '/[slug]' → app/[slug]/page.tsx. "
        "route '/blog/[slug]' → app/blog/[slug]/page.tsx. "
        "route '/api/posts/[id]' → app/api/posts/[id]/route.ts. "
        "app/page.tsx EST OBLIGATOIRE — c'est la page racine du projet, elle doit toujours exister. "
        "app/page.tsx doit être un Server Component (pas de 'use client', pas de useState/useEffect). "
        "app/page.tsx doit afficher la liste des entités principales du projet via prisma.<modèle>.findMany "
        "où <modèle> est le nom camelCase du modèle Prisma du brief (ex: post→prisma.post, task→prisma.task). "
        "Ne jamais laisser app/page.tsx vide — il doit lister les vraies données du brief. "
        "Toujours inclure export const dynamic = 'force-dynamic' et un try/catch avec fallback []."
    ),
    "tags": ["nextjs", "app-router", "routing", "page.tsx", "home", "server-component", "convention"],
    "priority": "HIGH",
}

PRISMA_SCHEMA_STRUCTURE_STANDARD = {
    "category": "prisma",
    "text": (
        "Prisma schema structure canonique (OBLIGATOIRE). "
        "Dans prisma/schema.prisma, les blocs datasource et generator doivent être explicites et multi-lignes. "
        "Format valide minimal : "
        "datasource db {\n  provider = \"postgresql\"\n}\n"
        "generator client {\n  provider = \"prisma-client-js\"\n}. "
        "Eviter les variantes ambiguës/compactées qui déclenchent P1012. "
        "Ne pas mettre datasource.url dans schema.prisma avec Prisma 7 (garder l'URL dans prisma.config.ts). "
        "Si Prisma retourne 'This line is not a valid definition within a datasource', "
        "reconstruire les deux blocs exactement au format canonique ci-dessus avant run_build."
    ),
    "tags": ["prisma", "schema", "datasource", "generator", "p1012", "prisma7", "structure"],
    "priority": "CRITICAL",
}


# ID du standard Prisma 7 datasource contradictoire à corriger dans Qdrant
# (l'ancienne version indiquait que url = env(...) dans schema.prisma était "valide")
PRISMA7_DATASOURCE_STANDARD_ID = "ab928ac6-fdea-fb3d-f40e-b4e20620c4d5"

PRISMA7_DATASOURCE_CORRECTED_TEXT = (
    "ACTION: OBLIGATOIRE\n"
    "STACK: nextjs-clerk-prisma\n"
    "TECHNOLOGIE: Prisma 7 — générer schema.prisma ET prisma.config.ts\n"
    "RAISON: (Perplexity confirmé) Prisma 7 introduit prisma.config.ts. "
    "La datasource URL doit être portée par prisma.config.ts UNIQUEMENT. "
    "`url = env(\"DATABASE_URL\")` dans schema.prisma est INTERDIT — le gate prisma_schema_datasource_url "
    "bloque le build si cette ligne est présente dans schema.prisma.\n"
    "FICHIERS_OBLIGATOIRES:\n"
    "  prisma/schema.prisma  — datasource + generator + modèles\n"
    "  prisma.config.ts      — defineConfig depuis 'prisma/config'\n"
    "CONFIGURATION_SCHEMA_PRISMA:\n"
    "  datasource db {\n"
    "    provider = \"postgresql\"\n"
    "  }\n"
    "  generator client {\n"
    "    provider = \"prisma-client-js\"\n"
    "  }\n"
    "CONFIGURATION_PRISMA_CONFIG_TS:\n"
    "  import 'dotenv/config';\n"
    "  import { defineConfig, env } from 'prisma/config';\n"
    "  export default defineConfig({\n"
    "    schema: 'prisma/schema.prisma',\n"
    "    datasource: { url: env('DATABASE_URL') },\n"
    "  });\n"
    "DETECTION_REGEX: prisma\\.config\\.ts\n"
    "ALTERNATIVE: Générer les deux fichiers systématiquement\n"
    "EXEMPLE_INVALIDE:\n"
    "  datasource db {\n"
    "    provider = \"postgresql\"\n"
    "    url      = env(\"DATABASE_URL\")  <- INTERDIT PRISMA 7 — gate bloque le build\n"
    "  }\n"
    "EXEMPLE_VALIDE: prisma/schema.prisma (sans url) + prisma.config.ts (avec url)\n"
    "ERREUR_ATTENDUE: GateBlocked: NOT_BUILT_BY_GATE (prisma_schema_datasource_url)\n"
    "STATUS: active\n"
    "VERSION: 1.1"
)


def fix_prisma7_datasource_standard(client: QdrantClient, embeddings: OpenAIEmbeddings) -> dict:
    """Corrige le standard Prisma 7 datasource contradictoire dans Qdrant (upsert ciblé par ID).

    L'ancien standard (ab928ac6) disait que url = env(...) dans schema.prisma était 'valide',
    en contradiction directe avec le gate prisma_schema_datasource_url qui le bloque.
    Ce fix remplace le contenu du point existant avec la version corrigée (v1.1).
    """
    text = PRISMA7_DATASOURCE_CORRECTED_TEXT
    vector = embeddings.embed_query(text)
    payload = {
        "text": text,
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "7-prisma",
            "status": "active",
            "version": "1.1",
            "category": "prisma",
            "source": "factory_standards_v2",
        },
    }
    client.upsert(
        collection_name=QDRANT_COLLECTION_NAME,
        points=[PointStruct(id=PRISMA7_DATASOURCE_STANDARD_ID, vector=vector, payload=payload)],
        wait=True,
    )
    return {
        "point_id": PRISMA7_DATASOURCE_STANDARD_ID,
        "action": "fix_prisma7_datasource",
        "text_excerpt": text[:120] + "...",
    }


def inject_app_router_routing_standard(client: QdrantClient, embeddings: OpenAIEmbeddings) -> dict:
    """Insère le standard de routing App Router (/ → app/page.tsx) dans Qdrant."""
    text = APP_ROUTER_ROUTING_STANDARD["text"]
    vector = embeddings.embed_query(text)
    point_id = text_to_uuid(text)
    payload = {
        "text": text,
        "metadata": {
            "category": APP_ROUTER_ROUTING_STANDARD["category"],
            "tags": APP_ROUTER_ROUTING_STANDARD["tags"],
            "priority": APP_ROUTER_ROUTING_STANDARD["priority"],
            "source": "manual_injection",
            "tech": "nextjs,app-router",
            "version": "static",
            "outcome": "hard_rule",
            "stack": "nextjs-clerk-prisma",
            "status": "active",
            "zone": "ZONE_15-app-router-routing",
        },
    }
    client.upsert(
        collection_name=QDRANT_COLLECTION_NAME,
        points=[PointStruct(id=point_id, vector=vector, payload=payload)],
        wait=True,
    )
    return {
        "point_id": point_id,
        "category": APP_ROUTER_ROUTING_STANDARD["category"],
        "priority": APP_ROUTER_ROUTING_STANDARD["priority"],
        "text_excerpt": text[:100] + "...",
    }


def inject_prisma_schema_structure_standard(client: QdrantClient, embeddings: OpenAIEmbeddings) -> dict:
    """Injecte un standard Prisma canonique pour la structure datasource/generator."""
    text = PRISMA_SCHEMA_STRUCTURE_STANDARD["text"]
    vector = embeddings.embed_query(text)
    point_id = text_to_uuid(text)
    payload = {
        "text": text,
        "metadata": {
            "category": PRISMA_SCHEMA_STRUCTURE_STANDARD["category"],
            "tags": PRISMA_SCHEMA_STRUCTURE_STANDARD["tags"],
            "priority": PRISMA_SCHEMA_STRUCTURE_STANDARD["priority"],
            "source": "manual_injection",
            "tech": "prisma,nextjs",
            "version": "static",
            "outcome": "hard_rule",
            "stack": "nextjs-clerk-prisma",
            "status": "active",
            "zone": "7-prisma",
        },
    }
    client.upsert(
        collection_name=QDRANT_COLLECTION_NAME,
        points=[PointStruct(id=point_id, vector=vector, payload=payload)],
        wait=True,
    )
    return {
        "point_id": point_id,
        "category": PRISMA_SCHEMA_STRUCTURE_STANDARD["category"],
        "priority": PRISMA_SCHEMA_STRUCTURE_STANDARD["priority"],
        "text_excerpt": text[:100] + "...",
    }


def _infer_zone_from_metadata(metadata: dict, default_zone: str) -> str:
    category = str((metadata or {}).get("category", "")).strip().lower()
    mapping = {
        "prisma": "7-prisma",
        "clerk": "6-clerk",
        "nextjs": "4-nextjs",
        "typescript": "3-typescript",
        "testing": "8-testing",
        "security": "9-security",
        "learner_pattern": "14-antipatterns",
    }
    return mapping.get(category, default_zone)


def backfill_source_zone_metadata(
    client: QdrantClient,
    default_source: str = "factory_standards_v2",
    default_zone: str = "unclassified",
) -> dict:
    """
    Backfill non destructif des champs metadata.source et metadata.zone.
    Ne remplace pas les valeurs existantes; complète uniquement les champs manquants/vides.
    """
    offset = None
    scanned = 0
    updated = 0
    missing_source_before = 0
    missing_zone_before = 0

    while True:
        points, offset = client.scroll(
            collection_name=QDRANT_COLLECTION_NAME,
            limit=200,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        if not points:
            break
        for p in points:
            scanned += 1
            payload = p.payload or {}
            metadata = payload.get("metadata", {})
            if not isinstance(metadata, dict):
                metadata = {}

            source = str(metadata.get("source", "") or "").strip()
            zone = str(metadata.get("zone", "") or "").strip()
            changed = False

            if not source:
                missing_source_before += 1
                metadata["source"] = default_source
                changed = True
            if not zone:
                missing_zone_before += 1
                metadata["zone"] = _infer_zone_from_metadata(metadata, default_zone)
                changed = True

            if changed:
                client.set_payload(
                    collection_name=QDRANT_COLLECTION_NAME,
                    points=[p.id],
                    payload={"metadata": metadata},
                )
                updated += 1

        if offset is None:
            break

    return {
        "action": "backfill_metadata_source_zone",
        "collection": QDRANT_COLLECTION_NAME,
        "scanned": scanned,
        "updated": updated,
        "missing_source_before": missing_source_before,
        "missing_zone_before": missing_zone_before,
        "default_source": default_source,
        "default_zone": default_zone,
    }


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
    parser.add_argument(
        "--inject-app-router-routing",
        action="store_true",
        default=False,
        help="Injecte le standard App Router routing (/ → app/page.tsx) dans Qdrant.",
    )
    parser.add_argument(
        "--fix-prisma7-datasource",
        action="store_true",
        default=False,
        help="Corrige le standard Prisma 7 datasource (ab928ac6) — supprime url=env(...) de schema.prisma.",
    )
    parser.add_argument(
        "--inject-untyped-array",
        action="store_true",
        default=False,
        help="Injecte le standard TypeScript strict — tableau non typé interdit (let x = [] sans type).",
    )
    parser.add_argument(
        "--inject-prisma-schema-structure",
        action="store_true",
        default=False,
        help="Injecte le standard Prisma schema canonique (datasource/generator multi-lignes).",
    )
    parser.add_argument(
        "--backfill-metadata-source-zone",
        action="store_true",
        default=False,
        help="Complète metadata.source et metadata.zone pour les points Qdrant incomplets.",
    )
    parser.add_argument(
        "--default-metadata-source",
        default="factory_standards_v2",
        help="Valeur source par défaut lors du backfill (si absente).",
    )
    parser.add_argument(
        "--default-metadata-zone",
        default="unclassified",
        help="Valeur zone par défaut lors du backfill (si absente et non inférable).",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    load_dotenv(dotenv_path=".env")
    qdrant_url = _get_qdrant_url()

    if (
        args.inject_clerk_standard
        or args.inject_prisma7_standard
        or args.inject_generic_listing
        or args.inject_auth_null_guard
        or args.inject_app_router_routing
        or args.fix_prisma7_datasource
        or args.inject_untyped_array
        or args.inject_prisma_schema_structure
        or args.backfill_metadata_source_zone
    ):
        _client = QdrantClient(url=qdrant_url)
        results = []
        _embeddings = None
        if (
            args.inject_clerk_standard
            or args.inject_prisma7_standard
            or args.inject_generic_listing
            or args.inject_auth_null_guard
            or args.inject_app_router_routing
            or args.fix_prisma7_datasource
            or args.inject_untyped_array
            or args.inject_prisma_schema_structure
        ):
            _embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
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
        if args.inject_app_router_routing:
            r = inject_app_router_routing_standard(_client, _embeddings)
            r["generated_at"] = datetime.now(timezone.utc).isoformat()
            r["collection"] = QDRANT_COLLECTION_NAME
            results.append(r)
        if args.fix_prisma7_datasource:
            r = fix_prisma7_datasource_standard(_client, _embeddings)
            r["generated_at"] = datetime.now(timezone.utc).isoformat()
            r["collection"] = QDRANT_COLLECTION_NAME
            results.append(r)
        if args.inject_untyped_array:
            r = inject_untyped_array_standard(_client, _embeddings)
            r["generated_at"] = datetime.now(timezone.utc).isoformat()
            r["collection"] = QDRANT_COLLECTION_NAME
            results.append(r)
        if args.inject_prisma_schema_structure:
            r = inject_prisma_schema_structure_standard(_client, _embeddings)
            r["generated_at"] = datetime.now(timezone.utc).isoformat()
            r["collection"] = QDRANT_COLLECTION_NAME
            results.append(r)
        if args.backfill_metadata_source_zone:
            r = backfill_source_zone_metadata(
                _client,
                default_source=args.default_metadata_source,
                default_zone=args.default_metadata_zone,
            )
            r["generated_at"] = datetime.now(timezone.utc).isoformat()
            results.append(r)
        combined = {"injected": results, "count": len(results)}
        metrics_log_path = _write_metrics_log(combined)
        combined["metrics_log_path"] = metrics_log_path
        print(json.dumps(combined, ensure_ascii=True))
    else:
        output = enrich_qdrant(patterns_report_path=args.patterns_report)
        print(json.dumps(output, ensure_ascii=True))
