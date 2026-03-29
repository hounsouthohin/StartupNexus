"""
brief_catalog.py — Source unique des briefs de test structurés.

Format : chaque brief est un dict JSON avec description, models[], pages[], routes[].
- models  : liste de strings Prisma DSL verbatim (N modèles, autant que nécessaire)
- pages   : liste de {"path": "/...", "auth": bool}
- routes  : liste de {"method": "GET|POST|...", "path": "/api/..."}

Ce format est la source de vérité transmise directement à l'architect.
Aucun parsing regex — l'architect lit les champs directement.
"""
from __future__ import annotations

from typing import Dict, List


# ─────────────────────────────────────────────────────────────────────────────
# BRIEFS STRUCTURÉS — 5 familles
# ─────────────────────────────────────────────────────────────────────────────

PHASE0_BRIEFS: List[Dict] = [
    # Famille 1 — CRUD simple (1 modèle, pas de relations)
    {
        "project_name": "task-manager",
        "family": "crud_simple",
        "tags": ["crud", "single_model", "auth_guard"],
        "brief": {
            "description": "App de gestion de tâches personnelles avec Clerk (utilisateur unique).",
            "models": [
                "Task { id String @id @default(uuid()), title String, done Boolean @default(false), dueDate DateTime?, userId String, createdAt DateTime @default(now()) }",
            ],
            "pages": [
                {"path": "/", "auth": True},
                {"path": "/new", "auth": True},
            ],
            "routes": [
                {"method": "PATCH", "path": "/api/tasks/[id]"},
                {"method": "DELETE", "path": "/api/tasks/[id]"},
            ],
        },
    },
    # Famille 2 — CRUD relationnel (2 modèles avec relation)
    {
        "project_name": "invoice-app",
        "family": "crud_relational",
        "tags": ["crud", "relations", "multi_model", "status_workflow"],
        "brief": {
            "description": "App de facturation avec clients et factures, Clerk auth.",
            "models": [
                "Client { id String @id @default(uuid()), name String, email String, userId String, createdAt DateTime @default(now()) }",
                "Invoice { id String @id @default(uuid()), amount Float, status String @default(\"draft\"), clientId String, userId String, createdAt DateTime @default(now()) }",
            ],
            "pages": [
                {"path": "/clients", "auth": True},
                {"path": "/invoices", "auth": True},
                {"path": "/invoices/new", "auth": True},
            ],
            "routes": [
                {"method": "POST", "path": "/api/invoices"},
                {"method": "PATCH", "path": "/api/invoices/[id]"},
            ],
        },
    },
    # Famille 3 — App workflow (2 modèles, states kanban)
    {
        "project_name": "kanban-board",
        "family": "workflow",
        "tags": ["kanban", "multi_model", "state_transitions", "relations"],
        "brief": {
            "description": "App Kanban avec boards et cartes, Clerk auth.",
            "models": [
                "Board { id String @id @default(uuid()), name String, userId String, createdAt DateTime @default(now()) }",
                "Card { id String @id @default(uuid()), title String, column String @default(\"todo\"), boardId String, createdAt DateTime @default(now()) }",
            ],
            "pages": [
                {"path": "/", "auth": True},
                {"path": "/boards/[id]", "auth": True},
            ],
            "routes": [
                {"method": "POST", "path": "/api/boards/[id]/cards"},
                {"method": "PATCH", "path": "/api/cards/[id]"},
            ],
        },
    },
    # Famille 4 — App contenu (pages publiques + privées)
    {
        "project_name": "personal-blog",
        "family": "content",
        "tags": ["cms", "slug", "public_private_pages", "publish_toggle"],
        "brief": {
            "description": "Blog CMS avec Clerk (auteur unique), pages publiques et dashboard.",
            "models": [
                "Post { id String @id @default(cuid()), title String, content String, slug String @unique, published Boolean @default(false), authorId String, createdAt DateTime @default(now()) }",
            ],
            "pages": [
                {"path": "/", "auth": False},
                {"path": "/blog/[slug]", "auth": False},
                {"path": "/dashboard", "auth": True},
            ],
            "routes": [
                {"method": "PUT", "path": "/api/posts/[id]"},
            ],
        },
    },
    # Famille 5 — App dashboard/analytics (agrégations)
    {
        "project_name": "expense-tracker",
        "family": "dashboard",
        "tags": ["analytics", "aggregation", "single_model", "dashboard"],
        "brief": {
            "description": "App de suivi de dépenses avec dashboard récapitulatif par catégorie, Clerk auth.",
            "models": [
                "Expense { id String @id @default(uuid()), amount Float, category String, description String, date DateTime, userId String, createdAt DateTime @default(now()) }",
            ],
            "pages": [
                {"path": "/", "auth": True},
                {"path": "/expenses", "auth": True},
                {"path": "/expenses/new", "auth": True},
            ],
            "routes": [
                {"method": "POST", "path": "/api/expenses"},
                {"method": "DELETE", "path": "/api/expenses/[id]"},
            ],
        },
    },
]


def get_batch_projects(batch_size: int = 5) -> List[Dict]:
    """
    Retourne une liste de projets pour run_batch.py.
    Format : [{"project_name": ..., "brief": {...}}]
    Si batch_size > 5, recycle les briefs en suffixant les noms.
    """
    base = [{"project_name": b["project_name"], "brief": b["brief"]} for b in PHASE0_BRIEFS]
    if batch_size <= len(base):
        return base[:batch_size]

    out: List[Dict] = []
    for i in range(batch_size):
        entry = dict(base[i % len(base)])
        if i >= len(base):
            suffix = f"-{i // len(base) + 1:02d}"
            entry["project_name"] = entry["project_name"] + suffix
        out.append(entry)
    return out


def get_coverage_projects(max_projects: int = 0) -> List[Dict]:
    """
    Retourne les briefs complets (avec family/tags) pour run_stack_coverage_check.py.
    max_projects=0 → tous les briefs.
    """
    if max_projects > 0:
        return PHASE0_BRIEFS[:max_projects]
    return list(PHASE0_BRIEFS)
