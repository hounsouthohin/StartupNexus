"""
Reveal Test — 3 briefs révélateurs de la capacité d'adaptation du moteur.

Objectif : tester la généralisation sur des domaines métier réels,
hors du périmètre des sanity runs (Blog CMS + Todo variants).

Les 3 briefs sont conçus pour stresser des dimensions précises :

  Brief 1 — marketplace-mvp
    · 2 modèles Prisma avec relation (Product ↔ Order)
    · Types variés : Float (price), Int (stock), Json (items)
    · Dualité acheteur/vendeur (pages publiques + privées)
    · Routes imbriquées : PUT /api/products/[id], POST /api/orders

  Brief 2 — habit-tracker
    · 2 modèles avec relation forte (Habit ↔ HabitLog)
    · Routes imbriquées profondes : POST /api/habits/[id]/log
    · Page analytique (/dashboard avec streaks)
    · Types : DateTime (completedAt), Int (targetCount)

  Brief 3 — invoice-generator
    · 2 modèles B2B avec relation Client ↔ Invoice
    · 5 pages distinctes (app complexe)
    · Types : Float (amount), DateTime (dueDate), Json (items), String status
    · Workflow de statut : draft → sent → paid
    · Route de mise à jour de statut : PUT /api/invoices/[id]/status

Usage (depuis factory-sprint0/) :
  python scripts/run_reveal_test.py --sanity-mode
  python scripts/run_reveal_test.py           # run complet (avec QA, GitHub, Learner)
"""

from __future__ import annotations

import asyncio
import argparse
import json
import os
import sys
from typing import Any, Dict, List

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


REVEAL_PROJECTS: List[Dict[str, Any]] = [
    # ─────────────────────────────────────────────────────────────────────────
    # BRIEF 1 — Marketplace MVP
    # Teste : 2 modèles + relation, types Float/Int/Json,
    #         pages mixtes public/privé, routes CRUD complètes
    # ─────────────────────────────────────────────────────────────────────────
    {
        "project_name": "marketplace-mvp",
        "brief": {
            "description": "Marketplace de produits artisanaux avec Clerk (vendeurs et acheteurs).",
            "models": [
                "Product { id String @id @default(cuid()), name String, description String, price Float, stock Int @default(0), imageUrl String?, authorId String, createdAt DateTime @default(now()) }",
                "Order { id String @id @default(cuid()), productId String, quantity Int, totalPrice Float, status String @default(\"pending\"), buyerId String, createdAt DateTime @default(now()) }",
            ],
            "pages": [
                {"path": "/", "auth": False},
                {"path": "/products/[id]", "auth": False},
                {"path": "/dashboard", "auth": True},
                {"path": "/orders", "auth": True},
            ],
            "routes": [
                {"method": "GET", "path": "/api/products"},
                {"method": "POST", "path": "/api/products"},
                {"method": "PUT", "path": "/api/products/[id]"},
                {"method": "POST", "path": "/api/orders"},
                {"method": "GET", "path": "/api/orders"},
            ],
        },
    },

    # ─────────────────────────────────────────────────────────────────────────
    # BRIEF 2 — Habit Tracker
    # Teste : relation forte Habit ↔ HabitLog, routes imbriquées [id]/log,
    #         types DateTime + Int, page analytique avec streaks
    # ─────────────────────────────────────────────────────────────────────────
    {
        "project_name": "habit-tracker",
        "brief": {
            "description": "Application de suivi d'habitudes personnelles avec Clerk.",
            "models": [
                "Habit { id String @id @default(cuid()), name String, description String?, frequency String @default(\"daily\"), targetCount Int @default(1), color String @default(\"#4F46E5\"), authorId String, createdAt DateTime @default(now()) }",
                "HabitLog { id String @id @default(cuid()), habitId String, completedAt DateTime @default(now()), note String?, authorId String }",
            ],
            "pages": [
                {"path": "/dashboard", "auth": True},
                {"path": "/habits/[id]", "auth": True},
            ],
            "routes": [
                {"method": "GET", "path": "/api/habits"},
                {"method": "POST", "path": "/api/habits"},
                {"method": "DELETE", "path": "/api/habits/[id]"},
                {"method": "POST", "path": "/api/habits/[id]/log"},
                {"method": "GET", "path": "/api/habits/[id]/log"},
            ],
        },
    },

    # ─────────────────────────────────────────────────────────────────────────
    # BRIEF 3 — Invoice Generator (B2B SaaS)
    # Teste : app complexe 5 pages, relation Client ↔ Invoice,
    #         types Float + DateTime + Json, workflow de statut,
    #         route de mise à jour partielle PUT /api/invoices/[id]/status
    # ─────────────────────────────────────────────────────────────────────────
    {
        "project_name": "invoice-generator",
        "brief": {
            "description": "Générateur de factures B2B avec Clerk (freelances et PME).",
            "models": [
                "Client { id String @id @default(cuid()), name String, email String, company String?, address String?, authorId String, createdAt DateTime @default(now()) }",
                "Invoice { id String @id @default(cuid()), clientId String, invoiceNumber String @unique, amount Float, status String @default(\"draft\"), dueDate DateTime, items Json, notes String?, authorId String, createdAt DateTime @default(now()) }",
            ],
            "pages": [
                {"path": "/dashboard", "auth": True},
                {"path": "/clients", "auth": True},
                {"path": "/clients/[id]", "auth": True},
                {"path": "/invoices", "auth": True},
                {"path": "/invoices/[id]", "auth": True},
            ],
            "routes": [
                {"method": "GET", "path": "/api/clients"},
                {"method": "POST", "path": "/api/clients"},
                {"method": "GET", "path": "/api/invoices"},
                {"method": "POST", "path": "/api/invoices"},
                {"method": "PUT", "path": "/api/invoices/[id]/status"},
            ],
        },
    },
]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reveal Test — 3 briefs métier révélateurs de la capacité d'adaptation du moteur"
    )
    parser.add_argument(
        "--sanity-mode",
        action="store_true",
        help="Mode sanity: arrêt après dev_test_activity (skip QA/GitHub/Learner). Recommandé pour diagnostics rapides.",
    )
    parser.add_argument(
        "--result-timeout-seconds",
        type=float,
        default=None,
        help="Timeout par workflow (secondes). Par défaut: attente complète.",
    )
    parser.add_argument(
        "--only",
        type=str,
        choices=["marketplace-mvp", "habit-tracker", "invoice-generator"],
        default=None,
        help="Exécuter un seul brief (debug ciblé).",
    )
    return parser.parse_args()


