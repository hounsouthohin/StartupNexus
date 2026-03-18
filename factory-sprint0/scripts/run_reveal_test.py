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
from typing import List, Dict

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


REVEAL_PROJECTS: List[Dict[str, str]] = [
    # ─────────────────────────────────────────────────────────────────────────
    # BRIEF 1 — Marketplace MVP
    # Teste : 2 modèles + relation, types Float/Int/Json,
    #         pages mixtes public/privé, routes CRUD complètes
    # ─────────────────────────────────────────────────────────────────────────
    {
        "project_name": "marketplace-mvp",
        "phrase": (
            "Marketplace de produits artisanaux avec Clerk (vendeurs et acheteurs).\n"
            "\n"
            "Modèle Prisma : Product {\n"
            "  id String @id @default(cuid()),\n"
            "  name String,\n"
            "  description String,\n"
            "  price Float,\n"
            "  stock Int @default(0),\n"
            "  imageUrl String?,\n"
            "  authorId String,\n"
            "  createdAt DateTime @default(now())\n"
            "}\n"
            "\n"
            "Modèle Prisma : Order {\n"
            "  id String @id @default(cuid()),\n"
            "  productId String,\n"
            "  quantity Int,\n"
            "  totalPrice Float,\n"
            "  status String @default(\"pending\"),\n"
            "  buyerId String,\n"
            "  createdAt DateTime @default(now())\n"
            "}\n"
            "\n"
            "Pages :\n"
            "  - / : catalogue public (liste de tous les produits)\n"
            "  - /products/[id] : page détail produit publique avec bouton commande\n"
            "  - /dashboard : dashboard vendeur protégé (mes produits + mes ventes)\n"
            "  - /orders : historique commandes de l'acheteur (protégé)\n"
            "\n"
            "API Routes :\n"
            "  - GET  /api/products        : liste publique\n"
            "  - POST /api/products        : créer un produit (auth vendeur)\n"
            "  - PUT  /api/products/[id]   : modifier stock/prix (auth vendeur)\n"
            "  - POST /api/orders          : passer une commande (auth acheteur)\n"
            "  - GET  /api/orders          : mes commandes (auth acheteur)\n"
        ),
    },

    # ─────────────────────────────────────────────────────────────────────────
    # BRIEF 2 — Habit Tracker
    # Teste : relation forte Habit ↔ HabitLog, routes imbriquées [id]/log,
    #         types DateTime + Int, page analytique avec streaks
    # ─────────────────────────────────────────────────────────────────────────
    {
        "project_name": "habit-tracker",
        "phrase": (
            "Application de suivi d'habitudes personnelles avec Clerk.\n"
            "\n"
            "Modèle Prisma : Habit {\n"
            "  id String @id @default(cuid()),\n"
            "  name String,\n"
            "  description String?,\n"
            "  frequency String @default(\"daily\"),\n"
            "  targetCount Int @default(1),\n"
            "  color String @default(\"#4F46E5\"),\n"
            "  authorId String,\n"
            "  createdAt DateTime @default(now())\n"
            "}\n"
            "\n"
            "Modèle Prisma : HabitLog {\n"
            "  id String @id @default(cuid()),\n"
            "  habitId String,\n"
            "  completedAt DateTime @default(now()),\n"
            "  note String?,\n"
            "  authorId String\n"
            "}\n"
            "\n"
            "Pages :\n"
            "  - /dashboard : vue principale protégée avec liste des habitudes et streaks\n"
            "  - /habits/[id] : détail d'une habitude avec historique des logs\n"
            "\n"
            "API Routes :\n"
            "  - GET  /api/habits             : liste des habitudes de l'utilisateur\n"
            "  - POST /api/habits             : créer une habitude\n"
            "  - DELETE /api/habits/[id]      : supprimer une habitude\n"
            "  - POST /api/habits/[id]/log    : enregistrer une complétion d'habitude\n"
            "  - GET  /api/habits/[id]/log    : historique des logs d'une habitude\n"
        ),
    },

    # ─────────────────────────────────────────────────────────────────────────
    # BRIEF 3 — Invoice Generator (B2B SaaS)
    # Teste : app complexe 5 pages, relation Client ↔ Invoice,
    #         types Float + DateTime + Json, workflow de statut,
    #         route de mise à jour partielle PUT /api/invoices/[id]/status
    # ─────────────────────────────────────────────────────────────────────────
    {
        "project_name": "invoice-generator",
        "phrase": (
            "Générateur de factures B2B avec Clerk (freelances et PME).\n"
            "\n"
            "Modèle Prisma : Client {\n"
            "  id String @id @default(cuid()),\n"
            "  name String,\n"
            "  email String,\n"
            "  company String?,\n"
            "  address String?,\n"
            "  authorId String,\n"
            "  createdAt DateTime @default(now())\n"
            "}\n"
            "\n"
            "Modèle Prisma : Invoice {\n"
            "  id String @id @default(cuid()),\n"
            "  clientId String,\n"
            "  invoiceNumber String @unique,\n"
            "  amount Float,\n"
            "  status String @default(\"draft\"),\n"
            "  dueDate DateTime,\n"
            "  items Json,\n"
            "  notes String?,\n"
            "  authorId String,\n"
            "  createdAt DateTime @default(now())\n"
            "}\n"
            "\n"
            "Pages :\n"
            "  - /dashboard : résumé financier (chiffre d'affaires, factures en attente)\n"
            "  - /clients : liste des clients (protégé)\n"
            "  - /clients/[id] : fiche client avec ses factures\n"
            "  - /invoices : liste de toutes les factures avec filtres par statut\n"
            "  - /invoices/[id] : détail d'une facture (aperçu PDF-like)\n"
            "\n"
            "API Routes :\n"
            "  - GET  /api/clients             : liste des clients\n"
            "  - POST /api/clients             : créer un client\n"
            "  - GET  /api/invoices            : liste des factures\n"
            "  - POST /api/invoices            : créer une facture\n"
            "  - PUT  /api/invoices/[id]/status : changer le statut (draft→sent→paid)\n"
        ),
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

        print(f"  [{status:14s}] {name}")
        print(f"               requirements={reqs}  spec_coverage={coverage}  user_flows={flows_covered}/{flows_total}")
        if error_snippet:
            print(f"               erreur: {error_snippet}")
        print()

    print(f"  Métriques écrites : {result.get('metrics_log_path', 'N/A')}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
