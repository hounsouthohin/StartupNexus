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
        "version ^5.0.0. Les packages @clerk/clerk-sdk, @clerk/clerk-js, "
        "@clerk/sdk, @clerk/react n'existent pas ou sont obsolètes et ne doivent "
        "jamais apparaître dans package.json. "
        "Import server-side : from '@clerk/nextjs/server'. "
        "Import client-side : from '@clerk/nextjs'. "
        "Ne jamais inventer de variante du nom du package Clerk."
    ),
    "tags": ["clerk", "npm", "package", "install", "nextjs", "dependency", "version"],
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
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    load_dotenv(dotenv_path=".env")
    qdrant_url = _get_qdrant_url()

    if args.inject_clerk_standard or args.inject_prisma7_standard:
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
        combined = {"injected": results, "count": len(results)}
        metrics_log_path = _write_metrics_log(combined)
        combined["metrics_log_path"] = metrics_log_path
        print(json.dumps(combined, ensure_ascii=True))
    else:
        output = enrich_qdrant(patterns_report_path=args.patterns_report)
        print(json.dumps(output, ensure_ascii=True))
