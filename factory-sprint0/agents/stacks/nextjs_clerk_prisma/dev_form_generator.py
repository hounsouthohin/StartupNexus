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

import json
import logging
import os

import jinja2

from .dev_naming import path_to_client_component
from .dev_model_context import ModelGenerationContext
from .dev_pages_generator import _find_create_model as _infer_create_model, _gen_page_full

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
# Filtre tojson explicite — évite la dépendance à la version Jinja2 (disponible nativement en 3.x)
_jinja_env.filters["tojson"] = lambda v: json.dumps(v, ensure_ascii=False)


def _render(template_name: str, **ctx) -> str:
    return _jinja_env.get_template(template_name).render(**ctx)


# ── Tokens sémantiques pour les templates Jinja2 ─────────────────────────────
# Les templates reçoivent des noms de classes Tailwind sémantiques (CSS variables).
# tailwind.config.js mappe primary → hsl(var(--primary)), globals.css fixe la valeur HSL.

_CARD_STYLES: dict[str, str] = {
    "elevated": "bg-card rounded-lg shadow-sm border border-border",
    "flat":     "bg-muted/30 rounded-lg",
    "bordered": "bg-card rounded-lg border-2 border-border",
}
_P_CLASSES: dict[str, str] = {
    "compact":  "p-4",
    "normal":   "p-6",
    "spacious": "p-8",
}
_TRANSITION_CLASSES: dict[str, str] = {
    "none":     "transition-none",
    "standard": "transition-colors duration-150",
    "enhanced": "transition-all duration-300 ease-out",
}


def _design_tokens(design_system: dict | None = None) -> dict:
    """Retourne les tokens Tailwind pour les templates Jinja2.
    La couleur réelle vit dans globals.css (CSS variable --primary) —
    les tokens couleur sont donc toujours sémantiques ('primary', 'primary/85'…).
    Les autres tokens (card_cls, p_cls, transition_cls, list_style) dépendent du preset.
    """
    ds = design_system or {}
    return {
        # Couleur — toujours sémantique (CSS variable)
        "primary":        "primary",
        "primary_hover":  "primary/85",
        "primary_light":  "primary/10",
        "primary_ring":   "primary",
        # Carte — style du conteneur form/detail
        "card_cls":       _CARD_STYLES.get(ds.get("card_style", "elevated"), _CARD_STYLES["elevated"]),
        # Espacement — padding page + formulaires
        "p_cls":          _P_CLASSES.get(ds.get("density", "normal"), _P_CLASSES["normal"]),
        # Animation — classe de transition Tailwind
        "transition_cls": _TRANSITION_CLASSES.get(ds.get("animation_level", "standard"), _TRANSITION_CLASSES["standard"]),
        # Layout liste publique — "table" | "card-grid"
        "list_style":     ds.get("list_style", "table"),
    }


# ── Helpers de contexte ───────────────────────────────────────────────────────

def _related_display(fk, model_contexts: dict) -> str:
    """Premier champ d'affichage du modèle lié, défaut 'id'."""
    rel_ctx: ModelGenerationContext | None = model_contexts.get(fk.related_model)
    return rel_ctx.display_fields[0] if rel_ctx and rel_ctx.display_fields else "id"


def _field_to_ctx(field, spec_enums: dict, enum_value_labels: dict | None = None) -> dict:
    """Convertit FieldInfo en dict template-friendly (ajoute enum_values et enum_labels)."""
    if field.input_type == "enum-select":
        # Priorité 1 : valeurs déjà résolues dans FieldInfo (enum Prisma ou String contraint)
        ev = list(field.allowed_values) if field.allowed_values else spec_enums.get(field.base_type, [])
        el = (enum_value_labels or {}).get(field.base_type, {})
    else:
        ev, el = [], {}
    return {
        "name":       field.name,
        "input_type": field.input_type,
        "is_optional": field.is_optional,
        "has_default": field.has_default,
        "enum_values": ev,
        "enum_labels": el,
    }


