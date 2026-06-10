"""getPublished — actif si le modèle a des pages publiques ET un champ status."""
from __future__ import annotations
from .base import ServiceMethodModule, scalar_select_block, dt_inline_map

_PUBLISHED_LIKE = {"published", "active", "enabled", "approved", "public", "visible"}


class StatusModule(ServiceMethodModule):
    def should_activate(self, ctx) -> bool:
        return bool(ctx.has_public_pages and ctx.has_status)

    def generate(self, ctx, **kwargs) -> list[str]:
        camel = ctx.camel
        serialized = ctx.serialized_type
        _sel = scalar_select_block(ctx)
        _map = dt_inline_map(ctx)

        _status_field = next(
            (f for f in ctx.model.fields if f.name.lower() == "status"), None
        )
        _published_val = "published"
        if _status_field:
            _base = _status_field.type.rstrip("?").rstrip("[]")
            _enum_vals: list[str] = ctx.spec_enums.get(_base, [])
            _published_val = next(
                (v for v in _enum_vals if v in _PUBLISHED_LIKE),
                _enum_vals[0] if _enum_vals else "published",
            )

        return [
            "",
            f"  getPublished: async (page: number = 1, pageSize: number = 20): Promise<{serialized}[]> => {{",
            f"    const items = await prisma.{camel}.findMany({{ where: {{ status: '{_published_val}' }}, select: {{ {_sel} }}, orderBy: {{ createdAt: 'desc' }}, take: pageSize, skip: (page - 1) * pageSize }})",
            f"    return items.map({_map}) as {serialized}[]",
            "  },",
        ]
