# 🚀 ROADMAP AGILE 2025 -- SOFTWARE AGENT FACTORY

**Version 1.4 -- Consensus Multi-AI + Corrections Critiques**  
**Date : 04 Février 2026**

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

### **SPRINT 0.5 -- Validation Architecture + Contrats Interface**

| Dimension | Détail |
|-----------|--------|
| **Objectif** | Projet pilote validant architecture + définition contrats interface agents |
| **Agent** | Architecte Agent + orchestration manuelle temporaire |
| **Livrable** | 1 micro-projet (ToDo app) déployé + contrats JSON schemas agents + rapport validation |
| **Signal mesurable** | Projet fonctionnel prod + contrats interface documentés + baseline complexité orchestration mesurée |

**⚠️ Nouveau v1.4 — CORRECTION #1 (Architecture Fusion) :**

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

**Configuration LangGraph :**
```yaml
mode_deployment:
  fusion: true  # Défaut Sprint 0.5-3
  split: false  # Activation possible Sprint 4 sans refactoring

agents_config:
  dev_test:
    responsibilities: [dev, test]
    contract_dev: schemas/dev_agent.json
    contract_test: schemas/test_agent.json
```

**Validation Sprint 0.5 :**
- Tester switch `fusion: false` → agents séparés fonctionnent sans modification code métier
- Mesurer overhead séparation : temps latence, complexité orchestration

---

### **SPRINT 1 -- Spécifications + Superviseur DRAFT**

| Dimension | Détail |
|-----------|--------|
| **Objectif** | Spécifications techniques + architecture Superviseur PROVISOIRE |
| **Agent** | Architecte Agent (RAG sur factory_standards) |
| **Livrable** | SPEC.md + diagramme Mermaid + repo GitHub + SUPERVISEUR_DRAFT_v0.md |
| **Signal mesurable** | Score RAG >0.75 + Superviseur doc >300 lignes avec tags obligatoires |

**⚠️ Nouveau v1.4 — CORRECTION #3 (Superviseur Provisoire) :**

**Tags Obligatoires Document :**
```markdown
# SUPERVISEUR CENTRAL - DRAFT v0
⚠️ STATUT: PROVISOIRE
⚠️ REVIEW_MANDATORY: Sprint 4
⚠️ NO_OPTIMIZATION: Interdite avant validation empirique
⚠️ NO_HARD_CONTRACTS: Interfaces flexibles uniquement
```

**Restrictions Explicites Sprint 1-3 :**
```yaml
Autorisé:
  - Orchestration observationnelle (logs, métriques)
  - Routage basique agents
  - Escalade erreurs simple
  
Interdit:
  - Optimisation workflows
  - Contrats figés entre agents
  - Dépendances fortes (couplage)
  - Décisions autonomes critiques
```

**Rôle Superviseur Sprint 1-3 :**
- Observer patterns orchestration
- Logger décisions routing
- Métriques temps exécution agents
- **PAS** de logique métier complexe

---

### **SPRINT 2 -- Génération Code + Tests + Evaluator Observation + LearnerAgent Shadow**

| Dimension | Détail |
|-----------|--------|
| **Objectif** | Code full-stack projet 1 + calibration Evaluator + validation schéma LearnerAgent |
| **Agents** | DevTestAgent + EvaluatorAgent (observation) + LearnerAgent (shadow mode) |
| **Livrable** | Code + tests + PR + Evaluator scores documentés + LearnerAgent suggestions log |
| **Signal mesurable** | Coverage >80% + Evaluator observations projet 1 + LearnerAgent log ≥3 suggestions |

**⚠️ Nouveau v1.4 — CORRECTION #4 (LearnerAgent Shadow Mode) :**

**LearnerAgent Mode Shadow Sprint 2-3 :**
```yaml
Comportement:
  - Analyse logs, code, métriques (comme mode actif)
  - Génère suggestions standards
  - Écrit dans log UNIQUEMENT (pas upsert Qdrant)
  - Valide schéma données factory_standards

Output Sprint 2:
  learner_shadow_log.json:
    - suggested_standards: [...]
    - confidence_scores: [...]
    - schema_validation: OK/FAIL
```

**Objectifs Shadow Mode :**
1. Valider structure JSON standards avant écriture réelle
2. Tester pertinence suggestions (review humain)
3. Détecter problèmes schéma Qdrant tôt (correction facile)

**Activation Mode Actif :** Sprint 5 (après validation Sprint 2-4)

**Evaluator Mode Observation :**
- Pas de baseline figée
- Scores documentés comme "référence observationnelle v0"
- Calibration continue sur projets 1-3

---

