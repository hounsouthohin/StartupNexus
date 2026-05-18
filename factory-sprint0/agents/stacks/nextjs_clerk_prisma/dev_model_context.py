"""
agents/stacks/nextjs_clerk_prisma/dev_model_context.py
───────────────────────────────────────────────────────
ModelGenerationContext — contexte précalculé par modèle Prisma.

Problème résolu :
  La logique de détection de champs (relation vs scalaire vs enum vs FK vs DateTime)
  était dupliquée en 4 endroits avec des angles morts différents :
    - dev_types_generator._is_relation_field        (avec enums)
    - dev_zod_generator._is_relation_field          (avec enums)
    - dev_service_generator._relation_fields        (SANS enums — aveugle aux enums Prisma)
    - dev_pages_generator._form_fields / _fk_fields (SANS enums — exclut les champs enum)

Ce module est la SOURCE UNIQUE de vérité pour ces calculs.
Chaque générateur reçoit un ModelGenerationContext déjà calculé.

Usage :
    from .dev_model_context import build_all_contexts

    contexts = build_all_contexts(spec_obj)
    for model in spec_obj.models:
        ctx = contexts[model.name]
        # Accès direct : ctx.editable_fields, ctx.fk_fields, ctx.has_status, ...
"""
from __future__ import annotations

import logging
import re as _re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Types scalaires Prisma reconnus — tout ce qui n'est pas ici ET commence par une
# majuscule est soit un modèle (relation) soit un enum.
_PRISMA_SCALAR_TYPES: frozenset[str] = frozenset([
    "String", "Int", "Float", "Decimal", "Boolean",
    "DateTime", "Json", "Bytes", "BigInt",
])

# Noms de champs qui doivent être rendus comme <textarea> dans les formulaires.
_TEXTAREA_NAMES: frozenset[str] = frozenset([
    "content", "description", "body", "notes",
    "message", "text", "bio", "about", "details",
])


# ── Sous-types ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class FieldInfo:
    """Champ scalaire mutable d'un modèle (non-auto, non-relation, non-owner, non-FK)."""
    name: str
    prisma_type: str    # ex: "String?", "DateTime", "Int"
    base_type: str      # ex: "String" (sans ? ni [])
    is_optional: bool   # type se termine par ?
    has_default: bool   # @default(...) non-auto → optionnel à la création
    input_type: str     # "text" | "number" | "textarea" | "checkbox" | "datetime-local" | "enum-select"
    attributes: str     # attributs Prisma bruts (pour diagnostic)


@dataclass(frozen=True)
class FKFieldInfo:
    """Champ de clé étrangère (xxxId) résolu vers un modèle connu de la spec."""
    field_name: str      # "categoryId"
    related_model: str   # "RecipeCategory"
    related_camel: str   # "recipeCategory"
    related_kebab: str   # "recipe-category"


@dataclass(frozen=True)
class DatetimeFieldInfo:
    """Champ DateTime — nécessaire pour _serialize() dans les services."""
    name: str
    is_nullable: bool


@dataclass(frozen=True)
class RelationFieldInfo:
    """Champ @relation — inclus dans include:{} de getAllWithRelations()."""
    name: str
    is_array: bool


# ── Contexte principal ────────────────────────────────────────────────────────

@dataclass
class ModelGenerationContext:
    """
    Contexte précalculé pour UN modèle Prisma.

    Produit par build_model_context(model, spec) — appelé UNE SEULE FOIS par modèle
    dans dev_graph.py, avant l'appel de tous les générateurs.

    Chaque générateur accède à ce contexte au lieu de recalculer les mêmes informations
    avec des angles morts différents.
    """

    # ── Identité ─────────────────────────────────────────────────────────────
    model: object           # PrismaModel (non-typé pour éviter l'import circulaire)
    name: str               # "Recipe"
    camel: str              # "recipe"
    kebab: str              # "recipe"
    owner: str              # "userId" — champ owner résolu via model.resolved_owner()

    # ── Types générés ────────────────────────────────────────────────────────
    serialized_type: str    # "SerializedRecipe"
    spec_enums: dict        # spec.enums — distingue enum Prisma vs modèle (relation)

    # ── Champs catégorisés (calculés une seule fois) ──────────────────────────
    # editable_fields : champs mutables dans les formulaires.
    #   Exclus : auto (id, createdAt, updatedAt), owner, @relation, tableaux, FK (dans fk_fields).
    editable_fields: list[FieldInfo]

    # fk_fields : champs xxxId résolus vers un modèle connu.
    #   Rendus comme <select> dans les formulaires create.
    fk_fields: list[FKFieldInfo]

    # datetime_fields : champs DateTime pour générer _serialize() dans le service.
    datetime_fields: list[DatetimeFieldInfo]

    # relation_fields : champs @relation pour include:{} de getAllWithRelations().
    relation_fields: list[RelationFieldInfo]

    # display_fields : jusqu'à 4 champs scalaires affichables dans les listes UI.
    display_fields: list[str]

    # ── Feature flags ─────────────────────────────────────────────────────────
    has_slug: bool       # modèle a un champ "slug" → active getBySlug() et detail-slug pages
    has_status: bool     # modèle a un champ "status" → badge coloré + getPublished()
    has_relations: bool  # au moins un @relation → active getAllWithRelations()

    # ── Contexte pages (nécessite spec) ───────────────────────────────────────
    # has_public_pages : au moins une page auth=False avec model=ce modèle.
    #   CRITIQUE : conditionne la génération de getPublicAll() et getPublicById().
    #   Sans ce flag, ces méthodes exposent tous les enregistrements sans filtre owner.
    has_public_pages: bool
    has_public_list: bool    # page list publique (type="list", auth=False)
    has_public_detail: bool  # page detail publique (type="detail"|"detail-slug", auth=False)

    # list_page_path : chemin de la page liste principale pour ce modèle.
    #   Utilisé par les Server Actions (redirect post-create/delete).
    list_page_path: str


