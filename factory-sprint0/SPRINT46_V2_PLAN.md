# Plan Sprint 4.6 v2 — Supervision Inline Multi-Agents
## Version finale — 20 Mars 2026
## Propriétaires : Claude (Phases 0-2) + Codex (Phase 3) + Claude supervise (Phase 4)

---

## VISION CIBLE

Chaque fichier généré par le Dev sort validé (conformité sémantique + sécurité + cohérence
architecturale) avant que le suivant soit écrit. Le build valide uniquement la compilabilité.
Le Learner reçoit un rapport comportemental par run pour améliorer les standards à la source.
Chaque superviseur est une Temporal Activity visible sur le dashboard.

## PIPELINE CIBLE

```
BRIEF
  ↓
ARCHITECT ACTIVITY
  brief_normalizer → RAG → planner → spec_writer
  Output : spec, requirements[], plan{}, user_flows[]
  ↓
DEV ACTIVITY (modifié)
  1. Templates écrits (package.json, middleware.ts, etc.)
  2. Pour chaque fichier généré par write_file() :
       supervision_routing consulté (JSON stack)
           ↓ dispatch parallel
       conformity_activity   security_activity   architecture_activity
           ↓ si confidence > 0.7 et status=needs_fix
       fix_instruction chirurgicale → Dev corrige CE FICHIER UNIQUEMENT
       superviseur re-vérifie → OK → fichier suivant
  3. Après tous les fichiers :
       tsc --noEmit + prisma validate (outils déterministes)
           ↓ si erreurs
       build_supervisor_activity → fix ciblé (ligne précise)
  ↓
BUILD (compilabilité uniquement)
  Si échec → build_supervisor_activity → fix ciblé → re-build
  ↓
QA ACTIVITY → GITHUB ACTIVITY
  ↓
LEARNER ACTIVITY
  Reçoit rapport superviseurs (bons + mauvais comportements par fichier)
  Pattern récurrent → StandardSuggestion → Qdrant (après validation humaine)
  Prochain run : Dev génère juste dès le premier essai
```

---

## RÈGLE MULTI-STACK (non négociable)

