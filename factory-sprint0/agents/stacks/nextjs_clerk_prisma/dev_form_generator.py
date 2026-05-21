"""
agents/stacks/nextjs_clerk_prisma/dev_form_generator.py  (Jinja2 edition)
──────────────────────────────────────────────────────────────────────────
Génération déterministe des page-client.tsx — orchestrateur Jinja2.

Les templates sont dans ./templates/*.tsx.j2.
Ce fichier ne contient aucune concaténation de strings JSX — seulement la
préparation des variables de contexte et l'appel à Jinja2.

Fichiers produits (tous dans template_written) :
  app/{list_path}/page-client.tsx
  app/{list_path}/new/page-client.tsx
  app/{list_path}/[id]/page-client.tsx   (si page detail déclarée)
  app/{list_path}/[id]/edit/page-client.tsx

Point d'entrée : generate_all_page_clients(spec, model_contexts, project_workdir)
"""
from __future__ import annotations

import logging
import os

import jinja2

from .dev_naming import path_to_client_component
from .dev_model_context import ModelGenerationContext
from .dev_pages_generator import _find_create_model as _infer_create_model

logger = logging.getLogger(__name__)

# ── Environnement Jinja2 ──────────────────────────────────────────────────────

_TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

_jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(_TEMPLATES_DIR),
    undefined=jinja2.StrictUndefined,
    trim_blocks=True,
    lstrip_blocks=True,
    keep_trailing_newline=True,
    autoescape=False,  # TSX — pas d'HTML escaping
)


def _render(template_name: str, **ctx) -> str:
    return _jinja_env.get_template(template_name).render(**ctx)


# ── Helpers de contexte ───────────────────────────────────────────────────────

def _related_display(fk, model_contexts: dict) -> str:
    """Premier champ d'affichage du modèle lié, défaut 'id'."""
    rel_ctx: ModelGenerationContext | None = model_contexts.get(fk.related_model)
    return rel_ctx.display_fields[0] if rel_ctx and rel_ctx.display_fields else "id"


def _field_to_ctx(field, spec_enums: dict) -> dict:
    """Convertit FieldInfo en dict template-friendly (ajoute enum_values)."""
    return {
        "name":       field.name,
        "input_type": field.input_type,
        "is_optional": field.is_optional,
        "has_default": field.has_default,
        "enum_values": spec_enums.get(field.base_type, []) if field.input_type == "enum-select" else [],
    }


def _fk_to_ctx(fk, display: str) -> dict:
    return {
        "field_name":    fk.field_name,
        "related_model": fk.related_model,
        "related_camel": fk.related_camel,
        "related_display": display,
    }


# ── Générateurs individuels (chacun rend UN template) ────────────────────────

def _gen_list_client(page, ctx: ModelGenerationContext) -> str:
    list_path = ctx.list_page_path or f"/{ctx.kebab}s"
    auth_required = getattr(page, "auth_required", True)
    return _render(
        "list_client.tsx.j2",
        name=ctx.name,
        camel=ctx.camel,
        serialized_type=ctx.serialized_type,
        client_name=path_to_client_component(page.path),
        list_path=list_path,
        list_dir=list_path.lstrip("/"),
        display_fields=ctx.display_fields[:2],
        auth_required=auth_required,
        has_delete=auth_required,
    )


def _gen_create_client(page, ctx: ModelGenerationContext, model_contexts: dict) -> str:
    list_path = ctx.list_page_path or f"/{ctx.kebab}s"
    list_dir = list_path.lstrip("/")
    fk_fields = [_fk_to_ctx(fk, _related_display(fk, model_contexts)) for fk in ctx.fk_fields]
    editable_fields = [_field_to_ctx(f, ctx.spec_enums) for f in ctx.editable_fields]
    fk_props = ", ".join(
        f"{fk['related_camel']}Options: Serialized{fk['related_model']}[]"
        for fk in fk_fields
    )
    fk_destructure = ", ".join(f"{fk['related_camel']}Options" for fk in fk_fields)
    fk_type_imports = ", ".join(f"Serialized{fk['related_model']}" for fk in fk_fields)
    return _render(
        "create_client.tsx.j2",
        name=ctx.name,
        serialized_type=ctx.serialized_type,
        client_name=path_to_client_component(page.path),
        list_path=list_path,
        list_dir=list_dir,
        # Import absolu via @/ — résolvable depuis n'importe quelle profondeur
        actions_import=f"@/app/{list_dir}/actions",
        type_imports=fk_type_imports,
        fk_fields=fk_fields,
        editable_fields=editable_fields,
        fk_props=fk_props,
        fk_destructure=fk_destructure,
    )


