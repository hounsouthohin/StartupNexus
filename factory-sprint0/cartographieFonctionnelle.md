# Cartographie Fonctionnelle — Software Agent Factory

> Dernière mise à jour : 18 avril 2026 (post-plan 6 étapes)

---

## Vue d'ensemble du pipeline

```
TodoPilotWorkflow (Temporal)
  ├── architect_activity      → ProjectSpec (models, pages, routes, requirements[])
  ├── dev_test_activity       → DevGraph LangGraph → fichiers écrits + build
  ├── qa_activity             → analyse qualité + spec_coverage
  ├── github_activity         → push repo
  └── learner_activity        → génère suggestions Qdrant (shadow mode)
```

---

## Couche 1 — Workflow (Temporal)

| Fichier | Rôle |
|---|---|
| `workflows/todo_pilot_workflow.py` | Orchestrateur principal, séquence les activities |
| `workflows/activities/dev_test_activity.py` | Lance DevGraph, gère retries, calcule success |
| `workflows/activities/architect_activity.py` | Appelle architect agent, valide ProjectSpec |
| `workflows/activities/qa_activity.py` | Lance QA agent, note spec_coverage |
| `workflows/activities/learner_activity.py` | Génère suggestions RAG à partir du dernier run |

---

## Couche 2 — DevGraph (LangGraph StateGraph)

**Point d'entrée** : `run_dev_agent()` dans `agents/dev_graph.py`

### Nœuds du graph

```
START → dev → prebuild_gate → tools → file_validate → extract_error → (route) → dev ou END
```

| Nœud | Fonction | Déclencheur |
|---|---|---|
| `dev` | `dev_node` | LLM gpt-4o-mini avec system prompt stack |
| `prebuild_gate` | `prebuild_gate_node` | Bloque npm run build prématuré |
| `tools` | `ToolNode` | Exécute les tool_calls (write_file, shell_exec, read_file) |
| `file_validate` | `file_validate_node` | tsc --noEmit sur fichiers écrits ce tour |
| `extract_error` | `extract_build_error_node` | Détecte succès/erreur depuis ToolMessages |

### Routage

| Condition | Routage |
|---|---|
| `success=True` | → END |
| `last_build_error` + attempts < MAX | → dev (correction) |
| `attempts >= MAX_BUILD_ATTEMPTS` | → END (abandon) |
| `file_validation_errors` + retries ≤ MAX | → dev (correction tsc) |
| `file_validation_errors` vide ou retries > MAX | → extract_error |
| `prebuild_blocking=True` | → dev (re-prompt) |

---

## Couche 3 — Fonctions utilitaires (dev_graph.py)

| Fonction | Rôle | Phase |
|---|---|---|
| `_error_signature(stderr)` | MD5 hash 8 chars — détection boucle correction | post-build |
| `_build_targeted_correction(error)` | Injecte erreur build + diagnostic catalogue dans HumanMessage | post-build |
| `_prune_messages(messages)` | Élagage sémantique : garde system + first/last human + 3 derniers rounds | context management |
| `_is_build_command(command)` | Détecte `npm run build` dans tool_calls | prebuild gate |
| `_extract_written_ts_files(messages)` | Parcourt ToolMessages pour trouver les fichiers .ts/.tsx écrits | file_validate |
| `_parse_tsc_errors_for_files(output, files)` | Filtre tsc output sur les fichiers cibles uniquement | file_validate |

---

## Couche 4 — Catalogue d'erreurs (tsc_error_catalog.py)

**Fichier** : `agents/tsc_error_catalog.py`

Structure déclarative : `TSC_ERROR_CATALOG[code] = { _pattern, _extract, entries[] }`

| Code | Sous-cas | Action | rag_query |
|---|---|---|---|
| TS2307 | local (starts @/ ./) | CREATE_FILE | "créer composant React fichier manquant" |
| TS2307 | npm (fallback) | NPM_INSTALL | None |
| TS2339 | "never" in type | ADD_TYPE_ANNOTATION | "TypeScript never tableau Prisma" |
| TS2339 | default | CHECK_SCHEMA | "propriété Prisma inexistante schéma" |
| TS2304 | default | CHECK_TYPES_FILE | "types lib exportés Prisma" |
| TS2724 | default | CHECK_TYPES_FILE | "types lib exportés Prisma" |
| TS7006 | default | ADD_EXPLICIT_TYPE | "paramètre type explicite React event" |
| TS7031 | default | ADD_EXPLICIT_TYPE | "destructuring type explicite composant" |
| TS2531 | default | ADD_NULL_CHECK | "null check guard Prisma findUnique" |
| TS2345 | nullable → non-null | FIX_AUTH_GUARD | "auth guard userId null Clerk Prisma" |
| TS2345 | default | FIX_TYPE_MISMATCH | "type mismatch incompatible Prisma" |