# ── Helpers de calcul ─────────────────────────────────────────────────────────

def _is_auto_field(name: str, attributes: str) -> bool:
    """True si le champ est géré automatiquement par Prisma (jamais dans les Input types)."""
    if name.lower() in ("id", "createdat", "updatedat", "deletedat"):
        return True
    attrs_lower = (attributes or "").lower()
    return (
        "@id" in attrs_lower
        or "@default(now())" in attrs_lower
        or "@updatedat" in attrs_lower.replace(" ", "")
    )


def _has_non_auto_default(attributes: str) -> bool:
    """True si le champ a @default(...) non-auto → optionnel à la création."""
    if not attributes:
        return False
    attrs = attributes.lower()
    if any(tok in attrs for tok in ("@default(now())", "@default(uuid())", "@default(cuid())")):
        return False
    return "@default(" in attrs


def _is_relation(field_type: str, attributes: str, spec_enums: dict) -> bool:
    """
    Détecte si un champ est une relation Prisma.

    Règle : relation si @relation explicite OU type commence par une majuscule
    ET n'est pas un type scalaire connu ET n'est pas un enum déclaré dans spec.
    C'est la logique canonique — remplace les 4 copies disparates.
    """
    if "@relation" in (attributes or ""):
        return True
    base = field_type.rstrip("?").rstrip("[]")
    if base in _PRISMA_SCALAR_TYPES:
        return False
    if spec_enums and base in spec_enums:
        return False
    return bool(base) and base[0].isupper()


def _detect_input_type(field_name: str, base_type: str, spec_enums: dict) -> str:
    """Détermine le type d'input HTML pour un champ scalaire."""
    if base_type in spec_enums:
        return "enum-select"
    if base_type == "Boolean":
        return "checkbox"
    if base_type in ("Int", "Float", "Decimal"):
        return "number"
    if base_type == "DateTime":
        return "datetime-local"
    if field_name.lower() in _TEXTAREA_NAMES:
        return "textarea"
    return "text"


def _pascal_to_camel(name: str) -> str:
    return name[0].lower() + name[1:] if name else name


def _pascal_to_kebab(name: str) -> str:
    return _re.sub(r"(?<!^)(?=[A-Z])", "-", name).lower()


def _resolve_fk_fields(model, model_names: set[str], owner: str) -> list[FKFieldInfo]:
    """Résout les champs FK avec fallback suffix pour les noms de modèles composés."""
    result: list[FKFieldInfo] = []
    for f in model.fields:
        if f.name in {owner, "id"} or "@relation" in (f.attributes or ""):
            continue
        if not f.name.endswith("Id"):
            continue
        base = f.name[:-2]                                # "categoryId" → "category"
        related = base[0].upper() + base[1:]              # → "Category"
        if related not in model_names:
            # Fallback : "Category" absent → cherche "RecipeCategory"
            matches = [mn for mn in model_names if mn.endswith(related)]
            if matches:
                related = matches[0]
        if related in model_names:
            result.append(FKFieldInfo(
                field_name=f.name,
                related_model=related,
                related_camel=_pascal_to_camel(related),
                related_kebab=_pascal_to_kebab(related),
            ))
    return result


def _resolve_display_fields(model, owner: str, model_names: "frozenset[str] | None" = None) -> list[str]:
    """Jusqu'à 4 champs scalaires affichables (non-système, non-relation, non-FK, non-slug)."""
    excluded = {"id", "createdAt", "updatedAt", "slug", owner}
    result: list[str] = []
    for f in model.fields:
        if f.name in excluded:
            continue
        if "@relation" in (f.attributes or "") or f.type.endswith("[]"):
            continue
        # Exclure les FK raw (xxxId → UUID illisible en UI)
        if f.name.endswith("Id") and model_names:
            base = f.name[:-2]
            related = base[0].upper() + base[1:] if base else ""
            if related in model_names or any(mn.endswith(related) for mn in model_names if related):
                continue
        if f.type.rstrip("?") in ("String", "Int", "Float", "Boolean", "DateTime"):
            result.append(f.name)
        if len(result) >= 4:
            break
    return result or ["id"]


