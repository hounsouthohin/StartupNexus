factory-sprint0/                  ← Dossier racine du projet actif (on pourra archiver par sprint plus tard)
├── .env                          ← Variables d'environnement (clés API, ports, etc.)
├── .gitignore
├── docker-compose.yml            ← n8n + Temporal + Qdrant + Postgres (comme prévu dans la roadmap)
├── dynamicconfig/                ← Config Temporal dev/prod
│   └── development-sql.yaml
├── requirements.txt              ← Dépendances Python (temporalio, langgraph, langchain-openai, flask, etc.)
├── README.md                     ← Vision du projet + comment lancer (on le remplira ensemble)
│
├── config/                       ← TOUTES les configs globales
│   └── factory_config.py         ← Config centrale (chemins, modèles LLM, timeouts, etc.)
│
├── prompts/                      ← **TOUS** les prompts système (versionnés, clairs, réutilisables)
│   ├── architect.md              ← Prompt système Agent Architecte
│   ├── dev.md                    ← Prompt Agent Dev (Sprint 1)
│   └── qa.md                     ← Prompt Agent QA (plus tard)
│
├── agents/                       ← **Cœur LangGraph** : un fichier par agent ou graphe
│   ├── __init__.py
│   ├── architect.py              ← Définition du graphe LangGraph "Architecte" + nœuds
│   ├── dev.py                    ← Agent Dev (à venir)
│   └── shared_tools.py           ← Outils communs (E2B, GitHub, etc.)
│
├── workflows/                    ← Workflows Temporal (un fichier par workflow principal)
│   ├── __init__.py
│   ├── workflow.py               ← Workflow principal SaaSFactoryWorkflow (orchestre les agents)
│   └── activities/               ← Activities pures (pas d'AI dedans, juste exécution)
│       ├── __init__.py
│       └── utils.py              ← Ex: sauvegarde fichiers, appel GitHub, etc.
│
├── api/                          ← Interface d'entrée (Flask ou futur n8n webhook)
│   ├── __init__.py
│   └── flask_api.py              ← Endpoint /start-saas + queue vers Temporal
│
├── utils/                        ← Fonctions utilitaires partagées (logging, helpers)
│   ├── __init__.py
│   └── logger.py                 ← Config logger safe si besoin
│
└── run/                          ← Point d'entrée unique (plus de main.py tout-en-un)
    └── worker.py                 ← Lance Flask + Worker Temporal + dispatcher