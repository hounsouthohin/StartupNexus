"""
brief_catalog.py — Source unique des briefs de test Phase 0.

Règle de format : chaque brief est ENTIÈREMENT EXPLICITE.
- Modèles Prisma avec champs et types verbatim
- Pages avec paths exacts + protection auth
- Routes API avec METHOD /path + auth requise ou non

Source partagée par run_batch.py et run_stack_coverage_check.py.
Ne jamais dupliquer les briefs dans les scripts individuels.
"""
from __future__ import annotations

from typing import Dict, List


# ─────────────────────────────────────────────────────────────────────────────
# BRIEFS PHASE 0 — 5 familles, 1 brief par famille
# ─────────────────────────────────────────────────────────────────────────────

PHASE0_BRIEFS: List[Dict[str, object]] = [
    # Famille 1 — CRUD simple (1 modèle, pas de relations)
    {
        "project_name": "task-manager",
        "family": "crud_simple",
        "tags": ["crud", "single_model", "auth_guard"],
        "phrase": (
            "App de gestion de tâches personnelles avec Clerk (utilisateur unique).\n"
            "- Modele Prisma : Task { id String @id @default(uuid()), title String, done Boolean @default(false), dueDate DateTime?, userId String, createdAt DateTime @default(now()) }\n"
            "- Pages : / (liste des tâches, auth requise), /new (formulaire création, auth requise)\n"
            "- API Route : PATCH /api/tasks/[id] (toggle done, auth requise) | DELETE /api/tasks/[id] (suppression, auth requise)\n"
            "- Stack: nextjs-clerk-prisma"
        ),
    },
    # Famille 2 — CRUD relationnel (2+ modèles avec relation)
    {
        "project_name": "invoice-app",
        "family": "crud_relational",
        "tags": ["crud", "relations", "multi_model", "status_workflow"],
        "phrase": (
            "App de facturation avec clients et factures, Clerk auth.\n"
            "- Modele Prisma : Client { id String @id @default(uuid()), name String, email String, userId String, createdAt DateTime @default(now()) } | Invoice { id String @id @default(uuid()), amount Float, status String @default(\"draft\"), clientId String, userId String, createdAt DateTime @default(now()) }\n"
            "- Pages : /clients (liste clients, auth requise), /invoices (liste factures, auth requise), /invoices/new (création facture, auth requise)\n"
            "- API Route : POST /api/invoices (créer facture, auth requise) | PATCH /api/invoices/[id] (changer status draft/sent/paid, auth requise)\n"
            "- Stack: nextjs-clerk-prisma"
        ),
    },
    # Famille 3 — App workflow (kanban/states)
    {
        "project_name": "kanban-board",
        "family": "workflow",
        "tags": ["kanban", "multi_model", "state_transitions", "relations"],
        "phrase": (
            "App Kanban avec boards et cartes, Clerk auth.\n"
            "- Modele Prisma : Board { id String @id @default(uuid()), name String, userId String, createdAt DateTime @default(now()) } | Card { id String @id @default(uuid()), title String, column String @default(\"todo\"), boardId String, createdAt DateTime @default(now()) }\n"
            "- Pages : / (liste des boards, auth requise), /boards/[id] (vue kanban avec colonnes todo/in_progress/done, auth requise)\n"
            "- API Route : POST /api/boards/[id]/cards (créer carte, auth requise) | PATCH /api/cards/[id] (déplacer vers colonne, auth requise)\n"
            "- Stack: nextjs-clerk-prisma"
        ),
    },
    # Famille 4 — App contenu (blog/CMS, pages publiques + privées)
    {
        "project_name": "personal-blog",
        "family": "content",
        "tags": ["cms", "slug", "public_private_pages", "publish_toggle"],
        "phrase": (
            "Blog CMS avec Clerk (auteur unique).\n"
            "- Modele Prisma : Post { id String @id @default(cuid()), title String, content String, slug String @unique, published Boolean @default(false), authorId String, createdAt DateTime @default(now()) }\n"
            "- Pages : / (liste articles publics, publique), /blog/[slug] (article, publique), /dashboard (gestion articles, auth requise)\n"
            "- API Route : PUT /api/posts/[id] (toggle published, auth requise)\n"
            "- Stack: nextjs-clerk-prisma"
        ),
    },
    # Famille 5 — App dashboard/analytics
    {
        "project_name": "expense-tracker",
        "family": "dashboard",
        "tags": ["analytics", "aggregation", "single_model", "dashboard"],
        "phrase": (
            "App de suivi de dépenses avec dashboard récapitulatif, Clerk auth.\n"
            "- Modele Prisma : Expense { id String @id @default(uuid()), amount Float, category String, description String, date DateTime, userId String, createdAt DateTime @default(now()) }\n"
            "- Pages : / (dashboard avec total par catégorie, auth requise), /expenses (liste complète, auth requise), /expenses/new (formulaire ajout, auth requise)\n"
            "- API Route : POST /api/expenses (créer dépense, auth requise) | DELETE /api/expenses/[id] (supprimer, auth requise)\n"
            "- Stack: nextjs-clerk-prisma"
        ),
    },
]


def get_batch_projects(batch_size: int = 5) -> List[Dict[str, str]]:
    """
    Retourne une liste de projets pour run_batch.py.
    Format: [{"project_name": ..., "phrase": ...}]
    Si batch_size > 5, recycle les briefs en suffixant les noms.
    """
    base = [{"project_name": b["project_name"], "phrase": b["phrase"]} for b in PHASE0_BRIEFS]
    if batch_size <= len(base):
        return base[:batch_size]

    out: List[Dict[str, str]] = []
    for i in range(batch_size):
        entry = dict(base[i % len(base)])
        if i >= len(base):
            suffix = f"-{i // len(base) + 1:02d}"
            entry["project_name"] = entry["project_name"] + suffix
        out.append(entry)
    return out


def get_coverage_projects(max_projects: int = 0) -> List[Dict[str, object]]:
    """
    Retourne les briefs complets (avec family/tags) pour run_stack_coverage_check.py.
    max_projects=0 → tous les briefs.
    """
    if max_projects > 0:
        return PHASE0_BRIEFS[:max_projects]
    return list(PHASE0_BRIEFS)
