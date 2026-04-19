"""
brief_catalog.py — Source unique des briefs de test structurés.

Format enrichi (v2) : chaque brief est un dict avec :
- description   : description humaine de l'app
- architecture  : hints d'architecture (SaaS, multi-tenant, public/private, etc.)
- models        : liste de strings Prisma DSL verbatim
- pages         : liste de {"path": "/...", "auth": bool}
- routes        : liste de {"method": "GET|POST|...", "path": "/api/..."}
- user_flows    : liste de strings décrivant les flux utilisateur principaux

Le format enrichi permet à l'architect de générer des specs plus précises
et au dev agent de produire des apps complètes (CRUD complet, pages détail, etc.).
"""
from __future__ import annotations

from typing import Dict, List


# ─────────────────────────────────────────────────────────────────────────────
# BRIEFS STRUCTURÉS v2 — 5 familles, CRUD complet, pages détail incluses
# ─────────────────────────────────────────────────────────────────────────────

PHASE0_BRIEFS: List[Dict] = [
    # Famille 1 — CRUD simple (1 modèle, pas de relations)
    {
        "project_name": "task-manager",
        "family": "crud_simple",
        "tags": ["crud", "single_model", "auth_guard"],
        "brief": {
            "description": "App de gestion de tâches personnelles avec Clerk (utilisateur unique).",
            "architecture": "SaaS single-tenant — chaque utilisateur voit uniquement ses propres tâches. Toutes les pages sont protégées par Clerk. CRUD complet avec page liste + page détail + formulaire création.",
            "models": [
                "Task { id String @id @default(uuid()), title String, done Boolean @default(false), dueDate DateTime?, userId String, createdAt DateTime @default(now()), @@index([userId]) }",
            ],
            "pages": [
                {"path": "/tasks", "auth": True},
                {"path": "/tasks/[id]", "auth": True},
                {"path": "/tasks/new", "auth": True},
            ],
            "routes": [
                {"method": "GET",    "path": "/api/tasks"},
                {"method": "POST",   "path": "/api/tasks"},
                {"method": "GET",    "path": "/api/tasks/[id]"},
                {"method": "PATCH",  "path": "/api/tasks/[id]"},
                {"method": "DELETE", "path": "/api/tasks/[id]"},
            ],
            "user_flows": [
                "L'utilisateur se connecte via Clerk et accède à /tasks",
                "L'utilisateur crée une tâche via /tasks/new → POST /api/tasks → redirect /tasks",
                "L'utilisateur marque une tâche comme terminée → PATCH /api/tasks/[id]",
                "L'utilisateur supprime une tâche → DELETE /api/tasks/[id]",
                "L'utilisateur consulte le détail d'une tâche → /tasks/[id]",
            ],
        },
    },
    # Famille 2 — CRUD relationnel (2 modèles avec relation FK)
    {
        "project_name": "invoice-app",
        "family": "crud_relational",
        "tags": ["crud", "relations", "multi_model", "status_workflow"],
        "brief": {
            "description": "App de facturation avec clients et factures, Clerk auth.",
            "architecture": "SaaS single-tenant — un utilisateur gère ses clients et factures. Invoice est liée à Client via clientId (FK). Status workflow : draft → sent → paid. CRUD complet sur les deux modèles.",
            "models": [
                "Client { id String @id @default(uuid()), name String, email String @unique, userId String, createdAt DateTime @default(now()), @@index([userId]) }",
                "Invoice { id String @id @default(uuid()), amount Float, status String @default(\"draft\"), clientId String, userId String, createdAt DateTime @default(now()), @@index([userId]), @@index([clientId]) }",
            ],
            "pages": [
                {"path": "/clients", "auth": True},
                {"path": "/clients/[id]", "auth": True},
                {"path": "/clients/new", "auth": True},
                {"path": "/invoices", "auth": True},
                {"path": "/invoices/[id]", "auth": True},
                {"path": "/invoices/new", "auth": True},
            ],
            "routes": [
                {"method": "GET",    "path": "/api/clients"},
                {"method": "POST",   "path": "/api/clients"},
                {"method": "GET",    "path": "/api/clients/[id]"},
                {"method": "PATCH",  "path": "/api/clients/[id]"},
                {"method": "DELETE", "path": "/api/clients/[id]"},
                {"method": "GET",    "path": "/api/invoices"},
                {"method": "POST",   "path": "/api/invoices"},
                {"method": "GET",    "path": "/api/invoices/[id]"},
                {"method": "PATCH",  "path": "/api/invoices/[id]"},
                {"method": "DELETE", "path": "/api/invoices/[id]"},
            ],
            "user_flows": [
                "L'utilisateur crée un client via /clients/new → POST /api/clients → redirect /clients",
                "L'utilisateur crée une facture via /invoices/new (sélectionne un client) → POST /api/invoices → redirect /invoices",
                "L'utilisateur passe une facture en 'sent' → PATCH /api/invoices/[id] { status: 'sent' }",
                "L'utilisateur consulte le détail d'une facture → /invoices/[id]",
                "L'utilisateur supprime un client → DELETE /api/clients/[id]",
            ],
        },
    },
    # Famille 3 — App workflow (2 modèles, états kanban)
    {
        "project_name": "kanban-board",
        "family": "workflow",
        "tags": ["kanban", "multi_model", "state_transitions", "relations"],
        "brief": {
            "description": "App Kanban avec boards et cartes, Clerk auth.",
            "architecture": "SaaS single-tenant — chaque utilisateur a ses propres boards. Card est liée à Board via boardId (FK). Colonne workflow : todo → in-progress → done. CRUD complet board + cartes.",
            "models": [
                "Board { id String @id @default(uuid()), name String, userId String, createdAt DateTime @default(now()), @@index([userId]) }",
                "Card { id String @id @default(uuid()), title String, column String @default(\"todo\"), boardId String, createdAt DateTime @default(now()), @@index([boardId]) }",
            ],
            "pages": [
                {"path": "/boards", "auth": True},
                {"path": "/boards/[id]", "auth": True},
                {"path": "/boards/new", "auth": True},
            ],
            "routes": [
                {"method": "GET",    "path": "/api/boards"},
                {"method": "POST",   "path": "/api/boards"},
                {"method": "GET",    "path": "/api/boards/[id]"},
                {"method": "PATCH",  "path": "/api/boards/[id]"},
                {"method": "DELETE", "path": "/api/boards/[id]"},
                {"method": "POST",   "path": "/api/boards/[id]/cards"},
                {"method": "PATCH",  "path": "/api/cards/[id]"},
                {"method": "DELETE", "path": "/api/cards/[id]"},
            ],
            "user_flows": [
                "L'utilisateur crée un board → POST /api/boards → redirect /boards",
                "L'utilisateur ouvre un board → /boards/[id] (affiche toutes les cartes groupées par colonne)",
                "L'utilisateur crée une carte dans un board → POST /api/boards/[id]/cards",
                "L'utilisateur déplace une carte (change la colonne) → PATCH /api/cards/[id] { column: 'in-progress' }",
                "L'utilisateur supprime une carte → DELETE /api/cards/[id]",
            ],
        },
    },
    # Famille 4 — App contenu (pages publiques + privées, slug)
    {
        "project_name": "personal-blog",
        "family": "content",
        "tags": ["cms", "slug", "public_private_pages", "publish_toggle"],
        "brief": {
            "description": "Blog CMS avec Clerk (auteur unique), pages publiques et dashboard.",
            "architecture": "CMS hybride — pages publiques (/ et /blog/[slug]) accessibles sans auth ; dashboard auteur protégé par Clerk. Un seul auteur. Workflow de publication : draft → published via toggle.",
            "models": [
                "Post { id String @id @default(cuid()), title String, content String, slug String @unique, published Boolean @default(false), authorId String, createdAt DateTime @default(now()), @@index([authorId]), @@index([slug]) }",
            ],
            "pages": [
                {"path": "/", "auth": False},
                {"path": "/blog/[slug]", "auth": False},
                {"path": "/dashboard", "auth": True},
                {"path": "/dashboard/posts/new", "auth": True},
                {"path": "/dashboard/posts/[id]/edit", "auth": True},
            ],
            "routes": [
                {"method": "GET",    "path": "/api/posts"},
                {"method": "POST",   "path": "/api/posts"},
                {"method": "GET",    "path": "/api/posts/[id]"},
                {"method": "PUT",    "path": "/api/posts/[id]"},
                {"method": "DELETE", "path": "/api/posts/[id]"},
            ],
            "user_flows": [
                "Le visiteur consulte la liste des articles publiés sur /",
                "Le visiteur lit un article via /blog/[slug]",
                "L'auteur se connecte via Clerk et accède à /dashboard",
                "L'auteur crée un article → /dashboard/posts/new → POST /api/posts → redirect /dashboard",
                "L'auteur publie un article → PUT /api/posts/[id] { published: true }",
                "L'auteur supprime un article → DELETE /api/posts/[id]",
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
            "architecture": "SaaS single-tenant — dashboard avec total par catégorie calculé côté serveur. Liste paginée des dépenses. CRUD complet. Formulaire de création avec catégorie et montant.",
            "models": [
                "Expense { id String @id @default(uuid()), amount Float, category String, description String, date DateTime, userId String, createdAt DateTime @default(now()), @@index([userId]) }",
            ],
            "pages": [
                {"path": "/dashboard", "auth": True},
                {"path": "/expenses", "auth": True},
                {"path": "/expenses/[id]", "auth": True},
                {"path": "/expenses/new", "auth": True},
            ],
            "routes": [
                {"method": "GET",    "path": "/api/expenses"},
                {"method": "POST",   "path": "/api/expenses"},
                {"method": "GET",    "path": "/api/expenses/[id]"},
                {"method": "PATCH",  "path": "/api/expenses/[id]"},
                {"method": "DELETE", "path": "/api/expenses/[id]"},
            ],
            "user_flows": [
                "L'utilisateur se connecte et accède au /dashboard (totaux par catégorie)",
                "L'utilisateur consulte la liste de ses dépenses → /expenses",
                "L'utilisateur ajoute une dépense → /expenses/new → POST /api/expenses → redirect /expenses",
                "L'utilisateur modifie une dépense → PATCH /api/expenses/[id]",
                "L'utilisateur supprime une dépense → DELETE /api/expenses/[id]",
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
