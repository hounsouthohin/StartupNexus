"""
service_modules/base.py
────────────────────────
ServiceMethodModule ABC + helpers partagés entre tous les modules.

Les helpers sont extraits de dev_service_generator.py pour éviter la
duplication. Chaque module importe depuis ici ce dont il a besoin.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..dev_model_context import ModelGenerationContext, RelationFieldInfo


class ServiceMethodModule(ABC):
    """Interface qu'un module de méthode de service doit implémenter."""

    @abstractmethod
    def should_activate(self, ctx: "ModelGenerationContext") -> bool:
        """Retourne True si ce module doit générer des méthodes pour ce modèle."""

    @abstractmethod
    def generate(self, ctx: "ModelGenerationContext", **kwargs) -> list[str]:
        """
        Génère les lignes TypeScript à insérer dans le corps du service object.

        kwargs attendus (optionnels selon module) :
          all_contexts : dict[str, ModelGenerationContext]
          required_queries : list (QueryDeclaration) — custom queries
        Retourne une liste de strings (lignes), sans ouvrir/fermer le service object.
        """


# ─────────────────────────────────────────────────────────────────────────────
# Helpers partagés (anciennement dans dev_service_generator.py)
# ─────────────────────────────────────────────────────────────────────────────

def scalar_select_block(ctx: "ModelGenerationContext") -> str:
    """Prisma select block pour les champs scalaires uniquement (exclut owner, relations, tableaux)."""
    parts = []
    for f in ctx.model.fields:
        if f.name == ctx.owner:
            continue
        if "@relation" in (f.attributes or ""):
            continue
        if f.type.endswith("[]"):
            continue
        parts.append(f"{f.name}: true")
    return ", ".join(parts)


def dt_inline_map(ctx: "ModelGenerationContext") -> str:
    """
    Map function TypeScript inline : convertit les champs DateTime en ISO string.
    Utilisé pour les findMany avec select (owner exclu du résultat).
    """
    dt_parts = []
    for df in ctx.datetime_fields:
        if df.name == ctx.owner:
            continue
        if df.is_nullable:
            dt_parts.append(f"{df.name}: item.{df.name} ? item.{df.name}.toISOString() : null")
        else:
            dt_parts.append(f"{df.name}: item.{df.name}.toISOString()")
    if not dt_parts:
        return "item => item"
    return "item => ({ ...item, " + ", ".join(dt_parts) + " })"


def dt_map_with_relations(ctx: "ModelGenerationContext", all_contexts: dict) -> str:
    """
    Map function TypeScript inline pour getAllWithRelations / getByIdWithRelations.
    Sérialise les DateTime du modèle racine ET des modèles enfants dans les relations.
    """
    root_parts = []
    for df in ctx.datetime_fields:
        if df.name == ctx.owner:
            continue
        if df.is_nullable:
            root_parts.append(f"{df.name}: item.{df.name} ? item.{df.name}.toISOString() : null")
        else:
            root_parts.append(f"{df.name}: item.{df.name}.toISOString()")

    rel_parts = []
    for r in ctx.relation_fields:
        field = next((f for f in ctx.model.fields if f.name == r.name), None)
        related_name = field.type.rstrip("?").rstrip("[]") if field else None
        related_ctx = all_contexts.get(related_name) if related_name else None
        if not related_ctx or not related_ctx.datetime_fields:
            continue
        selected_in_nested = {"id"} | set(related_ctx.display_fields)
        if r.is_array:
            nested_dt = [
                (f"{rdf.name}: c.{rdf.name} ? c.{rdf.name}.toISOString() : null"
                 if rdf.is_nullable else f"{rdf.name}: c.{rdf.name}.toISOString()")
                for rdf in related_ctx.datetime_fields
                if rdf.name in selected_in_nested
            ]
            if not nested_dt:
                continue
            rel_parts.append(
                f"{r.name}: (item.{r.name} ?? []).map(c => ({{ ...c, {', '.join(nested_dt)} }}))"
            )
        else:
            nested_dt = [
                (f"{rdf.name}: item.{r.name}.{rdf.name} ? item.{r.name}.{rdf.name}.toISOString() : null"
                 if rdf.is_nullable else f"{rdf.name}: item.{r.name}.{rdf.name}.toISOString()")
                for rdf in related_ctx.datetime_fields
                if rdf.name in selected_in_nested
            ]
            if not nested_dt:
                continue
            rel_parts.append(
                f"{r.name}: item.{r.name} ? {{ ...item.{r.name}, {', '.join(nested_dt)} }} : item.{r.name}"
            )

    all_parts = root_parts + rel_parts
    if not all_parts:
        return "item => item"
    return "item => ({ ...item, " + ", ".join(all_parts) + " })"


def relation_nested_select(r: "RelationFieldInfo", ctx: "ModelGenerationContext", all_contexts: dict) -> str:
    """Select imbriqué pour un champ @relation dans getAllWithRelations."""
    field = next((f for f in ctx.model.fields if f.name == r.name), None)
    related_name = field.type.rstrip("?").rstrip("[]") if field else None
    related_ctx = all_contexts.get(related_name) if related_name else None
    if related_ctx:
        fields = ["id"] + [f for f in related_ctx.display_fields if f != "id"]
        nested = ", ".join(f"{f}: true" for f in fields)
    else:
        nested = "id: true"
    return f"{r.name}: {{ select: {{ {nested} }} }}"


def build_rel_select(ctx: "ModelGenerationContext", all_contexts: dict) -> str:
    """Construit le select scalaire + nested relations pour getAllWithRelations."""
    scalar_parts = [
        f"{f.name}: true" for f in ctx.model.fields
        if f.name != ctx.owner
        and "@relation" not in (f.attributes or "")
        and not f.type.endswith("[]")
    ]
    rel_parts = [relation_nested_select(r, ctx, all_contexts) for r in ctx.relation_fields]
    return ", ".join(scalar_parts + rel_parts)
