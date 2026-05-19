# agents/architect.py
from __future__ import annotations

import json
import logging
import operator
from typing import List, TypedDict, Annotated

from temporalio.exceptions import ApplicationError
from pydantic import BaseModel, Field

from agents.stack_config import _DEFAULT_STACK_ID

logger = logging.getLogger(__name__)

# ── Prompt LLM pour brief_writer_node ────────────────────────────────────────
# Hardcodé (pas de RAG) — règles stables qui ne changent pas entre projets.
# Mise à jour ici si la stack évolue (ex: Prisma 8, Clerk V7).

_BRIEF_WRITER_SYSTEM_PROMPT = """\
Tu es un architecte logiciel expert de la stack Next.js 14 + Clerk V5 + Prisma 7 + PostgreSQL.
Ta mission : convertir un brief en langage naturel en une spec JSON structurée prête pour le générateur de code.

## RÈGLES STACK (NON NÉGOCIABLES)

### Auth
- Auth = Clerk V5 uniquement. JAMAIS : bcrypt, jwt, password, next-auth, /api/auth/register, /api/auth/login
- **TOUS les modèles sans exception** (y compris les lookups : Category, Tag, Type, Label...) DOIVENT avoir `userId String`.
  La factory est single-tenant : chaque utilisateur possède SES propres catégories, tags, etc.
  Ne jamais créer un modèle sans `userId String`, même pour les lookups partagés en apparence.
  Exception autorisée : `authorId String` à la place de `userId String` pour le modèle principal d'un CMS/blog (Post, Article, Recipe).
- Les sous-modèles enfants (ex: Comment d'une Task) utilisent le FK du parent ET ont aussi `userId String` en propre.

### Champs obligatoires dans tout modèle
- `id String @id @default(uuid())`
- `createdAt DateTime @default(now())`

### Relations — déclaration stricte
- Le modèle ENFANT déclare : `taskId String` + `task Task @relation(fields: [taskId], references: [id], onDelete: Cascade)`
- Le modèle PARENT déclare juste : `comments Comment[]`
- Ne jamais déclarer @relation sur les deux côtés

### Format des modèles (CRITIQUE)
Chaque modèle est une STRING avec tous les champs séparés par des VIRGULES sur une seule ligne :
`"ModelName { field1 Type1 attrs1, field2 Type2 attrs2, ... }"`
Les virgules DANS les attributs comme @relation(..., ...) ne comptent PAS comme séparateurs.

### Enums
`{ "NomEnum": ["valeur1", "valeur2"] }` — valeurs en snake_case minuscules

### Pages — pattern standard
- `/` : home publique (auth: false, page_type: "custom")
- `/{model-kebab}` : liste (auth: true, sauf si contenu public comme un blog)
- `/{model-kebab}/new` : création (auth: true TOUJOURS)
- `/{model-kebab}/[id]` : détail par id (auth selon visibilité)
- `/{model-kebab}/[slug]` : détail par slug si le modèle a un champ `slug` (page_type: "detail-slug", auth: false)
- Ne PAS générer `/[id]/edit` sauf si le brief le demande explicitement

### Routes API
Les Server Actions gèrent le CRUD → `"routes": []` dans la grande majorité des cas.
Ajouter des routes seulement pour : webhooks, exports CSV, endpoints publics stateless.

## FORMAT DE SORTIE — JSON uniquement, aucun markdown, aucun commentaire

```json
{
  "models": ["ModelName { field Type attrs, field Type attrs, ... }", ...],
  "enums": { "EnumName": ["val1", "val2"] },
  "pages": [
    {"path": "/", "auth": false, "page_type": "custom"},
    {"path": "/tasks", "auth": true, "model": "Task", "page_type": "list"},
    {"path": "/tasks/new", "auth": true, "model": "Task", "page_type": "create"},
    {"path": "/tasks/[id]", "auth": true, "model": "Task", "page_type": "detail"}
  ],
  "routes": [],
  "user_flows": ["L'utilisateur crée une tâche depuis /tasks/new", ...]
}
```

page_type valeurs autorisées : "list" | "create" | "detail" | "detail-slug" | "custom"

## EXEMPLES

### Exemple 1 — Task Manager avec commentaires

Brief : "Une app de gestion de tâches. Les utilisateurs créent des tâches avec titre, description et statut (pending/in_progress/done). Ils peuvent commenter chaque tâche."

Sortie :
{
  "models": [
    "Task { id String @id @default(uuid()), title String, description String?, status TaskStatus @default(pending), userId String, createdAt DateTime @default(now()), comments Comment[] }",
    "Comment { id String @id @default(uuid()), content String, taskId String, task Task @relation(fields: [taskId], references: [id], onDelete: Cascade), userId String, createdAt DateTime @default(now()) }"
  ],
  "enums": {
    "TaskStatus": ["pending", "in_progress", "done"]
  },
  "pages": [
    {"path": "/", "auth": false, "page_type": "custom"},
    {"path": "/tasks", "auth": true, "model": "Task", "page_type": "list"},
    {"path": "/tasks/new", "auth": true, "model": "Task", "page_type": "create"},
    {"path": "/tasks/[id]", "auth": true, "model": "Task", "page_type": "detail"}
  ],
  "routes": [],
  "user_flows": [
    "L'utilisateur crée une tâche depuis /tasks/new",
    "L'utilisateur consulte sa liste de tâches à /tasks",
    "L'utilisateur lit le détail et commente à /tasks/[id]"
  ]
}

### Exemple 2 — Blog public avec catégories

Brief : "Un blog avec des articles publics (visibles sans connexion). Chaque article a un titre, contenu, slug unique et une catégorie. Les auteurs gèrent leurs articles depuis leur espace connecté."

Sortie :
{
  "models": [
    "Category { id String @id @default(uuid()), name String @unique, userId String, posts Post[], createdAt DateTime @default(now()) }",
    "Post { id String @id @default(uuid()), title String, content String, slug String @unique, status PostStatus @default(draft), categoryId String, category Category @relation(fields: [categoryId], references: [id]), authorId String, createdAt DateTime @default(now()) }"
  ],
  "enums": {
    "PostStatus": ["draft", "published"]
  },
  "pages": [
    {"path": "/", "auth": false, "page_type": "custom"},
    {"path": "/posts", "auth": false, "model": "Post", "page_type": "list"},
    {"path": "/posts/new", "auth": true, "model": "Post", "page_type": "create"},
    {"path": "/posts/[slug]", "auth": false, "model": "Post", "page_type": "detail-slug"}
  ],
  "routes": [],
  "user_flows": [
    "Un visiteur parcourt les articles à /posts",
    "Un visiteur lit un article à /posts/[slug]",
    "Un auteur connecté crée un article depuis /posts/new"
  ]
}

### Exemple 3 — SaaS multi-modèle (expense tracker avec catégories)

Brief : "Un gestionnaire de dépenses. Chaque utilisateur crée des dépenses avec montant, description et catégorie. Les catégories sont gérées séparément."

Sortie :
{
  "models": [
    "Category { id String @id @default(uuid()), name String, userId String, expenses Expense[], createdAt DateTime @default(now()) }",
    "Expense { id String @id @default(uuid()), title String, amount Float, description String?, categoryId String, category Category @relation(fields: [categoryId], references: [id]), userId String, createdAt DateTime @default(now()) }"
  ],
  "enums": {},
  "pages": [
    {"path": "/", "auth": false, "page_type": "custom"},
    {"path": "/categories", "auth": true, "model": "Category", "page_type": "list"},
    {"path": "/categories/new", "auth": true, "model": "Category", "page_type": "create"},
    {"path": "/expenses", "auth": true, "model": "Expense", "page_type": "list"},
    {"path": "/expenses/new", "auth": true, "model": "Expense", "page_type": "create"},
    {"path": "/expenses/[id]", "auth": true, "model": "Expense", "page_type": "detail"}
  ],
  "routes": [],
  "user_flows": [
    "L'utilisateur crée une catégorie depuis /categories/new",
    "L'utilisateur saisit une dépense depuis /expenses/new",
    "L'utilisateur consulte ses dépenses à /expenses"
  ]
}

Retourne UNIQUEMENT le JSON, sans balises markdown ni explication.\
"""


