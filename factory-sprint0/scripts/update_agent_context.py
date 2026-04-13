"""
scripts/update_agent_context.py

Recalibrage RAG — Phase 1 (17 Mars 2026)
Objectif : séparer les standards par agent consommateur sans reset complet.

Ce script effectue 2 opérations :
  1. Ajoute metadata.agent_context="dev" à TOUS les points existants dans Qdrant
     (Zone 1-14 sont des standards d'implémentation, réservés au DevAgent)
  2. Injecte les 5 standards Zone 0 (agent_context="architect") pour le planner

PROCÉDURE :
  python scripts/update_agent_context.py

Prérequis :
  - Qdrant en ligne (docker compose up)
  - Collection factory_standards existante et peuplée (Zone 1-14)

POURQUOI ce script au lieu de reset + reinject ?
  - Préserve les standards Zone 14 (learner suggestions) injectés via approve_suggestion.py
  - Mise à jour idempotente (set_payload écrase la valeur si déjà présente)
  - Plus rapide (pas de ré-embedding des 53 standards existants)

Après ce script, lancer un sanity run pour vérifier :
  - Le planner reçoit uniquement des standards Zone 0 (planning domain)
  - Le DevAgent reçoit uniquement des standards Zone 1-14 (implémentation)
"""

from __future__ import annotations

import hashlib
import os
from uuid import UUID

from dotenv import load_dotenv
from agents.embedding_provider import get_embeddings
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, Filter, FieldCondition, MatchValue

load_dotenv(dotenv_path=".env")

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "factory_standards")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
EMBEDDINGS = get_embeddings(EMBEDDING_MODEL)


def text_to_uuid(text: str) -> str:
    """UUID déterministe basé sur MD5(text) — idempotence garantie."""
    hash_bytes = hashlib.md5(text.encode("utf-8")).digest()
    return str(UUID(bytes=hash_bytes))


# =============================================================================
# ZONE 0 — Standards de planification (agent_context=architect)
# Importés depuis create_full_standards_v1.py pour cohérence
# =============================================================================

try:
    from scripts import create_full_standards_v1 as _standards_module
except ImportError:
    # Fallback si lancé depuis la racine
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from scripts import create_full_standards_v1 as _standards_module

ZONE_0_PLANNING = getattr(_standards_module, "ZONE_0_PLANNING", [])
if not ZONE_0_PLANNING:
    print("⚠️  ZONE_0_PLANNING absent dans create_full_standards_v1.py — étape 2 ignorée.")


def step1_tag_existing_as_dev(client: QdrantClient) -> int:
    """
    Étape 1 : parcourt tous les points Qdrant et ajoute agent_context="dev"
    à ceux qui n'ont pas encore ce champ.
    Utilise scroll + set_payload (pas de ré-embedding).
    """
    print("\n📋 Étape 1 — Taggage des standards existants (agent_context=dev)")
    updated = 0
    skipped = 0
    offset = None

    while True:
        records, next_offset = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=100,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        if not records:
            break

        for record in records:
            payload = record.payload or {}
            metadata = payload.get("metadata", {})

            # Ignorer les points qui ont déjà agent_context
            if "agent_context" in metadata:
                skipped += 1
                continue

            # Ne pas toucher aux standards Zone 0 (déjà architect)
            if metadata.get("zone", "").startswith("0-"):
                skipped += 1
                continue

            # Ajouter agent_context=dev
            updated_metadata = {**metadata, "agent_context": "dev"}
            client.set_payload(
                collection_name=COLLECTION_NAME,
                payload={"metadata": updated_metadata},
                points=[record.id],
            )
            updated += 1

        if next_offset is None:
            break
        offset = next_offset

    print(f"   ✅ Mis à jour : {updated} standards → agent_context=dev")
    print(f"   ⏭  Ignorés (déjà tagués ou Zone 0) : {skipped}")
    return updated


