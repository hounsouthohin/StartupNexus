# 🚀 ROADMAP AGILE 2025 -- SOFTWARE AGENT FACTORY

**Version 1.5 -- Sprint 2 Rétrospective + Gouvernance Standards**  
**Date : 17 Février 2026**

---

## 🎯 VISION

Usine logicielle 100% autonome et auto-apprenante transformant une commande humaine en application full-stack déployée, testée, sécurisée et constamment améliorée, sans intervention humaine.

---

## 📋 SPRINTS EXÉCUTABLES

---

### **PHASE 0 -- Fondations** ✅ TERMINÉ

| Composant | Rôle | Statut |
|-----------|------|--------|
| n8n | Interface humaine + webhook | ✅ Opérationnel |
| Temporal.io | Orchestration durable | ✅ Opérationnel |
| LangGraph | Chef d'orchestre agents | ✅ Opérationnel |
| Qdrant | Base vectorielle (1 collection initiale) | ✅ Opérationnel |

**Collection Qdrant initiale :**
- `factory_standards` (global, peuplée avec standards initiaux)

---

### **SPRINT 0.5 -- Validation Architecture + Contrats Interface** ✅ TERMINÉ

| Dimension | Détail |
|-----------|--------|
| **Objectif** | Projet pilote validant architecture + définition contrats interface agents |
| **Agent** | Architecte Agent + orchestration manuelle temporaire |
| **Livrable** | 1 micro-projet (ToDo app) déployé + contrats JSON schemas agents + rapport validation |
| **Signal mesurable** | Projet fonctionnel prod + contrats interface documentés + baseline complexité orchestration mesurée |

**Contrats Interface Obligatoires :**
```yaml
Pour chaque agent (même fusionné):
  - Input Schema: JSON strict (validation)
  - Output Schema: JSON strict (validation)
  - Error Schema: codes erreur standardisés
  - Health Check: endpoint /status

Exemple DevTestAgent:
  - Conceptuellement: DevAgent + TestAgent (2 responsabilités)
  - Physiquement: 1 déploiement (fusion optimisation)
  - Interface: 2 contrats distincts (dev_input/output + test_input/output)
```

---

### **SPRINT 1 -- Spécifications + Superviseur DRAFT** ✅ TERMINÉ

| Dimension | Détail |
|-----------|--------|
| **Objectif** | Spécifications techniques + architecture Superviseur PROVISOIRE |
| **Agent** | Architecte Agent (RAG sur factory_standards) |
| **Livrable** | SPEC.md + diagramme Mermaid + repo GitHub + SUPERVISEUR_DRAFT_v0.md |
| **Signal mesurable** | Score RAG >0.75 + Superviseur doc >300 lignes avec tags obligatoires |

**Tags Obligatoires Document :**
```markdown
# SUPERVISEUR CENTRAL - DRAFT v0
⚠️ STATUT: PROVISOIRE
⚠️ REVIEW_MANDATORY: Sprint 4
⚠️ NO_OPTIMIZATION: Interdite avant validation empirique
⚠️ NO_HARD_CONTRACTS: Interfaces flexibles uniquement
```

---

### **SPRINT 2 -- Génération Code + Tests + Infrastructure Apprentissage** ✅ TERMINÉ

| Dimension | Détail |
|-----------|--------|
| **Objectif** | Code full-stack + infrastructure apprentissage + corrections critiques |
| **Agents** | DevTestAgent + EvaluatorAgent + LearnerAgent (shadow) |
| **Livrable** | Code + tests + PR + corrections Phase 1 + standards enrichis |
| **Signal mesurable** | Coverage >80% + Phase 1 validée + 61 standards Qdrant |

**✅ Nouveau v1.5 — PHASE 1 CORRECTIONS (17 Fév 2026) :**

**Architecture Layered Implémentée :**
```yaml
Hiérarchie source de vérité:
  Code: Sécurité absolue (validation paths, interdictions)
  Prompt: Workflow et structure (quand appeler RAG, ordre opérations)
  RAG: Détails techniques évolutifs (versions, patterns, configs)
```

