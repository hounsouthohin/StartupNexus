# Cartographie Structurelle — Software Agent Factory
*Version 1.0 — 18 Avril 2026*

---

## Vision en une phrase

Une usine logicielle autonome qui transforme un **brief textuel** ("App de gestion de tâches avec Clerk")
en une **application Next.js complète, buildée et validée**, sans intervention humaine.

---

## Vue d'ensemble — Le flux en 5 étapes

```
HUMAIN
  │
  │  brief (description + modèles Prisma + pages + routes)
  ▼
┌─────────────────────────────────────────────────────────────┐
│  TEMPORAL WORKFLOW — TodoPilotWorkflow                       │
│                                                             │
│  [1] architect_activity  →  [2] dev_test_activity           │
│                              (génère + builde l'app)        │
│                          →  [3] qa_activity        (désactivé sanity mode)
│                          →  [4] github_activity    (désactivé sanity mode)
│                          →  [5] learner_activity   (désactivé sanity mode)
└─────────────────────────────────────────────────────────────┘
  │
  ▼
Application Next.js générée dans /app/generated-projects/<nom-projet>/
```

---

## Infrastructure Docker — 6 services

```
docker-compose.yml
│
├── temporal             → Orchestrateur de workflows (port 7233)
│                          Gère la durabilité, les retries, le monitoring
│
├── temporal-ui          → Dashboard web Temporal (port 8080)
│                          Visualiser l'état des workflows en temps réel
│
├── elasticsearch        → Backend stockage Temporal (port 9200)
│
├── postgresql           → Base de données des projets générés (port 5432)
│                          Prisma des apps générées pointe ici
│
├── qdrant               → Base vectorielle RAG (port 6333)
│                          Stocke 84 standards de code (ZONE_1 → ZONE_18)
│
└── factory-worker       → Cerveau de la factory (port 5000 Flask)
                           Contient tout le code Python + Node.js
                           Monte le volume /app/generated-projects/
```

**Point d'entrée humain :**
```bash
docker compose exec factory-worker python scripts/run_batch.py \
  --batch-size 4 --briefs scripts/test_4_briefs.json --sanity-mode
```

---

## Couche 1 — Temporal Workflow

**Fichier :** `workflows/todo_pilot_workflow.py`

```
TodoPilotWorkflow
│
├── Input  : project_name + brief{} + stack_id="nextjs-clerk-prisma"
│
├── Génère : run_id (UUID unique par run, propagé à tous les agents)
│
├── Appelle séquentiellement :
│   1. architect_activity   (queue: factory-task-queue)
│   2. dev_test_activity     (queue: factory-task-queue)
│   3. [qa / github / learner — désactivés en sanity-mode]
│
└── Output : workflow_status=COMPLETED + build_status=SUCCESS/FAILURE
```

**Rôle Temporal :** si un step plante (timeout réseau, crash LLM), Temporal
le relance automatiquement sans perdre l'état du workflow.

---

## Couche 2 — Architect Activity

**Fichier :** `agents/architect.py`

```
Brief utilisateur
      │
      ▼
[brief_normalizer]    gpt-4o-mini, ZÉRO RAG
      │               Transforme tout brief en brief structuré normalisé
      ▼
[retrieval_node]      Qdrant (k=10, filtre stack=nextjs-clerk-prisma + status=active)
      │               Récupère les standards de code pertinents
      ▼
[planner_node]        gpt-4o-mini + brief normalisé + standards RAG
      │               Produit plan{data_models, pages, api_routes, user_flows[]}
      ▼
[spec_writer_node]    gpt-4o-mini + plan + requirements déterministes
      │               Écrit une spec Markdown actionnable pour le DevAgent
      ▼
[formatter_node]      0 LLM — pack ArchitectOutput
      │
      ▼
ArchitectOutput {
  spec         : Markdown détaillé (pages, routes, schéma Prisma)
  requirements : ["Task model", "GET /api/tasks", ...]  ← DÉTERMINISTE (jamais LLM)
  user_flows   : ["Utilisateur crée une tâche depuis /new", ...]
  stack_id     : "nextjs-clerk-prisma"
}
```

**Point clé :** `requirements[]` est dérivé mécaniquement de `plan.data_models`,
`plan.pages`, `plan.api_routes` — jamais généré par le LLM pour éviter les
"ghost success" (build réussi mais mauvaise app).

---

## Couche 3 — Dev Test Activity (cœur de la génération)

**Fichier :** `agents/dev_test_agent.py` → appelle `agents/dev_graph.py`

### 3a. Pré-run (avant LLM)

```
Étape 0 — Templates écrits sur disque (14 fichiers protégés)
  package.json, middleware.ts, app/layout.tsx, prisma/schema.prisma,
  lib/prisma.ts, jest.config.js, tsconfig.json, .env.local...
  → Ces fichiers ne sont JAMAIS écrasés par le LLM

Étape 1 — schema.prisma matérialisé depuis ArchitectOutput.data_models
Étape 2 — lib/types.ts généré déterministiquement (types TypeScript + Input types)
Étape 3 — npm install (~83s)
Étape 4 — prisma generate
```

