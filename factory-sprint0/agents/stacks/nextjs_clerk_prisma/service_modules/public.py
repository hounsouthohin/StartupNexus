"""getPublicById + getPublicAll — actif si le modèle a des pages publiques."""
from __future__ import annotations
from .base import ServiceMethodModule, MethodDecl, scalar_select_block, dt_inline_map

_VISIBILITY_NAMES = {"published", "ispublic", "is_public", "public", "visible", "isvisible"}
_PUBLISHED_LIKE = {"published", "active", "enabled", "approved", "public", "visible"}
_FUTURE_DATE_NAMES = {"date", "startdate", "startsat", "eventdate", "scheduledat", "duedate", "expiresat"}


class PublicModule(ServiceMethodModule):
    def should_activate(self, ctx) -> bool:
        return bool(ctx.has_public_pages)

    def methods_for(self, ctx) -> list[MethodDecl]:
        s = ctx.serialized_type
        # Le filtre appliqué par getPublicAll dépend du modèle — la note reflète le code
        # réellement émis ci-dessous (has_status → statut publié ; sinon Boolean visibilité).
        if ctx.has_status:
            _note = "  (sans owner, filtrée par statut publié)"
        elif getattr(ctx, "has_published_bool", False):
            _note = "  (sans owner, filtrée published=true)"
        else:
            _note = "  (sans owner)"
        return [
            MethodDecl("getPublicById", f"(id: string) → Promise<{s}>  (sans owner)"),
            MethodDecl("getPublicAll",  f"(page?: number, pageSize?: number) → Promise<{s}[]>{_note}"),
        ]

    def generate(self, ctx, **kwargs) -> list[str]:
        camel = ctx.camel
        serialized = ctx.serialized_type
        _sel = scalar_select_block(ctx)
        _map = dt_inline_map(ctx)

        # Ajouter les relations FK non-tableau dans le select de getPublicAll
        # → item.category?.name disponible dans les templates de liste publique
        # (les relations tableau comme resources[] sont exclues — trop coûteux pour une liste)
        all_contexts = kwargs.get("all_contexts") or {}
        _fk_only = [r for r in ctx.relation_fields if not r.is_array]
        if _fk_only:
            from .base import relation_nested_select
            _fk_sel = ", ".join(relation_nested_select(r, ctx, all_contexts) for r in _fk_only)
            _sel = _sel + ", " + _fk_sel

        # ── getPublicById — filtre de visibilité pour éviter l'IDOR ──────────
        _pub_by_id_filter = ""
        _vis_field_p = next(
            (f for f in ctx.model.fields
             if f.name.lower() in _VISIBILITY_NAMES
             and f.type.rstrip("?").rstrip("[]") == "Boolean"),
            None,
        )
        if _vis_field_p:
            _pub_by_id_filter = f", {_vis_field_p.name}: true"
        elif ctx.has_published_bool:
            _pub_by_id_filter = ", published: true"

        lines: list[str] = [
            "",
            f"  getPublicById: async (id: string): Promise<{serialized}> => {{",
            f"    const item = await prisma.{camel}.findUnique({{ where: {{ id{_pub_by_id_filter} }} }})",
            "    if (!item) notFound()",
            "    return _serialize(item)",
            "  },",
        ]

        # ── getPublicAll — filtre selon has_status / Boolean visibility / date ─
        if ctx.has_status:
            _sf = next((f for f in ctx.model.fields if f.name.lower() == "status"), None)
            _pval = "published"
            if _sf:
                _base = _sf.type.rstrip("?").rstrip("[]")
                _ev: list[str] = ctx.spec_enums.get(_base, [])
                _pval = next((v for v in _ev if v in _PUBLISHED_LIKE), _ev[0] if _ev else "published")
            lines += [
                "",
                f"  getPublicAll: async (page: number = 1, pageSize: number = 20): Promise<{serialized}[]> => {{",
                f"    const items = await prisma.{camel}.findMany({{ where: {{ status: '{_pval}' }}, select: {{ {_sel} }}, orderBy: {{ createdAt: 'desc' }}, take: pageSize, skip: (page - 1) * pageSize }})",
                f"    return items.map({_map}) as {serialized}[]",
                "  },",
            ]
        else:
            _where_parts: list[str] = []
            if _vis_field_p:
                _where_parts.append(f"{_vis_field_p.name}: true")
            elif ctx.has_published_bool:
                _where_parts.append("published: true")

            _date_field = next(
                (f for f in ctx.model.fields
                 if f.name.lower() in _FUTURE_DATE_NAMES
                 and f.type.rstrip("?").rstrip("[]") == "DateTime"
                 and not f.type.endswith("?")),
                None,
            )
            if _date_field:
                _where_parts.append(f"{_date_field.name}: {{ gte: new Date() }}")

            _pub_filter = f"where: {{ {', '.join(_where_parts)} }}, " if _where_parts else ""
            lines += [
                "",
                f"  getPublicAll: async (page: number = 1, pageSize: number = 20): Promise<{serialized}[]> => {{",
                f"    const items = await prisma.{camel}.findMany({{ {_pub_filter}select: {{ {_sel} }}, orderBy: {{ createdAt: 'desc' }}, take: pageSize, skip: (page - 1) * pageSize }})",
                f"    return items.map({_map}) as {serialized}[]",
                "  },",
            ]

        return lines
