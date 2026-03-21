# Migration Temporal — Architecture Parallèle par Batch

**Version** : 1.3 — M3 signaux
**Date** : 2026-03-20
**Statut** : ACTIF — document pivot pour toutes les phases M1 → M4

| Phase | État |
|-------|------|
| M0 | ✅ Contrats figés, feature flag, structure artifact |
| M1 | ✅ asyncio.gather sur superviseurs per-file dans dev.py |
| M2 | ✅ GenerationSessionWorkflow + worker multi-queues (scaffold) |
| M3 | 🔄 EN COURS — signaux + continue_as_new |
| M4 | ⏳ Learner aligné batchs |

---

## 1. Contexte et objectif

### Situation actuelle (mode `inline`)

La supervision (conformity, security, architecture) s'exécute **séquentiellement à l'intérieur de `dev_test_activity`**, une unique activité Temporal. Le workflow voit une boîte noire. Aucun retry par superviseur, aucune observabilité par fichier, aucun scaling horizontal possible.

### Cible (mode `workflow`)

```
GenerationSessionWorkflow
  ├── generate_batch_activity       (factory-dev-queue)
  ├── conformity_activity    ┐
  ├── security_activity      ├── asyncio.gather — factory-supervisors-queue
  ├── architecture_activity  ┘
  ├── aggregate_corrections_activity
  ├── apply_corrections_activity
  └── (repeat N batches)
       └── build_activity           (factory-build-queue)
```

---

## 2. Feature Flag — Bascule progressive

Défini dans `config/factory_config.py` :

```python
TEMPORAL_PARALLEL_MODE = os.getenv("TEMPORAL_PARALLEL_MODE", "inline")
```

| Valeur | Comportement | Phase |
|--------|-------------|-------|
| `inline` | Supervision séquentielle dans dev.py (actuel) | M0 — default |
| `asyncio` | asyncio.gather dans dev.py, toujours 1 activité | M1 |
| `workflow` | GenerationSessionWorkflow orchestre les activités | M2 |
| `signal` | Full signal-driven + continue_as_new | M3 |

**Règle** : Les deux modes doivent coexister à tout moment. Le flag se change par env var, sans redéploiement de code. Un run en cours avec `inline` n'est jamais affecté par un changement de flag.

---

## 3. Stockage des Artifacts (`artifact_ref`)

Les signaux Temporal ne portent **jamais** le contenu des fichiers générés. Ils portent uniquement des références (`artifact_ref`).

### Format d'un `artifact_ref`

```json
{
  "run_id": "run_abc123",
  "batch_id": "batch_003",
  "path": "/app/generated-projects/run_abc123/batches/batch_003/files.json"
}
```

### Structure sur disque

```
FACTORY_WORKDIR/
└── {run_id}/
    ├── batches/
    │   ├── batch_001/
    │   │   ├── files.json          ← fichiers générés du batch (dict path→content)
    │   │   ├── supervisor_conformity.json
    │   │   ├── supervisor_security.json
    │   │   └── supervisor_architecture.json
    │   └── batch_002/
    │       └── ...
    ├── corrections/
    │   └── bundle_{batch_id}.json  ← CorrectionsBundle agrégé
    └── build/
        └── failure_report.json     ← BuildFailureReport si échec
```

**Pourquoi fichiers locaux et non Redis/S3 ?**
Cohérent avec l'existant (`FACTORY_WORKDIR` déjà utilisé partout), zéro dépendance externe nouvelle, accessible depuis tous les workers du même host Docker.

---

## 4. Contrats de Payload (figés M0)

### 4.1 `BatchReady`

Émis par `generate_batch_activity` pour signaler qu'un batch est prêt à superviser.

```json
{
  "run_id": "string — identifiant unique du run",
  "batch_id": "string — ex: batch_001",
  "artifact_ref": {
    "run_id": "string",
    "batch_id": "string",
    "path": "string — chemin absolu vers files.json"
  },
  "stack_id": "string — ex: nextjs-clerk-prisma",
  "requirements_ref": "string — chemin vers requirements.json du run",
  "plan_ref": "string — chemin vers plan.json du run",
  "files_count": "integer — nombre de fichiers dans ce batch",
  "batch_index": "integer — index 0-based du batch dans le run"
}
```

### 4.2 `SupervisorResult`

Émis par chaque activité superviseur après analyse d'un batch.

```json
{
  "run_id": "string",
  "batch_id": "string",
  "supervisor": "string — conformity | security | architecture",
  "status": "string — ok | needs_fix | error",
  "confidence": "float — 0.0 à 1.0",
  "fixes_count": "integer — nombre de corrections proposées",
  "fixes_ref": "string — chemin vers supervisor_{name}.json",
  "latency_ms": "integer — temps d'exécution du superviseur"
}
```

### 4.3 `CorrectionsBundle`

Émis par `aggregate_corrections_activity` après fusion des 3 SupervisorResult.