**Corrections Appliquées :**
1. **Prompts centralisés** : `utils/prompt_loader.py` + load_prompt()
2. **Prompts nettoyés** : 0 version hardcodée (délégation au RAG)
3. **Patches loggués** : tool_patch_applied (7 events/run observés)
4. **Métriques vraies** : clerk_compliant détection réelle
5. **Docker healthchecks** : Qdrant + Temporal + PostgreSQL
6. **Standards critiques** : shadcn/ui, Prisma 7, npm tokens, Mermaid

**Défense à 2 Niveaux (Principe Architectural) :**
```yaml
Niveau 1 - Prévention (RAG/Prompt):
  - Standards Qdrant enrichis (mots-clés multiples)
  - k=5 retrieval (était 2)
  - Prompts chargés dynamiquement
  - Agent consulte RAG AVANT génération

Niveau 2 - Garde-fou Observable (Tool):
  - Sanitize package.json avant npm install
  - Validation noms packages npm
  - Suppression packages invalides
  - Logging tool_patch_applied
  → LearnerAgent voit patterns → propose renforcement standards
```

**Standards Qdrant — État Sprint 2 :**
- 61 standards opérationnels
- Catégories : nextjs, clerk, prisma, testing, deployment
- Priorités : HIGH (10), MEDIUM (30), LOW (21)

**LearnerAgent Shadow Mode :**
- 9 events loggués par run
- Patterns détectés : middleware_matcher, next_version, ts_jest_version
- avg_quality_score : 13.8 (baseline observationnelle)

---

### **SPRINT 3 -- Déploiement + Gouvernance Standards + Sémantique Workflow**

| Dimension | Détail |
|-----------|--------|
| **Objectif** | Staging + workflow sémantique + standards gouvernance + corrections critiques |
| **Agents** | QADeployAgent + Superviseur + LearnerAgent (shadow) + get_latest_version tool |
| **Livrable** | URL staging + workflow_status/build_status séparé + standards metadata + corrections Prisma 7 |
| **Signal mesurable** | Temps <10min + sémantique clarifiée + standards versionnés + shadcn/ui error=0 |

**✅ Nouveau v1.5 — CORRECTIONS CRITIQUES SPRINT 3 :**

**1. Workflow Sémantique (Recommandation Gemini Option B) :**
```python
@dataclass
class TodoPilotOutput:
    workflow_status: str  # "COMPLETED", "FAILED_UNRECOVERABLE"
    build_status: str     # "SUCCESS", "BUILD_FAILED", "TESTS_FAILED", "NOT_RUN"
    project_name: str
    generated_files_count: int
    # ...

Impact:
  - Workflow continue même si build fail → collecte données
  - Statut explicite PARTIAL/FAILURE si DevTest=false
  - LearnerAgent reçoit signaux clairs
  - Métriques fiables (workflow vs build séparés)
```

**2. Standards Qdrant — Metadata Gouvernance (Phase 1) :**
```python
{
    "category": "nextjs",
    "text": "...",
    "tags": [...],
    "priority": "HIGH",
    
    # NOUVEAU — Metadata gouvernance
    "version": "1.0",                    # Version du standard
    "created_at": "2026-02-17",          # Date ajout
    "last_validated": "2026-02-17",      # Dernière validation
    "dependencies": ["next@14.2.3"],     # Dépendances trackées
    "source": "manual",                  # manual | learner | web_search
    "confidence": 1.0,                   # 0-1, baisse si non validé
}
```

**3. Standards Critiques Additionnels :**
```yaml
Ajoutés Sprint 3:
  - shadcn/ui package invalide (défense 2 niveaux)
  - Prisma 7 breaking changes (datasource.url)
  - Prisma versions cohérentes (CLI + client)
  - Mermaid validation timeout
  - npm token warning containers
  - Setup projet Next.js (structure /app, /components, /lib)
  - Clerk authentication (ClerkProvider, middleware)
  - Prisma database (PrismaClient singleton)
  - shadcn/ui components (initialisation CLI)
  - Jest testing (config, setup, mocks)
```

