"""
agents/dev_service_generator.py
────────────────────────────────
Génération DÉTERMINISTE des fichiers lib/services/{model}.service.ts depuis ProjectSpec.

Chaque service expose 5 fonctions CRUD standard :
  getAll       — findMany filtré par owner_field
  getById      — findFirst par id + owner_field
  create       — create avec owner_field ajouté depuis auth()
  update       — update par id (pas d'owner check, la route le fait)
  remove       — delete par id + owner_field

Les champs DateTime du DTO (string ISO) sont convertis en Date avant Prisma.
Les enums Prisma sont castés via (rest as any) pour éviter les conflits de types.

Intégration dans dev_graph.py (après generate_types_file) :
    service_files = generate_service_files(spec_obj, project_workdir)
    template_written.update(service_files)
"""
from __future__ import annotations

import logging
import os
import re as _re

logger = logging.getLogger(__name__)

# Types Prisma qui sont des DateTime → nécessitent new Date() avant Prisma
_DATETIME_PRISMA_TYPES = {"DateTime"}


def _pascal_to_camel(name: str) -> str:
    """PascalCase → camelCase. Ex: LeaveRequest → leaveRequest"""
    return name[0].lower() + name[1:] if name else name


def _pascal_to_kebab(name: str) -> str:
    """PascalCase → kebab-case. Ex: LeaveRequest → leave-request"""
    return _re.sub(r"(?<!^)(?=[A-Z])", "-", name).lower()


def _is_auto_field(field_name: str, attributes: str) -> bool:
    attrs_lower = (attributes or "").lower()
    return (
        "@id" in attrs_lower
        or "@default(now())" in attrs_lower
        or "@updatedat" in attrs_lower.replace(" ", "")
        or field_name.lower() in {"id", "createdat", "updatedat", "deletedat"}
    )


def _is_relation_field(field_name: str, field_type: str, attributes: str) -> bool:
    if "@relation" in (attributes or ""):
        return True
    base = field_type.rstrip("?").rstrip("[]")
    from agents.dev_types_generator import _PRISMA_TO_TS
    if base in _PRISMA_TO_TS:
        return False
    return bool(base) and base[0].isupper()


def _get_datetime_fields(model) -> list[str]:
    """Retourne les noms de champs DateTime du modèle (hors auto-gérés)."""
    result = []
    owner = (model.owner_field or "userId").lower()
    for field in model.fields:
        if _is_auto_field(field.name, field.attributes):
            continue
        if field.name.lower() == owner:
            continue
        if _is_relation_field(field.name, field.type, field.attributes):
            continue
        base_type = field.type.rstrip("?").rstrip("[]")
        if base_type in _DATETIME_PRISMA_TYPES:
            result.append(field.name)
    return result


def _generate_service_for_model(model) -> str:
    """
    Génère le contenu complet du fichier .service.ts pour un modèle.
    Format : objet exporté nommé {camelCase}Service — pattern DAL standard.
    LLM-agnostic : le contrat est injecté dans le prompt de la route, pas deviné.
    """
    name = model.name                        # ex: LeaveRequest
    camel = _pascal_to_camel(name)           # ex: leaveRequest
    owner = model.owner_field or "userId"    # ex: userId

    date_fields = _get_datetime_fields(model)

    lines = [
        "// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER",
        "import prisma from '@/lib/prisma'",
        f"import type {{ {name} }} from '@prisma/client'",
        f"import type {{ Create{name}Input, Update{name}Input }} from '@/lib/types'",
        "",
        f"export const {camel}Service = {{",
        f"  getAll: ({owner}: string): Promise<{name}[]> =>",
        f"    prisma.{camel}.findMany({{ where: {{ {owner} }} }}),",
        "",
        f"  getById: ({owner}: string, id: string): Promise<{name} | null> =>",
        f"    prisma.{camel}.findFirst({{ where: {{ id, {owner} }} }}),",
        "",
        f"  create: async ({owner}: string, data: Create{name}Input): Promise<{name}> => {{",
    ]

    if date_fields:
        destruct_vars = ", ".join(date_fields)
        lines.append(f"    const {{ {destruct_vars}, ...rest }} = data")
        lines += [
            f"    return prisma.{camel}.create({{",
            "      data: {",
            "        ...(rest as any),",
            f"        {owner},",
        ]
        for df in date_fields:
            lines.append(f"        {df}: new Date({df}),")
        lines += ["      }", "    })"]
    else:
        lines += [
            f"    return prisma.{camel}.create({{",
            f"      data: {{ ...(data as any), {owner} }}",
            "    })",
        ]

    lines += [
        "  },",
        "",
        f"  update: async (id: string, data: Update{name}Input): Promise<{name}> => {{",
    ]

    if date_fields:
        destruct_vars = ", ".join(date_fields)
        lines.append(f"    const {{ {destruct_vars}, ...rest }} = data")
        lines += [
            f"    return prisma.{camel}.update({{",
            "      where: { id },",
            "      data: {",
            "        ...(rest as any),",
        ]
        for df in date_fields:
            lines.append(
                f"        ...({df} !== undefined ? {{ {df}: new Date({df}) }} : {{}}),"
            )
        lines += ["      }", "    })"]
    else:
        lines += [
            f"    return prisma.{camel}.update({{",
            "      where: { id },",
            "      data: { ...(data as any) }",
            "    })",
        ]

    lines += [
        "  },",
        "",
        f"  delete: async ({owner}: string, id: string): Promise<void> => {{",
        f"    await prisma.{camel}.delete({{ where: {{ id, {owner} }} }})",
        "  },",
        "}",
        "",
    ]

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
            logger.info("[service_generator] ✓ %s généré (%d modèle champs)", rel_path, len(model.fields))
        except Exception as e:
            logger.error("[service_generator] ✗ Erreur écriture %s : %s", rel_path, e)

    return written


def format_service_map_for_prompt(spec) -> str:
    """
    Génère un bloc compact (5 lignes/service) injectable dans le prompt LLM.
    Objectif : le LLM sait exactement quel objet importer et quelles méthodes appeler,
    sans lire le fichier entier — budget ~60 chars/méthode.

    Format injecté :
      ### Service Map (DAL pré-généré — NE PAS recréer)
      **projectService** → import { projectService } from '@/lib/services/project.service'
        .getAll(userId)  → Promise<Project[]>
        .getById(userId, id) → Promise<Project | null>
        .create(userId, data: CreateProjectInput) → Promise<Project>
        .update(id, data: UpdateProjectInput) → Promise<Project>
        .delete(userId, id) → Promise<void>
    """
    if not spec or not getattr(spec, "models", None):
        return ""

    lines = ["### Service Map (DAL pré-généré — NE PAS recréer ces fichiers)\n"]
    for model in spec.models:
        name = model.name
        camel = _pascal_to_camel(name)
        kebab = _pascal_to_kebab(name)
        owner = model.owner_field or "userId"
        import_path = f"@/lib/services/{kebab}.service"
        lines.append(f"**{camel}Service** → `import {{ {camel}Service }} from '{import_path}'`")
        lines.append(f"  .getAll({owner})  → `Promise<{name}[]>`")
        lines.append(f"  .getById({owner}, id)  → `Promise<{name} | null>`")
        lines.append(f"  .create({owner}, data: Create{name}Input)  → `Promise<{name}>`")
        lines.append(f"  .update(id, data: Update{name}Input)  → `Promise<{name}>`")
        lines.append(f"  .delete({owner}, id)  → `Promise<void>`")
        lines.append("")

    return "\n".join(lines)