```json
{
  "run_id": "string",
  "batch_id": "string",
  "must_fix": [
    {
      "file": "string — chemin du fichier",
      "supervisor": "string",
      "fix": "string — description de la correction",
      "confidence": "float"
    }
  ],
  "should_fix": [
    {
      "file": "string",
      "supervisor": "string",
      "fix": "string",
      "confidence": "float"
    }
  ],
  "files_impacted": ["string — liste des fichiers touchés"],
  "total_fixes": "integer"
}
```

**Règle** : `must_fix` = confidence >= 0.8. `should_fix` = confidence 0.5–0.8. En dessous de 0.5 → ignoré.

### 4.4 `BuildFailureReport`

Émis par `build_activity` en cas d'échec de build.

```json
{
  "run_id": "string",
  "stderr_ref": "string — chemin vers build/failure_report.json",
  "failing_files": ["string — fichiers mentionnés dans stderr"],
  "error_summary": "string — première ligne d'erreur tronquée à 500 chars",
  "suggested_fix_ref": "string | null — chemin vers fix suggéré par build_supervisor"
}
```

---

## 5. Task Queues

| Queue | Workers | Activités enregistrées |
|-------|---------|----------------------|
| `factory-task-queue` | worker principal (actuel) | toutes activités existantes — backward compat |
| `factory-dev-queue` | worker dev | `generate_batch_activity`, `apply_corrections_activity` |
| `factory-supervisors-queue` | worker superviseurs | `conformity_activity`, `security_activity`, `architecture_activity`, `aggregate_corrections_activity` |
| `factory-build-queue` | worker build | `build_activity`, `build_supervisor_activity` |

**Pendant M1** : une seule queue `factory-task-queue` suffit. La séparation des queues se fait en M2.
**Pendant M2** : les 3 nouvelles queues sont créées mais peuvent pointer vers le même worker process (pas besoin de 3 processus distincts au démarrage).

---

## 6. État transmis dans `continue_as_new`

Après chaque `CONTINUE_AS_NEW_THRESHOLD` batchs (défaut : 10), le workflow se recrée avec l'état suivant :

```python
@dataclass
class GenerationSessionState:
    run_id: str
    stack_id: str
    project_name: str
    batch_cursor: int           # index du prochain batch à générer
    completed_files: list[str]  # fichiers déjà générés et validés (paths)
    corrections_applied: int    # total cumulé de corrections appliquées
    iteration: int              # numéro d'itération du workflow (incrémenté à chaque continue_as_new)
    requirements_ref: str       # chemin vers requirements.json — immuable dans le run
    plan_ref: str               # chemin vers plan.json — immuable dans le run
```

**Règle** : `completed_files` permet au nouveau workflow instance de ne pas regénérer les fichiers déjà validés. C'est le seul état qui doit survivre à `continue_as_new`.

---

## 7. Configuration supervision dans le JSON stack

À ajouter dans `config/stacks/nextjs-clerk-prisma.json` (section `"supervision"`) :

```json
"supervision": {
  "batch_size": 3,
  "supervisor_timeout_ms": 30000,
  "continue_as_new_threshold": 10,
  "min_confidence_must_fix": 0.8,
  "min_confidence_should_fix": 0.5,
  "enabled_supervisors": ["conformity", "security", "architecture"]
}
```

**Règle** : Toute valeur numérique liée à la supervision est dans le JSON stack, jamais hardcodée en Python.

---

## 8. Stratégie de transition M1 → M2

Le risque principal est d'avoir deux chemins de supervision actifs sur le même run.

**Règle de coexistence** :
- `TEMPORAL_PARALLEL_MODE` est lu **une seule fois** au démarrage du run, dans `todo_pilot_workflow.py`
- La valeur est transmise dans l'input de chaque activité (`run_mode` field)
- Un run commencé en `inline` se termine en `inline`, même si le flag change entre-temps
- Pas de migration de run en cours — uniquement les nouveaux runs utilisent le nouveau mode

```python
# todo_pilot_workflow.py — lecture unique au début du run
run_mode = TEMPORAL_PARALLEL_MODE  # lu depuis factory_config au démarrage du workflow

# transmis dans tous les inputs d'activités
dev_test_input["run_mode"] = run_mode
```

---

## 9. Critères de sortie par phase

| Phase | Critère quantitatif | Critère qualitatif |
|-------|--------------------|--------------------|
| M1 | latence supervision −30% mesurée sur 3 runs | Tests `test_sprint46_v2` verts, mode `inline` toujours fonctionnel |
| M2 | 3 runs `marketplace-mvp` en mode `workflow` avec taux succès ≥ mode `inline` | Activités visibles individuellement dans Temporal UI |
| M3 | 3 runs consécutifs sans timeout, taille historique Temporal stable (±10%) | Query `state_snapshot` répond en cours de run |
| M4 | Suggestions Learner basées sur batch_id traceable | Traçabilité run → batch → correction → standard visible dans logs |

---

## 10. Ordre d'exécution inter-équipes

