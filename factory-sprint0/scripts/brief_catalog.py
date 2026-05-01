"""
brief_catalog.py — Source unique des briefs de test structurés.

Format v4 (Option A — Server Actions, Avril 2026) — chaque brief contient :
- description   : description humaine de l'app (contexte métier)
- architecture  : intent SaaS, multi-tenant, public/private, workflow
- models        : Prisma DSL verbatim
- pages         : [{"path": "/...", "auth": bool}]
- pages_detail  : {"path": "QUOI afficher, quels champs, quelles actions, état vide"}
                  Les pages avec boutons/formulaires d'action sont marquées [INTERACTIVE].
                  Mutations : "Server Action createXxx({...})" (jamais "POST /api/...").
                  Select lists pré-chargées : "Server Component charge via xxxService.getAll(userId)
                  et passe en props au formulaire Client."
- routes        : mutations uniquement (POST/PATCH/DELETE → planner génère actions.ts).
                  Les routes GET sont supprimées — Server Components lisent via service DAL.
- user_flows    : flux utilisateur principaux

[INTERACTIVE] déclenche la génération d'un Client Component séparé pour les éléments
interactifs (boutons, formulaires avec hooks React).
"""
from __future__ import annotations

from typing import Dict, List


PHASE0_BRIEFS: List[Dict] = [

    # ──────────────────────────────────────────────────────────────────
    # Projet 1 — Gestion de projets et tâches (project-hub)
    # 3 modèles : Project, Task, Comment
    # Complexité : relations imbriquées, workflow statut, commentaires
    # ──────────────────────────────────────────────────────────────────
    {
        "project_name": "project-hub",
        "family": "project_management",
        "tags": ["multi_model", "relations", "status_workflow", "comments", "nested_routes"],
        "brief": {
            "description": (
                "Application SaaS de gestion de projets et tâches. "
                "L'utilisateur crée des projets, y ajoute des tâches avec priorité et statut, "
                "et peut commenter chaque tâche. Vue kanban par projet (todo/in-progress/done)."
            ),
            "architecture": (
                "SaaS single-tenant — toutes les pages protégées par Clerk. "
                "Task est liée à Project via projectId. Comment est liée à Task via taskId "
                "avec authorId (= userId Clerk). "
                "Workflow statut Task : todo → in-progress → done. "
                "CRUD complet sur projets, tâches et commentaires. "
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
                {"path": "/projects",                     "auth": True},
                {"path": "/projects/new",                 "auth": True},
                {"path": "/projects/[id]",                "auth": True},
                {"path": "/projects/[id]/tasks/new",      "auth": True},
                {"path": "/tasks/[id]",                   "auth": True},
            ],
            "pages_detail": {
                "/projects": (
                    "Liste des projets de l'utilisateur. "
                    "Chaque carte affiche : nom du projet, description courte (60 chars max), "
                    "badge statut (active=vert, archived=gris), date de création. "
                    "Lien cliquable → /projects/[id]. "
                    "Bouton 'Archiver' → Server Action updateProject(id, { status: 'archived' }) si active. "
                    "Bouton 'Réactiver' → Server Action updateProject(id, { status: 'active' }) si archived. "
                    "Bouton 'Supprimer' → Server Action deleteProject(id). "
                    "Bouton 'Nouveau projet' en haut à droite → /projects/new. "
                    "Si liste vide : 'Aucun projet. Créez votre premier projet !'. "
                    "[INTERACTIVE]"
                ),
                "/projects/new": (
                    "Formulaire de création de projet. "
                    "Champs : nom (input text, required, placeholder 'Nom du projet'), "
                    "description (textarea, optionnel, placeholder 'Description du projet'). "
                    "Bouton 'Créer le projet'. "
                    "Submit → Server Action createProject({ name, description }) → redirect /projects/[id]. "
                    "Erreur inline si nom vide. "
                    "[INTERACTIVE]"
                ),
                "/projects/[id]": (
                    "Page du projet. Titre en H1, description, badge statut. "
                    "3 colonnes côte à côte : 'À faire' (todo), 'En cours' (in-progress), 'Terminé' (done). "
                    "Chaque colonne liste les tâches filtrées par statut. "
                    "Chaque tâche affiche : titre, badge priorité (high=rouge, medium=jaune, low=gris), "
                    "lien → /tasks/[id], bouton 'Supprimer' → Server Action deleteTask(id). "
                    "Bouton de transition par tâche : "
                    "'Démarrer' (todo→in-progress, Server Action updateTask(id, { status: 'in-progress' })), "
                    "'Terminer' (in-progress→done, Server Action updateTask(id, { status: 'done' })). "
                    "Bouton 'Nouvelle tâche' → /projects/[id]/tasks/new. "
                    "Bouton retour '← Mes projets'. "
                    "notFound() si projet introuvable ou n'appartient pas à l'utilisateur. "
                    "[INTERACTIVE]"
                ),
                "/projects/[id]/tasks/new": (
                    "Formulaire de création de tâche. "
                    "Champs : titre (input text, required), "
                    "description (textarea, optionnel), "
                    "priorité (select : low / medium / high, défaut : medium). "
                    "Bouton 'Créer la tâche'. "
                    "Submit → Server Action createTask({ title, description, priority, projectId }) "
                    "→ redirect /projects/[id]. "
                    "Erreur inline si titre vide. "
                    "[INTERACTIVE]"
                ),
                "/tasks/[id]": (
                    "Détail d'une tâche. Titre en H1, description, badge priorité, badge statut. "
                    "Boutons de transition de statut : "
                    "'Démarrer' si todo (Server Action updateTask(id, { status: 'in-progress' })), "
                    "'Terminer' si in-progress (Server Action updateTask(id, { status: 'done' })), "
                    "'Réouvrir' si done (Server Action updateTask(id, { status: 'todo' })). "
                    "Section 'Commentaires' : liste des commentaires triés par date croissante "
                    "(contenu, auteur=authorId tronqué, date formatée). "
                    "Bouton 'Supprimer' par commentaire si authorId = userId connecté "
                    "→ Server Action deleteComment(id). "
                    "Formulaire inline en bas : textarea placeholder 'Ajouter un commentaire' "
                    "+ bouton 'Commenter' → Server Action createComment({ content, taskId }). "
                    "Bouton retour '← Projet'. "
                    "notFound() si tâche introuvable. "
                    "[INTERACTIVE]"
                ),
            },
            "routes": [
                {"method": "POST",   "path": "/api/projects"},
                {"method": "PATCH",  "path": "/api/projects/[id]"},
                {"method": "DELETE", "path": "/api/projects/[id]"},
                {"method": "POST",   "path": "/api/projects/[id]/tasks"},
                {"method": "PATCH",  "path": "/api/tasks/[id]"},
                {"method": "DELETE", "path": "/api/tasks/[id]"},
                {"method": "POST",   "path": "/api/tasks/[id]/comments"},
                {"method": "DELETE", "path": "/api/comments/[id]"},
            ],
            "user_flows": [
                "L'utilisateur crée un projet : /projects/new → Server Action createProject() → redirect /projects/[id]",
                "L'utilisateur ajoute une tâche : /projects/[id]/tasks/new → Server Action createTask() → redirect /projects/[id]",
                "L'utilisateur déplace une tâche en 'En cours' : bouton sur /projects/[id] → Server Action updateTask(id, { status: 'in-progress' })",
                "L'utilisateur consulte une tâche et ajoute un commentaire : /tasks/[id] → Server Action createComment()",
                "L'utilisateur archive un projet terminé : bouton sur /projects → Server Action updateProject(id, { status: 'archived' })",
                "L'utilisateur supprime une tâche : bouton sur /projects/[id] → Server Action deleteTask(id)",
            ],
        },
    },

    # ──────────────────────────────────────────────────────────────────
    # Projet 2 — CRM contact (contact-crm)
    # 3 modèles : Company, Contact, Interaction
    # Complexité : dashboard agrégé, pré-chargement Server Component,
    #              relations Company→Contact→Interaction, query params pré-sélection
    # ──────────────────────────────────────────────────────────────────
    {
        "project_name": "contact-crm",
        "family": "crm",
        "tags": ["multi_model", "dashboard", "aggregation", "relations", "server_preload"],
        "brief": {
            "description": (
                "Mini CRM de gestion de contacts professionnels. "
                "L'utilisateur gère ses entreprises clientes, les contacts dans chaque entreprise, "
                "et l'historique des interactions (appels, emails, réunions) par contact."
            ),
            "architecture": (
                "SaaS single-tenant — toutes les pages protégées par Clerk. "
                "Contact est lié à Company via companyId. "
                "Interaction est liée à Contact via contactId. "
                "Tous les modèles ont userId pour l'ownership direct. "
                "Dashboard avec métriques agrégées calculées côté serveur. "
                "Les formulaires de création reçoivent les listes de sélection "
                "pré-chargées côté serveur (Server Component → props Client Component). "
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
                {"path": "/",                  "auth": True},
                {"path": "/companies",         "auth": True},
                {"path": "/companies/new",     "auth": True},
                {"path": "/companies/[id]",    "auth": True},
                {"path": "/contacts",          "auth": True},
                {"path": "/contacts/new",      "auth": True},
                {"path": "/contacts/[id]",     "auth": True},
                {"path": "/interactions/new",  "auth": True},
            ],
            "pages_detail": {
                "/": (
                    "Dashboard récapitulatif (Server Component). "
                    "3 métriques en haut : nombre total d'entreprises, nombre total de contacts, "
                    "nombre total d'interactions. "
                    "Section 'Interactions récentes' : 5 dernières interactions triées par date "
                    "(type badge, notes tronquées à 80 chars, prénom+nom du contact via include, date formatée). "
                    "Section 'Accès rapides' : liens vers /companies/new, /contacts/new, /interactions/new. "
                    "Si aucune interaction : 'Aucune activité récente.'"
                ),
                "/companies": (
                    "Liste de toutes les entreprises. "
                    "Chaque ligne : nom, secteur (badge coloré), site web (lien externe si renseigné), "
                    "date d'ajout. "
                    "Lien → /companies/[id]. "
                    "Bouton 'Supprimer' par ligne → Server Action deleteCompany(id). "
                    "Bouton 'Nouvelle entreprise' en haut → /companies/new. "
                    "Si vide : 'Aucune entreprise. Ajoutez votre premier client !'. "
                    "[INTERACTIVE]"
                ),
                "/companies/new": (
                    "Formulaire de création d'entreprise. "
                    "Champs : nom (input text, required), "
                    "secteur (select : Tech / Finance / Santé / Retail / Éducation / Autre, required), "
                    "site web (input url, optionnel, placeholder 'https://'). "
                    "Bouton 'Ajouter l'entreprise'. "
                    "Submit → Server Action createCompany({ name, industry, website }) → redirect /companies. "
                    "Erreur inline si champ requis manquant. "
                    "[INTERACTIVE]"
                ),
                "/companies/[id]": (
                    "Détail d'une entreprise. Nom en H1, secteur badge, site web cliquable. "
                    "Section 'Contacts' : liste de tous les contacts de cette entreprise "
                    "(prénom+nom, email, téléphone, lien → /contacts/[id]). "
                    "Bouton 'Nouveau contact pour cette entreprise' → /contacts/new?companyId=[id]. "
                    "Bouton retour '← Entreprises'. "
                    "notFound() si entreprise introuvable ou n'appartient pas à l'utilisateur."
                ),
                "/contacts": (
                    "Liste de tous les contacts. "
                    "Chaque ligne : prénom+nom, email, téléphone (ou '-'), "
                    "entreprise (nom via include, lien → /companies/[id]). "
                    "Lien → /contacts/[id]. "
                    "Bouton 'Supprimer' par ligne → Server Action deleteContact(id). "
                    "Bouton 'Nouveau contact' en haut → /contacts/new. "
                    "Si vide : 'Aucun contact.'. "
                    "[INTERACTIVE]"
                ),
                "/contacts/new": (
                    "Formulaire de création de contact. "
                    "page.tsx (Server Component) pré-charge les entreprises via "
                    "companyService.getAll(userId) et passe companies[] en props au formulaire Client. "
                    "Champs : prénom (input text, required), nom (input text, required), "
                    "email (input email, required), téléphone (input tel, optionnel), "
                    "entreprise (select parmi companies[], required — "
                    "pré-sélectionné si ?companyId= présent en query param). "
                    "Bouton 'Ajouter le contact'. "
                    "Submit → Server Action createContact({ firstName, lastName, email, phone, companyId }) "
                    "→ redirect /contacts. "
                    "Erreur inline si champ requis manquant. "
                    "[INTERACTIVE]"
                ),
                "/contacts/[id]": (
                    "Profil du contact. Prénom+Nom en H1, email (lien mailto:), téléphone, "
                    "entreprise (nom, lien → /companies/[id]). "
                    "Section 'Historique des interactions' : toutes les interactions de ce contact "
                    "triées par date décroissante (type badge coloré : "
                    "Appel=bleu, Email=vert, Réunion=orange, Démo=violet, Autre=gris ; "
                    "notes en texte ; date formatée). "
                    "Bouton 'Supprimer' par interaction → Server Action deleteInteraction(id). "
                    "Bouton 'Ajouter une interaction' → /interactions/new?contactId=[id]. "
                    "Bouton retour '← Contacts'. "
                    "notFound() si contact introuvable. "
                    "[INTERACTIVE]"
                ),
                "/interactions/new": (
                    "Formulaire d'ajout d'interaction. "
                    "page.tsx (Server Component) pré-charge les contacts via "
                    "contactService.getAll(userId) et passe contacts[] en props au formulaire Client. "
                    "Champs : type (select : Appel téléphonique / Email / Réunion / Démo / Autre, required), "
                    "notes (textarea, required, placeholder 'Résumé de l'échange...'), "
                    "date (input date, required, défaut = aujourd'hui), "
                    "contact (select parmi contacts[], required — "
                    "pré-sélectionné si ?contactId= présent en query param). "
                    "Bouton 'Enregistrer l'interaction'. "
                    "Submit → Server Action createInteraction({ type, notes, date, contactId }) "
                    "→ redirect /contacts/[contactId] si contactId connu, sinon /contacts. "
                    "Erreur inline si champ requis manquant. "
                    "[INTERACTIVE]"
                ),
            },
            "routes": [
                {"method": "POST",   "path": "/api/companies"},
                {"method": "DELETE", "path": "/api/companies/[id]"},
                {"method": "POST",   "path": "/api/contacts"},
                {"method": "DELETE", "path": "/api/contacts/[id]"},
                {"method": "POST",   "path": "/api/interactions"},
                {"method": "DELETE", "path": "/api/interactions/[id]"},
            ],
            "user_flows": [
                "L'utilisateur ajoute une entreprise : /companies/new → Server Action createCompany() → redirect /companies",
                "L'utilisateur ajoute un contact dans une entreprise : /contacts/new?companyId=[id] → Server Action createContact() → redirect /contacts",
                "L'utilisateur enregistre un appel avec un contact : /interactions/new?contactId=[id] → Server Action createInteraction() → redirect /contacts/[id]",
                "L'utilisateur consulte le profil d'un contact et voit son historique : /contacts/[id]",
                "L'utilisateur consulte le dashboard et voit les 5 dernières interactions : /",
                "L'utilisateur supprime une entreprise sans contacts : bouton Supprimer → Server Action deleteCompany(id)",
            ],
        },
    },

    # ──────────────────────────────────────────────────────────────────
    # Projet 3 — Gestion des congés (leave-manager)
    # 3 modèles : Department, Employee, LeaveRequest
    # Complexité : workflow d'approbation multi-statut, calcul de durée,
    #              dashboard avec pending, pré-chargement Server Component pour selects
    # ──────────────────────────────────────────────────────────────────
    {
        "project_name": "leave-manager",
        "family": "hr_workflow",
        "tags": ["multi_model", "workflow", "approval", "dashboard", "date_calculations", "server_preload"],
        "brief": {
            "description": (
                "Application RH de gestion des demandes de congé. "
                "L'utilisateur (manager RH) gère les départements, les employés, "
                "et traite les demandes de congé (approbation ou rejet). "
                "Dashboard avec demandes en attente et métriques clés."
            ),
            "architecture": (
                "SaaS single-tenant — toutes les pages protégées par Clerk. "
                "Employee est lié à Department via departmentId. "
                "LeaveRequest est liée à Employee via employeeId. "
                "Tous les modèles ont userId (le manager connecté via Clerk). "
                "Workflow statut LeaveRequest : pending → approved | rejected. "
                "Les formulaires de création reçoivent les listes (départements, employés) "
                "pré-chargées côté serveur (Server Component → props Client Component). "
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
                {"path": "/",                "auth": True},
                {"path": "/departments",     "auth": True},
                {"path": "/departments/new", "auth": True},
                {"path": "/employees",       "auth": True},
                {"path": "/employees/new",   "auth": True},
                {"path": "/employees/[id]",  "auth": True},
                {"path": "/leaves",          "auth": True},
                {"path": "/leaves/new",      "auth": True},
                {"path": "/leaves/[id]",     "auth": True},
            ],
            "pages_detail": {
                "/": (
                    "Dashboard RH (Server Component). "
                    "3 métriques en haut : total employés, demandes en attente (status=pending), "
                    "demandes approuvées ce mois. "
                    "Section 'Demandes en attente' : liste de toutes les LeaveRequest avec status=pending — "
                    "prénom+nom de l'employé (via include), type de congé badge, "
                    "dates (du X au Y), bouton 'Approuver' → Server Action updateLeaveRequest(id, { status: 'approved' }) "
                    "et bouton 'Rejeter' → Server Action updateLeaveRequest(id, { status: 'rejected' }). "
                    "Si aucune demande en attente : 'Aucune demande en attente.'. "
                    "Section 'Employés récents' : 3 derniers employés ajoutés (prénom+nom, poste). "
                    "[INTERACTIVE]"
                ),
                "/departments": (
                    "Liste des départements. "
                    "Chaque ligne : nom du département, nombre d'employés (via _count si possible). "
                    "Bouton 'Supprimer' par ligne → Server Action deleteDepartment(id). "
                    "Bouton 'Nouveau département' → /departments/new. "
                    "Si vide : 'Aucun département créé.'. "
                    "[INTERACTIVE]"
                ),
                "/departments/new": (
                    "Formulaire de création de département. "
                    "Champ : nom (input text, required, placeholder 'Ex: Ingénierie, RH, Finance'). "
                    "Bouton 'Créer le département'. "
                    "Submit → Server Action createDepartment({ name }) → redirect /departments. "
                    "Erreur inline si nom vide. "
                    "[INTERACTIVE]"
                ),
                "/employees": (
                    "Liste de tous les employés. "
                    "Chaque ligne : prénom+nom, poste, département (badge via include), "
                    "date d'embauche formatée. "
                    "Lien → /employees/[id]. "
                    "Bouton 'Supprimer' par ligne → Server Action deleteEmployee(id). "
                    "Bouton 'Nouvel employé' → /employees/new. "
                    "Si vide : 'Aucun employé.'. "
                    "[INTERACTIVE]"
                ),
                "/employees/new": (
                    "Formulaire d'ajout d'employé. "
                    "page.tsx (Server Component) pré-charge les départements via "
                    "departmentService.getAll(userId) et passe departments[] en props au formulaire Client. "
                    "Champs : prénom (input text, required), nom (input text, required), "
                    "poste (input text, required, placeholder 'Ex: Développeur, Designer'), "
                    "département (select parmi departments[], required). "
                    "Bouton 'Ajouter l'employé'. "
                    "Submit → Server Action createEmployee({ firstName, lastName, position, departmentId }) "
                    "→ redirect /employees. "
                    "Erreur inline si champ requis manquant. "
                    "[INTERACTIVE]"
                ),
                "/employees/[id]": (
                    "Profil d'un employé. Prénom+Nom en H1, poste, département badge. "
                    "Section 'Congés' : liste de toutes ses LeaveRequest triées par startDate décroissant "
                    "(type badge, dates, durée calculée en jours : "
                    "Math.ceil((endDate - startDate) / (1000*60*60*24)) + 1 jours, "
                    "badge statut : pending=jaune, approved=vert, rejected=rouge). "
                    "Bouton 'Nouvelle demande pour cet employé' → /leaves/new?employeeId=[id]. "
                    "Bouton retour '← Employés'. "
                    "notFound() si employé introuvable."
                ),
                "/leaves": (
                    "Liste de toutes les demandes de congé. "
                    "Chaque ligne : prénom+nom de l'employé (via include), "
                    "type badge (Annuel=bleu, Maladie=orange, Autre=gris), "
                    "dates (du X au Y), durée en jours, badge statut (pending=jaune, approved=vert, rejected=rouge). "
                    "Lien → /leaves/[id]. "
                    "Bouton 'Nouvelle demande' → /leaves/new. "
                    "Si vide : 'Aucune demande de congé.'. "
                    "[INTERACTIVE]"
                ),
                "/leaves/new": (
                    "Formulaire de demande de congé. "
                    "page.tsx (Server Component) pré-charge les employés via "
                    "employeeService.getAll(userId) et passe employees[] en props au formulaire Client. "
                    "Champs : employé (select parmi employees[], required — "
                    "pré-sélectionné si ?employeeId= présent en query param), "
                    "type (select : Congé annuel / Congé maladie / Autre, required), "
                    "date de début (input date, required), "
                    "date de fin (input date, required, >= date de début), "
                    "motif (textarea, required, placeholder 'Motif de la demande...'). "
                    "Bouton 'Soumettre la demande'. "
                    "Submit → Server Action createLeaveRequest({ type, startDate, endDate, reason, employeeId }) "
                    "→ redirect /leaves. "
                    "Erreur inline si champ requis manquant ou date fin < date début. "
                    "[INTERACTIVE]"
                ),
                "/leaves/[id]": (
                    "Détail d'une demande de congé. "
                    "Prénom+Nom de l'employé en H1, type badge, dates (du X au Y), "
                    "durée calculée en jours, motif, badge statut, date de soumission. "
                    "Si status=pending : bouton 'Approuver' → Server Action updateLeaveRequest(id, { status: 'approved' }) "
                    "et bouton 'Rejeter' → Server Action updateLeaveRequest(id, { status: 'rejected' }). "
                    "Bouton 'Supprimer' si status=pending → Server Action deleteLeaveRequest(id) → redirect /leaves. "
                    "Bouton retour '← Demandes de congé'. "
                    "notFound() si demande introuvable. "
                    "[INTERACTIVE]"
                ),
            },
            "routes": [
                {"method": "POST",   "path": "/api/departments"},
                {"method": "DELETE", "path": "/api/departments/[id]"},
                {"method": "POST",   "path": "/api/employees"},
                {"method": "DELETE", "path": "/api/employees/[id]"},
                {"method": "POST",   "path": "/api/leaves"},
                {"method": "PATCH",  "path": "/api/leaves/[id]"},
                {"method": "DELETE", "path": "/api/leaves/[id]"},
            ],
            "user_flows": [
                "Le manager crée les départements : /departments/new → Server Action createDepartment() → redirect /departments",
                "Le manager ajoute un employé dans un département : /employees/new → Server Action createEmployee() → redirect /employees",
                "Le manager soumet une demande de congé pour un employé : /leaves/new → Server Action createLeaveRequest() → redirect /leaves",
                "Le manager approuve une demande en attente : bouton sur / (dashboard) → Server Action updateLeaveRequest(id, { status: 'approved' })",
                "Le manager rejette une demande : bouton sur /leaves/[id] → Server Action updateLeaveRequest(id, { status: 'rejected' })",
                "Le manager consulte l'historique des congés d'un employé : /employees/[id]",
            ],
        },
    },
]


def get_batch_projects(batch_size: int = 3) -> List[Dict]:
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
