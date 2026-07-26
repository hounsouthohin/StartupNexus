"""
service_modules/base.py
────────────────────────
ServiceMethodModule ABC + helpers partagés entre tous les modules.

Les helpers sont extraits de dev_service_generator.py pour éviter la
duplication. Chaque module importe depuis ici ce dont il a besoin.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..dev_model_context import ModelGenerationContext, RelationFieldInfo


@dataclass(frozen=True)
class MethodDecl:
    """Une méthode réellement émise par un module, telle qu'exposée aux consommateurs.

    Vit dans le MÊME fichier que le code qui l'émet — c'est tout l'enjeu :
    un miroir recopié ailleurs finit toujours par diverger (cas `getPublished`,
    présent dans 4 représentations dont 3 mirrors manuels — voir docs/remodularisation_plan.md).
    """
    name: str   # ex: "getBySlugWithRelations"
    sig: str    # ex: "(slug: string) → Promise<SerializedPost>  (avec relations, public)"


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

    @abstractmethod
    def methods_for(self, ctx: "ModelGenerationContext") -> list[MethodDecl]:
        """
        SOURCE UNIQUE : les méthodes que ce module émet RÉELLEMENT pour ce ctx.

        Doit refléter exactement les conditions internes de generate() — y compris les
        conditions imbriquées (ex: slug.py n'émet getBySlugWithRelations que si le modèle
        a AUSSI des relations). CONTRACTS.md, le registre et les capabilities dérivent
        d'ici : aucune autre liste de méthodes ne doit être maintenue à la main.
        """


# ─────────────────────────────────────────────────────────────────────────────
# Helpers partagés (anciennement dans dev_service_generator.py)
# ─────────────────────────────────────────────────────────────────────────────

_PRISMA_SCALARS = frozenset({
    "String", "Int", "Float", "Boolean", "DateTime", "Decimal", "Json", "BigInt", "Bytes",
})


def _is_scalar_selectable(f, ctx: "ModelGenerationContext") -> bool:
    """
    True si le champ va dans un `select` scalaire — PAS une relation ni l'owner.

    Un champ dont le TYPE est un modèle est une relation, MÊME SANS @relation : c'est
    le cas du côté inverse d'un 1-1 (ex: `invoice Invoice?`). L'inclure comme scalaire
    ET comme relation produit une clé dupliquée → TS1117 (constaté coworking 26 Juil).
    """
    if f.name == ctx.owner:
        return False
    if "@relation" in (f.attributes or ""):
        return False
    if f.type.endswith("[]"):
        return False
    _base = f.type.rstrip("?").rstrip("[]")
    return _base in _PRISMA_SCALARS or _base in (ctx.spec_enums or {})


def scalar_select_block(ctx: "ModelGenerationContext") -> str:
    """Prisma select block pour les champs scalaires uniquement (exclut owner, relations, tableaux)."""
    return ", ".join(f"{f.name}: true" for f in ctx.model.fields if _is_scalar_selectable(f, ctx))


def dt_inline_map(ctx: "ModelGenerationContext") -> str:
    """
    Map function TypeScript inline : convertit DateTime → ISO string ET Decimal → number.
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
    for dcf in getattr(ctx, "decimal_fields", []) or []:
        if dcf.name == ctx.owner:
            continue
        if dcf.is_nullable:
            dt_parts.append(f"{dcf.name}: item.{dcf.name} != null ? Number(item.{dcf.name}) : null")
        else:
            dt_parts.append(f"{dcf.name}: Number(item.{dcf.name})")
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
    for dcf in getattr(ctx, "decimal_fields", []) or []:
        if dcf.name == ctx.owner:
            continue
        if dcf.is_nullable:
            root_parts.append(f"{dcf.name}: item.{dcf.name} != null ? Number(item.{dcf.name}) : null")
        else:
            root_parts.append(f"{dcf.name}: Number(item.{dcf.name})")

    rel_parts = []
    for r in ctx.relation_fields:
        field = next((f for f in ctx.model.fields if f.name == r.name), None)
        related_name = field.type.rstrip("?").rstrip("[]") if field else None
        related_ctx = all_contexts.get(related_name) if related_name else None
        _related_decimals = list(getattr(related_ctx, "decimal_fields", []) or []) if related_ctx else []
        if not related_ctx or (not related_ctx.datetime_fields and not _related_decimals):
            continue
        selected_in_nested = {"id"} | set(related_ctx.display_fields)
        if r.is_array:
            nested_dt = [
                (f"{rdf.name}: c.{rdf.name} ? c.{rdf.name}.toISOString() : null"
                 if rdf.is_nullable else f"{rdf.name}: c.{rdf.name}.toISOString()")
                for rdf in related_ctx.datetime_fields
                if rdf.name in selected_in_nested
            ] + [
                (f"{rdc.name}: c.{rdc.name} != null ? Number(c.{rdc.name}) : null"
                 if rdc.is_nullable else f"{rdc.name}: Number(c.{rdc.name})")
                for rdc in _related_decimals
                if rdc.name in selected_in_nested
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
            ] + [
                (f"{rdc.name}: item.{r.name}.{rdc.name} != null ? Number(item.{r.name}.{rdc.name}) : null"
                 if rdc.is_nullable else f"{rdc.name}: Number(item.{r.name}.{rdc.name})")
                for rdc in _related_decimals
                if rdc.name in selected_in_nested
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
    # _is_scalar_selectable exclut les relations singulières sans @relation (invoice Invoice?)
    # → plus de doublon avec le bloc relations (TS1117).
    scalar_parts = [f"{f.name}: true" for f in ctx.model.fields if _is_scalar_selectable(f, ctx)]
    rel_parts = [relation_nested_select(r, ctx, all_contexts) for r in ctx.relation_fields]
    return ", ".join(scalar_parts + rel_parts)
