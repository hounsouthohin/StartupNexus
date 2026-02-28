# DIAGNOSTIC COMPLET DU PROJET — Software Agent Factory
## Date : 24 Février 2026 | Référence : Roadmap3.0 (v2.0)
### Rédigé pour donner un contexte exhaustif à l'agent orchestreur Claude

---

## 0. RÉSUMÉ EXÉCUTIF

Le projet est un pipeline Temporal entièrement fonctionnel (Architect → Dev → QA → GitHub → Learner) qui génère des applications Next.js 14 + Clerk V5 + Prisma 7. La mécanique de base tourne. Le Sprint 2 est à 95% terminé sur le plan architectural mais bloqué sur **un seul signal** : `build_success=false` persistant sur tous les runs du 24 février (4 runs consécutifs, toujours `BUILD_FAILED`). Le Sprint 3 a été partiellement anticipé (Stack-as-Config JSON, blueprint validator, stack_config.py) mais plusieurs fondations critiques sont **manquantes ou brisées** : run_id non propagé aux outils, Learner déconnecté du shadow log, standards non taggés dans Qdrant, LearnerActivity générant des suggestions hardcodées.

**État réel par sprint :**
- Sprint 0, 0.5, 1 → ✅ TERMINÉS (inchangés per roadmap)
- Sprint 2 → 🟡 EN COURS — signal manquant : `build_success=true`
- Sprint 3 → 🟠 PARTIELLEMENT ANTICIPÉ — 4 items sur 7 réalisés, 3 bloquants manquants

---

## 1. CE QUI FONCTIONNE BIEN ✅

### 1.1 Pipeline Temporal end-to-end
**Fichier :** `workflows/todo_pilot_workflow.py`
Le workflow est **solide et bien architecturé** :
- run_id généré via `uuid4()` dès le démarrage (ligne 59) — fondation Sprint 3B ✅
- stack_id = "nextjs-clerk-prisma" hardcodé dans le workflow (ligne 54) — conforme Sprint 3 ✅
- Retry policies différenciées : 5 tentatives pour architect_activity (Qdrant peut redémarrer), 3 pour les autres ✅
- QA en mode "best-effort" : un échec QA ne bloque pas le run métier ✅
- GitHub en mode "best-effort" : idem ✅
- Learner en mode "best-effort" ✅
- Séparation workflow_status (COMPLETED/FAILED_UNRECOVERABLE) vs build_status (SUCCESS/BUILD_FAILED/TESTS_FAILED) ✅
- TodoPilotOutput correctement structuré avec tous les compteurs ✅

### 1.2 Sanitizers shared_tools.py — Arsenal défensif complet
**Fichier :** `agents/shared_tools.py`
Le fichier est **très riche** en sanitizers qui protègent contre les hallucinations LLM :
- `_sanitize_package_json_content()` : Clerk package remapping, peer dep minimums, VERSION_PINS ✅
- `_sanitize_middleware_content()` : Clerk V4→V5 (withClerkMiddleware → clerkMiddleware) ✅
- `_sanitize_test_content()` : Clerk test mock fixes (@clerk/nextjs/api → @clerk/nextjs/server) ✅
- `_sanitize_source_content()` : Clerk source import fixes + App Router fixes ✅
- `_sanitize_nextconfig_content()` : eslint.ignoreDuringBuilds=true forcé ✅
- `_remove_pages_router_conflicts()` : supprime pages/ quand app/ existe ✅
- `_remove_problematic_babel_config()` : force SWC par défaut ✅
- `_remove_pages_tests_router_conflicts()` : nettoyage tests legacy pages/ ✅
- `validate_blueprint()` en mode WARNING (Sprint 3 correct) ✅
- `_log_patch()` centralisé en 1 helper (ligne 65) ✅
- `CLERK_TEST_MOCK_FIXES` contient bien `"@clerk/nextjs/api": "@clerk/nextjs/server"` (Fix 1 roadmap) ✅
- `JEST_REQUIRED_DEV_DEPS` contient bien `"node-mocks-http": "^1.14.0"` (Fix 2 roadmap) ✅