def _gen_edit_client(ctx: ModelGenerationContext, model_contexts: dict) -> str:
    list_path = ctx.list_page_path or f"/{ctx.kebab}s"
    list_dir = list_path.lstrip("/")
    fk_fields = [_fk_to_ctx(fk, _related_display(fk, model_contexts)) for fk in ctx.fk_fields]
    editable_fields = [_field_to_ctx(f, ctx.spec_enums) for f in ctx.editable_fields]
    return _render(
        "edit_client.tsx.j2",
        name=ctx.name,
        serialized_type=ctx.serialized_type,
        client_name=f"{ctx.name}EditClient",
        list_path=list_path,
        list_dir=list_dir,
        fk_fields=fk_fields,
        editable_fields=editable_fields,
    )


def _gen_detail_client(page, ctx: ModelGenerationContext) -> str:
    list_path = ctx.list_page_path or f"/{ctx.kebab}s"
    list_dir = list_path.lstrip("/")
    # Déduplique : display_fields d'abord, puis les éditables restants
    shown = list(dict.fromkeys(ctx.display_fields + [f.name for f in ctx.editable_fields]))
    auth_required = getattr(page, "auth_required", True)
    return _render(
        "detail_client.tsx.j2",
        name=ctx.name,
        serialized_type=ctx.serialized_type,
        client_name=path_to_client_component(page.path),
        list_path=list_path,
        list_dir=list_dir,
        display_fields=shown,
        auth_required=auth_required,
        has_delete=auth_required,
    )


# ── Point d'entrée ────────────────────────────────────────────────────────────

def generate_all_page_clients(
    spec,
    model_contexts: dict,
    project_workdir: str,
) -> dict[str, str]:
    """
    Génère déterministiquement les page-client.tsx pour toutes les pages CRUD.
    Retourne {rel_path: content} pour intégration dans template_written.
    """
    written: dict[str, str] = {}
    pages = getattr(spec, "pages", []) or []

    # Modèles avec CRUD complet (list auth + create) → éligibles à l'edit page
    # Les pages create ont intentionnellement model=None (project_spec.py) — on infère
    crud_models: set[str] = set()
    has_create: set[str] = set()
    for p in pages:
        pt = getattr(p, "page_type", None)
        pm = getattr(p, "model", None)
        if not pm and pt == "create":
            _inf = _infer_create_model(p, spec)
            pm = _inf.name if _inf else None
        if pt == "list" and pm and getattr(p, "auth_required", True):
            crud_models.add(pm)
        if pt == "create" and pm:
            has_create.add(pm)
    crud_models &= has_create

    # Pages list / create / detail
    for page in pages:
        model_name = getattr(page, "model", None)
        page_type = getattr(page, "page_type", None)
        # Les pages create ont intentionnellement model=None — inférer depuis la page list parente
        if not model_name and page_type == "create":
            _inf = _infer_create_model(page, spec)
            model_name = _inf.name if _inf else None
        if not model_name:
            continue
        ctx = model_contexts.get(model_name)
        if ctx is None:
            continue

        page_path_clean = page.path.strip("/")

        try:
            if page_type == "list":
                rel = f"app/{page_path_clean}/page-client.tsx" if page_path_clean else "app/page-client.tsx"
                content = _gen_list_client(page, ctx)
            elif page_type == "create":
                rel = f"app/{page_path_clean}/page-client.tsx"
                content = _gen_create_client(page, ctx, model_contexts)
            elif page_type in ("detail", "detail-slug"):
                rel = f"app/{page_path_clean}/page-client.tsx"
                content = _gen_detail_client(page, ctx)
            else:
                continue
        except Exception as _gen_err:
            logger.error("[form_gen] erreur génération %s (%s) : %s", page_path_clean, page_type, _gen_err)
            continue

        abs_path = os.path.join(project_workdir, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        written[rel] = content
        logger.info("[form_gen] ✓ %s (model=%s type=%s)", rel, model_name, page_type)

    # Edit pages — pour chaque modèle CRUD complet
    for model in spec.models:
        if model.name not in crud_models:
            continue
        ctx = model_contexts.get(model.name)
        if ctx is None:
            continue
        list_path = ctx.list_page_path
        if not list_path:
            continue

        try:
            route = list_path.lstrip("/")
            rel = f"app/{route}/[id]/edit/page-client.tsx"
            content = _gen_edit_client(ctx, model_contexts)
        except Exception as _edit_err:
            logger.error("[form_gen] erreur edit %s : %s", model.name, _edit_err)
            continue

        abs_path = os.path.join(project_workdir, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        written[rel] = content
        logger.info("[form_gen] ✓ edit %s (model=%s)", rel, model.name)

    logger.info("[form_gen] %d page-client.tsx générés (Jinja2)", len(written))
    return written
