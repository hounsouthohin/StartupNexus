# OPERATIONAL REALITY - Audit operationnel vs declarations Sprint 2

## 1. Executive Summary

- Conformite theorie vs realite (estimee): **49%**
- Verdict global: **Partiellement conforme, avec trous critiques d'observabilite et de gouvernance runtime**

Top 3 gaps identifies:
1. **Prompts non centralises uniformement**: seul Dev utilise `utils/prompt_loader.py`; Architect/QA/TestCoverage chargent autrement.
2. **RAG non observable en production**: impossible de prouver quels standards Qdrant sont effectivement recuperes.
3. **LearnerAgent non implemente comme agent runtime**: shadow mode existe surtout comme logging + script evaluator, pas comme composant d'orchestration actif.

Top 3 risques:
1. **Risque de derive fonctionnelle** (ce qui est “declare” n'est pas ce qui tourne vraiment).
2. **Risque de regressions silencieuses** (pas de telemetrie retrieval RAG, pas de couverture de l'usage reel des standards).
3. **Risque securite majeur** (secrets presents en clair dans `.env`).

Recommandations prioritaires:
1. Instrumenter `rag_search` (query, top-k, ids/doc metadata, score) et logger dans `logs/metrics/rag_usage_*.json`.
2. Centraliser *tous* les chargements de prompts via `utils/prompt_loader.py`.
3. Introduire un vrai `LearnerAgent` runtime (activity dediee) ou renommer officiellement le scope actuel en “Learner telemetry only”.
4. Ajouter healthcheck Qdrant + `depends_on: service_healthy` pour `factory-worker`.
5. Rotation immediate des secrets `.env` exposes.

---

## 2. Audits detailles

## Audit 1 - Prompts centralises

### Findings

| Agent | Utilise load_prompt() | Prompt file existe | Status |
|---|---|---|---|
| architect | Non (`load_prompts` maison) | `prompts/architect.md` | Partiel |
| dev | Oui (`load_prompt("dev")`) | `prompts/dev.md` | OK |
| qa | Non (lecture fichier directe) | `prompts/qa.md` | Partiel |
| test_coverage | Non (lecture fichier directe) | `prompts/test_coverage.md` | Partiel |
| dev_test_agent | N/A (orchestrateur fusion) | N/A | N/A |
| github_activity | N/A (pas LLM prompt) | N/A | N/A |

- Prompts presents dans `prompts/`: `architect.md`, `dev.md`, `qa.md`, `test_coverage.md`.
- Prompts non charges detectes: **aucun**.
- Agents utilisant prompts sans `load_prompt`: Architect, QA, TestCoverage.

### Evidence

- Loader central: `factory-sprint0/utils/prompt_loader.py:6`
- Dev utilise loader central: `factory-sprint0/agents/dev.py:18`, `factory-sprint0/agents/dev.py:133`
- Architect charge localement: `factory-sprint0/agents/architect.py:52`
- QA charge localement: `factory-sprint0/agents/qa.py:61`
- TestCoverage charge localement: `factory-sprint0/agents/test_coverage.py:112`

### Severity

- **Medium**

### Actions recommandees

1. Remplacer les lectures directes/parse custom par `load_prompt()` pour Architect/QA/TestCoverage.
2. Ajouter un test unitaire “all prompt-based agents use prompt_loader”.

---

## Audit 2 - Patches loggues (defense niveau 2)

### Findings

Fonctions `shared_tools.py` detectees:
- Helpers: `_truncate_output`, `_resolve_safe_path`, `_is_valid_npm_package_name`, `_normalize_npm_package_name`, `_sanitize_package_json`, `_write_learner_event`
- Tools: `rag_search`, `write_file`, `validate_syntax`, `prisma_migrate`, `read_files`, `run_build`, `run_tests`, `log_to_learner`

Corrections automatiques analysees:
- **Logguees (`tool_patch_applied`)**:
  - package name invalide corrige/supprime (`_sanitize_package_json`)
  - fix middleware matcher `/protected/**` -> `/protected/(.*)` (`write_file`)
  - fix versions `ts-jest` et `next` (`run_tests`)
  - injections fichiers config (`tsconfig.json`, `jest.setup.js`, `jest.config.js`, mock clerk middleware) (`run_tests`)
- **Non logguee**:
  - suppression `package-lock.json` en fallback npm ci -> npm install (`run_tests`)

Score logging corrections: **9/10** (estimation sur branches de patch explicites).

Format logging:
- Globalement coherent (`metric="tool_patch_applied"`, payload structuré), mais pas de schema strict impose runtime.

### Evidence

- Points de log patch: `factory-sprint0/agents/shared_tools.py:124`, `factory-sprint0/agents/shared_tools.py:149`, `factory-sprint0/agents/shared_tools.py:224`, `factory-sprint0/agents/shared_tools.py:523`, `factory-sprint0/agents/shared_tools.py:541`, `factory-sprint0/agents/shared_tools.py:621`, `factory-sprint0/agents/shared_tools.py:648`, `factory-sprint0/agents/shared_tools.py:683`, `factory-sprint0/agents/shared_tools.py:714`
- Correction non logguee (remove lockfile): `factory-sprint0/agents/shared_tools.py:795`
- Ecriture log learner: `factory-sprint0/agents/shared_tools.py:872`

### Severity

- **Medium**

### Actions recommandees

1. Logger aussi les correctifs de fallback lockfile (`tool_patch_applied`, patch=`lockfile_reset`).
2. Normaliser un mini-schema de payload patch (file, patch, reason, before, after).

---

## Audit 3 - Standards Qdrant utilises

### Findings

- Les appels RAG existent dans le code:
  - `Dev` via `rag_search(query)`
  - `Architect` via retriever direct
- Mais les logs existants **ne tracent pas**:
  - query exacte par run
  - documents/IDs recuperes
  - scores similarity
  - coverage des standards consultes

Conséquence:
- `X/61` consultes, `IDs jamais consultes`, `Top 5 consultes`: **non mesurable avec la telemetry actuelle**.
- Qualite retrieval en exploitation: **Non auditable objectivement** (gap critique d'observabilite).

Note de coherence:
- La base declaree “61 standards” n'est pas verifiable depuis les logs run.
- Le script de peuplement contient 65 occurrences `"text":` (pas necessairement 65 points valides), suggerant possible derive entre declaration et corpus reel.

### Evidence

- Appel RAG Dev: `factory-sprint0/agents/shared_tools.py:171`, `factory-sprint0/agents/dev.py:140`
- k par defaut: `factory-sprint0/config/factory_config.py:14`
- Appel RAG Architect (k=10): `factory-sprint0/agents/architect.py:92`
- Aucune trace rag_search exploitable dans `logs/` (pas de query/doc ids)

### Severity

- **High**

### Actions recommandees

1. Instrumenter `rag_search` avec journal JSON: `{run_id, agent, query, k, doc_ids, metadata, scores}`.
2. Ajouter KPI “standard_usage_rate = consulted_unique / total_standards”.
3. Ajouter audit automatisé hebdo sur standards jamais consultes.

---

## Audit 4 - Architecture Layered (Code -> Prompt -> RAG)

### Findings

Conformites:
- **Code (hard rules)**: validations contracts runtime, interdits auth dans Architect activity.
- **Prompt**: contraintes Clerk explicites.
- **RAG**: contient versions/patterns/configs techniques.

Violations/derives:
- Versions hardcodees dans code (ex: `next=14.2.3`, `ts-jest=29.1.2`) alors que ces details devraient etre majoritairement pilotés par RAG.
- Certaines regles critiques restent principalement dans prompts (donc non garanties si LLM derape).
- Corpus RAG `populate_qdrant.py` melange standards + blocs de patch/notes operationnelles.

Verdict architecture layered: **Partiellement respectee**.

### Evidence

- Hard rules contracts: `factory-sprint0/workflows/activities/architect_activity.py:48`, `factory-sprint0/workflows/activities/dev_test_activity.py:73`, `factory-sprint0/workflows/activities/qa_activity.py:33`, `factory-sprint0/workflows/activities/github_activity.py:22`
- Hard rules auth interdite: `factory-sprint0/workflows/activities/architect_activity.py:12`
- Prompt constraints: `factory-sprint0/prompts/architect.md:1`, `factory-sprint0/prompts/dev.md:17`
- RAG corpus: `factory-sprint0/scripts/populate_qdrant.py:33`
- Hardcoded version patches: `factory-sprint0/agents/shared_tools.py:538`, `factory-sprint0/agents/shared_tools.py:556`

### Severity

- **High**

### Actions recommandees

1. Migrer les version pins du code vers politiques RAG + garde-fous code minimaux.
2. Formaliser “ce qui doit etre Code vs Prompt vs RAG” dans un contrat d’architecture.
3. Nettoyer le corpus Qdrant (separer standards stables vs notes de run).

---

## Audit 5 - Learner Agent shadow mode

### Findings

- `LearnerAgent` comme agent runtime dedie: **non trouve** (pas de fichier agent learner actif).
- Shadow mode reel: present via `_write_learner_event` appele depuis activities DevTest/QA et tools.
- Analyse de patterns: faite par `agents/evaluator.py` (script/agent analytique hors workflow principal).
- Ecriture Qdrant: non automatique depuis workflow (coherent shadow), mais possible via script manuel `scripts/enrich_qdrant.py`.

Qualite des donnees shadow:
- `learner_shadow_log.json` contient beaucoup d'evenements metrics + patches.
- Format heterogene (payload parfois dict, parfois string JSON legacy via `events`).
- Suggestions “standards” explicites haute valeur: faibles; surtout telemetrie d'execution.

Verdict:
- LearnerAgent implemente: **Partiellement**
- Shadow mode fonctionnel: **Oui (telemetrie)**
- Qualite suggestions: **Moyen a faible**
- Pret activation Sprint 5: **Non (avec corrections)**

### Evidence

- No learner runtime class/file: recherche `factory-sprint0/agents` (seulement tools de log)
- Log writer: `factory-sprint0/agents/shared_tools.py:872`
- Appels depuis activities: `factory-sprint0/workflows/activities/dev_test_activity.py:40`, `factory-sprint0/workflows/activities/qa_activity.py:15`
- Evaluator patterns: `factory-sprint0/agents/evaluator.py:136`
- Shadow log structure: `factory-sprint0/logs/shadow/learner_shadow_log.json:1`, `factory-sprint0/logs/shadow/learner_shadow_log.json:1495`
- Contrat learner: `factory-sprint0/schemas/contracts/learner_agent_contract.json:3`

### Severity

- **High**

### Actions recommandees

1. Soit creer un vrai `agents/learner.py` branche dans workflow, soit renommer officiellement la fonctionnalite actuelle.
2. Unifier schema des events shadow (supprimer format legacy `events` stringifie).
3. Exiger generation automatique de `patterns_report` post-batch (pipeline stable).

---

## Audit 6 - Docker healthchecks

### Findings

- Services `docker-compose`: 7 (`elasticsearch`, `postgresql`, `temporal`, `temporal-ui`, `n8n`, `qdrant`, `factory-worker`)
- Healthchecks definis: 3/7 (`elasticsearch`, `postgresql`, `temporal`)
- `depends_on condition: service_healthy`:
  - `temporal <- postgresql + elasticsearch`
  - `temporal-ui <- temporal`
  - `factory-worker <- temporal` (OK)
- `factory-worker <- qdrant` est seulement `service_started` (pas `healthy`)
- Mitigation partielle: `wait-for-it.py` dans la commande `factory-worker`.

Test empirique boot:
- **Non realisable ici** (Docker daemon indisponible sur l'environnement d'audit).

### Evidence

- Healthchecks: `factory-sprint0/docker-compose.yml:19`, `factory-sprint0/docker-compose.yml:42`, `factory-sprint0/docker-compose.yml:77`
- depends_on healthy: `factory-sprint0/docker-compose.yml:72`, `factory-sprint0/docker-compose.yml:97`, `factory-sprint0/docker-compose.yml:157`
- qdrant service_started only: `factory-sprint0/docker-compose.yml:159`
- wait-for-it usage: `factory-sprint0/docker-compose.yml:149`
- Command test echec docker: `docker compose ... ps` -> daemon introuvable (pipe Docker Desktop)

### Severity

- **Medium**

### Actions recommandees

1. Ajouter healthcheck Qdrant et basculer `factory-worker` sur `service_healthy`.
2. Conserver `wait-for-it` comme defense supplementaire, pas principale.
3. Ajouter test CI de boot compose + assert “no connection refused”.

---

## Audit 7 - Configurations non utilisees

### Findings

### A. Variables `.env`

- Variables presentes:
  - `TEMPORAL_VERSION`, `TEMPORAL_UI_VERSION`, `ELASTICSEARCH_VERSION`, `POSTGRESQL_VERSION`, `OLLAMA_MODEL`, `OPENAI_API_KEY`, `GITHUB_TOKEN`
- Variables lues par le code runtime:
  - `OPENAI_API_KEY`, `GITHUB_TOKEN`
- Variables `.env` non utilisees detectees:
  - `TEMPORAL_VERSION`, `TEMPORAL_UI_VERSION`, `ELASTICSEARCH_VERSION`, `POSTGRESQL_VERSION`, `OLLAMA_MODEL`

### B. `config/factory_config.py`

- Parametres utilises: `QDRANT_URL`, `QDRANT_COLLECTION_NAME`, `EMBEDDING_MODEL`, `DEFAULT_VECTOR_SEARCH_LIMIT`, timeouts, `TEMPORAL_ADDRESS`.
- Dead config claire: **aucune** (dans ce fichier).

### C. Fichiers de config

- `dynamicconfig/development-sql.yaml`: **utilise** (montage + env Temporal).
- `config/agents_config.yaml`: surtout utilise par tests/docs/scripts, pas par orchestration runtime principale.
- `config/langgraph_config.yaml`: idem, peu/no runtime binding observe (principalement docs/tests/metrics script).

### Evidence

- `.env`: `factory-sprint0/.env:1`
- Usage env runtime: `factory-sprint0/workflows/activities/architect_activity.py:44`, `factory-sprint0/workflows/activities/github_activity.py:33`
- Factory config usage: `factory-sprint0/agents/shared_tools.py:16`, `factory-sprint0/api/flask_api.py:19`, `factory-sprint0/scripts/run_batch.py:23`
- Dynamicconfig compose: `factory-sprint0/docker-compose.yml:65`, `factory-sprint0/docker-compose.yml:69`
- `agents_config.yaml` / `langgraph_config.yaml` references surtout tests/docs: `factory-sprint0/tests/test_sprint1_validation.py:79`, `factory-sprint0/tests/test_sprint1_validation.py:332`

### Severity

- **Medium**

### Actions recommandees

1. Nettoyer `.env` des variables non consommees ou les activer via substitution compose.
2. Clarifier “runtime config source of truth” (factory_config vs yaml).
3. Si `agents_config/langgraph_config` doivent piloter runtime, brancher explicitement dans worker/workflow.

---

## 3. Dead Code / Dead Config

## Dead config (probable)

| Element | Type | Statut | Impact si supprime | Recommandation |
|---|---|---|---|---|
| `TEMPORAL_VERSION` (.env) | Env | Non lu | Nul | Supprimer |
| `TEMPORAL_UI_VERSION` (.env) | Env | Non lu | Nul | Supprimer |
| `ELASTICSEARCH_VERSION` (.env) | Env | Non lu | Nul | Supprimer |
| `POSTGRESQL_VERSION` (.env) | Env | Non lu | Nul | Supprimer |
| `OLLAMA_MODEL` (.env) | Env | Non lu | Nul | Supprimer ou implementer |
| `config/langgraph_config.yaml` | Config | Peu/no runtime usage | Faible | Conserver si roadmap split proche, sinon archiver |
| `config/agents_config.yaml` | Config | Peu/no runtime usage direct | Faible | Conserver court terme, puis brancher ou simplifier |

## Dead/ambiguous behavior

| Element | Type | Observation | Recommandation |
|---|---|---|---|
| Learner “agent” | Architecture | Pas d'agent runtime dedie, mais telemetrie + evaluator | Renommer scope ou implementer agent reel |
| RAG usage analytics | Observability | Impossible de mesurer IDs/docs consultes | Ajouter logs retrieval obligatoires |

---

## 4. Pret Sprint 3 ?

### Checklist validation

- [x] Workflows Temporal executes (SaaS + TodoPilot)
- [x] Activities contracts validates runtime
- [x] Shadow telemetry learner ecrite
- [ ] Prompts centralises uniformement
- [ ] Observabilite RAG exploitable
- [ ] Learner runtime architecture claire
- [ ] Docker health path complet (Qdrant healthy gate)
- [ ] Hygiene secrets/configs complete

### Correctifs necessaires avant continuation

1. **Critical**: rotation secrets `.env` exposes + retirer secrets du repo.
2. **High**: instrumentation RAG pour auditabilite reelle.
3. **High**: decision architecture Learner (agent reel vs telemetry only) + alignement doc/code.
4. **Medium**: centraliser loader prompts sur tous agents LLM.
5. **Medium**: healthcheck Qdrant + depends_on healthy.
6. **Medium**: cleanup config/env non utilises.

### Estimation effort correctifs

- P0 (secrets + hygiene): 0.5 jour
- P1 (RAG telemetry + KPI usage): 1.5 jours
- P1 (Learner architecture clarification + wiring minimal): 1 a 2 jours
- P2 (prompt loader unifie): 0.5 a 1 jour
- P2 (Docker health path complet): 0.5 jour
- P2 (config cleanup + doc sync): 0.5 jour

**Total estime**: **4 a 6 jours**

---

## Annexe - Limites de cet audit

- Le test empirique de boot Docker (`down/up`, mesure temps, erreurs connection refused) n'a pas pu etre execute dans cet environnement: daemon Docker indisponible.
- L'usage reel des 61 standards Qdrant (IDs consultes, top consultes, jamais consultes) est non calculable avec les logs actuels, faute de telemetrie retrieval.
