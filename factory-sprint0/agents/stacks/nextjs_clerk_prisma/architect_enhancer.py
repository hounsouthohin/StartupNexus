"""
agents/stacks/nextjs_clerk_prisma/architect_enhancer.py
─────────────────────────────────────────────────────────
Enrichissements Prisma-spécifiques pour le planner_node de l'Architect.

Extrait de agents/architect.py (T-enhancer) pour séparer la logique
Prisma de la logique de planification générique.
"""
from __future__ import annotations


def inject_prisma_relations(models: list) -> list:
    """
    Détecte les foreign keys (xxxId String) et injecte les deux côtés de la relation Prisma.
    Obligatoire — Prisma P1012 si un côté manque. Idempotent.
    """
    from agents.project_spec import PrismaField

    model_names = {m.name for m in models}
    model_by_name: dict = {m.name: m for m in models}
    relations_to_inject: list[tuple] = []

    for model in models:
        existing_relation_types = {
            f.type.rstrip("?").rstrip("[]")
            for f in model.fields
            if "@relation" in (f.attributes or "")
        }
        for field in model.fields:
            fname = field.name
            if not (fname.endswith("Id") or fname.endswith("_id")):
                continue
            base_type = field.type.rstrip("?")
            if base_type not in ("String", "Int", "BigInt"):
                continue
            ref_model_raw = fname[:-3] if fname.endswith("_id") else fname[:-2]
            ref_model = ref_model_raw[0].upper() + ref_model_raw[1:]
            if ref_model not in model_names or ref_model in existing_relation_types:
                continue
            rel_field_name = ref_model[0].lower() + ref_model[1:]
            if rel_field_name in {f.name for f in model.fields}:
                continue

            child_field = PrismaField(
                name=rel_field_name,
                type=ref_model,
                attributes=f"@relation(fields: [{fname}], references: [id])",
            )
            child_name_lower = model.name[0].lower() + model.name[1:]
            child_plural = child_name_lower + "s"
            parent_model = model_by_name[ref_model]
            parent_field = None
            if child_plural not in {f.name for f in parent_model.fields}:
                parent_field = PrismaField(name=child_plural, type=f"{model.name}[]", attributes="")

            relations_to_inject.append((model, child_field, parent_model, parent_field))
            existing_relation_types.add(ref_model)

    import logging
    _log = logging.getLogger(__name__)
    for child_model, child_field, parent_model, parent_field in relations_to_inject:
        child_model.fields.append(child_field)
        if parent_field is not None:
            parent_model.fields.append(parent_field)
        _log.info(
            "[planner] relation %s.%s ↔ %s.%s",
            child_model.name, child_field.name,
            parent_model.name, parent_field.name if parent_field else "(existant)",
        )
    return models
