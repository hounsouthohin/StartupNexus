"""
agents/stacks/base.py
─────────────────────
Contrat abstrait que toute stack doit implémenter.

Le moteur (dev_test_activity, architect_activity) importe uniquement StackAdapter
et utilise get_adapter_for_stack(stack_id) pour obtenir l'implémentation concrète.
Ajouter une nouvelle stack = créer agents/stacks/<new_stack>/ + implémenter StackAdapter
+ enregistrer dans _REGISTRY ci-dessous. Aucune modification du moteur core.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class StackAdapter(ABC):
    """Interface unique que toute stack doit implémenter."""

    @property
    @abstractmethod
    def stack_id(self) -> str:
        """Identifiant canonique ex: 'nextjs-clerk-prisma'."""

    @abstractmethod
    async def run_dev_agent(
        self,
        spec: dict[str, Any],
        project_name: str,
        run_id: str,
        project_workdir: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Lance le dev agent pour cette stack, retourne le résultat brut."""

    @property
    def pre_run_commands(self) -> list[dict[str, Any]]:
        """Liste des commandes pré-LLM (npm install, prisma generate…).
        Par défaut lues depuis la stack config JSON — override si besoin."""
        from agents.stack_config import load_stack_config
        return load_stack_config(self.stack_id).get("pre_run_commands", [])

    @property
    def protected_files(self) -> set[str]:
        """Fichiers que le LLM ne peut pas écraser.
        Par défaut lus depuis la stack config JSON."""
        from agents.stack_config import load_stack_config
        return set(load_stack_config(self.stack_id).get("protected_files", []))

    @property
    def role_rag_queries(self) -> dict[str, str]:
        """Mapping rôle → requête Qdrant par type de fichier.
        Par défaut lu depuis la stack config JSON."""
        from agents.stack_config import load_stack_config
        return load_stack_config(self.stack_id).get("role_rag_queries", {})

    def inject_relations(self, models: list) -> list:
        """Hook optionnel — injecte les relations manquantes dans les modèles Prisma.
        Par défaut : no-op (retourne les modèles inchangés)."""
        return models


# ── Registre des stacks disponibles ──────────────────────────────────────────
# Pour ajouter une stack : créer agents/stacks/<id>/ + implémenter StackAdapter
# + ajouter l'entrée ici. Le moteur n'importe jamais une stack directement.

def get_adapter_for_stack(stack_id: str) -> StackAdapter:
    """Retourne l'adapter concret pour un stack_id donné."""
    from agents.stacks.nextjs_clerk_prisma.adapter import NextjsClerkPrismaAdapter
    _REGISTRY: dict[str, type[StackAdapter]] = {
        "nextjs-clerk-prisma": NextjsClerkPrismaAdapter,
    }
    cls = _REGISTRY.get(stack_id)
    if cls is None:
        raise ValueError(
            f"Stack '{stack_id}' non enregistrée. "
            f"Stacks disponibles : {list(_REGISTRY.keys())}"
        )
    return cls()
