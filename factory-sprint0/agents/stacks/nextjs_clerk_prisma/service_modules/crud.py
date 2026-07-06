"""getAll + getById + create + update + delete — toujours actif."""
from __future__ import annotations
from .base import ServiceMethodModule, scalar_select_block, dt_inline_map


class CrudModule(ServiceMethodModule):
    def should_activate(self, ctx) -> bool:
        return True

    def generate(self, ctx, **kwargs) -> list[str]:
        owner = ctx.owner
        camel = ctx.camel
        serialized = ctx.serialized_type
        name = ctx.name
        _sel = scalar_select_block(ctx)
        _map = dt_inline_map(ctx)

        # M2M : les ids reçus du formulaire ({related}Ids) sont traduits en
        # connect (create) / set (update) — jamais passés bruts à Prisma.
        _m2m = list(getattr(ctx, "m2m_fields", []) or [])
        if _m2m:
            _destructure = ", ".join(mf.input_name for mf in _m2m)
            _connect_parts = ", ".join(
                f"...({mf.input_name} && {mf.input_name}.length ? {{ {mf.name}: {{ connect: {mf.input_name}.map(_id => ({{ id: _id }})) }} }} : {{}})"
                for mf in _m2m
            )
            _set_parts = ", ".join(
                f"...({mf.input_name} ? {{ {mf.name}: {{ set: {mf.input_name}.map(_id => ({{ id: _id }})) }} }} : {{}})"
                for mf in _m2m
            )
            create_lines = [
                f"  create: async ({owner}: string, data: Create{name}Input): Promise<{serialized}> => {{",
                f"    const {{ {_destructure}, ...rest }} = data",
                f"    const result = await prisma.{camel}.create({{",
                f"      data: {{ ...rest, {owner}, {_connect_parts} }}",
                "    })",
                "    return _serialize(result)",
                "  },",
            ]
            update_lines = [
                f"  update: async ({owner}: string, id: string, data: Update{name}Input): Promise<{serialized}> => {{",
                f"    const {{ {_destructure}, ...rest }} = data",
                f"    const result = await prisma.{camel}.update({{",
                f"      where: {{ id, {owner} }},",
                f"      data: {{ ...rest, {_set_parts} }}",
                "    })",
                "    return _serialize(result)",
                "  },",
            ]
        else:
            create_lines = [
                f"  create: async ({owner}: string, data: Create{name}Input): Promise<{serialized}> => {{",
                f"    const result = await prisma.{camel}.create({{",
                f"      data: {{ ...data, {owner} }}",
                "    })",
                "    return _serialize(result)",
                "  },",
            ]
            update_lines = [
                f"  update: async ({owner}: string, id: string, data: Update{name}Input): Promise<{serialized}> => {{",
                f"    const result = await prisma.{camel}.update({{",
                f"      where: {{ id, {owner} }},",
                "      data: { ...data }",
                "    })",
                "    return _serialize(result)",
                "  },",
            ]

        return [
            f"  getAll: async ({owner}: string, page: number = 1, pageSize: number = 20): Promise<{serialized}[]> => {{",
            f"    const items = await prisma.{camel}.findMany({{ where: {{ {owner} }}, select: {{ {_sel} }}, orderBy: {{ createdAt: 'desc' }}, take: pageSize, skip: (page - 1) * pageSize }})",
            f"    return items.map({_map}) as {serialized}[]",
            "  },",
            "",
            f"  getById: async ({owner}: string, id: string): Promise<{serialized}> => {{",
            f"    const item = await prisma.{camel}.findFirst({{ where: {{ id, {owner} }} }})",
            "    if (!item) notFound()",
            "    return _serialize(item)",
            "  },",
            "",
            *create_lines,
            "",
            *update_lines,
            "",
            f"  delete: async ({owner}: string, id: string): Promise<void> => {{",
            f"    await prisma.{camel}.delete({{ where: {{ id, {owner} }} }})",
            "  },",
        ]
