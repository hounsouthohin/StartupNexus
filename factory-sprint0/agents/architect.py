
# agents/architect.py
from __future__ import annotations

import json
import logging
import operator
import os
from typing import List, TypedDict, Annotated

from temporalio.exceptions import ApplicationError
from pydantic import BaseModel, Field

from agents.stack_config import _DEFAULT_STACK_ID

logger = logging.getLogger(__name__)


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
- "date"           → date SANS heure (birthDate, dueDate — l'heure n'a pas de sens pour ce champ)
- "datetime"       → date ET heure (rendez-vous, créneau, échéance horaire). Si le brief dit
                     "date et heure" ou si l'heure est significative → TOUJOURS "datetime", jamais "date"
                     (un rendez-vous annoté "date" perd son heure dans le formulaire — bug réel).
- "url"            → lien web (website, url, link, avatar, imageUrl)
- "email"          → adresse email (email, contactEmail)

NE PAS annoter : id, createdAt, updatedAt, userId, authorId, xxxId (FK), slug, champs bool, champs Int/Float standards.

RÈGLE ABSOLUE : les clés de field_annotations doivent correspondre EXACTEMENT aux noms de champs déclarés dans les modèles reçus. Ne jamais inventer un nom de champ.
Exemple INTERDIT : si le modèle a `published Boolean`, ne PAS écrire `"status": {...}` — ce champ n'existe pas.
Si un modèle utilise `published Boolean` pour gérer brouillon/publié → ne rien annoter pour ce champ (Boolean exclu).

### required_queries
Déclare les queries métier clairement nécessaires d'après le brief — AU-DELÀ des méthodes standard déjà générées (getAll, getById, create, update, delete, + getPublicAll/getPublicById si pages publiques, + getBySlug si champ slug).
Patterns disponibles :
- "filter_by_field"    → findMany where { field: value }        (ex: getByStatus, getByCategory)
- "search_text"        → findMany where { field: contains: q }  (ex: searchByTitle)
- "filter_by_relation" → findMany where { relation: { field } } (ex: getByProject)

Ne déclare une query que si le brief la mentionne explicitement ou si elle est évidente pour le domaine métier.

### features
Liste les features actives parmi : "status_flow", "slug_routing", "public_pages", "search", "pagination", "file_upload", "calendar_view".
Déduis-les du brief — ne liste que ce qui est clairement présent.

### status_flows
Si un modèle a un champ de statut qui décrit un CYCLE DE VIE, déclare sa machine à états.
Indices d'un cycle de vie dans le brief : des étapes qui se suivent, un passage d'un état à un autre,
une soumission, une validation, une approbation, un refus, une clôture, un « puis », un « une fois que ».

Clé = nom du MODÈLE (ex: "ExpenseReport"), JAMAIS le nom du champ — deux modèles peuvent chacun
avoir leur propre workflow.

- "field"         : le champ Prisma portant l'état (ex: "status")
- "initial"       : l'état de départ de toute nouvelle entité (ex: "draft")
- "transitions"   : le graphe des passages AUTORISÉS — {état: [états directement atteignables]}
- "locked_states" : états où les CHAMPS MÉTIER ne sont plus modifiables. [] si le brief n'en parle pas.

RÈGLES :
- LISTE BLANCHE : ne déclare que les passages que le brief autorise. Tout passage non listé est INTERDIT.
- Un état terminal (définitif, sans suite) → liste vide [].
- Un état peut mener à PLUSIEURS états (ex: un dossier examiné → accepté OU rejeté).
- Un retour en arrière n'existe QUE si le brief le décrit (ex: dépublier un article).
- N'invente aucune étape que le brief ne décrit pas.
- Si le statut est une simple ÉTIQUETTE sans cycle de vie (catégorie, type, priorité, niveau) →
  NE PAS déclarer de status_flow. Une étiquette n'est pas une machine à états.
- Laisse {} si aucun modèle n'a de cycle de vie.