### 1.3 Stack-as-Config — Fondation posée
**Fichiers :** `config/stacks/nextjs-clerk-prisma.json` + `agents/stack_config.py`
- Le fichier JSON existe avec la bonne structure globale ✅
- `stack_config.py` charge le JSON et override les constantes Python de `shared_tools.py` (lignes 516-536) ✅
- Fonctions utilitaires : `get_version_pins()`, `get_blueprint()`, `get_forbidden_imports()`, etc. ✅
- Le JSON contient `forbidden_paths`, `forbidden_imports`, `import_remaps` complets ✅
- La section `blueprint.required_files` est définie ✅
- `build_hooks` listés ✅

### 1.4 Validation de contrats inter-agents
**Fichier :** `scripts/validate_contracts.py` (référencé par les activities)
Chaque activity appelle `validate_input()` et `validate_output()` avant/après exécution :
- `architect_activity.py` ✅
- `dev_test_activity.py` ✅
- `qa_activity.py` ✅
- `learner_activity.py` ✅
Les contrats JSON existent dans `schemas/contracts/`.

### 1.5 Prompt loader centralisé
**Fichier :** `utils/prompt_loader.py`
Utilisé par :
- `agents/architect.py` → `load_prompt("architect")` ✅
- `agents/qa.py` → `load_prompt()` ✅
- `agents/test_coverage.py` → `load_prompt()` ✅

### 1.6 Sécurité de base
- `.env.example` créé avec template propre (aucune valeur réelle) ✅
- Variables inutiles (`TEMPORAL_VERSION`, `ELASTICSEARCH_VERSION`, `OLLAMA_MODEL`) **absentes** du `.env.example` ✅
- Chemins absolus interdits dans `write_file()` via `_resolve_safe_path()` ✅
- Path traversal bloqué ✅

### 1.7 RAG actif
- Qdrant client initialisé en singleton dans `shared_tools.py` ✅
- k=10 pour architect, k=5 (DEFAULT_VECTOR_SEARCH_LIMIT) pour dev agent ✅
- Cache LRU implémenté (50 entrées max) ✅
- `_wait_for_qdrant()` avec polling 90s dans `architect.py` ✅
- `rag_usage.jsonl` loggué avec doc_ids réels + scores ✅

### 1.8 Learner shadow log fonctionnel
- `_write_learner_event()` correctement défini ✅
- Appelé depuis de nombreux endroits dans shared_tools (patches, config injections, lockfile resets) ✅
- 364 événements accumulés au dernier run (delta de 9 events/run en moyenne) ✅
- `patterns_report.json` généré avec 1 pattern HIGH détecté ✅

### 1.9 Architect Agent — Architecture LangGraph
- Graph: retrieval → planner → spec_writer → diagrammer → formatter ✅
- Validation Clerk compliance (FORBIDDEN_AUTH_PATTERNS) avec rewrite forcé ✅
- Gestion erreur Mermaid avec 3 tentatives et messages d'erreur contextuels ✅
- Dossier temporaire cross-platform (Windows/Linux) ✅

---

## 2. CE QUI NE FONCTIONNE PAS OU FONCTIONNE MAL ❌

### 2.1 [BLOQUANT SPRINT 2] build_success=false — 100% des runs récents
**Preuve :** 4 runs consécutifs le 24 février 2026 → tous `BUILD_FAILED`
```
todo_pilot_batch_20260224T023119Z.json → BUILD_FAILED (184s, 19 fichiers)
todo_pilot_batch_20260224T025428Z.json → BUILD_FAILED (330s, 12 fichiers)
todo_pilot_batch_20260224T090249Z.json → BUILD_FAILED (inconnu)
todo_pilot_batch_20260224T090829Z.json → BUILD_FAILED (212s, 14 fichiers)
```
Le signal de clôture Sprint 2 est `build_success=true sur 1 run`. Ce signal n'a jamais été obtenu. Les 2 fixes mineurs (Fix 1 et Fix 2 de la roadmap) sont **déjà implémentés** dans le code — ce n'est donc plus la cause des échecs. La cause réelle des BUILD_FAILED est **inconnue sans inspection des logs de build** (stdout/stderr npm run build).

