"""
scripts/approve_suggestion.py — Sprint 4 item 7

Workflow y/n pour les suggestions générées par le LearnerActivity.
- Lit les events 'learner_suggestion' du shadow log
- Affiche chaque suggestion en attente (non encore approuvée/rejetée)
- y → upsert dans Qdrant avec status=active
- n → marque comme rejeté dans le shadow log
- q → interrompt la revue (reprendre plus tard)

SLA : à exécuter dans les 48h après un run significatif.
Usage : python scripts/approve_suggestion.py
"""

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

SHADOW_LOG_PATH = Path("logs/shadow/learner_shadow_log.json")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "factory_standards")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")


def text_to_uuid(text: str) -> str:
    """UUID déterministe MD5(text) — idempotence garantie."""
    hash_bytes = hashlib.md5(text.encode("utf-8")).digest()
    return str(UUID(bytes=hash_bytes))


def _load_pending_suggestions() -> list[dict]:
    if not SHADOW_LOG_PATH.exists():
        print(f"[!] Shadow log introuvable: {SHADOW_LOG_PATH}")
        return []
    try:
        log = json.loads(SHADOW_LOG_PATH.read_text(encoding="utf-8"))
        return [
            e for e in log.get("suggested_standards", [])
            if e.get("event_type") == "learner_suggestion"
            and e.get("payload", {}).get("status") not in ("approved", "rejected")
        ]
    except Exception as e:
        print(f"[!] Erreur lecture shadow log: {e}")
        return []


def _mark_suggestion(suggestion_id: str, status: str) -> None:
    try:
        log = json.loads(SHADOW_LOG_PATH.read_text(encoding="utf-8"))
        for event in log.get("suggested_standards", []):
            if (
                event.get("event_type") == "learner_suggestion"
                and event.get("payload", {}).get("suggestion_id") == suggestion_id
            ):
                event["payload"]["status"] = status
                event["payload"]["reviewed_at"] = datetime.now(timezone.utc).isoformat()
        SHADOW_LOG_PATH.write_text(
            json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception as e:
        print(f"[!] Impossible de mettre à jour le statut: {e}")


def _build_standard_text(payload: dict) -> str:
    category = payload.get("category", "anti_pattern").upper()
    title = payload.get("title", "")
    description = payload.get("description", "")
    evidence = payload.get("evidence", {})
    return (
        f"ACTION: INTERDIT\n"
        f"STACK: nextjs-clerk-prisma\n"
        f"CATEGORIE: {category}\n"
        f"TITRE: {title}\n"
        f"RAISON: {description}\n"
        f"EVIDENCE: {json.dumps(evidence, ensure_ascii=False)}\n"
        f"STATUS: active\n"
        f"SOURCE: learner_auto_detected\n"
        f"VERSION: 1.0"
    )


def _upsert_to_qdrant(payload: dict) -> bool:
    try:
        from langchain_openai import OpenAIEmbeddings
        from qdrant_client import QdrantClient
        from qdrant_client.http.models import PointStruct

        embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
        client = QdrantClient(url=QDRANT_URL)

        text = _build_standard_text(payload)
        vector = embeddings.embed_query(text)
        point_id = text_to_uuid(text)

        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "text": text,
                    "metadata": {
                        "zone": "ZONE_14_ANTIPATTERNS",
                        "category": payload.get("category", "anti_pattern"),
                        "severity": payload.get("severity", "high"),
                        "suggestion_id": payload.get("suggestion_id", ""),
                        "status": "active",
                        "source": "learner_approved",
                        "sprint": payload.get("sprint", "sprint4"),
                    },
                },
            )],
            wait=True,
        )
        print(f"  -> Upsert Qdrant OK — point_id={point_id}")
        return True
    except Exception as e:
        print(f"  [!] Erreur upsert Qdrant: {e}")
        return False