def _fk_to_ctx(fk, display: str) -> dict:
    return {
        "field_name":    fk.field_name,
        "related_model": fk.related_model,
        "related_camel": fk.related_camel,
        "related_display": display,
    }


# ── Générateurs individuels (chacun rend UN template) ────────────────────────

def _gen_list_client(page, ctx: ModelGenerationContext, spec=None, empty_state_message: str = "", design_tokens: dict | None = None, parent_relations: "list | None" = None) -> str:
    auth_required = getattr(page, "auth_required", True)
    # Pour les pages publiques, ctx.list_page_path pointe vers la liste authentifiée
    # (spec.get_list_page_for_model priorise auth=True). Utiliser page.path directement
    # pour que le lien "Voir" et has_detail pointent vers la bonne hiérarchie de routes.
    if not auth_required and getattr(page, "path", None):
        list_path = page.path
    else:
        list_path = ctx.list_page_path or f"/{ctx.kebab}s"
    fields = ctx.display_fields
    # Pages publiques : exclure les champs textarea (texte long) des cards de listing.
    # Un excerpt/résumé court suffit ; afficher content entier dans une card est contre-UX.
    if not auth_required:
        _textarea_set = {fi.name for fi in ctx.editable_fields if fi.input_type == "textarea"}
        fields = [f for f in fields if f not in _textarea_set]
        # Pages publiques : exclure les champs boolean des cards (ex: published → "true/false" = mauvaise UX)
        _boolean_set = {fi.name for fi in ctx.editable_fields if fi.base_type == "Boolean"}
        fields = [f for f in fields if f not in _boolean_set]
    # Champs boolean pour les badges visuels dans les cards (ex: published → Publié/Brouillon)
    _boolean_fields = {fi.name for fi in ctx.editable_fields if fi.base_type == "Boolean"}
    # Pages privées : promouvoir les booleans juste après le titre (position 1)
    # Le template montre display_fields[1:3] — sans promotion, un boolean en position 3+
    # ne déclenche jamais le badge (ex: Article : title/content/excerpt/published → published hors fenêtre)
    if auth_required and _boolean_fields:
        _bool_in  = [f for f in fields if f in _boolean_fields]
        _non_bool = [f for f in fields if f not in _boolean_fields]
        if _bool_in and len(_non_bool) >= 1:
            fields = [_non_bool[0]] + _bool_in + _non_bool[1:]
    _model_labels = ctx.ui_labels
    _enum_value_labels = ctx.enum_value_labels
    status_field = None
    status_labels: dict = {}
    if ctx.has_status:
        status_field = "status"
        for ef in ctx.editable_fields:
            if ef.name == "status" and ef.input_type == "enum-select":
                status_labels = _enum_value_labels.get(ef.base_type, {}) or {}
                break
    # has_detail : vrai si une page detail est déclarée dans le spec pour ce modèle
    # Active le lien "Voir" dans la colonne Actions du tableau
    _detail_path = f"{list_path}/[id]"
    _slug_detail_path = f"{list_path}/[slug]"
    _spec_pages = getattr(spec, "pages", []) or [] if spec else []
    has_detail = any(
        p.path in (_detail_path, _slug_detail_path) and p.page_type in ("detail", "detail-slug")
        for p in _spec_pages
    )
    # Pages publiques → template dédié selon list_style du preset
    # Pages auth card-grid → cards avec actions (Voir/Modifier/Supprimer)
    # Pages auth table → tableau standard
    _ls = (design_tokens or {}).get("list_style", "table")
    if not auth_required:
        template = "public_list_card_grid.tsx.j2" if _ls == "card-grid" else "public_list_client.tsx.j2"
    elif _ls == "card-grid":
        template = "list_client_card_grid.tsx.j2"
    elif ctx.has_status and status_labels:
        template = "list_client_status.tsx.j2"
    else:
        template = "list_client.tsx.j2"

    return _render(
        template,
        name=ctx.name,
        camel=ctx.camel,
        serialized_type=ctx.serialized_type,
        client_name=path_to_client_component(page.path),
        list_path=list_path,
        list_dir=list_path.lstrip("/"),
        display_fields=fields,
        field_labels={f: _model_labels.get(f, f) for f in fields},
        title_plural=ctx.title_plural,
        auth_required=auth_required,
        has_delete=auth_required,
        has_slug=ctx.has_slug,
        has_detail=has_detail,
        status_field=status_field,
        status_labels=status_labels,
        status_values=list(status_labels.keys()),
        has_search=False,
        empty_state_message=empty_state_message,
        parent_relations=parent_relations or [],
        boolean_fields=_boolean_fields,
        **(design_tokens or {}),
    )


