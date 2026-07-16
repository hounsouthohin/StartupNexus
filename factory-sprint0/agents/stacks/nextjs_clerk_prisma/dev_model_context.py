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
from dataclasses import dataclass, field

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

# Valeurs par défaut pour les champs String sémantiquement contraints.
# Utilisé comme filet de sécurité quand l'architect génère String @default(...)
# au lieu d'un Prisma enum — évite les <select> vides dans les formulaires.
# RÈGLE 4 architect doit toujours produire des enums Prisma corrects ;
# ce dict ne couvre que les cas de défaillance architect.
_STRING_ENUM_DEFAULTS: dict[str, tuple[str, ...]] = {
    "status":   ("active", "inactive", "pending", "draft", "published", "completed", "cancelled"),
    "priority": ("low", "medium", "high", "urgent"),
    "type":     ("standard", "premium", "basic", "other"),
    "role":     ("admin", "user", "moderator", "member"),
    "state":    ("active", "inactive", "pending", "closed"),
    "visibility": ("public", "private", "draft"),
    "category": ("general", "work", "personal", "other"),
}


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
    allowed_values: tuple[str, ...] = ()  # valeurs enum autorisées (enum Prisma ou String contraint)
    semantic_type: str = ""  # annotation sémantique brute (email/url/currency/date…) — source Zod fine


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
class DecimalFieldInfo:
    """Champ Decimal — Prisma retourne un objet Decimal, jamais un number JS.
    _serialize() doit appeler .toNumber() (même pattern que DateTime → toISOString)."""
    name: str
    is_nullable: bool


@dataclass(frozen=True)
class RelationFieldInfo:
    """Champ @relation — inclus dans include:{} de getAllWithRelations()."""
    name: str
    is_array: bool


@dataclass(frozen=True)
class M2MFieldInfo:
    """
    Relation many-to-many implicite Prisma (ex: `tags Tag[]` sans @relation,
    où Tag n'a PAS de FK vers ce modèle — sinon ce serait le côté inverse d'un 1-N).
    input_name : nom du champ formulaire/Zod portant les ids sélectionnés (ex: "tagIds").
    """
    name: str            # "tags" — nom du champ relation sur le modèle
    related_model: str   # "Tag"
    related_camel: str   # "tag"
    related_kebab: str   # "tag"
    input_name: str      # "tagIds"


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

    # decimal_fields : champs Decimal — convertis via .toNumber() dans les serializers.
    decimal_fields: list[DecimalFieldInfo]

    # relation_fields : champs @relation pour include:{} de getAllWithRelations().
    relation_fields: list[RelationFieldInfo]

    # m2m_fields : relations many-to-many implicites (Post.tags Tag[] ↔ Tag.posts Post[]).
    #   Sous-ensemble de relation_fields (is_array=True, sans FK inverse chez le related).
    #   Portent la sélection multiple dans les formulaires (connect/set dans le service).
    m2m_fields: list[M2MFieldInfo]

    # display_fields : jusqu'à 4 champs scalaires affichables dans les listes UI.
    display_fields: list[str]

    # ── Feature flags ─────────────────────────────────────────────────────────
    slug_source: str          # champ titre à slugifier (auto-slug côté service) ; "" = slug manuel
    has_slug: bool            # modèle a un champ "slug" → active getBySlug() et detail-slug pages
    has_status: bool          # modèle a un champ "status" → badge coloré + getPublished()
    has_published_bool: bool  # modèle a un champ "Boolean published" → filtre getPublicAll()
    has_relations: bool       # au moins un @relation → active getAllWithRelations()
    has_m2m: bool             # au moins une relation many-to-many implicite → multi-select + connect

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

    # enum_value_labels : labels lisibles par valeur d'enum, depuis spec.enum_value_labels.
    #   Alimenté par l'architect LLM. Dict vide si absent — fallback vers la valeur brute dans les templates.
    enum_value_labels: dict

    # ui_labels : labels affichés par champ, depuis spec.ui_labels[model_name].
    #   Ex: {"title": "Titre", "urgency": "Urgence"}. Dict vide si absent → fallback nom du champ.
    ui_labels: dict

    # title_plural : titre pluriel du modèle dans la langue du brief.
    #   Ex: "Tâches" pour Task. Fallback: "{ModelName}s".
    title_plural: str

    # title_singular : titre singulier du modèle dans la langue du brief.
    #   Ex: "Tâche" pour Task. Utilisé pour « Nouveau X » / « Modifier X ».
    #   Fallback: nom brut du modèle (mieux vaut ça qu'un pluriel mécaniquement tronqué).
    title_singular: str

    # ── Type I — Workflow / machine à états (Juil 2026) ───────────────────────
    # status_flow : StatusFlowDeclaration produite par l'architect pour CE modèle, ou None.
    #   None = pas de cycle de vie (statut simple étiquette, ou aucun statut) → aucun
    #   changement de comportement, le modèle reste un CRUD classique.
    #   Porte `initial` (état de départ) et `transitions` {état: [états atteignables]}.
    status_flow: object = None

    # create_excluded_fields : champs présents dans editable_fields mais JAMAIS saisis à la
    #   CRÉATION — ils restent éditables ensuite. À ne pas confondre avec le slug, exclu
    #   PARTOUT (auto-généré à vie).
    #   Cas type I : le statut d'un workflow est forcé à `status_flow.initial` par le service ;
    #   l'exclure aussi de l'édition figerait toute entité en brouillon pour l'éternité.
    create_excluded_fields: list[str] = field(default_factory=list)


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


