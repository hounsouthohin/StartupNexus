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
# Structure en 3 sections séparées (planSecond.md) :
#   _STACK_INVARIANTS   : règles fondamentales — ne changent pas sans breaking change de stack
#   _DEDUCTION_RULES    : règles de transformation brief → modèle — évoluent à chaque nouvelle hallucination
#   _FEW_SHOT_EXAMPLES  : exemples par catégorie — candidats à externalisation JSON + enrichissement learner

_STACK_INVARIANTS = """\
## RÈGLES STACK (NON NÉGOCIABLES)

### Auth
- Auth = Clerk V6 uniquement. JAMAIS : bcrypt, jwt, password, next-auth, /api/auth/register, /api/auth/login
- **JAMAIS de modèle `User` dans le schema Prisma.** Clerk gère les utilisateurs. `userId` est une String externe issue de Clerk — ce n'est PAS une FK vers un modèle Prisma. Ne pas créer de modèle User, UserProfile, Account ou similaire.
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
Ajouter des routes seulement pour : webhooks, exports CSV, endpoints publics stateless.\
"""

_DEDUCTION_RULES = """\
## RÈGLES DE DÉDUCTION (applique AVANT de générer un modèle ou un champ)

### RÈGLE 1 — Préservation des champs
Si le brief décrit un attribut comme une valeur simple, **conserver ce champ tel quel dans le modèle**.

- `category String` dans le brief → champ `category String` dans Prisma. **NE PAS créer un modèle `Category`.**
- `published Boolean` dans le brief → champ `published Boolean` dans Prisma. **NE PAS transformer en enum.**
- `type String` ou `status String` simple → champ String.

**Créer un modèle séparé (Category, Tag, Type...) UNIQUEMENT si le brief dit EXPLICITEMENT** que l'entité est créée, listée ou gérée séparément — exemples : "les catégories sont gérées séparément", "l'utilisateur crée ses propres catégories", "page dédiée /categories".

### RÈGLE 2 — enum vs Boolean
**Un enum `{ draft, published }` est une ERREUR. Un enum `{ brouillon, publié }` est une ERREUR.**
Si tu vois exactement 2 valeurs dont l'une est `published`, `active`, `enabled`, `visible`, `publié`, `actif` — c'est un `Boolean @default(false)`. PAS un enum.

Phrasés qui déclenchent **Boolean** (PAS enum) :
- "statut (brouillon ou publié)", "brouillon ou publié", "publié/brouillon", "publié ou non"
- "actif/inactif", "visible/caché", "activé/désactivé"

Phrasés qui déclenchent **enum** :
- 3 états ou plus : "pending/approved/rejected", "draft/sent/paid", "todo/in_progress/done"
- Le brief contient explicitement le mot "enum" : "statut géré par un enum (draft, published, archived)"
- 2 états avec workflow de transition nommé (ex: "l'admin peut approuver ou refuser")\
"""

