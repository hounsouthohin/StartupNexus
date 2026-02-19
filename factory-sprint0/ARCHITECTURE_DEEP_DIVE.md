# ARCHITECTURE DEEP DIVE - StartupNexus (factory-sprint0)

## 1) Vue d'ensemble

### 1.1 Flux global (ASCII)

```text
[User: "Cree une Todo app avec Clerk"]
        |
        | (A) n8n webhook
        v
[n8n Webhook node]
  file: workflow.json
  path: POST /webhook/start-saas (n8n)
        |
        | HTTP POST {"phrase": ...}
        v
[Factory API Flask]
  file: api/flask_api.py
  endpoint: POST /start-saas
        |
        | Client.start_workflow(SaaSFactoryWorkflow.run, {phrase, project_name})
        v
[Temporal Server]
        |
        v
[Temporal Worker]
  file: run/worker.py
  queue: factory-task-queue
  workflows registered: SaaSFactoryWorkflow + TodoPilotWorkflow
        |
        v
[SaaSFactoryWorkflow] OR [TodoPilotWorkflow]
  activities sequence:
    1) architect_activity
    2) dev_test_activity
    3) qa_activity
    4) github_activity
        |
        +--> Qdrant (RAG read)
        +--> OpenAI (LLM + embeddings)
        +--> GitHub API (repo + branch + PR)
        +--> logs/shadow + logs/metrics
```

### 1.2 Point cle sur ta requete "Todo app avec Clerk"

- Le chemin **n8n actuel** ne lance pas `TodoPilotWorkflow`, il lance `SaaSFactoryWorkflow` via `POST /start-saas`.
  - n8n -> API: `factory-sprint0/workflow.json:22-26`
  - API -> workflow SaaS: `factory-sprint0/api/flask_api.py:31-36`
- Le chemin `TodoPilotWorkflow` est demarre par `scripts/run_batch.py`.
  - `factory-sprint0/scripts/run_batch.py:65-70`

### 1.3 Technologies critiques

- Orchestration: Temporal (`temporalio`)
- API: Flask
- LLM: OpenAI (ChatOpenAI + OpenAIEmbeddings)
- RAG: Qdrant + LangChain retriever
- SCM: GitHub API (PyGithub)
- Agent graph: LangGraph
- Validation contrats: JSON Schema (`jsonschema`)

## 2) Flux de donnees complet (Partie 2)

## Etape 1 - n8n webhook recoit

- Fichier responsable: `factory-sprint0/workflow.json:1`
- Entree webhook:
  - Node Webhook: `factory-sprint0/workflow.json:4-17`
  - Path: `start-saas`
- Transformation:
  - n8n construit body JSON vers API: `{"phrase": $json.body.phrase || "SaaS inconnu"}`
  - `factory-sprint0/workflow.json:25`
  - `project_name` n'est pas envoye par n8n (API le genere si absent)
- Appel suivant:
  - HTTP POST `http://factory-worker:5000/start-saas`
  - `factory-sprint0/workflow.json:22`
- Gestion erreurs:
  - Node IF sur presence du champ `message`
  - success response: `factory-sprint0/workflow.json:57-69`
  - error response: `factory-sprint0/workflow.json:72-84`

## Etape 2 - Temporal workflow demarre

### Chemin A (n8n/API)

- Fichier responsable: `factory-sprint0/api/flask_api.py:27`
- Workflow type: `SaaSFactoryWorkflow`
  - demarrage: `factory-sprint0/api/flask_api.py:31-36`
- Parametres passes:
  - `{"phrase": phrase, "project_name": project_name}`
  - validation minimale API: `phrase` obligatoire (`factory-sprint0/api/flask_api.py:58-59`)
- Erreurs:
  - exception -> HTTP 500 JSON `Impossible de demarrer le workflow...`
  - `factory-sprint0/api/flask_api.py:77-78`

### Chemin B (batch TodoPilot)