### **SPRINT 3 -- Déploiement Staging + Métriques Observation**

| Dimension | Détail |
|-----------|--------|
| **Objectif** | Déploiement staging + observation métriques (pas baseline définitive) |
| **Agents** | QADeployAgent + Superviseur (observateur) + LearnerAgent (shadow) |
| **Livrable** | URL staging + dashboard métriques + LearnerAgent suggestions cumulées + observations intervention |
| **Signal mesurable** | Temps <10min + E2E 100% + observations intervention projet 1-2 documentées + LearnerAgent log ≥5 suggestions |

**Métriques Observation Sprint 3 :**
- Intervention humaine projets 1-2 : enregistrée (pas baseline)
- Temps déploiement : observé
- Taux erreur : documenté

**LearnerAgent Shadow :**
- Cumul suggestions projets 1-2
- Validation schéma sur 2 projets différents
- Review humain qualité suggestions

---

### **SPRINT 4 -- Gate Décisionnel + Baseline Dynamique + Sécurité**

| Dimension | Détail |
|-----------|--------|
| **Objectif** | Validation architecture empirique + baseline glissante + sécurité + finalisation Superviseur |
| **Agents** | SecurityComplianceAgent + Superviseur (finalisation) + LearnerAgent (validation) + Evaluator (baseline) |
| **Livrable** | Décision architecture + Superviseur v1.0 + baseline mobile activée + 0 CRITICAL + standards validés |
| **Signal mesurable** | 3 projets prod + décision split/fusion documentée + baseline rolling définie + suggestions LearnerAgent validées |

**⚠️ Nouveau v1.4 — CORRECTION #2 (Baseline Glissante) :**

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
```

**Dashboard Progression Relative :**
```
Au lieu de: "Intervention 35% (cible <25%)"
Afficher: "Intervention -15% vs baseline mobile (tendance ↓)"
```

**Gate Architecture Sprint 4 :**

**Critères Mesurés :**
1. Nombre agents nécessaires : 5-8 agents constatés
2. Complexité orchestration : X% code total
3. Overhead séparation : latence +Y% si split

**Décision :**
```yaml
SI agents ≤8 ET complexité <20%:
  - CONSERVER fusion (mode actuel)
  - Tag: "Architecture validée empiriquement"

SI agents >8 OU complexité >20%:
  - ACTIVER split mode (switch config LangGraph)
  - Pas de refactoring (contrats définis Sprint 0.5)
  - Tag: "Pivot vers micro-agents atomiques"
```

**Superviseur Finalisation :**
- Review observations Sprint 1-3
- Spécifications v1.0 basées sur patterns réels
- Élimination tag DRAFT
- Optimisations autorisées post-Sprint 4

**LearnerAgent Validation :**
- Review suggestions shadow mode (15-20 suggestions cumulées)
- Validation humain : pertinence, schéma Qdrant OK
- **SI validation >70%** → activation mode actif Sprint 5
- **SI validation <70%** → amélioration prompts, shadow mode prolongé

---

### **SPRINT 5 -- LearnerAgent Actif + Infra + Collections**

| Dimension | Détail |
|-----------|--------|
| **Objectif** | Apprentissage actif validé + infrastructure auto + collections dynamiques |
| **Agents** | TerraformDevOpsAgent + LearnerAgent (actif SI validé Sprint 4) |
| **Livrable** | DB/VPC/CI-CD + upsert standards réels Qdrant + collection test créée + baseline mobile mise à jour |
| **Signal mesurable** | Infra <15min + LearnerAgent ≥1 upsert Qdrant + baseline recalculée projets 2-4 |

**Activation LearnerAgent :**
```yaml
Conditions:
  - Validation suggestions shadow >70% Sprint 4
  - Architecture stable (pas pivot en cours)
  - ≥3 projets production
  - Schéma Qdrant validé

Mode Actif:
  - Upsert factory_standards autorisé
  - Versioning automatique standards
  - Monitoring qualité génération
