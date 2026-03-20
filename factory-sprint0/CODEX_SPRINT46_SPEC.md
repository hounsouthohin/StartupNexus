# Spec Codex — Sprint 4.6 — Agent Critique

Tâches à implémenter par Codex. Claude a déjà créé les contrats et prompts.

**Ne pas toucher aux fichiers :**
- `prompts/` (déjà rédigés par Claude)
- `schemas/contracts/` (déjà rédigés par Claude)
- `config/stacks/`

---

## C1 — `factory-sprint0/agents/conformity_agent.py`

Créer ce fichier from scratch.

### Signature publique

```python
async def run_conformity_agent(
    requirements: list[str],
    combined_files: dict[str, str],
    project_name: str = "",
    run_id: str = "",
    stack_id: str = "nextjs-clerk-prisma",
) -> dict:
    """
    Retourne toujours un dict (jamais d'exception levée).
    Format conforme à schemas/contracts/conformity_agent_contract.json.
    En cas d'erreur → {"coverage": [], "conformity_score": 0.0, "skipped": True}
    """
```

### Comportement

1. Charger `prompts/base/conformity.md` + `prompts/stacks/{stack_id}/rules_conformity.md`
2. SystemMessage = concaténation des 2 fichiers
3. HumanMessage = requirements numérotés + combined_files tronqués (voir budget tokens)
4. Appeler `ChatOpenAI(model="gpt-4o-mini", temperature=0.0)` avec `response_format={"type": "json_object"}`
5. Parser JSON, calculer `conformity_score = (implemented + 0.5 * partial) / total` si absent
6. Retourner le dict

### Budget tokens combined_files

- `prisma/schema.prisma` : intégral
- `app/api/**/*.ts` : 100 premières lignes
- `app/**/*.tsx` : 60 premières lignes
- autres : 30 premières lignes

### Gestion d'erreurs (toutes les branches)

| Situation | Retour |
|-----------|--------|
| `combined_files` vide | `{"coverage": [], "conformity_score": 0.0, "skipped": True}` |
| `requirements` vide | `{"coverage": [], "conformity_score": 1.0, "skipped": True}` |
| Réponse LLM non-JSON | `{"coverage": [], "conformity_score": 0.0, "parse_error": True}` |
| Exception LLM | `{"coverage": [], "conformity_score": 0.0, "skipped": True}` |

**Jamais de `raise` depuis cette fonction.**

---

## C2 — `factory-sprint0/agents/security_agent.py`

Créer ce fichier from scratch.

### Signature publique

```python
async def run_security_agent(
    api_files: dict[str, str],
    project_name: str = "",
    run_id: str = "",
    stack_id: str = "nextjs-clerk-prisma",
) -> dict:
    """
    Retourne toujours un dict (jamais d'exception levée).
    Format conforme à schemas/contracts/security_agent_contract.json.
    """
```

### Comportement

1. Si `api_files` vide → retourner immédiatement `{"issues": [], "security_score": 1.0, "handlers_audited": 0, "skipped": True}`
2. Garder uniquement les chemins `app/api/**/*.ts` (exclure webhooks : `app/api/webhooks/**`)
3. Charger `prompts/base/security.md` + `prompts/stacks/{stack_id}/rules_security.md`
4. SystemMessage = concaténation des 2 fichiers
5. HumanMessage = contenu intégral des api_files filtrés
6. Appeler `ChatOpenAI(model="gpt-4o-mini", temperature=0.0)` avec `response_format={"type": "json_object"}`
7. Parser JSON
8. Si `handlers_audited` absent → compter les `export async function (GET|POST|PUT|DELETE|PATCH)` dans api_files via regex
9. Si `security_score` absent → `(handlers_audited - nb_issues_high) / handlers_audited` (0 si handlers_audited=0)
10. Retourner le dict

### Gestion d'erreurs

| Situation | Retour |
|-----------|--------|
| `api_files` vide | `{"issues": [], "security_score": 1.0, "handlers_audited": 0, "skipped": True}` |
| Réponse LLM non-JSON | `{"issues": [], "security_score": 0.0, "parse_error": True}` |
| Exception LLM | `{"issues": [], "security_score": 0.0, "skipped": True}` |

**Jamais de `raise`.**

---

## C3 — `factory-sprint0/agents/shared_tools.py` : 2 nouvelles fonctions

Ajouter après `run_tests()`.

### `run_tsc_check(project_dir: str) -> dict`

```python
async def run_tsc_check(project_dir: str) -> dict:
    """Lance tsc --noEmit. Non bloquant si tsc/tsconfig absent."""
```

Logique :
1. Si `tsconfig.json` absent dans project_dir → `{"errors": [], "success": True, "skipped": True}`
2. `subprocess.run(["npx", "tsc", "--noEmit", "--pretty", "false"], cwd=project_dir, capture_output=True, text=True, timeout=60)`
3. Si `FileNotFoundError` ou timeout → `{"errors": [], "success": True, "skipped": True}`
4. Parser stdout : format `file(line,col): error TSxxxx: message`
5. Retourner `{"errors": [{file, line, col, code, message}], "success": returncode == 0}`

Utiliser `asyncio.get_event_loop().run_in_executor(None, ...)` pour ne pas bloquer la boucle async.

### `run_prisma_validate(project_dir: str) -> dict`

```python
async def run_prisma_validate(project_dir: str) -> dict:
    """Lance npx prisma validate. Non bloquant si schema absent."""
```

Logique :
1. Si `prisma/schema.prisma` absent → `{"valid": True, "errors": [], "skipped": True}`
2. `subprocess.run(["npx", "prisma", "validate", "--schema", "prisma/schema.prisma"], cwd=project_dir, capture_output=True, text=True, timeout=30)`
3. Si `FileNotFoundError` ou timeout → `{"valid": True, "errors": [], "skipped": True}`
4. Retourner `{"valid": returncode == 0, "errors": [stderr] if returncode != 0 else []}`

