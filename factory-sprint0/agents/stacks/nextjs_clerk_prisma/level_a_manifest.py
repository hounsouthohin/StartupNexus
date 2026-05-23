"""
level_a_manifest.py
────────────────────────────────────────────────────────────────────────
LevelAManifest — contrat structuré produit par Level A, consommé par dev_test.

Remplace l'interface STRING (service_map_str + path list) par un objet typé
qui expose exactement les méthodes disponibles par modèle.

Flux :
  dev_graph.py → build_level_a_manifest() → LevelAManifest
                                          ↓
                        planner.py        ← manifest.page_contracts
                        dev_context.py    ← manifest.models[name]
                        build_system_prompt ← manifest.service_map_str
"""
from __future__ import annotations

import re as _re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .dev_model_context import ModelGenerationContext


# ── Sous-types ───────────────────────────────────────────────────────────────

@dataclass
class ServiceMethod:
    name: str        # "getPublicAll"
    signature: str   # "() → Promise<SerializedProject[]> (status filtrée si enum)"


@dataclass
class ModelManifest:
    name: str                       # "Project"
    camel: str                      # "project"
    kebab: str                      # "project"
    serialized_type: str            # "SerializedProject"
    service_import: str             # "@/lib/services/project.service"
    service_var: str                # "projectService"
    methods: list[ServiceMethod]
    context: object                 # ModelGenerationContext (non typé → évite import circulaire)


# ── Manifest principal ───────────────────────────────────────────────────────

@dataclass
class LevelAManifest:
    models: dict[str, ModelManifest]             # {model_name: ModelManifest}
    template_written: dict[str, str]             # {path: content}
    page_contracts: dict[str, tuple[str, str]]   # {page_path: (page_hint, client_hint)}
    service_map_str: str                         # backward-compat string pour system_prompt


# ── Dérivation des méthodes depuis ModelGenerationContext ────────────────────

def _methods_from_context(ctx: "ModelGenerationContext") -> list[ServiceMethod]:
    """
    Dérive la liste exacte des méthodes de service depuis les flags ModelGenerationContext.
    Miroir de la logique de _generate_service_for_model() — doit rester synchrone.
    """
    name = ctx.name
    owner = ctx.owner
    s = ctx.serialized_type
    methods: list[ServiceMethod] = []

    methods.append(ServiceMethod(
        "getAll",
        f"({owner}: string, page?: number) → Promise<{s}[]>",
    ))

    if getattr(ctx, "has_public_pages", False) and getattr(ctx, "has_status", False):
        methods.append(ServiceMethod(
            "getPublished",
            f"() → Promise<{s}[]>  (sans owner, status=published filtrée)",
        ))

    methods.append(ServiceMethod(
        "getById",
        f"({owner}: string, id: string) → Promise<{s}>",
    ))

    if getattr(ctx, "has_public_pages", False):
        methods.append(ServiceMethod(
            "getPublicById",
            f"(id: string) → Promise<{s}>  (sans owner)",
        ))
        if getattr(ctx, "has_status", False):
            _filter_note = ", status filtrée (enum)"
        elif getattr(ctx, "has_published_bool", False):
            _filter_note = ", published=true filtrée"
        else:
            _filter_note = ""
        methods.append(ServiceMethod(
            "getPublicAll",
            f"() → Promise<{s}[]>  (sans owner{_filter_note})",
        ))

    if getattr(ctx, "has_slug", False):
        methods.append(ServiceMethod(
            "getBySlug",
            f"(slug: string) → Promise<{s}>",
        ))

    if getattr(ctx, "has_relations", False):
        methods.append(ServiceMethod(
            "getAllWithRelations",
            f"({owner}: string) → Promise<{s}[]>  (avec relations)",
        ))
        methods.append(ServiceMethod(
            "getByIdWithRelations",
            f"({owner}: string, id: string) → Promise<{s}>  (avec relations)",
        ))
        if getattr(ctx, "has_public_pages", False):
            methods.append(ServiceMethod(
                "getPublicByIdWithRelations",
                f"(id: string) → Promise<{s}>  (sans owner, avec relations)",
            ))
        if getattr(ctx, "has_slug", False):
            methods.append(ServiceMethod(
                "getBySlugWithRelations",
                f"(slug: string) → Promise<{s}>  (avec relations)",
            ))

    methods.append(ServiceMethod(
        "create",
        f"({owner}: string, data: Create{name}Input) → Promise<{name}>",
    ))
    methods.append(ServiceMethod(
        "update",
        f"({owner}: string, id: string, data: Update{name}Input) → Promise<{name}>",
    ))
    methods.append(ServiceMethod(
        "delete",
        f"({owner}: string, id: string) → Promise<void>",
    ))

    return methods


def _pascal_to_kebab(name: str) -> str:
    return _re.sub(r"(?<!^)(?=[A-Z])", "-", name).lower()


def _pascal_to_camel(name: str) -> str:
    return name[0].lower() + name[1:] if name else name


# ── Factory ──────────────────────────────────────────────────────────────────

def build_level_a_manifest(
    spec,
    contexts: "dict[str, ModelGenerationContext]",
    template_written: dict[str, str],
    service_map_str: str,
    page_contracts: "dict[str, tuple[str, str]] | None" = None,
) -> LevelAManifest:
    """
    Assemble LevelAManifest depuis les sorties des générateurs Level A.
    Appelé UNE SEULE FOIS dans dev_graph.py après tous les générateurs déterministes.

    page_contracts — optionnel : déjà calculé par build_page_contracts() dans planner.py.
                    Si absent, renseigné via {} (calculé plus tard par planner si besoin).
    """
    models: dict[str, ModelManifest] = {}

    for m in spec.models:
        ctx = contexts.get(m.name)
        if ctx is None:
            continue
        kebab = getattr(ctx, "kebab", _pascal_to_kebab(m.name))
        camel = getattr(ctx, "camel", _pascal_to_camel(m.name))
        models[m.name] = ModelManifest(
            name=m.name,
            camel=camel,
            kebab=kebab,
            serialized_type=getattr(ctx, "serialized_type", f"Serialized{m.name}"),
            service_import=f"@/lib/services/{kebab}.service",
            service_var=f"{camel}Service",
            methods=_methods_from_context(ctx),
            context=ctx,
        )

    return LevelAManifest(
        models=models,
        template_written=dict(template_written),
        page_contracts=page_contracts or {},
        service_map_str=service_map_str,
    )


def find_model_for_path_segment(manifest: LevelAManifest, segment: str) -> "ModelManifest | None":
    """
    Résout le ModelManifest associé à un segment de chemin URL.

    Cherche dans l'ordre :
      1. kebab direct  : "project" → Project
      2. kebab pluriel : "projects" → Project
      3. list_page_path : modèle dont la list_page_path commence par /segment/
         (couvre les pages custom comme /dashboard → modèle Project si list_page_path=/dashboard/projects)

    Utilisé par dev_context._dep_page pour les pages sans page.model déclaré.
    """
    if not manifest or not segment:
        return None

    for mm in manifest.models.values():
        if mm.kebab == segment or mm.kebab + "s" == segment:
            return mm

    # Fallback list_page_path
    for mm in manifest.models.values():
        ctx = mm.context
        lpp = getattr(ctx, "list_page_path", "") or ""
        lpp_segs = [s for s in lpp.strip("/").split("/") if s and not s.startswith("[")]
        if lpp_segs and lpp_segs[0] == segment:
            return mm

    return None