locked_states — quand le brief dit qu'une entité n'est plus modifiable à partir d'une étape :
  « on ne peut plus modifier une demande une fois soumise » → tous les états à partir de
  "soumise" incluse sont verrouillés (soumise + tous ceux qui suivent), car on ne revient
  jamais en arrière dans ces workflows.
  ⚠ Ne JAMAIS mettre l'état initial dans locked_states : un brouillon doit rester modifiable.
  ⚠ locked_states ne bloque QUE les champs métier — le statut continue d'avancer.
  Laisse [] si le brief ne mentionne aucun verrouillage : ne l'invente pas.

### ux_hints
Produis des indications UX pour améliorer l'expérience utilisateur final.

**empty_states** : pour chaque page list déclarée dans les pages du brief, écris le message affiché quand la liste est vide.
  Format : { "/path": "Message en français — inclure un appel à l'action si pertinent." }
  Règle : le message doit être dans la langue du brief. S'il y a des dépendances FK (ex: Invoice nécessite un Client), le mentionner.

**dependency_order** : si des modèles ont des dépendances FK (model B référence model A via xxxId), lister l'ordre de création en langage naturel dans la langue du brief.
  Ex: ["Créez d'abord un Client avant de créer une Facture."]
  Laisser vide [] s'il n'y a pas de dépendances FK significatives.

**primary_action** : laisser vide {} — non utilisé pour ce niveau.

## FORMAT DE SORTIE — JSON uniquement, aucun markdown

⚠ Les exemples ci-dessous illustrent la FORME du JSON, PAS des gabarits de domaine.
Annote TOUJOURS les champs réellement présents dans les modèles reçus ; n'invente pas de champ
et ne plaque pas ces exemples sur un brief dont le domaine est différent.

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
  "features": ["status_flow"],
  "status_flows": {
    "Task": {
      "field": "status",
      "initial": "todo",
      "transitions": {"todo": ["in_progress"], "in_progress": ["done", "todo"], "done": []},
      "locked_states": []
    }
  },
  "ux_hints": {
    "empty_states": {
      "/tasks": "Aucune tâche pour le moment. Créez votre première tâche."
    },
    "dependency_order": [],
    "primary_action": {}
  }
}

Exemple pour un blog public avec slug (modèle utilise `published Boolean`) :
{
  "field_annotations": {
    "content": {"semantic_type": "textarea"},
    "excerpt": {"semantic_type": "textarea"}
  },
  "required_queries": [],
  "features": ["slug_routing", "public_pages"],
  "status_flows": {},
  "ux_hints": {
    "empty_states": {
      "/blog": "Aucun article publié pour le moment.",
      "/dashboard": "Aucun article. Rédigez votre premier article."
    },
    "dependency_order": [],
    "primary_action": {}
  }
}

Exemple pour un blog avec vrai statut enum (modèle a `status PostStatus @default(draft)`) :
{
  "field_annotations": {
    "content": {"semantic_type": "textarea"},
    "excerpt": {"semantic_type": "textarea"},
    "status": {"semantic_type": "status-enum", "values": ["draft", "published"]}
  },
  "required_queries": [],
  "features": ["slug_routing", "public_pages", "status_flow"],
  "status_flows": {
    "Post": {
      "field": "status",
      "initial": "draft",
      "transitions": {"draft": ["published"], "published": ["draft"]},
      "locked_states": []
    }
  },
  "ux_hints": {
    "empty_states": {
      "/blog": "Aucun article publié pour le moment.",
      "/dashboard": "Aucun article. Rédigez votre premier article."
    },
    "dependency_order": [],
    "primary_action": {}
  }
}

