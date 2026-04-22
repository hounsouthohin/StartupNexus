"""
brief_catalog.py — Source unique des briefs de test structurés.

Format v3 — chaque brief contient :
- description   : description humaine de l'app (contexte métier)
- architecture  : intent SaaS, multi-tenant, public/private, workflow
- models        : Prisma DSL verbatim
- pages         : [{"path": "/...", "auth": bool}]
- pages_detail  : {"path": "QUOI afficher, quels champs, quelles actions, état vide"}
                  Les pages avec boutons/formulaires d'action sont marquées [INTERACTIVE].
- routes        : [{"method": "...", "path": "/api/..."}]
- user_flows    : flux utilisateur principaux

pages_detail est le champ le plus critique : il dit au spec_writer exactement
quoi afficher sur chaque page, ce que le LLM ne peut pas deviner seul.
[INTERACTIVE] déclenche la génération d'un Client Component séparé (page-client.tsx)
pour les éléments interactifs — les boutons/handlers ne peuvent pas être dans un Server Component.
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
                "CRUD complet sur projets, tâches et commentaires."
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
                    "Bouton 'Archiver' (PATCH /api/projects/[id] { status: 'archived' }) si active. "
                    "Bouton 'Réactiver' (PATCH { status: 'active' }) si archived. "
                    "Bouton 'Supprimer' (DELETE /api/projects/[id]). "
                    "Bouton 'Nouveau projet' en haut à droite → /projects/new. "
                    "Si liste vide : 'Aucun projet. Créez votre premier projet !'. "
                    "[INTERACTIVE]"
                ),
                "/projects/new": (
                    "Formulaire de création de projet (Client Component). "
                    "Champs : nom (input text, required, placeholder 'Nom du projet'), "
                    "description (textarea, optionnel, placeholder 'Description du projet'). "
                    "Bouton 'Créer le projet'. "
                    "Submit → POST /api/projects { name, description } → redirect /projects/[id]. "
                    "Erreur inline si nom vide."
                ),
                "/projects/[id]": (
                    "Page du projet. Titre en H1, description, badge statut. "
                    "3 colonnes côte à côte : 'À faire' (todo), 'En cours' (in-progress), 'Terminé' (done). "
                    "Chaque colonne liste les tâches filtrées par statut. "
                    "Chaque tâche affiche : titre, badge priorité (high=rouge, medium=jaune, low=gris), "
                    "lien → /tasks/[id], bouton 'Supprimer' (DELETE /api/tasks/[id]). "
                    "Bouton de transition par tâche : 'Démarrer' (todo→in-progress, PATCH /api/tasks/[id] { status: 'in-progress' }), "
                    "'Terminer' (in-progress→done, PATCH { status: 'done' }). "
                    "Bouton 'Nouvelle tâche' → /projects/[id]/tasks/new. "
                    "Bouton retour '← Mes projets'. "
                    "notFound() si projet introuvable ou n'appartient pas à l'utilisateur. "
                    "[INTERACTIVE]"
                ),
                "/projects/[id]/tasks/new": (
                    "Formulaire de création de tâche (Client Component). "
                    "Champs : titre (input text, required), "
                    "description (textarea, optionnel), "
                    "priorité (select : low / medium / high, défaut : medium). "
                    "Bouton 'Créer la tâche'. "
                    "Submit → POST /api/projects/[id]/tasks { title, description, priority } "
                    "→ redirect /projects/[id]. "
                    "Erreur inline si titre vide."
                ),
                "/tasks/[id]": (
                    "Détail d'une tâche. Titre en H1, description, badge priorité, badge statut. "
                    "Boutons de transition de statut : "
                    "'Démarrer' si todo (PATCH /api/tasks/[id] { status: 'in-progress' }), "
                    "'Terminer' si in-progress (PATCH { status: 'done' }), "
                    "'Réouvrir' si done (PATCH { status: 'todo' }). "
                    "Section 'Commentaires' : liste des commentaires triés par date croissante "
                    "(contenu, auteur=authorId tronqué, date formatée). "
                    "Bouton 'Supprimer' par commentaire si authorId = userId connecté "
                    "(DELETE /api/comments/[id]). "
                    "Formulaire inline en bas : textarea placeholder 'Ajouter un commentaire' "
                    "+ bouton 'Commenter' (POST /api/tasks/[id]/comments { content }). "
                    "Bouton retour '← Projet'. "
                    "notFound() si tâche introuvable. "
                    "[INTERACTIVE]"
                ),
            },
            "routes": [
                {"method": "GET",    "path": "/api/projects"},
                {"method": "POST",   "path": "/api/projects"},
                {"method": "GET",    "path": "/api/projects/[id]"},
                {"method": "PATCH",  "path": "/api/projects/[id]"},
                {"method": "DELETE", "path": "/api/projects/[id]"},
                {"method": "GET",    "path": "/api/projects/[id]/tasks"},
                {"method": "POST",   "path": "/api/projects/[id]/tasks"},
                {"method": "GET",    "path": "/api/tasks/[id]"},
                {"method": "PATCH",  "path": "/api/tasks/[id]"},
                {"method": "DELETE", "path": "/api/tasks/[id]"},
                {"method": "POST",   "path": "/api/tasks/[id]/comments"},
                {"method": "DELETE", "path": "/api/comments/[id]"},
            ],
            "user_flows": [
                "L'utilisateur crée un projet : /projects/new → POST /api/projects → redirect /projects/[id]",
                "L'utilisateur ajoute une tâche : /projects/[id]/tasks/new → POST /api/projects/[id]/tasks → redirect /projects/[id]",
                "L'utilisateur déplace une tâche en 'En cours' : bouton sur /projects/[id] → PATCH /api/tasks/[id] { status: 'in-progress' }",
                "L'utilisateur consulte une tâche et ajoute un commentaire : /tasks/[id] → POST /api/tasks/[id]/comments",
                "L'utilisateur archive un projet terminé : bouton sur /projects → PATCH /api/projects/[id] { status: 'archived' }",
                "L'utilisateur supprime une tâche : bouton sur /projects/[id] → DELETE /api/tasks/[id]",
            ],
        },
    },

    # ──────────────────────────────────────────────────────────────────
    # Projet 2 — CRM contact (contact-crm)
    # 3 modèles : Company, Contact, Interaction
    # Complexité : dashboard agrégé, fetch côté Client Component,
    #              relations Company→Contact→Interaction, query params pré-sélection
    # ──────────────────────────────────────────────────────────────────
    {
        "project_name": "contact-crm",
        "family": "crm",
        "tags": ["multi_model", "dashboard", "aggregation", "relations", "client_fetch"],
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
                "Les formulaires de création chargent les listes de sélection via fetch côté client."
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
                    "Bouton 'Supprimer' par ligne (DELETE /api/companies/[id]). "
                    "Bouton 'Nouvelle entreprise' en haut → /companies/new. "
                    "Si vide : 'Aucune entreprise. Ajoutez votre premier client !'. "
                    "[INTERACTIVE]"
                ),
                "/companies/new": (
                    "Formulaire de création d'entreprise (Client Component). "
                    "Champs : nom (input text, required), "
                    "secteur (select : Tech / Finance / Santé / Retail / Éducation / Autre, required), "
                    "site web (input url, optionnel, placeholder 'https://'). "
                    "Bouton 'Ajouter l'entreprise'. "
                    "Submit → POST /api/companies { name, industry, website } → redirect /companies. "
                    "Erreur inline si champ requis manquant."
                ),
                "/companies/[id]": (
                    "Détail d'une entreprise. Nom en H1, secteur badge, site web cliquable. "
                    "Section 'Contacts' : liste de tous les contacts de cette entreprise "
                    "(prénom+nom, email, téléphone, lien → /contacts/[id]). "
                    "Bouton 'Nouveau contact pour cette entreprise' → /contacts/new?companyId=[id]. "
                    "Bouton retour '← Entreprises'. "
                    "notFound() si entreprise introuvable ou n'appartient pas à l'utilisateur. "
                    "[INTERACTIVE]"
                ),
                "/contacts": (
                    "Liste de tous les contacts. "
                    "Chaque ligne : prénom+nom, email, téléphone (ou '-'), "
                    "entreprise (nom via include, lien → /companies/[id]). "
                    "Lien → /contacts/[id]. "
                    "Bouton 'Supprimer' par ligne (DELETE /api/contacts/[id]). "
                    "Bouton 'Nouveau contact' en haut → /contacts/new. "
                    "Si vide : 'Aucun contact.'. "
                    "[INTERACTIVE]"
                ),
                "/contacts/new": (
                    "Formulaire de création de contact (Client Component). "
                    "Champs : prénom (input text, required), nom (input text, required), "
                    "email (input email, required), téléphone (input tel, optionnel), "
                    "entreprise (select parmi les entreprises de l'utilisateur, required — "
                    "pré-sélectionné si ?companyId= présent en query param). "
                    "Charger la liste des entreprises via GET /api/companies au montage du composant "
                    "(useEffect + fetch). "
                    "Bouton 'Ajouter le contact'. "
                    "Submit → POST /api/contacts { firstName, lastName, email, phone, companyId } "
                    "→ redirect /contacts. "
                    "Erreur inline si champ requis manquant."
                ),
                "/contacts/[id]": (
                    "Profil du contact. Prénom+Nom en H1, email (lien mailto:), téléphone, "
                    "entreprise (nom, lien → /companies/[id]). "
                    "Section 'Historique des interactions' : toutes les interactions de ce contact "
                    "triées par date décroissante (type badge coloré : "
                    "Appel=bleu, Email=vert, Réunion=orange, Démo=violet, Autre=gris ; "
                    "notes en texte ; date formatée). "
                    "Bouton 'Supprimer' par interaction (DELETE /api/interactions/[id]). "
                    "Bouton 'Ajouter une interaction' → /interactions/new?contactId=[id]. "
                    "Bouton retour '← Contacts'. "
                    "notFound() si contact introuvable. "
                    "[INTERACTIVE]"
                ),
                "/interactions/new": (
                    "Formulaire d'ajout d'interaction (Client Component). "
                    "Champs : type (select : Appel téléphonique / Email / Réunion / Démo / Autre, required), "
                    "notes (textarea, required, placeholder 'Résumé de l'échange...'), "
                    "date (input date, required, défaut = aujourd'hui), "
                    "contact (select parmi tous les contacts de l'utilisateur, required — "
                    "pré-sélectionné si ?contactId= présent en query param). "
                    "Charger la liste des contacts via GET /api/contacts au montage du composant "
                    "(useEffect + fetch). "
                    "Bouton 'Enregistrer l'interaction'. "
                    "Submit → POST /api/interactions { type, notes, date, contactId } "
                    "→ redirect /contacts/[contactId] si contactId connu, sinon /contacts. "
                    "Erreur inline si champ requis manquant."
                ),
            },
            "routes": [
                {"method": "GET",    "path": "/api/companies"},
                {"method": "POST",   "path": "/api/companies"},
                {"method": "GET",    "path": "/api/companies/[id]"},
                {"method": "DELETE", "path": "/api/companies/[id]"},
                {"method": "GET",    "path": "/api/contacts"},
                {"method": "POST",   "path": "/api/contacts"},
                {"method": "GET",    "path": "/api/contacts/[id]"},
                {"method": "DELETE", "path": "/api/contacts/[id]"},
                {"method": "GET",    "path": "/api/interactions"},
                {"method": "POST",   "path": "/api/interactions"},
                {"method": "DELETE", "path": "/api/interactions/[id]"},
            ],
            "user_flows": [
                "L'utilisateur ajoute une entreprise : /companies/new → POST /api/companies → redirect /companies",
                "L'utilisateur ajoute un contact dans une entreprise : /contacts/new?companyId=[id] → POST /api/contacts → redirect /contacts",
                "L'utilisateur enregistre un appel avec un contact : /interactions/new?contactId=[id] → POST /api/interactions → redirect /contacts/[id]",
                "L'utilisateur consulte le profil d'un contact et voit son historique : /contacts/[id]",
                "L'utilisateur consulte le dashboard et voit les 5 dernières interactions : /",
                "L'utilisateur supprime une entreprise sans contacts : bouton Supprimer → DELETE /api/companies/[id]",
            ],
        },
    },

    # ──────────────────────────────────────────────────────────────────
    # Projet 3 — Gestion des congés (leave-manager)
    # 3 modèles : Department, Employee, LeaveRequest
    # Complexité : workflow d'approbation multi-statut, calcul de durée,
    #              dashboard avec pending, fetch Client Component pour select
    # ──────────────────────────────────────────────────────────────────
    {
        "project_name": "leave-manager",
        "family": "hr_workflow",
        "tags": ["multi_model", "workflow", "approval", "dashboard", "date_calculations", "client_fetch"],
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
                "Les formulaires de création chargent les listes (départements, employés) "
                "via fetch côté Client Component au montage."
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
                    "dates (du X au Y), bouton 'Approuver' (PATCH /api/leaves/[id] { status: 'approved' }) "
                    "et bouton 'Rejeter' (PATCH { status: 'rejected' }). "
                    "Si aucune demande en attente : 'Aucune demande en attente.'. "
                    "Section 'Employés récents' : 3 derniers employés ajoutés (prénom+nom, poste). "
                    "[INTERACTIVE]"
                ),
                "/departments": (
                    "Liste des départements. "
                    "Chaque ligne : nom du département, nombre d'employés (via _count si possible). "
                    "Bouton 'Supprimer' par ligne (DELETE /api/departments/[id]). "
                    "Bouton 'Nouveau département' → /departments/new. "
                    "Si vide : 'Aucun département créé.'. "
                    "[INTERACTIVE]"
                ),
                "/departments/new": (
                    "Formulaire de création de département (Client Component). "
                    "Champ : nom (input text, required, placeholder 'Ex: Ingénierie, RH, Finance'). "
                    "Bouton 'Créer le département'. "
                    "Submit → POST /api/departments { name } → redirect /departments. "
                    "Erreur inline si nom vide."
                ),
                "/employees": (
                    "Liste de tous les employés. "
                    "Chaque ligne : prénom+nom, poste, département (badge via include), "
                    "date d'embauche formatée. "
                    "Lien → /employees/[id]. "
                    "Bouton 'Supprimer' par ligne (DELETE /api/employees/[id]). "
                    "Bouton 'Nouvel employé' → /employees/new. "
                    "Si vide : 'Aucun employé.'. "
                    "[INTERACTIVE]"
                ),
                "/employees/new": (
                    "Formulaire d'ajout d'employé (Client Component). "
                    "Champs : prénom (input text, required), nom (input text, required), "
                    "poste (input text, required, placeholder 'Ex: Développeur, Designer'), "
                    "département (select parmi les départements, required). "
                    "Charger la liste des départements via GET /api/departments au montage "
                    "(useEffect + fetch). "
                    "Bouton 'Ajouter l'employé'. "
                    "Submit → POST /api/employees { firstName, lastName, position, departmentId } "
                    "→ redirect /employees. "
                    "Erreur inline si champ requis manquant."
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
                    "Formulaire de demande de congé (Client Component). "
                    "Champs : employé (select parmi tous les employés, required — "
                    "pré-sélectionné si ?employeeId= présent en query param), "
                    "type (select : Congé annuel / Congé maladie / Autre, required), "
                    "date de début (input date, required), "
                    "date de fin (input date, required, >= date de début), "
                    "motif (textarea, required, placeholder 'Motif de la demande...'). "
                    "Charger la liste des employés via GET /api/employees au montage "
                    "(useEffect + fetch). "
                    "Bouton 'Soumettre la demande'. "
                    "Submit → POST /api/leaves { type, startDate, endDate, reason, employeeId } "
                    "→ redirect /leaves. "
                    "Erreur inline si champ requis manquant ou date fin < date début."
                ),
                "/leaves/[id]": (
                    "Détail d'une demande de congé. "
                    "Prénom+Nom de l'employé en H1, type badge, dates (du X au Y), "
                    "durée calculée en jours, motif, badge statut, date de soumission. "
                    "Si status=pending : bouton 'Approuver' (PATCH /api/leaves/[id] { status: 'approved' }) "
                    "et bouton 'Rejeter' (PATCH { status: 'rejected' }). "
                    "Bouton 'Supprimer' si status=pending (DELETE /api/leaves/[id] → redirect /leaves). "
                    "Bouton retour '← Demandes de congé'. "
                    "notFound() si demande introuvable. "
                    "[INTERACTIVE]"
                ),
            },
            "routes": [
                {"method": "GET",    "path": "/api/departments"},
                {"method": "POST",   "path": "/api/departments"},
                {"method": "DELETE", "path": "/api/departments/[id]"},
                {"method": "GET",    "path": "/api/employees"},
                {"method": "POST",   "path": "/api/employees"},
                {"method": "GET",    "path": "/api/employees/[id]"},
                {"method": "DELETE", "path": "/api/employees/[id]"},
                {"method": "GET",    "path": "/api/leaves"},
                {"method": "POST",   "path": "/api/leaves"},
                {"method": "GET",    "path": "/api/leaves/[id]"},
                {"method": "PATCH",  "path": "/api/leaves/[id]"},
                {"method": "DELETE", "path": "/api/leaves/[id]"},
            ],
            "user_flows": [
                "Le manager crée les départements : /departments/new → POST /api/departments → redirect /departments",
                "Le manager ajoute un employé dans un département : /employees/new → POST /api/employees → redirect /employees",
                "Le manager soumet une demande de congé pour un employé : /leaves/new → POST /api/leaves → redirect /leaves",
                "Le manager approuve une demande en attente : bouton sur / (dashboard) → PATCH /api/leaves/[id] { status: 'approved' }",
                "Le manager rejette une demande : bouton sur /leaves/[id] → PATCH /api/leaves/[id] { status: 'rejected' }",
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
