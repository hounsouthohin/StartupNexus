"""
agents/stacks/nextjs_clerk_prisma/dev_middleware_generator.py
──────────────────────────────────────────────────────────────
Génération DÉTERMINISTE de middleware.ts depuis ProjectSpec.

Le middleware Clerk est généré dynamiquement depuis spec.get_public_pages() —
les routes publiques du brief sont injectées dans createRouteMatcher().
Cela garantit que les visiteurs anonymes peuvent accéder aux pages marquées
auth=false dans le brief, sans que le développeur doive modifier middleware.ts.

Sans ce générateur, middleware.ts utilisait un template fixe qui ne protégeait
que /sign-in et /sign-up — toutes les autres routes étaient bloquées pour les
visiteurs anonymes, contredisant le flag auth=false dans le brief.

Intégration dans dev_graph.py :
    mw_files = generate_middleware(spec_obj, project_workdir)
    template_written.update(mw_files)   # LLM ne peut pas écraser
"""
from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

# Routes Clerk toujours publiques — indépendantes du brief
_CLERK_PUBLIC_ROUTES = ["/sign-in(.*)", "/sign-up(.*)"]


def generate_middleware(spec, project_workdir: str) -> dict[str, str]:
    """
    Génère middleware.ts avec les routes publiques extraites du brief.

    Les routes publiques incluent :
    - /sign-in(.*) et /sign-up(.*) — toujours présentes (Clerk)
    - Chaque page avec auth_required=False dans le brief (ex: /blog → /blog(.*))

    Les routes dynamiques ([id]) sont exclues du matcher car elles sont couvertes
    par le pattern wildcard de la route parent (ex: /blog/[id] couvert par /blog(.*)).

    Retourne {rel_path: content} pour intégration dans template_written.
    """
    public_paths: list[str] = list(_CLERK_PUBLIC_ROUTES)

    for page in spec.get_public_pages():
        path = page.path.rstrip("/")
        # Exclure la racine '/' (gérée par redirect déterministe)
        # Exclure les routes dynamiques (couvertes par le parent)
        if not path or "[" in path:
            continue
        pattern = f"{path}(.*)"
        if pattern not in public_paths:
            public_paths.append(pattern)

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
