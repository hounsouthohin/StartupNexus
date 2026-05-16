"""
agents/dev_navigation_generator.py
────────────────────────────────────
Génération DÉTERMINISTE de app/components/navigation.tsx depuis ProjectSpec.

Lit spec.pages[] et génère un composant Navigation avec un lien par page
principale (les pages /new et les pages dynamiques [id] sont exclues du nav —
elles sont accessibles depuis leurs pages parentes).

Intégration dans dev_graph.py (après generate_middleware) :
    nav_files = generate_navigation(spec_obj, project_workdir)
    template_written.update(nav_files)

app/layout.tsx (template) importe <Navigation /> depuis ce composant.
"""
from __future__ import annotations

import logging
import os
import re as _re

logger = logging.getLogger(__name__)

# Pages exclues de la navigation principale (accessibles via leurs parents)
_EXCLUDED_SUFFIXES = ("/new", "/edit")
_EXCLUDED_PATTERNS = (_re.compile(r"/\[.*?\]"),)  # segments dynamiques [id]


def _is_nav_page(path: str) -> bool:
    """Retourne True si la page doit apparaître dans la navigation principale."""
    for suffix in _EXCLUDED_SUFFIXES:
        if path.rstrip("/").endswith(suffix):
            return False
    for pattern in _EXCLUDED_PATTERNS:
        if pattern.search(path):
            return False
    return True


def _label_from_path(path: str) -> str:
    """
    Génère un label lisible depuis un chemin URL.
      /dashboard      → Dashboard
      /blog           → Blog
      /categories     → Catégories
      /leave-requests → Leave Requests
    """
    segment = path.rstrip("/").split("/")[-1] or "Home"
    # kebab-case → mots séparés
    words = segment.replace("-", " ").replace("_", " ")
    return words.title()


def generate_navigation(spec, project_workdir: str) -> dict[str, str]:
    """
    Génère app/components/navigation.tsx et l'écrit sur disque.
    Retourne {chemin_relatif: contenu} pour template_written.
    """
    pages = getattr(spec, "pages", []) or []

    nav_links: list[tuple[str, str]] = []  # (path, label)
    for page in pages:
        path = getattr(page, "path", "") or ""
        if not path or not _is_nav_page(path):
            continue
        label = _label_from_path(path)
        nav_links.append((path, label))

    # Si aucune page nav, on génère quand même un composant vide valide
    if not nav_links:
        logger.warning("[navigation_generator] Aucune page nav trouvée dans la spec")

    link_lines = "\n".join(
        f'      <Link href="{path}" className="text-sm text-gray-600 hover:text-gray-900 font-medium">'
        f"{label}</Link>"
        for path, label in nav_links
    )

    content = f"""\
import Link from 'next/link'

export default function Navigation() {{
  return (
    <nav className="flex items-center gap-6">
{link_lines}
    </nav>
  )
}}
"""

    rel_path = "app/components/navigation.tsx"
    abs_path = os.path.join(project_workdir, "app", "components", "navigation.tsx")
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    try:
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(
            "[navigation_generator] ✓ %s généré (%d liens)", rel_path, len(nav_links)
        )
    except Exception as e:
        logger.error("[navigation_generator] ✗ Erreur écriture %s : %s", rel_path, e)

    return {rel_path: content}
