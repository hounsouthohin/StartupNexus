# 🚀 ROADMAP AGILE 2025 -- SOFTWARE AGENT FACTORY

### **Version Hybride Optimisée + Auto-Apprenante -- Mise à jour 17 Décembre 2025**

------------------------------------------------------------------------

## 🌟 **VISION**

Créer la **première usine logicielle 100% autonome et auto-apprenante**, capable de
transformer une simple commande humaine  
➡️ *« Fais-moi un SaaS de gestion de tâches avec authentification »*  
en une application **full‑stack déployée, testée, sécurisée, monitorée et constamment améliorée**,  
sans intervention humaine – et qui **s’enrichit automatiquement** à chaque projet livré.

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
- Repo GitHub + worker Temporal fonctionnel

------------------------------------------------------------------------

# 🟧 PHASE 1 -- MVP (en cours – 5 semaines)

### **Sprint 1 -- Spécifications + création repo** (terminé)
📌 Agents : *Architecte (avec RAG renforcé)*  
📦 Livrables : `SPEC.md` + diagramme Mermaid conformes aux standards

### **Sprint 2 -- Génération code + tests** (prochain)
📌 Agents : *Dev Agent + TestCoverage Agent*  
📦 Livrables : Code full-stack + tests unitaires + PR auto

### **Sprint 3 -- Déploiement staging** (prochain)
📌 Agents : *QA Agent + Deploy Agent*  
📦 Livrables : Staging live < 10 min (Render/Vercel)

------------------------------------------------------------------------

# 🟩 PHASE 2 -- Industrialisation & Sécurité (3 semaines)

### **Sprint 4 -- Sécurité & Conformité**
🔐 Agents : *Security Agent + Compliance Agent*  
🎯 Objectifs :
- Audit automatique de chaque spec (vulnérabilités, déviation standards)
- 0 vulnérabilité critique
- Boucles de correction ReAct si non-conforme

### **Sprint 5 -- GitOps + Infra as Code**
⚙️ Agents : *Terraform Agent + DevOps Agent*  
🎯 Objectifs : Provisionning auto DB, VPC, CI/CD GitHub Actions

### **Sprint 6 -- Frontend Pro + Tests E2E**
🎨 Agents : *UI/UX Agent + Playwright Agent*  
🎯 Objectifs :
- UI professionnelle (shadcn/ui + Tailwind obligatoire)
- 100% tests E2E passés

------------------------------------------------------------------------

# 🟪 PHASE 3 -- Auto-Apprentissage & Évolution Continue (nouveau – 3 semaines)

### **Sprint 7 -- Meta-Agent Learner (Continuous Learning)**
🤖 Agent : *LearnerAgent* (nouveau rôle clé)  
🎯 Objectifs :
- À la fin de chaque projet réussi : analyse logs, métriques prod, feedback client, code final
- Extraction automatique des "winning patterns"
- Génération + upsert de nouveaux standards dans Qdrant (`factory_standards`)
- Enrichissement continu de la mémoire collective (plus besoin d’ajout manuel)

### **Sprint 8 -- Standards dynamiques & par client**
🧠 Agents : *LearnerAgent + Superviseur*  
🎯 Objectifs :
- Collections dédiées par client (ex: `client_123_standards`) héritant des standards globaux
- Personnalisation automatique selon historique client
- Versioning léger des standards (métadonnées : project_id, outcome, metrics)

### **Sprint 9 -- Boucle d’amélioration complète**
🔄 Agents : *Tous les agents + Superviseur central*  
🎯 Objectifs :
- Détection proactive d’améliorations (Security → nouveau standard, DevOps → optimisation infra)
- PR automatiques d’optimisation sur les repos existants
- Usine qui s’améliore seule à chaque livraison

------------------------------------------------------------------------

# 🧠 Mini‑Concepts (Résumé express mis à jour)

### **Qdrant + LearnerAgent**
> Plus qu’une base vectorielle → **mémoire vive et évolutive** de la startup.  
> Chaque projet réussi nourrit automatiquement les standards → les prochains projets sont meilleurs dès le départ.

### **Standards**
> Ce ne sont plus des règles statiques imposées manuellement →  
> Ce sont des **leçons apprises validées en production**, extraites et injectées par les agents eux-mêmes.

------------------------------------------------------------------------

# 🎯 Priorités actuelles (17 décembre 2025)

- Respect strict des standards existants (prompt Architecte renforcé) → en cours
- Fonctionnement bout-en-bout > esthétique
- Prochaine milestone : **Security Agent + Compliance** (Sprint 4)
- Puis **LearnerAgent** pour passer à l’usine auto-apprenante

------------------------------------------------------------------------

# 🏁 Objectif final mis à jour

🚀 **Usine logicielle 100% autonome ET auto-apprenante prête mi-mai 2026**  
✨ 9 sprints seulement → architecture robuste, évolutive et qui **ne demande jamais d’intervention humaine pour s’améliorer**.