**Impact :** Sprint 2 ne peut pas être déclaré terminé.

### 2.2 [CRITIQUE Sprint 3B] run_id NON propagé dans les outils
**Fichier :** `agents/shared_tools.py`
Partout où `_write_learner_event()` est appelé dans `shared_tools.py`, le `run_id` est passé comme **chaîne vide** `""` :
- Ligne 269 : `run_id=""`
- Ligne 295 : `run_id=""`
- Ligne 329 : `run_id=""`
- Ligne 967 : `run_id=""`
- Et tous les autres appels dans run_tests()

De même, `_append_rag_usage_event()` dans `rag_search` (ligne 685) passe `run_id=""`.

**Conséquence :** Impossible de corréler les événements shadow log avec un run_id précis → Mode Replay (Sprint 5) et anti-patterns (Sprint 4) seront impossibles à construire sans cette fondation. La roadmap Sprint 3B dit explicitement : "IMPORTANT : run_id doit être propagé à tous les appels".

**Cause :** Les outils LangChain (`@tool`) sont des fonctions décorées qui ne reçoivent pas automatiquement le run_id du workflow. Il faudrait soit :
- Passer run_id en contexte global thread-local dans chaque activity avant d'appeler l'agent
- Ou injecter run_id dans les arguments du tool (nécessite refactoring)

### 2.3 [CRITIQUE Sprint 3E] Learner DÉCONNECTÉ du shadow log
**Fichier :** `agents/learner.py`
La roadmap Phase E est explicite : "Le learner.py existe mais génère des suggestions hardcodées basées sur total_files < 8. Il ne lit jamais learner_shadow_log.json."

C'est exactement l'état actuel :
```python
# Seules 2 conditions hardcodées :
if total_files < 8:  # suggestion hardcodée
if build_status != "SUCCESS":  # suggestion hardcodée
```

Le Learner :
- Ne lit **jamais** `learner_shadow_log.json` ❌
- Ne filtre **jamais** par run_id ❌
- Ne classe **jamais** par `trigger_context` (rag_retrieved vs tool_guardrail) ❌
- Ne produit **jamais** de `StandardSuggestion` structurée avec `action`, `technology`, `evidence`, `confidence`, `requires_human_approval` ❌

**Conséquence :** Les suggestions générées sont inutiles pour le Gate Décisionnel Sprint 4 (besoin de 15-20 suggestions validées à 70%).

### 2.4 [CRITIQUE Sprint 3C] Standards Qdrant NON taggés avec stack_id
**Fichier :** `agents/shared_tools.py` — `rag_search` (ligne 677)
La recherche RAG est **non filtrée** : elle interroge toute la collection sans filtrer sur `metadata.stack`. Les 64 standards existants n'ont probablement pas de `metadata.stack = "nextjs-clerk-prisma"` ni de `metadata.status = "active"`.

La roadmap Sprint 3C requiert :
- Ajouter `metadata.stack`, `metadata.status`, `metadata.version` à chaque standard
- Filtrer `rag_search` par `stack_id` dès maintenant

**Impact :** Le RAG retourne des standards potentiellement hors-contexte. Le `qdrant_filter` défini dans le JSON stack config n'est **pas utilisé** par `rag_search`.

### 2.5 [MOYEN] nextjs-clerk-prisma.json — Schéma non conforme à la roadmap
**Fichier :** `config/stacks/nextjs-clerk-prisma.json`

