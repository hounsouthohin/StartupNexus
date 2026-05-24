"""
agents/dev_service_generator.py
────────────────────────────────
Génération DÉTERMINISTE des fichiers lib/services/{model}.service.ts depuis ProjectSpec.

Chaque service expose des fonctions CRUD standard dont la présence dépend
du ModelGenerationContext (flags has_public_pages, has_slug, has_relations).

SÉCURITÉ : getPublicAll() et getPublicById() ne sont générés QUE si le modèle
a au moins une page publique (auth=False) dans la spec. Sans ce guard, ces méthodes
exposeront tous les enregistrements sans filtre owner si le LLM les utilise sur un
modèle admin-only.

Intégration dans dev_graph.py (après generate_types_file) :
    from .dev_model_context import build_all_contexts
    contexts = build_all_contexts(spec_obj)
    service_files = generate_service_files(spec_obj, project_workdir, contexts)
    template_written.update(service_files)
"""
from __future__ import annotations

import logging
import os

from .dev_model_context import ModelGenerationContext, RelationFieldInfo, build_all_contexts

logger = logging.getLogger(__name__)


def _scalar_select_block(ctx: ModelGenerationContext) -> str:
    """Prisma select block pour les champs scalaires uniquement (exclut owner, relations, tableaux)."""
    parts = []
    for f in ctx.model.fields:
        if f.name == ctx.owner:
            continue
        if "@relation" in (f.attributes or ""):
            continue
        if f.type.endswith("[]"):
            continue
        parts.append(f"{f.name}: true")
    return ", ".join(parts)


def _dt_inline_map(ctx: ModelGenerationContext) -> str:
    """
    Map function TypeScript inline : convertit les champs DateTime en ISO string.
    Utilisé pour les findMany avec select (owner exclu du résultat — _serialize inapplicable).
    """
    dt_parts = []
    for df in ctx.datetime_fields:
        if df.name == ctx.owner:
            continue
        if df.is_nullable:
            dt_parts.append(f"{df.name}: item.{df.name} ? item.{df.name}.toISOString() : null")
        else:
            dt_parts.append(f"{df.name}: item.{df.name}.toISOString()")
    if not dt_parts:
        return "item => item"
    return "item => ({ ...item, " + ", ".join(dt_parts) + " })"


def _relation_nested_select(r: "RelationFieldInfo", ctx: "ModelGenerationContext", all_contexts: dict) -> str:
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


def _compile_query(ctx: ModelGenerationContext, q) -> list[str]:
    """
    Compile une QueryDeclaration en méthode TypeScript.
    Retourne les lignes à insérer dans le service object, ou [] si pattern inconnu.
    """
    name = ctx.name
    camel = ctx.camel
    owner = ctx.owner
    serialized = ctx.serialized_type
    _sel = _scalar_select_block(ctx)
    _map = _dt_inline_map(ctx)

    method_name = q.name or f"getBy{q.field[0].upper() + q.field[1:] if q.field else 'Unknown'}"
    param = q.param_name or (q.field if q.field else "value")
    ret_type = f"{serialized}[]" if q.return_many else serialized
    find_op = "findMany" if q.return_many else "findFirst"

    if q.pattern == "filter_by_field":
        if q.return_many:
            return [
                "",
                f"  {method_name}: async ({owner}: string, {param}: string, page: number = 1, pageSize: number = 20): Promise<{ret_type}> => {{",
                f"    const items = await prisma.{camel}.{find_op}({{ where: {{ {owner}, {q.field}: {param} }}, select: {{ {_sel} }}, orderBy: {{ createdAt: 'desc' }}, take: pageSize, skip: (page - 1) * pageSize }})",
                f"    return items.map({_map}) as {ret_type}",
                "  },",
            ]
        else:
            return [
                "",
                f"  {method_name}: async ({owner}: string, {param}: string): Promise<{ret_type}> => {{",
                f"    const item = await prisma.{camel}.{find_op}({{ where: {{ {owner}, {q.field}: {param} }}, select: {{ {_sel} }}, orderBy: {{ createdAt: 'desc' }}, take: 1 }})",
                "    if (!item) notFound()",
                f"    return ({_map})(item) as {ret_type}",
                "  },",
            ]

    elif q.pattern == "search_text":
        return [
            "",
            f"  {method_name}: async ({owner}: string, q: string, page: number = 1, pageSize: number = 20): Promise<{ret_type}> => {{",
            f"    const items = await prisma.{camel}.findMany({{ where: {{ {owner}, {q.field}: {{ contains: q, mode: 'insensitive' }} }}, select: {{ {_sel} }}, orderBy: {{ createdAt: 'desc' }}, take: pageSize, skip: (page - 1) * pageSize }})",
            f"    return items.map({_map}) as {ret_type}",
            "  },",
        ]

    elif q.pattern == "count_by_field":
        return [
            "",
            f"  {method_name}: async ({owner}: string): Promise<{{ {q.field}: string, count: number }}[]> => {{",
            f"    const rows = await prisma.{camel}.groupBy({{ by: ['{q.field}'], where: {{ {owner} }}, _count: {{ _all: true }} }})",
            f"    return rows.map(r => ({{ {q.field}: r.{q.field} as string, count: r._count._all }}))",
            "  },",
        ]

    elif q.pattern == "filter_by_relation":
        # field = FK field like "assigneeId" → relation "assignee", param "assigneeId"
        rel = q.field[:-2] if q.field.endswith("Id") else q.field
        return [
            "",
            f"  {method_name}: async ({owner}: string, {param}: string, page: number = 1, pageSize: number = 20): Promise<{ret_type}> => {{",
            f"    const items = await prisma.{camel}.findMany({{ where: {{ {owner}, {rel}: {{ id: {param} }} }}, select: {{ {_sel} }}, orderBy: {{ createdAt: 'desc' }}, take: pageSize, skip: (page - 1) * pageSize }})",
            f"    return items.map({_map}) as {ret_type}",
            "  },",
        ]

    logger.warning("[service_generator] pattern inconnu '%s' pour query '%s' — ignoré", q.pattern, method_name)
    return []