- Fichier responsable: `factory-sprint0/scripts/run_batch.py:54`
- Workflow type: `TodoPilotWorkflow`
  - demarrage: `factory-sprint0/scripts/run_batch.py:65-70`
- Parametres:
  - `{"phrase": ..., "project_name": ...}`
- Erreurs:
  - timeout par run (`asyncio.wait_for`) `factory-sprint0/scripts/run_batch.py:73-83`
  - erreurs serialisees dans `runs[].error`

### Worker d'execution Temporal

- Fichier: `factory-sprint0/run/worker.py:36-52`
- Register:
  - Workflows: `SaaSFactoryWorkflow`, `TodoPilotWorkflow`
  - Activities: architect/dev_test/qa/github
- Queue: `factory-task-queue` (`factory-sprint0/run/worker.py:33`)

## Etape 3 - Activities sequentielles

## 3.1 `architect_activity`

- Fichier: `factory-sprint0/workflows/activities/architect_activity.py:37`
- Input attendu:
  - contrat `architect_agent.input_schema`: `phrase` requis, `project_name` optionnel
  - `factory-sprint0/schemas/contracts/architect_agent_contract.json:8-27`
- Validation:
  - `validate_input("architect_agent", input_data)`
  - `factory-sprint0/workflows/activities/architect_activity.py:48`
- Traitement:
  - charge agent architect (`create_architect_agent`)
  - `factory-sprint0/workflows/activities/architect_activity.py:57-58`
  - initialise state LangGraph puis `ainvoke`
  - `factory-sprint0/workflows/activities/architect_activity.py:70-80`
- Sortie:
  - `{"specification": str, "mermaid_diagram": str}`
  - `factory-sprint0/workflows/activities/architect_activity.py:86-93`
  - valide output schema `architect_agent`
  - `factory-sprint0/workflows/activities/architect_activity.py:107`
- Appels externes:
  - OpenAI embeddings + ChatOpenAI
  - `factory-sprint0/agents/architect.py:83,89,93`
  - Qdrant retriever k=10
  - `factory-sprint0/agents/architect.py:90-93`
- Gestion erreurs:
  - manque OPENAI key -> `ApplicationError("MISSING_CONFIGURATION")`
  - `factory-sprint0/workflows/activities/architect_activity.py:44-45`
  - erreurs import/init/execution -> `ApplicationError` codes dedies
  - `factory-sprint0/workflows/activities/architect_activity.py:61,68,116`
  - guard Clerk (patterns interdits) -> `SPEC_NOT_CLERK_COMPLIANT`
  - `factory-sprint0/workflows/activities/architect_activity.py:95-104`

## 3.2 `dev_test_activity`

- Fichier: `factory-sprint0/workflows/activities/dev_test_activity.py:52`
- Input attendu:
  - contrat `dev_test_agent.input_schema`: `spec`, `mermaid`, `project_name`
  - `factory-sprint0/schemas/contracts/dev_test_agent_contract.json:7-15`
- Validation:
  - `validate_input("dev_test_agent", input_data)`
  - `factory-sprint0/workflows/activities/dev_test_activity.py:73`
- Traitement:
  - appelle `dev_test_agent(input_data)` (wrapper fusion Dev+Test)
  - `factory-sprint0/workflows/activities/dev_test_activity.py:77,85`
- Sortie:
  - valide `dev_test_agent.output_schema`
  - `factory-sprint0/workflows/activities/dev_test_activity.py:91`
  - payload principal:
    - `dev_output`, `test_output`, `combined_files`, `success`, `metadata`
    - schema: `factory-sprint0/schemas/contracts/dev_test_agent_contract.json:17-48`
- Tools utilises (indirectement via Dev + Test agents):
  - Dev: `write_file`, `validate_syntax`, `prisma_migrate`, `rag_search`, `read_files`, `run_build`
  - `factory-sprint0/agents/dev.py:10-17,34`
  - Test coverage: `run_tests` (avec ecriture fichiers)
  - `factory-sprint0/agents/test_coverage.py:8,151`