Tout ce qui est stack-spécifique vit dans config/stacks/*.json et prompts/stacks/<stack>/*.md.
Le code Python est un exécuteur générique.
Ajouter Vue/FastAPI = créer un JSON + des rules_ + des standards Qdrant. Zéro Python modifié.

Conséquence directe : AUCUN pattern regex stack-spécifique dans les agents Python.
Le _HANDLER_RE de security_agent.py (pattern Next.js hardcodé) est supprimé.
La détection des fichiers à superviser est gérée par supervision_routing dans le JSON.

---

## PHASE 0 — AUDIT & CLEANUP (Claude)
### Prérequis : rien. Doit être complète avant Phase 3.

### P0.1 — Guards à supprimer dans shared_tools.py

Supprimer entièrement :
- La liste CONTENT_GUARDS (blocking + non-blocking) et toute la logique qui l'utilise
- _sanitize_package_json_content() et tous ses appels
- _sanitize_nextconfig_content() et tous ses appels
- _apply_clerk_middleware_v5() et tous ses appels
- _remove_pages_router_conflicts() et tous ses appels
- _remove_problematic_babel_config() et tous ses appels
- _ensure_nextconfig_eslint_ignore() et tous ses appels
- _ensure_tsconfig_paths() et tous ses appels (si présent)
- _ensure_env_local() et tous ses appels (si présent)
- SANITIZER_REGISTRY dict et la boucle d'appel dans run_build()
- Tout import ou référence à ces fonctions

Conserver :
- run_build(), run_tests(), run_tsc_check(), run_prisma_validate() — outillage neutre
- write_file(), read_file() — outillage neutre
- Tout le système de templates (templated_files) — infrastructure, pas des guards
- _log_patch(), _write_learner_event(), _append_rag_usage_event() — observabilité

### P0.2 — Instructions mortes dans les prompts

prompts/dev.md :
  Retirer toute mention de : CONTENT_GUARD, sanitizer, "le guard va corriger",
  "le système va supprimer", toute instruction compensatoire liée aux guards.
  Les instructions doivent exprimer ce que le Dev DOIT faire, pas ce que le système corrigera.

prompts/stacks/nextjs-clerk-prisma/rules_dev.md :
  Même audit. Retirer toute règle du type "si tu génères X, le guard Y s'en occupera".
  Conserver uniquement les règles prescriptives pures (INTERDIT X, OBLIGATOIRE Y).

prompts/base/conformity.md :
  Réécriture complète en Phase 2 — ne pas modifier ici, sera remplacé.

prompts/base/security.md :
  Réécriture complète en Phase 2 — ne pas modifier ici, sera remplacé.

### P0.3 — Standards Qdrant à auditer (create_full_standards_v1.py)

Identifier et reformuler tout standard qui :
  - Mentionne un sanitizer ou guard comme mécanisme de correction
  - Dit "le système corrigera X automatiquement"
  - Décrit un comportement d'infrastructure plutôt qu'une règle de génération

Ces standards doivent exprimer uniquement : INTERDIT X / OBLIGATOIRE Y / PRÉFÉRÉ Z
avec DETECTION_REGEX, EXEMPLE_INVALIDE, EXEMPLE_VALIDE, ERREUR_ATTENDUE.
Un standard est une règle pour le Dev, pas une promesse de correction automatique.

### P0.4 — JSON Stack nextjs-clerk-prisma.json

Supprimer : champ "sanitizers" (ou vider la liste — le champ sera réutilisé Sprint 6)
Ajouter : champ "supervision_routing" (voir Phase 1)
Vérifier : "build_hooks" — si références à des fonctions supprimées, nettoyer

### P0.5 — Tests obsolètes

Supprimer : factory-sprint0/tests/test_sprint46_validation.py
  Ce fichier teste l'ancienne architecture post-génération (_run_critique_phase,
  run_conformity_agent(combined_files)). Avec la nouvelle architecture,
  ces tests sont invalides et doivent être remplacés par test_sprint46_v2_validation.py.

### P0.6 — Temporal Worker audit

Lire le fichier d'enregistrement des activités Temporal (worker.py ou équivalent).
Lister toutes les activités actuellement enregistrées.
Préparer la liste des 4 nouvelles activités à ajouter en Phase 3 :
  - conformity_activity
  - security_activity
  - architecture_activity
  - build_supervisor_activity

### P0.7 — Fichiers obsolètes à archiver

factory-sprint0/plan.md :
  Ce fichier contient l'ancien plan de 9 fixes (sanitizers, ensure_tsconfig, etc.).
  Ajouter en tête de fichier : "# OBSOLÈTE — Superseded par SPRINT46_V2_PLAN.md (20 Mars 2026)"

factory-sprint0/CODEX_SPRINT46_SPEC.md (si existe) :
  Même traitement — marquer comme superseded.

### P0.8 — dev_test_agent.py nettoyage préliminaire

Supprimer :
  - _run_critique_phase() et tous ses appels
  - _run_async_safely() (utilisé uniquement par _run_critique_phase)
  - Les imports de run_conformity_agent et run_security_agent
  - Les 4 métriques critique_* dans le bloc metadata (elles seront remplacées
    par les nouvelles métriques per-file dans la Phase 3)
  - Le shadow log event "critique_phase"

---

## PHASE 1 — ARCHITECTURE & CONTRATS (Claude)
### Prérequis : Phase 0 complète.

### P1.1 — supervision_routing dans nextjs-clerk-prisma.json

```json
"supervision_routing": {
  "app/api/**/*.ts":        ["conformity", "security"],
  "app/**/*.tsx":           ["conformity", "architecture"],
  "app/**/*.ts":            ["conformity", "architecture"],
  "prisma/schema.prisma":   ["architecture"],
  "lib/**/*.ts":            ["conformity"],
  "**/*.test.*":            [],
  "**/*.config.*":          [],
  "**/*.css":               []
}
```

Note : les clés sont des glob patterns. Le Python dispatcher utilise fnmatch ou pathlib.
Note : les valeurs sont des identifiants de superviseurs, pas des noms de fonction.
Le dispatcher lit ces identifiants et mappe vers l'activité Temporal correspondante.

### P1.2 — Contrats JSON pour les 4 activités

schemas/contracts/conformity_agent_contract.json (mise à jour v2) :
```json
{
  "agent_name": "conformity_supervisor",
  "version": "2.0.0",
  "description": "Supervision inline per-file — conformité structurelle ET sémantique",
  "input_schema": {
    "type": "object",
    "required": ["file_path", "file_content", "requirements", "plan"],
    "additionalProperties": false,
    "properties": {
      "file_path":     { "type": "string" },
      "file_content":  { "type": "string" },
      "requirements":  { "type": "array", "items": { "type": "string" } },
      "plan":          { "type": "object" },
      "files_so_far":  { "type": "object", "description": "Fichiers déjà générés et validés" },
      "project_name":  { "type": "string" },
      "run_id":        { "type": "string" },
      "stack_id":      { "type": "string" }
    }
  },
  "output_schema": {
    "type": "object",
    "required": ["status", "confidence"],
    "additionalProperties": false,
    "properties": {
      "status":          { "type": "string", "enum": ["ok", "needs_fix", "skipped"] },
      "confidence":      { "type": "number", "minimum": 0, "maximum": 1 },
      "fix_instruction": { "$ref": "#/definitions/fix_instruction" },
      "note":            { "type": "string" }
    },
    "definitions": {
      "fix_instruction": {
        "type": "object",
        "required": ["file", "problem", "fix"],
        "additionalProperties": false,
        "properties": {
          "file":             { "type": "string" },
          "problem":          { "type": "string" },
          "fix":              { "type": "string" },
          "lines_concerned":  { "type": "array", "items": { "type": "integer" } }
        }
      }
    }
  },
  "calibration": {
    "confidence_threshold_block": 0.7,
    "confidence_threshold_observe": 0.5,
    "non_blocking": false,
    "max_retries": 1
  }
}
```

schemas/contracts/security_agent_contract.json (mise à jour v2) :
  Même structure que conformity. Champ supplémentaire dans input : aucun.
  output : même format. severity dans fix_instruction : "high|medium|low".

schemas/contracts/architecture_agent_contract.json (nouveau) :
  input : file_path, file_content, prisma_schema (string), plan, files_so_far, run_id, stack_id
  output : status, confidence, fix_instruction (même format)

schemas/contracts/build_supervisor_contract.json (nouveau) :
```json
{
  "agent_name": "build_supervisor",
  "version": "1.0.0",
  "description": "Analyse post-build — instruction ciblée sur la zone défaillante uniquement",
  "input_schema": {
    "required": ["build_stderr", "combined_files"],
    "properties": {
      "build_stderr":    { "type": "string" },
      "combined_files":  { "type": "object" },
      "run_id":          { "type": "string" },
      "stack_id":        { "type": "string" }
    }
  },
  "output_schema": {
    "required": ["status"],
    "properties": {
      "status":          { "type": "string", "enum": ["ok", "needs_fix", "skipped"] },
      "failing_file":    { "type": "string" },
      "fix_instruction": { "$ref": "#/definitions/fix_instruction" }
    }
  }
}
```

### P1.3 — Mise à jour dev_test_agent_contract.json (metadata)

Remplacer les 4 métriques critique_* par les nouvelles métriques inline :
```json
"supervisor_corrections_count": { "type": "integer" },
"supervisor_files_reviewed":    { "type": "integer" },
"conformity_score":             { "type": "number", "minimum": 0, "maximum": 1 },
"security_score":               { "type": "number", "minimum": 0, "maximum": 1 },
"architecture_score":           { "type": "number", "minimum": 0, "maximum": 1 },
"build_corrections_count":      { "type": "integer" }
```

---

## PHASE 2 — PROMPTS & STANDARDS (Claude)
### Prérequis : Phase 1 complète.

### P2.1 — Réécriture prompts/base/conformity.md

Le prompt doit instruire l'agent sur DEUX niveaux de vérification :

NIVEAU 1 — Structurel :
  Le fichier à la bonne route couvre-t-il un requirement attendu ?
  (ex: app/products/page.tsx → requirement "Page: /products")

NIVEAU 2 — Sémantique (le niveau qui manquait) :
  Le CONTENU du fichier fait-il réellement ce que le brief demande ?
  Exemples :
  - La page /products AFFICHE-T-ELLE des produits avec prix + bouton achat ?
    Pas juste "<div>Products</div>" statique.
  - Le handler POST /api/orders CRÉE-T-IL une commande avec productId + buyerId ?
    Pas juste un return Response.json({ok: true}).
  - Le dashboard FILTRE-T-IL par userId/authorId ou expose-t-il toutes les données ?

Format de réponse OBLIGATOIRE : JSON strict (response_format=json_object).
Si status=needs_fix, fix_instruction DOIT être présent avec file + problem + fix + lines_concerned.
Si confidence < 0.5, retourner status=skipped (ne pas bloquer sur incertitude).

### P2.2 — Création prompts/base/architecture.md

L'agent vérifie la cohérence entre le fichier courant et le reste du projet :

Vérifications principales :
1. Les champs obligatoires du modèle Prisma sont-ils créés dans les handlers ?
   (ex: un Post nécessite authorId → POST /api/posts doit définir authorId: userId)
2. Les relations Prisma sont-elles exploitées correctement dans les composants ?
   (ex: Order a une relation vers Product → la page Orders doit afficher product.name, pas productId)
3. Les imports entre fichiers sont-ils valides ?
   (ex: import depuis "@/lib/prisma" → lib/prisma.ts doit exister dans files_so_far)
4. Les types TypeScript sont-ils cohérents avec le schéma ?
   (ex: si Prisma a price: Float, le composant ne doit pas traiter price comme une String)

Format de réponse : identique à conformity (status/confidence/fix_instruction).

### P2.3 — Création prompts/base/build_supervisor.md

L'agent analyse un stderr de build et identifie chirurgicalement la cause.

Comportement attendu :
1. Lire le stderr — extraire le(s) fichier(s) et ligne(s) responsables
2. Lire le contenu de ce(s) fichier(s) dans combined_files
3. Identifier la correction minimale suffisante pour résoudre l'erreur
4. Retourner une fix_instruction pointant exactement vers les lignes à modifier

Règle critique : NE PAS suggérer de réécriture complète. Correction chirurgicale uniquement.
Si l'erreur est dans un fichier template protégé → status=skipped (ne jamais toucher les templates).

### P2.4 — Mise à jour prompts/stacks/nextjs-clerk-prisma/rules_conformity.md

Ajouter des exemples de conformité SÉMANTIQUE spécifiques à la stack :

Exemple conforme (sémantique) :
```tsx
// app/products/page.tsx — CORRECT
const products = await fetch('/api/products').then(r => r.json())
return <ul>{products.map(p => <li key={p.id}>{p.name} — {p.price}€ <button>Acheter</button></li>)}</ul>
```

Exemple non conforme (structurel ok, sémantique KO) :
```tsx
// app/products/page.tsx — MAUVAIS : fichier existe mais contenu vide
export default function ProductsPage() {
  return <div>Products</div>
}
```

### P2.5 — Création prompts/stacks/nextjs-clerk-prisma/rules_architecture.md

Règles de cohérence architecturale spécifiques Next.js/Clerk/Prisma :
- Tout modèle Prisma avec authorId doit avoir ses routes filtrées par userId Clerk
- Les relations Prisma (ex: Order → Product via productId) doivent être incluses avec include:{} dans les queries list
- Chaque import @/lib/prisma suppose que lib/prisma.ts existe (template protégé — toujours présent)
- Les Server Components Next.js 14 n'ont pas accès à useState — si besoin d'état, 'use client' obligatoire

### P2.6 — Mise à jour create_full_standards_v1.py

ZONE_15 (conformity) — enrichir avec :
  - Standard : conformité sémantique (page qui fait vs page qui existe)
  - Standard : handler qui implémente la logique métier vs handler retournant un stub
  - Conserver les standards structurels existants

ZONE_16 (security) — enrichir avec :
  - Retirer toute mention de guard ou sanitizer
  - Ajouter standard : pattern auth() Clerk v6 obligatoire avant Prisma (avec EXEMPLE_VALIDE complet)

ZONE_17 (architecture) — créer, 5 standards minimum :
  - Cohérence authorId Prisma ↔ userId Clerk dans les routes
  - Relations Prisma exploitées dans les composants (include vs ID brut)
  - Imports valides entre fichiers générés
  - Types TypeScript cohérents avec le schema Prisma
  - Server Component vs Client Component (règle useState)

---

## PHASE 3 — IMPLÉMENTATION CODEX
### Prérequis : Phases 0, 1, 2 complètes.
### C1-C5 peuvent être exécutées en parallèle. C6 dépend de C1-C4. C7-C9 parallèles avec C1-C5.

---

### C1 — Refactoring conformity_agent.py + création conformity_activity.py

**conformity_agent.py — nouvelle signature :**
```python
async def run_conformity_supervisor(
    file_path: str,
    file_content: str,
    requirements: list[str],
    plan: dict,
    files_so_far: dict[str, str] | None = None,
    project_name: str = "",
    run_id: str = "",
    stack_id: str = "nextjs-clerk-prisma",
) -> dict:
    """
    Supervision inline per-file.
    Vérifie conformité structurelle ET sémantique d'un fichier unique.
    Retourne toujours un dict, jamais d'exception.
    Format conforme à conformity_agent_contract.json v2.
    """
