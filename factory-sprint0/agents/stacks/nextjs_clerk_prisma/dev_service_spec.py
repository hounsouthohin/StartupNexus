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
    Inventaire exact des méthodes — DÉRIVÉ des service_modules (17 Juil 2026).

    Avant : cette fonction ré-énumérait les méthodes à la main (« miroir autoritaire :
    l'ajouter ici AUSSI »). Ce « aussi » a produit le fantôme `getPublished` dans
    CONTRACTS.md → le LLM l'appelait → TS2339.
    Maintenant : chaque module déclare ce qu'il émet (`methods_for`), à côté du code qui
    l'émet. Diverger est devenu structurellement impossible.
    Voir docs/remodularisation_plan.md.
    """
    from .service_modules import methods_for_ctx

    s = ctx.serialized_type
    name = ctx.name
    methods: list[MethodSpec] = [
        MethodSpec(_d.name, _d.sig) for _d in methods_for_ctx(ctx)
    ]

    # ── Queries métier custom ─────────────────────────────────────────────────
    # Seule catégorie qui ne vient PAS des modules : déclarée par l'architect au cas par cas.
    for q in (required_queries or []):
        _method_name = getattr(q, "name", None) or f"getBy{getattr(q, 'field', 'Unknown')}"
        _ret = f"Promise<{s}[]>" if getattr(q, "return_many", True) else f"Promise<{s}>"
        methods.append(MethodSpec(
            _method_name,
            f"(userId: string, ...) → {_ret}  (query métier)",
        ))

    return ServiceSpec(
        model_name=name,
        camel=ctx.camel,
        kebab=ctx.kebab,
        owner=ctx.owner,
        serialized=s,
        methods=tuple(methods),
    )