async def main() -> None:
    args = _parse_args()

    from scripts.run_batch import run_batch

    projects = REVEAL_PROJECTS
    if args.only:
        projects = [p for p in REVEAL_PROJECTS if p["project_name"] == args.only]

    print(f"\n{'='*60}")
    print(f"  REVEAL TEST — {len(projects)} brief(s)")
    print(f"  Sanity mode : {args.sanity_mode}")
    print(f"  Projets     : {[p['project_name'] for p in projects]}")
    print(f"{'='*60}\n")

    result = await run_batch(
        projects=projects,
        result_timeout_seconds=args.result_timeout_seconds,
        sanity_mode=args.sanity_mode,
    )

    # ── Résumé lisible ─────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  RÉSULTATS REVEAL TEST")
    print(f"{'='*60}")
    print(f"  BUILD_SUCCESS  : {result['build_success_count']}/{len(projects)}")
    print(f"  BUILD_PARTIAL  : {result.get('build_partial_count', 0)}/{len(projects)}")
    print(f"  BUILD_FAILED   : {result.get('build_failure_count', 0)}/{len(projects)}")
    print(f"  Durée totale   : {result['total_duration_seconds']}s")
    print()

    for run in result.get("runs", []):
        status = run.get("build_status", "UNKNOWN")
        name = run["project_name"]
        reqs = run.get("activity_results", {}).get("architect", {}).get("requirements_count", "?")
        metric = run.get("run_metric", {})
        coverage = metric.get("spec_coverage", "?")
        error_snippet = (metric.get("last_build_error", "") or "")[:120]
        journeys = run.get("activity_results", {}).get("dev_test", {}).get("metadata", {})
        flows_covered = journeys.get("user_flows_covered", "?")
        flows_total = journeys.get("user_flows_total", "?")

        print(f"  [{(status or 'UNKNOWN'):14s}] {name}")
        print(f"               requirements={reqs}  spec_coverage={coverage}  user_flows={flows_covered}/{flows_total}")
        if error_snippet:
            print(f"               erreur: {error_snippet}")
        print()

    print(f"  Métriques écrites : {result.get('metrics_log_path', 'N/A')}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