```

Supprimer : run_conformity_agent() (ancienne signature combined_files)
Supprimer : _budgeted_files_view() (n'est plus nécessaire — on passe un fichier unique)
Conserver : _strip_json_fences(), _compute_score() (utile pour score agrégé par run)
Conserver : _normalize_coverage() (peut servir pour le rapport Learner)

Le LLM reçoit :
  - Le fichier unique (path + contenu complet)
  - Les requirements du projet
  - Un résumé du plan (data_models, pages, routes — pas les fichiers complets)
  - Les paths des fichiers déjà générés (pas leur contenu, sauf schema.prisma)

**workflows/activities/conformity_activity.py — nouveau fichier :**
```python
from temporalio import activity
from agents.conformity_agent import run_conformity_supervisor

@activity.defn(name="conformity_activity")
async def conformity_activity(input_data: dict) -> dict:
    return await run_conformity_supervisor(
        file_path=input_data["file_path"],
        file_content=input_data["file_content"],
        requirements=input_data.get("requirements", []),
        plan=input_data.get("plan", {}),
        files_so_far=input_data.get("files_so_far", {}),
        project_name=input_data.get("project_name", ""),
        run_id=input_data.get("run_id", ""),
        stack_id=input_data.get("stack_id", "nextjs-clerk-prisma"),
    )
