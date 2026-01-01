PS C:\Users\BAMBARA Arthur\Desktop\StartupNexus\factory-sprint0> docker compose logs factory-worker
factory-worker  | Port 6333 on host qdrant is now available.
factory-worker  | ✅ Connexion à Qdrant réussie !
factory-worker  | La collection 'factory_standards' existe déjà.
factory-worker  | Début de l'embedding et de l'upload des standards...
factory-worker  | ✅ 20 standards ont été injectés/mis à jour dans Qdrant ! 🚀
factory-worker  |    L'Agent Architecte peut maintenant utiliser le RAG pour des specs et diagrammes de haute qualité.
factory-worker  | Port 7233 on host temporal is now available.
factory-worker  |  * Serving Flask app 'worker'
factory-worker  |  * Debug mode: off
factory-worker  | WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
factory-worker  |  * Running on all addresses (0.0.0.0)
factory-worker  |  * Running on http://127.0.0.1:5000
factory-worker  |  * Running on http://172.18.0.8:5000
factory-worker  | Press CTRL+C to quit
factory-worker  | 2026-01-01T01:53:51.640534Z  WARN temporalio_sdk_core::worker::heartbeat: Worker heartbeating configured for runtime, but server version does not support it.
factory-worker  | 172.18.0.5 - - [01/Jan/2026 01:54:07] "POST /start-saas HTTP/1.1" 200 -
factory-worker  | Worker + API Flask démarrés – prêts 🚀
factory-worker  | Test : POST http://localhost:5000/start-saas avec {'phrase': 'crée un SaaS de gestion de tâches'}
factory-worker  | [DISPATCH] Démarrage workflow pour : cree-moi-un-site-web-simple-avec-authentification
factory-worker  | RAG Context for Planner:
factory-worker  | --- STANDARD 1 (security) ---
factory-worker  | 
factory-worker  | 
factory-worker  | --- STANDARD 2 (security) ---
factory-worker  | 
factory-worker  | 
factory-worker  | --- STANDARD 3 (architecture) ---
factory-worker  | 
factory-worker  | 
factory-worker  | --- STANDARD 4 (ui) ---
factory-worker  | 
factory-worker  |
factory-worker  | --- STANDARD 5 (security) ---
factory-worker  |
factory-worker  |
factory-worker  | --- STANDARD 6 (backend) ---
factory-worker  |
factory-worker  |
factory-worker  | --- STANDARD 7 (structure) ---
factory-worker  |
factory-worker  |
factory-worker  | --- STANDARD 8 (frontend) ---
factory-worker  |
factory-worker  |
factory-worker  | --- STANDARD 9 (security) ---
factory-worker  |
factory-worker  |
factory-worker  | --- STANDARD 10 (testing) ---
factory-worker  |
factory-worker  | --- END RAG CONTEXT ---
factory-worker  | [INFO] Starting Dev Agent process.
factory-worker  | [INFO] Dev Agent: Starting iteration 1
factory-worker  | [INFO] Dev Agent: Proposed writing file: package.json
factory-worker  | [WARNING] File 'package.json' already exists and will be overwritten.
factory-worker  | [INFO] Dev Agent: Starting iteration 2
factory-worker  | [INFO] Dev Agent: Tool executed successfully. Prompting to continue.
factory-worker  | [INFO] Dev Agent: Proposed writing file: jest.config.js
factory-worker  | [WARNING] File 'jest.config.js' already exists and will be overwritten.
factory-worker  | [INFO] Dev Agent: Starting iteration 3
factory-worker  | [INFO] Dev Agent: Tool executed successfully. Prompting to continue.
factory-worker  | [INFO] Dev Agent: Proposed writing file: schema.prisma
factory-worker  | [INFO] Dev Agent: Starting iteration 4
factory-worker  | [INFO] Dev Agent: Tool executed successfully. Prompting to continue.
factory-worker  | [INFO] Dev Agent: Proposed writing file: package.json
factory-worker  | [INFO] Dev Agent: Proposed writing file: jest.config.js
factory-worker  | [INFO] Dev Agent: Proposed writing file: schema.prisma
factory-worker  | [WARNING] File 'package.json' already exists and will be overwritten.
factory-worker  | [WARNING] File 'jest.config.js' already exists and will be overwritten.
factory-worker  | [INFO] Dev Agent: Starting iteration 5
factory-worker  | [INFO] Dev Agent: Tool executed successfully. Prompting to continue.
factory-worker  | [INFO] Dev Agent: Proposed writing file: package.json
factory-worker  | [WARNING] File 'package.json' already exists and will be overwritten.
factory-worker  | [INFO] Dev Agent: Starting iteration 6
factory-worker  | [INFO] Dev Agent: Tool executed successfully. Prompting to continue.
factory-worker  | [INFO] Dev Agent: Proposed writing file: jest.config.js
factory-worker  | [WARNING] File 'jest.config.js' already exists and will be overwritten.
factory-worker  | [INFO] Dev Agent: Starting iteration 7
factory-worker  | [INFO] Dev Agent: Tool executed successfully. Prompting to continue.
factory-worker  | [INFO] Dev Agent: Proposed writing file: schema.prisma
factory-worker  | [INFO] Dev Agent: Starting iteration 8
factory-worker  | [INFO] Dev Agent: Tool executed successfully. Prompting to continue.
factory-worker  | [INFO] Dev Agent: Proposed writing file: app/layout.tsx
factory-worker  | [INFO] Dev Agent: Proposed writing file: middleware.ts
factory-worker  | [INFO] Dev Agent: Starting iteration 9
factory-worker  | [INFO] Dev Agent: Tool executed successfully. Prompting to continue.
factory-worker  | [INFO] Dev Agent: Proposed writing file: middleware.ts
factory-worker  | [INFO] Dev Agent: Starting iteration 10
factory-worker  | [INFO] Dev Agent: Tool executed successfully. Prompting to continue.
factory-worker  | [INFO] Dev Agent: Starting iteration 11
factory-worker  | [WARNING] Dev Agent: A tool error occurred. Entering error correction loop.
factory-worker  | [INFO] Dev Agent: Proposed writing file: schema.prisma
factory-worker  | [INFO] Dev Agent: Proposed writing file: app/layout.tsx
factory-worker  | [INFO] Dev Agent: Proposed writing file: middleware.ts
factory-worker  | [WARNING] File 'app/layout.tsx' already exists and will be overwritten.
factory-worker  | [INFO] Dev Agent: Starting iteration 12
factory-worker  | [INFO] Dev Agent: Tool executed successfully. Prompting to continue.
factory-worker  | [INFO] Dev Agent: Proposed writing file: package.json
factory-worker  | [WARNING] File 'package.json' already exists and will be overwritten.
factory-worker  | [INFO] Dev Agent: Starting iteration 13
factory-worker  | [INFO] Dev Agent: Tool executed successfully. Prompting to continue.
factory-worker  | [INFO] Dev Agent: Proposed writing file: schema.prisma
factory-worker  | [INFO] Dev Agent: Starting iteration 14
factory-worker  | [INFO] Dev Agent: Tool executed successfully. Prompting to continue.
factory-worker  | [INFO] Executing 'npm run build' in directory '.'...
factory-worker  | [ERROR] Build failed (code 1):
factory-worker  | STDOUT:
factory-worker  |
factory-worker  | STDERR:
factory-worker  | npm error Missing script: "build"
factory-worker  | npm error
factory-worker  | npm error To see a list of scripts, run:
factory-worker  | npm error   npm run
factory-worker  | npm error A complete log of this run can be found in: /root/.npm/_logs/2026-01-01T01_55_33_311Z-debug-0.log
factory-worker  |
factory-worker  | [INFO] Dev Agent: Starting iteration 15
factory-worker  | [WARNING] Dev Agent: A tool error occurred. Entering error correction loop.
factory-worker  | [INFO] Dev Agent: Proposed writing file: package.json
factory-worker  | [INFO] Dev Agent: Proposed writing file: jest.config.js
factory-worker  | [INFO] Dev Agent: Proposed writing file: schema.prisma
factory-worker  | [WARNING] File 'package.json' already exists and will be overwritten.
factory-worker  | [WARNING] File 'jest.config.js' already exists and will be overwritten.
factory-worker  | [INFO] Dev Agent: Starting iteration 16
factory-worker  | [INFO] Dev Agent: Tool executed successfully. Prompting to continue.
factory-worker  | [INFO] Dev Agent: Proposed writing file: package.json
factory-worker  | [INFO] Dev Agent: Proposed writing file: jest.config.js
factory-worker  | [INFO] Dev Agent: Proposed writing file: schema.prisma
factory-worker  | [WARNING] File 'package.json' already exists and will be overwritten.
factory-worker  | [WARNING] File 'jest.config.js' already exists and will be overwritten.
factory-worker  | [INFO] Dev Agent: Starting iteration 17
factory-worker  | [INFO] Dev Agent: Tool executed successfully. Prompting to continue.
factory-worker  | [INFO] Executing 'npm run build' in directory '.'...
factory-worker  | [ERROR] Build failed (code 1):
factory-worker  | STDOUT:
factory-worker  |
factory-worker  | STDERR:
factory-worker  | npm error Missing script: "build"
factory-worker  | npm error
factory-worker  | npm error To see a list of scripts, run:
factory-worker  | npm error   npm run
factory-worker  | npm error A complete log of this run can be found in: /root/.npm/_logs/2026-01-01T01_55_53_748Z-debug-0.log
factory-worker  |
factory-worker  | [INFO] Dev Agent: Starting iteration 18
factory-worker  | [WARNING] Dev Agent: A tool error occurred. Entering error correction loop.
factory-worker  | [INFO] Dev Agent: Proposed writing file: package.json
factory-worker  | [INFO] Dev Agent: Proposed writing file: jest.config.js
factory-worker  | [INFO] Dev Agent: Proposed writing file: schema.prisma
factory-worker  | [WARNING] File 'package.json' already exists and will be overwritten.
factory-worker  | [WARNING] File 'jest.config.js' already exists and will be overwritten.
factory-worker  | [INFO] Dev Agent: Starting iteration 19
factory-worker  | [INFO] Dev Agent: Tool executed successfully. Prompting to continue.
factory-worker  | [INFO] Executing 'npm run build' in directory '.'...
factory-worker  | [ERROR] Build failed (code 1):
factory-worker  | STDOUT:
factory-worker  |
factory-worker  | STDERR:
factory-worker  | npm error Missing script: "build"
factory-worker  | npm error
factory-worker  | npm error To see a list of scripts, run:
factory-worker  | npm error   npm run
factory-worker  | npm error A complete log of this run can be found in: /root/.npm/_logs/2026-01-01T01_56_02_888Z-debug-0.log
factory-worker  |
factory-worker  | [INFO] Dev Agent: Starting iteration 20
factory-worker  | [WARNING] Dev Agent: A tool error occurred. Entering error correction loop.
factory-worker  | [INFO] Dev Agent: Proposed writing file: package.json
factory-worker  | [INFO] Dev Agent: Proposed writing file: jest.config.js
factory-worker  | [INFO] Dev Agent: Proposed writing file: schema.prisma
factory-worker  | [WARNING] File 'package.json' already exists and will be overwritten.
factory-worker  | [WARNING] File 'jest.config.js' already exists and will be overwritten.
factory-worker  | [INFO] Dev Agent: Starting iteration 21
factory-worker  | [INFO] Dev Agent: Tool executed successfully. Prompting to continue.
factory-worker  | [INFO] Executing 'npm run build' in directory '.'...
factory-worker  | [ERROR] Build failed (code 1):
factory-worker  | STDOUT:
factory-worker  |
factory-worker  | STDERR:
factory-worker  | npm error Missing script: "build"
factory-worker  | npm error
factory-worker  | npm error To see a list of scripts, run:
factory-worker  | npm error   npm run
factory-worker  | npm error A complete log of this run can be found in: /root/.npm/_logs/2026-01-01T01_56_14_145Z-debug-0.log
factory-worker  |
factory-worker  | [INFO] Dev Agent: Starting iteration 22
factory-worker  | [WARNING] Dev Agent: A tool error occurred. Entering error correction loop.
factory-worker  | [INFO] Dev Agent: Proposed writing file: package.json
factory-worker  | [INFO] Dev Agent: Proposed writing file: jest.config.js
factory-worker  | [INFO] Dev Agent: Proposed writing file: schema.prisma
factory-worker  | [WARNING] File 'package.json' already exists and will be overwritten.
factory-worker  | [WARNING] File 'jest.config.js' already exists and will be overwritten.
factory-worker  | [INFO] Dev Agent: Starting iteration 23
factory-worker  | [INFO] Dev Agent: Tool executed successfully. Prompting to continue.
factory-worker  | [INFO] Executing 'npm run build' in directory '.'...
factory-worker  | [ERROR] Build failed (code 1):
factory-worker  | STDOUT:
factory-worker  |
factory-worker  | STDERR:
factory-worker  | npm error Missing script: "build"
factory-worker  | npm error
factory-worker  | npm error To see a list of scripts, run:
factory-worker  | npm error   npm run
factory-worker  | npm error A complete log of this run can be found in: /root/.npm/_logs/2026-01-01T01_56_25_237Z-debug-0.log
factory-worker  |
factory-worker  | [INFO] Dev Agent: Starting iteration 24
factory-worker  | [WARNING] Dev Agent: A tool error occurred. Entering error correction loop.
factory-worker  | [INFO] Dev Agent: Proposed writing file: package.json
factory-worker  | [INFO] Dev Agent: Proposed writing file: jest.config.js
factory-worker  | [INFO] Dev Agent: Proposed writing file: schema.prisma
factory-worker  | [WARNING] File 'package.json' already exists and will be overwritten.
factory-worker  | [WARNING] File 'jest.config.js' already exists and will be overwritten.
factory-worker  | [INFO] Dev Agent: Starting iteration 25
PS C:\Users\BAMBARA Arthur\Desktop\StartupNexus\factory-sprint0>
