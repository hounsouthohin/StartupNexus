"""
agents/dev_types_generator.py
─────────────────────────────
Génération DÉTERMINISTE de lib/types.ts depuis ProjectSpec.

Rôle : écrire lib/types.ts AVANT que le LLM commence, de façon à ce que :
  1. Les types Prisma soient re-exportés proprement  → élimine TS2339 sur prisma.model
  2. Les Input types (Create/Update) soient disponibles → le LLM n'invente pas ses propres interfaces
  3. Les types de paramètres de route soient définis → le LLM importe au lieu de redéfinir

Ce fichier est la SOURCE DE VÉRITÉ des types partagés entre tous les fichiers du projet.
Il est ajouté à protected_files → le LLM ne peut pas l'écraser.

Intégration dans dev_graph.py :
    types_result = generate_types_file(spec_obj, project_workdir)
    template_written[types_result.path] = types_result.content
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Mapping Prisma type → TypeScript type
_PRISMA_TO_TS: dict[str, str] = {
    "String":   "string",
    "Int":      "number",
    "Float":    "number",
    "Decimal":  "number",
    "Boolean":  "boolean",
    "DateTime": "Date",      # Prisma 7 CreateInput attend Date, pas string
    "Json":     "unknown",
    "Bytes":    "string",
    "BigInt":   "bigint",
}

# Noms de champs considérés "auto-générés" — exclus des Input types
_AUTO_FIELDS = {"id", "createdat", "updatedat", "deletedat"}


@dataclass
class TypesFileResult:
    path: str          # toujours "lib/types.ts"
    content: str
    model_names: list[str]
    input_types: list[str]


def _prisma_attr_is_auto(attributes: str) -> bool:
    """Retourne True si le champ est auto-géré par Prisma (id, timestamps, auto-default)."""
    attrs_lower = (attributes or "").lower()
    return "@id" in attrs_lower or "@default(now())" in attrs_lower or "@updatedAt" in attrs_lower.replace(" ", "")


def _prisma_type_to_ts(prisma_type: str) -> str:
    """Convertit un type Prisma (potentiellement avec ?) en TypeScript."""
    optional = prisma_type.endswith("?")
    base = prisma_type.rstrip("?").rstrip("[]")
    # Primitifs connus → mapping direct
    # Type inconnu commençant par une majuscule → enum Prisma → string
    ts = _PRISMA_TO_TS.get(base, "string" if base and base[0].isupper() else "unknown")
    return f"{ts} | null" if optional else ts


def _is_relation_field(field_name: str, field_type: str, attributes: str) -> bool:
    """
    Détecte si un champ est une relation Prisma (à exclure des Input types).
    Les relations ont @relation dans leurs attributs OU leur type commence par une majuscule
    et n'est pas un type primitif Prisma.
    """
    if "@relation" in (attributes or ""):
        return True
    base_type = field_type.rstrip("?").rstrip("[]")
    # Type primitif connu → pas une relation
    if base_type in _PRISMA_TO_TS:
        return False
    # Type commence par une majuscule et inconnu → probablement un modèle (relation)
    if base_type and base_type[0].isupper():
        return True
    return False


def _field_has_non_auto_default(attributes: str) -> bool:
    """True si le champ a un @default qui n'est pas now() ou uuid() (ex: @default(PENDING))."""
    if not attributes:
        return False
    attrs = attributes.lower()
    if "@default(now())" in attrs or "@default(uuid())" in attrs or "@default(cuid())" in attrs:
        return False
    return "@default(" in attrs