- Appels externes:
  - OpenAI (Dev + TestCoverage): `factory-sprint0/agents/dev.py:32`, `factory-sprint0/agents/test_coverage.py:123`
  - Qdrant via `rag_search` (Dev): `factory-sprint0/agents/shared_tools.py:170-191`
  - subprocess npm/npx/prisma/jest/eslint: `factory-sprint0/agents/shared_tools.py:262-863`
- Logs learner shadow:
  - `_write_learner_event(..., metric="dev_test_run", ...)`
  - `factory-sprint0/workflows/activities/dev_test_activity.py:38-47`
- Gestion erreurs:
  - exceptions -> `ApplicationError("DEV_TEST_EXECUTION_FAILED")`
  - `factory-sprint0/workflows/activities/dev_test_activity.py:149-152`
  - finally: log metric, meme en erreur
  - `factory-sprint0/workflows/activities/dev_test_activity.py:153-154`

## 3.3 `qa_activity`

- Fichier: `factory-sprint0/workflows/activities/qa_activity.py:27`
- Input attendu:
  - contrat `qa_agent.input_schema`: `specification`, `project_name`
  - `factory-sprint0/schemas/contracts/qa_agent_contract.json:8-22`
- Validation:
  - `validate_input("qa_agent", input_data)`
  - `factory-sprint0/workflows/activities/qa_activity.py:33`
- Traitement:
  - cree agent QA LangGraph puis `ainvoke`
  - `factory-sprint0/workflows/activities/qa_activity.py:47-58`
  - parse dernier message en JSON ou fallback fichier unique
  - `factory-sprint0/workflows/activities/qa_activity.py:65-77`
- Sortie:
  - `{"e2e_tests": {path: content}}`
  - `factory-sprint0/workflows/activities/qa_activity.py:80`
  - validation output schema
  - `factory-sprint0/workflows/activities/qa_activity.py:81`
- Appels externes:
  - OpenAI Chat model: `factory-sprint0/agents/qa.py:72-76`
  - pas de Qdrant dans QA actuel
- Logs learner shadow:
  - metric `qa_run` via `_write_learner_event`
  - `factory-sprint0/workflows/activities/qa_activity.py:13-23`
- Gestion erreurs:
  - exceptions -> `ApplicationError("QA_EXECUTION_FAILED")`
  - `factory-sprint0/workflows/activities/qa_activity.py:98`

## 3.4 `github_activity`

- Fichier: `factory-sprint0/workflows/activities/github_activity.py:16`
- Input attendu:
  - contrat `github_agent.input_schema`: `files`, `project_name`
  - `factory-sprint0/schemas/contracts/github_agent_contract.json:8-25`
- Validation:
  - `validate_input("github_agent", input_data)`
  - `factory-sprint0/workflows/activities/github_activity.py:22`
- Traitement:
  - auth GitHub token
  - `factory-sprint0/workflows/activities/github_activity.py:33-43`
  - create/get repo
  - branch `dev`
  - push/update files
  - create/reuse PR
  - `factory-sprint0/workflows/activities/github_activity.py:47-142`
- Sortie:
  - `{"pr_url": str, "repo_url": str}`
  - validation output schema
  - `factory-sprint0/workflows/activities/github_activity.py:145`
- Appels externes:
  - GitHub API (PyGithub)
- Gestion erreurs:
  - MISSING_CONFIGURATION si token absent
  - codes `REPO_CREATION_FAILED`, `FILE_PUSH_FAILED`, `GITHUB_ACTIVITY_FAILED`, etc.
  - `factory-sprint0/workflows/activities/github_activity.py:35,61,125,151`

## Etape 4 - Logging et metriques

- Logs execution workflow/activity:
  - logs Python stdout/stderr (worker/API), ex. `logging.basicConfig` worker
  - `factory-sprint0/run/worker.py:27-31`
