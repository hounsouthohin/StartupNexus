"""
agents/stacks/nextjs_clerk_prisma/module_search.py
───────────────────────────────────────────────────
FeatureModule : search — barre de recherche + filtre client-side sur la liste.

Activation : "search" dans EnrichedSpec.features ET modèle a une page list.
Produit    : app/{list_dir}/page-client.tsx (remplace la version de base)
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


class SearchModule(FeatureModule):

    @property
    def name(self) -> str:
        return "module_search"

    def should_activate(self, enriched_spec, ctx) -> bool:
        if not ctx.list_page_path:
            return False
        # module_status_flow gère ce cas : list_client_status.tsx.j2 intègre
        # la barre de recherche via has_search — pas besoin d'un fichier intermédiaire.
        if ctx.has_status:
            return False
        if enriched_spec and enriched_spec.has_feature("search"):
            return True
        # Heuristique : modèle avec au moins un champ String éditable non-FK
        return any(
            f.input_type == "text"
            for f in ctx.editable_fields
        )

    def generate(self, spec, ctx, enriched_spec, workdir: str) -> dict[str, str]:
        list_path = ctx.list_page_path
        list_dir = list_path.lstrip("/")
        route = list_dir

        # Retrouve la page list pour le client_name
        pages = getattr(spec, "pages", []) or []
        list_page = next(
            (p for p in pages if getattr(p, "model", None) == ctx.name and getattr(p, "page_type", None) == "list"),
            None,
        )
        client_name = path_to_client_component(list_page.path) if list_page else f"{ctx.name}ListClient"
        auth_required = getattr(list_page, "auth_required", True) if list_page else True

        fields = ctx.display_fields[:2]
        _ui_labels = getattr(spec, "ui_labels", {}) or {}
        _model_labels = _ui_labels.get(ctx.name, {})
        _title_plurals = getattr(spec, "title_plurals", {}) or {}

        try:
            content = _jinja_env.get_template("list_client_search.tsx.j2").render(
                name=ctx.name,
                camel=ctx.camel,
                serialized_type=ctx.serialized_type,
                client_name=client_name,
                list_path=list_path,
                list_dir=list_dir,
                display_fields=fields,
                field_labels={f: _model_labels.get(f, f) for f in fields},
                title_plural=_title_plurals.get(ctx.name, f"{ctx.name}s"),
                auth_required=auth_required,
                has_delete=auth_required,
                has_slug=ctx.has_slug,
            )
        except Exception as e:
            logger.error("[module_search] rendu template échoué pour %s : %s", ctx.name, e)
            return {}

        rel = f"app/{route}/page-client.tsx"
        abs_path = os.path.join(workdir, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info("[module_search] ✓ %s (%s)", rel, ctx.name)
        return {rel: content}


# Auto-enregistrement au chargement du module
register(SearchModule())
