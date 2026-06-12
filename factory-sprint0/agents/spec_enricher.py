"""
agents/spec_enricher.py
────────────────────────
Nœud DÉTERMINISTE — enrichit pages_detail avec des data_fetches calculés depuis
le service map et les pages de la spec. Aucun appel LLM.

Problème résolu : pages_detail_node (LLM) génère souvent des data_fetches incorrects
(méthodes inexistantes, signatures erronnées). Le SpecEnricher calcule les data_fetches
exacts depuis le service map qui est la SOURCE DE VÉRITÉ des méthodes disponibles.

Stratégie :
1. Pour les pages custom (page_type="custom") :
   - auth=True, chemin contient "dashboard" → getAll(userId) pour tous les modèles auth
   - auth=True, chemin comme "/my-{model}" → getAll(userId) pour ce modèle
   - auth=False → getPublicAll() pour les modèles avec pages publiques
   - "/" (home) → [] (page statique)
2. Override les data_fetches LLM uniquement si la version calculée est plus précise
   (non vide quand LLM a retourné vide, ou LLM a utilisé une méthode inexistante).
3. Préserve les data_fetches LLM quand ils semblent corrects (méthodes reconnues).

Exécution : APRÈS pages_detail_node, AVANT planner_node.
"""
from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# Méthodes valides connues du service map (doit rester synchrone avec service_modules/)
_VALID_SERVICE_METHODS = frozenset({
    "getAll", "getById", "create", "update", "delete",
    "getAllWithRelations", "getByIdWithRelations",
    "getPublished", "getPublicAll", "getPublicById",
    "getBySlug", "getBySlugOwned", "getBySlugWithRelations",
    "getPublicByIdWithRelations",
})


def _camel(name: str) -> str:
    """PascalCase → camelCase."""
    return name[0].lower() + name[1:] if name else name


def _kebab(name: str) -> str:
    """PascalCase → kebab-case."""
    return re.sub(r"(?<!^)(?=[A-Z])", "-", name).lower()


def _has_relations(model_str: str) -> bool:
    return "@relation" in model_str


def _has_public_model(model_name: str, pages: list[dict]) -> bool:
    """True si ce modèle a au moins une page publique."""
    return any(
        not p.get("auth", True) and p.get("model") == model_name
        for p in pages
        if isinstance(p, dict)
    )


def _detect_model_from_path(path: str, model_names: list[str]) -> str | None:
    """Tente de déduire un modèle depuis un chemin de page."""
    path_lower = path.lower()
    for name in model_names:
        if _kebab(name) in path_lower or name.lower() in path_lower:
            return name
    return None


def _is_valid_data_fetches(data_fetches: list) -> bool:
    """Vérifie que les data_fetches LLM utilisent des méthodes connues."""
    if not data_fetches:
        return True  # vide = neutre, pas invalide
    for fetch in data_fetches:
        if not isinstance(fetch, dict):
            return False
        service_call = fetch.get("service", "")
        # Extrait le nom de méthode depuis "xxxService.method(args)"
        match = re.search(r"\.(\w+)\(", service_call)
        if match and match.group(1) not in _VALID_SERVICE_METHODS:
            # Méthode inconnue → data_fetches LLM invalides
            return False
    return True


def _compute_data_fetches(
    page_path: str,
    page_auth: bool,
    page_type: str,
    model_names: list[str],
    pages: list[dict],
    brief_models: list[str],
) -> list[dict]:
    """
    Calcule les data_fetches pour une page custom.

    Règles (par ordre de priorité) :
    1. "/" → [] (home statique)
    2. Chemin dashboard → getAll pour tous les modèles auth
    3. Chemin type "/my-{model}" ou "/{model}-management" → getAll pour ce modèle
    4. Public page avec modèle public → getPublicAll
    5. Fallback auth → getAll pour tous les modèles
    6. Fallback public → []
    """
    if page_path == "/":
        return []

    path_lower = page_path.lower()

    # Dashboard → getAll pour tous les modèles auth (en excluant commentaires/enfants)
    if "dashboard" in path_lower or "hub" in path_lower:
        if page_auth:
            fetches = []
            for model_str in brief_models:
                name = model_str.split()[0] if model_str.split() else None
                if not name:
                    continue
                svc = _camel(name)
                has_rels = _has_relations(model_str)
                method = "getAllWithRelations" if has_rels else "getAll"
                fetches.append({
                    "service": f"{svc}Service.{method}(userId)",
                    "as": f"{svc}s",
                })
            return fetches

    # Chemin spécifique à un modèle
    model_match = _detect_model_from_path(page_path, model_names)
    if model_match:
        svc = _camel(model_match)
        has_rels = any(model_match in ms and _has_relations(ms) for ms in brief_models)
        if page_auth:
            method = "getAllWithRelations" if has_rels else "getAll"
            return [{"service": f"{svc}Service.{method}(userId)", "as": f"{svc}s"}]
        elif _has_public_model(model_match, pages):
            return [{"service": f"{svc}Service.getPublicAll()", "as": f"{svc}s"}]

    # Fallback auth → getAll pour le premier modèle
    if page_auth and model_names:
        svc = _camel(model_names[0])
        return [{"service": f"{svc}Service.getAll(userId)", "as": f"{svc}s"}]

    return []


