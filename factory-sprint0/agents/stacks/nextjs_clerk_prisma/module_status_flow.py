"""
agents/stacks/nextjs_clerk_prisma/module_status_flow.py
────────────────────────────────────────────────────────
FeatureModule : status_flow — badges colorés + filtre par statut sur la liste.

Activation : modèle a un champ "status" (ctx.has_status).
Produit    : app/{list_dir}/page-client.tsx (remplace la version de base ou search).
             Compose avec module_search si "search" est aussi actif.
"""
from __future__ import annotations

import logging
import os

import jinja2

from .feature_module import FeatureModule, register
from .dev_naming import path_to_client_component

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
_jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(_TEMPLATES_DIR),
    undefined=jinja2.StrictUndefined,
    trim_blocks=True,
    lstrip_blocks=True,
    keep_trailing_newline=True,
    autoescape=False,
)


class StatusFlowModule(FeatureModule):

    @property
    def name(self) -> str:
        return "module_status_flow"

    def should_activate(self, enriched_spec, ctx) -> bool:
        return bool(ctx.has_status and ctx.list_page_path)

    def generate(self, spec, ctx, enriched_spec, workdir: str) -> dict[str, str]:
        list_path = ctx.list_page_path
        list_dir = list_path.lstrip("/")
        route = list_dir

        # Page list — pour client_name et auth_required
        pages = getattr(spec, "pages", []) or []
        list_page = next(
            (p for p in pages if getattr(p, "model", None) == ctx.name and getattr(p, "page_type", None) == "list"),
            None,
        )
        client_name = path_to_client_component(list_page.path) if list_page else f"{ctx.name}ListClient"
        auth_required = getattr(list_page, "auth_required", True) if list_page else True

        # Valeurs de l'enum status
        status_field_obj = next(
            (f for f in ctx.model.fields if f.name.lower() == "status"), None
        )
        status_values: list[str] = []
        if status_field_obj:
            base = status_field_obj.type.rstrip("?").rstrip("[]")
            status_values = ctx.spec_enums.get(base, [])
        if not status_values:
            status_values = ["pending", "active", "done"]

        # Compose avec module_search si la feature search est aussi active
        has_search = bool(
            enriched_spec and enriched_spec.has_feature("search")
            or any(f.input_type == "text" for f in ctx.editable_fields)
        )

        try:
            content = _jinja_env.get_template("list_client_status.tsx.j2").render(
                name=ctx.name,
                camel=ctx.camel,
                serialized_type=ctx.serialized_type,
                client_name=client_name,
                list_path=list_path,
                list_dir=list_dir,
                display_fields=ctx.display_fields[:2],
                auth_required=auth_required,
                has_delete=auth_required,
                status_field="status",
                status_values=status_values,
                has_search=has_search,
            )
        except Exception as e:
            logger.error("[module_status_flow] rendu template échoué pour %s : %s", ctx.name, e)
            return {}

        rel = f"app/{route}/page-client.tsx"
        abs_path = os.path.join(workdir, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info("[module_status_flow] ✓ %s (%s, %d statuts)", rel, ctx.name, len(status_values))
        return {rel: content}


# Auto-enregistrement au chargement du module
register(StatusFlowModule())