Divergences vs spec roadmap Sprint 3B :
| Champ | Roadmap | Actuel |
|-------|---------|--------|
| `id` | `"nextjs-clerk-prisma"` | absent (a `stack_id` à la place) |
| `display_name` | `"Next.js 14 + Clerk v5 + Prisma 7"` | absent |
| `status` | `"stable"` | absent |
| `@clerk/nextjs` version | `"^6.0.0"` | `"*"` (wildcard dangereux) |
| `prisma` version | `"^7.0.0"` | `"latest"` (peut casser) |
| `sanitizers` | liste de strings `["remove_pages_conflicts", ...]` | dict de booleans `{"eslint_ignore_builds": true, ...}` |
| `prompt_folder` | `"prompts/stacks/nextjs-clerk-prisma/"` | absent |

**Impact :** Si un nouveau collaborateur ou un agent lit ce JSON pour la conformité, il ne correspond pas exactement au schéma documenté. Les `sanitizers` comme liste de strings était le contrat prévu pour le `SanitizerRegistry` (Sprint 6-7).

### 2.6 [MOYEN] VERSION_PINS encore dans le code Python
**Fichier :** `agents/shared_tools.py` lignes 100-103
```python
VERSION_PINS: dict[str, str] = {
    "next": "14.2.25",
    "typescript": "^5.3.3",
}
```
La roadmap Sprint 3B dit : "VERSION_PINS supprimé du code Python, lus depuis le JSON". Certes, le bloc Stack-as-Config (ligne 516) override ces constantes si le JSON est chargé correctement — mais le fallback Python reste. La **rigidité** est estimée à 8.8/10 actuellement. L'objectif Sprint 3 est ~5/10.

### 2.7 [MOYEN] Architect output manque les champs requis pour Sprint 4
**Fichier :** `workflows/activities/architect_activity.py`
La sortie actuelle de l'Architect est :
```python
{"specification": "...", "mermaid_diagram": "..."}
```
La roadmap Sprint 4 exige (Architect Output Contract v2) :
```json
{
  "router_type": "app",
  "stack_id": "nextjs-clerk-prisma",
  "forbidden_paths": [...],
  "required_files": [...]
}
```
Ces champs ne sont ni générés ni transmis. Ce n'est pas bloquant pour Sprint 3 mais doit être planifié.

### 2.8 [MOYEN] rag_usage.jsonl — Architect ne log pas les IDs Qdrant réels
**Fichier :** `agents/architect.py` — `_append_architect_rag_event()` (ligne 43)
L'architect log des `docs` avec `snippet` (180 chars) mais **pas les IDs Qdrant réels**. La roadmap Sprint 3B exige : "rag_usage.jsonl doit stocker les IDs Qdrant réels des documents retournés, pas des snippets de 180 chars."

`shared_tools.py` le fait correctement (`doc_ids = [str(h.id) for h in search_hits]`) mais l'architect a son propre logger qui écrit des snippets.

### 2.9 [FAIBLE] Score qualité moyen trop bas (13.8/100 vs critère ≥ 45)
**Fichier :** `logs/shadow/patterns_report.json`
```json
"avg_quality_score": 13.8,
"global_failure_rate": 86.2
```
Le critère 7 de SPRINT2_SUCCESS_Criteria.md exige `avg_quality_score ≥ 45`. Le score actuel de 13.8 est lié directement au `build_success=false`. Si le build réussit, ce score devrait remonter significativement (le poids `build_success` dans le score est 30/100).

### 2.10 [FAIBLE] Logs metrics non archivés
**Git status** montre de nombreux fichiers supprimés `D factory-sprint0/logs/metrics/todo_pilot_batch_*.json` et 4 nouveaux non trackés `??`. La roadmap Sprint 3A dit "Archiver logs/metrics anciens (garder 3 derniers)". C'est partiellement fait (les vieux sont supprimés du tracking) mais les 4 nouveaux ne sont pas commitables proprement.

### 2.11 [FAIBLE] .gitignore non vérifié pour .env
La roadmap Sprint 3A exige `.env ajouté au .gitignore`. `.env.example` existe mais on ne peut pas confirmer sans git ls-files que `.env` est bien ignoré (et que des clés n'ont pas été commitées dans l'historique git).