```

---

### C2 — Refactoring security_agent.py + création security_activity.py

**security_agent.py — nouvelle signature :**
```python
async def run_security_supervisor(
    file_path: str,
    file_content: str,
    prisma_schema: str = "",
    project_name: str = "",
    run_id: str = "",
    stack_id: str = "nextjs-clerk-prisma",
) -> dict:
    """
    Supervision inline per-file — routes API uniquement.
    Retourne toujours un dict, jamais d'exception.
    Format conforme à security_agent_contract.json v2.
    """
```

Supprimer : run_security_agent() (ancienne signature api_files dict global)
Supprimer : _HANDLER_RE (pattern Next.js hardcodé — violation multi-stack)
Supprimer : _count_handlers() (inutile en mode per-file)
Supprimer : le filtre "app/api/webhooks/" codé en dur — ce filtre va dans supervision_routing JSON

Note multi-stack : la détection "est-ce un fichier API ?" est gérée par supervision_routing
dans le JSON. security_agent.py reçoit uniquement des fichiers API — pas besoin de filtrer.

**workflows/activities/security_activity.py — nouveau fichier :**
```python
@activity.defn(name="security_activity")
async def security_activity(input_data: dict) -> dict:
    return await run_security_supervisor(
        file_path=input_data["file_path"],
        file_content=input_data["file_content"],
        prisma_schema=input_data.get("prisma_schema", ""),
        project_name=input_data.get("project_name", ""),
        run_id=input_data.get("run_id", ""),
        stack_id=input_data.get("stack_id", "nextjs-clerk-prisma"),
    )
