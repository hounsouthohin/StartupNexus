"""
agents/dev_pages_generator.py
──────────────────────────────
Génération déterministe des loading.tsx uniquement.

Option B (Avril 2026) : lib/types.ts et lib/services/ sont désormais générés
par le LLM — auteur unique du code applicatif, cohérence garantie.

Seuls les loading.tsx restent déterministes : squelette trivial, aucun contrat
à communiquer au LLM, toujours correct quel que soit le brief.
"""
from __future__ import annotations

import logging
import os

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