_SEMANTIC_TO_INPUT: dict[str, str] = {
    "textarea":      "textarea",
    "status-enum":   "enum-select",
    "priority-enum": "enum-select",
    "currency":      "number",
    "date":          "date",
    "datetime":      "datetime-local",
    "url":           "url",
    "email":         "email",
    "color":         "color",
    "text":          "text",
}


def _detect_input_type_and_values(
    field_name: str,
    base_type: str,
    spec_enums: dict,
    enriched_type: str = "",
    annotation_values: "list[str] | None" = None,
) -> tuple[str, tuple[str, ...]]:
    """
    Retourne (input_type, allowed_values) pour un champ scalaire.

    Priorité 1 : annotation sémantique LLM (enriched_type) — détermine le type d'input.
                 Les valeurs sont réconciliées : spec_enums prime sur annotation_values.
    Priorité 2 : enum Prisma déclaré dans spec.enums.
    Priorité 3 : String sémantiquement contraint (filet de sécurité si RÈGLE 4 architect ratée).
    Priorité 4 : heuristiques type standard.

    Réconciliation enriched_type + spec_enums :
    Avant, enriched_type court-circuitait en retournant () pour allowed_values, même quand
    spec_enums avait les valeurs réelles. Ce bug rendait tous les selects enum vides dans
    les formulaires enfants (module_detail_with_children). Le fix : enriched_type détermine
    le type d'input (textarea, enum-select, number…) mais spec_enums fournit toujours
    les valeurs quand elles existent.
    """
    if enriched_type:
        mapped = _SEMANTIC_TO_INPUT.get(enriched_type, "")
        if mapped:
            # Réconciliation : spec_enums est source de vérité pour les valeurs
            if base_type in spec_enums:
                return mapped, tuple(spec_enums[base_type])
            # Fallback : valeurs fournies par le semantic annotator
            if annotation_values:
                return mapped, tuple(annotation_values)
            return mapped, ()
    if base_type in spec_enums:
        return "enum-select", tuple(spec_enums[base_type])
    # Filet architect : String avec nom sémantique contraint → enum-select avec valeurs standard
    if base_type == "String" and field_name.lower() in _STRING_ENUM_DEFAULTS:
        return "enum-select", _STRING_ENUM_DEFAULTS[field_name.lower()]
    if base_type == "Boolean":
        return "checkbox", ()
    if base_type in ("Int", "Float", "Decimal"):
        return "number", ()
    if base_type == "DateTime":
        return "datetime-local", ()
    if field_name.lower() in _TEXTAREA_NAMES:
        return "textarea", ()
    return "text", ()



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


def _model_has_fk_to(candidate_model, target_name: str, model_names: set[str]) -> bool:
    """True si candidate_model a un champ FK (xxxId) résolvant vers target_name."""
    for f in candidate_model.fields:
        if not f.name.endswith("Id") or f.name == "id":
            continue
        base = f.name[:-2]
        related = base[0].upper() + base[1:] if base else ""
        if related == target_name:
            return True
        # Fallback suffix (même logique que _resolve_fk_fields) : "Category" → "RecipeCategory"
        if related not in model_names and target_name.endswith(related) and related:
            return True
    return False


