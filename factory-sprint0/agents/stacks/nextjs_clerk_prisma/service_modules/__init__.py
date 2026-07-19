"""
service_modules/__init__.py
────────────────────────────
Registre ordonné des ServiceMethodModules.

L'ordre détermine l'ordre des méthodes dans le fichier .service.ts généré.
Ajouter un module = l'instancier ici et l'insérer dans SERVICE_MODULES.
"""
import re as _re
from dataclasses import dataclass as _dataclass, field as _field

from .crud import CrudModule
from .child import ChildModule
from .public import PublicModule
from .relations import RelationsModule
from .public_relations import PublicRelationsModule
from .slug import SlugModule
from .transition import TransitionModule

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
    TransitionModule(),
]

# ── SERVICE_METHOD_REGISTRY : SUPPRIMÉ (17 Juil 2026) ───────────────────────
# C'était le 2e des 3 miroirs recopiés à la main de « quelles méthodes existent ».
# Il a sur-listé getBySlugWithRelations sous `if_slug` seul (D33) alors que slug.py ne
# l'émet que si le modèle a AUSSI des relations — un mensonge latent (TS2339).
# Remplacé par une DÉRIVATION depuis les modules eux-mêmes (voir plus bas).

_CHILD_METHOD_RE = _re.compile(r"^getBy[A-Z]\w+Id$")


# ── SOURCE UNIQUE (17 Juil 2026) ──────────────────────────────────────────────
# Les méthodes réellement émises pour un modèle, dérivées des MODULES eux-mêmes.
# Chaque module déclare ce qu'il émet à côté du code qui l'émet (methods_for) —
# donc CONTRACTS.md, le registre et les capabilities cessent d'être des miroirs
# recopiés à la main. C'est le remède au cas `getPublished` (4 représentations,
# 3 miroirs manuels) et à D33. Voir docs/remodularisation_plan.md.

def methods_for_ctx(ctx) -> list:
    """[MethodDecl] — toutes les méthodes émises pour ce modèle, modules actifs uniquement."""
    out: list = []
    for _mod in SERVICE_MODULES:
        try:
            if _mod.should_activate(ctx):
                out.extend(_mod.methods_for(ctx))
        except Exception:  # un module défaillant ne doit pas casser l'inventaire
            continue
    return out


def method_names_for_ctx(ctx) -> frozenset:
    """Noms des méthodes réellement émises — pour toute validation per-modèle."""
    return frozenset(_d.name for _d in methods_for_ctx(ctx))


@_dataclass
class _FkStub:
    related_model: str
    field_name: str


@_dataclass
class _CtxStub:
    """Contexte MINIMAL reconstruit depuis des drapeaux.

    Les consommateurs amont (spec_enricher, architect) tournent AVANT que les vrais
    ModelGenerationContext existent : ils ne disposent que de drapeaux extraits des
    chaînes de modèles. Or les NOMS de méthodes ne dépendent que de ces drapeaux
    structurels (les signatures, elles, exigent un vrai contexte).
    Ce stub permet donc à la validation amont de dériver de la MÊME source que la
    génération — au lieu d'un registre recopié à la main qui finit par mentir (D33).
    """
    name: str = "Model"
    owner: str = "userId"
    serialized_type: str = "SerializedModel"
    fk_fields: list = _field(default_factory=list)
    relation_fields: list = _field(default_factory=list)
    m2m_fields: list = _field(default_factory=list)
    has_slug: bool = False
    has_public_pages: bool = False
    has_status: bool = False
    has_published_bool: bool = False
    status_flow: object = None


def valid_methods_for_flags(
    has_public: bool = False,
    has_slug: bool = False,
    has_relations: bool = False,
    has_fk_fields: bool = False,
    fk_parent_names: list[str] | None = None,
    has_status_flow: bool = False,
) -> frozenset:
    """
    Méthodes valides pour un modèle décrit par ses drapeaux — DÉRIVÉ des modules.

    N'énumère plus rien à la main : interroge les vrais ServiceMethodModule via un
    contexte minimal. Conséquence : une méthode ajoutée/retirée dans un module se
    propage ici automatiquement, y compris ses conditions imbriquées.
    """
    _parents = [_p for _p in (fk_parent_names or []) if _p]
    stub = _CtxStub(
        fk_fields=[
            _FkStub(_p[0].upper() + _p[1:], f"{_p[0].lower() + _p[1:]}Id") for _p in _parents
        ],
        relation_fields=[True] if has_relations else [],
        has_slug=has_slug,
        has_public_pages=has_public,
        status_flow=True if has_status_flow else None,
    )
    return method_names_for_ctx(stub)


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
    # Tout est DÉRIVÉ des modules : chaque ligne conditionnelle est calculée par
    # différence (méthodes apparues quand on active un drapeau). Plus aucun nom de
    # méthode n'est écrit à la main ici — ajouter un module suffit à l'annoncer
    # à l'architect. C'était le 3e miroir manuel.
    _always = valid_methods_for_flags()

    def _delta(**flags) -> str:
        """Méthodes qui APPARAISSENT quand on active ces drapeaux."""
        return " / ".join(sorted(valid_methods_for_flags(**flags) - _always)) or "—"

    def _combo(a: dict, b: dict) -> str:
        """Méthodes qui n'existent QUE dans le croisement de deux drapeaux."""
        _both = valid_methods_for_flags(**{**a, **b})
        return " / ".join(sorted(
            _both - valid_methods_for_flags(**a) - valid_methods_for_flags(**b)
        )) or "—"

    _cond_lines = [
        (_delta(has_public=True),      "si published/isPublic/status ou page publique"),
        (_delta(has_slug=True),        "si champ `slug @unique`"),
        (_delta(has_relations=True),   "si @relation Prisma"),
        (_combo({"has_public": True}, {"has_relations": True}), "si public ET @relation"),
        (_combo({"has_slug": True}, {"has_relations": True}),   "si slug ET @relation"),
        ("getBy{ParentName}Id(userId, parentId)", "si FK vers un parent (ex: getByProjectId)"),
        (_delta(has_status_flow=True), "si machine à états (change le statut + capte les champs de la transition)"),
    ]

    return "\n".join([
        "## CONTRAINTES TECHNIQUES",
        "",
        "### Méthodes de service disponibles (source : service_modules/)",
        "",
        "Toujours disponibles pour tout modèle :",
        *[f"  {m}(userId, ...)" for m in sorted(_always)],
        "",
        "Disponibles selon les champs Prisma du modèle :",
        *[f"  {_m:<48} — {_why}" for _m, _why in _cond_lines if _m != "—"],
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


__all__ = ["SERVICE_MODULES", "valid_methods_for_flags",
           "is_valid_method_for_model", "build_factory_capabilities_string",
           "methods_for_ctx", "method_names_for_ctx"]
