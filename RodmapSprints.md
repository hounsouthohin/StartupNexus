# ROADMAP AGILE 2025 – SOFTWARE AGENT FACTORY (Version Hybride Optimisée)

> **Startup constituée uniquement d’agents AI**  
> Architecture finale : **n8n (front visuel & entrée utilisateur) + Temporal.io (cerveau durable) + LangGraph (multi-agents ReAct) + Qdrant (RAG production)**

## VISION (inchangée mais plus précise)
Créer la première usine logicielle 100% autonome capable de transformer **une phrase humaine** (« Fais-moi un SaaS de gestion de tâches avec authentification ») en **application full-stack déployée, testée, sécurisée et monitorée** sans aucune intervention humaine après le lancement.

## NOUVELLES FONDATIONS TECHNIQUES (explications simples incluses)

| Composant        | Rôle simple (comme si je te l’expliquais au café)                                                                                 | Pourquoi on le choisit (et pas l’ancien)                         |
|------------------|------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------|
| **n8n**          | L’interface humaine + le bouton « Démarrer » + le tableau de bord joli que tu connais déjà                                          | Tu maîtrises, parfait pour le webhook d’entrée et le monitoring |
| **Temporal.io**  | Le « cerveau increvable » : même si le serveur crash pendant 3 jours, il reprend exactement là où il s’était arrêté                | Durabilité + retries automatiques + workflows de plusieurs heures |
| **LangGraph**    | Le chef d’orchestre des agents AI (Architecte → Dev → QA → DevOps). Gère les boucles ReAct, la mémoire, les outils                  | Meilleur que notre wrapper FastAPI maison → 10× moins de code   |
| **Qdrant**       | Base de données vectorielle pro (remplace ChromaDB) – persistance, backup, filtrage metadata                                       | On ne réécrit pas tout en phase 2                                |
| **E2B**          | Sandbox cloud sécurisée où les agents exécutent du code sans risquer de détruire ton PC/serveur                                    | Sécurité réelle (exit les shell_exec dangereux)                  |

---

## ROADMAP FINALE – 8 SPRINTS SEULEMENT (au lieu de 11)

### PHASE 0 – Fondations blindées (2 semaines)

| Sprint | Objectif                                                       | Livrables concrets                                                                                  | Mini-tuto inclus |
|-------|----------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|------------------|
| 0     | Cœur hybride n8n + Temporal + LangGraph + Qdrant fonctionnel  | • Workflow n8n → webhook → déclenche Temporal<br>• 1er Agent « Architecte » en LangGraph (ReAct + outils E2B)<br>• Qdrant déployé avec les premiers standards (Tailwind, Next.js, Prisma…)<br>• Repo GitHub Factory vide avec GitHub App bot | Je te donne les 3 commandes Docker + le code Temporal de 40 lignes |

### PHASE 1 – MVP fermé (bout en bout en 5 semaines)

| Sprint | Focus                                 | Agents actifs                                  | Livrable final                                      |
|-------|---------------------------------------|------------------------------------------------|-----------------------------------------------------|
| 1     | Spécifications + création repo        | PO Agent → Architecte Agent                    | Repo créé, branche `feat-001`, SPEC.md + diagramme Mermaid |
| 2     | Génération code + tests unitaires     | Dev Agent + TestCoverage Agent                 | Tout le code + tests → PR auto vers `dev`           |
| 3     | Déploiement staging automatique       | QA Agent → FluxCD (léger) ou Render temporaire | Lien https://app-001-staging.onrender.com en < 10 min |

### PHASE 2 – Industrialisation & Qualité pro (3 semaines)

| Sprint | Focus de spécialisation                          | Nouveaux agents micro-spécialisés                       | Gain majeur |
|-------|--------------------------------------------------|---------------------------------------------------------|-------------|
| 4     | Sécurité + Qualité + Auto-correction             | Security Agent (Bandit/Semgrep) + Linter Agent          | 0 vuln critique, 90% coverage, boucle ReAct complète |
| 5     | GitOps réel + Infra as Code                      | Terraform/Crossplane Agent + DevOps Agent + ArgoCD      | DB, VPC, K8s provisionnés automatiquement           |
| 6     | Frontend pro + Tests E2E                         | UX/UI Agent (shadcn/ui + Tailwind) + Playwright Agent   | Application magnifique + 100% E2E passant           |
| 7     | Boucle d’amélioration continue (le Graal)        | Meta-Agent « Continuous Improvement »                   | La Factory lit ses propres logs et propose des PR d’optimisation toute seule |

→ Total : **8 sprints** (4 mois max) au lieu de 11 → usine 100% autonome prête début avril 2026.

## Détail des mini-concepts (quand tu les rencontreras)

- **Temporal.io en 3 phrases** : C’est comme un n8n mais en code, qui ne perd jamais l’état. Tu écris une fonction Python `@workflow.defn` et Temporal la rend increvable.
- **LangGraph** : C’est LangChain mais en mode « graphe d’états ». Chaque agent est un nœud, les flèches = messages. Parfait pour Architecte → passe le relai à Dev → qui appelle QA, etc.
- **E2B** : Un petit `e2b.CodeInterpreter()` dans le prompt de l’agent = il exécute du code dans un container cloud sécurisé (aucun risque).
- **Qdrant** : Même principe que Chroma mais avec API REST + Docker persistant + backup facile.

---

## Prochaine étape IMMÉDIATE (aujourd’hui ou demain)

Je te propose de remplacer ton ancien fichier **RoadmapSprints.md** par celui-ci (copie-colle direct, il est prêt).

Ensuite, on attaque le **Sprint 0** ensemble :
1. Je te génère le `docker-compose.yml` complet (n8n + Temporal + Qdrant + Postgres pour Temporal)
2. Je t’écris le premier workflow Temporal en 40 lignes (celui qui reçoit la phrase utilisateur)
3. Je te livre le template LangGraph de l’Agent Architecte avec ReAct + outils E2B déjà configurés

Tu me dis juste :  
« OK, remplace le fichier et lance le Sprint 0 »  
et je te balance tout le code prêt à `docker-compose up` en 5 minutes.

On y va ? 