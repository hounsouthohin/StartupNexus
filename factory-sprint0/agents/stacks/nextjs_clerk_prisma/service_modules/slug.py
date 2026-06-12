"""getBySlug + getBySlugOwned (+ getBySlugWithRelations si relations) — actif si le modèle a un champ slug."""
from __future__ import annotations
from .base import ServiceMethodModule, build_rel_select, dt_map_with_relations

_VISIBILITY_NAMES = {"published", "ispublic", "is_public", "public", "visible", "isvisible"}


class SlugModule(ServiceMethodModule):
    def should_activate(self, ctx) -> bool:
        return bool(ctx.has_slug)

    def generate(self, ctx, **kwargs) -> list[str]:
        all_contexts: dict = kwargs.get("all_contexts") or {}
        owner = ctx.owner
        camel = ctx.camel
        serialized = ctx.serialized_type

        # Filtre de visibilité : empêche l'accès aux brouillons via URL slug directe
        _vis_field = next(
            (f for f in ctx.model.fields
             if f.name.lower() in _VISIBILITY_NAMES
             and f.type.rstrip("?").rstrip("[]") == "Boolean"),
            None,
        )
        if _vis_field:
            _pub_filter = f", {_vis_field.name}: true"
        elif ctx.has_published_bool:
            _pub_filter = ", published: true"
        else:
            _pub_filter = ""

        lines: list[str] = [
            "",
            f"  getBySlug: async (slug: string): Promise<{serialized}> => {{",
            f"    const item = await prisma.{camel}.findUnique({{ where: {{ slug{_pub_filter} }} }})",
            "    if (!item) notFound()",
            "    return _serialize(item)",
            "  },",
            "",
            f"  getBySlugOwned: async ({owner}: string, slug: string): Promise<{serialized}> => {{",
            f"    const item = await prisma.{camel}.findFirst({{ where: {{ slug, {owner} }} }})",
            "    if (!item) notFound()",
            "    return _serialize(item)",
            "  },",
        ]

        if ctx.relation_fields:
            _rel_sel = build_rel_select(ctx, all_contexts)
            _rel_map = dt_map_with_relations(ctx, all_contexts)
            lines += [
                "",
                f"  getBySlugWithRelations: async (slug: string): Promise<{serialized}> => {{",
                f"    const item = await prisma.{camel}.findUnique({{ where: {{ slug{_pub_filter} }}, select: {{ {_rel_sel} }} }})",
                "    if (!item) notFound()",
                f"    return ({_rel_map})(item) as {serialized}",
                "  },",
            ]

        return lines
