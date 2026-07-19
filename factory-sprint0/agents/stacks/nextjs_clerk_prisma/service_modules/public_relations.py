"""getPublicByIdWithRelations — actif si le modèle a des pages publiques ET des relations."""
from __future__ import annotations
from .base import ServiceMethodModule, MethodDecl, build_rel_select, dt_map_with_relations

_VISIBILITY_NAMES = {"published", "ispublic", "is_public", "public", "visible", "isvisible"}


class PublicRelationsModule(ServiceMethodModule):
    def should_activate(self, ctx) -> bool:
        return bool(ctx.has_public_pages and ctx.relation_fields)

    def methods_for(self, ctx) -> list[MethodDecl]:
        return [MethodDecl(
            "getPublicByIdWithRelations",
            f"(id: string) → Promise<{ctx.serialized_type}>  (sans owner, avec relations)",
        )]

    def generate(self, ctx, **kwargs) -> list[str]:
        all_contexts: dict = kwargs.get("all_contexts") or {}
        camel = ctx.camel
        serialized = ctx.serialized_type

        _rel_sel = build_rel_select(ctx, all_contexts)
        _rel_map = dt_map_with_relations(ctx, all_contexts)

        # Filtre de visibilité — même logique que public.py::getPublicById (IDOR guard)
        _vis_field = next(
            (f for f in ctx.model.fields
             if f.name.lower() in _VISIBILITY_NAMES
             and f.type.rstrip("?").rstrip("[]") == "Boolean"),
            None,
        )
        _pub_filter = ""
        if _vis_field:
            _pub_filter = f", {_vis_field.name}: true"
        elif ctx.has_published_bool:
            _pub_filter = ", published: true"

        return [
            "",
            f"  getPublicByIdWithRelations: async (id: string): Promise<{serialized}> => {{",
            f"    const item = await prisma.{camel}.findUnique({{ where: {{ id{_pub_filter} }}, select: {{ {_rel_sel} }} }})",
            "    if (!item) notFound()",
            f"    return ({_rel_map})(item) as {serialized}",
            "  },",
        ]