_FEW_SHOT_EXAMPLES = """\
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
  ],
  "architecture": "Modèle principal : Task. Modèle enfant : Comment (lié à Task via taskId). Ownership : userId sur Task et Comment. Toutes les pages protégées par auth."
}

### Exemple 2 — Blog public (CMS single-auteur)

Brief : "Un blog personnel. L'auteur rédige des articles depuis son espace privé. Chaque article a un titre, un extrait, un statut (brouillon ou publié) et une catégorie. Les visiteurs lisent les articles publiés sans se connecter sur /posts et /posts/[slug]. L'auteur gère ses articles sur /dashboard."

Note RÈGLE 1 : "catégorie" est un attribut de l'article — le brief ne dit pas "page dédiée /categories" ni "gérées séparément" → `category String`, PAS de modèle Category.
Note RÈGLE 2 : "statut (brouillon ou publié)" = exactement 2 états, l'un est la négation de l'autre → `published Boolean @default(false)`, PAS un enum PostStatus.

Sortie :
{
  "models": [
    "Post { id String @id @default(uuid()), title String, excerpt String, published Boolean @default(false), category String, authorId String, createdAt DateTime @default(now()) }"
  ],
  "enums": {},
  "pages": [
    {"path": "/", "auth": false, "page_type": "custom"},
    {"path": "/posts", "auth": false, "model": "Post", "page_type": "list"},
    {"path": "/posts/new", "auth": true, "model": "Post", "page_type": "create"},
    {"path": "/posts/[slug]", "auth": false, "model": "Post", "page_type": "detail-slug"},
    {"path": "/dashboard", "auth": true, "page_type": "custom"}
  ],
  "routes": [],
  "user_flows": [
    "Un visiteur parcourt les articles publiés à /posts",
    "Un visiteur lit un article à /posts/[slug]",
    "Un auteur connecté gère ses articles depuis /dashboard"
  ],
  "architecture": "Modèle principal : Post. Données publiques : /posts et /posts/[slug] accessibles sans auth (published=true). Ownership : authorId sur Post. category est un champ texte simple — pas un modèle séparé."
}

### Exemple 3 — SaaS multi-modèle (invoice app avec clients)

Brief : "Une application de facturation. L'utilisateur gère ses clients dans une liste dédiée et crée des factures associées à un client. Une facture a un montant et un statut (draft/sent/paid)."

Note RÈGLE 1 : "liste dédiée" pour les clients → Client est un modèle séparé avec ses propres pages CRUD.
Note RÈGLE 2 : "draft/sent/paid" = 3 états avec transitions de workflow → enum InvoiceStatus.

Sortie :
{
  "models": [
    "Client { id String @id @default(uuid()), name String, email String, userId String, invoices Invoice[], createdAt DateTime @default(now()) }",
    "Invoice { id String @id @default(uuid()), amount Float, status InvoiceStatus @default(draft), clientId String, client Client @relation(fields: [clientId], references: [id], onDelete: Cascade), userId String, createdAt DateTime @default(now()) }"
  ],
  "enums": {
    "InvoiceStatus": ["draft", "sent", "paid"]
  },
  "pages": [
    {"path": "/", "auth": false, "page_type": "custom"},
    {"path": "/clients", "auth": true, "model": "Client", "page_type": "list"},
    {"path": "/clients/new", "auth": true, "model": "Client", "page_type": "create"},
    {"path": "/clients/[id]", "auth": true, "model": "Client", "page_type": "detail"},
    {"path": "/invoices", "auth": true, "model": "Invoice", "page_type": "list"},
    {"path": "/invoices/new", "auth": true, "model": "Invoice", "page_type": "create"},
    {"path": "/invoices/[id]", "auth": true, "model": "Invoice", "page_type": "detail"}
  ],
  "routes": [],
  "user_flows": [
    "L'utilisateur crée un client depuis /clients/new",
    "L'utilisateur crée une facture depuis /invoices/new",
    "L'utilisateur change le statut d'une facture à /invoices/[id]"
  ],
  "architecture": "Modèles : Client (entité dédiée avec liste propre) + Invoice (principal). Ownership : userId sur les deux. Relations : Invoice → Client (N:1, clientId obligatoire). Toutes les pages protégées par auth."
}\
"""

_FORMAT_DE_SORTIE = """\
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
  "user_flows": ["L'utilisateur crée une tâche depuis /tasks/new", ...],
  "architecture": "Modèle principal : Task. Ownership : userId sur tous les modèles. Relations : [description des relations si multi-modèle]. Contraintes non-dérivables : [ex: slug unique, données publiques sans auth]."
}
```

page_type valeurs autorisées : "list" | "create" | "detail" | "detail-slug" | "custom"

Le champ `architecture` capture ce qui n'est PAS dérivable du schéma Prisma seul : quelles données sont publiques, pourquoi certaines pages sont sans auth, contraintes métier importantes.\
"""

_BRIEF_WRITER_SYSTEM_PROMPT = "\n\n".join([
    (
        "Tu es un architecte logiciel expert de la stack Next.js 14 + Clerk V6 + Prisma 7 + PostgreSQL.\n"
        "Ta mission : convertir un brief en langage naturel en une spec JSON structurée prête pour le générateur de code."
    ),
    _STACK_INVARIANTS,
    _DEDUCTION_RULES,
    _FORMAT_DE_SORTIE,
    _FEW_SHOT_EXAMPLES,
    "Retourne UNIQUEMENT le JSON, sans balises markdown ni explication.",
])


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
    enriched_spec: dict  # produit par semantic_annotator_node


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


# ── Semantic Annotator node (LLM — enrichit la spec avec annotations sémantiques) ──

