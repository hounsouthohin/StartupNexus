# agents/architect.py
from __future__ import annotations

import logging
import operator
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

    spec = ProjectSpec(
        project_name=project_name,
        stack_id=stack_id,
        description=brief_description,
        models=models,
        routes=routes,
        pages=pages,
        pages_detail=brief_pages_detail,
        user_flows=user_flows,
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
    workflow = StateGraph(AgentState)
    workflow.add_node("planner", planner_node)
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", END)
    return workflow.compile()
