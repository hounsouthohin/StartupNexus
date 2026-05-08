"""
brief_catalog.py — Source unique des briefs de test structurés.

Format v4-L1 (Mai 2026) — briefs simplifiés niveau L1 pour validation build stable.

Niveau L1 : 4 pages par brief, pages_detail concises, aucun pattern complexe.
- Pas de dashboard avec métriques agrégées
- Pas de kanban, pas de transitions de statut multi-étapes
- Pas de pré-chargement Server Component pour les selects (FK en input text)
- Pas de routes imbriquées (/projects/[id]/tasks/new)
- Pages : 2 listes avec bouton supprimer + 2 formulaires de création simples

Format brief :
- description   : description humaine de l'app (contexte métier)
- architecture  : intent SaaS, multi-tenant, ownership
- models        : Prisma DSL verbatim
- pages         : [{"path": "/...", "auth": bool}]
- pages_detail  : {"path": "QUOI afficher, quels champs, quelles actions"}
                  [INTERACTIVE] = contient boutons ou formulaire React
- routes        : mutations POST/DELETE → génération actions.ts
- user_flows    : flux utilisateur principaux
"""
from __future__ import annotations

from typing import Dict, List


PHASE0_BRIEFS: List[Dict] = [

    # ──────────────────────────────────────────────────────────────────
    # Projet 1 — Gestion de projets et tâches (project-hub) — L1
    # 3 modèles : Project, Task, Comment
    # ──────────────────────────────────────────────────────────────────
    {
        "project_name": "project-hub",
        "family": "project_management",
        "tags": ["multi_model", "relations"],
        "brief": {
            "description": (
                "Application SaaS de gestion de projets et tâches. "
                "L'utilisateur crée des projets, y ajoute des tâches, "
                "et peut laisser des commentaires sur chaque tâche."
            ),
            "architecture": (
                "SaaS single-tenant — toutes les pages protégées par Clerk. "
                "Task est liée à Project via projectId (owner_field=userId). "
                "Comment est liée à Task via taskId (owner_field=authorId). "
                "Mutations via Server Actions (actions.ts) — jamais de routes API pour les mutations."
            ),
            "models": [
                (
                    "Project { id String @id @default(uuid()), name String, "
                    "description String?, status String @default(\"active\"), "
                    "userId String, createdAt DateTime @default(now()), @@index([userId]) }"
                ),
                (
                    "Task { id String @id @default(uuid()), title String, "
                    "description String?, status String @default(\"todo\"), "
                    "priority String @default(\"medium\"), "
                    "projectId String, userId String, "
                    "createdAt DateTime @default(now()), "
                    "@@index([projectId]), @@index([userId]) }"
                ),
                (
                    "Comment { id String @id @default(uuid()), content String, "
                    "taskId String, authorId String, "
                    "createdAt DateTime @default(now()), @@index([taskId]) }"
                ),
            ],
            "pages": [
                {"path": "/projects",      "auth": True},
                {"path": "/projects/new",  "auth": True},
                {"path": "/tasks",         "auth": True},
                {"path": "/tasks/new",     "auth": True},
            ],
            "pages_detail": {
                "/projects": (
                    "Liste des projets de l'utilisateur. "
                    "Affiche : nom, statut (badge : active=vert, archived=gris), date de création. "
                    "Bouton 'Nouveau projet' en haut → /projects/new. "
                    "Bouton 'Supprimer' par ligne → Server Action deleteProject(id). "
                    "État vide : 'Aucun projet. Créez votre premier projet !'. "
                    "[INTERACTIVE]"
                ),
                "/projects/new": (
                    "Formulaire de création de projet. "
                    "Champs : nom (input text, required), description (textarea, optionnel). "
                    "Bouton 'Créer le projet'. "
                    "Submit → Server Action createProject({ name, description }) → redirect /projects. "
                    "[INTERACTIVE]"
                ),
                "/tasks": (
                    "Liste de toutes les tâches. "
                    "Affiche : titre, priorité (badge : high=rouge, medium=jaune, low=gris), "
                    "statut (badge : todo=gris, in-progress=bleu, done=vert), date de création. "
                    "Bouton 'Nouvelle tâche' en haut → /tasks/new. "
                    "Bouton 'Supprimer' par ligne → Server Action deleteTask(id). "
                    "État vide : 'Aucune tâche.'. "
                    "[INTERACTIVE]"
                ),
                "/tasks/new": (
                    "Formulaire de création de tâche. "
                    "Champs : titre (input text, required), "
                    "description (textarea, optionnel), "
                    "priorité (select : low / medium / high, défaut medium), "
                    "projectId (input text, required, placeholder 'ID du projet'). "
                    "Bouton 'Créer la tâche'. "
                    "Submit → Server Action createTask({ title, description, priority, projectId }) → redirect /tasks. "
                    "[INTERACTIVE]"
                ),
            },
            "routes": [
                {"method": "POST",   "path": "/api/projects"},
                {"method": "DELETE", "path": "/api/projects/[id]"},
                {"method": "POST",   "path": "/api/tasks"},
                {"method": "DELETE", "path": "/api/tasks/[id]"},
            ],
            "user_flows": [
                "L'utilisateur crée un projet : /projects/new → Server Action createProject() → redirect /projects",
                "L'utilisateur crée une tâche : /tasks/new → Server Action createTask() → redirect /tasks",
                "L'utilisateur supprime un projet : bouton Supprimer → Server Action deleteProject(id)",
                "L'utilisateur supprime une tâche : bouton Supprimer → Server Action deleteTask(id)",
            ],
        },
    },

    # ──────────────────────────────────────────────────────────────────
    # Projet 2 — CRM contact (contact-crm) — L1
    # 3 modèles : Company, Contact, Interaction
    # ──────────────────────────────────────────────────────────────────
    {
        "project_name": "contact-crm",
        "family": "crm",
        "tags": ["multi_model", "relations"],
        "brief": {
            "description": (
                "Mini CRM de gestion de contacts professionnels. "
                "L'utilisateur gère ses entreprises clientes et les contacts associés."
            ),
            "architecture": (
                "SaaS single-tenant — toutes les pages protégées par Clerk. "
                "Contact est lié à Company via companyId. "
                "Interaction est liée à Contact via contactId. "
                "Tous les modèles ont userId pour l'ownership direct. "
                "Mutations via Server Actions (actions.ts) — jamais de routes API pour les mutations."
            ),
            "models": [
                (
                    "Company { id String @id @default(uuid()), name String, "
                    "website String?, industry String, "
                    "userId String, createdAt DateTime @default(now()), @@index([userId]) }"
                ),
                (
                    "Contact { id String @id @default(uuid()), firstName String, lastName String, "
                    "email String, phone String?, "
                    "companyId String, userId String, "
                    "createdAt DateTime @default(now()), "
                    "@@index([userId]), @@index([companyId]) }"
                ),
                (
                    "Interaction { id String @id @default(uuid()), "
                    "type String, notes String, date DateTime, "
                    "contactId String, userId String, "
                    "createdAt DateTime @default(now()), "
                    "@@index([userId]), @@index([contactId]) }"
                ),
            ],
            "pages": [
                {"path": "/companies",      "auth": True},
                {"path": "/companies/new",  "auth": True},
                {"path": "/contacts",       "auth": True},
                {"path": "/contacts/new",   "auth": True},
            ],
            "pages_detail": {
                "/companies": (
                    "Liste de toutes les entreprises. "
                    "Affiche : nom, secteur (badge), site web (lien si renseigné), date d'ajout. "
                    "Bouton 'Nouvelle entreprise' en haut → /companies/new. "
                    "Bouton 'Supprimer' par ligne → Server Action deleteCompany(id). "
                    "État vide : 'Aucune entreprise. Ajoutez votre premier client !'. "
                    "[INTERACTIVE]"
                ),
                "/companies/new": (
                    "Formulaire de création d'entreprise. "
                    "Champs : nom (input text, required), secteur (input text, required), "
                    "site web (input url, optionnel, placeholder 'https://'). "
                    "Bouton 'Ajouter l'entreprise'. "
                    "Submit → Server Action createCompany({ name, industry, website }) → redirect /companies. "
                    "[INTERACTIVE]"
                ),
                "/contacts": (
                    "Liste de tous les contacts. "
                    "Affiche : prénom+nom, email, téléphone (ou '-'), date d'ajout. "
                    "Bouton 'Nouveau contact' en haut → /contacts/new. "
                    "Bouton 'Supprimer' par ligne → Server Action deleteContact(id). "
                    "État vide : 'Aucun contact.'. "
                    "[INTERACTIVE]"
                ),
                "/contacts/new": (
                    "Formulaire de création de contact. "
                    "Champs : prénom (input text, required), nom (input text, required), "
                    "email (input email, required), téléphone (input tel, optionnel), "
                    "companyId (input text, required, placeholder 'ID de l'entreprise'). "
                    "Bouton 'Ajouter le contact'. "
                    "Submit → Server Action createContact({ firstName, lastName, email, phone, companyId }) → redirect /contacts. "
                    "[INTERACTIVE]"
                ),
            },
            "routes": [
                {"method": "POST",   "path": "/api/companies"},
                {"method": "DELETE", "path": "/api/companies/[id]"},
                {"method": "POST",   "path": "/api/contacts"},
                {"method": "DELETE", "path": "/api/contacts/[id]"},
            ],
            "user_flows": [
                "L'utilisateur ajoute une entreprise : /companies/new → Server Action createCompany() → redirect /companies",
                "L'utilisateur ajoute un contact : /contacts/new → Server Action createContact() → redirect /contacts",
                "L'utilisateur supprime une entreprise : bouton Supprimer → Server Action deleteCompany(id)",
                "L'utilisateur supprime un contact : bouton Supprimer → Server Action deleteContact(id)",
            ],
        },
    },

    # ──────────────────────────────────────────────────────────────────
    # Projet 3 — Suivi de facturation (invoice-tracker) — L1
    # 3 modèles : Client, Invoice, InvoiceItem
    # ──────────────────────────────────────────────────────────────────
    {
        "project_name": "invoice-tracker",
        "family": "billing",
        "tags": ["billing", "relations"],
        "brief": {
            "description": (
                "Application SaaS de suivi de facturation. "
                "L'utilisateur gère ses clients et crée des factures."
            ),
            "architecture": (
                "SaaS single-tenant — toutes les pages protégées par Clerk. "
                "Invoice est lié à Client via clientId (owner_field=userId sur Invoice). "
                "Le champ 'client Client @relation(fields: [clientId], references: [id])' "
                "dans Invoice permet invoice.client.name via include. "
                "InvoiceItem est lié à Invoice via invoiceId "
                "(owner_field=invoiceId — pas userId direct sur InvoiceItem). "
                "Mutations via Server Actions (actions.ts) — jamais de routes API pour les mutations."
            ),
            "models": [
                (
                    "Client { id String @id @default(uuid()), name String, email String, "
                    "phone String?, address String?, "
                    "invoices Invoice[], "
                    "userId String, createdAt DateTime @default(now()), @@index([userId]) }"
                ),
                (
                    "Invoice { id String @id @default(uuid()), number String, "
                    "status String @default(\"draft\"), dueDate DateTime, "
                    "clientId String, "
                    "client Client @relation(fields: [clientId], references: [id]), "
                    "userId String, createdAt DateTime @default(now()), "
                    "@@index([userId]), @@index([clientId]) }"
                ),
                (
                    "InvoiceItem { id String @id @default(uuid()), description String, "
                    "quantity Int @default(1), unitPrice Float, "
                    "invoiceId String, "
                    "@@index([invoiceId]) }"
                ),
            ],
            "pages": [
                {"path": "/clients",       "auth": True},
                {"path": "/clients/new",   "auth": True},
                {"path": "/invoices",      "auth": True},
                {"path": "/invoices/new",  "auth": True},
            ],
            "pages_detail": {
                "/clients": (
                    "Liste de tous les clients. "
                    "Affiche : nom, email (lien mailto:), téléphone (ou '-'), date d'ajout. "
                    "Bouton 'Nouveau client' en haut → /clients/new. "
                    "Bouton 'Supprimer' par ligne → Server Action deleteClient(id). "
                    "État vide : 'Aucun client. Ajoutez votre premier client !'. "
                    "[INTERACTIVE]"
                ),
                "/clients/new": (
                    "Formulaire de création de client. "
                    "Champs : nom (input text, required), email (input email, required), "
                    "téléphone (input tel, optionnel), adresse (textarea, optionnel). "
                    "Bouton 'Ajouter le client'. "
                    "Submit → Server Action createClient({ name, email, phone, address }) → redirect /clients. "
                    "[INTERACTIVE]"
                ),
                "/invoices": (
                    "Liste de toutes les factures. "
                    "Affiche : numéro, statut (badge : draft=gris, sent=bleu, paid=vert), "
                    "date d'échéance, date de création. "
                    "Bouton 'Nouvelle facture' en haut → /invoices/new. "
                    "État vide : 'Aucune facture.'. "
                    "[INTERACTIVE]"
                ),
                "/invoices/new": (
                    "Formulaire de création de facture. "
                    "Champs : numéro (input text, required, placeholder 'FAC-001'), "
                    "clientId (input text, required, placeholder 'ID du client'), "
                    "date d'échéance (input date, required). "
                    "Bouton 'Créer la facture'. "
                    "Submit → Server Action createInvoice({ number, clientId, dueDate }) → redirect /invoices. "
                    "[INTERACTIVE]"
                ),
            },
            "routes": [
                {"method": "POST",   "path": "/api/clients"},
                {"method": "DELETE", "path": "/api/clients/[id]"},
                {"method": "POST",   "path": "/api/invoices"},
                {"method": "DELETE", "path": "/api/invoices/[id]"},
            ],
            "user_flows": [
                "L'utilisateur ajoute un client : /clients/new → Server Action createClient() → redirect /clients",
                "L'utilisateur crée une facture : /invoices/new → Server Action createInvoice() → redirect /invoices",
                "L'utilisateur supprime un client : bouton Supprimer → Server Action deleteClient(id)",
            ],
        },
    },

    # ──────────────────────────────────────────────────────────────────
    # Projet 4 — Gestion des congés (leave-manager) — L1
    # 3 modèles : Department, Employee, LeaveRequest
    # Test : noms de modèles longs, segment URL "leaves" ≠ "leave-requests"
    # ──────────────────────────────────────────────────────────────────
    {
        "project_name": "leave-manager",
        "family": "hr_workflow",
        "tags": ["multi_model", "relations"],
        "brief": {
            "description": (
                "Application RH de gestion des demandes de congé. "
                "L'utilisateur gère les départements et soumet des demandes de congé."
            ),
            "architecture": (
                "SaaS single-tenant — toutes les pages protégées par Clerk. "
                "Employee est lié à Department via departmentId. "
                "LeaveRequest est liée à Employee via employeeId. "
                "Tous les modèles ont userId (le manager connecté via Clerk). "
                "Mutations via Server Actions (actions.ts) — jamais de routes API pour les mutations."
            ),
            "models": [
                (
                    "Department { id String @id @default(uuid()), name String, "
                    "userId String, createdAt DateTime @default(now()), @@index([userId]) }"
                ),
                (
                    "Employee { id String @id @default(uuid()), firstName String, lastName String, "
                    "position String, departmentId String, "
                    "userId String, createdAt DateTime @default(now()), "
                    "@@index([userId]), @@index([departmentId]) }"
                ),
                (
                    "LeaveRequest { id String @id @default(uuid()), "
                    "type String, startDate DateTime, endDate DateTime, "
                    "reason String, status String @default(\"pending\"), "
                    "employeeId String, userId String, "
                    "createdAt DateTime @default(now()), "
                    "@@index([userId]), @@index([employeeId]) }"
                ),
            ],
            "pages": [
                {"path": "/departments",      "auth": True},
                {"path": "/departments/new",  "auth": True},
                {"path": "/leaves",           "auth": True},
                {"path": "/leaves/new",       "auth": True},
            ],
            "pages_detail": {
                "/departments": (
                    "Liste des départements. "
                    "Affiche : nom, date de création. "
                    "Bouton 'Nouveau département' en haut → /departments/new. "
                    "Bouton 'Supprimer' par ligne → Server Action deleteDepartment(id). "
                    "État vide : 'Aucun département.'. "
                    "[INTERACTIVE]"
                ),
                "/departments/new": (
                    "Formulaire de création de département. "
                    "Champ : nom (input text, required, placeholder 'Ex: Ingénierie, RH, Finance'). "
                    "Bouton 'Créer le département'. "
                    "Submit → Server Action createDepartment({ name }) → redirect /departments. "
                    "[INTERACTIVE]"
                ),
                "/leaves": (
                    "Liste de toutes les demandes de congé. "
                    "Affiche : type (badge), date de début, date de fin, "
                    "statut (badge : pending=jaune, approved=vert, rejected=rouge), date de soumission. "
                    "Bouton 'Nouvelle demande' en haut → /leaves/new. "
                    "État vide : 'Aucune demande de congé.'. "
                    "[INTERACTIVE]"
                ),
                "/leaves/new": (
                    "Formulaire de demande de congé. "
                    "Champs : type (select : Congé annuel / Congé maladie / Autre, required), "
                    "date de début (input date, required), "
                    "date de fin (input date, required), "
                    "motif (textarea, required, placeholder 'Motif de la demande...'), "
                    "employeeId (input text, required, placeholder 'ID de l'employé'). "
                    "Bouton 'Soumettre la demande'. "
                    "Submit → Server Action createLeaveRequest({ type, startDate, endDate, reason, employeeId }) → redirect /leaves. "
                    "[INTERACTIVE]"
                ),
            },
            "routes": [
                {"method": "POST",   "path": "/api/departments"},
                {"method": "DELETE", "path": "/api/departments/[id]"},
                {"method": "POST",   "path": "/api/leave-requests"},
                {"method": "DELETE", "path": "/api/leave-requests/[id]"},
            ],
            "user_flows": [
                "Le manager crée un département : /departments/new → Server Action createDepartment() → redirect /departments",
                "Le manager soumet une demande de congé : /leaves/new → Server Action createLeaveRequest() → redirect /leaves",
                "Le manager supprime un département : bouton Supprimer → Server Action deleteDepartment(id)",
            ],
        },
    },

    # ──────────────────────────────────────────────────────────────────
    # Projet 5 — Suivi de dépenses (expense-tracker) — L1
    # 3 modèles : Category, Expense, Receipt
    # Test : champs Float (amount, amount), FK categoryId en input text
    # ──────────────────────────────────────────────────────────────────
    {
        "project_name": "expense-tracker",
        "family": "finance",
        "tags": ["finance", "relations"],
        "brief": {
            "description": (
                "Application SaaS de suivi de dépenses personnelles ou professionnelles. "
                "L'utilisateur catégorise ses dépenses et conserve les justificatifs."
            ),
            "architecture": (
                "SaaS single-tenant — toutes les pages protégées par Clerk. "
                "Expense est lié à Category via categoryId (owner_field=userId sur Expense). "
                "Receipt est lié à Expense via expenseId (pas userId direct sur Receipt). "
                "Mutations via Server Actions (actions.ts) — jamais de routes API pour les mutations."
            ),
            "models": [
                (
                    "Category { id String @id @default(uuid()), name String, "
                    "color String @default(\"#6366f1\"), "
                    "userId String, createdAt DateTime @default(now()), @@index([userId]) }"
                ),
                (
                    "Expense { id String @id @default(uuid()), "
                    "description String, amount Float, "
                    "date DateTime @default(now()), "
                    "categoryId String, userId String, "
                    "createdAt DateTime @default(now()), "
                    "@@index([userId]), @@index([categoryId]) }"
                ),
                (
                    "Receipt { id String @id @default(uuid()), "
                    "note String?, fileUrl String?, "
                    "expenseId String, "
                    "createdAt DateTime @default(now()), @@index([expenseId]) }"
                ),
            ],
            "pages": [
                {"path": "/categories",      "auth": True},
                {"path": "/categories/new",  "auth": True},
                {"path": "/expenses",        "auth": True},
                {"path": "/expenses/new",    "auth": True},
            ],
            "pages_detail": {
                "/categories": (
                    "Liste des catégories de dépenses de l'utilisateur. "
                    "Affiche : nom, couleur (pastille colorée), date de création. "
                    "Bouton 'Nouvelle catégorie' en haut → /categories/new. "
                    "Bouton 'Supprimer' par ligne → Server Action deleteCategory(id). "
                    "État vide : 'Aucune catégorie. Créez votre première catégorie !'. "
                    "[INTERACTIVE]"
                ),
                "/categories/new": (
                    "Formulaire de création de catégorie. "
                    "Champs : nom (input text, required), "
                    "couleur (input text, optionnel, placeholder '#6366f1'). "
                    "Bouton 'Créer la catégorie'. "
                    "Submit → Server Action createCategory({ name, color }) → redirect /categories. "
                    "[INTERACTIVE]"
                ),
                "/expenses": (
                    "Liste de toutes les dépenses de l'utilisateur. "
                    "Affiche : description, montant (formaté en €), date, date de création. "
                    "Bouton 'Nouvelle dépense' en haut → /expenses/new. "
                    "Bouton 'Supprimer' par ligne → Server Action deleteExpense(id). "
                    "État vide : 'Aucune dépense enregistrée.'. "
                    "[INTERACTIVE]"
                ),
                "/expenses/new": (
                    "Formulaire d'ajout de dépense. "
                    "Champs : description (input text, required), "
                    "montant (input number, required, step 0.01, min 0), "
                    "date (input date, required), "
                    "categoryId (input text, required, placeholder 'ID de la catégorie'). "
                    "Bouton 'Ajouter la dépense'. "
                    "Submit → Server Action createExpense({ description, amount, date, categoryId }) → redirect /expenses. "
                    "[INTERACTIVE]"
                ),
            },
            "routes": [
                {"method": "POST",   "path": "/api/categories"},
                {"method": "DELETE", "path": "/api/categories/[id]"},
                {"method": "POST",   "path": "/api/expenses"},
                {"method": "DELETE", "path": "/api/expenses/[id]"},
            ],
            "user_flows": [
                "L'utilisateur crée une catégorie : /categories/new → Server Action createCategory() → redirect /categories",
                "L'utilisateur ajoute une dépense : /expenses/new → Server Action createExpense() → redirect /expenses",
                "L'utilisateur supprime une catégorie : bouton Supprimer → Server Action deleteCategory(id)",
                "L'utilisateur supprime une dépense : bouton Supprimer → Server Action deleteExpense(id)",
            ],
        },
    },

    # ──────────────────────────────────────────────────────────────────
    # Projet 6 — Bibliothèque personnelle (book-library) — L1
    # 3 modèles : Author, Book, ReadingSession
    # Test : champs Int (publishedYear, pagesRead), DateTime optionnel
    # ──────────────────────────────────────────────────────────────────
    {
        "project_name": "book-library",
        "family": "personal",
        "tags": ["content", "relations"],
        "brief": {
            "description": (
                "Application SaaS de gestion de bibliothèque personnelle. "
                "L'utilisateur catalogue ses auteurs, ses livres et suit ses sessions de lecture."
            ),
            "architecture": (
                "SaaS single-tenant — toutes les pages protégées par Clerk. "
                "Book est lié à Author via authorId (owner_field=userId sur Book). "
                "ReadingSession est liée à Book via bookId (owner_field=userId sur ReadingSession). "
                "Mutations via Server Actions (actions.ts) — jamais de routes API pour les mutations."
            ),
            "models": [
                (
                    "Author { id String @id @default(uuid()), "
                    "firstName String, lastName String, "
                    "nationality String?, "
                    "userId String, createdAt DateTime @default(now()), @@index([userId]) }"
                ),
                (
                    "Book { id String @id @default(uuid()), "
                    "title String, genre String, "
                    "publishedYear Int, "
                    "authorId String, userId String, "
                    "createdAt DateTime @default(now()), "
                    "@@index([userId]), @@index([authorId]) }"
                ),
                (
                    "ReadingSession { id String @id @default(uuid()), "
                    "startedAt DateTime @default(now()), "
                    "finishedAt DateTime?, "
                    "pagesRead Int @default(0), "
                    "bookId String, userId String, "
                    "createdAt DateTime @default(now()), "
                    "@@index([userId]), @@index([bookId]) }"
                ),
            ],
            "pages": [
                {"path": "/authors",       "auth": True},
                {"path": "/authors/new",   "auth": True},
                {"path": "/books",         "auth": True},
                {"path": "/books/new",     "auth": True},
            ],
            "pages_detail": {
                "/authors": (
                    "Liste des auteurs de la bibliothèque. "
                    "Affiche : prénom + nom, nationalité (ou '-'), date d'ajout. "
                    "Bouton 'Ajouter un auteur' en haut → /authors/new. "
                    "Bouton 'Supprimer' par ligne → Server Action deleteAuthor(id). "
                    "État vide : 'Aucun auteur. Ajoutez votre premier auteur !'. "
                    "[INTERACTIVE]"
                ),
                "/authors/new": (
                    "Formulaire d'ajout d'auteur. "
                    "Champs : prénom (input text, required), nom (input text, required), "
                    "nationalité (input text, optionnel). "
                    "Bouton 'Ajouter l'auteur'. "
                    "Submit → Server Action createAuthor({ firstName, lastName, nationality }) → redirect /authors. "
                    "[INTERACTIVE]"
                ),
                "/books": (
                    "Liste de tous les livres de la bibliothèque. "
                    "Affiche : titre, genre (badge), année de publication, date d'ajout. "
                    "Bouton 'Ajouter un livre' en haut → /books/new. "
                    "Bouton 'Supprimer' par ligne → Server Action deleteBook(id). "
                    "État vide : 'Aucun livre. Ajoutez votre premier livre !'. "
                    "[INTERACTIVE]"
                ),
                "/books/new": (
                    "Formulaire d'ajout de livre. "
                    "Champs : titre (input text, required), genre (input text, required), "
                    "année de publication (input number, required, min 1000, max 2100), "
                    "authorId (input text, required, placeholder 'ID de l'auteur'). "
                    "Bouton 'Ajouter le livre'. "
                    "Submit → Server Action createBook({ title, genre, publishedYear, authorId }) → redirect /books. "
                    "[INTERACTIVE]"
                ),
            },
            "routes": [
                {"method": "POST",   "path": "/api/authors"},
                {"method": "DELETE", "path": "/api/authors/[id]"},
                {"method": "POST",   "path": "/api/books"},
                {"method": "DELETE", "path": "/api/books/[id]"},
            ],
            "user_flows": [
                "L'utilisateur ajoute un auteur : /authors/new → Server Action createAuthor() → redirect /authors",
                "L'utilisateur ajoute un livre : /books/new → Server Action createBook() → redirect /books",
                "L'utilisateur supprime un auteur : bouton Supprimer → Server Action deleteAuthor(id)",
                "L'utilisateur supprime un livre : bouton Supprimer → Server Action deleteBook(id)",
            ],
        },
    },

    # ──────────────────────────────────────────────────────────────────
    # Projet 7 — Organisation d'événements (event-planner) — L1
    # 3 modèles : Venue, Event, Guest
    # Test : champ Int (capacity), DateTime pour la date d'événement
    # ──────────────────────────────────────────────────────────────────
    {
        "project_name": "event-planner",
        "family": "events",
        "tags": ["events", "relations"],
        "brief": {
            "description": (
                "Application SaaS d'organisation d'événements. "
                "L'utilisateur gère ses salles et crée des événements avec leurs invités."
            ),
            "architecture": (
                "SaaS single-tenant — toutes les pages protégées par Clerk. "
                "Event est lié à Venue via venueId (owner_field=userId sur Event). "
                "Guest est lié à Event via eventId (owner_field=userId sur Guest). "
                "Mutations via Server Actions (actions.ts) — jamais de routes API pour les mutations."
            ),
            "models": [
                (
                    "Venue { id String @id @default(uuid()), "
                    "name String, address String, "
                    "capacity Int @default(50), "
                    "userId String, createdAt DateTime @default(now()), @@index([userId]) }"
                ),
                (
                    "Event { id String @id @default(uuid()), "
                    "title String, description String?, "
                    "eventDate DateTime, "
                    "venueId String, userId String, "
                    "createdAt DateTime @default(now()), "
                    "@@index([userId]), @@index([venueId]) }"
                ),
                (
                    "Guest { id String @id @default(uuid()), "
                    "firstName String, lastName String, email String, "
                    "eventId String, userId String, "
                    "createdAt DateTime @default(now()), "
                    "@@index([userId]), @@index([eventId]) }"
                ),
            ],
            "pages": [
                {"path": "/venues",       "auth": True},
                {"path": "/venues/new",   "auth": True},
                {"path": "/events",       "auth": True},
                {"path": "/events/new",   "auth": True},
            ],
            "pages_detail": {
                "/venues": (
                    "Liste des salles disponibles. "
                    "Affiche : nom, adresse, capacité (badge avec nombre), date d'ajout. "
                    "Bouton 'Nouvelle salle' en haut → /venues/new. "
                    "Bouton 'Supprimer' par ligne → Server Action deleteVenue(id). "
                    "État vide : 'Aucune salle. Ajoutez votre première salle !'. "
                    "[INTERACTIVE]"
                ),
                "/venues/new": (
                    "Formulaire d'ajout de salle. "
                    "Champs : nom (input text, required), adresse (input text, required), "
                    "capacité (input number, required, min 1, défaut 50). "
                    "Bouton 'Ajouter la salle'. "
                    "Submit → Server Action createVenue({ name, address, capacity }) → redirect /venues. "
                    "[INTERACTIVE]"
                ),
                "/events": (
                    "Liste de tous les événements. "
                    "Affiche : titre, description (tronquée à 60 chars ou '-'), "
                    "date de l'événement (formatée), date de création. "
                    "Bouton 'Nouvel événement' en haut → /events/new. "
                    "Bouton 'Supprimer' par ligne → Server Action deleteEvent(id). "
                    "État vide : 'Aucun événement planifié.'. "
                    "[INTERACTIVE]"
                ),
                "/events/new": (
                    "Formulaire de création d'événement. "
                    "Champs : titre (input text, required), "
                    "description (textarea, optionnel), "
                    "date de l'événement (input datetime-local, required), "
                    "venueId (input text, required, placeholder 'ID de la salle'). "
                    "Bouton 'Créer l'événement'. "
                    "Submit → Server Action createEvent({ title, description, eventDate, venueId }) → redirect /events. "
                    "[INTERACTIVE]"
                ),
            },
            "routes": [
                {"method": "POST",   "path": "/api/venues"},
                {"method": "DELETE", "path": "/api/venues/[id]"},
                {"method": "POST",   "path": "/api/events"},
                {"method": "DELETE", "path": "/api/events/[id]"},
            ],
            "user_flows": [
                "L'utilisateur ajoute une salle : /venues/new → Server Action createVenue() → redirect /venues",
                "L'utilisateur crée un événement : /events/new → Server Action createEvent() → redirect /events",
                "L'utilisateur supprime une salle : bouton Supprimer → Server Action deleteVenue(id)",
                "L'utilisateur supprime un événement : bouton Supprimer → Server Action deleteEvent(id)",
            ],
        },
    },

    # ──────────────────────────────────────────────────────────────────
    # Projet 8 — Support client (support-tickets) — L1
    # 3 modèles : Category, Ticket, Message
    # Test : modèle "Category" réutilisé (conflit potentiel de nommage)
    #        statut multi-valeurs sur Ticket (open/pending/closed)
    # ──────────────────────────────────────────────────────────────────
    {
        "project_name": "support-tickets",
        "family": "support",
        "tags": ["support", "relations"],
        "brief": {
            "description": (
                "Application SaaS de gestion de tickets de support. "
                "L'utilisateur crée des catégories de problèmes et ouvre des tickets."
            ),
            "architecture": (
                "SaaS single-tenant — toutes les pages protégées par Clerk. "
                "Ticket est lié à Category via categoryId (owner_field=userId sur Ticket). "
                "Message est lié à Ticket via ticketId (owner_field=authorId — pas userId direct sur Message). "
                "Mutations via Server Actions (actions.ts) — jamais de routes API pour les mutations."
            ),
            "models": [
                (
                    "Category { id String @id @default(uuid()), "
                    "name String, description String?, "
                    "userId String, createdAt DateTime @default(now()), @@index([userId]) }"
                ),
                (
                    "Ticket { id String @id @default(uuid()), "
                    "subject String, "
                    "status String @default(\"open\"), "
                    "priority String @default(\"medium\"), "
                    "categoryId String, userId String, "
                    "createdAt DateTime @default(now()), "
                    "@@index([userId]), @@index([categoryId]) }"
                ),
                (
                    "Message { id String @id @default(uuid()), "
                    "content String, "
                    "ticketId String, authorId String, "
                    "createdAt DateTime @default(now()), @@index([ticketId]) }"
                ),
            ],
            "pages": [
                {"path": "/categories",      "auth": True},
                {"path": "/categories/new",  "auth": True},
                {"path": "/tickets",         "auth": True},
                {"path": "/tickets/new",     "auth": True},
            ],
            "pages_detail": {
                "/categories": (
                    "Liste des catégories de support. "
                    "Affiche : nom, description (tronquée ou '-'), date de création. "
                    "Bouton 'Nouvelle catégorie' en haut → /categories/new. "
                    "Bouton 'Supprimer' par ligne → Server Action deleteCategory(id). "
                    "État vide : 'Aucune catégorie.'. "
                    "[INTERACTIVE]"
                ),
                "/categories/new": (
                    "Formulaire de création de catégorie. "
                    "Champs : nom (input text, required), description (textarea, optionnel). "
                    "Bouton 'Créer la catégorie'. "
                    "Submit → Server Action createCategory({ name, description }) → redirect /categories. "
                    "[INTERACTIVE]"
                ),
                "/tickets": (
                    "Liste de tous les tickets de support. "
                    "Affiche : sujet, priorité (badge : high=rouge, medium=jaune, low=gris), "
                    "statut (badge : open=bleu, pending=jaune, closed=gris), date de création. "
                    "Bouton 'Nouveau ticket' en haut → /tickets/new. "
                    "Bouton 'Supprimer' par ligne → Server Action deleteTicket(id). "
                    "État vide : 'Aucun ticket ouvert.'. "
                    "[INTERACTIVE]"
                ),
                "/tickets/new": (
                    "Formulaire d'ouverture de ticket. "
                    "Champs : sujet (input text, required), "
                    "priorité (select : low / medium / high, défaut medium), "
                    "categoryId (input text, required, placeholder 'ID de la catégorie'). "
                    "Bouton 'Ouvrir le ticket'. "
                    "Submit → Server Action createTicket({ subject, priority, categoryId }) → redirect /tickets. "
                    "[INTERACTIVE]"
                ),
            },
            "routes": [
                {"method": "POST",   "path": "/api/categories"},
                {"method": "DELETE", "path": "/api/categories/[id]"},
                {"method": "POST",   "path": "/api/tickets"},
                {"method": "DELETE", "path": "/api/tickets/[id]"},
            ],
            "user_flows": [
                "L'utilisateur crée une catégorie : /categories/new → Server Action createCategory() → redirect /categories",
                "L'utilisateur ouvre un ticket : /tickets/new → Server Action createTicket() → redirect /tickets",
                "L'utilisateur supprime une catégorie : bouton Supprimer → Server Action deleteCategory(id)",
                "L'utilisateur supprime un ticket : bouton Supprimer → Server Action deleteTicket(id)",
            ],
        },
    },

    # ──────────────────────────────────────────────────────────────────
    # Projet 9 — Inventaire d'actifs (asset-inventory) — L1
    # 3 modèles : Location, Asset, MaintenanceRecord
    # Test : Float sur MaintenanceRecord.cost, DateTime sur scheduledAt
    #        segment "maintenances" → service "maintenanceRecord"
    # ──────────────────────────────────────────────────────────────────
    {
        "project_name": "asset-inventory",
        "family": "operations",
        "tags": ["inventory", "relations"],
        "brief": {
            "description": (
                "Application SaaS d'inventaire d'actifs matériels. "
                "L'utilisateur gère les emplacements de stockage et les équipements associés."
            ),
            "architecture": (
                "SaaS single-tenant — toutes les pages protégées par Clerk. "
                "Asset est lié à Location via locationId (owner_field=userId sur Asset). "
                "MaintenanceRecord est lié à Asset via assetId (owner_field=userId sur MaintenanceRecord). "
                "Mutations via Server Actions (actions.ts) — jamais de routes API pour les mutations."
            ),
            "models": [
                (
                    "Location { id String @id @default(uuid()), "
                    "name String, description String?, "
                    "userId String, createdAt DateTime @default(now()), @@index([userId]) }"
                ),
                (
                    "Asset { id String @id @default(uuid()), "
                    "name String, serialNumber String, "
                    "status String @default(\"active\"), "
                    "locationId String, userId String, "
                    "createdAt DateTime @default(now()), "
                    "@@index([userId]), @@index([locationId]) }"
                ),
                (
                    "MaintenanceRecord { id String @id @default(uuid()), "
                    "description String, cost Float @default(0), "
                    "scheduledAt DateTime, "
                    "assetId String, userId String, "
                    "createdAt DateTime @default(now()), "
                    "@@index([userId]), @@index([assetId]) }"
                ),
            ],
            "pages": [
                {"path": "/locations",         "auth": True},
                {"path": "/locations/new",     "auth": True},
                {"path": "/assets",            "auth": True},
                {"path": "/assets/new",        "auth": True},
            ],
            "pages_detail": {
                "/locations": (
                    "Liste des emplacements de stockage. "
                    "Affiche : nom, description (ou '-'), date de création. "
                    "Bouton 'Nouvel emplacement' en haut → /locations/new. "
                    "Bouton 'Supprimer' par ligne → Server Action deleteLocation(id). "
                    "État vide : 'Aucun emplacement. Créez votre premier emplacement !'. "
                    "[INTERACTIVE]"
                ),
                "/locations/new": (
                    "Formulaire de création d'emplacement. "
                    "Champs : nom (input text, required), description (textarea, optionnel). "
                    "Bouton 'Créer l'emplacement'. "
                    "Submit → Server Action createLocation({ name, description }) → redirect /locations. "
                    "[INTERACTIVE]"
                ),
                "/assets": (
                    "Liste de tous les actifs. "
                    "Affiche : nom, numéro de série, statut (badge : active=vert, inactive=gris), date de création. "
                    "Bouton 'Nouvel actif' en haut → /assets/new. "
                    "Bouton 'Supprimer' par ligne → Server Action deleteAsset(id). "
                    "État vide : 'Aucun actif enregistré.'. "
                    "[INTERACTIVE]"
                ),
                "/assets/new": (
                    "Formulaire d'ajout d'actif. "
                    "Champs : nom (input text, required), "
                    "numéro de série (input text, required), "
                    "locationId (input text, required, placeholder 'ID de l'emplacement'). "
                    "Bouton 'Ajouter l'actif'. "
                    "Submit → Server Action createAsset({ name, serialNumber, locationId }) → redirect /assets. "
                    "[INTERACTIVE]"
                ),
            },
            "routes": [
                {"method": "POST",   "path": "/api/locations"},
                {"method": "DELETE", "path": "/api/locations/[id]"},
                {"method": "POST",   "path": "/api/assets"},
                {"method": "DELETE", "path": "/api/assets/[id]"},
            ],
            "user_flows": [
                "L'utilisateur crée un emplacement : /locations/new → Server Action createLocation() → redirect /locations",
                "L'utilisateur ajoute un actif : /assets/new → Server Action createAsset() → redirect /assets",
                "L'utilisateur supprime un emplacement : bouton Supprimer → Server Action deleteLocation(id)",
                "L'utilisateur supprime un actif : bouton Supprimer → Server Action deleteAsset(id)",
            ],
        },
    },

    # ──────────────────────────────────────────────────────────────────
    # Projet 10 — Carnet de recettes (recipe-book) — L1
    # 3 modèles : Category, Recipe, Ingredient
    # Test : Int (prepTime, servings), modèle "Category" répété (conflit)
    #        segment "ingredients" → service "ingredient" (singulier)
    # ──────────────────────────────────────────────────────────────────
    {
        "project_name": "recipe-book",
        "family": "personal",
        "tags": ["content", "relations"],
        "brief": {
            "description": (
                "Application SaaS de carnet de recettes culinaires. "
                "L'utilisateur classe ses recettes par catégorie et liste les ingrédients."
            ),
            "architecture": (
                "SaaS single-tenant — toutes les pages protégées par Clerk. "
                "Recipe est lié à Category via categoryId (owner_field=userId sur Recipe). "
                "Ingredient est lié à Recipe via recipeId (pas userId direct sur Ingredient). "
                "Mutations via Server Actions (actions.ts) — jamais de routes API pour les mutations."
            ),
            "models": [
                (
                    "Category { id String @id @default(uuid()), "
                    "name String, "
                    "userId String, createdAt DateTime @default(now()), @@index([userId]) }"
                ),
                (
                    "Recipe { id String @id @default(uuid()), "
                    "title String, description String?, "
                    "prepTime Int @default(30), servings Int @default(4), "
                    "categoryId String, userId String, "
                    "createdAt DateTime @default(now()), "
                    "@@index([userId]), @@index([categoryId]) }"
                ),
                (
                    "Ingredient { id String @id @default(uuid()), "
                    "name String, quantity String, unit String, "
                    "recipeId String, "
                    "createdAt DateTime @default(now()), @@index([recipeId]) }"
                ),
            ],
            "pages": [
                {"path": "/categories",      "auth": True},
                {"path": "/categories/new",  "auth": True},
                {"path": "/recipes",         "auth": True},
                {"path": "/recipes/new",     "auth": True},
            ],
            "pages_detail": {
                "/categories": (
                    "Liste des catégories de recettes. "
                    "Affiche : nom, date de création. "
                    "Bouton 'Nouvelle catégorie' en haut → /categories/new. "
                    "Bouton 'Supprimer' par ligne → Server Action deleteCategory(id). "
                    "État vide : 'Aucune catégorie. Créez votre première catégorie !'. "
                    "[INTERACTIVE]"
                ),
                "/categories/new": (
                    "Formulaire de création de catégorie. "
                    "Champ : nom (input text, required, placeholder 'Ex: Entrées, Plats, Desserts'). "
                    "Bouton 'Créer la catégorie'. "
                    "Submit → Server Action createCategory({ name }) → redirect /categories. "
                    "[INTERACTIVE]"
                ),
                "/recipes": (
                    "Liste de toutes les recettes. "
                    "Affiche : titre, temps de préparation (en min), nombre de portions, date de création. "
                    "Bouton 'Nouvelle recette' en haut → /recipes/new. "
                    "Bouton 'Supprimer' par ligne → Server Action deleteRecipe(id). "
                    "État vide : 'Aucune recette. Ajoutez votre première recette !'. "
                    "[INTERACTIVE]"
                ),
                "/recipes/new": (
                    "Formulaire de création de recette. "
                    "Champs : titre (input text, required), "
                    "description (textarea, optionnel), "
                    "temps de préparation en minutes (input number, required, min 1, défaut 30), "
                    "nombre de portions (input number, required, min 1, défaut 4), "
                    "categoryId (input text, required, placeholder 'ID de la catégorie'). "
                    "Bouton 'Créer la recette'. "
                    "Submit → Server Action createRecipe({ title, description, prepTime, servings, categoryId }) → redirect /recipes. "
                    "[INTERACTIVE]"
                ),
            },
            "routes": [
                {"method": "POST",   "path": "/api/categories"},
                {"method": "DELETE", "path": "/api/categories/[id]"},
                {"method": "POST",   "path": "/api/recipes"},
                {"method": "DELETE", "path": "/api/recipes/[id]"},
            ],
            "user_flows": [
                "L'utilisateur crée une catégorie : /categories/new → Server Action createCategory() → redirect /categories",
                "L'utilisateur crée une recette : /recipes/new → Server Action createRecipe() → redirect /recipes",
                "L'utilisateur supprime une catégorie : bouton Supprimer → Server Action deleteCategory(id)",
                "L'utilisateur supprime une recette : bouton Supprimer → Server Action deleteRecipe(id)",
            ],
        },
    },
]


def get_batch_projects(batch_size: int = 10) -> List[Dict]:
    base = [{"project_name": b["project_name"], "brief": b["brief"]} for b in PHASE0_BRIEFS]
    if batch_size <= len(base):
        return base[:batch_size]
    # Si batch_size > catalogue, on cycle avec suffixe numérique pour éviter les collisions workdir
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
