"""
dev_hub_generator.py — Génération déterministe de app/dashboard/page.tsx

Problème résolu : le LLM executor oublie régulièrement `import Link from 'next/link'`
sur la hub page, causant un `Cannot find name 'Link'` au build.

La hub page est simple et 100% dérivable du spec_obj — aucune raison de la confier au LLM.

Output : app/dashboard/page.tsx avec :
  - imports corrects (Link, auth, redirect, services)
  - auth() guard
  - Promise.all pour les counts (via service.getAll)
  - grid de stat cards par modèle avec lien vers la list page
"""
from __future__ import annotations

import logging
import os
import pathlib

logger = logging.getLogger(__name__)


def _service_var(camel: str) -> str:
    return f"{camel}Service"


def _service_import(camel: str, kebab: str) -> str:
    return f"import {{ {_service_var(camel)} }} from '@/lib/services/{kebab}.service'"


def generate_hub_page(spec_obj, model_contexts: dict, project_workdir: str) -> dict[str, str]:
    """
    Génère app/dashboard/page.tsx de manière déterministe.

    Retourne {path: content} à intégrer dans template_written.
    Retourne {} si spec_obj est None ou s'il n'y a pas de modèles.
    """
    if spec_obj is None or not model_contexts:
        return {}

    models = [ctx for ctx in model_contexts.values() if ctx.list_page_path]
    if not models:
        return {}

    # ── Imports services ──────────────────────────────────────────────────────
    service_imports = "\n".join(
        _service_import(ctx.camel, ctx.kebab) for ctx in models
    )

    # ── Promise.all ligne ─────────────────────────────────────────────────────
    promise_vars = ", ".join(f"{ctx.camel}Items" for ctx in models)
    promise_calls = ",\n    ".join(
        f"{_service_var(ctx.camel)}.getAll(userId)" for ctx in models
    )

    # ── Count vars ────────────────────────────────────────────────────────────
    count_lines = "\n  ".join(
        f"const {ctx.camel}Count = {ctx.camel}Items.length" for ctx in models
    )

    # ── Stat cards ────────────────────────────────────────────────────────────
    cards = "\n        ".join(
        f"""<div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">{ctx.title_plural}</p>
          <p className="text-3xl font-bold text-foreground mb-4">{{{ctx.camel}Count}}</p>
          <Link href="{ctx.list_page_path}" className="text-sm text-primary hover:underline">
            Gérer →
          </Link>
        </div>"""
        for ctx in models
    )

    content = f"""\
import Link from 'next/link'
import {{ auth }} from '@clerk/nextjs/server'
import {{ redirect }} from 'next/navigation'
{service_imports}

export const dynamic = 'force-dynamic'

export default async function DashboardPage() {{
  const {{ userId }} = await auth()
  if (!userId) redirect('/sign-in')

  const [{promise_vars}] = await Promise.all([
    {promise_calls},
  ])

  {count_lines}

  return (
    <main className="container mx-auto p-8">
      <h1 className="text-2xl font-bold text-foreground mb-6">Tableau de bord</h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {cards}
      </div>
    </main>
  )
}}
"""

    dest = "app/dashboard/page.tsx"
    abs_path = pathlib.Path(project_workdir) / "app" / "dashboard" / "page.tsx"
    try:
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_text(content, encoding="utf-8")
        logger.info("[hub_generator] app/dashboard/page.tsx généré (%d modèles)", len(models))
    except Exception as _e:
        logger.warning("[hub_generator] écriture échouée : %s", _e)
        return {}

    return {dest: content}