_SEMANTIC_ANNOTATOR_SYSTEM_PROMPT = """\
Tu es un annotateur sémantique. Tu reçois un brief applicatif et sa liste de modèles Prisma.
Ta mission : produire un JSON compact d'annotations sémantiques pour guider les générateurs de code.

## CE QUE TU ANNOTES

### field_annotations
Annote uniquement les champs dont le type sémantique est NON-DÉRIVABLE du nom ou du type Prisma seul.
Clé = nom exact du champ Prisma. Valeur = objet avec "semantic_type" et optionnellement "values".

Types à annoter :
- "textarea"       → champs texte long (bio, description longue, content, notes, instructions, body)
- "status-enum"    → enum de statut workflow. Inclure "values" dans l'ordre logique du workflow.
- "priority-enum"  → enum de priorité. Inclure "values" du plus faible au plus fort.
- "currency"       → montant monétaire (amount, price, cost, budget, salary)
- "date"           → date sans heure (birthDate, dueDate, startDate, endDate — type String ou DateTime)
- "url"            → lien web (website, url, link, avatar, imageUrl)
- "email"          → adresse email (email, contactEmail)

NE PAS annoter : id, createdAt, updatedAt, userId, authorId, xxxId (FK), slug, champs bool, champs Int/Float standards.

### required_queries
Déclare les queries métier clairement nécessaires d'après le brief — AU-DELÀ des 7 méthodes CRUD standard déjà générées (getAll, getById, create, update, delete, getPublished, getBySlug).
Patterns disponibles :
- "filter_by_field"    → findMany where { field: value }        (ex: getByStatus, getByCategory)
- "search_text"        → findMany where { field: contains: q }  (ex: searchByTitle)
- "filter_by_relation" → findMany where { relation: { field } } (ex: getByProject)

Ne déclare une query que si le brief la mentionne explicitement ou si elle est évidente pour le domaine métier.

### features
Liste les features actives parmi : "status_flow", "slug_routing", "public_pages", "search", "pagination", "file_upload", "calendar_view".
Déduis-les du brief — ne liste que ce qui est clairement présent.

## FORMAT DE SORTIE — JSON uniquement, aucun markdown

Exemple pour un gestionnaire de tâches avec statut workflow :
{
  "field_annotations": {
    "description": {"semantic_type": "textarea"},
    "status": {"semantic_type": "status-enum", "values": ["todo", "in_progress", "done"]},
    "priority": {"semantic_type": "priority-enum", "values": ["low", "medium", "high"]},
    "dueDate": {"semantic_type": "date"}
  },
  "required_queries": [
    {"name": "getByStatus", "pattern": "filter_by_field", "field": "status", "return_many": true}
  ],
  "features": ["status_flow"]
}

Exemple pour un blog public avec slug :
{
  "field_annotations": {
    "content": {"semantic_type": "textarea"},
    "excerpt": {"semantic_type": "textarea"},
    "status": {"semantic_type": "status-enum", "values": ["draft", "published"]}
  },
  "required_queries": [],
  "features": ["slug_routing", "public_pages", "status_flow"]
}

Retourne UNIQUEMENT le JSON. Si aucune annotation n'est pertinente, retourne {"field_annotations": {}, "required_queries": [], "features": []}.\
"""


async def semantic_annotator_node(state: AgentState) -> dict:
    """
    Enrichit la spec avec des annotations sémantiques (semantic_type par champ,
    queries métier, features actives).

    Activé après brief_writer_node — les modèles doivent être présents.
    Fail-safe : toute erreur LLM retourne {} sans bloquer le pipeline.
    Le résultat est stocké dans brief["enriched_spec"] et state["enriched_spec"].
    """
    brief = state.get("brief", {})

    if brief.get("enriched_spec"):
        logger.info("[semantic_annotator] déjà présent → skip")
        return {}

    models = brief.get("models", [])
    if not models:
        logger.warning("[semantic_annotator] models absent → skip")
        return {}

    from agents.llm_provider import get_chat_llm
    from langchain_core.messages import SystemMessage, HumanMessage as _HM

    llm = get_chat_llm(temperature=0.0).bind(
        response_format={"type": "json_object"}
    )

    context = {
        "description": brief.get("description", "").strip(),
        "models": models,
        "enums": brief.get("enums", {}),
    }

    messages = [
        SystemMessage(content=_SEMANTIC_ANNOTATOR_SYSTEM_PROMPT),
        _HM(content=json.dumps(context, ensure_ascii=False)),
    ]

    try:
        response = await llm.ainvoke(messages)
        enriched: dict = json.loads(response.content)
    except json.JSONDecodeError as e:
        logger.error("[semantic_annotator] réponse non-JSON — %s", e)
        return {}
    except Exception as e:
        logger.error("[semantic_annotator] erreur LLM — %s", e)
        return {}

    if not isinstance(enriched, dict):
        logger.warning("[semantic_annotator] format inattendu — skip")
        return {}

    # Validation légère avec le schéma Pydantic
    try:
        from agents.semantic_spec import EnrichedSpec
        validated = EnrichedSpec(**enriched)
        enriched = validated.model_dump()
    except Exception as _ve:
        logger.warning("[semantic_annotator] validation Pydantic échouée (%s) — raw conservé", _ve)

    field_count = len(enriched.get("field_annotations", {}))
    query_count = len(enriched.get("required_queries", []))
    features = enriched.get("features", [])
    logger.info(
        "[semantic_annotator] ✓ %d champ(s) annoté(s), %d query(ies), features=%s",
        field_count, query_count, features,
    )

    updated_brief = {**brief, "enriched_spec": enriched}
    return {"brief": updated_brief, "enriched_spec": enriched}


