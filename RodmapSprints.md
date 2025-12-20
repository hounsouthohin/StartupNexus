# 🚀 ROADMAP AGILE 2025 -- SOFTWARE AGENT FACTORY

### **Version Hybride Optimisée + Auto-Apprenante -- Mise à jour 19 Décembre 2025**

------------------------------------------------------------------------

## 🌟 **VISION**

Créer la **première usine logicielle 100% autonome et auto-apprenante**, capable de  
transformer une simple commande humaine  
➡️ *« Fais-moi un SaaS de gestion de tâches avec authentification »*  
en une application **full‑stack déployée, testée, sécurisée, monitorée et constamment améliorée**,  
sans intervention humaine à long terme – et qui **s’enrichit automatiquement** à chaque projet livré.

------------------------------------------------------------------------

## 🧱 **FONDATIONS TECHNIQUES – ÉTAT ACTUEL**

  ------------------------------------------------------------------------------
  Composant         Rôle simple                  Pourquoi ce choix          Statut
  ----------------- ---------------------------- -------------------------- --------------
  **n8n**           Interface humaine + webhook  Maîtrise + dashboard       ✅ Fonctionnel

  **Temporal.io**   Orchestration durable        Retries + état persistant  ✅ Fonctionnel
                    (cerveau increvable)                                   

  **LangGraph**     Chef d'orchestre des agents  Graphes clairs, ReAct      ✅ Fonctionnel
                                                 10× moins de code          (Architecte + RAG)

  **Qdrant**        Base vectorielle persistante Mémoire collective         ✅ Fonctionnel
                    + RAG réel                   Auto-apprentissage futur   (collection factory_standards peuplée)

  **E2B**           Sandbox sécurisée code       Exécution sans risque       🔧 À intégrer plus tard
  ------------------------------------------------------------------------------

------------------------------------------------------------------------

# 🏗️ **ROADMAP MISE À JOUR -- 9 SPRINTS (évolution vers l’auto-apprentissage)**

------------------------------------------------------------------------

# 🟦 PHASE 0 -- Fondations (terminée 🚀)

### 🎯 Objectif atteint :
Cœur **n8n → Flask API → Temporal → LangGraph → Qdrant** pleinement opérationnel.

### 📦 Livrables réalisés :
- API Flask + queue → déclenchement workflow
- Agent **Architecte** avec RAG réel sur collection `factory_standards`
- Standards initiaux (Next.js App Router, shadcn/ui, Clerk/NextAuth, Prisma, sécurité)
- Worker Temporal fonctionnel

------------------------------------------------------------------------

# 🟧 PHASE 1 -- MVP (en cours – 5 semaines)

### **Sprint 1 -- Spécifications + création repo** (terminé)
📌 Agents : *Architecte (avec RAG renforcé)*  
📦 Livrables : `SPEC.md` + diagramme Mermaid conformes aux standards

### **Sprint 2 -- Génération code + tests** (prochain)
📌 Agents : *Dev Agent + TestCoverage Agent*  
📦 Livrables : Code full-stack + tests unitaires + PR auto + **GitHub repo auto-push**

### **Sprint 3 -- Déploiement staging** (prochain)
📌 Agents : *QA Agent + Deploy Agent*  
📦 Livrables : Staging live < 10 min (Render/Vercel)

### **Hybride Hooks (temporaires – Phase 1)**
- **Hook secrets externes** : Si token GitHub/Render/Vercel expiré ou erreur critique non réparable par retry → notification au directeur (email/Slack) pour fourniture rapide (2 min max)  
- **Hook review qualité** : Si score de confiance RAG < 0.8 ou détection de pattern inconnu → PR GitHub avec label "human-review-needed" pour validation rapide (5-10 min)  
- **Tracking** : Chaque hook est loggé dans Temporal + upsert dans Qdrant pour analyse par LearnerAgent plus tard  
- **Objectif** : Limiter à <10% des workflows, disparaître progressivement

------------------------------------------------------------------------

# 🟩 PHASE 2 -- Industrialisation & Sécurité (3 semaines)

### **Sprint 4 -- Sécurité & Conformité**
🔐 Agents : *Security Agent + Compliance Agent*  
🎯 Objectifs :
- Audit automatique de chaque spec (vulnérabilités, déviation standards)
- 0 vulnérabilité critique
- Boucles de correction ReAct si non-conforme
- **Hook sécurité critique** : Si vulnérabilité zero-day ou compliance légale non gérée → pause + notification humaine pour override (rare)

