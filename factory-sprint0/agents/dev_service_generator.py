"""
agents/dev_service_generator.py
────────────────────────────────
Génération DÉTERMINISTE des fichiers lib/services/{model}.service.ts depuis ProjectSpec.

Chaque service expose 5 fonctions CRUD standard :
  getAll       — findMany filtré par owner_field → SerializedXxx[] (dates string)
  getById      — findFirst par id + owner_field → SerializedXxx | null
  create       — create avec owner_field ajouté depuis auth() → Xxx (Prisma brut)
  update       — update par id → Xxx (Prisma brut)
  remove       — delete par id + owner_field → void

Les méthodes de lecture retournent SerializedXxx (dates DateTime déjà converties en string
via _serialize). Les méthodes d'écriture retournent le type Prisma brut car elles sont
appelées depuis les Server Actions, pas depuis les Client Components.

Intégration dans dev_graph.py (après generate_types_file) :
    service_files = generate_service_files(spec_obj, project_workdir)
    template_written.update(service_files)
"""
from __future__ import annotations

import logging
import os
import re as _re

logger = logging.getLogger(__name__)


def _pascal_to_camel(name: str) -> str:
    """PascalCase → camelCase. Ex: LeaveRequest → leaveRequest"""
    return name[0].lower() + name[1:] if name else name


def _pascal_to_kebab(name: str) -> str:
    """PascalCase → kebab-case. Ex: LeaveRequest → leave-request"""
    return _re.sub(r"(?<!^)(?=[A-Z])", "-", name).lower()


def _resolve_owner(model) -> str:
    """Délègue à model.resolved_owner() — SSoT dans PrismaModel."""
    return model.resolved_owner()


def _relation_fields(model) -> list[str]:
    """Retourne les noms des champs portant un @relation dans le modèle."""
    return [f.name for f in model.fields if "@relation" in (f.attributes or "")]


def _datetime_fields(model) -> list[tuple[str, bool]]:
    """Retourne les champs DateTime du modèle sous forme (nom, est_nullable)."""
    return [
        (f.name, f.type.endswith("?"))
        for f in model.fields
        if f.type.rstrip("?").rstrip("[]") == "DateTime"
    ]


def _generate_service_for_model(model) -> str:
    """
    Génère le contenu complet du fichier .service.ts pour un modèle.
    Les méthodes de lecture retournent SerializedXxx — dates déjà string via _serialize.
    Les méthodes d'écriture retournent le type Prisma brut (Server Actions, pas Client Components).
    """
    name = model.name
    camel = _pascal_to_camel(name)
    owner = _resolve_owner(model)
    relations = _relation_fields(model)
    serialized_name = f"Serialized{name}"
    dt_fields = _datetime_fields(model)

    lines = [
        "// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER",
        "import { notFound } from 'next/navigation'",
        "import prisma from '@/lib/prisma'",
        f"import type {{ {name} }} from '@prisma/client'",
        f"import type {{ Create{name}Input, Update{name}Input, {serialized_name} }} from '@/lib/types'",
        "",
    ]

    # Sérialiseur local — convertit les champs DateTime en string une seule fois.
    # Toutes les méthodes de lecture passent par lui → TS2551 impossible (string n'a pas .toISOString()).
    if dt_fields:
        serialize_lines = ["  ...item,"]
        for fname, nullable in dt_fields:
            if nullable:
                serialize_lines.append(f"  {fname}: item.{fname} ? item.{fname}.toISOString() : null,")
            else:
                serialize_lines.append(f"  {fname}: item.{fname}.toISOString(),")
        lines.extend([
            f"const _serialize = (item: {name}): {serialized_name} => ({{",
            *serialize_lines,
            f"}}) as {serialized_name}",
            "",
        ])
    else:
        lines.extend([
            f"const _serialize = (item: {name}): {serialized_name} => item as unknown as {serialized_name}",
            "",
        ])

    lines.extend([
        f"export const {camel}Service = {{",
        f"  getAll: async ({owner}: string): Promise<{serialized_name}[]> => {{",
        f"    const items = await prisma.{camel}.findMany({{ where: {{ {owner} }} }})",
        "    return items.map(_serialize)",
        "  },",
        "",
        f"  getById: async ({owner}: string, id: string): Promise<{serialized_name}> => {{",
        f"    const item = await prisma.{camel}.findFirst({{ where: {{ id, {owner} }} }})",
        "    if (!item) notFound()",
        "    return _serialize(item)",
        "  },",
    ])

    if relations:
        include_block = ", ".join(f"{r}: true" for r in relations)
        lines.extend([
            "",
            f"  getAllWithRelations: async ({owner}: string): Promise<{serialized_name}[]> => {{",
            f"    const items = await prisma.{camel}.findMany({{ where: {{ {owner} }}, include: {{ {include_block} }} }})",
            "    return items.map(_serialize)",
            "  },",
        ])

    lines.extend([
        "",
        f"  create: async ({owner}: string, data: Create{name}Input): Promise<{name}> => {{",
        f"    return prisma.{camel}.create({{",
        f"      data: {{ ...(data as any), {owner} }}",
        "    })",
        "  },",
        "",
        f"  update: async (id: string, data: Update{name}Input): Promise<{name}> => {{",
        f"    return prisma.{camel}.update({{",
        "      where: { id },",
        "      data: { ...(data as any) }",
        "    })",
        "  },",
        "",
        f"  delete: async ({owner}: string, id: string): Promise<void> => {{",
        f"    await prisma.{camel}.delete({{ where: {{ id, {owner} }} }})",
        "  },",
        "}",
        "",
    ])

    return "\n".join(lines)