def _resolve_m2m_fields(model, spec, model_names: set[str], spec_enums: dict) -> list[M2MFieldInfo]:
    """
    Détecte les relations many-to-many implicites Prisma.

    Critère : champ tableau (`Tag[]`) dont le type est un modèle connu ET dont le
    modèle cible n'a PAS de FK vers ce modèle. Si le cible a une FK (Comment.postId),
    le champ tableau est le côté inverse d'un 1-N — pas un M2M.
    """
    result: list[M2MFieldInfo] = []
    all_models = {m.name: m for m in spec.models}
    for f in model.fields:
        if "[]" not in f.type:
            continue
        base = f.type.rstrip("?").rstrip("[]")
        if base in _PRISMA_SCALAR_TYPES or base in spec_enums:
            continue  # tableau scalaire ou enum — pas une relation
        related = all_models.get(base)
        if related is None:
            continue
        if _model_has_fk_to(related, model.name, model_names):
            continue  # côté inverse d'un 1-N — géré par relation_fields/ChildModule
        related_camel = _pascal_to_camel(base)
        result.append(M2MFieldInfo(
            name=f.name,
            related_model=base,
            related_camel=related_camel,
            related_kebab=_pascal_to_kebab(base),
            input_name=f"{related_camel}Ids",
        ))
    return result


def _resolve_display_fields(
    model,
    owner: str,
    model_names: "frozenset[str] | None" = None,
    spec_enums: "dict | None" = None,
) -> list[str]:
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
        base_type = f.type.rstrip("?").rstrip("[]")
        if base_type in ("String", "Int", "Float", "Boolean", "DateTime") or (spec_enums and base_type in spec_enums):
            result.append(f.name)
        if len(result) >= 4:
            break
    return result or ["id"]


# ── Factory principale ────────────────────────────────────────────────────────