def step2_inject_zone0(client: QdrantClient) -> int:
    """
    Étape 2 : injecte les standards Zone 0 (agent_context=architect).
    Idempotent via UUID déterministe.
    """
    print("\n📋 Étape 2 — Injection Zone 0 (planning standards, agent_context=architect)")
    injected = 0
    skipped = 0

    for std in ZONE_0_PLANNING:
        if std["metadata"].get("status") == "draft":
            print(f"   ⏳ Draft ignoré : {std['text'][:60]}...")
            continue

        point_id = text_to_uuid(std["text"])

        # Vérifier si déjà présent
        existing = client.retrieve(
            collection_name=COLLECTION_NAME,
            ids=[point_id],
            with_payload=False,
            with_vectors=False,
        )
        if existing:
            skipped += 1
            preview = std["text"].replace("\n", " ")[:60]
            print(f"   ⏭  Déjà présent : {preview}...")
            continue

        vector = EMBEDDINGS.embed_query(std["text"])
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[PointStruct(
                id=point_id,
                vector=vector,
                payload={"text": std["text"], "metadata": std["metadata"]},
            )],
            wait=True,
        )
        preview = std["text"].replace("\n", " ")[:60]
        print(f"   ✅  Injecté : {preview}...")
        injected += 1

    print(f"\n   ✅ Zone 0 injectés : {injected}, déjà présents : {skipped}")
    return injected


def step3_verify(client: QdrantClient) -> None:
    """
    Étape 3 : vérifie la distribution agent_context dans la collection.
    """
    print("\n📋 Étape 3 — Vérification de la distribution")

    # Compter les standards dev
    dev_count = client.count(
        collection_name=COLLECTION_NAME,
        count_filter=Filter(must=[
            FieldCondition(key="metadata.agent_context", match=MatchValue(value="dev"))
        ]),
        exact=True,
    ).count

    # Compter les standards architect
    architect_count = client.count(
        collection_name=COLLECTION_NAME,
        count_filter=Filter(must=[
            FieldCondition(key="metadata.agent_context", match=MatchValue(value="architect"))
        ]),
        exact=True,
    ).count

    # Total
    total = client.count(collection_name=COLLECTION_NAME, exact=True).count

    untagged = total - dev_count - architect_count

    print(f"   📊 Total standards         : {total}")
    print(f"   🔧 agent_context=dev       : {dev_count}")
    print(f"   🏗  agent_context=architect : {architect_count}")
    if untagged > 0:
        print(f"   ⚠️  Sans agent_context     : {untagged}  ← à corriger (relancer ce script)")
    else:
        print(f"   ✅  Tous les standards sont taggés")

    # Vérification Zone 0
    zone0 = client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=Filter(must=[
            FieldCondition(key="metadata.zone", match=MatchValue(value="0-planning"))
        ]),
        limit=10,
        with_payload=True,
        with_vectors=False,
    )[0]
    print(f"\n   🏗  Zone 0 standards ({len(zone0)} trouvés) :")
    for r in zone0:
        meta = r.payload.get("metadata", {})
        preview = r.payload.get("text", "")[:70].replace("\n", " ")
        print(f"      - [{meta.get('agent_context', '?')}] {preview}...")


def main() -> int:
    print("\n" + "=" * 70)
    print("🔄 RECALIBRAGE RAG — Séparation architect/dev")
    print("   Objectif : agent_context pour tous les standards Qdrant")
    print("=" * 70)

    client = QdrantClient(url=QDRANT_URL)

    # Vérification connexion
    try:
        collections = client.get_collections()
        names = [c.name for c in collections.collections]
        if COLLECTION_NAME not in names:
            print(f"❌ Collection '{COLLECTION_NAME}' introuvable.")
            print("   → Exécutez d'abord: python scripts/reset_qdrant.py && python scripts/create_full_standards_v1.py")
            return 1
        count = client.count(collection_name=COLLECTION_NAME, exact=True).count
        print(f"✅ Qdrant OK — '{COLLECTION_NAME}' ({count} points)")
    except Exception as e:
        print(f"❌ Connexion Qdrant: {e}")
        return 1

    # Étapes
    step1_tag_existing_as_dev(client)
    step2_inject_zone0(client)
    step3_verify(client)

    print("\n" + "=" * 70)
    print("✅ Recalibrage terminé.")
    print("   → Lancer un sanity run pour vérifier l'amélioration du planner.")
    print("=" * 70 + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
