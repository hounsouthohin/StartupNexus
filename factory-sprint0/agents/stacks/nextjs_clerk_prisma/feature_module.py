"""
agents/stacks/nextjs_clerk_prisma/feature_module.py
─────────────────────────────────────────────────────
Contrat de module de feature déterministe.

Chaque module encapsule une feature transversale (search, status_flow, pagination…).
Il décide lui-même s'il doit s'activer (should_activate) et produit ses fichiers
(generate). Le dispatcher run_feature_modules itère tous les modules enregistrés.

Convention de registration : appeler register() en bas de chaque module concret.

Usage dans dev_graph.py (après generate_all_page_clients) :
    from .feature_module import run_feature_modules
    _feature_files = run_feature_modules(spec_obj, _model_contexts, _enriched_spec, project_workdir)
    template_written.update(_feature_files)
"""
from __future__ import annotations

import importlib
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

_REGISTRY: list["FeatureModule"] = []


class FeatureModule(ABC):
    """Interface que chaque module de feature doit implémenter."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Identifiant lisible du module — affiché dans les logs."""

    @abstractmethod
    def should_activate(self, enriched_spec, ctx) -> bool:
        """
        Retourne True si ce module doit générer des fichiers pour ce modèle.

        enriched_spec : EnrichedSpec | None
        ctx           : ModelGenerationContext
        """

    @abstractmethod
    def generate(self, spec, ctx, enriched_spec, workdir: str) -> dict[str, str]:
        """
        Génère les fichiers du module pour ce modèle.

        enriched_spec : EnrichedSpec | None — pour lire features[] et composer les modules
        Retourne {chemin_relatif: contenu} — intégré dans template_written.
        Ne doit jamais lever d'exception non gérée (retourner {} si erreur).
        """


def load_feature_modules(module_names: list[str], package: str) -> None:
    """
    Charge dynamiquement les modules de feature depuis une liste de noms.
    Chaque module appelle register() lors de son import (convention side-effect).
    Remplace les imports hardcodés dans dev_graph.py — driven by stack JSON config.
    """
    for name in module_names:
        try:
            importlib.import_module(f".{name}", package=package)
            logger.debug("[feature_module] loaded module: %s", name)
        except ImportError as exc:
            logger.warning("[feature_module] module introuvable '%s' : %s", name, exc)


def register(module: FeatureModule) -> FeatureModule:
    """Enregistre un module dans le registry global."""
    _REGISTRY.append(module)
    logger.debug("[feature_module] registered: %s", module.name)
    return module


def run_feature_modules(
    spec,
    model_contexts: dict,
    enriched_spec,
    workdir: str,
) -> dict[str, str]:
    """
    Dispatcher principal — appelé UNE FOIS par run dans dev_graph.py.

    Itère tous les modules enregistrés × tous les modèles.
    Appelle generate() uniquement si should_activate() retourne True.
    Retourne le merge de tous les fichiers produits.
    """
    all_written: dict[str, str] = {}

    if not _REGISTRY:
        logger.debug("[feature_module] aucun module enregistré")
        return all_written

    for ctx in model_contexts.values():
        for module in _REGISTRY:
            try:
                if not module.should_activate(enriched_spec, ctx):
                    continue
                files = module.generate(spec, ctx, enriched_spec, workdir)
                if files:
                    logger.info(
                        "[feature_module] %s → %s (%d fichier(s))",
                        module.name, ctx.name, len(files),
                    )
                    all_written.update(files)
            except Exception as exc:
                logger.error(
                    "[feature_module] %s / %s non bloquant : %s",
                    module.name, ctx.name, exc,
                )

    return all_written