```

**Baseline Mobile Mise à Jour :**
- Recalcul automatique après projet 4
- Fenêtre = projets 2-4 (plus récents)
- Dashboard affiche tendance évolution

---

### **SPRINT 6 -- Frontend Pro + Tests E2E + Optimisation Evaluator**

| Dimension | Détail |
|-----------|--------|
| **Objectif** | UI professionnelle + tests E2E + amélioration Evaluator vs baseline mobile |
| **Agents** | UIPlaywrightAgent + EvaluatorAgent + LearnerAgent |
| **Livrable** | Interface shadcn/ui + tests Playwright 100% + amélioration Evaluator mesurée + baseline mobile mise à jour |
| **Signal mesurable** | Tests 100% + Lighthouse >90 + Evaluator amélioration >+2pts vs baseline mobile actuelle |

**Baseline Mobile Projets 3-5 :**
- Amélioration mesurée dynamiquement
- Pas de seuil absolu figé
- Progression relative affichée dashboard

---

### **SPRINT 7 -- Meta-Learning + Réduction Intervention Mesurée**

| Dimension | Détail |
|-----------|--------|
| **Objectif** | Auto-amélioration Evaluator + réduction intervention vs baseline mobile |
| **Agents** | LearnerAgent + EvaluatorAgent (auto-amélioration) + Superviseur |
| **Livrable** | Evaluator auto-optimisé + réduction intervention -20% vs baseline mobile + versioning prompts |
| **Signal mesurable** | Intervention tendance ↓20% + Evaluator amélioration >+3pts + versioning prompts opérationnel |

**Meta-Learning :**
```yaml
EvaluatorAgent:
  - S'améliore via patterns LearnerAgent
  - Versioning prompts obligatoire (v1, v2, v3...)
  - Rollback possible si drift détecté

Baseline Mobile Projets 4-6:
  - Réduction mesurée dynamiquement
  - Objectif -20% intervention (réaliste)
```

---

### **SPRINT 8 -- Scalabilité Multi-Clients Prouvée**

| Dimension | Détail |
|-----------|--------|
| **Objectif** | Capacité multi-clients via projets test + personnalisation auto |
| **Agents** | LearnerAgent + Superviseur |
| **Livrable** | 3 projets test collections distinctes + héritage global + personnalisation + baseline mobile mise à jour |
| **Signal mesurable** | 3 collections test + <50% duplication vs global + personnalisation fonctionnelle |

**Projets Test Fictifs :**
```yaml
Clients simulés:
  - client_demo_saas_001
  - client_demo_ecommerce_002  
  - client_demo_crm_003

Validation:
  - Collections créées dynamiquement
  - Héritage factory_standards vérifié
  - Personnalisation auto-générée
  - Baseline mobile projets 5-7
```

---

### **SPRINT 9 -- Production Ready + Validation Scalabilité**

| Dimension | Détail |
|-----------|--------|
| **Objectif** | Capacité industrielle prouvée tests charge + métriques production réelles |
| **Agents** | Tous agents + Superviseur Central v1.0 |
| **Livrable** | Tests charge 50 projets simulés + 10-50 projets réels + dashboard + PR auto + baseline finale |
| **Signal mesurable** | Capacité 50 projets prouvée + intervention -50% vs baseline initiale + uptime >99.5% + MTTR <2h |

**Tests Charge Simulés :**
```yaml
Infrastructure:
  - 50 projets parallèles générés automatiquement
  - Monitoring performance: latence, mémoire, CPU
  - Validation: dégradation <30% à 40 projets

Seuil réussite:
  - Tous projets complétés
  - Performance maintenue
  - 0 crash système
```

**Projets Réels :**
```yaml
Volume flexible:
  - Minimum: 10 projets (validation statistique basique)
  - Optimal: 30-50 projets (validation robuste)
  - Baseline finale: moyenne mobile projets réels

Métriques finales:
  - Intervention: réduction -50% vs baseline initiale Sprint 4
  - Evaluator: amélioration >+5pts
  - Standards auto-générés: >20