---

## 3. CE QUI EST HORS CADRE OU À CHANGER 🔧

### 3.1 SPRINT2_SUCCESS_Criteria.md — Critères 7 et 12 non validés
Le score qualité moyen (13.8/100) est largement sous les 45 requis par le critère 7. Le temps moyen de run est dans les tolérances (212-330s soit 3.5 à 5.5 min, objectif < 8 min ✅).

### 3.2 Workflow Temporal — Stack_id hardcodé vs. dynamique
Le `stack_id = "nextjs-clerk-prisma"` est hardcodé dans `todo_pilot_workflow.py` ligne 54. C'est conforme à la roadmap Sprint 3 ("hardcodé pour l'instant, dynamique Sprint 4"). **À NE PAS changer avant Sprint 4.**

### 3.3 agents/evaluator.py — Présent mais non intégré au pipeline
**Fichier :** `agents/evaluator.py`
L'évaluateur génère `patterns_report.json`. Il n'est pas appelé dans le workflow Temporal — il fonctionne séparément (script externe). C'est le comportement voulu pour Sprint 2-3 mais cela devrait être intégré Sprint 4-5.

### 3.4 config/agents_config.yaml — Rôle documentaire uniquement
La roadmap dit de "Commenter config/agents_config.yaml comme documentaire uniquement". Il faut vérifier que ce fichier ne pilote rien dans le code.

### 3.5 dev_test_activity.py — Structure de sortie à vérifier
Le `dev_test_result` retourne `dev_output`, `test_output`, `combined_files`, `metadata`. Le workflow l'utilise pour extraire les fichiers à pusher sur GitHub. À vérifier que `combined_files` contient bien tous les fichiers générés.

---

## 4. CE QUI RESTE À FAIRE — PLAN PRIORISÉ 📋

### PRIORITÉ 1 — SPRINT 2 CLOSURE (MAINTENANT)
**Objectif : obtenir build_success=true sur 1 run**

4.1 **Investiguer la cause réelle des BUILD_FAILED**
- Inspecter les logs GitHub PR générés : `https://github.com/hounsouthohin/saas-todo-batch-alpha`
- Lire les `STDOUT`/`STDERR` de `npm run build` dans les logs Temporal
- Les Fix 1 et Fix 2 de la roadmap sont déjà dans le code (CLERK_TEST_MOCK_FIXES et node-mocks-http) — la cause est ailleurs

4.2 **Hypothèses de build failure à investiguer :**
- Erreur TypeScript non couverte par les sanitizers existants
- Import interdit non détecté dans un fichier généré
- Prisma 7 breaking change non géré (la gestion `prisma.config.ts` existe mais peut rater)
- `@clerk/nextjs: "*"` dans le JSON stack config peut installer une version incompatible
- Conflit entre les fichiers générés par le LLM et le blueprint attendu

### PRIORITÉ 2 — SPRINT 3 FONDATIONS CRITIQUES (J1-J5, deadline 7 Mars)

4.3 **Propagation run_id dans les outils (2h de travail, impact Sprint 4-5)**
- Créer un `threading.local()` ou `contextvars.ContextVar` dans `shared_tools.py`
- Dans chaque activity, appeler `set_current_run_id(run_id)` avant d'invoquer l'agent
- Modifier `_write_learner_event()` et `_append_rag_usage_event()` pour lire le run_id du contexte
- Tous les `run_id=""` passés en dur doivent disparaître

4.4 **Learner connecté au shadow log (Phase E)**
- Modifier `agents/learner.py` pour lire `logs/shadow/learner_shadow_log.json`
- Filtrer par `run_id` (possible seulement après 4.3)
- Classifier par `trigger_context` : `rag_retrieved` → renforcer le prompt, `tool_guardrail` → créer standard Qdrant
- Générer des `StandardSuggestion` avec format prescrit : `action`, `technology`, `evidence`, `confidence`, `requires_human_approval`
- Écrire dans `logs/shadow/learner_suggestions.json`

