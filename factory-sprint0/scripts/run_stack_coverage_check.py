"""
Stack Coverage Check — test santé global Next.js + Clerk + Prisma.

But:
- Exécuter une batterie de briefs couvrant les patterns majeurs de la stack.
- Donner un score de couverture par domaine métier (RBAC, booking, billing, etc.).

Usage (depuis factory-sprint0/):
  .\\venv\\Scripts\\python.exe scripts\\run_stack_coverage_check.py --sanity-mode
  .\\venv\\Scripts\\python.exe scripts\\run_stack_coverage_check.py
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from collections import defaultdict
from typing import Dict, List

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


STACK_COVERAGE_PROJECTS: List[Dict[str, object]] = [
    {
        "project_name": "coverage-marketplace",
        "tags": ["catalog", "orders", "public_private_pages", "crud_api"],
        "phrase": (
            "Marketplace produits avec Clerk (vendeur/acheteur). "
            "Modèles Prisma Product et Order liés. "
            "Pages: /, /products/[id], /dashboard, /orders. "
            "Routes API: GET/POST /api/products, PUT /api/products/[id], GET/POST /api/orders."
        ),
    },
    {
        "project_name": "coverage-rbac-admin",
        "tags": ["rbac", "admin_guard", "org_scope", "audit_log"],
        "phrase": (
            "Dashboard multi-utilisateur avec rôles admin/member via Clerk. "
            "Modèles Prisma Workspace, Membership, Task, AuditLog. "
            "Pages protégées: /dashboard, /admin/users, /admin/audit. "
            "Routes API: GET /api/admin/users, PATCH /api/admin/users/[id]/role, GET /api/admin/audit."
        ),
    },
    {
        "project_name": "coverage-booking",
        "tags": ["booking", "datetime", "availability", "conflict_guard"],
        "phrase": (
            "Système de réservation de créneaux avec Clerk. "
            "Modèles Prisma Service, Slot, Booking. "
            "Empêcher les doubles réservations sur le même slot. "
            "Pages: /services, /services/[id], /bookings. "
            "Routes API: GET /api/slots, POST /api/bookings, DELETE /api/bookings/[id]."
        ),
    },
    {
        "project_name": "coverage-billing",
        "tags": ["billing", "invoice", "status_workflow", "json_field"],
        "phrase": (
            "Application de facturation avec Clerk. "
            "Modèles Prisma Client et Invoice avec items Json, amount Float, dueDate DateTime. "
            "Workflow statut invoice: draft -> sent -> paid. "
            "Pages: /clients, /invoices, /invoices/[id]. "
            "Routes API: GET/POST /api/clients, GET/POST /api/invoices, PUT /api/invoices/[id]/status."
        ),
    },
    {
        "project_name": "coverage-social",
        "tags": ["social_feed", "relations", "pagination", "filters"],
        "phrase": (
            "Mini réseau social avec Clerk. "
            "Modèles Prisma Post, Comment, Like, Follow. "
            "Feed paginé et filtrable par userId. "
            "Pages: /feed, /profile/[id], /post/[id]. "
            "Routes API: GET/POST /api/posts, POST /api/posts/[id]/like, GET/POST /api/posts/[id]/comments."
        ),
    },
    {
        "project_name": "coverage-habit-analytics",
        "tags": ["analytics", "streaks", "nested_routes", "datetime"],
        "phrase": (
            "Habit tracker avec Clerk. "
            "Modèles Prisma Habit et HabitLog. "
            "Pages: /dashboard avec streaks, /habits/[id]. "
            "Routes API imbriquées: GET/POST /api/habits et GET/POST /api/habits/[id]/log."
        ),
    },
    {
        "project_name": "coverage-support-tickets",
        "tags": ["ticketing", "status_transitions", "assignee", "protected_api"],
        "phrase": (
            "Support desk avec tickets et assignation agent. "
            "Modèles Prisma Ticket, TicketComment, AgentAssignment. "
            "Statuts ticket: open -> in_progress -> resolved -> closed. "
            "Pages: /tickets, /tickets/[id], /admin/agents. "
            "Routes API: GET/POST /api/tickets, PATCH /api/tickets/[id]/status, POST /api/tickets/[id]/assign."
        ),
    },
    {
        "project_name": "coverage-content-cms",
        "tags": ["cms", "slug", "seo_pages", "publish_toggle"],
        "phrase": (
            "CMS blog avec Clerk (auteur unique). "
            "Modèle Prisma Post avec slug unique et published boolean. "
            "Pages: /, /blog/[slug], /dashboard. "
            "Routes API: POST /api/posts, PUT /api/posts/[id] (toggle published), DELETE /api/posts/[id]."
        ),
    },
]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stack Coverage Check — batterie de briefs représentatifs Next.js + Clerk + Prisma"
    )
    parser.add_argument(
        "--sanity-mode",
        action="store_true",
        help="Mode rapide: arrêt du workflow après dev_test_activity.",
    )
    parser.add_argument(
        "--result-timeout-seconds",
        type=float,
        default=None,
        help="Timeout par workflow (secondes). Par défaut: attente complète.",
    )
    parser.add_argument(
        "--max-projects",
        type=int,
        default=0,
        help="Limiter le nombre de briefs (0 = tous).",
    )
    return parser.parse_args()


def _project_inputs(max_projects: int) -> List[Dict[str, str]]:
    dataset = STACK_COVERAGE_PROJECTS
    if max_projects and max_projects > 0:
        dataset = dataset[:max_projects]
    return [{"project_name": str(p["project_name"]), "phrase": str(p["phrase"])} for p in dataset]


async def main() -> None:
    args = _parse_args()
    from scripts.run_batch import run_batch

    projects = _project_inputs(args.max_projects)
    project_meta = {str(p["project_name"]): p for p in STACK_COVERAGE_PROJECTS}

    print(f"\n{'='*72}")
    print(" STACK COVERAGE CHECK")
    print(f" briefs        : {len(projects)}")
    print(f" sanity_mode   : {bool(args.sanity_mode)}")
    print(f"{'='*72}\n")

    result = await run_batch(
        projects=projects,
        result_timeout_seconds=args.result_timeout_seconds,
        sanity_mode=bool(args.sanity_mode),
    )

    runs = result.get("runs", []) or []
    tag_totals = defaultdict(int)
    tag_success = defaultdict(int)
    overall_success = 0

    print(f"{'='*72}")
    print(" RUN STATUS")
    print(f"{'='*72}")
    for run in runs:
        name = run.get("project_name", "")
        status = run.get("build_status", "UNKNOWN")
        ok = status in ("SUCCESS", "PARTIAL")
        if ok:
            overall_success += 1
        tags = list(project_meta.get(name, {}).get("tags", []))
        for t in tags:
            tag_totals[t] += 1
            if ok:
                tag_success[t] += 1
        print(f"- {name:28s} | {status:18s} | tags={tags}")

    print(f"\n{'='*72}")
    print(" COVERAGE SCORE")
    print(f"{'='*72}")
    print(f"- app success rate: {overall_success}/{len(runs)}")
    for tag in sorted(tag_totals.keys()):
        print(f"- {tag:22s}: {tag_success[tag]}/{tag_totals[tag]}")

    print(f"\n- metrics log: {result.get('metrics_log_path', 'N/A')}")
    print(f"{'='*72}\n")
    print(json.dumps(
        {
            "summary": {
                "apps_total": len(runs),
                "apps_success_like": overall_success,
                "tag_totals": dict(tag_totals),
                "tag_success": dict(tag_success),
            },
            "metrics_log_path": result.get("metrics_log_path", ""),
        },
        ensure_ascii=True,
    ))


if __name__ == "__main__":
    asyncio.run(main())