```

---

### C3 — Création architecture_agent.py + architecture_activity.py

**architecture_agent.py — nouveau fichier :**
```python
async def run_architecture_supervisor(
    file_path: str,
    file_content: str,
    prisma_schema: str = "",
    plan: dict | None = None,
    files_so_far: dict[str, str] | None = None,
    project_name: str = "",
    run_id: str = "",
    stack_id: str = "nextjs-clerk-prisma",
) -> dict:
    """
    Vérifie cohérence inter-fichiers :
    - Champs obligatoires Prisma présents dans les handlers
    - Relations Prisma exploitées (include, pas juste ID)
    - Imports valides vers fichiers existants
    - Types cohérents avec le schema
    Retourne toujours un dict, jamais d'exception.
    Format conforme à architecture_agent_contract.json.
    """
```

Structure interne identique aux autres superviseurs :
  _load_system_prompt("architecture", stack_id) via load_base_prompt + load_stack_rules_only
  LLM : gpt-4o-mini, temperature=0.0, response_format=json_object
  _strip_json_fences() → json.loads → validation output

**workflows/activities/architecture_activity.py — nouveau fichier :**
```python
@activity.defn(name="architecture_activity")
async def architecture_activity(input_data: dict) -> dict:
    return await run_architecture_supervisor(**input_data)
```

---

### C4 — Création build_supervisor_agent.py + build_supervisor_activity.py

**build_supervisor_agent.py — nouveau fichier :**
```python
async def run_build_supervisor(
    build_stderr: str,
    combined_files: dict[str, str],
    run_id: str = "",
    stack_id: str = "nextjs-clerk-prisma",
) -> dict:
    """
    Analyse le stderr d'un build raté.
    Retourne une fix_instruction ciblée sur la zone défaillante.
    Ne jamais suggérer une réécriture complète.
    Retourne toujours un dict, jamais d'exception.
    Format conforme à build_supervisor_contract.json.
    """
```

Logique :
  1. Parser le stderr pour extraire file + line (pattern Next.js/TypeScript errors)
  2. Extraire le contenu du fichier défaillant depuis combined_files
  3. Envoyer au LLM : stderr + fichier défaillant + instruction "correction minimale"
  4. Retourner fix_instruction avec file + problem + fix + lines_concerned

**workflows/activities/build_supervisor_activity.py — nouveau fichier :**
```python
@activity.defn(name="build_supervisor_activity")
async def build_supervisor_activity(input_data: dict) -> dict:
    return await run_build_supervisor(**input_data)