# ── Output contracts ─────────────────────────────────────────────────────────

class SpecOutput(BaseModel):
    """IR structuré de la spec — complément JSON du markdown brut."""
    spec_summary: str = Field(default="")
    entities_in_spec: list = Field(default_factory=list)
    missing_entities: list = Field(default_factory=list)
    pages_in_spec: list = Field(default_factory=list)
    routes_in_spec: list = Field(default_factory=list)


class ArchitectOutput(BaseModel):
    specification: str = Field(description="Résumé de la spec (ProjectSpec remplace le texte libre).")
    mermaid_diagram: str = Field(default="")
    requirements: list = Field(default_factory=list)
    user_flows: list = Field(default_factory=list)
    ir_schema: list = Field(default_factory=list)
    ir_pages: list = Field(default_factory=list)
    ir_routes: list = Field(default_factory=list)
    spec_structured: SpecOutput = Field(default_factory=SpecOutput)


class AgentState(TypedDict):
    messages: Annotated[List, operator.add]
    brief: dict
    rag_context: str
    plan: dict
    specification: str
    mermaid_diagram: str
    architect_output: ArchitectOutput
    run_id: str
    stack_id: str
    project_name: str
    requirements: list
    user_flows: list
    spec_structured: dict
    project_spec: dict


# ── Prisma DSL helpers (module-level — pas de dépendance closure) ─────────────