- JSON produits:
  - batch runs: `logs/metrics/todo_pilot_batch_*.json`
  - creation: `factory-sprint0/scripts/run_batch.py:141-149`
  - learner shadow log: `logs/shadow/learner_shadow_log.json`
  - ecriture: `factory-sprint0/agents/shared_tools.py:872-899`
  - patterns report: `logs/shadow/patterns_report.json`
  - ecriture: `factory-sprint0/agents/evaluator.py:236-241`
  - qdrant enrichment metrics: `logs/metrics/qdrant_enrichment_*.json`
  - ecriture: `factory-sprint0/scripts/enrich_qdrant.py:48-55`
- LearnerAgent shadow lit quoi exactement:
  - l'evaluator lit `logs/shadow/learner_shadow_log.json` (`suggested_standards` puis fallback `events`)
  - `factory-sprint0/agents/evaluator.py:27,42-47,138-145`

## 3) Contrats entre composants (Partie 3)

## 3.1 Contrats Temporal (activities)

- `architect_activity`
  - defini: `factory-sprint0/schemas/contracts/architect_agent_contract.json:8-58`
  - utilise: `factory-sprint0/workflows/activities/architect_activity.py:48,107`
  - validation: JSON Schema via `jsonschema.validate`
  - moteur: `factory-sprint0/scripts/validate_contracts.py:67-124`

- `dev_test_activity`
  - defini: `factory-sprint0/schemas/contracts/dev_test_agent_contract.json:7-48`
  - utilise: `factory-sprint0/workflows/activities/dev_test_activity.py:73,91`
  - validation: JSON Schema runtime

- `qa_activity`
  - defini: `factory-sprint0/schemas/contracts/qa_agent_contract.json:8-37`
  - utilise: `factory-sprint0/workflows/activities/qa_activity.py:33,81`
  - validation: JSON Schema runtime

- `github_activity`
  - defini: `factory-sprint0/schemas/contracts/github_agent_contract.json:8-43`
  - utilise: `factory-sprint0/workflows/activities/github_activity.py:22,145`
  - validation: JSON Schema runtime

## 3.2 Contrats Agents/Tools

- Outils DevAgent en production (liste reelle):
  - `write_file`, `validate_syntax`, `prisma_migrate`, `rag_search`, `read_files`, `run_build`
  - `factory-sprint0/agents/dev.py:34`
- Schémas parametres tools (Pydantic args_schema):
  - `WriteFileArgs`: `factory-sprint0/agents/shared_tools.py:196-199`
  - `ValidateSyntaxArgs`: `factory-sprint0/agents/shared_tools.py:258-260`
  - `PrismaMigrateArgs`: `factory-sprint0/agents/shared_tools.py:314-316`
  - `ReadFileArgs`: `factory-sprint0/agents/shared_tools.py:403-405`
  - `RunBuildArgs`: `factory-sprint0/agents/shared_tools.py:425-427`
  - `RunTestsArgs`: `factory-sprint0/agents/shared_tools.py:483-486`
- Format retours tools:
  - tous les tools retournent `str` (status ou erreur detaillee)
  - ex `write_file`: `factory-sprint0/agents/shared_tools.py:201-257`
  - ex `run_build`: `factory-sprint0/agents/shared_tools.py:429-482`
  - ex `run_tests`: `factory-sprint0/agents/shared_tools.py:488-863`
- Validation:
  - Tool args validates par LangChain + Pydantic (`@tool(args_schema=...)`)
  - pas de Pydantic global sur outputs tools (string libre)

## 3.3 Contrats Qdrant

- Collection:
  - nom: `factory_standards`
  - `factory-sprint0/config/factory_config.py:5`
  - init collection vector size 3072 cosine:
  - `factory-sprint0/init_qdrant.py:80-83`
- Payload structure (upsert initial):
  - `{"text": text, "metadata": metadata}`
  - `factory-sprint0/scripts/populate_qdrant.py:275-281`