def _gen_create_client(page, ctx: ModelGenerationContext, model_contexts: dict, spec=None, design_tokens: dict | None = None) -> str:
    list_path = ctx.list_page_path or f"/{ctx.kebab}s"
    list_dir = list_path.lstrip("/")
    _model_labels = ctx.ui_labels
    fk_fields = [_fk_to_ctx(fk, _related_display(fk, model_contexts)) for fk in ctx.fk_fields]
    editable_fields = [_field_to_ctx(f, ctx.spec_enums, ctx.enum_value_labels) for f in ctx.editable_fields]
    fk_props = ", ".join(
        f"{fk['related_camel']}Options: Serialized{fk['related_model']}[]"
        for fk in fk_fields
    )
    fk_destructure = ", ".join(f"{fk['related_camel']}Options" for fk in fk_fields)
    fk_type_imports = ", ".join(f"Serialized{fk['related_model']}" for fk in fk_fields)
    _field_labels = {f["name"]: _model_labels.get(f["name"], f["name"]) for f in editable_fields}
    for _fk in fk_fields:
        _field_labels[_fk["field_name"]] = _model_labels.get(_fk["field_name"], _fk["related_model"])
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
        field_labels=_field_labels,
        **(design_tokens or {}),
    )


def _gen_edit_client(ctx: ModelGenerationContext, model_contexts: dict, spec=None, design_tokens: dict | None = None) -> str:
    list_path = ctx.list_page_path or f"/{ctx.kebab}s"
    list_dir = list_path.lstrip("/")
    _model_labels = ctx.ui_labels
    fk_fields = [_fk_to_ctx(fk, _related_display(fk, model_contexts)) for fk in ctx.fk_fields]
    editable_fields = [_field_to_ctx(f, ctx.spec_enums, ctx.enum_value_labels) for f in ctx.editable_fields]
    _field_labels = {f["name"]: _model_labels.get(f["name"], f["name"]) for f in editable_fields}
    for _fk in fk_fields:
        _field_labels[_fk["field_name"]] = _model_labels.get(_fk["field_name"], _fk["related_model"])
    return _render(
        "edit_client.tsx.j2",
        name=ctx.name,
        serialized_type=ctx.serialized_type,
        client_name=f"{ctx.name}EditClient",
        list_path=list_path,
        list_dir=list_dir,
        fk_fields=fk_fields,
        editable_fields=editable_fields,
        field_labels=_field_labels,
        **(design_tokens or {}),
    )