def _split_fields(raw: str) -> list[str]:
    """Découpe les champs Prisma en respectant les virgules dans les parenthèses/crochets."""
    parts, current, depth = [], [], 0
    for ch in raw:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    if current:
        parts.append("".join(current))
    return parts


def _detect_owner_field(fields: list) -> str:
    """Déduit le champ d'ownership (userId, authorId, ou premier xxxId)."""
    field_names = [f.name for f in fields]
    if "userId" in field_names:
        return "userId"
    if "authorId" in field_names:
        return "authorId"
    for fname in field_names:
        if fname != "id" and fname.endswith("Id"):
            return fname
    return "userId"


def _parse_model_str(model_str: str):
    """Convertit une string Prisma DSL 'Name { field Type attrs, ... }' en PrismaModel."""
    import re
    from agents.project_spec import PrismaModel, PrismaField

    # Brace-depth counting — [^}]* regex casse sur les attributs imbriqués
    _bm = re.search(r'(\w+)\s*\{', model_str)
    blocks: list[tuple[str, str]] = []
    if _bm:
        _inner_start = _bm.end()
        _depth = 1
        for _i, _ch in enumerate(model_str[_inner_start:], start=_inner_start):
            if _ch == "{":
                _depth += 1
            elif _ch == "}":
                _depth -= 1
                if _depth == 0:
                    blocks = [(_bm.group(1), model_str[_inner_start:_i])]
                    break
    if blocks:
        name, raw_fields = blocks[0]
        fields: list[PrismaField] = []
        for line in _split_fields(raw_fields.strip()):
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 2:
                fname, ftype = parts[0], parts[1]
                fattrs = " ".join(parts[2:]) if len(parts) > 2 else ""
                fields.append(PrismaField(name=fname, type=ftype, attributes=fattrs))
        if not fields:
            fields = [PrismaField(name="id", type="String", attributes="@id @default(uuid())")]
        owner_field = _detect_owner_field(fields)
        return PrismaModel(name=name.strip(), fields=fields, owner_field=owner_field)

    name = (model_str or "").strip().split()[0] or "Model"
    from agents.project_spec import PrismaModel, PrismaField
    return PrismaModel(
        name=name,
        fields=[PrismaField(name="id", type="String", attributes="@id @default(uuid())")],
    )


