"""
agents/stacks/nextjs_clerk_prisma/dev_service_spec.py
──────────────────────────────────────────────────────
Source unique de vérité pour l'inventaire des méthodes d'un service.

Problème résolu :
  La question "quelles méthodes expose un service ?" était répondue
  indépendamment en 3 endroits (generator, manifest, doc LLM).
  Chaque copie pouvait diverger silencieusement — et le faisait.

Solution :
  `build_service_spec(ctx)` calcule UNE FOIS la liste des méthodes.
  Chaque consommateur lit cette struct et la formate selon ses besoins.

Consommateurs :
  - dev_service_generator.py → format_service_map_for_prompt()
  - level_a_manifest.py      → _methods_from_context()
  - planner.py               → build_page_contracts() (validation)
"""
from __future__ import annotations

from dataclasses import dataclass

from .dev_model_context import ModelGenerationContext

_PUBLISHED_LIKE = frozenset(
    {"published", "active", "enabled", "approved", "public", "visible"}
)


# ── Types ─────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class MethodSpec:
    name: str   # ex: "getByCourseId"
    sig: str    # ex: "(userId: string, courseId: string) → SerializedModule[]"


@dataclass(frozen=True)
class ServiceSpec:
    """
    Inventaire canonique des méthodes d'un service.

    Immuable après construction — ne jamais patcher après build_service_spec().
    """
    model_name: str
    camel: str
    kebab: str
    owner: str
    serialized: str
    methods: tuple[MethodSpec, ...]

    def has(self, method_name: str) -> bool:
        """True si la méthode existe dans ce service."""
        return any(m.name == method_name for m in self.methods)

    def parent_id_methods(self) -> list[MethodSpec]:
        """Méthodes getBy{Parent}Id — CROSS_ENTITY : une par FK déclarée."""
        return [
            m for m in self.methods
            if m.name.startswith("getBy") and m.name.endswith("Id")
            and m.name != "getById"
        ]


# ── Builder ───────────────────────────────────────────────────────────────────

def build_service_spec(
    ctx: ModelGenerationContext,
    required_queries: list | None = None,
) -> ServiceSpec:
    """
    Calcule l'inventaire exact des méthodes depuis ModelGenerationContext.

    Miroir AUTORITAIRE de _generate_service_for_model() :
    si une méthode est ajoutée dans le générateur, l'ajouter ici aussi.
    C'est ici que vit la décision — pas dans le générateur ni dans le manifest.
    """
    owner = ctx.owner
    s = ctx.serialized_type
    name = ctx.name
    methods: list[MethodSpec] = []

    # ── getAll ────────────────────────────────────────────────────────────────
    methods.append(MethodSpec(
        "getAll",
        f"({owner}: string, page?: number) → Promise<{s}[]>",
    ))

    # ── getBy{Parent}Id — une par FK déclarée (CROSS_ENTITY) ─────────────────
    for fk in (ctx.fk_fields or []):
        methods.append(MethodSpec(
            f"getBy{fk.related_model}Id",
            f"(userId: string, {fk.field_name}: string, page?: number) → Promise<{s}[]>",
        ))

    # getPublished DÉPRÉCIÉ (voir service_modules/__init__.py) : redondant avec getPublicAll,
    # qui filtre déjà par statut publié. Ne plus le lister dans CONTRACTS.md.

    # ── getById ───────────────────────────────────────────────────────────────
    methods.append(MethodSpec(
        "getById",
        f"({owner}: string, id: string) → Promise<{s}>",
    ))

    # ── getPublicById + getPublicAll — pages publiques ────────────────────────
    if ctx.has_public_pages:
        methods.append(MethodSpec(
            "getPublicById",
            f"(id: string) → Promise<{s}>  (sans owner)",
        ))
        if ctx.has_status:
            _note = "  (filtrée par statut publié)"
        elif getattr(ctx, "has_published_bool", False):
            _note = "  (filtrée published=true)"
        else:
            _note = ""
        methods.append(MethodSpec(
            "getPublicAll",
            f"() → Promise<{s}[]>  (sans owner{_note})",
        ))

    # ── getBySlug / getBySlugOwned ────────────────────────────────────────────
    if ctx.has_slug:
        methods.append(MethodSpec(
            "getBySlug",
            f"(slug: string) → Promise<{s}>  (public)",
        ))
        methods.append(MethodSpec(
            "getBySlugOwned",
            f"({owner}: string, slug: string) → Promise<{s}>",
        ))

    # ── getAllWithRelations / getByIdWithRelations ─────────────────────────────
    if ctx.relation_fields:
        methods.append(MethodSpec(
            "getAllWithRelations",
            f"({owner}: string, page?: number) → Promise<{s}[]>  (avec relations)",
        ))
        methods.append(MethodSpec(
            "getByIdWithRelations",
            f"({owner}: string, id: string) → Promise<{s}>  (avec relations)",
        ))
        if ctx.has_public_pages:
            methods.append(MethodSpec(
                "getPublicByIdWithRelations",
                f"(id: string) → Promise<{s}>  (sans owner, avec relations)",
            ))
        if ctx.has_slug:
            methods.append(MethodSpec(
                "getBySlugWithRelations",
                f"(slug: string) → Promise<{s}>  (avec relations, public)",
            ))

    # ── Queries métier custom ─────────────────────────────────────────────────
    for q in (required_queries or []):
        _method_name = getattr(q, "name", None) or f"getBy{getattr(q, 'field', 'Unknown')}"
        _ret = f"Promise<{s}[]>" if getattr(q, "return_many", True) else f"Promise<{s}>"
        methods.append(MethodSpec(
            _method_name,
            f"(userId: string, ...) → {_ret}  (query métier)",
        ))

    # ── create / update / delete ──────────────────────────────────────────────
    methods.append(MethodSpec("create", f"({owner}: string, data: Create{name}Input) → Promise<{s}>"))
    methods.append(MethodSpec("update", f"({owner}: string, id: string, data: Update{name}Input) → Promise<{s}>"))
    methods.append(MethodSpec("delete", f"({owner}: string, id: string) → Promise<void>"))

    return ServiceSpec(
        model_name=name,
        camel=ctx.camel,
        kebab=ctx.kebab,
        owner=owner,
        serialized=s,
        methods=tuple(methods),
    )