### **Sprint 5 -- GitOps + Infra as Code**
⚙️ Agents : *Terraform Agent + DevOps Agent*  
🎯 Objectifs : Provisionning auto DB, VPC, CI/CD GitHub Actions

### **Sprint 6 -- Frontend Pro + Tests E2E**
🎨 Agents : *UI/UX Agent + Playwright Agent*  
🎯 Objectifs :
- UI professionnelle (shadcn/ui + Tailwind obligatoire)
- 100% tests E2E passés
- **Hook feedback UX initial** : Sur les premiers projets, option de demander feedback humain rapide sur staging pour valider patterns UI

### **Hybride Hooks (temporaires – Phase 2)**
- **Hook sécurité & compliance** : Overrides exceptionnels pour cas légaux ou zero-day  
- **Hook feedback initial** : Sur les premiers déploiements staging, feedback humain rapide (UX, métriques) pour accélérer l’apprentissage  
- **Tracking & réduction** : Chaque intervention humaine est analysée par le Superviseur pour réduire automatiquement les hooks au fil des sprints

------------------------------------------------------------------------

# 🟪 PHASE 3 -- Auto-Apprentissage & Évolution Continue (nouveau – 3 semaines)

### **Sprint 7 -- Meta-Agent Learner (Continuous Learning)**
🤖 Agent : *LearnerAgent* (nouveau rôle clé)  
🎯 Objectifs :
- À la fin de chaque projet réussi : analyse logs, métriques prod, feedback client, code final
- Extraction automatique des "winning patterns"
- Analyse des interventions humaines passées → upsert de nouveaux standards pour réduire les hooks
- Enrichissement continu de la mémoire collective

### **Sprint 8 -- Standards dynamiques & par client**
🧠 Agents : *LearnerAgent + Superviseur*  
🎯 Objectifs :
- Collections dédiées par client (ex: `client_123_standards`) héritant des standards globaux
- Personnalisation automatique selon historique client
- Versioning léger des standards (métadonnées : project_id, outcome, metrics)
- **Objectif explicite** : Automatisation progressive des anciens hooks humains

### **Sprint 9 -- Boucle d’amélioration complète**
🔄 Agents : *Tous les agents + Superviseur central*  
🎯 Objectifs :
- Détection proactive d’améliorations (Security → nouveau standard, DevOps → optimisation infra)
- PR automatiques d’optimisation sur les repos existants
- **Usine qui s’améliore seule à chaque livraison**
- **Élimination complète des hooks humains** (objectif atteint ici)

------------------------------------------------------------------------

# 🧠 Mini‑Concepts (Résumé express mis à jour)

### **Qdrant + LearnerAgent**
> Plus qu’une base vectorielle → **mémoire vive et évolutive** de la startup.  
> Chaque projet réussi (et chaque intervention humaine) nourrit automatiquement les standards → les prochains projets sont meilleurs et plus autonomes.

### **Standards**
> Ce ne sont plus des règles statiques imposées manuellement →  
> Ce sont des **leçons apprises validées en production**, extraites et injectées par les agents eux-mêmes (y compris les leçons tirées des rares interventions humaines).

### **Hybride Hooks**
> Interventions humaines ciblées, temporaires et trackées pour accélérer le démarrage  
> → Objectif : <10% des workflows, disparition progressive via auto-apprentissage

------------------------------------------------------------------------

# 🎯 Priorités actuelles (19 décembre 2025)

- Respect strict des standards existants (prompt Architecte renforcé) → en cours
- Fonctionnement bout-en-bout > esthétique
- Implémentation Sprint 2 (code gen + tests + GitHub auto)
- Intégration des premiers **Hybride Hooks** (secrets & review qualité)
- Prochaine milestone : **Security Agent + Compliance** (Sprint 4)
- Puis **LearnerAgent** pour passer à l’usine auto-apprenante

------------------------------------------------------------------------

# 🏁 Objectif final mis à jour

🚀 **Usine logicielle 100% autonome ET auto-apprenante prête mi-mai 2026**  
✨ 9 sprints seulement → architecture robuste, évolutive et qui **ne demande plus jamais d’intervention humaine pour s’améliorer** (hooks disparus grâce au LearnerAgent).