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

    @property
    def priority(self) -> int:
        # 10 = gagne sur module_search (50) car son template intègre déjà has_search
        return 10

    @property
    def produces(self) -> list[str]:
        return ["app/{list_dir}/page-client.tsx"]

    def should_activate(self, enriched_spec, ctx) -> bool:
        # features["status_flow"] primaire (signal architect), ctx.has_status comme fallback structurel
        has_feature = bool(enriched_spec and enriched_spec.has_feature("status_flow"))
        return bool((has_feature or ctx.has_status) and ctx.list_page_path)

    def generate(self, spec, ctx, enriched_spec, workdir: str, model_contexts: "dict | None" = None, design_system: "dict | None" = None) -> dict[str, str]:
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
        _status_enum_name: str = ""
        if status_field_obj:
            _status_enum_name = status_field_obj.type.rstrip("?").rstrip("[]")
            status_values = ctx.spec_enums.get(_status_enum_name, [])
        if not status_values:
            status_values = ["pending", "active", "done"]

        # Labels traduits pour les options du filtre
        _enum_value_labels = getattr(spec, "enum_value_labels", {}) or {}
        status_labels: dict[str, str] = _enum_value_labels.get(_status_enum_name, {})

        # Compose avec module_search uniquement si l'architect a déclaré "search" — pas d'heuristique
        has_search = bool(enriched_spec and enriched_spec.has_feature("search"))

        fields = ctx.display_fields[:2]
        _model_labels = ctx.ui_labels

        # field_enum_labels : enums non-status dans display_fields (ex: priority)
        _field_enum_labels: dict[str, dict[str, str]] = {}
        for _ef in ctx.editable_fields:
            if _ef.name in fields and _ef.name != "status" and _ef.input_type == "enum-select":
                _lbls = _enum_value_labels.get(_ef.base_type, {})
                if _lbls:
                    _field_enum_labels[_ef.name] = _lbls
        _boolean_fields = {_ef.name for _ef in ctx.editable_fields if _ef.base_type == "Boolean"}

        # empty_state_message depuis ux_hints (produit par le semantic annotator)
        _empty_msg = ""
        try:
            _ux = getattr(enriched_spec, "ux_hints", None) if enriched_spec else None
            if _ux:
                _empty_msg = (getattr(_ux, "empty_states", {}) or {}).get(list_path, "")
        except Exception:
            pass

        # Tokens design (card_cls, p_cls, transition_cls, primary…) — source unique :
        # dev_form_generator._design_tokens. Les tokens hardcodés partiels avaient tué
        # le module ('card_cls' undefined) quand le template a évolué.
        from .dev_form_generator import _design_tokens, _related_display
        _tokens = _design_tokens(design_system)

        # Colonnes des parents FK (ex: nom du client sur la liste des projets) —
        # même construction que dev_form_generator pour ne pas perdre la colonne
        # quand ce module écrase le page-client de base.
        _parent_rels = [
            {
                "related_camel": fk.related_camel,
                "display_field": _related_display(fk, model_contexts or {}),
                "label": ctx.ui_labels.get(fk.field_name, fk.related_model),
            }
            for fk in ctx.fk_fields
        ]

        try:
            content = _jinja_env.get_template("list_client_status.tsx.j2").render(
                name=ctx.name,
                camel=ctx.camel,
                serialized_type=ctx.serialized_type,
                client_name=client_name,
                list_path=list_path,
                list_dir=list_dir,
                display_fields=fields,
                field_labels={f: _model_labels.get(f, f) for f in fields},
                title_plural=ctx.title_plural,
                auth_required=auth_required,
                has_delete=auth_required,
                status_field="status",
                status_values=status_values,
                status_labels=status_labels,
                field_enum_labels=_field_enum_labels,
                boolean_fields=_boolean_fields,
                has_search=has_search,
                has_slug=ctx.has_slug,
                empty_state_message=_empty_msg,
                parent_relations=_parent_rels,
                **_tokens,
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