def _gen_detail_client(page, ctx: ModelGenerationContext, spec=None, design_tokens: dict | None = None, textarea_fields: set | None = None) -> str:
    auth_required = getattr(page, "auth_required", True)
    page_path = getattr(page, "path", None)
    if not auth_required and page_path:
        # Pages publiques (detail-slug) : back link → parent du chemin, pas la liste authentifiée
        # Ex: "/blog/[slug]" → "/blog", "/posts/[slug]" → "/posts"
        _parts = page_path.rstrip("/").split("/")
        list_path = "/" + _parts[1] if len(_parts) >= 2 and _parts[1] else f"/{ctx.kebab}s"
    else:
        list_path = ctx.list_page_path or f"/{ctx.kebab}s"
    list_dir = list_path.lstrip("/")
    # Déduplique : display_fields d'abord, puis les éditables restants
    shown = list(dict.fromkeys(ctx.display_fields + [f.name for f in ctx.editable_fields]))

    # Sur les pages publiques : masquer les champs internes (Boolean, FK ids, slug, système).
    # Un lecteur n'a pas besoin de voir published:true, categoryId, slug, etc.
    if not auth_required:
        _model_fields = getattr(ctx.model, "fields", [])
        _bool_fields  = {f.name for f in _model_fields if f.type.rstrip("?").rstrip("[]") == "Boolean"}
        _fk_ids       = {f.name for f in _model_fields if f.name.endswith("Id") and f.name != "id"}
        _sys_fields   = {"slug", "authorId", "userId", "createdAt", "updatedAt"}
        shown = [f for f in shown if f not in _bool_fields and f not in _fk_ids and f not in _sys_fields]

    _model_labels = ctx.ui_labels
    _enum_value_labels = ctx.enum_value_labels
    # Pour les pages detail publiques, le H1 affiche le champ titre de l'item
    # (ex: item.title pour /blog/[slug]) plutôt que le nom de l'entité (ex: "Post").
    _title_field: str | None = None
    if not auth_required:
        for _candidate in ("title", "name", "heading", "label", "subject"):
            if _candidate in shown:
                _title_field = _candidate
                break
        if _title_field is None and shown:
            _title_field = shown[0]
    value_labels: dict = {}
    for ef in ctx.editable_fields:
        if ef.input_type == "enum-select" and ef.name in shown:
            labels = _enum_value_labels.get(ef.base_type, {}) or {}
            if labels:
                value_labels[ef.name] = labels
    boolean_fields = {fi.name for fi in ctx.editable_fields if fi.base_type == "Boolean"}
    return _render(
        "detail_client.tsx.j2",
        name=ctx.name,
        serialized_type=ctx.serialized_type,
        client_name=path_to_client_component(page.path),
        list_path=list_path,
        list_dir=list_dir,
        display_fields=shown,
        field_labels={f: _model_labels.get(f, f) for f in shown},
        value_labels=value_labels,
        auth_required=auth_required,
        has_delete=auth_required,
        title_field=_title_field,
        textarea_fields=textarea_fields or set(),
        boolean_fields=boolean_fields,
        **(design_tokens or {}),
    )


# ── Point d'entrée ────────────────────────────────────────────────────────────