4.5 **Tagger les 64 standards Qdrant + filtrer rag_search**
- Script de migration : ajouter `metadata.stack`, `metadata.status = "active"`, `metadata.version = "1.0"` à chaque point Qdrant
- Modifier `rag_search` dans `shared_tools.py` pour accepter un paramètre `stack_id` et appliquer le filtre `qdrant_filter` depuis le JSON stack config

4.6 **Corriger nextjs-clerk-prisma.json**
- Remplacer `"@clerk/nextjs": "*"` par `"@clerk/nextjs": "^6.0.0"`
- Remplacer `"prisma": "latest"` par `"^7.0.0"`
- Ajouter `"id"`, `"display_name"`, `"status"`, `"prompt_folder"` pour conformité au schéma

4.7 **Standards prescriptifs Qdrant (3 manquants per roadmap Sprint 2)**
- INTERDIT `pages/` quand `app/` existe → standard Qdrant à créer
- INTERDIT `import @clerk/nextjs/api` → standard Qdrant à créer
- OBLIGATOIRE `node-mocks-http` pour tests API Routes → standard Qdrant à créer
- Utiliser le template prescriptif complet (ACTION / STACK / TECHNOLOGIE / RAISON / DETECTION_REGEX / ALTERNATIVE / EXEMPLE_INVALIDE / EXEMPLE_VALIDE / ERREUR_ATTENDUE / STATUS / VERSION)

4.8 **Rotation secrets (Sécurité critique Sprint 3A)**
- Rotation de l'OPENAI_API_KEY si elle a été exposée dans git history
- Rotation du GITHUB_TOKEN
- Vérifier `.gitignore` contient bien `.env`
- Audit `git log --all -- .env` pour confirmer aucune clé exposée

4.9 **Archiver les anciens logs/metrics**
- Garder seulement les 3 derniers `todo_pilot_batch_*.json`
- Committer les suppressions proprement

### PRIORITÉ 3 — SPRINT 3 COMPLÉMENTS (J5-J9)

4.10 **Corriger _append_architect_rag_event() pour logguer les IDs Qdrant**
- Dans `architect.py`, extraire les UUIDs des documents via `doc.metadata.get("id")` ou l'attribut Qdrant

4.11 **Préparer Architect Output Contract v2 (avant Sprint 4)**
- Ajouter `router_type`, `stack_id`, `forbidden_paths`, `required_files` dans la sortie de `architect_activity`
- Mettre à jour le JSON Schema dans `schemas/contracts/architect_agent_contract.json`

4.12 **Version pins supprimés du code Python**
- Retirer les constantes `VERSION_PINS`, `JEST_REQUIRED_DEV_DEPS`, `CLERK_PACKAGE_FIXES` du code Python
- Le bloc "Stack-as-Config override" (lignes 516-536) devient la **seule source**
- Ajouter une erreur explicite si le JSON stack config est absent (au lieu du fallback silencieux)

---

## 5. TABLEAU DE BORD SPRINT

| Signal | Valeur actuelle | Objectif Sprint 2 | Objectif Sprint 3 |
|--------|----------------|-------------------|-------------------|
| build_success | 0/4 runs (0%) | 1 run ≥ 1 ✅ | 2+ runs reproductibles |
| Stack-as-Config JSON | ✅ Existe | — | Version corrigée |
| VERSION_PINS Python | ✅ Overridé mais présent | — | Supprimé |
| run_id propagé | ❌ "" partout | — | ✅ Partout |
| Standards taggés | ❌ 0/64 taggés | — | ✅ 64 taggés |
| LearnerActivity connectée | ❌ Hardcodé | — | ✅ Lit shadow log |
| StandardSuggestion structurées | ❌ Absent | — | ✅ Générées |
| Secrets rotés | ❓ Non vérifié | — | ✅ Rotés |
| avg_quality_score | 13.8/100 | ≥ 45 | — |
| Learner events/run | ~7-9 | — | — |
| Total learner events | 364 | — | — |
| Patterns détectés | 1 (P-001 HIGH) | ≥ 1 ✅ | — |