Retourne UNIQUEMENT le JSON. Si aucune annotation n'est pertinente, retourne {"field_annotations": {}, "required_queries": [], "features": [], "status_flows": {}, "ux_hints": {"empty_states": {}, "dependency_order": [], "primary_action": {}}}.\
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

    from agents.stack_config import get_llm_models as _get_llm_models
    _llm_models = _get_llm_models()
    _arch_model = _llm_models.get("architect_base", "gpt-4o-mini")
    llm = get_chat_llm(model=_arch_model, temperature=0.0, api_key=os.getenv("ARCHITECT_API_KEY", os.getenv("OPENAI_API_KEY"))).bind(
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
    _flows = enriched.get("status_flows", {}) or {}
    logger.info(
        "[semantic_annotator] ✓ %d champ(s) annoté(s), %d query(ies), features=%s, status_flows=%s",
        field_count, query_count, features,
        {m: f"{f.get('initial')}→{f.get('transitions')}" for m, f in _flows.items()} or "{}",
    )

    updated_brief = {**brief, "enriched_spec": enriched}
    return {"brief": updated_brief, "enriched_spec": enriched}


# ── Pages detail node (LLM — génère pages_detail depuis brief structuré) ─────

def _get_factory_capabilities() -> str:
    """Génère les contraintes techniques injectées dans pages_detail_node depuis service_modules."""
    try:
        from agents.stacks.nextjs_clerk_prisma.service_modules import build_factory_capabilities_string
        return build_factory_capabilities_string()
    except ImportError:
        # Fallback statique si service_modules non disponible (autre stack)
        return (
            "## CONTRAINTES TECHNIQUES\n\n"
            "### Convention paramètres dynamiques\n"
            "- Segment [id]   → params.id   (jamais params.taskId)\n"
            "- Segment [slug] → params.slug (toujours)\n\n"
            "### Design system — auto-généré (ne PAS décrire dans pages_detail)\n"
            "- La sidebar, le layout, les couleurs : générés automatiquement\n"
            "- Décrire UNIQUEMENT la logique fonctionnelle"
        )

_PAGES_DETAIL_SYSTEM_PROMPT = """\
Tu génères les contrats STRUCTURÉS des pages CUSTOM d'une application Next.js 14.

CONTEXTE : les pages avec un modèle Prisma (list, create, detail, edit) sont entièrement
générées par des templates déterministes — tu n'as PAS à les décrire.
Tu décris UNIQUEMENT les pages custom (dashboards, hubs, landings, pages sans modèle associé).

IMPORTANT : ta réponse est un objet JSON PLAT. Chaque clé est un path de page.

## FORMAT — objet structuré par page custom

Chaque valeur est un objet avec ces champs :
- "description"    : string — le texte statique, les liens et le contexte de la page
- "data_fetches"   : liste  — appels service. Format : {"service": "xxxService.method(args)", "as": "varName"}
- "interactive"    : bool   — true si interactions réelles (formulaire inline, filtre dynamique)
- "kpis"           : liste  — les CHIFFRES agrégés affichés. [] si aucun.
- "filtered_lists" : liste  — les LISTES d'un sous-ensemble conditionnel. [] si aucune.

## RAISONNEMENT — décompose ce que la page affiche (vaut pour TOUT domaine)

Pour chaque élément que le brief demande d'afficher, classe-le dans le bon champ :
- un CHIFFRE unique (un total, une moyenne, un « combien de… ») → "kpis"
- une LISTE d'un sous-ensemble conditionnel (« ceux qui… », « les X en retard/à venir ») → "filtered_lists"
- du texte, des liens, un hero → "description"
Ne laisse JAMAIS un chiffre ou une liste conditionnelle uniquement en prose : ce qui n'est pas
structuré est perdu par la suite. Déduis toujours ces éléments du brief réel, jamais d'un gabarit.

## kpis — un CHIFFRE agrégé
{"label", "source" (var de data_fetches), "agg": "count|sum|avg", "field", "filter_field", "filter_value"}
- "count" = NOMBRE d'éléments — field = ""
- "sum"   = TOTAL d'un champ numérique — field obligatoire
- "avg"   = MOYENNE d'un champ numérique — field obligatoire
DISTINCTION : un montant/total exprimé dans une unité (une devise, des km…) est un "sum", JAMAIS un "count".
❌ {"agg": "count"} pour « le total en euros »   ✅ {"agg": "sum", "field": "<le champ montant>"}

## filtered_lists — une LISTE d'un SOUS-ENSEMBLE CONDITIONNEL
{"label", "source" (var de data_fetches), "filter_field", "filter_op": "eq|within_days|before|after", "filter_value"}
- "eq"          = égalité (filter_value = la valeur cible)
- "within_days" = date dans les N prochains jours (filter_value = le nombre N)
- "before"      = date d'un ÉVÉNEMENT déjà passée (échéance dépassée, rendez-vous terminé)
- "after"       = date d'un ÉVÉNEMENT à venir (rendez-vous, échéance future)

DISTINCTIONS (ce qui N'EST PAS un filtered_list) :
- une LISTE n'est jamais un "kpis" (qui est un chiffre unique).
- « les dernières / récentes / les plus récentes / les N derniers » = un TRI, PAS un filtre.
  Les services renvoient déjà les données triées par date décroissante → affiche simplement la liste,
  ne crée AUCUN filtered_list pour ça.
- before/after s'appliquent à une date qui représente un ÉVÉNEMENT (échéance, rendez-vous, prélèvement),
  JAMAIS à createdAt/updatedAt (une date de création est toujours dans le passé → filtre vide).

## EXEMPLE — illustration de la FORME du JSON uniquement
(les noms de champs/valeurs ci-dessous viennent d'un brief fictif — DÉDUIS toujours les tiens
du brief réel, ne réutilise pas ces noms si le domaine est différent)
```json
{
  "/dashboard": {
    "description": "Tableau de bord. Liens rapides vers les pages de création.",
    "data_fetches": [{"service": "xxxService.getAll(userId)", "as": "xxxs"}],
    "interactive": false,
    "kpis": [{"label": "<libellé>", "source": "xxxs", "agg": "sum", "field": "<champ montant>", "filter_field": "<champ statut>", "filter_value": "<valeur>"}],
    "filtered_lists": [{"label": "<libellé>", "source": "xxxs", "filter_field": "<champ date>", "filter_op": "within_days", "filter_value": "7"}]
  }
}
```

## CONTRAINTES
- Ne décris QUE les pages custom reçues dans le tableau "pages" (jamais les pages avec modèle)
- Clés = paths commençant par "/", JSON plat (pas de wrapper)
- data_fetches / kpis / filtered_lists : [] quand vide
- interactive: true UNIQUEMENT si interactions réelles
- NOM DE SERVICE — INVARIANT : dans "service", toujours `<modelEnCamelCase>Service.methode(...)`.
  Le nom commence par une MINUSCULE et se termine par "Service" (ex: modèle `Recipe` → `recipeService`,
  modèle `RunEvent` → `runEventService`). JAMAIS le nom du modèle seul (`Recipe.getPublicAll()` est FAUX),
  jamais de majuscule initiale (`RecipeService` est FAUX).

## PAGES PUBLIQUES (auth=false) — RÈGLE ABSOLUE
Pour toute page publique (landing, home `/`, vitrine sans connexion) :
- data_fetches : UNIQUEMENT `getPublicAll()` ou `getBySlug()` — JAMAIS `getAll(userId)` ni `getById(userId, id)`
- `getPublished()` n'existe QUE si le modèle a un ENUM status — pour un Boolean published, TOUJOURS `getPublicAll()`
  ❌ Boolean published : `articleService.getPublished()` → BUILD_FAILED
  ✅ Boolean published : `articleService.getPublicAll()`
- La description NE DOIT PAS contenir : "auth()", "userId", "redirect", "connexion requise"
- La description DOIT préciser : "page publique — aucun appel Clerk" (l'executor n'ajoute pas auth() sans ces mots)\
"""


async def pages_detail_node(state: AgentState) -> dict:
    """
    Génère pages_detail pour les pages CUSTOM uniquement (page_type='custom', sans model).
    Les pages list/create/detail/edit avec model sont entièrement déterministes —
    le form generator Jinja2 les génère depuis ModelGenerationContext, pas depuis pages_detail.
    Les signaux [CROSS_ENTITY] pour les pages détail avec enfants sont injectés
    déterministiquement dans planner_node.

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

    # Filtre : uniquement les pages custom (sans model, page_type="custom" ou absente).
    # Les pages avec model (list/create/detail) sont générées déterministiquement —
    # le LLM ne les génère pas et n'a pas besoin de leur description.
    custom_pages = [
        p for p in pages
        if (isinstance(p, dict) and not p.get("model") and p.get("page_type", "custom") == "custom")
        or (not isinstance(p, dict))
    ]

    if not custom_pages:
        logger.info("[pages_detail] aucune page custom détectée → skip LLM")
        return {}

    logger.info(
        "[pages_detail] %d page(s) custom sur %d → LLM décrit uniquement les custom",
        len(custom_pages), len(pages),
    )

    from agents.llm_provider import get_chat_llm
    from langchain_core.messages import SystemMessage, HumanMessage as _HM

    from agents.stack_config import get_llm_models as _get_llm_models
    _llm_models = _get_llm_models()
    _arch_model = _llm_models.get("architect_base", "gpt-4o-mini")
    llm = get_chat_llm(model=_arch_model, temperature=0.0, api_key=os.getenv("ARCHITECT_API_KEY", os.getenv("OPENAI_API_KEY"))).bind(
        response_format={"type": "json_object"}
    )

    context: dict = {
        "description": brief.get("description", "").strip(),
        "models": models,
        "pages": custom_pages,
    }
    architecture = brief.get("architecture", "").strip()
    if architecture:
        context["architecture"] = architecture

    # ── 3.1 Injection méthodes valides per-modèle dans le contexte LLM ──────
    # Chaque modèle reçoit la liste exacte des méthodes que son service aura —
    # le LLM ne peut pas invoquer une méthode qui n'est pas dans cette liste.
    _model_methods_index: dict[str, frozenset] = {}
    try:
        from agents.stacks.nextjs_clerk_prisma.service_modules import valid_methods_for_flags as _vmf
        import re as _re2
        _VIS = frozenset({"published", "ispublic", "is_public", "public", "visible", "isvisible"})
        _FK_RE = _re2.compile(r'\b([a-z]\w*)Id\b')
        _per_model: dict[str, list[str]] = {}
        for _ms in (models if isinstance(models, list) else []):
            _ms_str = _ms if isinstance(_ms, str) else ""
            _parts = _ms_str.split()
            if not _parts:
                continue
            _mname = _parts[0]
            _sl = _ms_str.lower()
            _fk_parents = [
                m.group(1)[0].upper() + m.group(1)[1:]
                for m in _FK_RE.finditer(_ms_str)
                if m.group(1) not in {"id", "user", "clerk"}
            ]
            _flags = {
                "has_public": any(_re2.search(rf'\b{v}\b', _sl) for v in _VIS) or any(
                    not p.get("auth", True) and p.get("model") == _mname
                    for p in (brief.get("pages", []) or []) if isinstance(p, dict)
                ),
                "has_slug": bool(_re2.search(r'\bslug\b', _sl)) and '@unique' in _ms_str,
                "has_relations": '@relation' in _ms_str,
                "has_fk_fields": bool(_fk_parents),
                "fk_parent_names": _fk_parents,
            }
            _model_methods_index[_mname] = _vmf(**_flags)
            _per_model[_mname] = sorted(_model_methods_index[_mname])
        if _per_model:
            context["valid_service_methods"] = _per_model
    except Exception as _vmf_err:
        logger.warning("[pages_detail] injection méthodes per-modèle échouée (non bloquant) : %s", _vmf_err)

    messages = [
        SystemMessage(content=_PAGES_DETAIL_SYSTEM_PROMPT + "\n\n" + _get_factory_capabilities()),
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

    logger.info("[pages_detail] raw LLM keys: %s", list(pages_detail.keys())[:10] if isinstance(pages_detail, dict) else type(pages_detail).__name__)

    if not isinstance(pages_detail, dict):
        logger.warning("[pages_detail] format inattendu — skip")
        return {}

    # Unwrap si le LLM a wrappé la réponse dans un objet parent ({"pages": {...}}, etc.)
    _has_slash_key = any(isinstance(k, str) and k.startswith("/") for k in pages_detail)
    if not _has_slash_key and len(pages_detail) > 0:
        for _wrapper_val in pages_detail.values():
            if isinstance(_wrapper_val, dict) and any(isinstance(k, str) and k.startswith("/") for k in _wrapper_val):
                logger.info("[pages_detail] unwrap détecté — réponse wrappée dans '%s'", next(iter(pages_detail)))
                pages_detail = _wrapper_val
                break

    # Filtre + validation : clés valides (paths commençant par /), valeurs dict ou str non-vides.
    # Format cible (D1) : dict structuré {description, data_fetches, interactive}.
    # Backward compat : str acceptée pour les briefs antérieurs.
    from agents.semantic_spec import PageDetailContract as _PDC
    _validated: dict = {}
    for k, v in pages_detail.items():
        if not (isinstance(k, str) and k.startswith("/")):
            continue
        if isinstance(v, dict) and v:
            try:
                _pdc = _PDC(**v)
                _validated[k] = _pdc.model_dump(by_alias=True)
            except Exception:
                _validated[k] = v  # raw dict si validation échoue
        elif isinstance(v, str) and v.strip():
            _validated[k] = v  # backward compat string
    pages_detail = _validated

    # ── 3.2 Correction inline des méthodes invalides ─────────────────────────
    # Double protection avant spec_enricher : corrige immédiatement les méthodes
    # que le LLM a produites mais qui ne correspondent pas au service du modèle.
    if _model_methods_index:
        try:
            from agents.stacks.nextjs_clerk_prisma.service_modules import is_valid_method_for_model as _ivmm
            import re as _re3
            _total_corrected = 0
            _corrections: dict = {}  # chemin → detail corrigé (évite modifier dict en cours d'itération)
            for _path, _detail in pages_detail.items():
                if not isinstance(_detail, dict):
                    continue
                _fetches = _detail.get("data_fetches") or []
                if not isinstance(_fetches, list):
                    continue
                _page_auth = next(
                    (p.get("auth", True) for p in custom_pages
                     if isinstance(p, dict) and p.get("path") == _path),
                    True,
                )
                _fixed: list = []
                _path_corrected = 0  # compteur réinitialisé par path
                for _fetch in _fetches:
                    if not isinstance(_fetch, dict):
                        _fixed.append(_fetch)
                        continue
                    _svc_call = _fetch.get("service", "")
                    _m_match = _re3.search(r"\.(\w+)\(", _svc_call)
                    _s_match = _re3.match(r"([a-z]\w*)Service\.", _svc_call)
                    if not _m_match or not _s_match:
                        _fixed.append(_fetch)
                        continue
                    _method = _m_match.group(1)
                    _svc_base = _s_match.group(1)
                    _mname = next(
                        (m for m in _model_methods_index
                         if m[0].lower() + m[1:] == _svc_base or m.lower() == _svc_base),
                        None,
                    )
                    if _mname and not _ivmm(_method, _model_methods_index[_mname], any(
                        mv.startswith("getBy") and mv.endswith("Id")
                        for mv in _model_methods_index[_mname]
                    )):
                        _correct_method = "getAll(userId)" if _page_auth else "getPublicAll()"
                        _corrected_call = f"{_svc_base}Service.{_correct_method}"
                        logger.warning(
                            "[pages_detail] correction '%s' : %s → %s",
                            _path, _svc_call, _corrected_call,
                        )
                        _fixed.append({**_fetch, "service": _corrected_call})
                        _path_corrected += 1
                    else:
                        _fixed.append(_fetch)
                if _path_corrected:
                    _corrections[_path] = {**_detail, "data_fetches": _fixed}
                    _total_corrected += _path_corrected
            pages_detail.update(_corrections)
            if _total_corrected:
                logger.info("[pages_detail] ✓ %d méthode(s) corrigées inline", _total_corrected)
        except Exception as _corr_err:
            logger.warning("[pages_detail] correction inline échouée (non bloquant) : %s", _corr_err)

    _expected_paths = {p.get("path") if isinstance(p, dict) else str(p) for p in pages}
    logger.info("[pages_detail] pages attendues: %s", sorted(_expected_paths))
    logger.info("[pages_detail] pages retournées: %s", sorted(pages_detail.keys()))

    interactive_count = sum(
        1 for v in pages_detail.values()
        if (isinstance(v, dict) and v.get("interactive", False))
        or (isinstance(v, str) and "[INTERACTIVE]" in v)
    )
    logger.info(
        "[pages_detail] ✓ %d page(s) décrites, %d interactive",
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

    brief_pages_detail = brief.get("pages_detail", {})
    if not isinstance(brief_pages_detail, dict):
        brief_pages_detail = {}

    # ── Invariant detail-slug : page_type="detail-slug" exige slug String @unique dans le modèle ──
    # Le LLM page_planner peut générer [slug] pour un modèle avec isPublic Boolean sans champ slug.
    # Résultat : [id] (form generator) + [slug] (executor) coexistent → conflit routing Next.js fatal.
    # Ce check valide l'invariant AVANT de créer le ProjectSpec — la correction est logguée, pas silencieuse.
    _model_has_slug: dict[str, bool] = {
        _m.name: any(f.name == "slug" and "@unique" in f.attributes for f in _m.fields)
        for _m in models
    }
    for _pg in pages:
        if _pg.page_type == "detail-slug" and _pg.model:
            if not _model_has_slug.get(_pg.model, False):
                _old_path = _pg.path
                _pg.path = _pg.path.replace("[slug]", "[id]")
                _pg.page_type = "detail"
                seen_paths.discard(_old_path)
                seen_paths.add(_pg.path)
                logger.warning(
                    "[planner] invariant detail-slug : '%s' → '%s' "
                    "(modèle '%s' sans slug @unique — page_planner a ignoré RÈGLE 9)",
                    _old_path, _pg.path, _pg.model,
                )

    # ── Post-build : force auth_required=False pour les pages décrivant un comportement public ──
    # Corrige le cas où brief_writer_node (LLM) met auth=True sur une page qui devrait être publique.
    # Source de vérité : pages_detail généré par pages_detail_node (déjà dans brief à ce stade).
    _PUBLIC_SIGNALS = {
        "public", "sans auth", "sans authentification", "visiteur",
        "accessible sans connexion", "ne pas appeler auth", "pas d'import clerk",
        "no auth", "aucune authentification",
    }
    for _pg in pages:
        if not _pg.auth_required:
            continue  # déjà public, rien à faire
        _detail_raw = brief_pages_detail.get(_pg.path, "")
        # Gère dict structuré (D1) et str (backward compat)
        _detail = (
            " ".join(str(_detail_raw.get(k, "")) for k in ("description",)).lower()
            if isinstance(_detail_raw, dict)
            else str(_detail_raw).lower()
        )
        if any(_sig in _detail for _sig in _PUBLIC_SIGNALS):
            logger.warning(
                "[planner] '%s' forcée auth_required=False — pages_detail décrit un comportement public",
                _pg.path,
            )
            _pg.auth_required = False

    # ── Garde RÈGLE 5 : auto-ajout des pages détail pour les modèles parents ─────
    # Si le LLM a respecté RÈGLE 5 → ces pages existent déjà → aucun ajout.
    # Si le LLM a oublié → on les ajoute déterministiquement pour éviter les 404
    # post-création d'entités enfants (createComment → redirect /tasks/${id} → 404).
    _declared_detail_paths: set[str] = {
        p.path for p in pages if p.page_type in ("detail", "detail-slug")
    }
    _model_names_set: set[str] = {m.name for m in models}
    for _m in models:
        # Cherche les champs FK de ce modèle (xxxId pointant vers un autre modèle)
        for _f in _m.fields:
            if not _f.name.endswith("Id") or _f.name in {"id"}:
                continue
            _base = _f.name[:-2]
            _parent_name = _base[0].upper() + _base[1:] if _base else ""
            if _parent_name not in _model_names_set:
                _suffix_matches = [mn for mn in _model_names_set if mn.endswith(_parent_name)]
                if _suffix_matches:
                    _parent_name = _suffix_matches[0]
            if _parent_name not in _model_names_set:
                continue
            # Trouver le list_page du parent
            _parent_list = next(
                (p.path for p in pages if p.page_type == "list" and p.model == _parent_name),
                None,
            )
            if not _parent_list:
                continue
            _slug_path = f"{_parent_list}/[slug]"
            _detail_path = f"{_parent_list}/[id]"
            # Vérifie si [slug] est déjà utilisé sous ce parent — exact OU comme préfixe
            # (ex: /dashboard/categories/[slug]/edit signale que [slug] est en usage)
            _slug_in_use = any(
                p == _slug_path or p.startswith(f"{_slug_path}/") for p in seen_paths
            ) or _slug_path in _declared_detail_paths
            if _slug_in_use:
                continue  # [slug] déjà présent → ajouter [id] créerait un conflit Next.js
            if _detail_path not in _declared_detail_paths and _detail_path not in seen_paths:
                pages.append(AppPage(
                    path=_detail_path,
                    auth_required=True,
                    model=_parent_name,
                    page_type="detail",
                ))
                seen_paths.add(_detail_path)
                _declared_detail_paths.add(_detail_path)
                logger.warning(
                    "[planner] RÈGLE 5 auto-corrigée : '%s' ajoutée (parent de %s via %s)",
                    _detail_path, _m.name, _f.name,
                )

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

    brief_enums = brief.get("enums", {})
    if not isinstance(brief_enums, dict):
        brief_enums = {}

    brief_ui_labels = brief.get("ui_labels", {})
    if not isinstance(brief_ui_labels, dict):
        brief_ui_labels = {}

    brief_title_plurals = brief.get("title_plurals", {})
    if not isinstance(brief_title_plurals, dict):
        brief_title_plurals = {}

    brief_title_singulars = brief.get("title_singulars", {})
    if not isinstance(brief_title_singulars, dict):
        brief_title_singulars = {}

    brief_enum_value_labels = brief.get("enum_value_labels", {})
    if not isinstance(brief_enum_value_labels, dict):
        brief_enum_value_labels = {}

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
        ui_labels=brief_ui_labels,
        title_plurals=brief_title_plurals,
        title_singulars=brief_title_singulars,
        enum_value_labels=brief_enum_value_labels,
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

    # Propage design_system depuis le brief pour le frontend generator
    design_system = brief.get("design_system") or {}
    if design_system:
        spec_dict["design_system"] = design_system

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
    """
    Pipeline architect décomposé (Plan6 — Bloc D) :

    Brief libre (no models) :
        domain_interpreter → page_planner → semantic_annotator → pages_detail → spec_enricher → planner

    Brief avec models mais sans pages :
        page_planner → semantic_annotator → pages_detail → spec_enricher → planner

    Brief complet (models + pages) :
        semantic_annotator → pages_detail → spec_enricher → planner

    Tous les nœuds sont idempotents (skip si déjà rempli).
    """
    from langgraph.graph import StateGraph, START, END
    from agents.domain_interpreter import domain_interpreter_node
    from agents.page_planner import page_planner_node
    from agents.spec_enricher import spec_enricher_node

    def _route_entry(state: AgentState) -> str:
        brief = state.get("brief", {})
        has_models = bool(brief.get("models"))
        has_pages = bool(brief.get("pages"))
        if has_models and has_pages:
            return "semantic_annotator"
        if has_models:
            return "page_planner"
        return "domain_interpreter"

    workflow = StateGraph(AgentState)
    workflow.add_node("domain_interpreter", domain_interpreter_node)
    workflow.add_node("page_planner", page_planner_node)
    workflow.add_node("semantic_annotator", semantic_annotator_node)
    workflow.add_node("pages_detail", pages_detail_node)
    workflow.add_node("spec_enricher", spec_enricher_node)
    workflow.add_node("planner", planner_node)

    workflow.add_conditional_edges(
        START,
        _route_entry,
        {
            "domain_interpreter": "domain_interpreter",
            "page_planner": "page_planner",
            "semantic_annotator": "semantic_annotator",
        },
    )
    workflow.add_edge("domain_interpreter", "page_planner")
    workflow.add_edge("page_planner", "semantic_annotator")
    workflow.add_edge("semantic_annotator", "pages_detail")
    workflow.add_edge("pages_detail", "spec_enricher")
    workflow.add_edge("spec_enricher", "planner")
    workflow.add_edge("planner", END)
    return workflow.compile()