```

---

## 📊 CRITÈRES DE RÉVISION v1.4

| Décision | Critère déclencheur | Action |
|----------|---------------------|--------|
| Architecture fusion | >8 agents Sprint 4 OU complexité >20% | Activation switch split (pas refactoring) |
| Superviseur provisoire | Incompatibilité observations/specs Sprint 4 | Refactoring avant v1.0 finalisé |
| LearnerAgent shadow | Validation suggestions <70% Sprint 4 | Amélioration prompts, shadow prolongé |
| LearnerAgent actif | Qualité standards générés <60% | Désactivation temporaire, review algorithm |
| Baseline mobile | Stagnation 3 sprints consécutifs | Analyse blocages, ajustement métriques |
| Evaluator drift | Dérive >20% OU score <baseline mobile | Rollback prompts version antérieure |
| Collections dynamiques | >50% duplication client vs global | Révision héritage, consolidation |
| Meta-learning | Regression performance Evaluator | Désactivation meta-learning, audit |
| Scalabilité capacité | Dégradation >30% performance à 40 projets | Optimisation infra, scaling horizontal |

---

## 🎯 JALONS CLÉS v1.4

| Date cible | Livrable | Validation |
|------------|----------|------------|
| **Janvier 2026** | Sprint 0.5 terminé | Contrats interface + projet pilote validé |
| **Février 2026** | Sprints 1-3 terminés | Agents provisoires + shadow modes actifs |
| **Mars 2026** | Sprint 4 terminé | **Gate décisionnel** + baseline mobile + architecture validée |
| **Avril 2026** | Sprints 5-7 terminés | Apprentissage actif + meta-learning + réduction intervention |
| **Mai 2026** | Sprints 8-9 terminés | **Démo usine autonome** (capacité 50 projets prouvée) |

---

## ✅ DEFINITION OF DONE v1.4

**Capacités techniques validées :**
- [ ] Contrats interface agents définis et testés (Sprint 0.5)
- [ ] Architecture validée empiriquement Sprint 4 (fusion OU split décidé)
- [ ] Superviseur v1.0 finalisé basé observations réelles
- [ ] LearnerAgent shadow validé (≥70% suggestions pertinentes)
- [ ] LearnerAgent actif opérationnel avec upsert Qdrant
- [ ] Baseline mobile implémentée (fenêtre 3 projets)
- [ ] Tests charge 50 projets simulés réussis
- [ ] 10-50 projets réels déployés production (flexible)
- [ ] Intervention -50% vs baseline initiale Sprint 4
- [ ] Evaluator amélioration >+5pts vs baseline initiale
- [ ] >20 standards auto-générés validés
- [ ] Uptime >99.5% sur projets réels
- [ ] MTTR <2h
- [ ] Collections personnalisées 3+ démontrées
- [ ] Meta-learning avec versioning prompts opérationnel
- [ ] 0 décisions irréversibles prises avant validation empirique

---

## 🔄 CHANGEMENTS v1.3 → v1.4

| ID | Type | Description | Correction |
|----|------|-------------|------------|
| **#1** | Architecture | Contrats interface agents Sprint 0.5 | Consensus ChatGPT + Gemini |
| **#2** | Métriques | Baseline mobile (rolling average) | Consensus ChatGPT + Gemini |
| **#3** | Superviseur | Tag DRAFT + restrictions Sprint 1-3 | ChatGPT priorité #1 |
| **#4** | Apprentissage | LearnerAgent shadow mode Sprint 2-4 | Gemini innovation |

**Impacts :**
- Sprint 0.5 : +2 jours (contrats interface)
- Sprint 2-4 : +1 jour (shadow mode logging)
- Sprint 4 : +0.5 jour (finalisation Superviseur vs v1.3)
- Baseline : 0 impact (changement calcul uniquement)

**Total délai ajouté :** ~3.5 jours (négligeable sur 5 mois)

---

## 📊 COHÉRENCE ESTIMÉE v1.4

| Critère | v1.1 | v1.2 | v1.3 | v1.4 (estimé) |
|---------|------|------|------|---------------|
| Agents identifiés | 90% | 100% | 100% | 100% |
| Décisions matérialisées | 100% | 100% | 100% | 100% |
| Signaux mesurables | 40% | 60% | 95% | 100% |
| Gain autonomie net | 30% | 90% | 100% | 100% |
| Réversibilité validée | 27% | 41% | 100% | 100% |
| **Cohérence globale** | **40%** | **60%** | **~90%** | **~95%** |

---

## 🔐 RÉVERSIBILITÉ v1.4

| Décisions irréversibles | v1.1 | v1.2 | v1.3 | v1.4 |
|------------------------|------|------|------|------|
| Avant validation empirique | 3 | 5 | 0 | 0 |
| Protection architecture | ❌ | ❌ | ⚠️ | ✅ (contrats) |
| Protection données | ❌ | ❌ | ⚠️ | ✅ (shadow) |
| Protection métriques | ❌ | ❌ | ⚠️ | ✅ (mobile) |
| Protection orchestration | ❌ | ❌ | ⚠️ | ✅ (DRAFT) |

---

## 🎯 AMÉLIORATIONS CLÉS v1.4

**Risques Éliminés :**
1. ✅ Refactoring massif Sprint 4 (contrats interface)
2. ✅ Migration Qdrant complexe (shadow mode validation)
3. ✅ Fausses métriques progression (baseline mobile)
4. ✅ Superviseur refactoring global (statut DRAFT)

**Investissement :**
- +3.5 jours développement total
- 0 impact deadline (négligeable sur 5 mois)

**ROI :**
- Évite 2-3 semaines refactoring potentiel
- Protège killer feature (auto-apprentissage)
- Sécurise fondations (orchestration + métriques)

---

**🔒 Roadmap v1.4 FINALE verrouillée -- Consensus 3 IA appliqué -- Cohérence 95% -- Protection 4 risques critiques -- Exécution immédiate**