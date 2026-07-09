"""
agents/dev_zod_generator.py
────────────────────────────
Génération DÉTERMINISTE de lib/schemas.ts depuis ProjectSpec.

Rôle : écrire lib/schemas.ts AVANT que le LLM commence, de façon à ce que :
  1. Les schémas Zod correspondent EXACTEMENT aux types CreateXxxInput de lib/types.ts
  2. Le LLM n'invente pas ses propres .parse() ou z.object() incompatibles
  3. Les Server Actions importent et utilisent des schémas cohérents sans guess

Intégration dans dev_graph.py :
    from agents.stacks.nextjs_clerk_prisma.dev_zod_generator import generate_schemas_file
    schemas_result = generate_schemas_file(spec_obj, project_workdir)
    if schemas_result:
        template_written[schemas_result.path] = schemas_result.content
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass

from .dev_model_context import _is_relation, _is_auto_field, _has_non_auto_default

logger = logging.getLogger(__name__)

# Mapping Prisma type → validateur Zod
_PRISMA_TO_ZOD: dict[str, str] = {
    "String":   "z.string().min(1)",
    "Int":      "z.coerce.number().int().nonnegative()",   # FormData envoie toujours des strings
    "Float":    "z.coerce.number()",                        # idem
    "Decimal":  "z.coerce.number()",                        # idem
    "Boolean":  "z.coerce.boolean()",                       # checkbox envoie "on" ou absent
    "DateTime": "z.coerce.date()",   # accepte ISO strings des forms, produit un Date pour Prisma
    "Json":     "z.unknown()",
    "Bytes":    "z.string()",
    "BigInt":   "z.coerce.bigint()",
}

_AUTO_FIELDS = {"id", "createdat", "updatedat", "deletedat"}

# Validation sémantique (V3+V4) — signal PRINCIPAL = nom du champ (structurel, fiable,
# indépendant du LLM annotator), signal SECONDAIRE = annotation sémantique.
_URL_NAMES = frozenset({"url", "website", "link", "avatar", "image", "imageurl", "photo", "picture", "lien", "siteweb"})
# Champs numériques clairement non-négatifs (montants, mesures). Conservateur exprès :
# on exclut score/rate/balance/delta qui peuvent légitimement être négatifs.
# EXACT : match sur le nom entier (inclut les tokens courts/ambigus en suffixe : count, qty, age, fee).
_POSITIVE_EXACT = frozenset({
    "price", "prix", "amount", "montant", "cost", "cout", "budget", "salary", "salaire",
    "fee", "frais", "quantity", "quantite", "qty", "distance", "weight", "poids",
    "duration", "duree", "stock", "count", "age", "height", "hauteur", "length",
    "longueur", "width", "largeur", "capacity", "capacite",
})
# SUFFIXE : pour les noms composés camelCase (monthlyPrice, totalAmount). Tokens ≥ 4 lettres
# et sans ambiguïté de sous-chaîne (pas "count" → discount/account, pas "fee" → coffee).
_POSITIVE_SUFFIX = tuple(
    t for t in _POSITIVE_EXACT if len(t) >= 4 and t not in ("count", "cout")
)


def _is_positive_number_field(fn: str) -> bool:
    """fn (déjà en minuscules) désigne-t-il un nombre non-négatif (montant/mesure) ?"""
    return fn in _POSITIVE_EXACT or any(fn.endswith(tok) for tok in _POSITIVE_SUFFIX)


def _semantic_zod(field_name: str, base_type: str, input_type: str, semantic_type: str, loose: bool) -> "str | None":
    """
    Retourne un validateur Zod sémantique COMPLET si le champ a un type métier
    reconnu (email, url, nombre positif), sinon None (→ mapping Prisma standard).
    `loose` = True quand le champ est optionnel/à défaut/en update → suffixe .optional().
    """
    fn = field_name.lower()
    suffix = ".optional()" if loose else ""

    # Email — nom du champ prioritaire, annotation en secours
    if input_type == "email" or semantic_type == "email" or fn == "email" or fn.endswith("email"):
        return f"z.string().email(){suffix}"

    # URL
    if input_type == "url" or semantic_type == "url" or fn in _URL_NAMES or fn.endswith("url"):
        return f"z.string().url(){suffix}"

    # Nombre non-négatif (Float/Decimal ; les Int sont déjà .nonnegative() par défaut)
    if base_type in ("Float", "Decimal") and (semantic_type == "currency" or _is_positive_number_field(fn)):
        return f"z.coerce.number().nonnegative(){suffix}"

    return None


@dataclass
class SchemasFileResult:
    path: str       # toujours "lib/schemas.ts"
    content: str
    schema_names: list[str]


def _prisma_attr_is_auto(attributes: str) -> bool:
    attrs_lower = (attributes or "").lower()
    return (
        "@id" in attrs_lower
        or "@default(now())" in attrs_lower
        or "@updatedat" in attrs_lower.replace(" ", "")
    )


def _field_has_non_auto_default(attributes: str) -> bool:
    return _has_non_auto_default(attributes)


def _prisma_type_to_zod(prisma_type: str, attributes: str = "", enums: "dict | None" = None) -> str:
    """Convertit un type Prisma en validateur Zod, gère les optionnels et enums."""
    optional = prisma_type.endswith("?")
    is_array = "[]" in prisma_type
    base = prisma_type.rstrip("?").rstrip("[]")

    if base in _PRISMA_TO_ZOD:
        zod = _PRISMA_TO_ZOD[base]
    elif enums and base in enums:
        # Enum Prisma avec valeurs connues → z.enum([...]) strict
        values = ", ".join(f'"{v}"' for v in enums[base])
        zod = f"z.enum([{values}])"
    elif base and base[0].isupper():
        # Enum Prisma sans valeurs connues → z.string() fallback
        zod = "z.string()"
    else:
        zod = "z.unknown()"

    if is_array:
        zod = f"z.array({zod})"
    if optional:
        # Enum Prisma nullable : UncheckedCreateInput accepte RecipeStatus | null
        # → z.enum([...]).nullable().optional() pour valider correctement les <select>
        if enums and base in enums:
            zod = f"{zod}.nullable().optional()"
        else:
            zod = f"{zod}.optional()"
    return zod


def _generate_update_schema(model, enums: "dict | None" = None, ctx=None) -> list[str]:
    """
    Génère les lignes du Update schema.
    Boolean : z.preprocess pour que unchecked checkbox = false explicite (pas undefined).
    Tous les autres champs : .optional() classique.
    """
    fields_lines: list[str] = []

    if ctx is not None:
        for fi in ctx.editable_fields:
            if fi.base_type == "Boolean":
                # Unchecked checkbox → undefined dans FormData → .optional() pour ne pas
                # écraser la valeur existante lors d'un update partiel (ex: update title seul)
                fields_lines.append(
                    f"  {fi.name}: z.preprocess(v => v === 'true' || v === 'on', z.boolean()).optional(),"
                )
                continue
            # Raffinement sémantique (email/url/nombre positif) — toujours optionnel en update
            _sem = _semantic_zod(fi.name, fi.base_type, fi.input_type, fi.semantic_type, loose=True)
            if _sem is not None:
                fields_lines.append(f"  {fi.name}: {_sem},")
                continue
            zod_type = _prisma_type_to_zod(fi.prisma_type, fi.attributes, enums=enums)
            if zod_type == "z.string().min(1)":
                zod_type = "z.string()"
            if not zod_type.endswith(".optional()"):
                zod_type = f"{zod_type}.optional()"
            fields_lines.append(f"  {fi.name}: {zod_type},")
        for fk in ctx.fk_fields:
            fields_lines.append(f"  {fk.field_name}: z.string().optional(),")
        for m2m in getattr(ctx, "m2m_fields", []) or []:
            # Multi-select M2M — ids envoyés via formData.getAll(input_name)
            fields_lines.append(f"  {m2m.input_name}: z.array(z.string()).optional(),")
        return fields_lines

    # Fallback depuis model (sans ctx)
    owner = model.resolved_owner().lower()
    for field in model.fields:
        fn = field.name.lower()
        if fn in _AUTO_FIELDS or fn == owner:
            continue
        if _prisma_attr_is_auto(field.attributes):
            continue
        if _is_relation(field.type, field.attributes, enums or {}):
            continue

        base_type = field.type.rstrip("?").rstrip("[]")
        if base_type == "Boolean":
            fields_lines.append(
                f"  {field.name}: z.preprocess(v => v === 'true' || v === 'on', z.boolean()).optional(),"
            )
        else:
            zod_type = _prisma_type_to_zod(field.type, field.attributes, enums=enums)
            if zod_type == "z.string().min(1)":
                zod_type = "z.string()"
            if not zod_type.endswith(".optional()"):
                zod_type = f"{zod_type}.optional()"
            fields_lines.append(f"  {field.name}: {zod_type},")

    return fields_lines


def _generate_create_schema(model, enums: "dict | None" = None, ctx=None) -> list[str]:
    """Génère les lignes du schéma Create{Name}Schema (champs mutables, sans owner)."""
    fields_lines: list[str] = []

    if ctx is not None:
        # Source unique : ctx.editable_fields + ctx.fk_fields
        for fi in ctx.editable_fields:
            _loose = fi.is_optional or fi.has_default
            # Raffinement sémantique (email/url/nombre positif) prioritaire sur le mapping brut
            _sem = _semantic_zod(fi.name, fi.base_type, fi.input_type, fi.semantic_type, _loose)
            if _sem is not None:
                fields_lines.append(f"  {fi.name}: {_sem},")
                continue
            zod_type = _prisma_type_to_zod(fi.prisma_type, fi.attributes, enums=enums)
            if _loose:
                # Optional string: drop .min(1) — empty strings from HTML forms must pass
                if zod_type == "z.string().min(1)":
                    zod_type = "z.string()"
                if not zod_type.endswith(".optional()"):
                    zod_type = f"{zod_type}.optional()"
            fields_lines.append(f"  {fi.name}: {zod_type},")
        for fk in ctx.fk_fields:
            fields_lines.append(f"  {fk.field_name}: z.string().min(1),")
        for m2m in getattr(ctx, "m2m_fields", []) or []:
            # Multi-select M2M — optionnel à la création (tags facultatifs)
            fields_lines.append(f"  {m2m.input_name}: z.array(z.string()).optional(),")
        return fields_lines

    # Fallback : recalcul depuis model (compatibilité)
    owner = model.resolved_owner().lower()
    for field in model.fields:
        fn = field.name.lower()
        if fn in _AUTO_FIELDS or fn == owner:
            continue
        if _prisma_attr_is_auto(field.attributes):
            continue
        if _is_relation(field.type, field.attributes, enums or {}):
            continue

        zod_type = _prisma_type_to_zod(field.type, field.attributes, enums=enums)
        if _field_has_non_auto_default(field.attributes):
            # Optional string: drop .min(1) — empty strings from HTML forms must pass
            if zod_type == "z.string().min(1)":
                zod_type = "z.string()"
            if not zod_type.endswith(".optional()"):
                zod_type = f"{zod_type}.optional()"
        fields_lines.append(f"  {field.name}: {zod_type},")

    return fields_lines


def generate_schemas_file(spec, project_workdir: str, contexts: "dict | None" = None) -> SchemasFileResult | None:
    """
    Génère lib/schemas.ts depuis ProjectSpec et l'écrit sur le disque.

    Contenu pour chaque modèle :
      - Create{Model}Schema  (z.object — champs mutables)
      - Update{Model}Schema  (Create{Model}Schema.partial())
    """
    if not getattr(spec, "models", None):
        return None

    schema_names: list[str] = []
    lines: list[str] = [
        "// AUTO-GÉNÉRÉ PAR dev_zod_generator.py — NE PAS MODIFIER",
        "// Schémas Zod alignés sur lib/types.ts et ProjectSpec.",
        "// Utilisé dans les Server Actions pour valider les données entrantes.",
        "import { z } from 'zod'",
        "",
    ]

    spec_enums: dict | None = getattr(spec, "enums", None) or None

    for model in spec.models:
        ctx = (contexts or {}).get(model.name)
        name = model.name
        create_name = f"Create{name}Schema"
        update_name = f"Update{name}Schema"

        field_lines = _generate_create_schema(model, enums=spec_enums, ctx=ctx)
        if not field_lines:
            # Modèle sans champs mutables (rare) — schéma vide pour éviter erreur TS
            field_lines = ["  // aucun champ mutable détecté"]

        lines.append(f"// ── {name} ──────────────────────────────────────────────────")
        lines.append(f"export const {create_name} = z.object({{")
        lines.extend(field_lines)
        lines.append("})")
        lines.append("")
        update_field_lines = _generate_update_schema(model, enums=spec_enums, ctx=ctx)
        if not update_field_lines:
            update_field_lines = ["  // aucun champ mutable"]
        lines.append(f"export const {update_name} = z.object({{")
        lines.extend(update_field_lines)
        lines.append("})")
        lines.append(f"export type Create{name}Input = z.infer<typeof {create_name}>")
        lines.append(f"export type Update{name}Input = z.infer<typeof {update_name}>")
        lines.append("")

        schema_names.extend([create_name, update_name])
        logger.info("[zod_generator] ✓ %s + %s générés", create_name, update_name)

    content = "\n".join(lines)

    lib_dir = os.path.join(project_workdir, "lib")
    os.makedirs(lib_dir, exist_ok=True)
    abs_path = os.path.join(lib_dir, "schemas.ts")
    try:
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info("[zod_generator] lib/schemas.ts écrit (%d schémas)", len(schema_names))
    except Exception as e:
        logger.error("[zod_generator] Erreur écriture lib/schemas.ts : %s", e)
        return None

    return SchemasFileResult(path="lib/schemas.ts", content=content, schema_names=schema_names)
