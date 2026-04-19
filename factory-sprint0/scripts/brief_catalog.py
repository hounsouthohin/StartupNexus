"""
brief_catalog.py — Source unique des briefs de test structurés.

Format v3 — chaque brief contient :
- description   : description humaine de l'app (contexte métier)
- architecture  : intent SaaS, multi-tenant, public/private, workflow
- models        : Prisma DSL verbatim
- pages         : [{"path": "/...", "auth": bool}]
- pages_detail  : {"path": "QUOI afficher, quels champs, quelles actions, état vide"}
- routes        : [{"method": "...", "path": "/api/..."}]
- user_flows    : flux utilisateur principaux

pages_detail est le champ le plus critique : il dit au spec_writer exactement
quoi afficher sur chaque page, ce que le LLM ne peut pas deviner seul.
"""
from __future__ import annotations

from typing import Dict, List


PHASE0_BRIEFS: List[Dict] = [

    # ──────────────────────────────────────────────────────────────────
    # Famille 1 — CRUD simple (1 modèle)
    # ──────────────────────────────────────────────────────────────────
    {
        "project_name": "task-manager",
        "family": "crud_simple",
        "tags": ["crud", "single_model", "auth_guard"],
        "brief": {
            "description": "Application de gestion de tâches personnelles. Chaque utilisateur gère sa propre liste de tâches avec titre, date limite optionnelle et statut done/todo.",
            "architecture": "SaaS single-tenant — toutes les pages sont protégées par Clerk. Un utilisateur ne voit que ses propres tâches (filtrées par userId). CRUD complet : liste, détail, création, mise à jour, suppression.",
            "models": [
                "Task { id String @id @default(uuid()), title String, done Boolean @default(false), dueDate DateTime?, userId String, createdAt DateTime @default(now()), @@index([userId]) }",
            ],
            "pages": [
                {"path": "/tasks", "auth": True},
                {"path": "/tasks/[id]", "auth": True},
                {"path": "/tasks/new", "auth": True},
            ],
            "pages_detail": {
                "/tasks": (
                    "Liste de toutes les tâches de l'utilisateur connecté. "
                    "Chaque ligne affiche : titre de la tâche, date limite formatée (ex: '15 mai 2026') ou 'Sans échéance', "
                    "badge coloré vert 'Terminée' ou gris 'En cours'. "
                    "Lien cliquable sur chaque ligne vers /tasks/[id]. "
                    "Bouton 'Supprimer' par ligne (DELETE /api/tasks/[id]). "
                    "Bouton 'Nouvelle tâche' en haut à droite → /tasks/new. "
                    "Si liste vide : message 'Aucune tâche. Commencez par en créer une !' avec lien vers /tasks/new."
                ),
                "/tasks/[id]": (
                    "Détail d'une tâche. Affiche : titre en H1, statut (badge vert 'Terminée' / gris 'En cours'), "
                    "date limite ou 'Sans échéance', date de création (format lisible). "
                    "Bouton 'Marquer comme terminée' si done=false (PATCH /api/tasks/[id] { done: true }). "
                    "Bouton 'Rouvrir' si done=true (PATCH /api/tasks/[id] { done: false }). "
                    "Bouton retour '← Mes tâches' vers /tasks. "
                    "Si tâche introuvable ou n'appartient pas à l'utilisateur : notFound()."
                ),
                "/tasks/new": (
                    "Formulaire de création de tâche (Client Component). "
                    "Champs : titre (input text, required, placeholder 'Titre de la tâche'), "
                    "date limite (input date, optionnel). "
                    "Bouton 'Créer la tâche' (submit). "
                    "Submit → POST /api/tasks avec { title, dueDate } → redirect vers /tasks. "
                    "Afficher un message d'erreur inline si le titre est vide."
                ),
            },
            "routes": [
                {"method": "GET",    "path": "/api/tasks"},
                {"method": "POST",   "path": "/api/tasks"},
                {"method": "GET",    "path": "/api/tasks/[id]"},
                {"method": "PATCH",  "path": "/api/tasks/[id]"},
                {"method": "DELETE", "path": "/api/tasks/[id]"},
            ],
            "user_flows": [
                "L'utilisateur se connecte via Clerk et accède à /tasks (liste de ses tâches)",
                "L'utilisateur crée une tâche : /tasks/new → POST /api/tasks → redirect /tasks",
                "L'utilisateur consulte le détail d'une tâche : clic sur la ligne → /tasks/[id]",
                "L'utilisateur marque une tâche terminée : bouton sur /tasks/[id] → PATCH /api/tasks/[id]",
                "L'utilisateur supprime une tâche : bouton Supprimer sur /tasks → DELETE /api/tasks/[id]",
            ],
        },
    },

    # ──────────────────────────────────────────────────────────────────
    # Famille 2 — CRUD relationnel (Invoice → Client)
    # ──────────────────────────────────────────────────────────────────
    {
        "project_name": "invoice-app",
        "family": "crud_relational",
        "tags": ["crud", "relations", "multi_model", "status_workflow"],
        "brief": {
            "description": "Application de facturation. L'utilisateur gère ses clients et crée des factures associées à un client. Une facture a un montant, un statut (draft/sent/paid) et est liée à un client.",
            "architecture": "SaaS single-tenant. Invoice est liée à Client via clientId (relation Prisma @relation). Status workflow : draft → sent → paid. CRUD complet sur clients et factures. Toutes les pages protégées par Clerk.",
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
            "pages_detail": {
                "/clients": (
                    "Liste de tous les clients de l'utilisateur. "
                    "Chaque ligne affiche : nom du client, email, nombre de factures (si disponible), date d'ajout. "
                    "Lien cliquable vers /clients/[id]. "
                    "Bouton 'Supprimer' par ligne (DELETE /api/clients/[id]). "
                    "Bouton 'Nouveau client' en haut à droite → /clients/new. "
                    "Si liste vide : 'Aucun client. Ajoutez votre premier client !'."
                ),
                "/clients/[id]": (
                    "Détail d'un client : nom en H1, email, date de création. "
                    "Section 'Factures de ce client' : liste des factures avec montant, statut badge (draft=gris, sent=bleu, paid=vert), date. "
                    "Bouton 'Nouvelle facture pour ce client' → /invoices/new?clientId=[id]. "
                    "Bouton retour '← Clients'. notFound() si client introuvable."
                ),
                "/clients/new": (
                    "Formulaire Client Component. Champs : nom (input text, required), email (input email, required). "
                    "Submit → POST /api/clients → redirect /clients. "
                    "Erreur inline si champ manquant."
                ),
                "/invoices": (
                    "Liste de toutes les factures de l'utilisateur. "
                    "Chaque ligne : numéro/id tronqué, nom du client (via relation), montant formaté en euros, "
                    "badge statut (draft=gris, sent=bleu, paid=vert), date de création. "
                    "Lien vers /invoices/[id]. "
                    "Bouton 'Nouvelle facture' → /invoices/new. "
                    "Si vide : 'Aucune facture. Créez votre première facture !'."
                ),
                "/invoices/[id]": (
                    "Détail d'une facture : montant en H1 formaté, statut badge, nom du client (lien → /clients/[id]), date. "
                    "Boutons de changement de statut : 'Marquer comme envoyée' (PATCH status:sent) si draft, "
                    "'Marquer comme payée' (PATCH status:paid) si sent. "
                    "Bouton 'Supprimer' (DELETE) si status=draft. "
                    "Bouton retour '← Factures'. notFound() si introuvable."
                ),
                "/invoices/new": (
                    "Formulaire Client Component. Champs : sélecteur client (select parmi les clients de l'utilisateur, required), "
                    "montant (input number, required, min=0.01). "
                    "Submit → POST /api/invoices { clientId, amount } → redirect /invoices. "
                    "Charger la liste des clients via GET /api/clients au montage du composant."
                ),
            },
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
                "L'utilisateur crée un client : /clients/new → POST /api/clients → redirect /clients",
                "L'utilisateur crée une facture : /invoices/new (sélectionne un client, saisit le montant) → POST /api/invoices → redirect /invoices",
                "L'utilisateur passe une facture en 'sent' : bouton sur /invoices/[id] → PATCH /api/invoices/[id] { status: 'sent' }",
                "L'utilisateur passe une facture en 'paid' : bouton sur /invoices/[id] → PATCH /api/invoices/[id] { status: 'paid' }",
                "L'utilisateur supprime un client : bouton sur /clients → DELETE /api/clients/[id]",
            ],
        },
    },

    # ──────────────────────────────────────────────────────────────────
    # Famille 3 — Workflow Kanban (Board → Card)
    # ──────────────────────────────────────────────────────────────────
    {
        "project_name": "kanban-board",
        "family": "workflow",
        "tags": ["kanban", "multi_model", "state_transitions", "relations"],
        "brief": {
            "description": "Application Kanban. L'utilisateur crée des boards (tableaux) et y ajoute des cartes. Chaque carte appartient à un board et a une colonne (todo / in-progress / done).",
            "architecture": "SaaS single-tenant. Card est liée à Board via boardId (@relation). Colonne workflow : todo → in-progress → done. Un Board peut avoir plusieurs Cards. Toutes les pages protégées par Clerk.",
            "models": [
                "Board { id String @id @default(uuid()), name String, userId String, createdAt DateTime @default(now()), @@index([userId]) }",
                "Card { id String @id @default(uuid()), title String, column String @default(\"todo\"), boardId String, createdAt DateTime @default(now()), @@index([boardId]) }",
            ],
            "pages": [
                {"path": "/boards", "auth": True},
                {"path": "/boards/[id]", "auth": True},
                {"path": "/boards/new", "auth": True},
            ],
            "pages_detail": {
                "/boards": (
                    "Liste des boards de l'utilisateur. "
                    "Chaque card affiche : nom du board, nombre de cartes (si disponible), date de création. "
                    "Clic → /boards/[id]. "
                    "Bouton 'Supprimer' par board (DELETE /api/boards/[id]). "
                    "Bouton 'Nouveau board' → /boards/new. "
                    "Si vide : 'Aucun board. Créez votre premier tableau Kanban !'."
                ),
                "/boards/[id]": (
                    "Vue Kanban du board. Titre du board en H1. "
                    "3 colonnes côte à côte : 'À faire' (todo), 'En cours' (in-progress), 'Terminé' (done). "
                    "Chaque colonne affiche ses cartes (filtrées par column). "
                    "Chaque carte affiche son titre et des boutons pour changer de colonne "
                    "(ex: 'Démarrer' passe todo→in-progress, 'Terminer' passe in-progress→done, 'Supprimer'). "
                    "Formulaire inline en bas de chaque colonne : input 'Titre de la carte' + bouton 'Ajouter' "
                    "(POST /api/boards/[id]/cards { title, column }). "
                    "Bouton retour '← Mes boards'. notFound() si board introuvable ou n'appartient pas à l'utilisateur."
                ),
                "/boards/new": (
                    "Formulaire Client Component. Champ : nom du board (input text, required). "
                    "Submit → POST /api/boards { name } → redirect /boards."
                ),
            },
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
                "L'utilisateur crée un board : /boards/new → POST /api/boards → redirect /boards",
                "L'utilisateur ouvre un board → /boards/[id] : voit ses cartes en 3 colonnes",
                "L'utilisateur ajoute une carte dans une colonne : formulaire inline → POST /api/boards/[id]/cards",
                "L'utilisateur déplace une carte (change colonne) : bouton → PATCH /api/cards/[id] { column: 'in-progress' }",
                "L'utilisateur supprime une carte : bouton Supprimer → DELETE /api/cards/[id]",
            ],
        },
    },

    # ──────────────────────────────────────────────────────────────────
    # Famille 4 — CMS Blog (pages publiques + dashboard auteur)
    # ──────────────────────────────────────────────────────────────────
    {
        "project_name": "personal-blog",
        "family": "content",
        "tags": ["cms", "slug", "public_private_pages", "publish_toggle"],
        "brief": {
            "description": "Blog CMS avec un auteur unique. Les visiteurs lisent les articles publiés sans se connecter. L'auteur se connecte via Clerk pour créer, modifier et publier des articles.",
            "architecture": "CMS hybride — / et /blog/[slug] sont publiques (pas d'auth). /dashboard et sous-pages sont protégées par Clerk. Un seul auteur. Workflow : créer en draft → publier via toggle → visible sur /.",
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
            "pages_detail": {
                "/": (
                    "Page d'accueil publique. Affiche la liste des articles publiés (published=true), "
                    "ordonnés par date décroissante. Chaque article : titre (lien → /blog/[slug]), "
                    "extrait du contenu (150 premiers caractères + '...'), date de publication formatée. "
                    "Si aucun article publié : 'Aucun article pour le moment.'. "
                    "Lien 'Se connecter' en haut à droite si non authentifié."
                ),
                "/blog/[slug]": (
                    "Page article publique. Cherche le Post par slug (findUnique where slug). "
                    "Affiche : titre en H1, date de publication, contenu complet. "
                    "Bouton retour '← Tous les articles' vers /. "
                    "notFound() si slug inexistant ou article non publié."
                ),
                "/dashboard": (
                    "Dashboard auteur (protégé Clerk). Liste TOUS les articles (publiés et drafts). "
                    "Chaque ligne : titre, badge 'Publié' (vert) ou 'Brouillon' (gris), date de création. "
                    "Bouton 'Publier' / 'Dépublier' par ligne (PUT /api/posts/[id] { published: true/false }). "
                    "Bouton 'Modifier' → /dashboard/posts/[id]/edit. "
                    "Bouton 'Supprimer' (DELETE /api/posts/[id]). "
                    "Bouton 'Nouvel article' → /dashboard/posts/new."
                ),
                "/dashboard/posts/new": (
                    "Formulaire Client Component. Champs : titre (input text, required), "
                    "slug (input text, required, généré automatiquement depuis le titre en kebab-case), "
                    "contenu (textarea, required). "
                    "Submit → POST /api/posts { title, slug, content } → redirect /dashboard. "
                    "Article créé en draft par défaut."
                ),
                "/dashboard/posts/[id]/edit": (
                    "Formulaire édition Client Component. Pré-rempli avec les valeurs actuelles. "
                    "Champs : titre, slug, contenu. "
                    "Submit → PUT /api/posts/[id] → redirect /dashboard. "
                    "notFound() si article introuvable."
                ),
            },
            "routes": [
                {"method": "GET",    "path": "/api/posts"},
                {"method": "POST",   "path": "/api/posts"},
                {"method": "GET",    "path": "/api/posts/[id]"},
                {"method": "PUT",    "path": "/api/posts/[id]"},
                {"method": "DELETE", "path": "/api/posts/[id]"},
            ],
            "user_flows": [
                "Le visiteur consulte les articles publiés sur / (sans connexion)",
                "Le visiteur lit un article via /blog/[slug] (sans connexion)",
                "L'auteur se connecte via Clerk → accède à /dashboard",
                "L'auteur crée un article : /dashboard/posts/new → POST /api/posts → redirect /dashboard",
                "L'auteur publie un article : bouton sur /dashboard → PUT /api/posts/[id] { published: true }",
                "L'auteur modifie un article : /dashboard/posts/[id]/edit → PUT /api/posts/[id] → redirect /dashboard",
                "L'auteur supprime un article : bouton sur /dashboard → DELETE /api/posts/[id]",
            ],
        },
    },

    # ──────────────────────────────────────────────────────────────────
    # Famille 5 — Dashboard analytics (agrégations côté serveur)
    # ──────────────────────────────────────────────────────────────────
    {
        "project_name": "expense-tracker",
        "family": "dashboard",
        "tags": ["analytics", "aggregation", "single_model", "dashboard"],
        "brief": {
            "description": "Application de suivi de dépenses personnelles. L'utilisateur enregistre ses dépenses avec montant, catégorie et description. Un dashboard affiche les totaux par catégorie.",
            "architecture": "SaaS single-tenant. Dashboard avec agrégations calculées côté serveur (total par catégorie via groupBy Prisma ou reduce JS). CRUD complet sur les dépenses. Toutes les pages protégées par Clerk.",
            "models": [
                "Expense { id String @id @default(uuid()), amount Float, category String, description String, date DateTime, userId String, createdAt DateTime @default(now()), @@index([userId]) }",
            ],
            "pages": [
                {"path": "/dashboard", "auth": True},
                {"path": "/expenses", "auth": True},
                {"path": "/expenses/[id]", "auth": True},
                {"path": "/expenses/new", "auth": True},
            ],
            "pages_detail": {
                "/dashboard": (
                    "Dashboard récapitulatif. "
                    "Calcule les totaux par catégorie depuis toutes les dépenses de l'utilisateur. "
                    "Affiche une card par catégorie avec : nom de la catégorie, total formaté en euros, nombre de dépenses. "
                    "Total global de toutes les dépenses en grand en haut. "
                    "Lien 'Voir toutes les dépenses' → /expenses. "
                    "Bouton 'Ajouter une dépense' → /expenses/new. "
                    "Si aucune dépense : 'Aucune dépense enregistrée. Commencez à tracker vos dépenses !'."
                ),
                "/expenses": (
                    "Liste de toutes les dépenses, ordonnées par date décroissante. "
                    "Chaque ligne : description, catégorie (badge coloré), montant en euros, date formatée. "
                    "Lien vers /expenses/[id]. "
                    "Bouton 'Supprimer' par ligne (DELETE /api/expenses/[id]). "
                    "Bouton 'Ajouter une dépense' → /expenses/new. "
                    "Si vide : 'Aucune dépense.'."
                ),
                "/expenses/[id]": (
                    "Détail d'une dépense : description en H1, montant en grand, catégorie badge, date, date de création. "
                    "Bouton retour '← Mes dépenses' vers /expenses. "
                    "Bouton 'Supprimer' (DELETE /api/expenses/[id] → redirect /expenses). "
                    "notFound() si introuvable ou n'appartient pas à l'utilisateur."
                ),
                "/expenses/new": (
                    "Formulaire Client Component. Champs : "
                    "description (input text, required), "
                    "montant (input number, required, min=0.01, step=0.01), "
                    "catégorie (select avec options : Alimentation, Transport, Logement, Loisirs, Santé, Autre), "
                    "date (input date, required, défaut=aujourd'hui). "
                    "Submit → POST /api/expenses → redirect /expenses."
                ),
            },
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
                "L'utilisateur ajoute une dépense : /expenses/new → POST /api/expenses → redirect /expenses",
                "L'utilisateur consulte le détail d'une dépense → /expenses/[id]",
                "L'utilisateur supprime une dépense : bouton sur /expenses → DELETE /api/expenses/[id]",
            ],
        },
    },
]


def get_batch_projects(batch_size: int = 5) -> List[Dict]:
    base = [{"project_name": b["project_name"], "brief": b["brief"]} for b in PHASE0_BRIEFS]
    if batch_size <= len(base):
        return base[:batch_size]
    out: List[Dict] = []
    for i in range(batch_size):
        entry = dict(base[i % len(base)])
        if i >= len(base):
            entry["project_name"] = entry["project_name"] + f"-{i // len(base) + 1:02d}"
        out.append(entry)
    return out


def get_coverage_projects(max_projects: int = 0) -> List[Dict]:
    if max_projects > 0:
        return PHASE0_BRIEFS[:max_projects]
    return list(PHASE0_BRIEFS)
