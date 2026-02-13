# SUPERVISEUR CENTRAL - DRAFT v0
## Software Agent Factory — Document de Référence Orchestration

⚠️ STATUT: PROVISOIRE
⚠️ REVIEW_MANDATORY: Sprint 4
⚠️ NO_OPTIMIZATION: Interdite avant validation empirique
⚠️ NO_HARD_CONTRACTS: Interfaces flexibles uniquement

---

## Table des Matières

1. [Rôle et Vision](#1-rôle-et-vision)
2. [Périmètre Sprint 1-3](#2-périmètre-sprint-1-3)
3. [Ce qui est Autorisé](#3-ce-qui-est-autorisé)
4. [Ce qui est Interdit](#4-ce-qui-est-interdit)
5. [Architecture Agents](#5-architecture-agents)
6. [Routing Logic](#6-routing-logic)
7. [Flux de Données](#7-flux-de-données)
8. [Métriques Observées](#8-métriques-observées)
9. [Patterns Identifiés](#9-patterns-identifiés)
10. [Décisions Différées](#10-décisions-différées)
11. [Guide d'Utilisation Sprint 1-3](#11-guide-dutilisation-sprint-1-3)
12. [Critères de Finalisation v1.0](#12-critères-de-finalisation-v10)
13. [Contrats Interface](#13-contrats-interface)
14. [Gestion des Erreurs](#14-gestion-des-erreurs)
15. [Escalade et Alertes](#15-escalade-et-alertes)
16. [Historique des Versions](#16-historique-des-versions)

---

## 1. Rôle et Vision

Le Superviseur Central est le chef d'orchestre de la Software Agent Factory.
Son rôle est d'assurer la coordination des agents, la traçabilité des décisions,
et la collecte de métriques permettant d'améliorer continuellement le système.

### Vision Long Terme (Sprint 4+)
- Orchestration intelligente basée sur les patterns appris
- Décisions autonomes pour le routage des agents
- Optimisation dynamique des workflows selon les métriques
- Supervision proactive avec détection d'anomalies

### Vision Court Terme (Sprint 1-3 — CE DOCUMENT)
- Observation passive des workflows
- Collecte de métriques sans intervention
- Routage basique et déterministe
- Escalade simple en cas d'erreur

> ⚠️ Ce document décrit UNIQUEMENT le comportement Sprint 1-3.
> Toute optimisation ou logique autonome est INTERDITE avant le Gate Sprint 4.

---

## 2. Périmètre Sprint 1-3

Le Superviseur en mode OBSERVATEUR se limite strictement aux fonctions suivantes :

### Fonctions Actives
- Réception des événements depuis n8n via webhook
- Déclenchement du workflow Temporal approprié
- Logging de chaque transition d'état
- Collecte des métriques de performance
- Escalade des erreurs critiques vers l'opérateur humain

### Fonctions Désactivées (activation post Sprint 4)
- Optimisation automatique des timeouts
- Réorganisation dynamique des étapes
- Décisions de retry intelligentes
- Sélection automatique du modèle LLM
- Personnalisation des prompts en runtime

---

## 3. Ce qui est Autorisé

### Orchestration Observationnelle
```yaml
Autorisé:
  logging:
    - Timestamp de début/fin de chaque activity
    - Input/Output summarization (pas le contenu complet)
    - Statut de chaque étape (SUCCESS/FAILURE/RETRY)
    - Nombre de retries effectués
    - Durée en secondes de chaque activity

  routing:
    - Routage statique selon la configuration LangGraph
    - Sélection fusion/split selon langgraph_config.yaml
    - Transmission des résultats entre activities

  escalade:
    - Log de l'erreur avec contexte complet
    - Notification webhook si configuré
    - Arrêt propre du workflow avec code d'erreur explicite
```

### Métriques Collectées
```yaml
Par run:
  - run_id: identifiant unique du workflow Temporal
  - project_name: nom du projet traité
  - workflow_type: SaaSFactory | TodoPilot
  - start_timestamp: ISO 8601
  - end_timestamp: ISO 8601
  - total_duration_seconds: float
  - status: SUCCESS | FAILURE | PARTIAL

Par activity:
  - activity_name: architect | dev_test | qa | github
  - start_timestamp: ISO 8601
  - duration_seconds: float
  - attempts: integer (retries inclus)
  - status: SUCCESS | FAILURE
  - error_code: string | null
```

---

## 4. Ce qui est Interdit

### Logique Métier Complexe
Le Superviseur ne doit PAS :
- Analyser le contenu des spécifications générées
- Modifier les prompts envoyés aux agents
- Décider de relancer un agent avec des paramètres différents
- Interpréter les erreurs pour prendre des décisions correctives
- Implémenter des règles métier (ex: "si le build échoue, essaie une autre version")

### Optimisations Prématurées
Interdictions explicites jusqu'au Gate Sprint 4 :
```
❌ Modifier dynamiquement les timeouts Temporal
❌ Bypasser un agent si son output est "suffisant"
❌ Paralléliser des étapes sans validation empirique
❌ Implémenter un cache des outputs agents
❌ Prendre une décision architecturale (fusion vs split)
❌ Écrire dans Qdrant factory_standards (réservé LearnerAgent)
```

### Couplage Fort
```
❌ Accès direct aux internals des agents
❌ Partage d'état mutable entre agents
❌ Dépendances circulaires entre composants
❌ Contrats figés avant validation Sprint 4
```

---

## 5. Architecture Agents

### Tableau de Référence

| Agent | ID | Rôle | Mode Sprint 1-3 | Contrat | Timeout |
|-------|----|------|-----------------|---------|---------|
| Architecte | `architect_agent` | Génération specs + diagrammes Mermaid | Actif | `architect_agent_contract.json` | 300s |
| DevTest | `dev_test_agent` | Code full-stack + Tests unitaires (fusionné) | Actif (fusion) | `dev_agent_contract.json` + `test_agent_contract.json` | 2700s |
| QA | `qa_agent` | Tests E2E Playwright | Actif | `qa_agent_contract.json` | 600s |
| GitHub | `github_agent` | Création repo + PR | Actif | `github_agent_contract.json` | 600s |
| Learner | `learner_agent` | Auto-apprentissage standards | **Shadow** (log only) | TBD Sprint 2 | 300s |
| Superviseur | `superviseur` | Orchestration + métriques | **Observateur** | Ce document | N/A |

### Notes Architecture

**DevTestAgent — Mode Fusion**
Le DevTestAgent est physiquement un seul déploiement mais assume deux responsabilités :
- Responsabilité Dev : génération du code full-stack Next.js
- Responsabilité Test : génération des tests unitaires Jest

La fusion est maintenue jusqu'au Gate Sprint 4. Si le nombre d'agents dépasse 8
ou si la complexité orchestration dépasse 20%, le switch split s'active via
`config/langgraph_config.yaml` sans refactoring du code métier.

**LearnerAgent — Mode Shadow Sprint 2-3**
Le LearnerAgent observe les runs mais n'écrit PAS dans Qdrant.
Ses suggestions sont loggées dans `logs/shadow/learner_shadow_log.json`.
L'activation mode actif est conditionnée à une validation >70% Sprint 4.

---

## 6. Routing Logic

### Schéma de Routage (ASCII)

```
                    ┌─────────────────┐
                    │   HUMAIN        │
                    │  (n8n webhook)  │
                    └────────┬────────┘
                             │ POST /start-saas
                             │ { phrase, project_name }
                             ▼
                    ┌─────────────────┐
                    │  Flask API      │
                    │  :5000          │
                    │  /start-saas   │
                    └────────┬────────┘
                             │ job_queue.put()
                             ▼
                    ┌─────────────────┐
                    │  Temporal       │
                    │  workflow_      │
                    │  dispatcher     │
                    └────────┬────────┘
                             │ client.start_workflow()
                             ▼
              ┌──────────────────────────────┐
              │  SUPERVISEUR OBSERVATEUR     │
              │  ┌────────────────────────┐  │
              │  │ Log: workflow_start    │  │
              │  │ Métriques: start_time  │  │
              │  └────────────────────────┘  │
              └──────────────┬───────────────┘
                             │
              ┌──────────────▼───────────────┐
              │  1. architect_activity       │
              │  Timeout: 300s | Retry: 3    │
              │  Input: phrase, project_name │
              │  Output: spec, mermaid       │
              └──────────────┬───────────────┘
                             │ ✅ spec + mermaid
              ┌──────────────▼───────────────┐
              │  2. dev_test_activity        │
              │  Timeout: 2700s | Retry: 3   │
              │  Input: spec, mermaid, name  │
              │  Output: combined_files      │
              └──────────────┬───────────────┘
                             │ ✅ fichiers générés
              ┌──────────────▼───────────────┐
              │  3. qa_activity              │
              │  Timeout: 600s | Retry: 3    │
              │  Input: specification, name  │
              │  Output: e2e_tests (dict)    │
              └──────────────┬───────────────┘
                             │ ✅ tests E2E
              ┌──────────────▼───────────────┐
              │  4. github_activity          │
              │  Timeout: 600s | Retry: 3    │
              │  Input: files, project_name  │
              │  Output: {pr_url, repo_url}  │
              └──────────────┬───────────────┘
                             │ ✅ PR créée
              ┌──────────────▼───────────────┐
              │  SUPERVISEUR OBSERVATEUR     │
              │  ┌────────────────────────┐  │
              │  │ Log: workflow_end      │  │
              │  │ Métriques: end_time    │  │
              │  │ Export: logs/metrics/  │  │
              │  └────────────────────────┘  │
              └──────────────────────────────┘
```

### Règles de Routage

```yaml
Règle 1 — Séquence stricte:
  Les activities s'exécutent en séquence. Aucune parallélisation
  avant validation empirique Sprint 4.

Règle 2 — Fail-fast:
  Si une activity échoue après max_retries, le workflow s'arrête.
  Le Superviseur log l'erreur et notifie. Pas de contournement automatique.

Règle 3 — Output propagation:
  L'output de chaque activity est validé contre son contrat JSON
  avant d'être passé à l'activity suivante.

Règle 4 — Idempotence:
  Chaque run est identifié par un ID unique Temporal.
  Les retries ne créent pas de duplicats.
```

---

## 7. Flux de Données

### Pipeline Données Sprint 1

```
INPUT (n8n)
  └─► { phrase: string, project_name: string }
        │
        ▼
ARCHITECT AGENT
  Lecture: Qdrant factory_standards (RAG k=10)
  Écriture: Aucune
  Output: { specification: markdown, mermaid_diagram: string }
        │
        ▼
DEV_TEST AGENT (fusionné)
  Lecture: Qdrant factory_standards (RAG pour versions)
  Écriture: Fichiers en mémoire (pas persistés entre steps)
  Output: { combined_files: {path: content}, success: bool, metadata: {...} }
        │
        ▼
QA AGENT
  Lecture: specification (du workflow state)
  Écriture: Aucune
  Output: { e2e_tests: {path: content} }
        │
        ▼
GITHUB AGENT
  Lecture: combined_files + e2e_tests (merged)
  Écriture: GitHub repo + branch dev + PR
  Output: { pr_url: uri, repo_url: uri }
        │
        ▼
OUTPUT FINAL
  └─► URL Pull Request GitHub
```

### Données Persistées

| Composant | Données Persistées | Format | Retention |
|-----------|-------------------|--------|-----------|
| Temporal | Workflow history | Interne | 30 jours |
| Qdrant | factory_standards | Vectoriel | Permanent |
| GitHub | Code + PR | Git | Permanent |
| Logs | Métriques runs | JSON | 90 jours |
| Shadow Log | Suggestions LearnerAgent | JSON | Sprint 2-4 |

---

## 8. Métriques Observées

### Dashboard Runs (à remplir manuellement ou via scripts/validate_contracts.py)

| Run# | Date | Projet | Architect_s | DevTest_s | QA_s | GitHub_s | Total_s | Interventions | Erreurs | Statut |
|------|------|--------|-------------|-----------|------|----------|---------|---------------|---------|--------|
| 001 | - | todo-pilot | - | - | - | - | - | 0 | 0 | PENDING |
| 002 | - | - | - | - | - | - | - | - | - | - |
| 003 | - | - | - | - | - | - | - | - | - | - |

### Métriques Cumulées (mise à jour après chaque projet)

```
Projets complétés      : 0
Interventions totales  : 0
Taux de succès         : N/A
Temps moyen total      : N/A
Temps moyen architect  : N/A
Temps moyen dev_test   : N/A
Temps moyen qa         : N/A
Temps moyen github     : N/A
```

### Baseline Mobile (activation Sprint 4)

> ⚠️ La baseline mobile (rolling average 3 projets) ne sera calculée
> qu'à partir de Sprint 4 quand 3+ projets seront disponibles.

---

## 9. Patterns Identifiés

> ⚠️ Section vide — À remplir au fil des runs Sprint 1-3.
> Format attendu : pattern observé + fréquence + impact potentiel.

### Structure de Documentation d'un Pattern

```yaml
Pattern:
  id: PATTERN_001
  sprint_detecte: 2
  run_detecte: run#003
  description: >
    Description du pattern observé...
  frequence: 3/5 runs
  impact: LOW | MEDIUM | HIGH
  action_proposee: >
    Action suggérée (LearnerAgent shadow log)
  validation_humaine: PENDING | APPROVED | REJECTED
```

### Patterns Connus (pré-remplis depuis Sprint 0.5)

```yaml
Pattern PATTERN_000:
  id: PATTERN_000
  sprint_detecte: 0.5
  description: >
    DevTestAgent fusionné produit un output cohérent couvrant
    à la fois le code source et les tests unitaires.
    L'agent résout les conflits de dépendances de manière autonome.
  frequence: 1/1 runs
  impact: LOW
  action_proposee: Continuer en mode fusion jusqu'au Gate Sprint 4
  validation_humaine: APPROVED
```

---

## 10. Décisions Différées

| ID | Décision | Raison du Report | Sprint de Révision | Données Nécessaires |
|----|----------|------------------|--------------------|---------------------|
| DEC_001 | Architecture fusion vs split | Besoin de données empiriques sur 3 projets | Sprint 4 Gate | agent_count, complexity_ratio, latency_overhead |
| DEC_002 | Finalisation Superviseur v1.0 | Attente patterns réels Sprint 1-3 | Sprint 4 | patterns observés, métriques runs |
| DEC_003 | Activation LearnerAgent mode actif | Validation suggestions shadow >70% | Sprint 4-5 | learner_shadow_log.json review |
| DEC_004 | Activation baseline mobile | Besoin de 3+ projets complétés | Sprint 4 | 3 runs complets avec métriques |
| DEC_005 | Optimisations workflow | Pas de données pour optimiser | Post Sprint 4 | patterns + baseline + interventions |
| DEC_006 | Contrats figés agents | Architecture en validation | Post Sprint 4 Gate | DEC_001 résolu |
| DEC_007 | Meta-learning EvaluatorAgent | Besoin LearnerAgent actif d'abord | Sprint 7 | DEC_003 résolu |

---

## 11. Guide d'Utilisation Sprint 1-3

### Comment Ajouter une Observation

Après chaque run, mettre à jour la section 8 :

```bash
# 1. Lancer un run
python run/worker.py &
curl -X POST http://localhost:5000/start-saas 
  -H "Content-Type: application/json" 
  -d '{"phrase": "Crée une app ToDo", "project_name": "todo-v1"}'

# 2. Observer dans Temporal UI
open http://localhost:8080

# 3. Collecter les métriques depuis les logs Temporal
# Mettre à jour la table section 8 manuellement

# 4. Si pattern identifié, ajouter en section 9
```

### Comment Logger une Intervention Humaine

```yaml
# Format d'une intervention dans les logs
intervention:
  run_id: "saas-factory-1234567890"
  timestamp: "2026-02-13T10:30:00Z"
  type: MANUAL_FIX | RETRY | CONFIG_CHANGE | ABORT
  agent_impacte: architect | dev_test | qa | github
  description: "Description courte de ce qui a nécessité intervention"
  resolution: "Comment c'a été résolu"
  preventable: true | false
  learner_note: "Ce pattern devrait être appris par LearnerAgent Sprint 2"
```

### Comment Escalader une Erreur

```
Niveau 1 — Auto (géré par Temporal):
  → Retry automatique (max 3 tentatives)
  → Log dans Temporal UI

Niveau 2 — Superviseur (log dans metrics):
  → Après 3 retries échoués
  → Enregistrement dans logs/metrics/
  → Notification optionnelle webhook

Niveau 3 — Opérateur humain:
  → Erreur critique non-récupérable
  → Workflow arrêté proprement
  → Ticket créé manuellement
```

---

## 12. Critères de Finalisation v1.0

### Checklist Gate Sprint 4

Le Superviseur passera de DRAFT à v1.0 quand tous ces critères sont remplis :

```
Architecture:
  [ ] Décision fusion/split documentée (DEC_001)
  [ ] 3+ projets complétés avec métriques
  [ ] agent_count ≤ 8 confirmé empiriquement
  [ ] complexity_ratio < 20% confirmé

Observations:
  [ ] Section 8 (Métriques) remplie pour 3 projets minimum
  [ ] Section 9 (Patterns) avec ≥ 3 patterns validés
  [ ] Toutes les décisions différées (section 10) résolues ou reportées avec justification

LearnerAgent:
  [ ] Shadow log Sprint 2-3 : ≥ 15 suggestions
  [ ] Review humain : validation > 70%
  [ ] Schema Qdrant validé sur 2+ projets

Superviseur:
  [ ] Restrictions Sprint 1-3 levées (après validation empirique)
  [ ] Optimisations autorisées documentées
  [ ] Tags DRAFT remplacés par tags v1.0
  [ ] Contrats interfaces figés si architecture stable
```

---

## 13. Contrats Interface

### Format Standard Contrat Agent

Chaque agent respecte le format défini dans `schemas/contracts/`.

Exemple d'utilisation dans le code :
```python
from scripts.validate_contracts import validate_input, validate_output

# Avant d'appeler un agent
validate_input("architect_agent", input_data)

# Après avoir reçu un output
validate_output("architect_agent", output_data)
```

### Compatibilité Contrats Sprint 1-3

| Agent | Input Contract | Output Contract | Statut |
|-------|---------------|-----------------|--------|
| architect_agent | phrase (requis), project_name (optionnel) | specification + mermaid_diagram | ✅ Validé |
| dev_agent | spec + mermaid + project_name | files + final_message + success | ✅ Validé |
| test_agent | files | tests + metadata | ✅ Validé |
| qa_agent | specification + project_name | e2e_tests (dict) | ✅ Validé |
| github_agent | files + project_name | pr_url + repo_url | ✅ Validé |
| learner_agent | TBD Sprint 2 | TBD Sprint 2 | ⏳ Shadow |

---

## 14. Gestion des Erreurs

### Codes d'Erreur Standards

```yaml
VALIDATION_ERROR:
  description: Input/Output ne respecte pas le contrat JSON Schema
  recovery: Vérifier les données avant de relancer
  escalade: Niveau 2

RAG_CONNECTION_ERROR:
  description: Impossible de se connecter à Qdrant
  recovery: Vérifier docker-compose, relancer qdrant container
  escalade: Niveau 3

LLM_ERROR:
  description: Erreur API OpenAI (rate limit, timeout, erreur modèle)
  recovery: Retry automatique avec backoff exponentiel
  escalade: Niveau 1 (auto)

MERMAID_SYNTAX_ERROR:
  description: Diagramme Mermaid invalide après 3 tentatives
  recovery: Relancer architect avec prompt différent
  escalade: Niveau 2

BUILD_ERROR:
  description: next build échoue sur le code généré
  recovery: DevTestAgent retry avec correction automatique
  escalade: Niveau 1 (auto, max 3)

GITHUB_AUTH_ERROR:
  description: GITHUB_TOKEN invalide ou expiré
  recovery: Renouveler le token dans .env
  escalade: Niveau 3

TIMEOUT_ERROR:
  description: Activity dépasse son timeout configuré
  recovery: Augmenter timeout si récurrent, sinon investiguer
  escalade: Niveau 2
```

---

## 15. Escalade et Alertes

### Configuration Alertes (Sprint 1 — Manuelle)

```yaml
alertes_sprint_1:
  mode: manuel
  
  surveiller:
    - "3 retries consécutifs sur même activity"
    - "Temps dev_test_activity > 40 minutes"
    - "0 fichiers générés par DevTestAgent"
    - "RAG score < 0.5 sur architect"
  
  actions:
    - Vérifier Temporal UI http://localhost:8080
    - Consulter logs/metrics/ pour le run concerné
    - Documenter en section 9 (Patterns) si récurrent
```

### Webhook Notification (optionnel)

```python
# config/settings.py — ajouter si souhaité
ALERT_WEBHOOK_URL = os.getenv("ALERT_WEBHOOK_URL", None)
ALERT_ON_FAILURE = True
ALERT_ON_TIMEOUT = True
```

---

## 16. Historique des Versions

| Version | Date | Sprint | Auteur | Changements |
|---------|------|--------|--------|-------------|
| v0 DRAFT | 2026-02-13 | Sprint 1 | Factory Team | Création initiale — mode observateur |
| v0.1 | TBD | Sprint 2 | Factory Team | Ajout observations runs 1-2 |
| v0.2 | TBD | Sprint 3 | Factory Team | Ajout observations runs 3+ |
| v1.0 | TBD | Sprint 4 | Factory Team | **Finalisation post Gate Sprint 4** |

---

*Document généré pour Software Agent Factory v1.4*
*Dernière mise à jour : Sprint 1*
*Prochaine révision obligatoire : Sprint 4 Gate*