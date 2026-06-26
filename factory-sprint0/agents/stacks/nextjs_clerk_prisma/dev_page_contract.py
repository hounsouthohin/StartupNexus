"""
dev_page_contract.py
────────────────────
Niveau 1 — Page Contract Calculator.

Pour chaque page avec modèle dans la spec, calcule un contrat complet déterministe :
  - service_method         : méthode exacte à appeler depuis le service
  - nav_context            : "public" | "private"
  - list_path              : chemin liste correct (public vs privé selon auth_required)
  - detail_path            : chemin détail avec [slug] ou [id] selon le modèle
  - back_link              : chemin retour depuis une page détail / edit
  - slug_field             : "slug" si le modèle utilise slug, None sinon
  - display_fields_ordered : champs display avec Boolean promus en position 1
  - badge_fields           : champs Boolean → à rendre comme badges colorés
  - return_fields          : champs retournés par service_method (scalaires + FK non-array)

Ce contrat élimine toute la classe de bugs de navigation et de données :
  - Lien item.id au lieu de item.slug → slug_field explicite
  - getPublished() inexistant          → service_method calculé depuis les flags ctx
  - category?.name vide               → return_fields liste les FK incluses
  - Boolean badge hors fenêtre        → display_fields_ordered avec promotion intégrée

Utilisé par executor_node (dev_graph.py) : injecté dans _file_brief par fichier.
NE PAS confondre avec _page_contracts (planner.py) qui couvre uniquement les pages
[INTERACTIVE] et injecte des hints service call dans context_hint du plan.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


# ── Résolution méthode service ────────────────────────────────────────────────

def _resolve_service_method(page_type: str, auth_required: bool, ctx) -> str:
    """Méthode service exacte selon le type de page et les flags du ModelGenerationContext."""
    camel = ctx.camel

    if page_type == "list":
        if not auth_required:
            return f"{camel}Service.getPublicAll"
        elif ctx.has_relations:
            return f"{camel}Service.getAllWithRelations"
        else:
            return f"{camel}Service.getAll"

    elif page_type in ("detail", "detail-slug"):
        if not auth_required:
            if ctx.has_slug:
                return f"{camel}Service.getBySlug"
            elif any(getattr(r, "is_array", False) for r in ctx.relation_fields):
                return f"{camel}Service.getPublicByIdWithRelations"
            else:
                return f"{camel}Service.getPublicById"
        else:
            # Slug prend la priorité sur relations : la route est [slug], pas [id]
            if ctx.has_slug and ctx.has_relations:
                return f"{camel}Service.getBySlugWithRelations"
            elif ctx.has_slug:
                return f"{camel}Service.getBySlug"
            elif ctx.has_relations:
                return f"{camel}Service.getByIdWithRelations"
            else:
                return f"{camel}Service.getById"

    elif page_type == "edit":
        if ctx.has_slug:
            return f"{camel}Service.getBySlug"
        return f"{camel}Service.getById"

    elif page_type == "create":
        return f"{camel}Service.create"

    return ""


# ── Résolution chemins de navigation ─────────────────────────────────────────

def _find_list_path(model_name: str, spec_pages, auth_required: bool, ctx) -> str | None:
    """Chemin de la liste pour ce modèle dans le contexte auth donné."""
    if not auth_required:
        for p in spec_pages:
            if (getattr(p, "model", None) == model_name
                    and getattr(p, "page_type", None) == "list"
                    and not getattr(p, "auth_required", True)):
                return p.path
        return None
    return ctx.list_page_path


def _find_detail_path(model_name: str, spec_pages, auth_required: bool, ctx) -> str | None:
    """Chemin détail pour ce modèle dans le contexte auth donné."""
    for p in spec_pages:
        if (getattr(p, "model", None) == model_name
                and getattr(p, "page_type", None) in ("detail", "detail-slug")
                and bool(getattr(p, "auth_required", True)) == auth_required):
            return p.path
    # Fallback : dériver depuis list_path + paramètre slug ou id
    slug_or_id = "[slug]" if ctx.has_slug else "[id]"
    list_path = _find_list_path(model_name, spec_pages, auth_required, ctx)
    if list_path:
        return f"{list_path}/{slug_or_id}"
    return None


# ── Résolution display_fields ordonnés ───────────────────────────────────────

def _ordered_display_fields(ctx, auth_required: bool) -> list[str]:
    """
    display_fields avec :
    - Pages publiques : textarea et boolean exclus (mauvaise UX en listing card)
    - Pages privées  : boolean promus en position 1 (garantit entrée dans display_fields[1:3])
    """
    fields = list(ctx.display_fields)
    _boolean_names = {fi.name for fi in ctx.editable_fields if fi.base_type == "Boolean"}

    if not auth_required:
        _textarea_names = {fi.name for fi in ctx.editable_fields if fi.input_type == "textarea"}
        fields = [f for f in fields if f not in _textarea_names and f not in _boolean_names]
    else:
        if _boolean_names:
            _bool_in  = [f for f in fields if f in _boolean_names]
            _non_bool = [f for f in fields if f not in _boolean_names]
            if _bool_in and len(_non_bool) >= 1:
                fields = [_non_bool[0]] + _bool_in + _non_bool[1:]

    return fields


# ── Calculateur principal ─────────────────────────────────────────────────────

def compute_page_contracts(spec_obj, model_contexts: dict) -> dict[str, dict]:
    """
    Calcule les contrats de page pour toutes les pages avec modèle.
    Retourne dict[page_path → contract_dict].
    Appeler après build_all_contexts() dans run_dev_agent().
    """
    if not spec_obj or not model_contexts:
        return {}

    contracts: dict[str, dict] = {}
    spec_pages = getattr(spec_obj, "pages", []) or []

    for page in spec_pages:
        model_name = getattr(page, "model", None)
        if not model_name:
            continue
        ctx = model_contexts.get(model_name)
        if not ctx:
            continue

        page_type     = getattr(page, "page_type", "custom") or "custom"
        auth_required = bool(getattr(page, "auth_required", True))

        service_method = _resolve_service_method(page_type, auth_required, ctx)
        list_path      = _find_list_path(model_name, spec_pages, auth_required, ctx)
        detail_path    = _find_detail_path(model_name, spec_pages, auth_required, ctx)
        back_link      = list_path if page_type in ("detail", "detail-slug", "edit") else None

        badge_fields = (
            [fi.name for fi in ctx.editable_fields if fi.base_type == "Boolean"]
            if auth_required else []
        )

        # return_fields : scalaires display + relations FK non-array (ex: category.name)
        return_fields = list(ctx.display_fields)
        for r in ctx.relation_fields:
            if not getattr(r, "is_array", True):
                rel_ctx = model_contexts.get(getattr(r, "related_model", ""))
                if rel_ctx and rel_ctx.display_fields:
                    # Préférer un champ non-id comme label (name, title, etc.)
                    _non_id = [f for f in rel_ctx.display_fields if f != "id"]
                    disp = _non_id[0] if _non_id else rel_ctx.display_fields[0]
                else:
                    disp = "name"
                return_fields.append(f"{r.name}.{disp}")

        contracts[page.path] = {
            "service_method":         service_method,
            "nav_context":            "private" if auth_required else "public",
            "list_path":              list_path,
            "detail_path":            detail_path,
            "back_link":              back_link,
            "slug_field":             "slug" if ctx.has_slug else None,
            "slug_or_id":             "[slug]" if ctx.has_slug else "[id]",
            "display_fields_ordered": _ordered_display_fields(ctx, auth_required),
            "badge_fields":           badge_fields,
            "return_fields":          return_fields,
            "model_name":             model_name,
            "serialized_type":        ctx.serialized_type,
        }

    logger.info("[page_contract] %d contrats calculés", len(contracts))
    return contracts


# ── Formatage pour injection executor_node ────────────────────────────────────

def format_own_contract(contract: dict) -> str:
    """
    Contrat de la page elle-même (page modèle en fallback LLM).
    Injecté dans _file_brief quand _rt correspond à une page modèle.
    """
    lines = ["\nCONTRAT PAGE (déterministe — priorité absolue) :"]

    svc = contract.get("service_method", "")
    if svc:
        auth = contract.get("nav_context") == "private"
        arg  = "(userId)" if auth else "()"
        lines.append(f"  service_method : {svc}{arg}")

    detail = contract.get("detail_path")
    if detail:
        lines.append(f"  detail_path    : {detail}")

    slug = contract.get("slug_field")
    if slug:
        lines.append(
            f"  ⚠ slug_field   : utiliser item.{slug} dans les <Link> — JAMAIS item.id"
            f"  (la route utilise [{slug}], pas [id])"
        )

    back = contract.get("back_link")
    if back:
        lines.append(f"  back_link      : {back}")

    badges = contract.get("badge_fields", [])
    if badges:
        lines.append(
            f"  badge_fields   : {badges} → badges colorés"
            " (ex: published → vert=Publié / gris=Brouillon, JAMAIS texte brut 'true'/'false')"
        )

    return "\n".join(lines)


def format_nav_contracts(contracts: dict[str, dict], nav_context: str) -> str:
    """
    Pour une page custom (home, dashboard), injecte la référence de navigation
    de toutes les entités dans le bon contexte (public / private).
    Le LLM s'en sert pour construire les bons <Link> et appeler les bons services.
    """
    # Garder uniquement les contrats de pages liste du bon nav_context
    relevant = {
        path: c for path, c in contracts.items()
        if c.get("nav_context") == nav_context
    }
    if not relevant:
        return ""

    lines = [f"\nREFERENCE ENTITES ({nav_context.upper()}) — navigation et services :"]
    seen_models: set[str] = set()
    for path, c in list(relevant.items())[:8]:
        model = c.get("model_name", "")
        if model in seen_models:
            continue
        seen_models.add(model)
        svc    = c.get("service_method", "")
        detail = c.get("detail_path", "?")
        slug   = c.get("slug_field")
        auth   = nav_context == "private"
        arg    = "(userId)" if auth else "()"
        slug_note = f" | <Link> utilise item.{slug}" if slug else " | <Link> utilise item.id"
        lines.append(f"  [{model}] {svc}{arg} → détail: {detail}{slug_note}")

    return "\n".join(lines)
