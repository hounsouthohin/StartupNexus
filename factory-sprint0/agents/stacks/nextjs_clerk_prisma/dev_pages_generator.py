"""
agents/dev_pages_generator.py
──────────────────────────────
Génération déterministe des fichiers de scaffold.

- loading.tsx : squelette UI trivial, jamais incorrect.
- page.tsx stubs (R6 — Avril 2026) : scaffolds préventifs avec les imports
  requis pré-remplis (auth Clerk, redirect, notFound). Le LLM complète la
  logique métier en lisant le stub existant — il voit les imports dès le départ.
  Sans ces stubs, le LLM générait parfois des pages sans imports, forçant une
  boucle de correction sous throttling 429.
"""
from __future__ import annotations

import logging
import os
import re

logger = logging.getLogger(__name__)


def _gen_loading_tsx() -> str:
    return "\n".join([
        "export default function Loading() {",
        "  return (",
        '    <main className="container mx-auto p-6">',
        '      <div className="animate-pulse space-y-4">',
        '        <div className="h-8 bg-gray-200 rounded w-48" />',
        '        <div className="h-4 bg-gray-200 rounded w-full" />',
        '        <div className="h-4 bg-gray-200 rounded w-3/4" />',
        '        <div className="h-4 bg-gray-200 rounded w-5/6" />',
        "      </div>",
        "    </main>",
        "  )",
        "}",
    ])


def _page_path_to_loading(page_path: str) -> str:
    clean = page_path.strip("/")
    if not clean:
        return "app/loading.tsx"
    return f"app/{clean}/loading.tsx"


def generate_loading_files(spec: "ProjectSpec", project_workdir: str) -> None:  # type: ignore[name-defined]
    """
    Écrit app/<path>/loading.tsx pour chaque page protégée (auth_required=True).
    Skippé si le fichier existe déjà.
    """
    count = 0
    for page in spec.pages:
        if not page.auth_required:
            continue
        loading_rel = _page_path_to_loading(page.path)
        loading_abs = os.path.join(project_workdir, loading_rel.replace("/", os.sep))
        if os.path.exists(loading_abs):
            continue
        os.makedirs(os.path.dirname(loading_abs), exist_ok=True)
        with open(loading_abs, "w", encoding="utf-8") as f:
            f.write(_gen_loading_tsx())
        count += 1
        logger.info("[pages_gen] ✓ loading : %s", loading_rel)

    logger.info("[pages_gen] %d loading.tsx écrits", count)


# ── Page stubs (R6) ──────────────────────────────────────────────────────────

def _component_name(page_path: str) -> str:
    """'dashboard/users/[id]' → 'DashboardUsersIdPage'"""
    parts = [p for p in page_path.strip("/").split("/") if p]
    cleaned = []
    for p in parts:
        p = re.sub(r"[\[\]\.]+", "", p)   # retire [ ] et points
        p = re.sub(r"[^a-zA-Z0-9]", " ", p).title().replace(" ", "")
        if p:
            cleaned.append(p)
    return ("".join(cleaned) or "Home") + "Page"


def _gen_page_stub(page_path: str) -> str:
    """
    Génère un stub page.tsx pour un Server Component Next.js avec auth Clerk.
    Le stub contient les imports obligatoires pré-remplis. Le LLM lit ce fichier
    et complète la logique métier sans risquer d'oublier les imports.
    """
    dynamic_params = re.findall(r"\[([^\]]+)\]", page_path)
    component = _component_name(page_path)

    lines: list[str] = [
        "import { auth } from '@clerk/nextjs/server';",
        "import { redirect } from 'next/navigation';",
    ]
    if dynamic_params:
        lines.append("import { notFound } from 'next/navigation';")

    lines.append("")

    if dynamic_params:
        param_fields = ", ".join(f"{p}: string" for p in dynamic_params)
        lines.append(f"type Props = {{ params: {{ {param_fields} }} }};")
        lines.append("")
        lines.append(f"export default async function {component}({{ params }}: Props) {{")
    else:
        lines.append(f"export default async function {component}() {{")

    lines.extend([
        "  const { userId } = await auth();",
        "  if (!userId) redirect('/sign-in');",
        "",
        "  return <div />;",
        "}",
    ])

    return "\n".join(lines) + "\n"


