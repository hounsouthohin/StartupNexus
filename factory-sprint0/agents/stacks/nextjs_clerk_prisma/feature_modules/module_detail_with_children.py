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

    def generate(self, spec, ctx, enriched_spec, workdir: str, model_contexts: "dict | None" = None, design_system: "dict | None" = None) -> dict[str, str]:
        spec_pages = getattr(spec, "pages", []) or []

        # Trouver la page détail PRIVÉE de ce modèle (par model, indépendamment de list_page_path).
        # Les pages détail publiques ne rendent JAMAIS les enfants : les modèles enfants portent
        # souvent des données personnelles (nom, email des participants…) qui ne doivent pas être
        # exposées aux visiteurs non authentifiés. Le page-client détail de base (form generator)
        # reste en place pour la version publique. (Fuite PII réelle : club-running, 6 Juil 2026.)
        _detail_pages = [
            p for p in spec_pages
            if getattr(p, "model", None) == ctx.name
            and getattr(p, "page_type", None) in ("detail", "detail-slug")
        ]
        detail_page = next(
            (p for p in _detail_pages if getattr(p, "auth_required", True)),
            None,
        )
        if detail_page is None:
            if _detail_pages:
                logger.info(
                    "[detail_with_children] %s : page(s) détail publique(s) uniquement — "
                    "enfants non rendus (protection PII).", ctx.name,
                )
            return {}

        detail_path = detail_page.path
        auth_required = bool(getattr(detail_page, "auth_required", True))

        # list_path : back link de navigation retour
        # Page détail publique → liste publique du modèle (pas /dashboard/xxx privé)
        # Page détail privée  → liste privée via ctx.list_page_path
        if not auth_required:
            _public_list = next(
                (p for p in spec_pages
                 if getattr(p, "model", None) == ctx.name
                 and getattr(p, "page_type", None) == "list"
                 and not getattr(p, "auth_required", True)),
                None,
            )
            list_path = _public_list.path if _public_list else None
        else:
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

        # title_plurals : fallback spec si le ctx enfant n'est pas disponible.
        # DOIT être défini AVANT la boucle children_ctx qui l'utilise (UnboundLocalError sinon).
        _title_plurals_spec = getattr(spec, "title_plurals", {}) or {}

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

            # Base du chemin détail de l'enfant (ex: /projects) — None si pas de page detail déclarée.
            _child_detail_page = next(
                (p for p in spec_pages
                 if getattr(p, "model", None) == child_name
                 and getattr(p, "page_type", None) in ("detail", "detail-slug")),
                None,
            )
            _child_detail_base: str | None = None
            if _child_detail_page:
                _static = [s for s in _child_detail_page.path.strip("/").split("/") if not s.startswith("[")]
                _child_detail_base = "/" + "/".join(_static) if _static else None

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
                "detail_base": _child_detail_base,
            })

        if not children_ctx:
            return {}

        # Labels UI — depuis ModelGenerationContext (source unifiée)
        _model_labels = ctx.ui_labels
        _enum_value_labels = ctx.enum_value_labels

        display_fields = ctx.display_fields
        # Pages publiques : exclure les champs boolean éditoriaux (published, is_draft…)
        # qui n'ont pas de sens pour les visiteurs non-authentifiés.
        if not auth_required:
            _bool_set = {fi.name for fi in ctx.editable_fields if fi.base_type == "Boolean"}
            display_fields = [f for f in display_fields if f not in _bool_set]
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

        _boolean_fields = {fi.name for fi in ctx.editable_fields if fi.base_type == "Boolean"}
        from ..dev_form_generator import _design_tokens
        _tokens = _design_tokens(design_system)
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
                auth_required=auth_required,
                boolean_fields=_boolean_fields,
                **_tokens,
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