def spec_enricher_node(state: dict) -> dict:
    """
    Enrichit pages_detail avec des data_fetches déterministes.

    Skip si brief.pages_detail est vide.
    Fail-safe : toute exception est loggée, le state n'est pas modifié.
    """
    brief = state.get("brief", {})
    pages_detail: dict = brief.get("pages_detail", {})

    if not pages_detail:
        logger.debug("[spec_enricher] pages_detail vide → skip")
        return {}

    brief_models: list[str] = brief.get("models", [])
    pages: list[dict] = [p for p in brief.get("pages", []) if isinstance(p, dict)]

    model_names = [m.split()[0] for m in brief_models if m.split()]

    # Construire un index {path: {auth, page_type, model}} depuis les pages
    page_index: dict[str, dict] = {}
    for p in pages:
        path = p.get("path", "")
        if path:
            page_index[path] = {
                "auth": bool(p.get("auth", True)),
                "page_type": p.get("page_type", "custom"),
                "model": p.get("model"),
            }

    updated_detail: dict = {}
    overridden = 0

    for path, detail in pages_detail.items():
        if not isinstance(detail, dict):
            updated_detail[path] = detail
            continue

        page_info = page_index.get(path, {"auth": True, "page_type": "custom"})
        page_type = page_info.get("page_type", "custom")

        # Seules les pages custom reçoivent des data_fetches computés
        # Les pages list/create/detail/edit sont déterministes (templates)
        if page_type != "custom":
            updated_detail[path] = detail
            continue

        existing_fetches: list = detail.get("data_fetches", [])

        # Si le LLM a fourni des data_fetches valides → les conserver
        if existing_fetches and _is_valid_data_fetches(existing_fetches):
            updated_detail[path] = detail
            continue

        # Calcul déterministe
        try:
            computed = _compute_data_fetches(
                page_path=path,
                page_auth=page_info.get("auth", True),
                page_type=page_type,
                model_names=model_names,
                pages=pages,
                brief_models=brief_models,
            )
        except Exception as exc:
            logger.warning("[spec_enricher] calcul échoué pour '%s' : %s", path, exc)
            updated_detail[path] = detail
            continue

        if computed != existing_fetches:
            overridden += 1
            logger.info(
                "[spec_enricher] '%s' : data_fetches %s → %s",
                path,
                [f.get("service", "?") for f in existing_fetches],
                [f.get("service", "?") for f in computed],
            )
            updated_detail[path] = {**detail, "data_fetches": computed}
        else:
            updated_detail[path] = detail

    # ── Injection design preset (déterministe, 0 token) ────────────────────────
    design_injected = False
    try:
        from agents.core.design_resolver import resolve_preset
        preset = resolve_preset(brief.get("description", ""))
        existing_ds = brief.get("design_system", {}) or {}
        brand_name = existing_ds.get("brand_name", "")
        brief = {**brief, "design_system": {**preset, "brand_name": brand_name}}
        design_injected = True
    except Exception as _dr_err:
        logger.warning("[spec_enricher] design_resolver échoué : %s", _dr_err)

    if overridden == 0 and not design_injected:
        logger.debug("[spec_enricher] aucune modification → skip")
        return {}

    updated_brief = {**brief, "pages_detail": updated_detail} if overridden > 0 else brief
    logger.info(
        "[spec_enricher] ✓ %d data_fetches corrigé(s) | design=%s",
        overridden,
        brief.get("design_system", {}).get("preset_name", "?"),
    )
    return {"brief": updated_brief}