def _gen_error_tsx() -> str:
    """Client Component obligatoire pour Next.js error boundaries."""
    return "\n".join([
        "'use client'",
        "",
        "export default function Error({",
        "  error,",
        "  reset,",
        "}: {",
        "  error: Error & { digest?: string }",
        "  reset: () => void",
        "}) {",
        "  return (",
        '    <main className="container mx-auto p-6 text-center">',
        '      <h2 className="text-xl font-semibold text-red-600 mb-4">',
        "        Une erreur est survenue",
        "      </h2>",
        '      <p className="text-gray-500 mb-6">{error.message}</p>',
        "      <button",
        "        onClick={reset}",
        '        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"',
        "      >",
        "        Réessayer",
        "      </button>",
        "    </main>",
        "  )",
        "}",
    ]) + "\n"


def _gen_not_found_tsx() -> str:
    """Page 404 globale — affichée quand notFound() est appelé."""
    return "\n".join([
        "import Link from 'next/link'",
        "",
        "export default function NotFound() {",
        "  return (",
        '    <main className="container mx-auto p-6 text-center">',
        '      <h2 className="text-2xl font-semibold mb-4">Page introuvable</h2>',
        '      <p className="text-gray-500 mb-6">',
        "        La ressource demandée n'existe pas ou a été supprimée.",
        "      </p>",
        '      <Link href="/" className="text-blue-600 hover:underline">',
        "        Retour à l'accueil",
        "      </Link>",
        "    </main>",
        "  )",
        "}",
    ]) + "\n"


def generate_root_page_if_needed(spec: "ProjectSpec", project_workdir: str) -> bool:  # type: ignore[name-defined]
    """
    Génère un app/page.tsx déterministe (redirect) quand '/' est dans spec.pages
    mais absent de pages_detail — c'est-à-dire quand l'architect l'a injectée
    automatiquement sans que le brief ne la définisse.

    Sans ce guard, le LLM improvise un dashboard complet sur '/' et accède à des
    relations (invoice.client.name) qui n'existent pas dans SerializedXxx → TS2551.

    Retourne True si un fichier a été écrit, False sinon.
    """
    root_page = next((p for p in spec.pages if p.path == "/"), None)
    if root_page is None:
        return False

    # Si pages_detail définit un contenu pour '/', le LLM doit la générer librement
    pages_detail = getattr(spec, "pages_detail", {}) or {}
    if pages_detail.get("/") or pages_detail.get(""):
        return False

    # '/' présente sans pages_detail → redirect déterministe vers la première page réelle
    app_dir = os.path.join(project_workdir, "app")
    os.makedirs(app_dir, exist_ok=True)
    page_path = os.path.join(app_dir, "page.tsx")

    if os.path.exists(page_path):
        return False

    first_real_page = next(
        (p.path for p in spec.pages if p.path != "/" and "[" not in p.path),
        None,
    )
    redirect_target = first_real_page or "/sign-in"

    content = "\n".join([
        "import { redirect } from 'next/navigation'",
        "",
        "export default function Home() {",
        f"  redirect('{redirect_target}')",
        "}",
        "",
    ])

    with open(page_path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info("[pages_gen] ✓ app/page.tsx racine déterministe → redirect('%s')", redirect_target)
    return True


def generate_error_files(spec: "ProjectSpec", project_workdir: str) -> None:  # type: ignore[name-defined]
    """
    Écrit app/error.tsx et app/not-found.tsx si absents.
    Invariants pour toutes les apps de la stack — jamais générés par le LLM.
    """
    app_dir = os.path.join(project_workdir, "app")
    os.makedirs(app_dir, exist_ok=True)

    for filename, content_fn in (
        ("error.tsx", _gen_error_tsx),
        ("not-found.tsx", _gen_not_found_tsx),
    ):
        abs_path = os.path.join(app_dir, filename)
        if os.path.exists(abs_path):
            continue
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content_fn())
        logger.info("[pages_gen] ✓ %s", f"app/{filename}")


def generate_page_stubs(spec: "ProjectSpec", project_workdir: str) -> None:  # type: ignore[name-defined]
    """
    Écrit app/<path>/page.tsx pour chaque page du spec si le fichier n'existe pas.
    Les stubs sont intentionnellement minimalistes : imports corrects + export vide.
    Le LLM les lira (read_file) et écrira la version complète en conservant les imports.
    """
    count = 0
    for page in spec.pages:
        page_rel = f"app/{page.path.strip('/')}/page.tsx" if page.path.strip("/") else "app/page.tsx"
        page_abs = os.path.join(project_workdir, page_rel.replace("/", os.sep))
        if os.path.exists(page_abs):
            continue
        os.makedirs(os.path.dirname(page_abs), exist_ok=True)
        with open(page_abs, "w", encoding="utf-8") as f:
            f.write(_gen_page_stub(page.path))
        count += 1
        logger.info("[pages_gen] ✓ stub : %s", page_rel)

    logger.info("[pages_gen] %d page stubs écrits", count)
