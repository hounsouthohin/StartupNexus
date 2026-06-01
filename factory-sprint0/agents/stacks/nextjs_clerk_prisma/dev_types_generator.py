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

from .dev_model_context import _is_relation, _is_auto_field, _has_non_auto_default

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


def _prisma_type_to_ts(prisma_type: str, spec_enums: dict | None = None) -> str:
    """Convertit un type Prisma (potentiellement avec ?) en TypeScript."""
    optional = prisma_type.endswith("?")
    base = prisma_type.rstrip("?").rstrip("[]")
    if spec_enums and base in spec_enums:
        # Enum Prisma → nom de type importé depuis @prisma/client.
        # Ex: LeaveStatus → LeaveStatus (importé localement via import type { ..., LeaveStatus })
        # Plus robuste que les string literals : si une valeur est ajoutée à l'enum,
        # SerializedXxx reste correct sans régénération.
        ts = f"{base} | null" if optional else base
        return ts
    ts = _PRISMA_TO_TS.get(base, "string" if base and base[0].isupper() else "unknown")
    return f"{ts} | null" if optional else ts


def generate_types_file(
    spec: "ProjectSpec",  # type: ignore[name-defined]
    project_workdir: str,
    contexts: "dict | None" = None,
) -> "TypesFileResult":
    """
    Génère lib/types.ts depuis ProjectSpec et l'écrit sur le disque.

    contexts : dict[model_name, ModelGenerationContext] pré-calculé par dev_graph.py.
               Si fourni, utilise ctx.editable_fields + ctx.fk_fields (source unique).
               Sinon, recalcule depuis spec (fallback de compatibilité).

    Contenu :
      - import type { Prisma }       (binding local → Prisma.XxxUncheckedCreateInput utilisable)
      - Re-exports des types Prisma  (export type { ModelA, ModelB } from '@prisma/client')
      - Re-export du namespace Prisma (export type { Prisma })
      - ApiResponse<T>               (type utilitaire standard pour toutes les routes)
      - CreateXxxInput               (Omit<Prisma.XxxUncheckedCreateInput, auto_fields> — Direction A)
      - UpdateXxxInput               (Partial<CreateXxxInput>)
      - SerializedXxx                (all scalars, DateTime → string, pour les retours service)
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
    # Les enums sont importés ET exportés depuis la même ligne pour être disponibles
    # dans le scope local (nécessaire pour les utiliser dans SerializedXxx ci-dessous).
    # `export type { X } from 'mod'` seul ne suffit pas — X n'est pas lié localement.
    _enum_names = list((getattr(spec, "enums", None) or {}).keys())
    _all_local_imports = ["Prisma"] + _enum_names
    lines += [
        f"import type {{ {', '.join(_all_local_imports)} }} from '@prisma/client'",
        f"export type {{ {', '.join(_all_local_imports)} }}",
    ]
    if model_names:
        prisma_exports = ", ".join(model_names)
        lines += [
            "// Types Prisma — disponibles après `prisma generate`",
            f"export type {{ {prisma_exports} }} from '@prisma/client'",
            "",
        ]
    elif _enum_names:
        lines.append("")

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
    spec_enums: dict = getattr(spec, "enums", None) or {}
    _spec_models_by_name: dict = {m.name: m for m in spec.models}

    for model in spec.models:
        ctx = (contexts or {}).get(model.name)

        # Champ propriétaire (userId / ownerId / etc.) — fourni par auth, jamais par le formulaire
        _owner: str = (ctx.owner if ctx is not None else model.resolved_owner()) or ""

        # Champs auto-gérés par Prisma à exclure de UncheckedCreateInput
        _auto_names = {f.name for f in model.fields if _is_auto_field(f.name, f.attributes)}
        _omit_set: set[str] = {"id"} | _auto_names
        if _owner:
            _omit_set.add(_owner)
        _omit_ts = " | ".join(f"'{fn}'" for fn in sorted(_omit_set))

        create_type_name = f"Create{model.name}Input"
        update_type_name = f"Update{model.name}Input"
        input_types_generated.extend([create_type_name, update_type_name])

        # Direction A : Omit<Prisma.XxxUncheckedCreateInput, auto_fields>
        # → type toujours aligné sur ce que Prisma attend, y compris les enums stricts.
        # UncheckedCreateInput est un plain TS interface → Omit fonctionne correctement.
        lines.append(f"// Types d'entrée pour {model.name}")
        lines.append(f"export type {create_type_name} = Omit<Prisma.{model.name}UncheckedCreateInput, {_omit_ts}>")
        lines.append(f"export type {update_type_name} = Partial<{create_type_name}>")
        lines.append("")

        # SerializedXxx — type explicite (scalaires + relations optionnelles), DateTime → string.
        # N'utilise PAS Omit<PrismaType, K> : en Prisma v7 les types modèles sont des
        # génériques complexes (runtime.Types.DefaultSelection<...>) que TypeScript résout
        # incorrectement avec Omit → tous les scalaires disparaissent, reste {} uniquement.
        # Type auto-suffisant : ne dépend pas de la forme interne de @prisma/client.
        # Le champ owner (userId/authorId) est exclu : interne auth, jamais exposé au client.
        serialized_name = f"Serialized{model.name}"
        lines.append(f"// {model.name} — retour service (DateTime → string, NE PAS appeler .toISOString())")
        lines.append(f"export type {serialized_name} = {{")
        _owner_lower = _owner.lower() if _owner else ""
        for _sf in model.fields:
            if _owner_lower and _sf.name.lower() == _owner_lower:
                continue  # champ owner exclu de SerializedXxx — non exposé au client
            if _is_relation(_sf.type, _sf.attributes, spec_enums):
                # Relation → type inline dérivé du modèle lié (si présent dans la spec)
                # Rend item.category.name typé sans TS2551
                _base_rel = _sf.type.rstrip("?").rstrip("[]")
                _is_array_rel = "[]" in _sf.type
                _nullable_rel = _sf.type.endswith("?")
                _rel_model = _spec_models_by_name.get(_base_rel)
                if _rel_model is not None:
                    _rel_field_strs: list[str] = []
                    for _rf in _rel_model.fields:
                        if _is_relation(_rf.type, _rf.attributes, spec_enums):
                            continue
                        _rb = _rf.type.rstrip("?").rstrip("[]")
                        if _rb == "DateTime":
                            _rt = "string | null" if _rf.type.endswith("?") else "string"
                        else:
                            _rt = _prisma_type_to_ts(_rf.type, spec_enums)
                        _rel_field_strs.append(f"{_rf.name}: {_rt}")
                    _inner = "{ " + "; ".join(_rel_field_strs) + " }" if _rel_field_strs else "{ id: string }"
                else:
                    _inner = "{ id: string; [key: string]: unknown }"
                if _is_array_rel:
                    lines.append(f"  {_sf.name}?: {_inner}[]")
                elif _nullable_rel:
                    lines.append(f"  {_sf.name}?: {_inner} | null")
                else:
                    lines.append(f"  {_sf.name}?: {_inner}")
                continue
            _base = _sf.type.rstrip("?").rstrip("[]")
            _nullable = _sf.type.endswith("?")
            # DateTime → string dans SerializedXxx (sérialisé par _serialize dans le service)
            if _base == "DateTime":
                _ts = "string | null" if _nullable else "string"
            else:
                _ts = _prisma_type_to_ts(_sf.type, spec_enums)
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
            # Next.js 15 : params est une Promise — format obligatoire pour éviter TS2344
            lines.append(f"export type {type_name} = {{ params: Promise<{{ {params_block} }}> }}")
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