### 3b. LangGraph DevGraph (génération LLM)

```
                    ┌─────────────────────────────────┐
                    │         DevGraph (LangGraph)     │
                    │                                 │
  SystemPrompt ──→  │  [dev_node]                     │
  + Spec            │    gpt-4o-mini                  │
  + Rules           │    Appelle write_file()          │◄─── RAG bridge
  + Standards RAG   │    pour chaque fichier métier   │     (Python direct,
                    │         │                       │     pas tool call)
                    │         ▼                       │
                    │  [file_validate_node]            │
                    │    npx tsc --noEmit              │
                    │    Si erreur → context_hint      │
                    │    via tsc_error_catalog.py      │
                    │         │                       │
                    │    OK?──┘ Loop si erreurs TSC    │
                    │         │                       │
                    │         ▼                       │
                    │  [prebuild_gate]                 │
                    │    prisma_validate               │
                    │    tsc global                    │
                    │    eslint                        │
                    │    ast_use_client                │
                    │         │                       │
                    │         ▼                       │
                    │  [build_node]                    │
                    │    npm run build                 │
                    └─────────────────────────────────┘
```

### 3c. Post-build (après génération)

```
Journey Validator    → vérifie que chaque user_flow a une route dans les fichiers générés
                       user_flows_covered / user_flows_total → is_useful_app

TSC Activity         → tsc --noEmit final sur tous les fichiers
Prisma Validate      → validation du schema Prisma final
Spec Coverage        → requirements_met / requirements_total = spec_coverage
Snapshot             → persisté dans /app/generated-projects/snapshots/
```

---

## Couche 4 — Catalogue d'erreurs TypeScript

**Fichier :** `agents/tsc_error_catalog.py`

```
Quand tsc retourne une erreur, le catalog Python (O(1)) identifie le code :

TS2307 → Module manquant → CREATE_FILE ou NPM_INSTALL
TS2339 → Propriété inexistante → ADD_TYPE_ANNOTATION ou CHECK_SCHEMA
TS2304 → Nom introuvable → CHECK_TYPES_FILE
TS2724 → Export inexistant → CHECK_TYPES_FILE
TS7006 → Paramètre sans type → ADD_EXPLICIT_TYPE
TS7031 → Destructuring non typé → ADD_EXPLICIT_TYPE
TS2531 → Object possibly null → ADD_NULL_CHECK
TS2345 → Type incompatible → FIX_AUTH_GUARD ou FIX_TYPE_MISMATCH

Pour chaque match :
  → context_hint injecté dans le prompt LLM (instruction actionnable)
  → rag_query déclenche un appel RAG Python direct → standard correctif injecté
```

---

## Couche 5 — RAG Qdrant (mémoire de code)

**Collection :** `factory_standards` — **84 standards actifs**

```
ZONE_1  → ZONE_8   : Standards stack globaux (Clerk v6, Prisma 7, Next.js 14 App Router)
ZONE_9  → ZONE_14  : Standards prescriptifs (INTERDIT / OBLIGATOIRE / PRÉFÉRÉ)
ZONE_15 → ZONE_16  : Réservés (conformité sémantique + sécurité — Sprint 4.6)
ZONE_17            : Standards préventifs stack (9 règles : force-dynamic, auth guard,
                     typed arrays, prisma singleton, Zod validation...)
ZONE_18            : Standards correctifs TypeScript (7 standards, 1 par code d'erreur TSC)
```

**Filtrage :** chaque requête RAG filtre `metadata.stack = nextjs-clerk-prisma`
+ `metadata.status = active` → pas de bruit cross-stack.

```
Architect    → RAG query = brief normalisé → standards de conception
Dev (bridge) → RAG query = rag_query du catalog → standard correctif ciblé
```

---

## Couche 6 — Stack-as-Config

**Fichier :** `config/stacks/nextjs-clerk-prisma.json`

```json
{
  "id": "nextjs-clerk-prisma",
  "packages": { "next": "14.2.25", "@clerk/nextjs": "^6.0.0", ... },
  "forbidden_imports": ["@clerk/nextjs/api", "next-auth", ...],
  "blueprint": { "required_files": [...] },
  "commands": { "install": "npm install", "build": "npm run build" },
  "qdrant_filter": { "must": [{"key": "metadata.stack", "match": {...}}] },
  "env_validation": { ... },
  "templated_files": [...]   ← fichiers jamais écrasés par le LLM
}
```

**Principe :** toute règle stack-spécifique vit dans ce JSON.
Ajouter une nouvelle stack (Vue.js, FastAPI) = créer un nouveau fichier JSON.
Zéro Python modifié.

---

## Couche 7 — Prompts / Personas