```
M0  Claude ──────────────────────────────────────── Ce document + factory_config.py
     ↓
M1  Codex : asyncio.gather dans dev.py              ║  Claude : supervision config dans JSON stack
     ↓ (critère M1 validé par Claude)                ║           + métriques observability.py
M2  Codex : GenerationSessionWorkflow               ║  Claude : worker.py multi-queues
     ↓ (critère M2 validé par Claude)                          + branchement feature flag workflow
M3  Codex : signals + continue_as_new               ║  Claude : test continue_as_new state
     ↓ (critère M3 validé par Claude)
M4  Codex : learner.py nouveaux events              ║  Claude : vérification schéma events
```

**Règle** : Claude valide le critère de sortie de chaque phase avant que Codex commence la phase suivante.

---

## 11. Non-régressions obligatoires à chaque phase

1. `test_sprint46_v2` — suite complète verte
2. Mode `TEMPORAL_PARALLEL_MODE=inline` fonctionnel (backward compat)
3. Contrat de sortie de `dev_agent()` inchangé (même structure JSON)
4. `learner_suggestions.json` continue à se peupler normalement
5. `run_batch.py --size 1` sur "Cree une Todo app Next.js avec Clerk" → BUILD_SUCCESS

---

---

## 12. Signaux et Queries M3

### Architecture signal-driven

En M3, le workflow devient **réactif** : il ne pilote plus la génération lui-même. C'est le processus externe (dev.py ou dev_test_activity) qui signale quand un batch est prêt. Le workflow répond en orchestrant les superviseurs.

```
External (dev.py)                     GenerationSessionWorkflow
     │                                         │
     │  signal: batch_ready(artifact_ref)       │
     │─────────────────────────────────────────>│
     │                                         │ execute supervisors in parallel
     │                                         │ (conformity + security + architecture)
     │                                         │ aggregate corrections
     │                                         │
     │  query: state_snapshot()                │
     │─────────────────────────────────────────>│
     │  ← {corrections, batch_id, status}      │
     │                                         │
     │  (external applies corrections)          │
     │                                         │
     │  signal: batch_ready(next_artifact_ref) │
     │─────────────────────────────────────────>│
     │                                         │ ...
     │  signal: abort_generation()              │
     │─────────────────────────────────────────>│
     │                                         │ clean exit
```

### Contrats des signaux

#### Signal `batch_ready`

Envoyé par l'externe quand un batch de fichiers est prêt à superviser.

```python
@workflow.signal
async def batch_ready(self, payload: dict) -> None:
    # payload = BatchReady (section 4.1)
    # {run_id, batch_id, artifact_ref, stack_id, requirements_ref, plan_ref, files_count, batch_index}
```

#### Signal `abort_generation`

Arrêt propre demandé par l'externe (timeout, erreur critique, annulation utilisateur).

```python
@workflow.signal
async def abort_generation(self, reason: str = "") -> None:
    # Déclenche une sortie propre de la boucle principale
```

#### Query `state_snapshot`

Appelé par l'externe pour lire l'état courant du workflow (corrections disponibles, fichiers complétés).

```python
@workflow.query
def state_snapshot(self) -> dict:
    return {
        "run_id": self._state.run_id,
        "batch_cursor": self._state.batch_cursor,
        "iteration": self._state.iteration,
        "completed_files": self._state.completed_files,
        "corrections_applied": self._state.corrections_applied,
        "pending_corrections": self._pending_corrections,  # CorrectionsBundle du dernier batch
        "status": self._status,  # "waiting_batch" | "supervising" | "done" | "aborted"
    }
```

### Pattern d'attente de signal (Temporal Python)

```python
# Attendre le prochain signal batch_ready avec timeout
try:
    await workflow.wait_condition(
        lambda: self._pending_batch is not None or self._abort_requested,
        timeout=timedelta(minutes=30),
    )
except asyncio.TimeoutError:
    self._status = "aborted"
    return self._build_final_result()
```

### État interne M3 (ajouts à GenerationSessionState)

```python
# Attributs d'instance du workflow (pas dans le dataclass — état volatil)
self._pending_batch: dict | None = None      # BatchReady reçu via signal, pas encore traité
self._pending_corrections: dict | None = None  # CorrectionsBundle du dernier batch supervisé
self._abort_requested: bool = False           # True si signal abort_generation reçu
self._status: str = "waiting_batch"           # état courant pour query
```

### Règle de transition `continue_as_new` en M3

En mode signal-driven, `continue_as_new` est appelé UNIQUEMENT entre deux batchs (pas en cours de supervision) pour ne pas perdre un signal en transit.

```python
# ✅ Correct — entre deux batchs, après avoir traité pending_batch
if state.iteration % CONTINUE_AS_NEW_THRESHOLD == 0:
    workflow.continue_as_new(asdict(state))

# ❌ Incorrect — en plein asyncio.gather sur les superviseurs
```

---

*Ce document est la référence unique pour la migration. Toute décision d'architecture non couverte ici doit être ajoutée à ce document avant implémentation.*