def _generate_service_for_model(ctx: ModelGenerationContext, all_contexts: "dict | None" = None, required_queries: "list | None" = None) -> str:
    """
    Génère le contenu complet du fichier .service.ts pour un modèle.

    findMany → select explicite (Z25 : évite l'over-fetching).
    findFirst / findUnique → pas de select, passent par _serialize (types Prisma complets).
    getAllWithRelations → select scalaires + nested select par relation (remplace include).
    """
    name = ctx.name
    camel = ctx.camel
    owner = ctx.owner
    serialized = ctx.serialized_type
    dt_fields = ctx.datetime_fields
    relations = ctx.relation_fields

    # Pré-calculés une fois, utilisés par tous les findMany scalaires
    _sel = _scalar_select_block(ctx)
    _map = _dt_inline_map(ctx)

    lines = [
        "// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER",
        "import { notFound } from 'next/navigation'",
        "import prisma from '@/lib/prisma'",
        f"import type {{ {name} }} from '@prisma/client'",
        f"import type {{ Create{name}Input, Update{name}Input, {serialized} }} from '@/lib/types'",
        "",
    ]

    # _serialize : pour findFirst / findUnique (pas de select → type Prisma complet).
    # Exclut owner, convertit DateTime → string.
    if dt_fields:
        dt_lines = []
        for df in dt_fields:
            if df.is_nullable:
                dt_lines.append(
                    f"  {df.name}: rest.{df.name} ? rest.{df.name}.toISOString() : null,"
                )
            else:
                dt_lines.append(
                    f"  {df.name}: rest.{df.name}.toISOString(),"
                )
        lines += [
            f"const _serialize = (item: {name}): {serialized} => {{",
            f"  const {{ {owner}: _owner, ...rest }} = item",
            f"  return ({{",
            "    ...rest,",
            *dt_lines,
            f"  }}) as {serialized}",
            f"}}",
            "",
        ]
    else:
        lines += [
            f"const _serialize = (item: {name}): {serialized} => {{",
            f"  const {{ {owner}: _owner, ...rest }} = item",
            f"  return rest as {serialized}",
            f"}}",
            "",
        ]

    # Détecte les modèles enfants (owner = FK parent comme projectId, pas userId/authorId)
    _is_child_model = owner not in ('userId', 'authorId')
    _parent_relation = owner[:-2] if _is_child_model and owner.endswith("Id") else ""

    # ── getAll (privé — select scalaires, filtre owner) ───────────────────────
    lines += [
        f"export const {camel}Service = {{",
        f"  getAll: async ({owner}: string, page: number = 1, pageSize: number = 20): Promise<{serialized}[]> => {{",
        f"    const items = await prisma.{camel}.findMany({{ where: {{ {owner} }}, select: {{ {_sel} }}, orderBy: {{ createdAt: 'desc' }}, take: pageSize, skip: (page - 1) * pageSize }})",
        f"    return items.map({_map}) as {serialized}[]",
        "  },",
    ]

    # ── getAllByUser (modèles enfants — filtre via relation parent) ──────────
    # Généré uniquement pour les modèles enfants (owner = parentId).
    # Permet aux pages liste de fetcher par userId sans connaître le parentId.
    if _is_child_model and _parent_relation:
        lines += [
            "",
            f"  getAllByUser: async (userId: string, page: number = 1, pageSize: number = 20): Promise<{serialized}[]> => {{",
            f"    const items = await prisma.{camel}.findMany({{ where: {{ {_parent_relation}: {{ userId }} }}, select: {{ {_sel} }}, orderBy: {{ createdAt: 'desc' }}, take: pageSize, skip: (page - 1) * pageSize }})",
            f"    return items.map({_map}) as {serialized}[]",
            "  },",
        ]

    # ── getPublished (public — select scalaires, filtre sur valeur "active" de l'enum) ──
    if ctx.has_public_pages and ctx.has_status:
        _PUBLISHED_LIKE = {"published", "active", "enabled", "approved", "public", "visible"}
        _status_field = next(
            (f for f in ctx.model.fields if f.name.lower() == "status"), None  # type: ignore[union-attr]
        )
        _published_val = "published"
        if _status_field:
            _base = _status_field.type.rstrip("?").rstrip("[]")
            _enum_vals: list[str] = ctx.spec_enums.get(_base, [])
            _published_val = next(
                (v for v in _enum_vals if v in _PUBLISHED_LIKE),
                _enum_vals[0] if _enum_vals else "published",
            )
        lines += [
            "",
            f"  getPublished: async (page: number = 1, pageSize: number = 20): Promise<{serialized}[]> => {{",
            f"    const items = await prisma.{camel}.findMany({{ where: {{ status: '{_published_val}' }}, select: {{ {_sel} }}, orderBy: {{ createdAt: 'desc' }}, take: pageSize, skip: (page - 1) * pageSize }})",
            f"    return items.map({_map}) as {serialized}[]",
            "  },",
        ]

    # ── getById (privé — findFirst sans select → _serialize) ──────────────────
    lines += [
        "",
        f"  getById: async ({owner}: string, id: string): Promise<{serialized}> => {{",
        f"    const item = await prisma.{camel}.findFirst({{ where: {{ id, {owner} }} }})",
        "    if (!item) notFound()",
        "    return _serialize(item)",
        "  },",
    ]

    # ── getPublicById + getPublicAll (public — sans filtre owner) ─────────────
    if ctx.has_public_pages:
        lines += [
            "",
            f"  getPublicById: async (id: string): Promise<{serialized}> => {{",
            f"    const item = await prisma.{camel}.findUnique({{ where: {{ id }} }})",
            "    if (!item) notFound()",
            "    return _serialize(item)",
            "  },",
        ]
        if ctx.has_status:
            # Filtre par statut publié pour éviter l'exposition de brouillons entre utilisateurs
            _PUBLISHED_LIKE_P = {"published", "active", "enabled", "approved", "public", "visible"}
            _sf_p = next((f for f in ctx.model.fields if f.name.lower() == "status"), None)
            _pval = "published"
            if _sf_p:
                _base_p = _sf_p.type.rstrip("?").rstrip("[]")
                _ev_p: list[str] = ctx.spec_enums.get(_base_p, [])
                _pval = next((v for v in _ev_p if v in _PUBLISHED_LIKE_P), _ev_p[0] if _ev_p else "published")
            lines += [
                "",
                f"  getPublicAll: async (page: number = 1, pageSize: number = 20): Promise<{serialized}[]> => {{",
                f"    const items = await prisma.{camel}.findMany({{ where: {{ status: '{_pval}' }}, select: {{ {_sel} }}, orderBy: {{ createdAt: 'desc' }}, take: pageSize, skip: (page - 1) * pageSize }})",
                f"    return items.map({_map}) as {serialized}[]",
                "  },",
            ]
        else:
            # Filtre Boolean published si présent — évite d'exposer les records non publiés.
            _pub_filter = "where: { published: true }, " if getattr(ctx, "has_published_bool", False) else ""
            lines += [
                "",
                f"  getPublicAll: async (page: number = 1, pageSize: number = 20): Promise<{serialized}[]> => {{",
                f"    const items = await prisma.{camel}.findMany({{ {_pub_filter}select: {{ {_sel} }}, orderBy: {{ createdAt: 'desc' }}, take: pageSize, skip: (page - 1) * pageSize }})",
                f"    return items.map({_map}) as {serialized}[]",
                "  },",
            ]

    # ── getBySlug (public — findUnique sans select → _serialize) ──────────────
    if ctx.has_slug:
        lines += [
            "",
            f"  getBySlug: async (slug: string): Promise<{serialized}> => {{",
            f"    const item = await prisma.{camel}.findUnique({{ where: {{ slug }} }})",
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

    # ── getAllWithRelations + getByIdWithRelations (privé — nested select) ───────
    # Remplace include:{rel: true} par select imbriqué → types Prisma exacts, Z25 conforme.
    if relations:
        _scalar_parts = [
            f"{f.name}: true" for f in ctx.model.fields
            if f.name != ctx.owner
            and "@relation" not in (f.attributes or "")
            and not f.type.endswith("[]")
        ]
        _rel_parts = [_relation_nested_select(r, ctx, all_contexts or {}) for r in relations]
        _rel_sel = ", ".join(_scalar_parts + _rel_parts)
        lines += [
            "",
            f"  getAllWithRelations: async ({owner}: string, page: number = 1, pageSize: number = 20): Promise<{serialized}[]> => {{",
            f"    const items = await prisma.{camel}.findMany({{ where: {{ {owner} }}, select: {{ {_rel_sel} }}, orderBy: {{ createdAt: 'desc' }}, take: pageSize, skip: (page - 1) * pageSize }})",
            f"    return items.map({_map}) as {serialized}[]",
            "  },",
            "",
            f"  getByIdWithRelations: async ({owner}: string, id: string): Promise<{serialized}> => {{",
            f"    const item = await prisma.{camel}.findFirst({{ where: {{ id, {owner} }}, select: {{ {_rel_sel} }} }})",
            "    if (!item) notFound()",
            f"    return ({_map})(item) as {serialized}",
            "  },",
        ]

    # ── getPublicByIdWithRelations (public — nested select, sans filtre owner) ──
    if ctx.has_public_pages and relations:
        lines += [
            "",
            f"  getPublicByIdWithRelations: async (id: string): Promise<{serialized}> => {{",
            f"    const item = await prisma.{camel}.findUnique({{ where: {{ id }}, select: {{ {_rel_sel} }} }})",
            "    if (!item) notFound()",
            f"    return ({_map})(item) as {serialized}",
            "  },",
        ]

    # ── getBySlugWithRelations (public — nested select par slug) ──────────────
    if ctx.has_slug and relations:
        lines += [
            "",
            f"  getBySlugWithRelations: async (slug: string): Promise<{serialized}> => {{",
            f"    const item = await prisma.{camel}.findUnique({{ where: {{ slug }}, select: {{ {_rel_sel} }} }})",
            "    if (!item) notFound()",
            f"    return ({_map})(item) as {serialized}",
            "  },",
        ]

    # ── Queries métier custom (depuis EnrichedSpec.required_queries) ─────────
    for q in (required_queries or []):
        lines += _compile_query(ctx, q)

    # ── create / update / delete ──────────────────────────────────────────────
    lines += [
        "",
        f"  create: async ({owner}: string, data: Create{name}Input): Promise<{serialized}> => {{",
        f"    const result = await prisma.{camel}.create({{",
        f"      data: {{ ...data, {owner} }}",
        "    })",
        "    return _serialize(result)",
        "  },",
        "",
        f"  update: async ({owner}: string, id: string, data: Update{name}Input): Promise<{serialized}> => {{",
        f"    const result = await prisma.{camel}.update({{",
        f"      where: {{ id, {owner} }},",
        "      data: { ...data }",
        "    })",
        "    return _serialize(result)",
        "  },",
        "",
        f"  delete: async ({owner}: string, id: string): Promise<void> => {{",
        f"    await prisma.{camel}.delete({{ where: {{ id, {owner} }} }})",
        "  },",
        "}",
        "",
    ]

    return "\n".join(lines)


def generate_service_files(
    spec,
    project_workdir: str,
    contexts: "dict[str, ModelGenerationContext] | None" = None,
    enriched_spec=None,
) -> dict[str, str]:
    """
    Génère un fichier .service.ts par modèle Prisma et les écrit sur le disque.

    contexts      : précalculé par build_all_contexts(spec) dans dev_graph.py.
                    Si absent, calculé ici (compatibilité).
    enriched_spec : EnrichedSpec optionnel — injecte les required_queries custom.
    Retourne {chemin_relatif: contenu} pour intégration dans template_written.
    """
    if contexts is None:
        contexts = build_all_contexts(spec)

    written: dict[str, str] = {}
    services_dir = os.path.join(project_workdir, "lib", "services")
    os.makedirs(services_dir, exist_ok=True)

    for model in spec.models:
        ctx = contexts[model.name]

        # Filtre les queries déclarées pour ce modèle spécifique
        model_queries = []
        if enriched_spec and getattr(enriched_spec, "required_queries", None):
            model_queries = [
                q for q in enriched_spec.required_queries
                if q.model == ctx.name
            ]

        filename = f"{ctx.kebab}.service.ts"
        rel_path = f"lib/services/{filename}"
        content = _generate_service_for_model(ctx, all_contexts=contexts, required_queries=model_queries)

        abs_path = os.path.join(services_dir, filename)
        try:
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(content)
            written[rel_path] = content
            logger.info(
                "[service_generator] ✓ %s | public=%s slug=%s relations=%d queries=%d",
                rel_path, ctx.has_public_pages, ctx.has_slug, len(ctx.relation_fields), len(model_queries),
            )
        except Exception as e:
            logger.error("[service_generator] ✗ %s : %s", rel_path, e)

    return written


def format_service_map_for_prompt(spec, contexts: "dict[str, ModelGenerationContext] | None" = None) -> str:
    """
    Génère un bloc compact injectable dans le prompt LLM.
    Le LLM connaît le contrat exact de chaque service avant d'écrire les pages.
    """
    if not spec or not getattr(spec, "models", None):
        return ""

    if contexts is None:
        contexts = build_all_contexts(spec)

    lines = ["### Service Map (DAL pré-généré — NE PAS recréer ces fichiers)\n"]

    for model in spec.models:
        ctx = contexts[model.name]
        import_path = f"@/lib/services/{ctx.kebab}.service"

        lines.append(f"**{ctx.camel}Service** → `import {{ {ctx.camel}Service }} from '{import_path}'`")
        lines.append(f"  .getAll({ctx.owner}, page?)  → `Promise<{ctx.serialized_type}[]>` (dates déjà string, paginé)")

        if ctx.has_public_pages and ctx.has_status:
            lines.append(
                f"  .getPublished()  → `Promise<{ctx.serialized_type}[]>` SANS userId "
                "— pages publiques status='published'"
            )

        lines.append(
            f"  .getById({ctx.owner}, id)  → `Promise<{ctx.serialized_type}>` (notFound() si absent)"
        )

        if ctx.has_public_pages:
            lines.append(
                f"  .getPublicById(id)  → `Promise<{ctx.serialized_type}>` SANS owner — pages détail publiques"
            )
            lines.append(
                f"  .getPublicAll()  → `Promise<{ctx.serialized_type}[]>` SANS owner — fetch FK options publiques"
            )

        if ctx.has_slug:
            lines.append(
                f"  .getBySlug(slug)  → `Promise<{ctx.serialized_type}>` par slug — pages detail-slug"
            )

        if ctx.relation_fields:
            rel_list = ", ".join(r.name for r in ctx.relation_fields)
            lines.append(
                f"  .getAllWithRelations({ctx.owner})  → `Promise<{ctx.serialized_type}[]>` "
                f"avec relations: {{ {rel_list} }}"
            )
            lines.append(
                f"  .getByIdWithRelations({ctx.owner}, id)  → `Promise<{ctx.serialized_type}>` "
                f"avec relations: {{ {rel_list} }}"
            )
            if ctx.has_public_pages:
                lines.append(
                    f"  .getPublicByIdWithRelations(id)  → `Promise<{ctx.serialized_type}>` SANS owner, "
                    f"avec relations: {{ {rel_list} }}"
                )
            if ctx.has_slug:
                lines.append(
                    f"  .getBySlugWithRelations(slug)  → `Promise<{ctx.serialized_type}>` par slug, "
                    f"avec relations: {{ {rel_list} }}"
                )

        lines.append(f"  .create({ctx.owner}, data: Create{ctx.name}Input)  → `Promise<{ctx.name}>`")
        lines.append(f"  .update({ctx.owner}, id, data: Update{ctx.name}Input)  → `Promise<{ctx.name}>`")
        lines.append(f"  .delete({ctx.owner}, id)  → `Promise<void>`")
        lines.append("")

    return "\n".join(lines)