```

---

### C5 — Tests tests/test_sprint46_v2_validation.py

Supprimer d'abord : tests/test_sprint46_validation.py (obsolète — tests post-génération)

Créer : tests/test_sprint46_v2_validation.py avec les blocs suivants :

```python
# BLOC 1 — Conformité structurelle : fichier présent et non-stub
def test_conformity_supervisor_detects_stub_page():
    # Fichier : app/products/page.tsx avec contenu "<div>Products</div>"
    # Requirement : "Page: /products affichant la liste des produits"
    # Attendu : status=needs_fix, confidence > 0.7

# BLOC 2 — Conformité sémantique : fichier complet et conforme
def test_conformity_supervisor_validates_complete_page():
    # Fichier : app/products/page.tsx avec fetch + mapping + affichage
    # Attendu : status=ok

# BLOC 3 — Sécurité : handler sans auth
def test_security_supervisor_detects_missing_auth():
    # Fichier : app/api/posts/route.ts sans auth() avant db.post.create()
    # Attendu : status=needs_fix, fix_instruction.lines_concerned non vide

# BLOC 4 — Sécurité : handler conforme
def test_security_supervisor_validates_secure_handler():
    # Fichier avec auth() + authorId filter
    # Attendu : status=ok

# BLOC 5 — Architecture : relation Prisma non exploitée
def test_architecture_supervisor_detects_missing_include():
    # Fichier : page Orders affichant order.productId au lieu de order.product.name
    # Schema Prisma : Order { product Product @relation(...) }
    # Attendu : status=needs_fix

# BLOC 6 — Build supervisor : fix ciblé
def test_build_supervisor_returns_targeted_fix():
    # stderr TypeScript avec erreur précise sur un fichier
    # Attendu : fix_instruction.file == fichier défaillant

# BLOC 7 — Tous les superviseurs : jamais d'exception
def test_all_supervisors_never_raise():
    # Appel avec contenu vide, plan vide, fichiers vides
    # Attendu : retour dict valide, status=skipped, pas d'exception

# BLOC 8 — Supervision routing : dispatch correct
def test_supervision_routing_matches_file_types():
    # Tester _match_supervision_routing() avec différents file_path
    # "app/api/posts/route.ts" → ["conformity", "security"]
    # "app/products/page.tsx" → ["conformity", "architecture"]
    # "tests/post.test.ts" → []
```

---

### C6 — Intégration inline dans dev_test_agent.py (tâche critique — dépend de C1-C4)

**Nouvelle fonction à créer dans dev_test_agent.py :**

```python
def _match_supervision_routing(
    file_path: str,
    routing: dict[str, list[str]]
) -> list[str]:
    """
    Retourne la liste des superviseurs à appeler pour ce fichier.
    Utilise fnmatch pour matcher les patterns glob du JSON.
    """
    from fnmatch import fnmatch
    norm = file_path.replace("\\", "/")
    for pattern, supervisors in routing.items():
        if fnmatch(norm, pattern):
            return supervisors
    return []


async def _supervise_file(
    file_path: str,
    file_content: str,
    context: dict,  # {requirements, plan, files_so_far, prisma_schema, project_name, run_id, stack_id}
    supervisors: list[str],
) -> dict:
    """
    Lance les superviseurs applicables en parallèle.
    Retourne un dict {supervisor_id: result} ou {} si aucun superviseur.
    Non-bloquant : exceptions capturées et loggées.
    """
