"""
agents/dev_service_generator.py
────────────────────────────────
Génération DÉTERMINISTE des fichiers lib/services/{model}.service.ts depuis ProjectSpec.

Architecture assembler :
    _generate_service_for_model() itère SERVICE_MODULES (service_modules/__init__.py).
    Chaque module décide via should_activate(ctx) s'il génère des méthodes,
    puis retourne des lignes TypeScript via generate(ctx, **kwargs).

    Ajouter une nouvelle famille de méthodes = créer un module dans service_modules/,
    l'instancier dans SERVICE_MODULES. Aucune modification ici requise.

SÉCURITÉ : getPublicAll() et getPublicById() ne sont générés QUE si le modèle
a au moins une page publique (auth=False) dans la spec (guard dans public.py).

Intégration dans dev_graph.py :
    from .dev_model_context import build_all_contexts
    contexts = build_all_contexts(spec_obj)
    service_files = generate_service_files(spec_obj, project_workdir, contexts)
    template_written.update(service_files)
"""
from __future__ import annotations

import logging
import os

from .dev_model_context import ModelGenerationContext, build_all_contexts
from .service_modules import SERVICE_MODULES

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers header/serialize — partagés avec format_service_map_for_prompt
# ─────────────────────────────────────────────────────────────────────────────

