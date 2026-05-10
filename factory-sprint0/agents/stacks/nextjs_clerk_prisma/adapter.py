"""
agents/stacks/nextjs_clerk_prisma/adapter.py
────────────────────────────────────────────
Implémentation concrète de StackAdapter pour la stack Next.js 14 + Clerk V6 + Prisma 7.
Délègue l'exécution à dev_graph.run_dev_agent (inchangé).
"""
from __future__ import annotations

from typing import Any

from agents.stacks.base import StackAdapter


class NextjsClerkPrismaAdapter(StackAdapter):

    @property
    def stack_id(self) -> str:
        return "nextjs-clerk-prisma"

    async def run_dev_agent(
        self,
        spec: dict[str, Any],
        project_name: str,
        run_id: str,
        project_workdir: str = "",
        **kwargs: Any,
    ) -> dict[str, Any]:
        from .dev_graph import run_dev_agent
        return await run_dev_agent(
            spec=spec,
            project_name=project_name,
            run_id=run_id,
            **kwargs,
        )

    def inject_relations(self, models: list) -> list:
        from .architect_enhancer import inject_prisma_relations
        return inject_prisma_relations(models)