Même pattern `run_in_executor`.

---

## C4 — `factory-sprint0/agents/dev_test_agent.py` : étape CRITIQUE

### Nouvel état dans la state machine

```
GEN → STRUCT_GATES → REQ_GATES → CRITIQUE → BUILD → FINAL
```

### Nouvelle fonction à créer

```python
async def _run_critique_phase(
    project_dir: str,
    combined_files: dict,
    requirements: list[str],
    project_name: str,
    run_id: str,
    stack_id: str,
) -> dict:
    """
    Retourne {"feedback": str, "has_high_severity": bool, "metrics": dict}
    Jamais d'exception.
    """
```

Implémentation :

```python
from agents.conformity_agent import run_conformity_agent
from agents.security_agent import run_security_agent

# Vague 1 — outils déterministes
tsc_result, prisma_result = await asyncio.gather(
    run_tsc_check(project_dir),
    run_prisma_validate(project_dir),
    return_exceptions=True
)

# Vague 2 — agents LLM
api_files = {k: v for k, v in combined_files.items() if k.startswith("app/api/")}
conformity_result, security_result = await asyncio.gather(
    run_conformity_agent(requirements, combined_files, project_name, run_id, stack_id),
    run_security_agent(api_files, project_name, run_id, stack_id),
    return_exceptions=True
)

# Normaliser les exceptions
if isinstance(tsc_result, Exception): tsc_result = {"errors": [], "success": True, "skipped": True}
if isinstance(prisma_result, Exception): prisma_result = {"valid": True, "errors": [], "skipped": True}
if isinstance(conformity_result, Exception): conformity_result = {"coverage": [], "conformity_score": 0.0, "skipped": True}
if isinstance(security_result, Exception): security_result = {"issues": [], "security_score": 0.0, "skipped": True}

# Construire feedback pour le Dev Agent
feedback_parts = []

if tsc_result.get("errors"):
    feedback_parts.append("ERREURS TypeScript :\n" + "\n".join(
        f"  {e['file']}:{e.get('line','?')} — {e['message']}" for e in tsc_result["errors"][:5]
    ))

if not prisma_result.get("valid") and prisma_result.get("errors"):
    feedback_parts.append("ERREURS Prisma schema :\n" + str(prisma_result["errors"])[:300])

missing = [c for c in conformity_result.get("coverage", []) if c["status"] == "missing"]
if missing:
    feedback_parts.append("Requirements non implémentés :\n" + "\n".join(
        f"  - {c['requirement']}" for c in missing
    ))

high_issues = [i for i in security_result.get("issues", []) if i["severity"] == "high"]
if high_issues:
    feedback_parts.append("SÉCURITÉ CRITIQUE :\n" + "\n".join(
        f"  [{i['file']}] {i['handler']}: {i['issue']}\n  Fix: {i['fix']}" for i in high_issues
    ))

has_high_severity = bool(high_issues or tsc_result.get("errors") or not prisma_result.get("valid", True))

metrics = {
    "conformity_score": conformity_result.get("conformity_score", 0.0),
    "security_score": security_result.get("security_score", 1.0),
    "critique_issues_count": len(security_result.get("issues", [])) + len(missing),
    "critique_issues_fixed": 0,
    "tsc_errors_count": len(tsc_result.get("errors", [])),
    "prisma_valid": prisma_result.get("valid", True),
}

return {
    "feedback": "\n\n".join(feedback_parts),
    "has_high_severity": has_high_severity,
    "metrics": metrics,
}
```

### Intégration dans la boucle

- L'étape CRITIQUE tourne **une seule fois**, pas en boucle.
- Si `has_high_severity=True` → injecter `feedback` comme message dans l'historique du Dev Agent, puis laisser **1 itération** avant BUILD.
- Si `has_high_severity=False` → passer directement à BUILD.
- Ajouter `metrics` au `dev_metadata` existant.
- Logger dans le shadow log via `_write_learner_event` les 4 champs : `conformity_score`, `security_score`, `critique_issues_count`, `critique_issues_fixed`.

---

## C5 — `factory-sprint0/tests/test_sprint46_validation.py`

Tests statiques, pas de Docker, pas d'OpenAI réel. Mocker les LLM via `unittest.mock.AsyncMock`.

### 7 blocs obligatoires

```
BLOC 1 — conformity_agent retourne JSON valide sur input mock
BLOC 2 — security_agent retourne JSON valide sur input mock
BLOC 3 — conformity_score est float entre 0.0 et 1.0
BLOC 4 — security_score est float entre 0.0 et 1.0
BLOC 5 — run_tsc_check retourne skipped=True si tsconfig.json absent
BLOC 6 — _run_critique_phase ne lève pas d'exception si un agent retourne une Exception (return_exceptions=True)
BLOC 7 — _run_critique_phase retourne les 4 clés metrics : conformity_score, security_score, critique_issues_count, critique_issues_fixed
```

---

## Ordre d'exécution recommandé

```
1. C3  — shared_tools.py (fonctions autonomes, sans dépendances)
2. C1 + C2 — en parallèle (agents autonomes)
3. C4  — dev_test_agent.py (dépend de C1, C2, C3)
4. C5  — tests (dépend de tout)
```

## Points de validation par Claude (superviseur)

- Après C1+C2 : Claude vérifie le chargement des prompts et la gestion d'erreur.
- Après C4 : Claude vérifie l'intégration dans la state machine et les métriques shadow log.
- Après C5 : Claude lance 3 runs (marketplace, blog, admin) et valide le signal de clôture Sprint 4.6.