# ── Pages detail node (LLM — génère pages_detail depuis brief structuré) ─────

_PAGES_DETAIL_SYSTEM_PROMPT = """\
Tu génères les descriptions fonctionnelles détaillées (pages_detail) pour chaque page d'une application Next.js 14.
Ces descriptions guident un agent développeur pour générer les bons composants React.

## DONNÉES QUE TU REÇOIS
JSON avec : description (brief humain), models (liste Prisma DSL), pages (tableau [{path, auth, page_type, model?}]),
et optionnellement architecture (contraintes non-dérivables du brief).

## RÈGLES PAR TYPE DE PAGE

### page_type = "list"
- Affiche les champs visuels du modèle (EXCLURE : id, userId, authorId, xxxId, createdAt, updatedAt, champs relation[])
- Bouton "Nouveau" → href `/model/new`
- Bouton "Modifier" → router.push(`/model/${id}/edit`)
- Bouton "Supprimer" → delete{Model}(id)
- État vide : "Aucun {entity} pour l'instant."
- TOUJOURS terminer par [INTERACTIVE] (données serveur + boutons d'action)

### page_type = "create"
- Formulaire avec champs éditables du modèle (EXCLURE : id, userId, authorId, xxxId, createdAt)
- Si le modèle a une FK (ex: categoryId), inclure un select pour choisir la catégorie parente
- Submit → create{Model}(formData)
- PAS de [INTERACTIVE] (formulaire pur, déjà Client Component)

### page_type = "detail"
- Affiche tous les champs visuels du modèle
- Bouton "Modifier" → router.push(`/model/${id}/edit`)
- Bouton "Supprimer" → delete{Model}(id) puis redirect vers la liste
- TOUJOURS terminer par [INTERACTIVE] si la page est auth:true

### page_type = "detail-slug" (publique, auth: false)
- Affiche tous les champs visuels du modèle
- Lecture seule — aucun bouton d'action côté visiteur anonyme
- PAS de [INTERACTIVE]

### page_type = "custom"
- Décris le contenu selon le brief (hero, landing, dashboard métriques, etc.)
- Ajoute [INTERACTIVE] UNIQUEMENT si la page combine données serveur ET interactions utilisateur
- Page home statique / landing sans données → PAS de [INTERACTIVE]

## RÈGLE [INTERACTIVE]
Ajouter [INTERACTIVE] si et seulement si la page COMBINE les deux :
1. Données lues depuis la base via un service (getAll, getById, etc.)
2. Au moins un bouton d'action côté client (supprimer, modifier statut, etc.)
Sans données serveur = pas [INTERACTIVE]. Sans bouton d'action = pas [INTERACTIVE].

## NOMMAGE DES SERVER ACTIONS (CRITIQUE — correspondance exacte)
Les noms doivent suivre le pattern : {verb}{ModelName}
- create : createTask(formData), createExpense(formData)
- delete : deleteTask(id), deleteExpense(id)
- update : updateTask(id, formData)
Le nom du modèle DOIT correspondre exactement au nom déclaré dans "models".

## FORMAT DE SORTIE — JSON uniquement, aucun markdown
```json
{
  "/tasks": "Liste des tâches. Affiche : titre, statut, description. Bouton 'Nouveau' → /tasks/new. Bouton 'Modifier' → /tasks/${id}/edit. Bouton 'Supprimer' → deleteTask(id). État vide : 'Aucune tâche.'. [INTERACTIVE]",
  "/tasks/new": "Formulaire de création. Champs : titre (text), description (textarea), statut (select : pending, in_progress, done). Submit → createTask(formData).",
  "/tasks/[id]": "Détail d'une tâche. Affiche : titre, statut, description, date de création. Bouton 'Modifier' → /tasks/${id}/edit. Bouton 'Supprimer' → deleteTask(id) puis redirect /tasks. [INTERACTIVE]",
  "/": "Page d'accueil. Hero avec titre du projet et bouton 'Commencer' → /tasks."
}
```

Génère une entrée pour CHAQUE page dans le tableau "pages" reçu. Clés = paths exacts.
Retourne UNIQUEMENT le JSON, sans balises markdown ni explication.\
"""


