"""
feature_modules/module_detail_with_children.py
───────────────────────────────────────────────
Module déterministe : page-client.tsx pour les pages détail d'un modèle parent
qui a des enfants FK (relations 1-N).

Remplace la génération LLM des pages CROSS_ENTITY par un fichier déterministe
qui inclut :
  - Affichage des champs du parent
  - Liste des enfants avec suppression
  - Formulaire inline de création d'un enfant (useActionState)

Avantages vs LLM :
  - Pas de mismatch props (page.tsx et page-client.tsx générés en cohérence)
  - Pas de 404 post-création (fk_field injecté automatiquement dans le formulaire)
  - Extensible : ajouter un type d'enfant = ajouter une relation dans le schéma

Activation : tout modèle parent avec au moins une relation 1-N
             ET une page détail déclarée dans spec.pages.
"""
from __future__ import annotations

import logging
import os

import jinja2

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")

_jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(_TEMPLATES_DIR),
    undefined=jinja2.StrictUndefined,
    trim_blocks=True,
    lstrip_blocks=True,
    keep_trailing_newline=True,
    autoescape=False,
)

from ..feature_module import FeatureModule, register
from ..dev_naming import pascal_to_camel, pascal_to_kebab, path_to_client_component


def _get_child_display_fields(child_ctx) -> list[str]:
    """Champs affichables du modèle enfant (hors id, FK, owner)."""
    if child_ctx is None:
        return ["id"]
    return child_ctx.display_fields[:3] or ["id"]


def _get_child_create_fields(child_ctx) -> list[dict]:
    """Champs du formulaire de création d'un enfant."""
    if child_ctx is None:
        return []
    return [
        {
            "name": f.name,
            "input_type": f.input_type,
            "is_optional": f.is_optional,
            "has_default": f.has_default,
            "enum_values": list(f.allowed_values) if f.allowed_values else [],
            "enum_labels": {},
        }
        for f in child_ctx.editable_fields
        # Exclure les FK (elles sont injectées automatiquement comme champ caché)
        if f.name not in {fk.field_name for fk in child_ctx.fk_fields}
    ]


