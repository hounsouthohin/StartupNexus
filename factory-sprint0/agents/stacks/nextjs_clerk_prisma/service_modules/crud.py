"""getAll + getById + create + update + delete — toujours actif."""
from __future__ import annotations
from .base import ServiceMethodModule, scalar_select_block, dt_inline_map


class CrudModule(ServiceMethodModule):
    def should_activate(self, ctx) -> bool:
        return True

    def generate(self, ctx, **kwargs) -> list[str]:
        all_contexts: dict = kwargs.get("all_contexts") or {}
        owner = ctx.owner
        camel = ctx.camel
        serialized = ctx.serialized_type
        name = ctx.name
        _sel = scalar_select_block(ctx)
        _map = dt_inline_map(ctx)

        # Owner du modèle LIÉ (single-tenant : même valeur userId, mais le nom du
        # champ peut différer — Post.authorId lié à Tag.userId). Fallback owner courant.
        def _rel_owner(model_name: str) -> str:
            _rc = all_contexts.get(model_name)
            return _rc.owner if _rc is not None else owner

        # ── Garde d'ownership FK (S6) : une FK reçue du client doit pointer vers
        # un enregistrement du MÊME propriétaire — sinon relation croisée entre comptes.
        _fks = list(ctx.fk_fields)
        def _fk_guard(indent: str) -> list[str]:
            out: list[str] = []
            for fk in _fks:
                _ro = _rel_owner(fk.related_model)
                out.append(f"{indent}if (data.{fk.field_name}) {{")
                out.append(
                    f"{indent}  const _owned_{fk.field_name} = await prisma.{fk.related_camel}.findFirst({{ where: {{ id: data.{fk.field_name}, {_ro}: {owner} }}, select: {{ id: true }} }})"
                )
                out.append(f"{indent}  if (!_owned_{fk.field_name}) throw new Error('Référence liée introuvable.')")
                out.append(f"{indent}}}")
            return out

        # ── Slug auto-généré (V7) : slugify du titre + suffixe anti-collision.
        # L'user ne saisit jamais le slug ; l'unicité globale est préservée pour les URLs.
        _slug_src = getattr(ctx, "slug_source", "")
        def _slug_lines(indent: str) -> list[str]:
            if not _slug_src:
                return []
            _norm = (
                f"String(data.{_slug_src} ?? '').toLowerCase().trim()"
                ".normalize('NFD').replace(/[\\u0300-\\u036f]/g, '')"
                ".replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '')"
                f" || '{camel}'"
            )
            return [
                f"{indent}const _slugBase = {_norm}",
                f"{indent}let _slug = _slugBase",
                f"{indent}for (let _i = 2; await prisma.{camel}.findUnique({{ where: {{ slug: _slug }}, select: {{ id: true }} }}); _i++) {{ _slug = `${{_slugBase}}-${{_i}}` }}",
            ]
        _slug_field = ", slug: _slug" if _slug_src else ""

        # ── Garde d'ownership M2M (S10) : ne connecter/set QUE les ids appartenant
        # au propriétaire — pré-filtrage en base, jamais de connexion cross-compte.
        _m2m = list(getattr(ctx, "m2m_fields", []) or [])
        def _m2m_prefetch(indent: str) -> list[str]:
            out: list[str] = []
            for mf in _m2m:
                _ro = _rel_owner(mf.related_model)
                out.append(f"{indent}const _valid_{mf.input_name} = {mf.input_name} && {mf.input_name}.length")
                out.append(
                    f"{indent}  ? (await prisma.{mf.related_camel}.findMany({{ where: {{ id: {{ in: {mf.input_name} }}, {_ro}: {owner} }}, select: {{ id: true }} }})).map(_r => _r.id)"
                )
                out.append(f"{indent}  : []")
            return out

        if _m2m:
            _destructure = ", ".join(mf.input_name for mf in _m2m)
            _connect_parts = ", ".join(
                f"...(_valid_{mf.input_name}.length ? {{ {mf.name}: {{ connect: _valid_{mf.input_name}.map(_id => ({{ id: _id }})) }} }} : {{}})"
                for mf in _m2m
            )
            _set_parts = ", ".join(
                f"...({mf.input_name} !== undefined ? {{ {mf.name}: {{ set: _valid_{mf.input_name}.map(_id => ({{ id: _id }})) }} }} : {{}})"
                for mf in _m2m
            )
            create_lines = [
                f"  create: async ({owner}: string, data: Create{name}Input): Promise<{serialized}> => {{",
                *_fk_guard("    "),
                *_slug_lines("    "),
                f"    const {{ {_destructure}, ...rest }} = data",
                *_m2m_prefetch("    "),
                f"    const result = await prisma.{camel}.create({{",
                f"      data: {{ ...rest, {owner}{_slug_field}, {_connect_parts} }}",
                "    })",
                "    return _serialize(result)",
                "  },",
            ]
            update_lines = [
                f"  update: async ({owner}: string, id: string, data: Update{name}Input): Promise<{serialized}> => {{",
                *_fk_guard("    "),
                f"    const {{ {_destructure}, ...rest }} = data",
                *_m2m_prefetch("    "),
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
                *_fk_guard("    "),
                *_slug_lines("    "),
                f"    const result = await prisma.{camel}.create({{",
                f"      data: {{ ...data, {owner}{_slug_field} }}",
                "    })",
                "    return _serialize(result)",
                "  },",
            ]
            update_lines = [
                f"  update: async ({owner}: string, id: string, data: Update{name}Input): Promise<{serialized}> => {{",
                *_fk_guard("    "),
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