# ── Factory principale ────────────────────────────────────────────────────────

def build_model_context(model, spec) -> ModelGenerationContext:
    """
    Calcule ModelGenerationContext pour un modèle depuis la spec.
    Appeler UNE SEULE FOIS par modèle (en général dans dev_graph.py).
    """
    name = model.name
    camel = _pascal_to_camel(name)
    kebab = _pascal_to_kebab(name)
    owner = model.resolved_owner()
    spec_enums: dict = getattr(spec, "enums", None) or {}
    model_names: set[str] = {m.name for m in spec.models}

    fk_fields = _resolve_fk_fields(model, model_names, owner)
    fk_field_names = {fk.field_name for fk in fk_fields}

    editable: list[FieldInfo] = []
    datetime_fields: list[DatetimeFieldInfo] = []
    relation_fields: list[RelationFieldInfo] = []
    has_slug = False
    has_status = False

    for f in model.fields:
        fname_lower = f.name.lower()
        base_type = f.type.rstrip("?").rstrip("[]")
        is_optional = f.type.endswith("?")
        is_array = "[]" in f.type

        # Feature flags
        if fname_lower == "slug":
            has_slug = True
        if fname_lower == "status":
            has_status = True

        # Relations — détectées via la logique canonique unique
        if _is_relation(f.type, f.attributes, spec_enums):
            relation_fields.append(RelationFieldInfo(name=f.name, is_array=is_array))
            continue

        # DateTime → pour _serialize()
        if base_type == "DateTime":
            datetime_fields.append(DatetimeFieldInfo(name=f.name, is_nullable=is_optional))

        # Champs éditables : ni auto, ni owner, ni FK (FK gérés séparément)
        if _is_auto_field(f.name, f.attributes):
            continue
        if fname_lower == owner.lower():
            continue
        if f.name in fk_field_names:
            continue  # FK dans fk_fields, pas dans editable_fields
        if is_array:
            continue  # Tableaux → formulaires non supportés (Level A/D)

        editable.append(FieldInfo(
            name=f.name,
            prisma_type=f.type,
            base_type=base_type,
            is_optional=is_optional,
            has_default=_has_non_auto_default(f.attributes),
            input_type=_detect_input_type(f.name, base_type, spec_enums),
            attributes=f.attributes or "",
        ))

    # Contexte pages — nécessite spec pour conditionner les méthodes publiques
    pages = getattr(spec, "pages", []) or []
    model_pages = [p for p in pages if getattr(p, "model", None) == name]
    public_pages = [p for p in model_pages if not p.auth_required]
    has_public_pages = bool(public_pages)
    has_public_list = any(p.page_type == "list" for p in public_pages)
    has_public_detail = any(p.page_type in ("detail", "detail-slug") for p in public_pages)

    list_pages = [p for p in model_pages if p.page_type == "list"]
    private_list = next((p for p in list_pages if p.auth_required), None)
    public_list_page = next((p for p in list_pages if not p.auth_required), None)
    chosen_list = private_list or public_list_page
    list_page_path = chosen_list.path if chosen_list else ""

    ctx = ModelGenerationContext(
        model=model,
        name=name,
        camel=camel,
        kebab=kebab,
        owner=owner,
        serialized_type=f"Serialized{name}",
        spec_enums=spec_enums,
        editable_fields=editable,
        fk_fields=fk_fields,
        datetime_fields=datetime_fields,
        relation_fields=relation_fields,
        display_fields=_resolve_display_fields(model, owner, frozenset(model_names)),
        has_slug=has_slug,
        has_status=has_status,
        has_relations=bool(relation_fields),
        has_public_pages=has_public_pages,
        has_public_list=has_public_list,
        has_public_detail=has_public_detail,
        list_page_path=list_page_path,
    )

    logger.debug(
        "[model_context] %s : %d éditables, %d FK, %d datetime, %d relations | "
        "slug=%s status=%s public=%s",
        name, len(editable), len(fk_fields), len(datetime_fields), len(relation_fields),
        has_slug, has_status, has_public_pages,
    )
    return ctx


def build_all_contexts(spec) -> dict[str, ModelGenerationContext]:
    """
    Calcule ModelGenerationContext pour tous les modèles de la spec.
    Retourne {model_name: ctx} — à appeler une fois dans dev_graph.py.
    """
    return {m.name: build_model_context(m, spec) for m in spec.models}
