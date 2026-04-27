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


def _plural_camel(name: str) -> str:
    """Forme plurielle simple pour les noms de fonctions. Ex: project → projects"""
    camel = _pascal_to_camel(name)
    return camel + "s"


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
    """Génère le contenu complet du fichier .service.ts pour un modèle."""
    name = model.name                        # ex: LeaveRequest
    camel = _pascal_to_camel(name)           # ex: leaveRequest
    plural = _plural_camel(name)             # ex: leaveRequests
    owner = model.owner_field or "userId"    # ex: userId

    date_fields = _get_datetime_fields(model)

    # ── Bloc de conversion dates pour create ─────────────────────────
    # Destructure les champs date hors du spread pour éviter le conflit string/Date
    if date_fields:
        destruct_vars = ", ".join(date_fields)
        create_destruct = f"  const {{ {destruct_vars}, ...rest }} = data\n"
        create_data_fields = "      ...(rest as any),\n"
        create_data_fields += f"      {owner},\n"
        for df in date_fields:
            create_data_fields += f"      {df}: new Date({df}),\n"
    else:
        create_destruct = ""
        create_data_fields = f"      ...(data as any),\n      {owner},\n"

    # ── Bloc de conversion dates pour update (champs optionnels) ──────
    if date_fields:
        update_destruct_vars = ", ".join(date_fields)
        update_destruct = f"  const {{ {update_destruct_vars}, ...rest }} = data\n"
        update_data_fields = "      ...(rest as any),\n"
        for df in date_fields:
            update_data_fields += (
                f"      ...({df} !== undefined ? {{ {df}: new Date({df}) }} : {{}}),\n"
            )
    else:
        update_destruct = ""
        update_data_fields = "      ...(data as any),\n"

    lines = [
        "// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER",
        "import prisma from '@/lib/prisma'",
        f"import type {{ {name} }} from '@prisma/client'",
        f"import type {{ Create{name}Input, Update{name}Input }} from '@/lib/types'",
        "",
        f"export async function get{name}s({owner}: string): Promise<{name}[]> {{",
        f"  return prisma.{camel}.findMany({{ where: {{ {owner} }} }})",
        "}",
        "",
        f"export async function get{name}ById({owner}: string, id: string): Promise<{name} | null> {{",
        f"  return prisma.{camel}.findFirst({{ where: {{ id, {owner} }} }})",
        "}",
        "",
        f"export async function create{name}({owner}: string, data: Create{name}Input): Promise<{name}> {{",
    ]
    if create_destruct:
        lines.append(create_destruct.rstrip("\n"))
    lines += [
        f"  return prisma.{camel}.create({{",
        "    data: {",
        create_data_fields.rstrip("\n"),
        "    }",
        "  })",
        "}",
        "",
        f"export async function update{name}(id: string, data: Update{name}Input): Promise<{name}> {{",
    ]
    if update_destruct:
        lines.append(update_destruct.rstrip("\n"))
    lines += [
        f"  return prisma.{camel}.update({{",
        "    where: { id },",
        "    data: {",
        update_data_fields.rstrip("\n"),
        "    }",
        "  })",
        "}",
        "",
        f"export async function delete{name}({owner}: string, id: string): Promise<void> {{",
        f"  await prisma.{camel}.delete({{ where: {{ id, {owner} }} }})",
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
