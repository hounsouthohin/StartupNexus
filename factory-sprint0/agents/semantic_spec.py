"""
agents/semantic_spec.py
────────────────────────
Schéma Pydantic de la spécification sémantique enrichie.

Produit par : semantic_annotator_node dans architect.py
Consommé par : dev_model_context.py, dev_service_generator.py, dev_form_generator.py

Stack-agnostique : décrit les annotations sémantiques qu'un LLM infère depuis
un brief, indépendamment de la stack cible.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class FieldAnnotation(BaseModel):
    """Annotation sémantique d'un champ de modèle."""
    semantic_type: str = ""
    # Valeurs :
    #   "textarea"       → <textarea> (description, content, notes, body...)
    #   "status-enum"    → select workflow  (pending/active/done...)
    #   "priority-enum"  → select priorité  (low/medium/high...)
    #   "currency"       → number décimal
    #   "date"           → input date
    #   "datetime"       → input datetime-local
    #   "url"            → input url
    #   "email"          → input email
    #   "text"           → input text standard (défaut implicite)

    values: list[str] = Field(default_factory=list)
    # Pour enums : valeurs dans l'ordre logique.
    # Ex: ["pending", "in_progress", "done"]

    display_label: str = ""
    # Label UI si différent du nom snake_case.


class QueryDeclaration(BaseModel):
    """Déclaration d'une query métier à compiler en méthode de service."""
    model: str = ""
    # Modèle Prisma cible. Ex: "Task", "Recipe" — filtre vers le bon .service.ts.

    name: str = ""
    # Nom de la méthode. Ex: "getByStatus", "searchByTitle"

    pattern: str = ""
    # Template Prisma à appliquer :
    #   "filter_by_field"    → findMany where { field: value }
    #   "search_text"        → findMany where { field: { contains: q, mode: insensitive } }
    #   "count_by_field"     → groupBy [field] _count true
    #   "filter_by_relation" → findMany where { relation: { field: value } }

    field: str = ""
    # Champ Prisma cible. Ex: "status", "assigneeId", "title"

    param_name: str = ""
    # Nom du paramètre TypeScript. Si vide → déduit depuis field.

    return_many: bool = True
    # True → Promise<SerializedXxx[]>, False → Promise<SerializedXxx>


class EnrichedSpec(BaseModel):
    """
    Spec sémantique enrichie produite par le Semantic Annotator.
    Toutes les clés sont optionnelles — absence = fallback sur heuristiques Level A.
    """
    field_annotations: dict[str, FieldAnnotation] = Field(default_factory=dict)
    # Clé = nom du champ Prisma. Ex: "description", "status", "priority"

    required_queries: list[QueryDeclaration] = Field(default_factory=list)
    # Queries métier au-delà des 7 méthodes CRUD standard.

    features: list[str] = Field(default_factory=list)
    # Modules à activer. Ex: "search", "pagination", "status_flow", "public_pages"

    def get_semantic_type(self, field_name: str) -> str:
        """semantic_type d'un champ, ou '' si non annoté (→ heuristique)."""
        ann = self.field_annotations.get(field_name)
        return ann.semantic_type if ann else ""

    def get_enum_values(self, field_name: str) -> list[str]:
        """Valeurs d'enum annotées pour un champ, ou [] si non annoté."""
        ann = self.field_annotations.get(field_name)
        return ann.values if ann else []

    def has_feature(self, feature: str) -> bool:
        return feature in self.features