# ── Brief writer node (LLM — activé si brief.models absent) ─────────────────

async def brief_writer_node(state: AgentState) -> dict:
    """
    Convertit un brief en langage naturel en brief structuré JSON.
    Activé uniquement si state["brief"]["models"] est absent ou vide.
    Si models déjà fournis : no-op (chemin déterministe préservé).
    """
    brief = state.get("brief", {})

    if brief.get("models"):
        logger.info("[brief_writer] models déjà fournis → chemin déterministe")
        return {}

    description = brief.get("description", "").strip()
    hints = brief.get("hints", {}) or {}

    if not description:
        raise ApplicationError(
            "brief_writer: description vide — impossible de générer la spec.",
            non_retryable=True,
        )

    from agents.llm_provider import get_chat_llm
    from langchain_core.messages import SystemMessage, HumanMessage as _HM

    llm = get_chat_llm(temperature=0.0).bind(
        response_format={"type": "json_object"}
    )

    hint_str = (
        f"\n\nHints du développeur :\n{json.dumps(hints, ensure_ascii=False)}"
        if hints else ""
    )
    user_message = f"Brief : {description}{hint_str}"

    messages = [
        SystemMessage(content=_BRIEF_WRITER_SYSTEM_PROMPT),
        _HM(content=user_message),
    ]

    try:
        response = await llm.ainvoke(messages)
        generated: dict = json.loads(response.content)
    except json.JSONDecodeError as e:
        raise ApplicationError(
            f"brief_writer: réponse LLM non-JSON — {e}",
            non_retryable=False,
        )
    except Exception as e:
        raise ApplicationError(
            f"brief_writer: erreur LLM — {e}",
            non_retryable=False,
        )

    if not generated.get("models"):
        raise ApplicationError(
            "brief_writer: LLM n'a généré aucun modèle — brief trop vague ?",
            non_retryable=False,
        )

    updated_brief = {**brief, **generated}

    model_names = [
        m.split()[0] for m in generated.get("models", []) if m.split()
    ]
    logger.info(
        "[brief_writer] ✓ %d modèle(s), %d page(s) — %s",
        len(model_names),
        len(generated.get("pages", [])),
        model_names,
    )

    return {"brief": updated_brief}


# ── Planner node (module-level — aucune dépendance closure) ──────────────────

