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

from .dev_model_context import ModelGenerationContext, build_all_contexts

logger = logging.getLogger(__name__)


def _generate_service_for_model(ctx: ModelGenerationContext) -> str:
    """
    Génère le contenu complet du fichier .service.ts pour un modèle.

    Méthodes de lecture → retournent SerializedXxx (dates déjà string via _serialize).
    Méthodes d'écriture → retournent le type Prisma brut (appelées depuis Server Actions).
    Méthodes publiques (getPublished, getPublicAll, getPublicById) → générées UNIQUEMENT
    si ctx.has_public_pages est True.
    """
    name = ctx.name
    camel = ctx.camel
    owner = ctx.owner
    serialized = ctx.serialized_type
    dt_fields = ctx.datetime_fields
    relations = ctx.relation_fields

    lines = [
        "// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER",
        "import { notFound } from 'next/navigation'",
        "import prisma from '@/lib/prisma'",
        f"import type {{ {name} }} from '@prisma/client'",
        f"import type {{ Create{name}Input, Update{name}Input, {serialized} }} from '@/lib/types'",
        "",
    ]

    # _serialize : convertit les DateTime en string.
    # Toutes les méthodes de lecture passent par _serialize → TS2551 impossible.
    if dt_fields:
        serialize_lines = ["  ...item,"]
        for df in dt_fields:
            if df.is_nullable:
                serialize_lines.append(
                    f"  {df.name}: item.{df.name} ? item.{df.name}.toISOString() : null,"
                )
            else:
                serialize_lines.append(
                    f"  {df.name}: item.{df.name}.toISOString(),"
                )
        lines += [
            f"const _serialize = (item: {name}): {serialized} => ({{",
            *serialize_lines,
            f"}}) as {serialized}",
            "",
        ]
    else:
        lines += [
            f"const _serialize = (item: {name}): {serialized} => item as {serialized}",
            "",
        ]

    # ── getAll (privé — filtre owner) ─────────────────────────────────────────
    lines += [
        f"export const {camel}Service = {{",
        f"  getAll: async ({owner}: string, page: number = 1, pageSize: number = 20): Promise<{serialized}[]> => {{",
        f"    const items = await prisma.{camel}.findMany({{ where: {{ {owner} }}, orderBy: {{ createdAt: 'desc' }}, take: pageSize, skip: (page - 1) * pageSize }})",
        "    return items.map(_serialize)",
        "  },",
    ]

    # ── getPublished (public — filtre sur la valeur "active" de l'enum réel) ──
    # Généré UNIQUEMENT si le modèle a des pages publiques ET un champ status.
    # Utilise la vraie valeur "published-like" depuis ctx.spec_enums pour éviter
    # TS2322 quand l'enum n'a pas de valeur 'published' (ex: ["draft","archived"]).
    if ctx.has_public_pages and ctx.has_status:
        _PUBLISHED_LIKE = {"published", "active", "enabled", "approved", "public", "visible"}
        _status_field = next(
            (f for f in ctx.model.fields if f.name.lower() == "status"), None  # type: ignore[union-attr]
        )
        _published_val = "published"  # fallback
        if _status_field:
            _base = _status_field.type.rstrip("?").rstrip("[]")
            _enum_vals: list[str] = ctx.spec_enums.get(_base, [])
            _published_val = next(
                (v for v in _enum_vals if v in _PUBLISHED_LIKE),
                _enum_vals[0] if _enum_vals else "published",
            )
        lines += [
            "",
            f"  getPublished: async (): Promise<{serialized}[]> => {{",
            f"    const items = await prisma.{camel}.findMany({{ where: {{ status: '{_published_val}' }}, orderBy: {{ createdAt: 'desc' }}, take: 50, skip: 0 }})",
            "    return items.map(_serialize)",
            "  },",
        ]

    # ── getById (privé — filtre owner + id) ───────────────────────────────────
    lines += [
        "",
        f"  getById: async ({owner}: string, id: string): Promise<{serialized}> => {{",
        f"    const item = await prisma.{camel}.findFirst({{ where: {{ id, {owner} }} }})",
        "    if (!item) notFound()",
        "    return _serialize(item)",
        "  },",
    ]

    # ── getPublicById (public — sans filtre owner) ─────────────────────────────
    # Généré UNIQUEMENT si le modèle a des pages publiques.
    # Risque sécurité si généré pour un modèle privé : expose tous les enregistrements.
    if ctx.has_public_pages:
        lines += [
            "",
            f"  getPublicById: async (id: string): Promise<{serialized}> => {{",
            f"    const item = await prisma.{camel}.findUnique({{ where: {{ id }} }})",
            "    if (!item) notFound()",
            "    return _serialize(item)",
            "  },",
            "",
            f"  getPublicAll: async (): Promise<{serialized}[]> => {{",
            f"    const items = await prisma.{camel}.findMany({{ orderBy: {{ createdAt: 'desc' }}, take: 50, skip: 0 }})",
            "    return items.map(_serialize)",
            "  },",
        ]

    # ── getBySlug (public — champ slug @unique) ───────────────────────────────
    if ctx.has_slug:
        lines += [
            "",
            f"  getBySlug: async (slug: string): Promise<{serialized}> => {{",
            f"    const item = await prisma.{camel}.findUnique({{ where: {{ slug }} }})",
            "    if (!item) notFound()",
            "    return _serialize(item)",
            "  },",
        ]

    # ── getAllWithRelations (privé — include relations) ────────────────────────
    # JSON.parse/JSON.stringify sérialise les Date imbriquées dans les objets relation.
    # Le cast SerializedXxx[] est une approximation — les relations imbriquées ne sont
    # pas déclarées dans SerializedXxx mais existent dans les données runtime.
    if relations:
        include_block = ", ".join(f"{r.name}: true" for r in relations)
        lines += [
            "",
            f"  getAllWithRelations: async ({owner}: string): Promise<{serialized}[]> => {{",
            f"    const items = await prisma.{camel}.findMany({{ where: {{ {owner} }}, orderBy: {{ createdAt: 'desc' }}, take: 20, skip: 0, include: {{ {include_block} }} }})",
            f"    return JSON.parse(JSON.stringify(items)) as {serialized}[]",
            "  },",
        ]

    # ── create / update / delete ──────────────────────────────────────────────
    lines += [
        "",
        f"  create: async ({owner}: string, data: Create{name}Input): Promise<{name}> => {{",
        f"    return prisma.{camel}.create({{",
        f"      data: {{ ...data, {owner} }}",
        "    })",
        "  },",
        "",
        f"  update: async ({owner}: string, id: string, data: Update{name}Input): Promise<{name}> => {{",
        f"    return prisma.{camel}.update({{",
        f"      where: {{ id, {owner} }},",
        "      data: { ...data }",
        "    })",
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
) -> dict[str, str]:
    """
    Génère un fichier .service.ts par modèle Prisma et les écrit sur le disque.

    contexts : précalculé par build_all_contexts(spec) dans dev_graph.py.
               Si absent, calculé ici (compatibilité).
    Retourne {chemin_relatif: contenu} pour intégration dans template_written.
    """
    if contexts is None:
        contexts = build_all_contexts(spec)

    written: dict[str, str] = {}
    services_dir = os.path.join(project_workdir, "lib", "services")
    os.makedirs(services_dir, exist_ok=True)

    for model in spec.models:
        ctx = contexts[model.name]
        filename = f"{ctx.kebab}.service.ts"
        rel_path = f"lib/services/{filename}"
        content = _generate_service_for_model(ctx)

        abs_path = os.path.join(services_dir, filename)
        try:
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(content)
            written[rel_path] = content
            logger.info(
                "[service_generator] ✓ %s | public=%s slug=%s relations=%d",
                rel_path, ctx.has_public_pages, ctx.has_slug, len(ctx.relation_fields),
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
                f"avec include: {{ {rel_list} }}"
            )

        lines.append(f"  .create({ctx.owner}, data: Create{ctx.name}Input)  → `Promise<{ctx.name}>`")
        lines.append(f"  .update({ctx.owner}, id, data: Update{ctx.name}Input)  → `Promise<{ctx.name}>`")
        lines.append(f"  .delete({ctx.owner}, id)  → `Promise<void>`")
        lines.append("")

    return "\n".join(lines)
