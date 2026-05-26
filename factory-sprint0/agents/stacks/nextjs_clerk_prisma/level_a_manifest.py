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


# ── Dérivation des méthodes depuis ServiceSpec ───────────────────────────────

def _methods_from_context(ctx: "ModelGenerationContext") -> list[ServiceMethod]:
    """
    Délègue à build_service_spec — SOURCE UNIQUE de vérité.
    Ne plus modifier cette fonction : modifier build_service_spec() à la place.
    """
    from .dev_service_spec import build_service_spec
    spec = build_service_spec(ctx)
    return [ServiceMethod(name=m.name, signature=m.sig) for m in spec.methods]


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


def generate_contract_md(manifest: LevelAManifest) -> str:
    """
    Génère CONTRACTS.md — référence exacte des méthodes Level A pour le LLM executor.

    Injecté dans template_written → présent dans le répertoire projet avant la phase LLM.
    Le LLM lit ce fichier via read_file("CONTRACTS.md") pour connaître les méthodes
    disponibles sans les deviner ni les réinventer.
    """
    lines = [
        "# CONTRACTS — Level A Service API",
        "",
        "Ce fichier est généré automatiquement. Ne pas modifier.",
        "Il liste les méthodes de service disponibles pour chaque modèle.",
        "Importer depuis `@/lib/services/{model}.service` via la variable indiquée.",
        "",
    ]
    for mm in manifest.models.values():
        lines.append(f"## {mm.name}")
        lines.append(f"- **Import**: `import {{ {mm.service_var} }} from '{mm.service_import}'`")
        lines.append(f"- **Type sérialisé**: `{mm.serialized_type}` (dates = string, pas Date)")
        lines.append(f"- **Méthodes disponibles**:")
        for method in mm.methods:
            lines.append(f"  - `{mm.service_var}.{method.name}{method.signature}`")
        lines.append("")
    lines.append("## Règles d'utilisation")
    lines.append("- Ne jamais appeler `prisma.*` directement dans une page ou une action.")
    lines.append("- Toujours passer par le service ci-dessus.")
    lines.append("- Les méthodes absentes de cette liste n'existent pas — ne pas les inventer.")
    lines.append("")
    return "\n".join(lines)


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