```
prompts/
├── base/
│   └── personas/
│       ├── architect.md     → rôle + règles Architect (brief normalizer + planner + spec writer)
│       └── spec_writer.md   → règles extraction : models, pages, routes, user_flows
│
└── stacks/
    └── nextjs-clerk-prisma/
        ├── rules_dev.md     → 16 guardrails courts pour le DevAgent (pas d'exemples de code)
        └── dev_prompts.py   → system prompt assemblé dynamiquement (persona + rules + spec + RAG)
```

**Principe :** RAG = guidance principale (exemples concrets, patterns validés).
`rules_dev.md` = guardrails courts (<16 règles). Un standard Qdrant bien rédigé > 3 lignes rules_dev.md.

---

## Couche 8 — Boucle d'apprentissage (Learner)

```
Run N échoue avec erreur X
    │
    ▼
shadow_log.json          ← tous les events (patches, erreurs, tool calls) par run_id
    │
    ▼
learner.py               ← analyse les patterns récurrents (≥3 runs)
    │
    ▼
learner_suggestions.json ← StandardSuggestion structurée (pas Qdrant direct)
    │
    ▼  validation humaine (approve_suggestion.py → y/n/q)
    │
    ▼
Qdrant ZONE_14           ← upsert avec status=active
    │
    ▼
Run N+1 : RAG retourne le bon standard → LLM génère correctement dès le début
```

---

## Métriques produites par run

```
build_success          : bool   — l'app compile
spec_coverage          : float  — requirements couverts (0.0 → 1.0)
user_flows_coverage    : float  — flows utilisateur couverts (Journey Validator)
is_useful_app          : bool   — spec_coverage > 80% ET user_flows > 60%
tsc_errors_count       : int    — erreurs TypeScript résiduelles
semantic_violations    : list   — violations de patterns stack (forbidden imports, etc.)
prisma_validate        : bool   — schema Prisma valide
tests_passed           : bool   — tests Jest passent (non bloquant)
iterations             : int    — nombre de tours LLM nécessaires (cible : 1)
build_attempts         : int    — tentatives de build (cible : 1)
```

---

## Structure des fichiers clés

```
factory-sprint0/
│
├── workflows/
│   └── todo_pilot_workflow.py       ← point d'entrée Temporal
│
├── agents/
│   ├── architect.py                 ← LangGraph Architect (5 nœuds)
│   ├── dev_graph.py                 ← LangGraph DevGraph (génération + build)
│   ├── dev_test_agent.py            ← orchestrateur dev_test_activity
│   ├── tsc_error_catalog.py         ← catalogue erreurs TypeScript (O(1))
│   ├── shared_tools.py              ← tous les @tools (write_file, shell_exec, rag_search...)
│   ├── stack_config.py              ← loader JSON stack
│   ├── learner.py                   ← Learner shadow mode
│   └── prebuild_pipeline.py         ← pipeline pré-build (prisma, tsc, eslint)
│
├── config/
│   └── stacks/
│       └── nextjs-clerk-prisma.json ← Stack-as-Config (40 clés)
│
├── prompts/
│   ├── base/personas/               ← architect.md, spec_writer.md
│   └── stacks/nextjs-clerk-prisma/  ← rules_dev.md, dev_prompts.py
│
├── scripts/
│   ├── run_batch.py                 ← client Temporal (lancement des runs)
│   ├── brief_catalog.py             ← 5 familles de briefs structurés
│   ├── migrate_zones_17_18.py       ← migration standards ZONE_17+18 vers Qdrant
│   ├── approve_suggestion.py        ← validation humaine suggestions Learner → Qdrant
│   └── validate_config_consumption.py ← audit champs JSON consommés vs déclarés
│
├── logs/
│   └── metrics/
│       ├── rag_usage.jsonl          ← IDs Qdrant utilisés par run (Mode Replay)
│       ├── guard_rule_events.jsonl  ← events guards déclenchés
│       └── run_reports/             ← snapshot JSON complet par run
│
└── docker-compose.yml               ← 6 services (temporal, qdrant, postgresql...)
```

---

## Résumé — Image mentale finale

```
BRIEF HUMAIN
     │
     ▼
ARCHITECT (LangGraph, 3 LLM calls)
  → normalise le brief
  → consulte Qdrant (standards de conception)
  → produit spec + requirements[] + user_flows[]
     │
     ▼
DEV AGENT (LangGraph, 1-2 LLM calls cible)
  → écrit 14 fichiers depuis templates (jamais LLM)
  → LLM écrit les fichiers métier (pages, routes, composants)
  → tsc valide après chaque batch → catalog corrige si erreur
  → prebuild gate (prisma + tsc + eslint)
  → npm run build
     │
     ▼
VALIDATEURS DÉTERMINISTES
  → spec_coverage (requirements couverts ?)
  → Journey Validator (user_flows couverts ?)
  → is_useful_app = spec_coverage > 80% ET flows > 60%
     │
     ▼
APPLICATION NEXT.JS BUILDÉE
  /app/generated-projects/<projet>/
  (.next/ présent = déployable sur Vercel)
```

---

*Cartographie générée le 18 Avril 2026 — reflète l'état Sprint 4.5*