def _check_gate() -> None:
    """
    Gate Décisionnel Sprint 4 → Sprint 5.
    Seuils : >15 suggestions totales ET >70% approuvées.
    Affiche un signal et écrit logs/shadow/sprint5_gate.json si atteint.
    """
    if not SHADOW_LOG_PATH.exists():
        return
    try:
        log = json.loads(SHADOW_LOG_PATH.read_text(encoding="utf-8"))
        all_suggestions = [
            e for e in log.get("suggested_standards", [])
            if e.get("event_type") == "learner_suggestion"
        ]
        total = len(all_suggestions)
        approved_count = sum(
            1 for e in all_suggestions
            if e.get("payload", {}).get("status") == "approved"
        )
        if total == 0:
            return
        approval_rate = approved_count / total

        print(f"\n[Gate] Suggestions totales : {total}  |  Approuvees : {approved_count}  ({approval_rate:.0%})")

        gate_open = total > 15 and approval_rate > 0.70
        if gate_open:
            gate_path = SHADOW_LOG_PATH.parent / "sprint5_gate.json"
            gate_payload = {
                "gate": "sprint4_to_sprint5",
                "status": "OPEN",
                "triggered_at": datetime.now(timezone.utc).isoformat(),
                "total_suggestions": total,
                "approved": approved_count,
                "approval_rate": round(approval_rate, 3),
                "thresholds": {"min_suggestions": 15, "min_approval_rate": 0.70},
            }
            gate_path.write_text(json.dumps(gate_payload, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"\n{'=' * 70}")
            print("  GATE SPRINT 5 — OUVERT")
            print(f"  {total} suggestions, {approval_rate:.0%} approuvees (seuils: >15 / >70%)")
            print(f"  Signal ecrit : {gate_path}")
            print(f"{'=' * 70}\n")
        else:
            remaining_suggestions = max(0, 16 - total)
            remaining_rate = max(0.0, 0.71 - approval_rate)
            print(
                f"[Gate] Sprint 5 non encore debloque "
                f"({'encore ' + str(remaining_suggestions) + ' suggestion(s) requise(s)' if remaining_suggestions else ''}"
                f"{' + ' if remaining_suggestions and remaining_rate > 0 else ''}"
                f"{'taux approbation trop bas' if remaining_rate > 0 else ''})"
            )
    except Exception as e:
        print(f"[Gate] Erreur lors de la verification: {e}")


def main() -> int:
    print("\n" + "=" * 70)
    print("APPROVE SUGGESTIONS — LearnerActivity Sprint 4")
    print("  Revue des suggestions generees automatiquement par le Learner")
    print("=" * 70 + "\n")

    events = _load_pending_suggestions()
    if not events:
        print("Aucune suggestion en attente.")
        return 0

    print(f"{len(events)} suggestion(s) en attente de revue.\n")
    approved = rejected = 0

    for i, event in enumerate(events, 1):
        payload = event.get("payload", {})
        suggestion_id = payload.get("suggestion_id", f"??-{i}")
        category = payload.get("category", "?")
        severity = payload.get("severity", "?")
        title = payload.get("title", "(sans titre)")
        description = payload.get("description", "")
        evidence = payload.get("evidence", {})

        print(f"[{i}/{len(events)}] {suggestion_id}")
        print(f"  Categorie : {category}  |  Severite : {severity}")
        print(f"  Titre     : {title}")
        print(f"  Desc      : {description[:140]}")
        if evidence:
            print(f"  Evidence  : {json.dumps(evidence, ensure_ascii=False)[:100]}")
        print()

        while True:
            answer = input("  Approuver et injecter dans Qdrant ? [y/n/q] ").strip().lower()
            if answer in ("y", "n", "q"):
                break
            print("  -> Repondre y (oui), n (non) ou q (quitter)")

        if answer == "q":
            print("\n[!] Revue interrompue.")
            break
        elif answer == "y":
            success = _upsert_to_qdrant(payload)
            if success:
                _mark_suggestion(suggestion_id, "approved")
                approved += 1
        else:
            _mark_suggestion(suggestion_id, "rejected")
            rejected += 1
            print("  -> Rejete")
        print()

    print("=" * 70)
    print(f"Approuvees : {approved}  |  Rejetees : {rejected}")
    print("=" * 70 + "\n")

    _check_gate()
    return 0


if __name__ == "__main__":
    sys.exit(main())
