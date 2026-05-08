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
]


def get_batch_projects(batch_size: int = 4) -> List[Dict]:
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
