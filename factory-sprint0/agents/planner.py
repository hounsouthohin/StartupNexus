# agents/planner.py
"""
Plan-and-Execute V2 — génération déterministe du plan fichier par fichier.
Aucun LLM impliqué : l'ordre est dérivé directement depuis ProjectSpec.

lib/types.ts et lib/services/*.ts sont pré-générés de manière déterministe
par dev_types_generator et dev_service_generator AVANT que le LLM démarre.
Le plan LLM ne couvre que :
  1. app/api/**/route.ts   — une entrée par ApiRoute
  2. app/**/page.tsx       — une entrée par AppPage
"""
from __future__ import annotations

import re as _re
from typing import TYPE_CHECKING, List

from pydantic import BaseModel

if TYPE_CHECKING:
    from agents.project_spec import ProjectSpec


def _pascal_to_kebab(name: str) -> str:
    """Convertit PascalCase en kebab-case. Ex: LeaveRequest → leave-request, Task → task."""
    return _re.sub(r"(?<!^)(?=[A-Z])", "-", name).lower()


class FilePlanEntry(BaseModel):
    path: str
    role: str        # "types" | "service" | "route" | "page" | "page_client"
    context_hint: str = ""


def make_deterministic_plan(
    spec: "ProjectSpec",
    template_files: list[str],
) -> list[FilePlanEntry]:
    """
    Retourne la liste ordonnée des fichiers que l'executor doit générer.
    Les fichiers déjà écrits par les templates sont exclus.
    """
    template_set = set(template_files)
    entries: list[FilePlanEntry] = []

    model_names = [m.name for m in spec.models]

    # lib/types.ts et lib/services/*.ts sont pré-générés de manière déterministe
    # par dev_types_generator et dev_service_generator avant que le LLM démarre.
    # Ils sont ajoutés à template_written → exclus automatiquement du plan ci-dessous.

    # 1 — app/api/**/route.ts : une entrée par FICHIER (pas par ApiRoute).
    # Plusieurs méthodes HTTP sur le même chemin → même fichier route.ts.
    # On déduplique en groupant les ApiRoutes par file_path et en fusionnant les context_hints.
    _routes_by_file: dict[str, list[str]] = {}
    for route in spec.routes:
        rpath = route.path
        if rpath.startswith("/api"):
            rpath = rpath[4:]
        file_path = f"app/api{rpath.rstrip('/')}/route.ts"
        _routes_by_file.setdefault(file_path, []).append(f"{route.method} {route.path}")

    for file_path, methods in _routes_by_file.items():
        methods_str = ", ".join(methods)
        entries.append(FilePlanEntry(
            path=file_path,
            role="route",
            context_hint=(
                f"Handlers : {methods_str}. "
                "OBLIGATOIRE en debut de chaque handler : "
                "const { userId } = await auth(); "
                "if (!userId) return NextResponse.json({error:'Unauthorized'},{status:401}); "
                "— userId est string apres ce guard, jamais string|null."
            ),
        ))

    # 4 — app/**/page.tsx : une par AppPage
    for page in spec.pages:
        ppath = page.path.strip("/")
        file_path = "app/page.tsx" if not ppath else f"app/{ppath}/page.tsx"
        hint_parts = [f"Server Component. auth_required={page.auth_required}."]
        if page.auth_required:
            hint_parts.append(
                "import { auth } from '@clerk/nextjs/server' — "
                "const { userId } = await auth(); if (!userId) redirect('/sign-in');"
            )
        hint_parts.append(
            "Sérialiser les dates Prisma avant de passer aux Client Components : "
            ".toISOString()"
        )
        entries.append(FilePlanEntry(
            path=file_path,
            role="page",
            context_hint=" ".join(hint_parts),
        ))

    # Exclure les fichiers déjà écrits par les templates
    return [e for e in entries if e.path not in template_set]


def validate_plan(
    plan: list[FilePlanEntry],
    spec: "ProjectSpec",
    template_files: list[str],
) -> list[str]:
    """
    Vérifie que le plan couvre toutes les entités de la spec.
    Retourne la liste des fichiers manquants.
    """
    template_set = set(template_files)
    plan_paths = {e.path for e in plan} | template_set
    missing: list[str] = []

    for model in spec.models:
        svc = f"lib/services/{_pascal_to_kebab(model.name)}.service.ts"
        if svc not in plan_paths:
            missing.append(svc)

    for route in spec.routes:
        rpath = route.path
        if rpath.startswith("/api"):
            rpath = rpath[4:]
        rf = f"app/api{rpath.rstrip('/')}/route.ts"
        if rf not in plan_paths:
            missing.append(rf)

    for page in spec.pages:
        ppath = page.path.strip("/")
        pf = "app/page.tsx" if not ppath else f"app/{ppath}/page.tsx"
        if pf not in plan_paths:
            missing.append(pf)

    return missing