```

**Intégration dans la boucle Dev :**

Après chaque write_file() réussi dans le dev loop :
1. Lire supervision_routing depuis stack_cfg
2. Appeler _match_supervision_routing(file_path, routing)
3. Si liste non vide → appeler _supervise_file() avec le contexte courant
4. Pour chaque résultat avec status=needs_fix et confidence > 0.7 :
   - Construire un message de correction à partir de fix_instruction
   - Injecter dans le contexte Dev comme instruction à traiter avant le fichier suivant
5. Le Dev corrige le fichier en question uniquement
6. Le superviseur est rappelé pour re-vérification (max 1 fois)

**Après tous les fichiers générés :**
- Appeler run_tsc_check() + run_prisma_validate() en parallèle
- Si erreurs → appeler build_supervisor_activity pour fix ciblé
- Dev corrige → pas de re-passage par les superviseurs inline (déjà validés)

**Métriques à calculer et injecter dans metadata :**
```python
"supervisor_files_reviewed":    count(fichiers supervisés)
"supervisor_corrections_count": count(corrections appliquées inline)
"conformity_score":             mean(confidence scores conformity)
"security_score":               mean(confidence scores security)
"architecture_score":           mean(confidence scores architecture)
"build_corrections_count":      count(corrections post-build)
```

**Shadow log — nouveau format per-file :**
```python
_write_learner_event(
    event_type="supervisor_file_reviewed",
    payload={
        "file_path": file_path,
        "supervisors": ["conformity", "security"],
        "results": {
            "conformity": {"status": "ok", "confidence": 0.92},
            "security": {"status": "needs_fix", "confidence": 0.87, "fix_applied": True}
        },
        "project_name": ...,
        "stack_id": ...,
    },
    run_id=run_id,
)
```

---

### C7 — Suppression guards dans shared_tools.py (parallèle à C1-C5)

Exécuter le nettoyage défini en P0.1 :
Supprimer les fonctions et leurs appels listés.
Vérifier après suppression qu'aucun import externe ne référence ces fonctions.
Lancer les tests existants pour confirmer que rien de critique n'est cassé.

---

### C8 — Mise à jour Temporal worker (parallèle à C1-C5)

Identifier le fichier d'enregistrement des activités (worker.py ou factory_worker.py).
Ajouter les 4 imports et enregistrements :
```python
from workflows.activities.conformity_activity import conformity_activity
from workflows.activities.security_activity import security_activity
from workflows.activities.architecture_activity import architecture_activity
from workflows.activities.build_supervisor_activity import build_supervisor_activity

