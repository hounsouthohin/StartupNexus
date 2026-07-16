"""
service_modules/__init__.py
────────────────────────────
Registre ordonné des ServiceMethodModules.

L'ordre détermine l'ordre des méthodes dans le fichier .service.ts généré.
Ajouter un module = l'instancier ici et l'insérer dans SERVICE_MODULES.
"""
import re as _re

from .crud import CrudModule
from .child import ChildModule
from .public import PublicModule
from .relations import RelationsModule
from .public_relations import PublicRelationsModule
from .slug import SlugModule

# getPublished (ex-StatusModule) DÉPRÉCIÉ : sa requête était identique à celle de
# getPublicAll pour les modèles à statut (public.py, branche has_status) → 100% redondant.
# SERVICE_METHOD_REGISTRY ne l'a jamais listé → l'architect ne le connaissait déjà pas.
# Une seule vérité désormais : getPublicAll() pour toute liste publique, statut compris.
SERVICE_MODULES = [
    CrudModule(),
    ChildModule(),
    PublicModule(),
    RelationsModule(),
    PublicRelationsModule(),
    SlugModule(),
]

# ── Registre des méthodes par condition d'activation ────────────────────────
# Source de vérité pour spec_enricher (validation per-modèle) et
# pages_detail_node (capabilities string dynamique injectée dans le LLM architect).
#
# Note sur ChildModule : génère getBy{ParentName}Id() dynamiquement.
# Les noms concrets (getByProjectId, getByTaskId...) ne peuvent pas être énumérés ici.
# Le pattern est géré séparément via _re.match(r"getBy[A-Z]\w+Id$", method).
SERVICE_METHOD_REGISTRY = {
    "always":               frozenset({"getAll", "getById", "create", "update", "delete"}),
    "if_public_pages":      frozenset({"getPublicAll", "getPublicById"}),
    "if_slug":              frozenset({"getBySlug", "getBySlugOwned", "getBySlugWithRelations"}),
    "if_relations":         frozenset({"getAllWithRelations", "getByIdWithRelations"}),
    "if_public_relations":  frozenset({"getPublicByIdWithRelations"}),
    # ChildModule : getBy{ParentName}Id — dynamique, détecté par pattern regex
}

_CHILD_METHOD_RE = _re.compile(r"^getBy[A-Z]\w+Id$")


def valid_methods_for_flags(
    has_public: bool = False,
    has_slug: bool = False,
    has_relations: bool = False,
    has_fk_fields: bool = False,
    fk_parent_names: list[str] | None = None,
) -> frozenset:
    """
    Calcule l'ensemble des méthodes valides pour un modèle donné ses flags.
    Les méthodes ChildModule (getBy{Parent}Id) sont ajoutées depuis fk_parent_names.
    """
    methods: set[str] = set(SERVICE_METHOD_REGISTRY["always"])
    if has_public:
        methods |= SERVICE_METHOD_REGISTRY["if_public_pages"]
    if has_slug:
        methods |= SERVICE_METHOD_REGISTRY["if_slug"]
    if has_relations:
        methods |= SERVICE_METHOD_REGISTRY["if_relations"]
    if has_public and has_relations:
        methods |= SERVICE_METHOD_REGISTRY["if_public_relations"]
    for parent in (fk_parent_names or []):
        if parent:
            methods.add(f"getBy{parent[0].upper()}{parent[1:]}Id")
    return frozenset(methods)


def is_valid_method_for_model(method: str, valid_methods: frozenset, has_fk_fields: bool) -> bool:
    """
    Vérifie si une méthode est valide pour un modèle.
    Gère le pattern dynamique ChildModule (getBy{Parent}Id).
    """
    if method in valid_methods:
        return True
    if has_fk_fields and _CHILD_METHOD_RE.match(method):
        return True  # méthode ChildModule valide si le modèle a des FK
    return False


def build_factory_capabilities_string() -> str:
    """
    Génère la chaîne _FACTORY_CAPABILITIES injectée dans pages_detail_node.
    Appelée au runtime — toujours synchronisée avec les service_modules réels.
    """
    always_sorted = sorted(SERVICE_METHOD_REGISTRY["always"])
    return "\n".join([
        "## CONTRAINTES TECHNIQUES",
        "",
        "### Méthodes de service disponibles (source : service_modules/)",
        "",
        "Toujours disponibles pour tout modèle :",
        *[f"  {m}(userId, ...)" for m in always_sorted],
        "",
        "Disponibles selon les champs Prisma du modèle :",
        "  getPublicAll() / getPublicById(id)               — si published/isPublic/status ou page publique",
        "  getBySlug(slug) / getBySlugOwned(userId, slug)   — si champ `slug @unique`",
        "  getAllWithRelations(userId) / getByIdWithRelations(userId, id) — si @relation Prisma",
        "  getPublicByIdWithRelations(id)                   — si public ET @relation",
        "  getBy{ParentName}Id(userId, parentId)            — si FK vers un parent (ex: getByProjectId)",
        "",
        "⚠ JAMAIS inventer une méthode absente de CONTRACTS.md → TS2339 fatal au build.",
        "⚠ Pages publiques : getPublicAll() UNIQUEMENT — getPublished() N'EXISTE PAS.",
        "",
        "### Convention paramètres dynamiques — INVARIANT TypeScript",
        "- Segment [id]   → params.id   dans TypeScript (jamais params.taskId, params.postId, etc.)",
        "- Segment [slug] → params.slug dans TypeScript (toujours)",
        "",
        "### [CROSS_ENTITY] — signal pour données d'un modèle secondaire",
        "Si une page de type \"detail\" doit AUSSI afficher les données d'un modèle ENFANT,",
        "ajouter le tag [CROSS_ENTITY: NomDuModèle] dans la description de cette page.",
        "Exemple : /projects/[id] qui doit montrer ses tâches → [CROSS_ENTITY: Task]",
        "",
        "### Design system — auto-généré (ne PAS décrire dans pages_detail)",
        "- La sidebar, le layout, les couleurs : générés depuis design_system automatiquement",
        "- NE PAS écrire : \"Utilise bg-indigo-600\", \"bouton primaire vert\", \"sidebar noire\"",
        "- Décrire UNIQUEMENT la logique fonctionnelle, jamais le style visuel",
    ])


__all__ = ["SERVICE_MODULES", "SERVICE_METHOD_REGISTRY", "valid_methods_for_flags",
           "is_valid_method_for_model", "build_factory_capabilities_string"]
