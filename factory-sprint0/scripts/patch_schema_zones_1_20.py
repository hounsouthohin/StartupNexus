"""
scripts/patch_schema_zones_1_20.py

Ajoute les champs manquants rule_type / priority / trigger_context
aux standards déjà stockés dans Qdrant pour les zones 1 à 20.

Méthode : set_payload Qdrant — met à jour uniquement les métadonnées,
          SANS recalculer les embeddings (économique + idempotent).

ZONES COUVERTES :
  1-5   — Structure, Packages, TS, Next.js config, Layout       → architecture / medium  / always
  6     — Auth Clerk                                            → security     / critical / always
  7     — Prisma DB                                             → architecture / medium  / always
  8     — Jest tests                                            → architecture / low     / always
  9     — Sécurité de base                                      → security     / critical / always
  10    — Sécurité avancée                                      → security     / high    / always
  11    — Gestion d'erreurs                                     → reliability  / medium  / always
  12    — Tests avancés                                         → architecture / low     / always
  13    — Logique métier                                        → architecture / medium  / always
  14    — Anti-patterns                                         → architecture / high    / always
  15    — Conformité requirements                               → architecture / medium  / always
  16    — Sécurité applicative                                  → security     / high    / always
  17-18 — Zones complémentaires                                 → architecture / medium  / always
  19    — SaaS Senior                                           → architecture / high    / always
  20    — DAL Service                                           → architecture / high    / always

IDEMPOTENCE : set_payload ne touche que les champs listés.
  Relancer le script après un premier passage est silencieux.

COMMANDE :
  cd factory-sprint0
  docker compose exec factory-worker python scripts/patch_schema_zones_1_20.py
  docker compose exec factory-worker python scripts/patch_schema_zones_1_20.py --dry-run
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchAny

load_dotenv(dotenv_path=ROOT / ".env")

QDRANT_URL      = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "factory_standards")

# ── Mapping zone → (rule_type, priority, trigger_context) ───────────────────
# Clé : préfixe de la valeur du champ "zone" dans le payload Qdrant.
# Ex : zone="1-required-files" → préfixe "1"
ZONE_DEFAULTS: dict[str, tuple[str, str, str]] = {
    "1":  ("architecture", "medium",   "always"),
    "2":  ("architecture", "medium",   "always"),
    "3":  ("architecture", "medium",   "always"),
    "4":  ("architecture", "medium",   "always"),
    "5":  ("architecture", "medium",   "always"),
    "6":  ("security",     "critical", "always"),
    "7":  ("architecture", "medium",   "always"),
    "8":  ("architecture", "low",      "always"),
    "9":  ("security",     "critical", "always"),
    "10": ("security",     "high",     "always"),
    "11": ("reliability",  "medium",   "always"),
    "12": ("architecture", "low",      "always"),
    "13": ("architecture", "medium",   "always"),
    "14": ("architecture", "high",     "always"),
    "15": ("architecture", "medium",   "always"),
    "16": ("security",     "high",     "always"),
    "17": ("architecture", "medium",   "always"),
    "18": ("architecture", "medium",   "always"),
    "19": ("architecture", "high",     "always"),
    "20": ("architecture", "high",     "always"),
}


def _zone_prefix(zone_value: str) -> str | None:
    """Extrait le numéro de zone depuis 'X-nom-zone' ou 'X'."""
    if not zone_value:
        return None
    return zone_value.split("-")[0]


def run(dry_run: bool = False) -> None:
    client = QdrantClient(url=QDRANT_URL)

    total_scanned = 0
    total_patched = 0
    total_already_ok = 0
    offset = None

    print(f"\n{'[DRY-RUN] ' if dry_run else ''}Patch schema zones 1-20 — collection '{COLLECTION_NAME}'\n")

    while True:
        batch, next_offset = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=100,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )

        if not batch:
            break

        for point in batch:
            total_scanned += 1
            payload = point.payload or {}
            zone_val = str(payload.get("zone", ""))
            prefix = _zone_prefix(zone_val)

            if prefix not in ZONE_DEFAULTS:
                continue  # zone > 20 ou inconnue — on ne touche pas

            rule_type, priority, trigger_context = ZONE_DEFAULTS[prefix]

            # Vérifie si tous les champs sont déjà présents
            already_has = (
                "rule_type" in payload
                and "priority" in payload
                and "trigger_context" in payload
            )
            if already_has:
                total_already_ok += 1
                continue

            patch = {}
            if "rule_type" not in payload:
                patch["rule_type"] = rule_type
            if "priority" not in payload:
                patch["priority"] = priority
            if "trigger_context" not in payload:
                patch["trigger_context"] = trigger_context

            if dry_run:
                print(f"  [DRY] {point.id} zone={zone_val!r} → {patch}")
            else:
                client.set_payload(
                    collection_name=COLLECTION_NAME,
                    payload=patch,
                    points=[point.id],
                )

            total_patched += 1

        if next_offset is None:
            break
        offset = next_offset

    print(f"\nRésultat :")
    print(f"  Scannés  : {total_scanned}")
    print(f"  Déjà OK  : {total_already_ok}")
    if dry_run:
        print(f"  À patcher: {total_patched} (dry-run — rien écrit)")
    else:
        print(f"  Patchés  : {total_patched}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Affiche sans écrire")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