def generate_all_page_clients(
    spec,
    model_contexts: dict,
    project_workdir: str,
    enriched_spec=None,
    design_system: dict | None = None,
) -> dict[str, str]:
    """
    Génère déterministiquement les page-client.tsx pour toutes les pages CRUD.
    Retourne {rel_path: content} pour intégration dans template_written.
    design_system: dict depuis ProjectSpec (primary_color, etc.) — injecté dans les templates Jinja2.
    """
    tokens = _design_tokens(design_system)
    written: dict[str, str] = {}
    pages = getattr(spec, "pages", []) or []

    # Extraction des empty_states depuis ux_hints (produits par le semantic annotator)
    _empty_states: dict[str, str] = {}
    if enriched_spec is not None:
        try:
            _ux = getattr(enriched_spec, "ux_hints", None)
            if _ux:
                _empty_states = dict(getattr(_ux, "empty_states", {}) or {})
        except Exception:
            pass

    # Champs "textarea" depuis field_annotations — rendu prose dans detail_client.tsx.j2.
    # field_annotations = {field_name: FieldAnnotation(semantic_type="textarea")}
    # On croise avec les champs réels de chaque modèle pour construire {model_name: {field_name}}.
    _textarea_field_names: set[str] = set()
    if enriched_spec is not None:
        try:
            _fa = getattr(enriched_spec, "field_annotations", {}) or {}
            for _fa_name, _fa_val in _fa.items():
                _stype = getattr(_fa_val, "semantic_type", "") or str(_fa_val)
                if _stype == "textarea":
                    _textarea_field_names.add(_fa_name)
        except Exception:
            pass
    _textarea_fields: dict[str, set] = {}
    for _m_name, _m_ctx in model_contexts.items():
        _m_fields = {f.name for f in getattr(_m_ctx.model, "fields", [])}
        _overlap = _m_fields & _textarea_field_names
        if _overlap:
            _textarea_fields[_m_name] = _overlap

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

        # form_gen génère TOUJOURS le page-client.tsx de base pour les pages detail.
        # Si module_detail_with_children produit quelque chose, il écrase ensuite
        # (ordre garanti : form_gen → feature_modules). Si le module retourne {}
        # (M2M sans FK direct, schéma blog…), le fichier de base est présent.

        page_path_clean = page.path.strip("/")

        try:
            if page_type == "list":
                rel = f"app/{page_path_clean}/page-client.tsx" if page_path_clean else "app/page-client.tsx"
                _empty_msg = _empty_states.get(page.path, "")
                _parent_rels = [
                    {
                        "related_camel": fk.related_camel,
                        "display_field": _related_display(fk, model_contexts),
                        "label": ctx.ui_labels.get(fk.field_name, fk.related_model),
                    }
                    for fk in ctx.fk_fields
                ]
                content = _gen_list_client(page, ctx, spec=spec, empty_state_message=_empty_msg, design_tokens=tokens, parent_relations=_parent_rels)
            elif page_type == "create":
                rel = f"app/{page_path_clean}/page-client.tsx"
                content = _gen_create_client(page, ctx, model_contexts, spec=spec, design_tokens=tokens)
            elif page_type in ("detail", "detail-slug"):
                rel = f"app/{page_path_clean}/page-client.tsx"
                content = _gen_detail_client(page, ctx, spec=spec, design_tokens=tokens,
                                             textarea_fields=_textarea_fields.get(ctx.name))
            elif page_type == "edit":
                # page-client.tsx déterministe pour la page d'édition.
                # Le page.tsx est généré par generate_edit_page_stubs() dans dev_pages_generator.py.
                # Sans ce cas, le guard A3 bloque le run (page.tsx importe ./page-client absent).
                rel = f"app/{page_path_clean}/page-client.tsx"
                content = _gen_edit_client(ctx, model_contexts, spec=spec, design_tokens=tokens)
            else:
                continue
        except Exception as _gen_err:
            logger.error(
                "[form_gen] erreur génération '%s' (%s) : %s",
                page_path_clean, page_type, _gen_err,
                exc_info=True,
            )
            continue

        abs_path = os.path.join(project_workdir, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        written[rel] = content
        logger.info("[form_gen] ✓ %s (model=%s type=%s)", rel, model_name, page_type)

    # Edit pages — pour chaque modèle CRUD complet
    # Skip si une page edit est déjà déclarée dans spec.pages pour ce modèle :
    # loop 1 (spec.pages) l'a déjà traitée après normalisation [id]→[slug] dans _normalize_pages.
    _models_with_explicit_edit = {
        getattr(p, "model", None)
        for p in spec.pages
        if getattr(p, "page_type", "") == "edit" and getattr(p, "model", None)
    }
    for model in spec.models:
        if model.name not in crud_models:
            continue
        if model.name in _models_with_explicit_edit:
            continue
        ctx = model_contexts.get(model.name)
        if ctx is None:
            continue
        list_path = ctx.list_page_path
        if not list_path:
            continue

        try:
            route = list_path.lstrip("/")
            slug_or_id = "[slug]" if ctx.has_slug else "[id]"
            rel = f"app/{route}/{slug_or_id}/edit/page-client.tsx"
            content = _gen_edit_client(ctx, model_contexts, spec=spec, design_tokens=tokens)
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


def generate_parent_detail_pages(
    spec,
    model_contexts: dict,
    project_workdir: str,
    design_system: dict | None = None,
) -> dict[str, str]:
    """
    Auto-génère les pages détail pour les modèles parents qui ont des enfants FK
    mais aucune page détail déclarée dans le spec.

    Ex : Task a des Comments (taskId FK) mais /tasks/[id] absent du spec
    → génère app/tasks/[id]/page.tsx + page-client.tsx déterministes.

    Sans ces pages, createComment redirige vers /tasks/${validated.taskId}
    qui n'existe pas → 404 immédiat après création d'un enfant CROSS_ENTITY.

    Retourne {rel_path: content} pour intégration dans template_written.
    """
    from types import SimpleNamespace

    tokens = _design_tokens(design_system)
    written: dict[str, str] = {}

    # Modèles parents = modèles référencés comme FK par d'autres modèles
    fk_parent_names: set[str] = set()
    for ctx in model_contexts.values():
        for fk in ctx.fk_fields:
            fk_parent_names.add(fk.related_model)

    if not fk_parent_names:
        return written

    # Modèles déjà couverts par une page détail dans le spec
    models_with_detail: set[str] = set()
    for page in getattr(spec, "pages", []) or []:
        if getattr(page, "page_type", "") in ("detail", "detail-slug"):
            model_name = getattr(page, "model", None)
            if model_name:
                models_with_detail.add(model_name)

    for parent_name in fk_parent_names:
        if parent_name in models_with_detail:
            continue  # Déjà couvert dans le spec

        parent_ctx = model_contexts.get(parent_name)
        if parent_ctx is None:
            continue

        list_path = parent_ctx.list_page_path
        if not list_path:
            continue  # Pas de page liste → pas de détail auto-généré

        if parent_ctx.has_slug:
            logger.info("[form_gen] parent detail ignoré pour '%s' : has_slug=True → conflit [id] vs [slug]", parent_name)
            continue

        detail_path = f"{list_path}/[id]"
        page_path_clean = detail_path.strip("/")

        # Vérifier que les fichiers n'existent pas déjà sur disque
        page_rel = f"app/{page_path_clean}/page.tsx"
        client_rel = f"app/{page_path_clean}/page-client.tsx"
        page_abs = os.path.join(project_workdir, page_rel.replace("/", os.sep))
        client_abs = os.path.join(project_workdir, client_rel.replace("/", os.sep))
        if os.path.exists(page_abs) and os.path.exists(client_abs):
            logger.info("[form_gen] parent detail déjà présent : %s", detail_path)
            continue

        # Modèle Prisma réel
        parent_model = None
        if hasattr(spec, "get_model_by_name"):
            parent_model = spec.get_model_by_name(parent_name)
        if parent_model is None:
            parent_model = next(
                (m for m in (getattr(spec, "models", []) or []) if m.name == parent_name),
                None,
            )
        if parent_model is None:
            logger.warning("[form_gen] generate_parent_detail_pages: modèle '%s' introuvable", parent_name)
            continue

        # Page synthétique (ne modifie pas spec.pages)
        synthetic_page = SimpleNamespace(
            path=detail_path,
            page_type="detail",
            auth_required=True,
            model=parent_name,
        )

        try:
            os.makedirs(os.path.dirname(page_abs), exist_ok=True)

            if not os.path.exists(page_abs):
                # Passer parent_ctx pour que _gen_page_full utilise ctx.has_relations
                # (détecte les relations inverses `tasks Task[]` sans @relation explicite)
                page_content = _gen_page_full(synthetic_page, parent_model, spec=spec, ctx=parent_ctx)
                with open(page_abs, "w", encoding="utf-8") as f:
                    f.write(page_content)
                written[page_rel] = page_content

            if not os.path.exists(client_abs):
                client_content = _gen_detail_client(synthetic_page, parent_ctx, spec=spec, design_tokens=tokens)
                with open(client_abs, "w", encoding="utf-8") as f:
                    f.write(client_content)
                written[client_rel] = client_content

            logger.info(
                "[form_gen] ✓ parent detail auto-généré : %s (model=%s)",
                detail_path, parent_name,
            )

        except Exception as _err:
            logger.error(
                "[form_gen] erreur génération parent detail '%s' : %s",
                detail_path, _err,
                exc_info=True,
            )

    if written:
        logger.info("[form_gen] %d fichier(s) parent detail auto-générés", len(written))
    return written
