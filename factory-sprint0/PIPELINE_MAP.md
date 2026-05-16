# PIPELINE MAP — Software Agent Factory
> Document de référence — à consulter avant tout diagnostic ou modification.
> Dernière mise à jour : 2026-05-16

---

## 1. SÉQUENCE D'EXÉCUTION

```
run_batch.py
  └─ TodoPilotWorkflow (Temporal)
       ├─ [2] architect_activity
       │    └─ Produit : ProjectSpec (models, pages, routes, user_flows)
       │    └─ Gate : spec_validation_status == DEGRADED → abort
       │
       ├─ [3] dev_test_activity
       │    │
       │    ├─ PRÉ-PHASE A : Écriture templates infrastructure
       │    │    └─ write_template_files() → package.json, tsconfig.json, app/layout.tsx...
       │    │       Source : nextjs-clerk-prisma.json → templated_files
       │    │       BLOQUANT si package.json absent
       │    │
       │    ├─ PRÉ-PHASE B : Projection déterministe schema.prisma
       │    │    └─ ProjectSpec.to_prisma_schema_block() → prisma/schema.prisma
       │    │       ⚠ NON PROTÉGÉ — LLM peut écraser (BUG LATENT)
       │    │
       │    ├─ PRÉ-PHASE C : Générateurs déterministes
       │    │    ├─ dev_middleware_generator  → middleware.ts         [PROTÉGÉ]
       │    │    ├─ dev_navigation_generator → components/nav.tsx    [PROTÉGÉ]
       │    │    ├─ dev_types_generator      → lib/types.ts           [PROTÉGÉ]
       │    │    ├─ dev_zod_generator        → lib/schemas.ts         [PROTÉGÉ]
       │    │    ├─ dev_service_generator    → lib/services/*.ts      [PROTÉGÉ]
       │    │    ├─ dev_actions_generator    → app/**/actions.ts      [PROTÉGÉ]
       │    │    └─ dev_pages_generator      → app/**/page.tsx (+client) [PROTÉGÉ si model présent]
       │    │
       │    ├─ PRÉ-RUN COMMANDS (npm install, prisma generate)
       │    │    Source : nextjs-clerk-prisma.json → pre_run_commands
       │    │    Lecture : DIRECT_DATABASE_URL hardcodé comme placeholder
       │    │
       │    ├─ LLM DEV LOOP (LangGraph, MAX 15 turns / 3 build attempts)
       │    │    ├─ planner_node() → plan = fichiers à écrire (exclut template_written)
       │    │    ├─ executor_node() → write_file / shell_exec avec protection
       │    │    └─ feedback loop : erreur build → LLM reçoit diagnostic structuré
       │    │
       │    ├─ BUILD : npm run build
       │    └─ TEST  : npm test (non bloquant pour succès global)
       │
       ├─ [4] review_activity (si build SUCCESS ou PARTIAL)
       │    └─ Vérifie cohérence sémantique et sécurité → COHERENT/DEGRADED/INCOHERENT
       │
       ├─ [5] correction_pass_activity (si review DEGRADED/INCOHERENT)
       │
       ├─ [6] qa_activity
       │
       ├─ [7] github_activity — ⛔ PAUSÉ (test phase)
       │
       └─ [8] learner_activity
```

---

## 2. PROPRIÉTÉ DES FICHIERS CRITIQUES

| Fichier | Propriétaire réel | Protégé ? | LLM peut écraser ? | Risque |
|---|---|---|---|---|
| `package.json` | write_template_files | OUI | NON | Faible |
| `tsconfig.json` | write_template_files | OUI | NON | Faible |
| `prisma/schema.prisma` | `to_prisma_schema_block()` | **NON** | **OUI** | **ÉLEVÉ** |
| `middleware.ts` | dev_middleware_generator | OUI | NON | Faible |
| `lib/types.ts` | dev_types_generator | OUI | NON | Faible |
| `lib/schemas.ts` | dev_zod_generator | OUI | NON | Faible |
| `lib/services/*.ts` | dev_service_generator | OUI | NON | Faible |
| `app/**/actions.ts` | dev_actions_generator | OUI | NON | Faible |
| `app/**/page.tsx` (avec model) | dev_pages_generator | OUI | NON | Faible |
| `app/**/page.tsx` (sans model) | LLM | NON | OUI | Moyen |
| `app/**/page-client.tsx` | dev_pages_generator | OUI | NON | Faible |
| `app/layout.tsx` | Template (base) puis LLM | NON | OUI | Moyen |

---

## 3. DISTINCTION template_written vs protected_files

Ces deux concepts coexistent et se chevauchent — source de confusion.

```
template_written (dict)
  = fichiers écrits AVANT que le LLM démarre
  = transmis au planner → exclus du plan LLM
  = protège implicitement (le LLM ne les planifie pas)
  Source : write_template_files() + tous les dev_*_generators

protected_files (set)
  = liste explicite de chemins refusés par write_file()
  = même si le LLM essaie d'écrire → refusé à l'outil
  Source : nextjs-clerk-prisma.json → "protected_files" + ajouts dynamiques en dev_graph.py
```

