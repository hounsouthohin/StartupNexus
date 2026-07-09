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


class DataFetchContract(BaseModel):
    """Un appel de service à effectuer dans une page custom (Server Component)."""
    model_config = {"populate_by_name": True}
    service: str = ""
    # ex: "projectService.getAll(userId)" — signature exacte à copier dans le Server Component
    as_var: str = Field(default="", alias="as")
    # ex: "projects" — nom de la variable const dans le Server Component


class KPIDeclaration(BaseModel):
    """Contrat structuré d'un indicateur de dashboard (Juil 2026 — transport KPI).

    Remplace la prose ('affiche le total mensuel en euros des actifs') que le LLM dev
    ré-interprétait mal (count au lieu de sum, constaté 2 runs consécutifs).
    L'executor compile ce contrat en expression TypeScript EXACTE injectée dans le prompt."""
    label: str = ""
    # Libellé affiché. Ex: "Total mensuel (€)"
    source: str = ""
    # Variable des data_fetches portant les données. Ex: "subscriptions"
    agg: str = "count"
    # "count" → .length | "sum" → reduce(+field) | "avg" → sum/length
    field: str = ""
    # Champ numérique agrégé — OBLIGATOIRE pour sum/avg. Ex: "monthlyPrice"
    filter_field: str = ""
    # Champ de filtre optionnel. Ex: "status"
    filter_value: str = ""
    # Valeur du filtre. Ex: "active"


class FilteredListDeclaration(BaseModel):
    """Contrat structuré d'une LISTE FILTRÉE de dashboard (Juil 2026 — jumeau des KPI).

    Répond à la conformité fonctionnelle : la prose ('la liste de ceux dont le prélèvement
    arrive dans les 7 prochains jours') était appliquée partiellement par le LLM et parfois
    OMISE (constaté abo-tracker). L'executor compile ce contrat en expression .filter() exacte."""
    label: str = ""
    # Titre de la section. Ex: "Prélèvements sous 7 jours"
    source: str = ""
    # Variable des data_fetches portant les données. Ex: "subscriptions"
    filter_field: str = ""
    # Champ de filtre. Ex: "status", "nextBillingDate"
    filter_op: str = "eq"
    # "eq" → x.field === value | "within_days" → date entre maintenant et +N jours
    # "before" → date < maintenant | "after" → date > maintenant
    filter_value: str = ""
    # Pour eq : la valeur ("active"). Pour within_days : le nombre de jours ("7").


class PageDetailContract(BaseModel):
    """Contrat structuré pour une page custom (dashboard, landing, hub...).
    Produit par pages_detail_node — remplace les strings libres 'INTERACTIVE' de l'ancien format."""
    description: str = ""
    # Ce qui s'affiche sur la page : stats, listes résumées, textes, compteurs
    data_fetches: list[DataFetchContract] = Field(default_factory=list)
    # Appels de service nécessaires dans l'ordre d'exécution
    interactive: bool = False
    # True si la page combine données serveur ET interactions utilisateur
    # (filtres, formulaires inline, boutons d'action) → SPLIT page.tsx + page-client.tsx requis
    kpis: list[KPIDeclaration] = Field(default_factory=list)
    # Indicateurs chiffrés du dashboard — compilés en expressions TS exactes par l'executor.
    filtered_lists: list[FilteredListDeclaration] = Field(default_factory=list)
    # Listes filtrées (sous-ensembles conditionnels) — compilées en .filter() exact par l'executor.


class UXHints(BaseModel):
    """Contrats UX produits par le Semantic Annotator pour guider l'expérience utilisateur."""
    empty_states: dict[str, str] = Field(default_factory=dict)
    # Clé = path de page, valeur = message affiché quand la liste est vide.
    # Ex: {"/projects": "Aucun projet — créez votre premier projet."}

    dependency_order: list[str] = Field(default_factory=list)
    # Ordre de création des entités liées par FK.
    # Ex: ["Créez d'abord un Client avant une Invoice"]

    primary_action: dict[str, str] = Field(default_factory=dict)
    # Appel à l'action principal par page root.
    # Ex: {"/": "Commencer → /sign-in"}


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

    ux_hints: UXHints = Field(default_factory=UXHints)
    # Contrats UX : messages d'états vides, ordre de création, actions primaires.

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