async def pages_detail_node(state: AgentState) -> dict:
    """
    Génère pages_detail (descriptions fonctionnelles + marqueurs [INTERACTIVE])
    depuis le brief structuré produit par brief_writer_node.
    Skip si pages_detail déjà présent dans le brief.
    Fail-safe : en cas d'erreur LLM, retourne {} sans bloquer le pipeline.
    """
    brief = state.get("brief", {})

    existing_pd = brief.get("pages_detail", {})
    if existing_pd and isinstance(existing_pd, dict) and len(existing_pd) > 0:
        logger.info("[pages_detail] déjà présent (%d pages) → skip", len(existing_pd))
        return {}

    pages = brief.get("pages", [])
    models = brief.get("models", [])

    if not pages or not models:
        logger.warning("[pages_detail] pages ou models absent → skip")
        return {}

    from agents.llm_provider import get_chat_llm
    from langchain_core.messages import SystemMessage, HumanMessage as _HM

    llm = get_chat_llm(temperature=0.0).bind(
        response_format={"type": "json_object"}
    )

    context: dict = {
        "description": brief.get("description", "").strip(),
        "models": models,
        "pages": pages,
    }
    architecture = brief.get("architecture", "").strip()
    if architecture:
        context["architecture"] = architecture

    messages = [
        SystemMessage(content=_PAGES_DETAIL_SYSTEM_PROMPT),
        _HM(content=json.dumps(context, ensure_ascii=False)),
    ]

    try:
        response = await llm.ainvoke(messages)
        pages_detail: dict = json.loads(response.content)
    except json.JSONDecodeError as e:
        logger.error("[pages_detail] réponse LLM non-JSON — %s", e)
        return {}
    except Exception as e:
        logger.error("[pages_detail] erreur LLM — %s", e)
        return {}

    if not isinstance(pages_detail, dict):
        logger.warning("[pages_detail] format inattendu — skip")
        return {}

    interactive_count = sum(
        1 for v in pages_detail.values() if "[INTERACTIVE]" in str(v)
    )
    logger.info(
        "[pages_detail] ✓ %d page(s) décrites, %d [INTERACTIVE]",
        len(pages_detail),
        interactive_count,
    )

    return {"brief": {**brief, "pages_detail": pages_detail}}


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

    # Propage enriched_spec dans project_spec pour que dev_graph.py puisse le lire
    enriched_spec = brief.get("enriched_spec") or state.get("enriched_spec") or {}
    spec_dict = spec.model_dump()
    if enriched_spec:
        spec_dict["enriched_spec"] = enriched_spec

    return {
        "plan": spec_dict,
        "requirements": spec.to_requirements(),
        "user_flows": spec.user_flows,
        "project_spec": spec_dict,
        "architect_output": architect_output,
        "enriched_spec": enriched_spec,
    }


# ── Graph factory ─────────────────────────────────────────────────────────────

def create_architect_agent():
    from langgraph.graph import StateGraph, START, END

    def _route_entry(state: AgentState) -> str:
        """
        Brief libre  → brief_writer → semantic_annotator → pages_detail → planner
        Brief structuré (models présents) → semantic_annotator → pages_detail → planner
        Tous les nœuds sont idempotents (skip si déjà rempli).
        """
        brief = state.get("brief", {})
        if brief.get("models"):
            return "semantic_annotator"
        return "brief_writer"

    workflow = StateGraph(AgentState)
    workflow.add_node("brief_writer", brief_writer_node)
    workflow.add_node("semantic_annotator", semantic_annotator_node)
    workflow.add_node("pages_detail", pages_detail_node)
    workflow.add_node("planner", planner_node)
    workflow.add_conditional_edges(
        START,
        _route_entry,
        {"brief_writer": "brief_writer", "semantic_annotator": "semantic_annotator"},
    )
    workflow.add_edge("brief_writer", "semantic_annotator")
    workflow.add_edge("semantic_annotator", "pages_detail")
    workflow.add_edge("pages_detail", "planner")
    workflow.add_edge("planner", END)
    return workflow.compile()