**Conflit connu** : `prisma/schema.prisma` est dans `template_written` (écrit en PRÉ-PHASE B)
mais PAS dans `protected_files` → si le LLM appelle `write_file("prisma/schema.prisma", ...)`
l'outil l'accepte. Fix requis : ajouter `schema.prisma` à `protected_files`.

---

## 4. MÉCANISMES DÉSACTIVÉS OU MORTS

| Mécanisme | Statut | Localisation | Impact si activé |
|---|---|---|---|
| `JOURNEY_LLM_FALLBACK` | Désactivé (env var=0) | `journey_validator.py` | LLM juge la couverture des flows non résolus |
| `TEMPORAL_PARALLEL_MODE` | Importé, jamais exécuté | `todo_pilot_workflow.py` | Parallélisme M2 non opérationnel |
| `MAX_ACTIVITY_TSC_FEEDBACK_RETRIES` | Forcé à 0 | `dev_test_activity.py` | Ancien retry TSC — désactivé volontairement |
| `commands` dict (JSON config) | Lu, jamais utilisé | `nextjs-clerk-prisma.json` | Était censé contrôler build/test/install |
| `qdrant_filter` (JSON config) | Lu, jamais utilisé | `nextjs-clerk-prisma.json` | Était censé filtrer RAG par stack_id |
| `compatibility_matrix` (JSON config) | Lu, jamais utilisé | `nextjs-clerk-prisma.json` | Contraintes versions Jest/TS |
| `iteration_policy.tiers` (JSON config) | Présent, jamais consommé | `nextjs-clerk-prisma.json` | Ajustement max_iterations dynamique |
| `spec_fingerprint` | Calculé, jamais vérifié | `project_spec.py` | Mutation silencieuse spec entre activities |

---

## 5. ZONES DE FRICTION (CONFLITS POTENTIELS)

### Friction #1 — schema.prisma non protégé ⚠
- `to_prisma_schema_block()` écrit le fichier en PRÉ-PHASE B
- Non ajouté à `protected_files`
- Le LLM peut l'écraser → corruption garantie si LLM décide de "corriger" le schema
- **Fix** : ajouter `"prisma/schema.prisma"` à `protected_files` dans `nextjs-clerk-prisma.json`

### Friction #2 — user_flows coverage : regex vs format brief ⚠
- `journey_validator.py` cherche le chemin `/path` à droite du `→`
- Le brief formate les flows avec le chemin à GAUCHE du `→` : `"visiteur lit : /blog → action()"`
- Résultat : 3 flows sur 5 classés "unresolvable" pour le blog
- **Fix** : standardiser le format des flows dans le brief (chemin toujours à droite du `→`)
- Alternative désactivée : `JOURNEY_LLM_FALLBACK=1` (voir mécanismes désactivés)

### Friction #3 — spec_coverage PARTIAL threshold trop bas
- Seuil PARTIAL = 20% de requirements satisfaits
- Un run "PARTIAL" peut signifier que 80% des features sont absentes
- La métrique donne une fausse impression de succès partiel
- **À revisiter** : 50% serait plus honnête

### Friction #4 — Stack config JSON : clés mortes = documentation trompeuse
- `commands`, `qdrant_filter`, `compatibility_matrix`, `iteration_policy.tiers` sont dans le JSON
- Personne ne les lit en production
- Risque : un développeur modifie ces clés en croyant que ça change quelque chose

### Friction #5 — template_written sémantique vs protected_files sémantique
- Deux mécanismes qui font presque la même chose avec des implémentations différentes
- Confusion lors des diagnostics : "ce fichier est protégé ?" nécessite de vérifier les deux

---

## 6. CONTRATS D'INTERFACE ENTRE ACTIVITIES

```
architect_activity OUTPUT
  → project_spec: dict (ProjectSpec sérialisé)
  → requirements: list[str]
  → user_flows: list[str]
  → spec_validation_status: "OK" | "DEGRADED" | "UNKNOWN"

dev_test_activity OUTPUT
  → success: bool
  → combined_files: {filepath: content}  ← TOUS les fichiers écrits
  → metadata: {spec_coverage, requirements_met, user_flows_coverage, is_useful_app}
  → run_metric: dict (détaillé, persisté dans run_reports/)

review_activity OUTPUT
  → review_verdict: "COHERENT" | "DEGRADED" | "INCOHERENT"
  → review_report: {security_score, coherence_score, findings, targeted_fixes}

correction_pass_activity OUTPUT
  → correction_applied: bool
  → files_modified: list[str]
  → new_build_status: "BUILD_SUCCESS" | "BUILD_FAILED"
```

---

## 7. POINTS D'AMÉLIORATION IDENTIFIÉS (BACKLOG)

1. **Ajouter `prisma/schema.prisma` à `protected_files`** — friction #1, risque élevé
2. **Standardiser format user_flows dans les briefs** — friction #2, qualité métrique
3. **Nettoyer clés mortes du JSON stack config** — friction #4, maintenabilité
4. **Réviser seuil PARTIAL (20% → 50%)** — friction #3, honnêteté métrique
5. **Documenter `template_written` vs `protected_files`** en commentaire dans dev_graph.py
6. **Activer vérification spec_fingerprint** entre architect et dev (cohérence)
7. **Supprimer ou opérationaliser** `TEMPORAL_PARALLEL_MODE` et `GenerationSessionWorkflow`
