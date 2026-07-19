"""getAllWithRelations + getByIdWithRelations — actif si le modèle a des relations."""
from __future__ import annotations
from .base import ServiceMethodModule, MethodDecl, build_rel_select, dt_map_with_relations


class RelationsModule(ServiceMethodModule):
    def should_activate(self, ctx) -> bool:
        return bool(ctx.relation_fields)

    def methods_for(self, ctx) -> list[MethodDecl]:
        o, s = ctx.owner, ctx.serialized_type
        return [
            MethodDecl("getAllWithRelations",  f"({o}: string, page?: number, pageSize?: number) → Promise<{s}[]>  (avec relations)"),
            MethodDecl("getByIdWithRelations", f"({o}: string, id: string) → Promise<{s}>  (avec relations)"),
        ]

    def generate(self, ctx, **kwargs) -> list[str]:
        all_contexts: dict = kwargs.get("all_contexts") or {}
        owner = ctx.owner
        camel = ctx.camel
        serialized = ctx.serialized_type

        _rel_sel = build_rel_select(ctx, all_contexts)
        _rel_map = dt_map_with_relations(ctx, all_contexts)

        return [
            "",
            f"  getAllWithRelations: async ({owner}: string, page: number = 1, pageSize: number = 20): Promise<{serialized}[]> => {{",
            f"    const items = await prisma.{camel}.findMany({{ where: {{ {owner} }}, select: {{ {_rel_sel} }}, orderBy: {{ createdAt: 'desc' }}, take: pageSize, skip: (page - 1) * pageSize }})",
            f"    return items.map({_rel_map}) as {serialized}[]",
            "  },",
            "",
            f"  getByIdWithRelations: async ({owner}: string, id: string): Promise<{serialized}> => {{",
            f"    const item = await prisma.{camel}.findFirst({{ where: {{ id, {owner} }}, select: {{ {_rel_sel} }} }})",
            "    if (!item) notFound()",
            f"    return ({_rel_map})(item) as {serialized}",
            "  },",
        ]