- Query format:
  - via LangChain retriever similarity top-k
  - `shared_tools.rag_search` query string -> retriever `k=DEFAULT_VECTOR_SEARCH_LIMIT`
  - `factory-sprint0/agents/shared_tools.py:171-187`
  - Architect retriever k=10
  - `factory-sprint0/agents/architect.py:92`
- Response format:
  - `rag_search` retourne string concatenee des `doc.page_content`
  - `factory-sprint0/agents/shared_tools.py:187`
  - Architect retrieval retourne liste docs puis string `rag_context`
  - `factory-sprint0/agents/architect.py:99-105`

## 3.4 Contrats Logs/Metrics

- `learner_shadow_log.json`
  - structure observee: meta top-level + `suggested_standards[]`
  - sample: `factory-sprint0/logs/shadow/learner_shadow_log.json:1-13`
  - event schema pratique: `{timestamp, project_name, metric, value, success}`
  - `factory-sprint0/agents/shared_tools.py:887-894`
- `todo_pilot_batch_*.json`
  - schema runtime ecrit par `run_batch.py`
  - `factory-sprint0/scripts/run_batch.py:128-139`
  - sample fichier: `factory-sprint0/logs/metrics/todo_pilot_batch_20260217T024430Z.json:1-27`
- `patterns_report.json`
  - genere par EvaluatorAgent
  - mapping: `generated_at, log_source, total_runs, avg_quality_score, global_failure_rate, patterns[]...`
  - code: `factory-sprint0/agents/evaluator.py:216-234`
  - sample: `factory-sprint0/logs/shadow/patterns_report.json:1-42`
- Validation:
  - pas de JSON schema runtime applique a ces logs
  - structure imposee par code d'ecriture

## 4) Points d'entree et configuration (Partie 4)

## 4.1 Points d'entree possibles

- Lancer worker Temporal:
  - `python run/worker.py`
  - fichier: `factory-sprint0/run/worker.py:68-75`
- Lancer workflow via API:
  - `POST /start-saas` (`api/flask_api.py`)
  - `factory-sprint0/api/flask_api.py:52-78`
- Lancer workflow TodoPilot batch:
  - `python scripts/run_batch.py`
  - `factory-sprint0/scripts/run_batch.py:169-179`
- n8n webhook:
  - import `workflow.json` dans n8n, webhook path `start-saas`
  - `factory-sprint0/workflow.json:4-7`
  - route vers API: `factory-sprint0/workflow.json:22`

## 4.2 Configuration systeme

- Parametres centraux:
  - `factory-sprint0/config/factory_config.py:3-19`
  - Qdrant URL/collection, embedding model, k default, timeouts, temporal address
- Variables env utilisees par le code:
  - `OPENAI_API_KEY` (architect/qa/populate)
  - `GITHUB_TOKEN` (github activity)
  - `QDRANT_URL` (config/init/populate/enrich)
  - `TEMPORAL_ADDRESS` (worker/api/run_batch)
  - `MERMAID_TMP_DIR` (architect diagrammer)
  - references: 
    - `factory-sprint0/workflows/activities/architect_activity.py:44-45`
    - `factory-sprint0/workflows/activities/github_activity.py:33-35`
    - `factory-sprint0/run/worker.py:37`
    - `factory-sprint0/api/flask_api.py:19,29`
    - `factory-sprint0/agents/architect.py:155`
- Docker compose services/roles:
  - Elasticsearch: `factory-sprint0/docker-compose.yml:5-24`
  - PostgreSQL: `factory-sprint0/docker-compose.yml:29-47`
  - Temporal server: `factory-sprint0/docker-compose.yml:52-82`
  - Temporal UI: `factory-sprint0/docker-compose.yml:87-100`
  - n8n: `factory-sprint0/docker-compose.yml:104-119`
  - Qdrant: `factory-sprint0/docker-compose.yml:124-132`
  - factory-worker (API + worker): `factory-sprint0/docker-compose.yml:137-161`