---

## 6. CONTEXTE TECHNIQUE POUR L'ORCHESTREUR

### Architecture effective (ce qui tourne vraiment)
```
TodoPilotWorkflow (Temporal)
  ├─ architect_activity → create_architect_agent() [LangGraph]
  │    └─ retrieval → planner → spec_writer → diagrammer → formatter
  │         RAG: Qdrant vectorstore k=10, non filtré par stack
  │
  ├─ dev_test_activity → dev_agent() + test_coverage_agent() [ReAct]
  │    Tools: write_file, validate_syntax, prisma_migrate, rag_search, read_files, run_build, run_tests
  │    Sanitizers actifs: Clerk fix, VERSION_PINS, middleware V4→V5, pages router conflict
  │
  ├─ qa_activity → qa_agent() [LangGraph, best-effort]
  │    Tool: playwright_test (génère des tests E2E)
  │
  ├─ github_activity → crée repo + push fichiers + PR (best-effort)
  │
  └─ learner_activity → learner_agent() [SHADOW MODE]
       Problème: hardcodé, déconnecté du shadow log
```

### Fichiers clés à modifier pour les prochaines tâches

| Priorité | Fichier | Modification |
|----------|---------|-------------|
| P1 | `agents/shared_tools.py` | Investiguer BUILD_FAILED, propager run_id |
| P2 | `agents/learner.py` | Connecter au shadow log, StandardSuggestion |
| P2 | `agents/shared_tools.py` | Filtrer rag_search par stack_id |
| P2 | `config/stacks/nextjs-clerk-prisma.json` | Corriger versions, ajouter champs manquants |
| P3 | `agents/architect.py` | Logger IDs Qdrant réels |
| P3 | `workflows/activities/architect_activity.py` | Output Contract v2 |

### Flux de données run_id (état cible Sprint 3)
```
TodoPilotWorkflow.run()
  run_id = str(uuid4())
  → architect_activity(input_data, run_id)
      set_current_run_id(run_id)  # ← À CRÉER
      → create_architect_agent()  → _append_architect_rag_event(run_id=get_run_id())
  → dev_test_activity(input_data, run_id)
      set_current_run_id(run_id)  # ← À CRÉER
      → dev_agent() → tools → _write_learner_event(run_id=get_run_id())
                            → _append_rag_usage_event(run_id=get_run_id())
  → learner_activity(input_data, run_id)
      → learner_agent() → lire shadow_log filtré par run_id
                        → générer StandardSuggestion structurées
```

### Cause probable du BUILD_FAILED persistant
Les 2 fixes de la roadmap (CLERK_TEST_MOCK_FIXES + node-mocks-http) sont dans le code depuis plusieurs jours. Les builds échouent encore → la cause est différente. Candidats probables :
1. **TypeScript strict errors** : `typescript: ignoreBuildErrors: false` dans `next.config.js` (ligne 549 shared_tools) — les erreurs TS bloquent le build
2. **@clerk/nextjs: "*"** dans le JSON stack config → installe une version incompatible (peut-être ^7 qui casse l'API)
3. **Fichier généré manquant** du blueprint (ex: `prisma/schema.prisma` au lieu de `schema.prisma`)
4. **Erreur ESLint dans un fichier** non couverte par `ignoreDuringBuilds`

**Action immédiate recommandée :** Inspecter le `STDOUT`/`STDERR` du `npm run build` du dernier run dans les logs Temporal UI (http://localhost:8233) pour identifier l'erreur exacte.

---

*Rapport généré le 24 Février 2026 par analyse statique complète du projet.*
*Ce document est la source de vérité pour l'orchestreur Claude dans les sessions suivantes.*
