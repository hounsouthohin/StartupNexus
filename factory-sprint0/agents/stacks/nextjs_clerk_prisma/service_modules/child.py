"""getBy{Parent}Id — actif si le modèle a des FK vers un parent connu."""
from __future__ import annotations
from .base import ServiceMethodModule, MethodDecl, scalar_select_block, dt_inline_map


class ChildModule(ServiceMethodModule):
    def should_activate(self, ctx) -> bool:
        return bool(ctx.fk_fields)

    def methods_for(self, ctx) -> list[MethodDecl]:
        # Une méthode par FK déclarée — noms concrets (getByProjectId…), donc impossibles
        # à énumérer dans un registre statique : c'est ici, et nulle part ailleurs.
        s = ctx.serialized_type
        return [
            MethodDecl(
                f"getBy{fk.related_model}Id",
                f"(userId: string, {fk.field_name}: string, page?: number, pageSize?: number) → Promise<{s}[]>",
            )
            for fk in ctx.fk_fields
        ]

    def generate(self, ctx, **kwargs) -> list[str]:
        owner = ctx.owner
        camel = ctx.camel
        serialized = ctx.serialized_type
        _sel = scalar_select_block(ctx)
        _map = dt_inline_map(ctx)

        lines: list[str] = []
        for _fk in ctx.fk_fields:
            _fk_field = _fk.field_name
            _parent_model = _fk.related_model
            lines += [
                "",
                f"  getBy{_parent_model}Id: async (userId: string, {_fk_field}: string, page: number = 1, pageSize: number = 20): Promise<{serialized}[]> => {{",
                f"    const items = await prisma.{camel}.findMany({{ where: {{ {_fk_field}, {owner}: userId }}, select: {{ {_sel} }}, orderBy: {{ createdAt: 'desc' }}, take: pageSize, skip: (page - 1) * pageSize }})",
                f"    return items.map({_map}) as {serialized}[]",
                "  },",
            ]
        return lines
