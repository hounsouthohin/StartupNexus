(.venv) PS C:\Users\BAMBARA Arthur\Desktop\StartupNexus\factory-sprint0> docker compose logs factory-worker                                                      
factory-worker  | Port 6333 on host qdrant is now available.                              
factory-worker  | 2026-04-16 19:20:57,972 | __main__               | INFO    | ╔════════════════════════════════════════════════════════╗
factory-worker  | 2026-04-16 19:20:57,972 | __main__               | INFO    | ║     Software Agent Factory Worker                      ║
factory-worker  | 2026-04-16 19:20:57,972 | __main__               | INFO    | ║     Queues : main | dev | build                        ║
factory-worker  | 2026-04-16 19:20:57,972 | __main__               | INFO    | ╚════════════════════════════════════════════════════════╝
factory-worker  | 2026-04-16 19:20:57,972 | __main__               | INFO    | MAIN  (factory-task-queue)  : pipeline principal
factory-worker  | 2026-04-16 19:20:57,972 | __main__               | INFO    | DEV   (factory-dev-queue)   : generate_batch + apply_corrections
factory-worker  | 2026-04-16 19:20:57,972 | __main__               | INFO    | BUILD (factory-build-queue) : build
factory-worker  | 2026-04-16 19:20:57,972 | __main__               | INFO    | Workers en écoute... (Ctrl+C pour arrêter)
factory-worker  | 2026-04-16T19:20:57.974696Z  WARN temporalio_sdk_core::worker::heartbeat: Worker heartbeating configured for runtime, but server version does not support it.
factory-worker  | ✅ Connexion à Qdrant réussie !
factory-worker  | La collection 'factory_standards' existe déjà.
factory-worker  | 📊 La collection contient 68 standard(s).
factory-worker  | Port 7233 on host temporal is now available.
factory-worker  |  * Serving Flask app 'flask_api'
factory-worker  |  * Debug mode: off
factory-worker  | WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
factory-worker  |  * Running on all addresses (0.0.0.0)
factory-worker  |  * Running on http://127.0.0.1:5000
factory-worker  |  * Running on http://172.18.0.6:5000
factory-worker  | Press CTRL+C to quit
factory-worker  | 2026-04-16 19:35:54,185 | temporalio.workflow    | INFO    | TodoPilot démarré – Projet: task-manager | Brief: App de gestion de tâches personnelles avec Clerk (utilisateur unique). | Stack: nextjs-clerk-prisma ({'attempt': 1, 'namespace': 'default', 'run_id': '019d97ca-f614-7510-9dde-5942b8b55c3c', 'task_queue': 'factory-task-queue', 'workflow_id': 'todo-pilot-task-manager-94fbef31', 'workflow_type': 'TodoPilotWorkflow'})
factory-worker  | 2026-04-16 19:35:54,186 | temporalio.workflow    | INFO    | TodoPilot run_id=0f304d78-d445-41ad-98e8-cdacb4e3c148 ({'attempt': 1, 'namespace': 'default', 'run_id': '019d97ca-f614-7510-9dde-5942b8b55c3c', 'task_queue': 'factory-task-queue', 'workflow_id': 'todo-pilot-task-manager-94fbef31', 'workflow_type': 'TodoPilotWorkflow'})
factory-worker  | 2026-04-16 19:35:54,633 | temporalio.activity    | INFO    | Architect démarré → Projet: task-manager | Brief: App de gestion de tâches personnelles avec Clerk (utilisateur unique).... ({'activity_id': '1', 'activity_type': 'architect_activity', 'attempt': 1, 'namespace': 'default', 'task_queue': 'factory-task-queue', 'workflow_id': 'todo-pilot-task-manager-94fbef31', 'workflow_run_id': '019d97ca-f614-7510-9dde-5942b8b55c3c', 'workflow_type': 'TodoPilotWorkflow'})
factory-worker  | 2026-04-16 19:35:56,139 | httpx                  | INFO    | HTTP Request: GET http://qdrant:6333/collections "HTTP/1.1 200 OK"
factory-worker  | 2026-04-16 19:35:56,147 | httpx                  | INFO    | HTTP Request: GET http://qdrant:6333 "HTTP/1.1 200 OK"
factory-worker  | 2026-04-16 19:35:56,166 | httpx                  | INFO    | HTTP Request: GET http://qdrant:6333/collections/factory_standards "HTTP/1.1 200 OK"
factory-worker  | 2026-04-16 19:35:56,168 | httpx                  | INFO    | HTTP Request: GET http://qdrant:6333 "HTTP/1.1 200 OK"
factory-worker  | 2026-04-16 19:35:57,643 | httpx                  | INFO    | HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
factory-worker  | 2026-04-16 19:35:57,675 | agents.stack_config    | INFO    | [stack_config] Config chargée: nextjs-clerk-prisma (40 clés)
factory-worker  | 2026-04-16 19:35:58,205 | httpx                  | INFO    | HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
factory-worker  | 2026-04-16 19:35:58,229 | httpx                  | INFO    | HTTP Request: POST http://qdrant:6333/collections/factory_standards/points/query "HTTP/1.1 200 OK"
factory-worker  | 2026-04-16 19:35:58,246 | agents.architect       | INFO    | [retrieval] RAG: 10 standards retenus (query: 'App de gestion de tâches personnelles avec Clerk (utilisateur unique).')
factory-worker  | 2026-04-16 19:35:58,262 | agents.architect       | INFO    | [planner] ProjectSpec déterministe — 1 modèles, 2 pages, 2 routes | fingerprint=982e119a0aa416c6
factory-worker  | 2026-04-16 19:35:58,262 | temporalio.activity    | INFO    | [architect] project_spec.json écrit — fingerprint=982e119a0aa416c6 | 1 modèles | 2 pages | 2 routes ({'activity_id': '1', 'activity_type': 'architect_activity', 'attempt': 1, 'namespace': 'default', 'task_queue': 'factory-task-queue', 'workflow_id': 'todo-pilot-task-manager-94fbef31', 'workflow_run_id': '019d97ca-f614-7510-9dde-5942b8b55c3c', 'workflow_type': 'TodoPilotWorkflow'})
factory-worker  | 2026-04-16 19:35:58,273 | temporalio.activity    | INFO    | Architect terminé → ProjectSpec | 5 requirements | spec_validation=OK | fingerprint=982e119a0aa416c6 ({'activity_id': '1', 'activity_type': 'architect_activity', 'attempt': 1, 'namespace': 'default', 'task_queue': 'factory-task-queue', 'workflow_id': 'todo-pilot-task-manager-94fbef31', 'workflow_run_id': '019d97ca-f614-7510-9dde-5942b8b55c3c', 'workflow_type': 'TodoPilotWorkflow'})
factory-worker  | 2026-04-16 19:35:58,290 | temporalio.workflow    | INFO    | Architect terminé — 5 requirements | spec_validation=OK ({'attempt': 1, 'namespace': 'default', 'run_id': '019d97ca-f614-7510-9dde-5942b8b55c3c', 'task_queue': 'factory-task-queue', 'workflow_id': 'todo-pilot-task-manager-94fbef31', 'workflow_type': 'TodoPilotWorkflow'})
factory-worker  | 2026-04-16 19:35:58,290 | temporalio.workflow    | INFO    | [PARALLEL_MODE] run_mode=inline ({'attempt': 1, 'namespace': 'default', 'run_id': '019d97ca-f614-7510-9dde-5942b8b55c3c', 'task_queue': 'factory-task-queue', 'workflow_id': 'todo-pilot-task-manager-94fbef31', 'workflow_type': 'TodoPilotWorkflow'})
factory-worker  | 2026-04-16 19:35:58,303 | temporalio.activity    | INFO    | DevTest démarré → Projet: task-manager ({'activity_id': '2', 'activity_type': 'dev_test_activity', 'attempt': 1, 'namespace': 'default', 'task_queue': 'factory-task-queue', 'workflow_id': 'todo-pilot-task-manager-94fbef31', 'workflow_run_id': '019d97ca-f614-7510-9dde-5942b8b55c3c', 'workflow_type': 'TodoPilotWorkflow'})
factory-worker  | 2026-04-16 19:35:59,907 | agents.dev_graph       | INFO    | [dev_graph] résidu racine supprimé : /app/generated-projects/project_spec_task-manager.json
factory-worker  | 2026-04-16 19:35:59,908 | agents.dev_graph       | INFO    | [dev_graph] workdir isolé : /app/generated-projects/task-manager
factory-worker  | 2026-04-16 19:35:59,946 | agents.dev_file_ops    | INFO    | [templates] ✓ package.json écrit depuis template
factory-worker  | 2026-04-16 19:35:59,966 | agents.dev_file_ops    | INFO    | [templates] ✓ middleware.ts écrit depuis template
factory-worker  | 2026-04-16 19:35:59,988 | agents.dev_file_ops    | INFO    | [templates] ✓ app/layout.tsx écrit depuis template
factory-worker  | 2026-04-16 19:36:00,020 | agents.dev_file_ops    | INFO    | [templates] ✓ app/globals.css écrit depuis template
factory-worker  | 2026-04-16 19:36:00,045 | agents.dev_file_ops    | INFO    | [templates] ✓ jest.config.js écrit depuis template
factory-worker  | 2026-04-16 19:36:00,073 | agents.dev_file_ops    | INFO    | [templates] ✓ jest.setup.js écrit depuis template
factory-worker  | 2026-04-16 19:36:00,102 | agents.dev_file_ops    | INFO    | [templates] ✓ next.config.js écrit depuis template
factory-worker  | 2026-04-16 19:36:00,122 | agents.dev_file_ops    | INFO    | [templates] ✓ .eslintrc.stack.json écrit depuis template
factory-worker  | 2026-04-16 19:36:00,140 | agents.dev_file_ops    | INFO    | [templates] ✓ tsconfig.json écrit depuis template
factory-worker  | 2026-04-16 19:36:00,152 | agents.dev_file_ops    | INFO    | [templates] ✓ .env.local écrit depuis template
factory-worker  | 2026-04-16 19:36:00,171 | agents.dev_file_ops    | INFO    | [templates] ✓ tests/middleware.test.ts écrit depuis template
factory-worker  | 2026-04-16 19:36:00,188 | agents.dev_file_ops    | INFO    | [templates] ✓ lib/prisma.ts écrit depuis template
factory-worker  | 2026-04-16 19:36:00,204 | agents.dev_file_ops    | INFO    | [templates] ✓ prisma.config.ts écrit depuis template
factory-worker  | 2026-04-16 19:36:00,221 | agents.dev_file_ops    | INFO    | [templates] ✓ prisma/schema.prisma écrit depuis template
factory-worker  | 2026-04-16 19:36:00,222 | agents.dev_graph       | INFO    | [dev_graph] 14 fichiers pré-générés depuis templates : ['package.json', 'middleware.ts', 'app/layout.tsx', 'app/globals.css', 'jest.config.js', 'jest.setup.js', 'next.config.js', '.eslintrc.stack.json', 'tsconfig.json', '.env.local', 'tests/middleware.test.ts', 'lib/prisma.ts', 'prisma.config.ts', 'prisma/schema.prisma']
factory-worker  | 2026-04-16 19:36:00,222 | agents.dev_graph       | INFO    | [dev_graph] schema.prisma matérialisé depuis ProjectSpec (1 modèles)
factory-worker  | 2026-04-16 19:36:00,226 | agents.dev_types_generator | INFO    | [types_generator] ✓ lib/types.ts généré — 1 modèles, 2 types Input, 0 pages dynamiques
factory-worker  | 2026-04-16 19:36:00,226 | agents.dev_graph       | INFO    | [dev_graph] lib/types.ts généré — modèles: ['Task'], input types: ['CreateTaskInput', 'UpdateTaskInput']
factory-worker  | 2026-04-16 19:36:00,227 | agents.dev_graph       | INFO    | [dev_graph] npm install pre-run dans /app/generated-projects/task-manager ...
factory-worker  | 2026-04-16 19:37:00,592 | agents.dev_graph       | INFO    | [dev_graph] npm install pre-run OK
factory-worker  | 2026-04-16 19:37:00,593 | agents.dev_graph       | INFO    | [dev_graph] prisma generate pre-run dans /app/generated-projects/task-manager ...
factory-worker  | 2026-04-16 19:37:01,832 | agents.dev_graph       | INFO    | [dev_graph] prisma generate pre-run OK
factory-worker  | 2026-04-16 19:37:01,860 | agents.dev_graph       | INFO    | [dev_graph] System prompt chargé depuis dev_prompts.py
factory-worker  | 2026-04-16 19:37:01,861 | agents.dev_graph       | INFO    | [dev_graph] 6 outils : ['write_file', 'read_file', 'list_directory', 'shell_exec', 'file_exists', 'rag_search']
factory-worker  | 2026-04-16 19:37:12,026 | httpx                  | INFO    | HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
factory-worker  | 2026-04-16 19:37:12,039 | agents.dev_graph       | INFO    | [file_validate] Fichiers TS écrits ce tour : ['app/api/tasks/[id]/route.ts', 'app/new/page.tsx', 'app/page.tsx']
factory-worker  | 2026-04-16 19:37:13,877 | agents.dev_graph       | WARNING | [file_validate] TS errors dans fichiers écrits (retry 1/2) : ['app/api/tasks/[id]/route.ts', 'app/new/page.tsx', 'app/page.tsx']
factory-worker  | 2026-04-16 19:37:15,876 | httpx                  | INFO    | HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
factory-worker  | 2026-04-16 19:37:16,902 | httpx                  | INFO    | HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
factory-worker  | 2026-04-16 19:37:19,593 | httpx                  | INFO    | HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
factory-worker  | 2026-04-16 19:37:23,804 | httpx                  | INFO    | HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
factory-worker  | 2026-04-16 19:37:25,506 | httpx                  | INFO    | HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
factory-worker  | 2026-04-16 19:37:25,512 | agents.dev_graph       | WARNING | [dev_graph] MAX_BUILD_ATTEMPTS=3 atteint — arrêt boucle correction
factory-worker  | 2026-04-16 19:37:25,513 | agents.dev_graph       | INFO    | [dev_graph] terminé — success=False | build_executed=True | build_exit_code=1 | build_attempts=3 | .next/=False | workdir=/app/generated-projects/task-manager
factory-worker  | 2026-04-16 19:37:25,517 | temporalio.activity    | INFO    | [dev_graph] 19 fichiers lus depuis /app/generated-projects/task-manager ({'activity_id': '2', 'activity_type': 'dev_test_activity', 'attempt': 1, 'namespace': 'default', 'task_queue': 'factory-task-queue', 'workflow_id': 'todo-pilot-task-manager-94fbef31', 'workflow_run_id': '019d97ca-f614-7510-9dde-5942b8b55c3c', 'workflow_type': 'TodoPilotWorkflow'})
factory-worker  | 2026-04-16 19:37:27,030 | temporalio.activity    | INFO    | [TSC_ACTIVITY] ran=True ok=False errors=2 ({'activity_id': '2', 'activity_type': 'dev_test_activity', 'attempt': 1, 'namespace': 'default', 'task_queue': 'factory-task-queue', 'workflow_id': 'todo-pilot-task-manager-94fbef31', 'workflow_run_id': '019d97ca-f614-7510-9dde-5942b8b55c3c', 'workflow_type': 'TodoPilotWorkflow'})
factory-worker  | 2026-04-16 19:37:27,044 | agents.journey_validator | INFO    | [journey_validator] 3/3 flows couverts (100%) — is_useful_app=True (seuil=60%, unresolvable=1)
factory-worker  | 2026-04-16 19:37:28,134 | temporalio.activity    | INFO    | [PRISMA_VALIDATE] ran=True ok=True schema=prisma/schema.prisma ({'activity_id': '2', 'activity_type': 'dev_test_activity', 'attempt': 1, 'namespace': 'default', 'task_queue': 'factory-task-queue', 'workflow_id': 'todo-pilot-task-manager-94fbef31', 'workflow_run_id': '019d97ca-f614-7510-9dde-5942b8b55c3c', 'workflow_type': 'TodoPilotWorkflow'})
factory-worker  | 2026-04-16 19:37:28,138 | temporalio.activity    | INFO    | Snapshot persisté → /app/generated-projects/snapshots/task-manager_0f304d78.json ({'activity_id': '2', 'activity_type': 'dev_test_activity', 'attempt': 1, 'namespace': 'default', 'task_queue': 'factory-task-queue', 'workflow_id': 'todo-pilot-task-manager-94fbef31', 'workflow_run_id': '019d97ca-f614-7510-9dde-5942b8b55c3c', 'workflow_type': 'TodoPilotWorkflow'})
factory-worker  | 2026-04-16 19:37:28,146 | temporalio.activity    | INFO    | DevTest terminé → 19 fichiers | Success: False | Violations: 0 ({'activity_id': '2', 'activity_type': 'dev_test_activity', 'attempt': 1, 'namespace': 'default', 'task_queue': 'factory-task-queue', 'workflow_id': 'todo-pilot-task-manager-94fbef31', 'workflow_run_id': '019d97ca-f614-7510-9dde-5942b8b55c3c', 'workflow_type': 'TodoPilotWorkflow'})
factory-worker  | 2026-04-16 19:37:28,169 | utils.run_report       | INFO    | [run_report] écrit → /app/logs/metrics/run_reports/run_report_0f304d78-d445-41ad-98e8-cdacb4e3c148.json
factory-worker  | 2026-04-16 19:37:28,395 | temporalio.workflow    | INFO    | DevTest terminé – Fichiers: 19, Success: False ({'attempt': 1, 'namespace': 'default', 'run_id': '019d97ca-f614-7510-9dde-5942b8b55c3c', 'task_queue': 'factory-task-queue', 'workflow_id': 'todo-pilot-task-manager-94fbef31', 'workflow_type': 'TodoPilotWorkflow'})
factory-worker  | 2026-04-16 19:37:28,395 | temporalio.workflow    | INFO    | [SANITY_MODE] Early return after dev_test_activity ({'attempt': 1, 'namespace': 'default', 'run_id': '019d97ca-f614-7510-9dde-5942b8b55c3c', 'task_queue': 'factory-task-queue', 'workflow_id': 'todo-pilot-task-manager-94fbef31', 'workflow_type': 'TodoPilotWorkflow'})
(.venv) PS C:\Users\BAMBARA Arthur\Desktop\StartupNexus\factory-sprint0> 