**4. get_latest_version Tool (Fin Sprint 3) :**
```python
def get_latest_version(package: str, registry: str = "npm") -> dict:
    """
    Récupère version stable récente package npm/pypi.
    
    Returns:
        {
            "package": "next",
            "latest_stable": "15.0.2",
            "current_recommended": "14.2.3",  # depuis RAG
            "breaking_changes": True/False
        }
    
    Usage:
        - LearnerAgent hebdomadaire check versions
        - Propose mise à jour standards si version mature
        - Pas de update automatique (gouvernance humaine)
    """
```

**Standards Minimum Critiques Sprint 3 :**
1. Setup Projet (structure, tsconfig, scripts)
2. Clerk Authentication (provider, middleware, pages)
3. Prisma Database (singleton, User model)
4. shadcn/ui Components (init CLI, composants courants)
5. Jest Testing (config, setup, mocks Clerk)

**Validation Sprint 3 :**
- shadcn/ui error disparue (défense 2 niveaux fonctionne)
- Prisma 7 migrations réussies
- Standards métadata appliquée 5+ standards critiques
- get_latest_version opérationnel

---

### **SPRINT 4 -- Gate Décisionnel + Baseline Dynamique + Sécurité**

| Dimension | Détail |
|-----------|--------|
| **Objectif** | Validation architecture empirique + baseline glissante + sécurité + finalisation Superviseur |
| **Agents** | SecurityComplianceAgent + Superviseur (finalisation) + LearnerAgent (validation) + Evaluator (baseline) |
| **Livrable** | Décision architecture + Superviseur v1.0 + baseline mobile activée + 0 CRITICAL + standards validés |
| **Signal mesurable** | 3 projets prod + décision split/fusion documentée + baseline rolling définie + suggestions LearnerAgent validées |

**Baseline Mobile Sprint 4 :**
```yaml
Méthode:
  type: rolling_average
  window: 3 derniers projets
  recalcul: tous les projets (dynamique)

Métriques Baseline:
  - intervention_humaine_rate: moyenne(projets N-2, N-1, N)
  - evaluator_score: moyenne(projets N-2, N-1, N)
  - deployment_time: moyenne(projets N-2, N-1, N)
  - error_rate: moyenne(projets N-2, N-1, N)
  - standards_auto_generated: count nouveaux standards
```

**LearnerAgent Validation :**
- Review suggestions shadow mode (15-20 suggestions cumulées)
- Validation humain : pertinence >70%, schéma Qdrant OK
- **SI validation >70%** → activation mode actif Sprint 5
- **SI validation <70%** → amélioration prompts, shadow prolongé