# Dans la liste des activities du worker :
activities=[
    ...,  # existants
    conformity_activity,
    security_activity,
    architecture_activity,
    build_supervisor_activity,
]
```

---

### C9 — Mise à jour Learner Activity (parallèle à C1-C5)

learner.py doit lire les nouveaux événements shadow log :

Nouveau type d'événement à lire : "supervisor_file_reviewed"
  - Champs : file_path, supervisors, results (status/confidence/fix_applied par superviseur)

Logique Learner mise à jour :
  - Comptabiliser les corrections par superviseur par run
  - Pattern récurrent = même type de correction sur 3+ runs consécutifs sur le même type de fichier
  - Générer StandardSuggestion avec :
    - supervisor_type : conformity|security|architecture
    - file_type : app/api/*.ts | app/*.tsx | etc.
    - pattern : description du problème récurrent
    - proposed_standard : règle prescriptive (INTERDIT X / OBLIGATOIRE Y)
    - confidence : fréquence / 10
    - evidence : [run_ids]
    - zone_target : ZONE_15 | ZONE_16 | ZONE_17

Conserver : lecture des événements existants (build_error, tool_patch_applied)
  → le Learner agrège toutes les sources de signal

---

## PHASE 4 — VALIDATION (Claude supervise)
### Prérequis : Phase 3 complète.

### V1 — Vérification contrats et signatures
  - Chaque agent retourne bien le format du contrat v2
  - fix_instruction présent si status=needs_fix
  - confidence toujours dans [0, 1]
  - Aucun agent ne lève d'exception sur input vide/invalide

### V2 — Tests automatiques
  pytest tests/test_sprint46_v2_validation.py -v
  Tous les blocs (8) doivent passer.
  Pas de test_sprint46_validation.py dans le projet (supprimé en P0.5).

### V3 — Rebuild Docker + Qdrant
  python scripts/reset_qdrant.py
  python scripts/create_full_standards_v1.py
  Vérifier ZONE_15 (enrichie) + ZONE_16 (enrichie) + ZONE_17 (nouvelle) dans Qdrant.
  docker compose up --build -d factory-worker

### V4 — 3 runs de validation
  python scripts/run_batch.py --size 3
  Projets : marketplace-mvp, habit-tracker, invoice-generator
  Vérifier dans shadow log :
    - Événements "supervisor_file_reviewed" présents pour chaque run
    - conformity_score > 0.75 sur au moins 2 projets
    - security_score > 0.80 sur au moins 2 projets
    - supervisor_corrections_count > 0 (les superviseurs ont travaillé)

### V5 — Dashboard Temporal
  Confirmer visibilité des 4 nouvelles activities :
    conformity_activity, security_activity, architecture_activity, build_supervisor_activity
  Chaque activity doit apparaître dans le dashboard lors d'un run en direct.

### V6 — Signal de clôture Sprint 4.6
  ✅ Guards supprimés de shared_tools.py
  ✅ test_sprint46_validation.py supprimé, test_sprint46_v2_validation.py (8 blocs) vert
  ✅ 4 Temporal Activities visibles sur le dashboard
  ✅ Supervision inline active (supervisor_file_reviewed dans shadow log)
  ✅ Fix instructions chirurgicales (file + problem + fix + lines_concerned)
  ✅ supervision_routing déclaré dans nextjs-clerk-prisma.json
  ✅ ZONE_15 + ZONE_16 enrichies + ZONE_17 créée (≥5 standards chacune)
  ✅ conformity_score > 0.75 ET security_score > 0.80 sur ≥2 projets
  ✅ Learner lit les nouveaux événements per-file

---

## RÉCAPITULATIF FICHIERS TOUCHÉS

| Fichier | Action | Owner | Phase |
|---------|--------|-------|-------|
| shared_tools.py | Suppression guards + sanitizers + SANITIZER_REGISTRY | Claude+Codex | P0.1 / C7 |
| dev_test_agent.py | Suppression _run_critique_phase, ajout supervision inline | Codex | P0.8 / C6 |
| test_sprint46_validation.py | Suppression | Claude | P0.5 |
| plan.md | Archivage (header obsolète) | Claude | P0.7 |
| conformity_agent.py | Refactoring per-file sémantique | Codex | C1 |
| security_agent.py | Refactoring per-file, suppression _HANDLER_RE | Codex | C2 |
| architecture_agent.py | Création | Codex | C3 |
| build_supervisor_agent.py | Création | Codex | C4 |
| conformity_activity.py | Création Temporal Activity | Codex | C1 |
| security_activity.py | Création Temporal Activity | Codex | C2 |
| architecture_activity.py | Création Temporal Activity | Codex | C3 |
| build_supervisor_activity.py | Création Temporal Activity | Codex | C4 |
| worker.py (ou équivalent) | Enregistrement 4 nouvelles activités | Codex | C8 |
| learner.py | Lecture nouveaux événements per-file | Codex | C9 |
| test_sprint46_v2_validation.py | Création (8 blocs) | Codex | C5 |
| nextjs-clerk-prisma.json | Ajout supervision_routing, nettoyage sanitizers | Claude | P0.4 / P1.1 |
| conformity_agent_contract.json | Mise à jour v2 (per-file, sémantique) | Claude | P1.2 |
| security_agent_contract.json | Mise à jour v2 (per-file) | Claude | P1.2 |
| architecture_agent_contract.json | Création | Claude | P1.2 |
| build_supervisor_contract.json | Création | Claude | P1.2 |
| dev_test_agent_contract.json | Nouvelles métriques supervisor | Claude | P1.3 |
| prompts/dev.md | Retrait instructions mortes | Claude | P0.2 |
| rules_dev.md | Retrait instructions compensatoires | Claude | P0.2 |
| prompts/base/conformity.md | Réécriture sémantique | Claude | P2.1 |
| prompts/base/architecture.md | Création | Claude | P2.2 |
| prompts/base/build_supervisor.md | Création | Claude | P2.3 |
| rules_conformity.md | Ajout exemples sémantiques | Claude | P2.4 |
| rules_architecture.md | Création | Claude | P2.5 |
| create_full_standards_v1.py | ZONE_15/16 enrichies + ZONE_17 | Claude | P2.6 |

---

## DÉPENDANCES ENTRE PHASES

Phase 0 → Phase 1 → Phase 2 → Phase 3 (C1-C9) → Phase 4

Phase 3 interne :
  C1, C2, C3, C4, C5, C7, C8, C9 : parallèles
  C6 : dépend de C1 + C2 + C3 + C4

---

## RISQUES MULTI-AGENTS — MITIGATIONS EN PLACE

| Risque | Mitigation dans ce plan |
|--------|------------------------|
| Coût tokens élevé | supervision_routing : seuls les fichiers pertinents sont supervisés. gpt-4o-mini pour tous les superviseurs. Templates exclus. |
| Hallucination superviseur | Score de confiance obligatoire. Si confidence < 0.7 → observation uniquement, pas de blocage. Learner track les faux positifs. |
| Manque RAG | Chaque superviseur fait sa propre query RAG (ZONE_15/16/17) avant de juger. Si RAG vide → status=skipped. |
| Calibration prompts | Calibration sur 10 runs avant activation mode bloquant complet. Seuil de confiance progressif. |
| Multi-stack | supervision_routing dans JSON. _HANDLER_RE supprimé. rules_*.md par stack. Aucun pattern stack-specific en Python. |
| Superviseur trop sévère | max 1 re-vérification par fichier. Si après correction le superviseur maintient needs_fix → observation, ne bloque pas. |
| Boucle infinie | Max 1 itération corrective par fichier par superviseur. Après correction : supervision skippée pour ce fichier. |