class DetailWithChildrenModule(FeatureModule):
    """
    Génère page-client.tsx pour les modèles parents avec enfants FK.
    Déterministe et coordonné avec le page.tsx existant (qui passe `item`
    depuis getByIdWithRelations — les enfants sont dans item.<relation>).
    """

    @property
    def name(self) -> str:
        return "detail_with_children"

    @property
    def priority(self) -> int:
        return 100  # défaut — génère des detail page-client.tsx, pas de conflit avec search/status_flow

    @property
    def produces(self) -> list[str]:
        return ["app/{detail_path}/page-client.tsx"]

    def should_activate(self, enriched_spec, ctx) -> bool:
        # Activer dès qu'un modèle a des relations tableau (enfants FK).
        # Pas de dépendance à list_page_path : un modèle enfant (ex: Task sans liste standalone)
        # peut tout de même avoir une page détail avec ses propres enfants (ex: Comment).
        if not ctx.has_relations:
            return False
        return any(r.is_array for r in ctx.relation_fields)

    def generate(self, spec, ctx, enriched_spec, workdir: str, model_contexts: "dict | None" = None) -> dict[str, str]:
        spec_pages = getattr(spec, "pages", []) or []

        # Trouver la page détail de ce modèle dans le spec (par model, indépendamment de list_page_path)
        detail_page = next(
            (p for p in spec_pages
             if getattr(p, "model", None) == ctx.name
             and getattr(p, "page_type", None) in ("detail", "detail-slug")),
            None,
        )
        if detail_page is None:
            return {}

        detail_path = detail_page.path

        # list_path : depuis ctx ou déduit depuis le chemin détail ou chemin conventionnel
        list_path = ctx.list_page_path
        if not list_path and detail_path:
            _segs = [s for s in detail_path.strip("/").split("/") if not s.startswith("[")]
            list_path = "/" + "/".join(_segs) if _segs else f"/{ctx.kebab}s"
        if not list_path:
            list_path = f"/{ctx.kebab}s"

        # Trouver les modèles enfants : modèles qui ont une FK vers ctx.name
        child_prisma_models: dict = {}
        for m in (getattr(spec, "models", []) or []):
            if m.name == ctx.name:
                continue
            for f in m.fields:
                if not f.name.endswith("Id"):
                    continue
                base = f.name[:-2]
                candidate = base[0].upper() + base[1:] if base else ""
                if candidate == ctx.name or any(
                    mn == ctx.name for mn in [candidate]
                ):
                    child_prisma_models[m.name] = m
                    break

        if not child_prisma_models:
            return {}

        # Contextes ModelGenerationContext pour les champs enrichis (ne pas écraser le paramètre)
        all_model_contexts = model_contexts or {}

        children_ctx = []
        for child_name, child_model in child_prisma_models.items():
            # Trouver le FK field qui pointe vers le parent
            fk_field = next(
                (
                    f.name for f in child_model.fields
                    if f.name.endswith("Id") and (
                        f.name[:-2][0].upper() + f.name[:-2][1:] == ctx.name
                        if f.name[:-2] else False
                    )
                ),
                f"{pascal_to_camel(ctx.name)}Id",
            )
            # Relation array sur le parent (ex: "comments" pour Comment)
            relation_field = pascal_to_camel(child_name) + "s"
            # Essayer de trouver le nom exact depuis les relation_fields du parent
            for rf in ctx.relation_fields:
                if rf.is_array and rf.name.lower().startswith(pascal_to_camel(child_name).lower()):
                    relation_field = rf.name
                    break

            child_camel = pascal_to_camel(child_name)
            child_kebab = pascal_to_kebab(child_name)
            child_ctx_obj = all_model_contexts.get(child_name)

            # Trouver le list_path de l'enfant pour l'import des actions.
            # get_list_page_for_model() priorise auth_required=True — évite de pointer
            # vers une page publique (ex: /blog) qui n'a pas d'actions.ts.
            child_list_page = spec.get_list_page_for_model(child_name) or f"/{child_kebab}s"

            children_ctx.append({
                "name": child_name,
                "camel": child_camel,
                "kebab": child_kebab,
                "serialized_type": f"Serialized{child_name}",
                "relation_field": relation_field,
                "fk_field": fk_field,
                "display_fields": _get_child_display_fields(child_ctx_obj),
                "create_fields": _get_child_create_fields(child_ctx_obj),
                "actions_import": f"@/app/{child_list_page.lstrip('/')}/actions",
                "title_plural": (child_ctx_obj.title_plural if child_ctx_obj else _title_plurals_spec.get(child_name, f"{child_name}s")),
            })

        if not children_ctx:
            return {}

        # Labels UI — depuis ModelGenerationContext (source unifiée)
        _model_labels = ctx.ui_labels
        _enum_value_labels = ctx.enum_value_labels
        # title_plural pour les enfants : depuis leur ModelGenerationContext (source unifiée)
        # Fallback spec si le ctx enfant n'est pas encore disponible à ce stade
        _title_plurals_spec = getattr(spec, "title_plurals", {}) or {}

        display_fields = ctx.display_fields
        field_labels = {f: _model_labels.get(f, f) for f in display_fields}

        # Enrichir les labels enum des champs d'affichage
        enum_display: dict[str, dict] = {}
        for ef in ctx.editable_fields:
            if ef.input_type == "enum-select" and ef.name in display_fields:
                labels = _enum_value_labels.get(ef.base_type, {})
                if labels:
                    enum_display[ef.name] = labels

        # Labels pour les formulaires enfants — depuis le ctx enfant (source unifiée)
        for child in children_ctx:
            _child_ctx = all_model_contexts.get(child["name"])
            child_labels = (_child_ctx.ui_labels if _child_ctx else {}) or {}
            for cf in child["create_fields"]:
                cf["label"] = child_labels.get(cf["name"], cf["name"])
                # Labels enum pour les champs enfants
                if cf["input_type"] == "enum-select" and cf["enum_values"]:
                    child_child_ctx = all_model_contexts.get(child["name"])
                    if child_child_ctx:
                        for ef in child_child_ctx.editable_fields:
                            if ef.name == cf["name"] and ef.allowed_values:
                                ev_labels = _enum_value_labels.get(ef.base_type, {})
                                cf["enum_labels"] = ev_labels

        try:
            content = _jinja_env.get_template("detail_with_children_client.tsx.j2").render(
                name=ctx.name,
                camel=ctx.camel,
                serialized_type=ctx.serialized_type,
                client_name=path_to_client_component(detail_path),
                list_path=list_path,
                display_fields=display_fields,
                field_labels=field_labels,
                enum_display=enum_display,
                title_plural=ctx.title_plural,
                children=children_ctx,
                # tokens sémantiques CSS variables (tailwind.config.js → hsl(var(--primary)))
                primary="primary",
                primary_hover="primary/85",
                primary_light="primary/10",
                primary_ring="primary",
                # design_system non transmis par run_feature_modules → valeurs par défaut "normal"/"elevated"
                p_cls="p-6",
                card_cls="bg-card rounded-lg shadow-sm border border-border",
            )
        except Exception as e:
            logger.error("[detail_with_children] erreur template %s : %s", ctx.name, e)
            return {}

        page_path_clean = detail_path.strip("/")
        rel = f"app/{page_path_clean}/page-client.tsx"
        abs_path = os.path.join(workdir, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info("[detail_with_children] ✓ %s (parent=%s, %d enfant(s))", rel, ctx.name, len(children_ctx))
        return {rel: content}


register(DetailWithChildrenModule())