**🔔 Rappel Critique Learner (à garder jusqu'à Sprint 5) :**
```yaml
Pattern cible:
  - LearnerActivity dédiée Temporal: OBLIGATOIRE (comme architect/dev_test/qa/github)
  - Architecture Learner hybride:
      1) Logique déterministe (scoring/patterns) = source de vérité
      2) LLM optionnel (prompt learner) pour reformulation uniquement
      3) Gouvernance humaine avant tout upsert Qdrant

Garde-fous:
  - Learner non bloquant pour le workflow principal
  - Contrats input/output learner validés runtime
  - Logs shadow structurés et auditables
```

---

### **SPRINT 5 -- LearnerAgent Actif + Standards Maintenance + Web Search**

| Dimension | Détail |
|-----------|--------|
| **Objectif** | Apprentissage actif + maintenance automatique + web search agents |
| **Agents** | TerraformDevOpsAgent + LearnerAgent (actif) + StandardsMaintenanceAgent + web_search tool |
| **Livrable** | Infra auto + upsert standards + maintenance hebdo + web search opérationnel |
| **Signal mesurable** | Infra <15min + ≥1 upsert validé + maintenance détecte obsolescence + web search validé |

**✅ Nouveau v1.5 — STANDARDS MAINTENANCE AGENT :**

```python
@workflow.defn
class StandardsMaintenanceWorkflow:
    """
    Tourne hebdomadaire (Temporal scheduled workflow)
    """
    
    async def run(self):
        # 1. Détection obsolescence
        outdated = await self._check_external_dependencies()
        # get_latest_version pour chaque dependency trackée
        # Flag si version majeure retard
        
        # 2. Détection contradictions
        conflicts = await self._detect_conflicts()
        # Standards similaires texte différent
        
        # 3. Détection redondances
        duplicates = await self._find_duplicates()
        # Même information, 2+ standards
        
        # 4. Validation confidence
        low_confidence = await self._check_confidence()
        # Standards confidence <0.5
        # Non validés >90 jours
        
        # 5. Auto-fix si possible
        for dup in duplicates:
            if dup["confidence_diff"] > 0.3:
                await self._auto_merge(dup)  # Un standard meilleur
        
        # 6. Rapport humain si critique
        if outdated or conflicts or low_confidence:
            await self._send_notification(report)
        
        return report
```

**Détection Automatique Obsolescence :**
```yaml
Check 1 - Dependencies externes:
  - Scan dependencies chaque standard
  - get_latest_version(dep) vs current
  - Flag si semver.compare(latest, current) > 1

Check 2 - Dernière validation:
  - days_since = today - last_validated
  - SI days_since > 90: confidence *= 0.9
  - SI confidence < 0.5: flag pour review

Check 3 - Contradictions:
  - find_similar_standards(embedding)
  - SI texte différent: flag conflit

Check 4 - Redondances:
  - find_duplicates(semantic)
  - SI confidence_diff > 0.3: auto-merge
```

**✅ Nouveau v1.5 — WEB SEARCH POUR AGENTS :**

```python
@tool
def web_search(query: str, context: str) -> dict:
    """
    Agent cherche connaissance externe (StackOverflow, docs officielles).
    
    Args:
        query: Question technique
        context: Contexte projet (erreur, stack, versions)
    
    Returns:
        {
            "sources": [
                {"url": "...", "title": "...", "relevance": 0.9}
            ],
            "summary": "Solution condensée",
            "should_standardize": True/False
        }
    
    Usage:
        - DevAgent face à erreur non documentée RAG
        - LearnerAgent analyse succès web_search
        - SI URL utilisée 3x succès → propose distillation standard RAG
    
    Sécurité:
        - Allowlist sources officielles (npmjs.com, react.dev, etc.)
        - Caching 7 jours
        - Rate limiting
        - Sandboxing
    """
```

**Workflow Web Search → Standard :**
```
1. DevAgent erreur inconnue → web_search
2. Trouve solution StackOverflow → résout problème
3. Log: web_search_success (URL, query, solution)
4. LearnerAgent analyse logs
5. SI URL utilisée 3x avec succès:
   → Propose nouveau standard RAG (distillation connaissance)
6. Validation humaine
7. Standard ajouté Qdrant
8. Prochains agents trouvent solution dans RAG (pas web)
```

**LearnerAgent Mode Actif :**
```yaml
Conditions activation:
  - Validation shadow >70% Sprint 4
  - Architecture stable
  - ≥3 projets production
  - Schéma Qdrant validé

Capacités actives:
  - Upsert factory_standards
  - Versioning automatique
  - Monitoring qualité
  - Propose merges duplicates
  - Propose standards web_search

Rappel implémentation:
  - Conserver LearnerActivity dédiée comme point d'entrée unique
  - Si LLM indisponible: fallback automatique en mode déterministe
  - Interdire upsert auto sans état APPROVED (human review)
```

---

### **SPRINT 6 -- Frontend Pro + Dashboard Gouvernance Standards**

| Dimension | Détail |
|-----------|--------|
| **Objectif** | UI pro + tests E2E + dashboard gouvernance standards |
| **Agents** | UIPlaywrightAgent + EvaluatorAgent + Dashboard Standards |
| **Livrable** | Interface shadcn/ui + Playwright 100% + dashboard gouvernance opérationnel |
| **Signal mesurable** | Tests 100% + Lighthouse >90 + dashboard 3+ alerts gérées |

**✅ Nouveau v1.5 — DASHBOARD GOUVERNANCE STANDARDS :**

```
┌─────────────────────────────────────────────────────────┐
│ Standards Governance Dashboard                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ 🔴 Alerts (3)                                           │
│   • Next.js 15 released → 2 standards outdated          │
│   • Conflict: Jest config (2 standards contradictoires) │
│   • Low confidence: Clerk v5 standard (<0.5)            │
│                                                          │
│ 📊 Statistics                                           │
│   • 85 active standards                                 │
│   • 12 flagged for review                               │
│   • 0.87 avg confidence                                 │
│   • 5 pending updates                                   │
│                                                          │
│ 📝 Recent Changes (Auto + Manual)                       │
│   • [AUTO] Merged duplicate middleware standards        │
│   • [MANUAL] Updated Prisma 7 standard (approved)       │
│   • [AUTO] Flagged Next.js 14→15 (needs approval)      │
│                                                          │
│ 🤖 LearnerAgent Suggestions (8)                        │
│   ✓ Merge duplicate middleware stds (APPROVED)         │
│   ⚠ Update Next.js 14→15 (PENDING)                     │
│   ℹ Add React 19 compatibility std (PENDING)           │
│   ✓ Standardize web_search solution X (APPROVED)       │
│                                                          │
│ 📈 Trends (Last 30 Days)                               │
│   • Standards added: +12 (8 auto, 4 manual)            │
│   • Standards deprecated: 3                             │
│   • Avg confidence: 0.87 (+0.05)                        │
│   • Conflicts auto-resolved: 5                          │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Actions Dashboard :**
- **1-clic approval** suggestions LearnerAgent
- **Rollback** si standard génère regression
- **Manual override** decisions auto
- **Version history** chaque standard
- **Search/filter** standards par category, confidence, age

**Notifications :**
```yaml
Hebdomadaire:
  - StandardsMaintenanceWorkflow rapport
  - X standards flagged
  - Y auto-merges effectués
  - Z approvals pending

Immédiate (critique):
  - Breaking change détecté (version majeure)
  - Conflit haute sévérité (2 HIGH priority contradictoires)
  - Confidence critical (<0.3)
```

---

### **SPRINT 7 -- Meta-Learning + Versioning Standards**

| Dimension | Détail |
|-----------|--------|
| **Objectif** | Auto-amélioration Evaluator + versioning standards automatique |
| **Agents** | LearnerAgent + EvaluatorAgent (auto-amélioration) + Superviseur |
| **Livrable** | Evaluator auto-optimisé + versioning standards opérationnel + rollback validé |
| **Signal mesurable** | Intervention -20% vs baseline mobile + versioning 5+ standards + 1 rollback testé |

**Versioning Standards Automatique :**
```python
# Exemple évolution standard
{
    "id": "std_nextjs_version",
    "version": "1.0",
    "text": "Next.js 14.2.3+ requis",
    "created_at": "2026-02-17",
    "deprecated": False
}

# StandardsMaintenanceWorkflow détecte Next.js 15
# Crée nouvelle version automatiquement

{
    "id": "std_nextjs_version",
    "version": "2.0",
    "text": "Next.js 15.0.0+ requis pour nouveaux projets. 14.2.3+ legacy supporté.",
    "created_at": "2026-04-15",
    "deprecates": ["std_nextjs_version@1.0"],
    "breaking_change": True,
    "requires_approval": True  # humain doit approuver
}

# Rollback possible si problème
# Dashboard permet revenir à v1.0 en 1 clic
```

**Meta-Learning :**
```yaml
EvaluatorAgent:
  - Analyse patterns LearnerAgent suggestions
  - S'améliore basé sur validations humaines
  - Versioning prompts obligatoire (v1, v2, v3)
  - Rollback si drift >20%

Versioning Prompts:
  - prompts/evaluator_v1.0.md
  - prompts/evaluator_v2.0.md
  - Historique gardé
  - Comparaison A/B possible
```

---

### **SPRINT 8 -- Scalabilité Multi-Clients + Support Multi-Stack (Début)**

| Dimension | Détail |
|-----------|--------|
| **Objectif** | Multi-clients + début généralisation tech stacks |
| **Agents** | LearnerAgent + Superviseur + StandardsMaintenanceAgent |
| **Livrable** | 3 collections clients + héritage global + POC multi-stack |
| **Signal mesurable** | 3 collections + <50% duplication + POC Vue.js/Supabase validé |

**✅ Nouveau v1.5 — SUPPORT MULTI-STACK (DÉBUT) :**

```yaml
Sprint 8 - POC Stack Alternative:
  Stack actuelle: Next.js + Clerk + Prisma
  Stack test: Vue.js + Supabase + Drizzle
  
  Objectif:
    - Valider généralisation architecture
    - Identifier couplages stack-specific
    - Estimer effort abstraction
    - Décider roadmap multi-stack

Sprint 9 - Multi-stack Full:
  SI POC Sprint 8 réussi:
    - Abstraction agents stack-agnostic
    - Standards Qdrant par stack
    - Sélection stack dynamique user input
  
  SI POC échoue:
    - Reporter Sprint 10+
    - Focus qualité stack unique
```

**Critères Succès POC Multi-Stack :**
- 1 projet Vue.js/Supabase généré
- Build réussit
- Tests passent
- <40% modification code agents
- Standards séparés collection_vue_stack

---

### **SPRINT 9 -- Production Ready + Multi-Stack Full (SI POC Sprint 8 OK)**

| Dimension | Détail |
|-----------|--------|
| **Objectif** | Capacité industrielle + multi-stack opérationnel OU focus qualité stack unique |
| **Agents** | Tous agents + Superviseur Central v1.0 |
| **Livrable** | Tests charge 50 projets + 10-50 projets réels + multi-stack OU stack unique excellence |
| **Signal mesurable** | Capacité 50 projets + intervention -50% + uptime >99.5% + MTTR <2h |

**Tests Charge :**
```yaml
Infrastructure:
  - 50 projets parallèles (mix Next.js + Vue.js si multi-stack)
  - Monitoring: latence, mémoire, CPU
  - Seuil: dégradation <30% à 40 projets

Validation:
  - Tous projets complétés
  - Performance maintenue
  - 0 crash système
  - Standards gouvernance fonctionne sous charge
```

**Métriques Finales :**
```yaml
Projets réels: 10-50 déployés
Baseline finale: moyenne mobile projets réels

Objectifs:
  - Intervention: -50% vs baseline initiale Sprint 4
  - Evaluator: amélioration >+5pts
  - Standards auto-générés: >30
  - Standards auto-deprecated: >5
  - Web search → standard conversions: >3
  - Uptime: >99.5%
  - MTTR: <2h
```

---

## 📊 CRITÈRES DE RÉVISION v1.5

| Décision | Critère déclencheur | Action |
|----------|---------------------|--------|
| Défense 2 niveaux | Patches >5/projet 3 sprints | Renforcement standards RAG prioritaire |
| Workflow sémantique | Confusion métriques utilisateurs | Clarification contrats Output |
| Standards obsolescence | >10 standards confidence <0.5 | Maintenance manuelle forcée |
| Web search abuse | >30% solutions via web (pas RAG) | Audit qualité standards, amélioration RAG |
| LearnerAgent qualité | Standards générés <60% pertinence | Désactivation, amélioration prompts |
| Multi-stack POC | Échec build Vue.js Sprint 8 | Report multi-stack Sprint 10+ |
| Dashboard adoption | <30% alerts traitées 2 semaines | Formation utilisateur, UX amélioration |
| Versioning conflicts | >5 rollbacks/mois | Audit processus approbation |

---

## 🎯 JALONS CLÉS v1.5

| Date cible | Livrable | Validation |
|------------|----------|------------|
| **17 Fév 2026** | Sprint 2 terminé | Phase 1 corrections + défense 2 niveaux |
| **24 Fév 2026** | Sprint 3 terminé | Workflow sémantique + standards gouvernance + get_latest_version |
| **Mars 2026** | Sprint 4 terminé | **Gate décisionnel** + baseline mobile + LearnerAgent validation |
| **Avril 2026** | Sprints 5-6 terminés | Maintenance auto + web search + dashboard gouvernance |
| **Mai 2026** | Sprints 7-8 terminés | Meta-learning + versioning + POC multi-stack |
| **15 Mai 2026** | Sprint 9 terminé | **Démo usine autonome** (50 projets + multi-stack SI POC OK) |

---

## ✅ DEFINITION OF DONE v1.5

**Capacités techniques validées :**
- [x] Phase 1 corrections appliquées (17 Fév 2026)
- [x] Défense 2 niveaux opérationnelle (prévention + garde-fou)
- [x] Docker healthchecks (Qdrant, Temporal, PostgreSQL)
- [ ] Workflow sémantique (workflow_status vs build_status)
- [ ] Standards metadata gouvernance (version, confidence, dependencies)
- [ ] get_latest_version tool opérationnel
- [ ] Standards minimum critiques (5 catégories)
- [ ] LearnerAgent actif avec upsert Qdrant
- [ ] StandardsMaintenanceAgent hebdomadaire
- [ ] Web search pour agents opérationnel
- [ ] Dashboard gouvernance standards
- [ ] Versioning standards automatique
- [ ] Meta-learning avec rollback validé
- [ ] POC multi-stack (Vue.js/Supabase)
- [ ] Tests charge 50 projets
- [ ] 10-50 projets réels déployés
- [ ] Intervention -50% vs baseline initiale
- [ ] >30 standards auto-générés
- [ ] >3 web search → standard conversions
- [ ] Uptime >99.5%

---

## 🔄 CHANGEMENTS v1.4 → v1.5

| ID | Type | Description | Date |
|----|------|-------------|------|
| **#5** | Corrections | Phase 1 Sprint 2 (prompts, patches, métriques, Docker) | 17 Fév 2026 |
| **#6** | Architecture | Défense 2 niveaux (prévention + garde-fou observable) | 17 Fév 2026 |
| **#7** | Workflow | Sémantique clarifiée (workflow_status vs build_status) | Sprint 3 |
| **#8** | Standards | Metadata gouvernance (version, confidence, dependencies) | Sprint 3 |
| **#9** | Tools | get_latest_version + web_search agents | Sprint 3-5 |
| **#10** | Maintenance | StandardsMaintenanceAgent hebdomadaire | Sprint 5 |
| **#11** | Dashboard | Gouvernance standards (alerts, approval, versioning) | Sprint 6 |
| **#12** | Multi-stack | POC Vue.js/Supabase + roadmap conditionnelle | Sprint 8-9 |

**Impacts :**
- Sprint 2 : Phase 1 terminée (17 Fév)
- Sprint 3 : +1.5 jours (workflow sémantique + standards metadata)
- Sprint 5 : +2 jours (maintenance agent + web search)
- Sprint 6 : +2 jours (dashboard gouvernance)
- Sprint 8 : +2 jours (POC multi-stack)

**Total délai ajouté :** ~7.5 jours sur Sprint 3-8

---

## 🏗️ ARCHITECTURE DÉFENSE 2 NIVEAUX (Nouveau v1.5)

**Principe Fondamental :**
```
Erreurs inévitables → Observabilité → Apprentissage → Amélioration
```

**Niveau 1 — Prévention (RAG/Prompt) :**
```yaml
Objectif: Agent génère code correct dès le départ

Mécanismes:
  - Standards Qdrant enrichis (mots-clés multiples)
  - Retrieval k=5 (augmenté de 2)
  - Prompts chargés dynamiquement
  - Architecture Layered (Code → Prompt → RAG)

Validation:
  - Agent consulte RAG AVANT génération
  - Standard pertinent récupéré (top-k)
  - Code généré conforme standard
```

**Niveau 2 — Garde-fou Observable (Tool) :**
```yaml
Objectif: SI agent génère erreur quand même → corriger + apprendre

Mécanismes:
  - Sanitize runtime (ex: package.json)
  - Validation (ex: noms packages npm)
  - Correction automatique
  - Logging tool_patch_applied

Apprentissage:
  - LearnerAgent analyse patches
  - Détecte patterns récurrents
  - Propose renforcement standard RAG
  - Boucle ferme: patch → standard → prévention
```

**Exemple Concret — shadcn/ui :**
```
AVANT Défense 2 Niveaux:
1. Agent génère package.json avec "shadcn/ui"
2. npm install échoue (EINVALIDPACKAGENAME)
3. Workflow échoue
4. Pas d'apprentissage

APRÈS Défense 2 Niveaux:
1. Niveau 1: Agent consulte RAG, voit standard "INTERDIT shadcn/ui"
2. SI agent génère quand même (RAG k insuffisant):
   → Niveau 2: Tool sanitize détecte + supprime + logue patch
3. npm install réussit
4. LearnerAgent voit patch récurrent
5. Propose renforcement standard RAG
6. Prochains runs: Niveau 1 fonctionne (prévention)
```

---

## 📊 COHÉRENCE ESTIMÉE v1.5

| Critère | v1.4 | v1.5 (estimé) |
|---------|------|---------------|
| Agents identifiés | 100% | 100% |
| Décisions matérialisées | 100% | 100% |
| Signaux mesurables | 100% | 100% |
| Gain autonomie net | 100% | 100% |
| Réversibilité validée | 100% | 100% |
| Gouvernance standards | 0% | 90% |
| Défense erreurs | 60% | 95% |
| **Cohérence globale** | **~95%** | **~97%** |

---

## 🔐 GOUVERNANCE STANDARDS (Nouveau v1.5)

**Workflow Type — Mise à Jour Standard :**
```
1. Détection
   StandardsMaintenanceAgent flag standard obsolète
   ↓
2. Analyse
   LearnerAgent analyse impact:
   - Combien runs utilisent standard?
   - Quel taux succès?
   - Standards dépendants?
   ↓
3. Proposition
   LearnerAgent propose:
   - Nouvelle version standard
   - Breaking change? (nécessite approval)
   ↓
4. Validation
   Dashboard affiche proposition
   ↓
   SI confidence >0.9 ET impact faible:
     → Auto-approve
   SINON:
     → Approval humain requis
   ↓
5. Application
   Nouveau standard déployé Qdrant
   Ancien déprécié (pas supprimé)
   Version history conservée
   ↓
6. Migration Progressive
   Nouveaux runs utilisent v2
   Anciens projets restent v1 (si compatible)
   Monitoring qualité génération
   ↓
7. Rollback (SI Problème)
   Dashboard → rollback v1 en 1 clic
   LearnerAgent analyse cause échec v2
```

**Validation Qualité Standards :**
```yaml
Chaque standard utilisé run:
  - Success run? → confidence += 0.05
  - Échec run contredit standard? → confidence -= 0.2
  - Patch appliqué malgré standard? → flag insuffisant

Standards flaggés:
  - confidence <0.5: review humain
  - >5 patches même type: renforcement auto-proposé
  - Non utilisé 90 jours: dépréciation suggérée
```

---

**🔒 Roadmap v1.5 FINALE -- Sprint 2 Rétrospective Intégrée -- Gouvernance Standards Complète -- Défense 2 Niveaux Architecturée -- Cohérence 97% -- Exécution Continue**