def generate_service_files(spec, project_workdir: str) -> dict[str, str]:
    """
    Génère un fichier .service.ts par modèle Prisma et les écrit sur le disque.
    Retourne un dict {chemin_relatif: contenu} pour intégration dans template_written.
    """
    written: dict[str, str] = {}

    services_dir = os.path.join(project_workdir, "lib", "services")
    os.makedirs(services_dir, exist_ok=True)

    for model in spec.models:
        filename = f"{_pascal_to_kebab(model.name)}.service.ts"
        rel_path = f"lib/services/{filename}"
        content = _generate_service_for_model(model)

        abs_path = os.path.join(project_workdir, "lib", "services", filename)
        try:
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(content)
            written[rel_path] = content
            logger.info("[service_generator] ✓ %s généré (%d champs)", rel_path, len(model.fields))
        except Exception as e:
            logger.error("[service_generator] ✗ Erreur écriture %s : %s", rel_path, e)

    return written


def format_service_map_for_prompt(spec) -> str:
    """
    Génère un bloc compact (5 lignes/service) injectable dans le prompt LLM.
    Objectif : le LLM sait exactement quel objet importer et quelles méthodes appeler,
    sans lire le fichier entier — budget ~60 chars/méthode.
    """
    if not spec or not getattr(spec, "models", None):
        return ""

    lines = ["### Service Map (DAL pré-généré — NE PAS recréer ces fichiers)\n"]
    for model in spec.models:
        name = model.name
        camel = _pascal_to_camel(name)
        kebab = _pascal_to_kebab(name)
        owner = _resolve_owner(model)
        relations = _relation_fields(model)
        serialized_name = f"Serialized{name}"
        import_path = f"@/lib/services/{kebab}.service"
        lines.append(f"**{camel}Service** → `import {{ {camel}Service }} from '{import_path}'`")
        lines.append(f"  .getAll({owner})  → `Promise<{serialized_name}[]>` (dates déjà string)")
        lines.append(f"  .getById({owner}, id)  → `Promise<{serialized_name}>` (notFound() si absent — jamais null)")
        if relations:
            rel_list = ", ".join(relations)
            lines.append(
                f"  .getAllWithRelations({owner})  → `Promise<{serialized_name}[]>` avec include: {{ {rel_list} }}"
                f" ← UTILISER quand la page affiche des champs relationnels (ex: item.{relations[0]}.xxx)"
            )
        lines.append(f"  .create({owner}, data: Create{name}Input)  → `Promise<{name}>`")
        lines.append(f"  .update(id, data: Update{name}Input)  → `Promise<{name}>`")
        lines.append(f"  .delete({owner}, id)  → `Promise<void>`")
        lines.append("")

    return "\n".join(lines)
