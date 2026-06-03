"""
agents/stacks/nextjs_clerk_prisma/dev_middleware_generator.py
──────────────────────────────────────────────────────────────
Génération DÉTERMINISTE de middleware.ts depuis ProjectSpec.

Le middleware Clerk est généré dynamiquement depuis spec.get_public_pages() —
les routes publiques du brief sont injectées dans createRouteMatcher().

RÈGLE DE PRÉCISION : chaque page publique est ajoutée avec son chemin EXACT.
Jamais de wildcard parent (.*) — cela rendrait publics des sous-chemins
auth=true comme /recipes/new alors que seule /recipes est publique.

Avant (bug) : '/recipes(.*)' → /recipes/new accessible sans auth
Après (fix) : '/recipes' + '/recipes/:id' → seulement les pages déclarées publiques

Intégration dans dev_graph.py :
    mw_files = generate_middleware(spec_obj, project_workdir)
    template_written.update(mw_files)   # LLM ne peut pas écraser
"""
from __future__ import annotations

import logging
import os
import re as _re

logger = logging.getLogger(__name__)

# Routes Clerk toujours publiques — indépendantes du brief
_CLERK_PUBLIC_ROUTES = ["/sign-in(.*)", "/sign-up(.*)"]

_DYNAMIC_SEG_RE = _re.compile(r"\[(\w+)\]")


def _to_clerk_pattern(path: str) -> str:
    """Convertit les segments dynamiques Next.js en format Clerk.
    /recipes/[id] → /recipes/:id   (chemin exact, pas de wildcard)
    """
    return _DYNAMIC_SEG_RE.sub(r":\1", path)


def generate_middleware(spec, project_workdir: str) -> dict[str, str]:
    """
    Génère middleware.ts avec les routes publiques extraites du brief.

    Les routes publiques incluent :
    - /sign-in(.*) et /sign-up(.*) — toujours présentes (Clerk)
    - Chaque page auth_required=False dans le brief — chemin EXACT par page.

    Chaque page publique est ajoutée individuellement. Cela garantit que
    /recipes/new (auth=true) reste protégé même si /recipes (auth=false) est public.
    """
    public_paths: list[str] = list(_CLERK_PUBLIC_ROUTES)

    for page in spec.get_public_pages():
        path = page.path.rstrip("/")
        if not path:
            continue
        clerk_pattern = _to_clerk_pattern(path)
        if clerk_pattern not in public_paths:
            public_paths.append(clerk_pattern)

    matcher_entries = ",\n  ".join(f"'{p}'" for p in public_paths)

    content = "\n".join([
        "import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server';",
        "",
        "const isPublicRoute = createRouteMatcher([",
        f"  {matcher_entries},",
        "]);",
        "",
        "export default clerkMiddleware(async (auth, req) => {",
        "  if (!isPublicRoute(req)) await auth.protect();",
        "});",
        "",
        "export const config = {",
        "  matcher: [",
        "    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',",
        "    '/(api|trpc)(.*)',",
        "  ],",
        "};",
        "",
    ])

    rel_path = "middleware.ts"
    abs_path = os.path.join(project_workdir, rel_path)

    try:
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(
            "[middleware_gen] ✓ middleware.ts généré — routes publiques : %s",
            [p.path for p in spec.get_public_pages() if p.path and "[" not in p.path],
        )
    except Exception as e:
        logger.error("[middleware_gen] ✗ Erreur écriture middleware.ts : %s", e)
        return {}

    return {rel_path: content}