def _build_serialize_fn(ctx: ModelGenerationContext) -> list[str]:
    """Génère la fonction _serialize pour les findFirst/findUnique (type Prisma complet).
    Convertit DateTime → ISO string ET Decimal → number (Prisma retourne un objet Decimal,
    jamais un number JS — sans Number(), TS2352 au build + crash de sérialisation RSC)."""
    name = ctx.name
    owner = ctx.owner
    serialized = ctx.serialized_type
    dt_fields = ctx.datetime_fields
    dec_fields = getattr(ctx, "decimal_fields", []) or []

    if dt_fields or dec_fields:
        conv_lines = []
        for df in dt_fields:
            if df.is_nullable:
                conv_lines.append(f"  {df.name}: rest.{df.name} ? rest.{df.name}.toISOString() : null,")
            else:
                conv_lines.append(f"  {df.name}: rest.{df.name}.toISOString(),")
        for dcf in dec_fields:
            if dcf.is_nullable:
                conv_lines.append(f"  {dcf.name}: rest.{dcf.name} != null ? Number(rest.{dcf.name}) : null,")
            else:
                conv_lines.append(f"  {dcf.name}: Number(rest.{dcf.name}),")
        return [
            f"const _serialize = (item: {name}): {serialized} => {{",
            f"  const {{ {owner}: _owner, ...rest }} = item",
            "  return ({",
            "    ...rest,",
            *conv_lines,
            f"  }}) as {serialized}",
            "}",
            "",
        ]
    return [
        f"const _serialize = (item: {name}): {serialized} => {{",
        f"  const {{ {owner}: _owner, ...rest }} = item",
        f"  return rest as {serialized}",
        "}",
        "",
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Custom queries (QueryDeclaration — depuis EnrichedSpec)
# ─────────────────────────────────────────────────────────────────────────────

def _compile_query(ctx: ModelGenerationContext, q) -> list[str]:
    """Compile une QueryDeclaration en méthode TypeScript."""
    from .service_modules.base import scalar_select_block, dt_inline_map

    name = ctx.name
    camel = ctx.camel
    owner = ctx.owner
    serialized = ctx.serialized_type
    _sel = scalar_select_block(ctx)
    _map = dt_inline_map(ctx)

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
        return [
            "",
            f"  {method_name}: async ({owner}: string, {param}: string): Promise<{ret_type}> => {{",
            f"    const item = await prisma.{camel}.{find_op}({{ where: {{ {owner}, {q.field}: {param} }}, select: {{ {_sel} }}, orderBy: {{ createdAt: 'desc' }}, take: 1 }})",
            "    if (!item) notFound()",
            f"    return ({_map})(item) as {ret_type}",
            "  },",
        ]

    if q.pattern == "search_text":
        return [
            "",
            f"  {method_name}: async ({owner}: string, q: string, page: number = 1, pageSize: number = 20): Promise<{ret_type}> => {{",
            f"    const items = await prisma.{camel}.findMany({{ where: {{ {owner}, {q.field}: {{ contains: q, mode: 'insensitive' }} }}, select: {{ {_sel} }}, orderBy: {{ createdAt: 'desc' }}, take: pageSize, skip: (page - 1) * pageSize }})",
            f"    return items.map({_map}) as {ret_type}",
            "  },",
        ]

    if q.pattern == "count_by_field":
        return [
            "",
            f"  {method_name}: async ({owner}: string): Promise<{{ {q.field}: string, count: number }}[]> => {{",
            f"    const rows = await prisma.{camel}.groupBy({{ by: ['{q.field}'], where: {{ {owner} }}, _count: {{ _all: true }} }})",
            f"    return rows.map(r => ({{ {q.field}: r.{q.field} as string, count: r._count._all }}))",
            "  },",
        ]

    if q.pattern == "filter_by_relation":
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


# ─────────────────────────────────────────────────────────────────────────────
# Assembler principal
# ─────────────────────────────────────────────────────────────────────────────

def _generate_service_for_model(
    ctx: ModelGenerationContext,
    all_contexts: "dict | None" = None,
    required_queries: "list | None" = None,
) -> str:
    """
    Génère le contenu complet du fichier .service.ts pour un modèle.

    Délègue la génération des méthodes à SERVICE_MODULES (assembler pattern).
    Ce fichier ne contient plus la logique de génération — il orchestre seulement.

    CONTRAT : toute méthode ajoutée dans un module doit aussi être déclarée dans
    dev_service_spec.py::build_service_spec() pour le manifest et la doc LLM.
    """
    name = ctx.name
    camel = ctx.camel
    serialized = ctx.serialized_type

    header = [
        "// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER",
        "import { notFound } from 'next/navigation'",
        "import prisma from '@/lib/prisma'",
        f"import type {{ {name} }} from '@prisma/client'",
        f"import type {{ Create{name}Input, Update{name}Input, {serialized} }} from '@/lib/types'",
        "",
    ]

    serialize_fn = _build_serialize_fn(ctx)

    # Corps du service object — assemblé par les modules actifs
    body: list[str] = [f"export const {camel}Service = {{"]
    for module in SERVICE_MODULES:
        if module.should_activate(ctx):
            body += module.generate(ctx, all_contexts=all_contexts or {})

    # Custom queries depuis EnrichedSpec (ne font pas partie des modules standards)
    for q in (required_queries or []):
        body += _compile_query(ctx, q)

    body += ["}", ""]

    return "\n".join(header + serialize_fn + body)


# ─────────────────────────────────────────────────────────────────────────────
# Entry points publics
# ─────────────────────────────────────────────────────────────────────────────

def generate_service_files(
    spec,
    project_workdir: str,
    contexts: "dict[str, ModelGenerationContext] | None" = None,
    enriched_spec=None,
) -> dict[str, str]:
    """
    Génère un fichier .service.ts par modèle Prisma et les écrit sur le disque.

    contexts      : précalculé par build_all_contexts(spec) dans dev_graph.py.
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

        model_queries = []
        if enriched_spec and getattr(enriched_spec, "required_queries", None):
            model_queries = [q for q in enriched_spec.required_queries if q.model == ctx.name]

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

    Décisions "quelles méthodes existent" → déléguées à build_service_spec().
    Formatage "comment les présenter au LLM" → ici, avec le détail des relations.
    """
    from .dev_service_spec import build_service_spec

    if not spec or not getattr(spec, "models", None):
        return ""

    if contexts is None:
        contexts = build_all_contexts(spec)

    lines = ["### Service Map (DAL pré-généré — NE PAS recréer ces fichiers)\n"]

    for model in spec.models:
        ctx = contexts[model.name]
        svc = build_service_spec(ctx)
        import_path = f"@/lib/services/{svc.kebab}.service"
        rel_list = ", ".join(r.name for r in ctx.relation_fields) if ctx.relation_fields else ""

        lines.append(f"**{svc.camel}Service** → `import {{ {svc.camel}Service }} from '{import_path}'`")

        for m in svc.methods:
            if m.name == "getAll":
                lines.append(f"  .{m.name}({svc.owner}, page?)  → `Promise<{svc.serialized}[]>` (dates déjà string, paginé)")
            elif m.name.startswith("getBy") and m.name.endswith("Id") and m.name != "getById":
                lines.append(f"  .{m.name}(userId, ...)  → `Promise<{svc.serialized}[]>` enfants d'un parent — **CROSS_ENTITY**")
            elif m.name == "getPublished":
                lines.append(f"  .{m.name}()  → `Promise<{svc.serialized}[]>` SANS userId — pages publiques status='published'")
            elif m.name == "getById":
                lines.append(f"  .{m.name}({svc.owner}, id)  → `Promise<{svc.serialized}>` (notFound() si absent)")
            elif m.name == "getPublicById":
                lines.append(f"  .{m.name}(id)  → `Promise<{svc.serialized}>` SANS owner — pages détail publiques")
            elif m.name == "getPublicAll":
                lines.append(f"  .{m.name}()  → `Promise<{svc.serialized}[]>` SANS owner — fetch FK options publiques")
            elif m.name == "getBySlug":
                lines.append(f"  .{m.name}(slug)  → `Promise<{svc.serialized}>` par slug — pages detail-slug")
            elif m.name == "getBySlugOwned":
                lines.append(f"  .{m.name}({svc.owner}, slug)  → `Promise<{svc.serialized}>`")
            elif m.name == "getAllWithRelations":
                lines.append(f"  .{m.name}({svc.owner}, page?)  → `Promise<{svc.serialized}[]>` avec relations: {{ {rel_list} }}")
            elif m.name == "getByIdWithRelations":
                lines.append(f"  .{m.name}({svc.owner}, id)  → `Promise<{svc.serialized}>` avec relations: {{ {rel_list} }}")
            elif m.name == "getPublicByIdWithRelations":
                lines.append(f"  .{m.name}(id)  → `Promise<{svc.serialized}>` SANS owner, avec relations: {{ {rel_list} }}")
            elif m.name == "getBySlugWithRelations":
                lines.append(f"  .{m.name}(slug)  → `Promise<{svc.serialized}>` par slug, avec relations: {{ {rel_list} }}")
            elif m.name in ("create", "update", "delete"):
                lines.append(f"  .{m.name}(...)  → {m.sig.split('→')[-1].strip()}")
            else:
                lines.append(f"  .{m.name}(...)  → {m.sig.split('→')[-1].strip()}")

        lines.append("")

    return "\n".join(lines)
