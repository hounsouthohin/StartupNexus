"""getPublicByIdWithRelations — actif si le modèle a des pages publiques ET des relations."""
from __future__ import annotations
from .base import ServiceMethodModule, build_rel_select, dt_map_with_relations


class PublicRelationsModule(ServiceMethodModule):
    def should_activate(self, ctx) -> bool:
        return bool(ctx.has_public_pages and ctx.relation_fields)

    def generate(self, ctx, **kwargs) -> list[str]:
        all_contexts: dict = kwargs.get("all_contexts") or {}
        camel = ctx.camel
        serialized = ctx.serialized_type

        _rel_sel = build_rel_select(ctx, all_contexts)
        _rel_map = dt_map_with_relations(ctx, all_contexts)

        return [
            "",
            f"  getPublicByIdWithRelations: async (id: string): Promise<{serialized}> => {{",
            f"    const item = await prisma.{camel}.findUnique({{ where: {{ id }}, select: {{ {_rel_sel} }} }})",
            "    if (!item) notFound()",
            f"    return ({_rel_map})(item) as {serialized}",
            "  },",
        ]