## 4.3 Dependances critiques

- Qdrant
  - consulte par Architect (retriever k=10) et Dev via `rag_search` (k default 5)
  - `factory-sprint0/agents/architect.py:92`
  - `factory-sprint0/agents/shared_tools.py:185`
- OpenAI API
  - Architect: embeddings + gpt-4o
  - `factory-sprint0/agents/architect.py:89,93`
  - Dev: gpt-4o-mini
  - `factory-sprint0/agents/dev.py:32`
  - QA: gpt-4o
  - `factory-sprint0/agents/qa.py:72-75`
  - Test coverage: gpt-4o
  - `factory-sprint0/agents/test_coverage.py:123`
  - Enrich/populate/init Qdrant: embeddings model
- GitHub API
  - auth par token perso `GITHUB_TOKEN`
  - `factory-sprint0/workflows/activities/github_activity.py:33-43`
  - rate-limit: pas de gestion explicite code (pas de backoff custom)

## 5) Prompts et RAG (Partie 5)

## 5.1 Systeme de prompts

- `prompts/architect.md`
  - charge via parser sections `# Planner/#Spec Writer/#Diagrammer`
  - `factory-sprint0/agents/architect.py:52-73`
- `prompts/dev.md`
  - charge via utilitaire central `load_prompt("dev")`
  - `factory-sprint0/agents/dev.py:18,133`
  - loader: `factory-sprint0/utils/prompt_loader.py:6-25`
- `prompts/qa.md`
  - charge directement par lecture fichier dans `qa_agent_node`
  - `factory-sprint0/agents/qa.py:61-63`
  - `prompt_loader.py` n'est pas utilise pour QA

## 5.2 Architecture RAG

- Quand un agent appelle `rag_search`:
  - DevAgent via tool-calling (instruction obligatoire dans prompt + human message)
  - `factory-sprint0/prompts/dev.md:6-23`
  - `factory-sprint0/agents/dev.py:140`
- Quel agent fait quel type de requete:
  - Architect: retrieval direct sur requete utilisateur (pas via tool)
  - `factory-sprint0/agents/architect.py:96-105`
  - Dev: tool `rag_search(query)` orientee versions/config
  - `factory-sprint0/agents/shared_tools.py:171-191`
- Injection des resultats:
  - Architect: injecte `rag_context` dans planner input
  - `factory-sprint0/agents/architect.py:107`
  - Dev: sortie tool devient `ToolMessage` dans historique LLM
  - `factory-sprint0/agents/dev.py:217-247`
- `k=5` configuration:
  - central: `DEFAULT_VECTOR_SEARCH_LIMIT = 5`
  - `factory-sprint0/config/factory_config.py:14`
  - usage: `shared_tools.rag_search` -> `k=DEFAULT_VECTOR_SEARCH_LIMIT`
  - `factory-sprint0/agents/shared_tools.py:185`
  - par agent: Architect override `k=10`
  - `factory-sprint0/agents/architect.py:92`

## 5.3 Layered architecture (Code -> Prompt -> RAG)

- Code (regles dures)
  - validations JSON schema input/output en activities
  - `factory-sprint0/workflows/activities/*.py`
  - guard anti auth custom dans architect activity + spec checker
  - `factory-sprint0/workflows/activities/architect_activity.py:12-33,95-104`
  - patchs defensifs tool layer (middleware matcher, package sanitize)
  - `factory-sprint0/agents/shared_tools.py:220-245,105-168`
- Prompt (instructions)
  - contraintes Clerk-only dans prompts architect/dev
  - `factory-sprint0/prompts/architect.md:1-7`
  - `factory-sprint0/prompts/dev.md:17-23`
- RAG (standards techniques)
  - base `factory_standards` peuplee via `scripts/populate_qdrant.py`
  - payload text+metadata par categorie
  - `factory-sprint0/scripts/populate_qdrant.py:33-281`