def build_model_context(model, spec, enriched_spec=None) -> ModelGenerationContext:
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
    m2m_fields = _resolve_m2m_fields(model, spec, model_names, spec_enums)

    # slug_source (V7) : si le modèle a un champ `slug` ET un champ titre, le slug est
    # AUTO-GÉNÉRÉ côté service (slugify + suffixe anti-collision) — jamais saisi par l'user.
    # slug_source = nom exact du champ titre à slugifier ; "" = slug non auto (reste manuel).
    _TITLE_CANDIDATES = ("title", "name", "heading", "label", "subject")
    _fields_by_lower = {f.name.lower(): f.name for f in model.fields}
    slug_source = ""
    if "slug" in _fields_by_lower:
        for _c in _TITLE_CANDIDATES:
            if _c in _fields_by_lower:
                slug_source = _fields_by_lower[_c]
                break

    # ── status_flow (type I) — validation déterministe de la décision LLM ─────────
    # L'architect DÉCIDE le graphe (il comprend le métier), mais on ne compile JAMAIS une
    # déclaration invalide : un champ fantôme ou un état hors enum produirait du TypeScript
    # faux. Toute déclaration douteuse → None : le modèle redevient un CRUD simple.
    # Dégrader proprement vaut mieux que générer du faux avec assurance.
    status_flow = None
    create_excluded_fields: list[str] = []
    _flows = (getattr(enriched_spec, "status_flows", None) or {}) if enriched_spec else {}
    _decl = _flows.get(name)
    if _decl is not None:
        _sf_declared = getattr(_decl, "field", "") or "status"
        _sf_real = _fields_by_lower.get(_sf_declared.lower())
        _sf_obj = next((f for f in model.fields if f.name == _sf_real), None) if _sf_real else None
        _enum_vals: list[str] = []
        if _sf_obj is not None:
            _enum_vals = list(spec_enums.get(_sf_obj.type.rstrip("?").rstrip("[]"), []) or [])
        _initial = getattr(_decl, "initial", "") or ""
        _raw_trans = dict(getattr(_decl, "transitions", None) or {})

        if _sf_real and _enum_vals and _initial in _enum_vals:
            # Ne garder que les états réellement présents dans l'enum Prisma : un état
            # halluciné par le LLM ne doit jamais atteindre le compilateur.
            _clean = {
                _s: [_t for _t in (_nxt or []) if _t in _enum_vals]
                for _s, _nxt in _raw_trans.items() if _s in _enum_vals
            }
            if any(_clean.values()):
                from agents.semantic_spec import StatusFlowDeclaration as _SFD
                status_flow = _SFD(field=_sf_real, initial=_initial, transitions=_clean)
                create_excluded_fields.append(_sf_real)
            else:
                logger.warning(
                    "[model_context] %s : status_flow ignoré — aucune transition exploitable", name,
                )
        else:
            logger.warning(
                "[model_context] %s : status_flow ignoré — champ=%r initial=%r hors enum %s",
                name, _sf_declared, _initial, _enum_vals or "(aucun)",
            )

    editable: list[FieldInfo] = []
    datetime_fields: list[DatetimeFieldInfo] = []
    decimal_fields: list[DecimalFieldInfo] = []
    relation_fields: list[RelationFieldInfo] = []
    has_slug = False
    has_status = False
    has_published_bool = False

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
        if fname_lower == "published" and base_type == "Boolean":
            has_published_bool = True

        # Relations — détectées via la logique canonique unique
        if _is_relation(f.type, f.attributes, spec_enums):
            relation_fields.append(RelationFieldInfo(name=f.name, is_array=is_array))
            continue

        # DateTime → pour _serialize()
        if base_type == "DateTime":
            datetime_fields.append(DatetimeFieldInfo(name=f.name, is_nullable=is_optional))

        # Decimal → .toNumber() dans les serializers (objet Prisma Decimal ≠ number JS)
        if base_type == "Decimal":
            decimal_fields.append(DecimalFieldInfo(name=f.name, is_nullable=is_optional))

        # Champs éditables : ni auto, ni owner, ni FK (FK gérés séparément)
        if _is_auto_field(f.name, f.attributes):
            continue
        if fname_lower == owner.lower():
            continue
        if f.name in fk_field_names:
            continue  # FK dans fk_fields, pas dans editable_fields
        if is_array:
            continue  # Tableaux → formulaires non supportés (Level A/D)
        if fname_lower == "slug" and slug_source:
            continue  # slug auto-généré depuis le titre → jamais dans le formulaire (V7)

        _ann = (enriched_spec.field_annotations.get(f.name) if enriched_spec else None)
        _itype, _allowed = _detect_input_type_and_values(
            f.name, base_type, spec_enums,
            enriched_type=_ann.semantic_type if _ann else "",
            annotation_values=(_ann.values if _ann and _ann.values else None),
        )
        editable.append(FieldInfo(
            name=f.name,
            prisma_type=f.type,
            base_type=base_type,
            is_optional=is_optional,
            has_default=_has_non_auto_default(f.attributes),
            input_type=_itype,
            attributes=f.attributes or "",
            allowed_values=_allowed,
            semantic_type=(_ann.semantic_type if _ann else ""),
        ))

    # Guard: detail-slug page sans champ slug dans le modèle → incohérence architect
    if not has_slug:
        _pages_check = getattr(spec, "pages", []) or []
        _has_slug_page = any(
            getattr(p, "page_type", "") == "detail-slug"
            for p in _pages_check
            if getattr(p, "model", None) == name
        )
        if _has_slug_page:
            logger.warning(
                "[model_context] %s : page_type='detail-slug' déclarée mais aucun champ 'slug' "
                "dans le modèle Prisma — getBySlugWithRelations() ne sera PAS généré par le service. "
                "L'architect doit ajouter `slug String @unique` au modèle.",
                name,
            )

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
        decimal_fields=decimal_fields,
        relation_fields=relation_fields,
        m2m_fields=m2m_fields,
        display_fields=_resolve_display_fields(model, owner, frozenset(model_names), spec_enums=spec_enums),
        slug_source=slug_source,
        status_flow=status_flow,
        create_excluded_fields=create_excluded_fields,
        has_slug=has_slug,
        has_status=has_status,
        has_published_bool=has_published_bool,
        has_relations=bool(relation_fields),
        has_m2m=bool(m2m_fields),
        has_public_pages=has_public_pages,
        has_public_list=has_public_list,
        has_public_detail=has_public_detail,
        list_page_path=list_page_path,
        enum_value_labels=getattr(spec, "enum_value_labels", None) or {},
        ui_labels=(getattr(spec, "ui_labels", None) or {}).get(name, {}),
        title_plural=(getattr(spec, "title_plurals", None) or {}).get(name, f"{name}s"),
        title_singular=(getattr(spec, "title_singulars", None) or {}).get(name, name),
    )

    logger.debug(
        "[model_context] %s : %d éditables, %d FK, %d datetime, %d relations | "
        "slug=%s status=%s public=%s flow=%s",
        name, len(editable), len(fk_fields), len(datetime_fields), len(relation_fields),
        has_slug, has_status, has_public_pages,
        (f"{status_flow.initial}→{status_flow.transitions}" if status_flow else "—"),
    )
    return ctx


def build_all_contexts(spec, enriched_spec=None) -> dict[str, ModelGenerationContext]:
    """
    Calcule ModelGenerationContext pour tous les modèles de la spec.
    Retourne {model_name: ctx} — à appeler une fois dans dev_graph.py.
    Résilient : une erreur sur un modèle n'empêche pas les autres d'être traités.
    """
    result: dict[str, ModelGenerationContext] = {}
    for m in spec.models:
        try:
            result[m.name] = build_model_context(m, spec, enriched_spec=enriched_spec)
        except Exception as _ctx_err:
            logger.error(
                "[model_context] Impossible de construire le contexte pour '%s' : %s — "
                "ce modèle sera ignoré par les générateurs de templates.",
                m.name, _ctx_err,
                exc_info=True,
            )
    return result