**API** : `lookup_error(err_line: str) → CatalogMatch | None`
- `CatalogMatch.context_hint` : instruction actionnable pour le LLM
- `CatalogMatch.rag_query` : query vers Qdrant pour standard correctif
- `CatalogMatch.action` : code sémantique pour métriques

---

## Couche 5 — Prompts et règles stack

| Fichier | Rôle | Taille cible |
|---|---|---|
| `prompts/stacks/nextjs-clerk-prisma/rules_dev.md` | 16 contraintes pures, sans exemples de code | ~35 lignes |
| `prompts/stacks/nextjs-clerk-prisma/brief_normalizer.md` | Instructions de normalisation du brief pour l'architect | ~80 lignes |
| `agents/dev_prompts.py` : `build_system_prompt()` | Assemble system prompt : rules_dev + spec + types_exported | Python |

---

## Couche 6 — Base de connaissances (Qdrant)

**Collection** : `factory_standards`  
**Zones actives** : ZONE_1 → ZONE_14 (53 standards)

| Zone | Contenu |
|---|---|
| ZONE_1–8 | Patterns de code stack (preventive) |
| ZONE_9 | .env.local + Clerk keys |
| ZONE_10–13 | Prisma 7, auth patterns |
| ZONE_14 | Suggestions validées (approve_suggestion.py) |
| ZONE_18 (prévu) | Standards correctifs par code d'erreur tsc |

**Injection** : preventive uniquement pour l'instant (avant génération)  
**Pont manquant** → étapes 5+6 : ajouter standards correctifs + requête RAG depuis `rag_query` du catalogue

---

## Couche 7 — Outils LLM (shared_tools.py)

| Outil | Signature | Description |
|---|---|---|
| `write_file` | `(path, content)` | Écrit un fichier dans le workdir projet |
| `read_file` | `(path, start?, end?)` | Lit un fichier (lignes optionnelles) |
| `shell_exec` | `(command)` | Exécute une commande shell dans le workdir |
| `list_files` | `(path?)` | Liste les fichiers d'un dossier |

---

## Flux de validation progressive (file_validate_node)

```
[tools exécutés] → [fichiers .ts/.tsx écrits?]
    ↓ non → pass-through
    ↓ oui
[tsc --noEmit disponible?]
    ↓ non (npm install pas encore fait) → pass-through
    ↓ oui
[tsc clean?]
    ↓ oui → validated_files += écrits, pass-through
    ↓ non
[filtrer erreurs sur fichiers écrits ce tour]
    ↓ aucune erreur sur ces fichiers → pass-through
    ↓ erreurs
[pour chaque ligne d'erreur:]
  A2 : inject snippet ±4 lignes autour de l'erreur
  Catalogue : lookup_error() → inject context_hint
[HumanMessage(errors_enriched) → retour LLM]
```

---

## Fixes appliqués au pipeline (chronologie résumée)

| ID | Description | Fichier |
|---|---|---|
| A1 | Injection "build maintenant" quand validated_files non vide | dev_graph.py dev_node |
| A2 | Lecture lignes fichier ±4 autour de l'erreur tsc | dev_graph.py file_validate_node |
| C2 | Types exportés exacts injectés dans system prompt | dev_prompts.py build_system_prompt |
| D1 | MAX_ACTIVITY_TSC_FEEDBACK_RETRIES = 0 | dev_test_activity.py |
| E1 → catalogue | TS2307 local → CREATE_FILE (remplacé par catalogue) | tsc_error_catalog.py |
| Plan-1 | Catalogue déclaratif tsc_error_catalog.py (8 codes) | tsc_error_catalog.py |
| Plan-2 | file_validate_node rebranché sur catalogue | dev_graph.py |
| Plan-3 | _build_targeted_correction rebranché sur catalogue | dev_graph.py |
| Plan-4 | rules_dev.md réduit 190 → ~35 lignes | rules_dev.md |