- Decision de consulter RAG
  - Architect: toujours retrieval node en debut
  - `factory-sprint0/agents/architect.py:232-234`
  - Dev: encourage/force par prompt et message initial, mais execution depend de tool-calling LLM

## 6) Details techniques par composant

## Agents

- Architect Agent
  - role: plan/spec/diagram
  - input state: message user + rag_context
  - output: `ArchitectOutput` (Pydantic)
  - `factory-sprint0/agents/architect.py:39-50`
- Dev Agent
  - role: generation iterative + build fix loop
  - output: `files`, `final_message`, `success`, metadata
  - `factory-sprint0/agents/dev.py:352-364`
- TestCoverage Agent
  - role: generation tests + execution `run_tests`
  - output: `{tests: ...}`
  - `factory-sprint0/agents/test_coverage.py:175-218`
- QA Agent
  - role: generation E2E Playwright content
  - output via dernier message LLM

## Workflows

- Orchestration sequentielle (architect -> dev_test -> qa -> github)
  - TodoPilot: `factory-sprint0/workflows/todo_pilot_workflow.py:65-123`
  - SaaSFactory: `factory-sprint0/workflows/factory_workflow.py:62-132`
- Error handling
  - retry policy activities (3 tentatives)
  - `factory-sprint0/workflows/todo_pilot_workflow.py:57-61`
  - catch global -> output `FAILED_UNRECOVERABLE`
  - `factory-sprint0/workflows/todo_pilot_workflow.py:142-156`

## RAG

- Population initiale: `scripts/populate_qdrant.py`
- Query runtime: `shared_tools.rag_search` + architect retriever
- Injection: context planner (architect) + ToolMessages (dev)
- Enrichissement post-run: evaluator -> `patterns_report` -> `scripts/enrich_qdrant.py`

## Logs

- Ecriture shadow events: `shared_tools._write_learner_event`
- Lecture/aggregation: `agents/evaluator.py`
- Batch metrics runs: `scripts/run_batch.py`

## 7) Points d'attention (couplages, dead code, incoherences)

- Couplage fort n8n/API/workflow:
  - n8n lance SaaSFactory, pas TodoPilot.
  - pour un flux Todo direct depuis n8n, il faut nouvel endpoint/workflow mapping.
- Couplage fort a OpenAI/Qdrant:
  - si vectorstore non init, `rag_search` degrade en string d'erreur.
  - `factory-sprint0/agents/shared_tools.py:180-194`
- Dead code potentiel / dette:
  - `utils/prompt_loader.py` utilise par Dev seulement, pas par Architect/QA.
  - `agents_config.yaml` reference des timeouts/flags peu exploites dans code runtime.
  - `run_tests` tool n'est pas dans tools de `dev_agent`, seulement dans `test_coverage_agent`.
- Incoherences detectees:
  - `workflow.json` n'envoie pas `project_name`, API le genere.
  - `todo` path principal et `saas` path coexistent, naming pas aligne.
  - `populate_qdrant.py` contient des blocs "commentaires de patch" inclus dans la liste `STANDARDS` (qualite de corpus a surveiller).
- Risque securite critique:
  - `.env` contient des secrets sensibles en clair (`OPENAI_API_KEY`, `GITHUB_TOKEN`).
  - `factory-sprint0/.env:13-15`

## 8) Reponse directe a tes questions cle

- `run/worker.py` ou `scripts/run_batch.py` pour demarrer Temporal ?
  - `run/worker.py`: **execute le worker** (consomme la queue).
  - `scripts/run_batch.py`: **demarre des workflows TodoPilot** (client starter + metrics).
- n8n webhook connecte comment ?
  - webhook n8n -> HTTP node -> Flask `/start-saas` -> Temporal `SaaSFactoryWorkflow`.
- Learner shadow lit quoi ?
  - `agents/evaluator.py` lit `logs/shadow/learner_shadow_log.json`, surtout `suggested_standards[]`.

---
Document genere a partir du code source courant avec references fichier/ligne.