def generate_types_file(spec: "ProjectSpec", project_workdir: str) -> TypesFileResult:  # type: ignore[name-defined]
    """
    Génère lib/types.ts depuis ProjectSpec et l'écrit sur le disque.

    Contenu :
      - Re-exports des types Prisma  (export type { ModelA, ModelB } from '@prisma/client')
      - Re-export du namespace Prisma (export type { Prisma } from '@prisma/client')
      - ApiResponse<T>               (type utilitaire standard pour toutes les routes)
      - CreateXxxInput               (champs éditables du modèle, sans id/timestamps/relations)
      - UpdateXxxInput               (Partial<CreateXxxInput>)
      - XxxPageParams                (paramètres de route pour les pages dynamiques [id])
    """
    model_names = [m.name for m in spec.models]
    input_types_generated: list[str] = []

    lines: list[str] = [
        "// ── AUTO-GÉNÉRÉ PAR dev_types_generator.py — NE PAS MODIFIER ────────────────",
        "// Source de vérité des types partagés entre tous les fichiers du projet.",
        "// Regénéré à chaque run depuis ProjectSpec.",
        "// ─────────────────────────────────────────────────────────────────────────────",
        "",
    ]

    # ── 1. Re-exports Prisma ────────────────────────────────────────────────────
    if model_names:
        prisma_exports = ", ".join(model_names)
        lines += [
            "// Types Prisma — disponibles après `prisma generate`",
            f"export type {{ {prisma_exports} }} from '@prisma/client'",
            "export type { Prisma } from '@prisma/client'",
            "",
        ]

    # ── 2. ApiResponse<T> — type utilitaire standard ────────────────────────────
    lines += [
        "// Type de réponse API standard — utilise-le dans tous les route handlers",
        "export type ApiResponse<T> = {",
        "  data: T | null",
        "  error: string | null",
        "  success: boolean",
        "}",
        "",
        "// Type de réponse paginée",
        "export type PaginatedResponse<T> = ApiResponse<T[]> & {",
        "  total: number",
        "  page: number",
        "  pageSize: number",
        "}",
        "",
    ]

    # ── 3. Input types par modèle ───────────────────────────────────────────────
    for model in spec.models:
        editable_fields: list[tuple[str, str]] = []  # (nom+optionality, type TS)
        _owner = model.resolved_owner().lower()

        for field in model.fields:
            # Exclure les champs auto-gérés (id, createdAt, updatedAt)
            if _prisma_attr_is_auto(field.attributes):
                continue
            if field.name.lower() in _AUTO_FIELDS:
                continue
            # Exclure l'owner_field — il est ajouté par le service depuis auth()
            if field.name.lower() == _owner:
                continue
            # Exclure les relations (objets Prisma imbriqués)
            if _is_relation_field(field.name, field.type, field.attributes):
                continue
            ts_type = _prisma_type_to_ts(field.type)
            is_nullable = field.type.endswith("?")
            has_default = _field_has_non_auto_default(field.attributes)

            if is_nullable:
                # description?: string | null — optionnel ET nullable
                # undefined ⊆ string|null|undefined → LLM passe `description?: string` sans TS2345
                # string|null ⊆ string|null|undefined → page passe données Prisma sans TS2322
                editable_fields.append((field.name + "?", ts_type))
            elif has_default:
                # Champ optionnel à la création (a un @default) mais non nullable
                editable_fields.append((field.name + "?", ts_type))
            else:
                editable_fields.append((field.name, ts_type))

        if not editable_fields:
            # Modèle sans champs éditables détectables → type minimal
            editable_fields = [("data", "unknown")]

        create_type_name = f"Create{model.name}Input"
        update_type_name = f"Update{model.name}Input"
        input_types_generated.extend([create_type_name, update_type_name])

        lines.append(f"// Types d'entrée pour {model.name}")
        lines.append(f"export type {create_type_name} = {{")
        for fname, ftype in editable_fields:
            lines.append(f"  {fname}: {ftype}")
        lines.append("}")
        lines.append(f"export type {update_type_name} = Partial<{create_type_name}>")
        lines.append("")

        # SerializedXxx — type explicite (tous les champs scalaires), DateTime → string.
        # N'utilise PAS Omit<PrismaType, K> : en Prisma v7 les types modèles sont des
        # génériques complexes (runtime.Types.DefaultSelection<...>) que TypeScript résout
        # incorrectement avec Omit → tous les scalaires disparaissent, reste {} uniquement.
        # Type auto-suffisant : ne dépend pas de la forme interne de @prisma/client.
        serialized_name = f"Serialized{model.name}"
        lines.append(f"// {model.name} — retour service (DateTime → string, NE PAS appeler .toISOString())")
        lines.append(f"export type {serialized_name} = {{")
        for _sf in model.fields:
            if _is_relation_field(_sf.name, _sf.type, _sf.attributes):
                continue
            _base = _sf.type.rstrip("?").rstrip("[]")
            _nullable = _sf.type.endswith("?")
            # DateTime → string dans SerializedXxx (sérialisé par _serialize dans le service)
            if _base == "DateTime":
                _ts = "string | null" if _nullable else "string"
            else:
                _ts = _prisma_type_to_ts(_sf.type)
            lines.append(f"  {_sf.name}: {_ts}")
        lines.append("}")
        lines.append("")

    # ── 4. Route param types pour les pages dynamiques ─────────────────────────
    dynamic_pages = [p for p in spec.pages if "[" in p.path]
    if dynamic_pages:
        lines.append("// Paramètres de route pour les pages dynamiques")
        seen_params: set[str] = set()
        for page in dynamic_pages:
            # Extrait les segments dynamiques : /posts/[id]/comments/[commentId]
            import re
            params = re.findall(r"\[(\w+)\]", page.path)
            if not params:
                continue
            # Nom du type : PostIdPageParams, TaskIdCommentIdPageParams, etc.
            type_suffix = "".join(p.capitalize() for p in params)
            # Cherche le premier modèle dont le nom apparaît dans le path
            model_hint = ""
            for m in spec.models:
                if m.name.lower() in page.path.lower():
                    model_hint = m.name
                    break
            type_name = f"{model_hint or 'Dynamic'}{type_suffix}PageParams"
            if type_name in seen_params:
                continue
            seen_params.add(type_name)
            params_block = ", ".join(f"{p}: string" for p in params)
            lines.append(f"export type {type_name} = {{ params: {{ {params_block} }} }}")
        lines.append("")

    # ── 5. Auth types (Clerk) ───────────────────────────────────────────────────
    lines += [
        "// Types Clerk — userId garanti non-null dans les routes protégées",
        "export type AuthenticatedRequest = Request & { auth: { userId: string } }",
        "",
    ]

    content = "\n".join(lines)

    # Écriture sur le disque
    output_path = os.path.join(project_workdir, "lib", "types.ts")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info(
        "[types_generator] ✓ lib/types.ts généré — %d modèles, %d types Input, %d pages dynamiques",
        len(model_names),
        len(input_types_generated),
        len(dynamic_pages),
    )

    return TypesFileResult(
        path="lib/types.ts",
        content=content,
        model_names=model_names,
        input_types=input_types_generated,
    )