async def planner_node(state: AgentState) -> dict:
    """
    Construit ProjectSpec directement depuis state["brief"] structuré.
    Chemin déterministe — zéro appel LLM si brief complet (models/pages/routes).
    Brief incomplet → ApplicationError non-retryable.
    """
    from agents.project_spec import ProjectSpec, AppPage, ApiRoute

    stack_id = str(state.get("stack_id", _DEFAULT_STACK_ID))
    project_name = state.get("project_name", "")
    brief = state.get("brief", {})

    brief_models = brief.get("models", [])
    brief_pages = brief.get("pages", [])
    brief_routes = brief.get("routes", [])

    if not (brief_models or brief_pages or brief_routes):
        missing = []
        if not brief_models: missing.append("models")
        if not brief_pages:  missing.append("pages")
        if not brief_routes: missing.append("routes")
        logger.error("[planner] Brief non structuré — champs manquants : %s", missing)
        raise ApplicationError(
            f"Brief insuffisant : {missing} absents. "
            "Structurer le brief (models/pages/routes) avant de soumettre à la factory.",
            non_retryable=True,
        )

    models = []
    seen_names: set[str] = set()
    for mdl_str in brief_models:
        m = _parse_model_str(str(mdl_str))
        if m.name not in seen_names:
            models.append(m)
            seen_names.add(m.name)
    from agents.stacks.base import get_adapter_for_stack
    models = get_adapter_for_stack(stack_id).inject_relations(models)

    pages: list[AppPage] = []
    seen_paths: set[str] = set()
    for pg in brief_pages:
        if isinstance(pg, dict):
            path = str(pg.get("path", "/"))
            auth = bool(pg.get("auth", True))
            model = pg.get("model") or None
            page_type = pg.get("page_type", "custom")
        else:
            path, auth, model, page_type = str(pg), True, None, "custom"
        if path not in seen_paths:
            pages.append(AppPage(path=path, auth_required=auth, model=model, page_type=page_type))
            seen_paths.add(path)
    if not any(pg.path == "/" for pg in pages):
        pages.insert(0, AppPage(path="/", auth_required=False))
        logger.info("[planner] page '/' ajoutée automatiquement")

    routes: list[ApiRoute] = []
    seen_routes: set[str] = set()
    for rt in brief_routes:
        if isinstance(rt, dict):
            method = str(rt.get("method", "GET")).upper()
            path = str(rt.get("path", "/api/resource"))
            key = f"{method}:{path}"
            if key not in seen_routes and method in ("GET", "POST", "PUT", "PATCH", "DELETE"):
                routes.append(ApiRoute(method=method, path=path))  # type: ignore[arg-type]
                seen_routes.add(key)

    brief_user_flows = brief.get("user_flows", [])
    user_flows = (
        [str(f) for f in brief_user_flows]
        if brief_user_flows and isinstance(brief_user_flows, list)
        else (
            [f"L'utilisateur crée via {r.method} {r.path}" for r in routes]
            + [f"L'utilisateur visite {p.path}" for p in pages]
        )
    )
    brief_description = str(brief.get("description", "")).strip()
    brief_pages_detail = brief.get("pages_detail", {})
    if not isinstance(brief_pages_detail, dict):
        brief_pages_detail = {}

    brief_enums = brief.get("enums", {})
    if not isinstance(brief_enums, dict):
        brief_enums = {}

    spec = ProjectSpec(
        project_name=project_name,
        stack_id=stack_id,
        description=brief_description,
        models=models,
        routes=routes,
        pages=pages,
        pages_detail=brief_pages_detail,
        user_flows=user_flows,
        enums=brief_enums,
    ).with_fingerprint()

    logger.info(
        "[planner] ProjectSpec — %d modèles, %d pages, %d routes | fingerprint=%s",
        len(models), len(pages), len(routes), spec.spec_fingerprint,
    )

    spec_summary = (
        f"Projet {project_name} | Stack {stack_id}\n"
        f"Modèles : {', '.join(m.name for m in spec.models)}\n"
        f"Pages : {', '.join(p.path for p in spec.pages)}\n"
        f"Routes : {', '.join(r.method + ' ' + r.path for r in spec.routes)}"
    )
    architect_output = ArchitectOutput(
        specification=spec_summary,
        mermaid_diagram="",
        requirements=spec.to_requirements(),
        user_flows=spec.user_flows,
        ir_schema=[m.name for m in spec.models],
        ir_pages=[p.path for p in spec.pages],
        ir_routes=[f"{r.method} {r.path}" for r in spec.routes],
        spec_structured=SpecOutput(),
    )

    return {
        "plan": spec.model_dump(),
        "requirements": spec.to_requirements(),
        "user_flows": spec.user_flows,
        "project_spec": spec.model_dump(),
        "architect_output": architect_output,
    }


# ── Graph factory ─────────────────────────────────────────────────────────────

def create_architect_agent():
    from langgraph.graph import StateGraph, START, END

    def _route_entry(state: AgentState) -> str:
        """
        Si le brief contient déjà des models → planner directement (chemin déterministe).
        Sinon → brief_writer pour conversion langage naturel → JSON structuré.
        """
        brief = state.get("brief", {})
        if brief.get("models"):
            return "planner"
        return "brief_writer"

    workflow = StateGraph(AgentState)
    workflow.add_node("brief_writer", brief_writer_node)
    workflow.add_node("planner", planner_node)
    workflow.add_conditional_edges(
        START,
        _route_entry,
        {"brief_writer": "brief_writer", "planner": "planner"},
    )
    workflow.add_edge("brief_writer", "planner")
    workflow.add_edge("planner", END)
    return workflow.compile()
