# agents/planner.py
"""
Plan-and-Execute V2 — génération déterministe du plan fichier par fichier.
Aucun LLM impliqué : l'ordre est dérivé directement depuis ProjectSpec.

Fichiers pré-générés de manière déterministe AVANT que le LLM démarre :
  - lib/types.ts         (dev_types_generator)
  - lib/schemas.ts       (dev_zod_generator)
  - lib/services/*.ts    (dev_service_generator)
Ces fichiers sont dans template_written → exclus automatiquement du plan.

Le plan LLM ne couvre que :
  1. app/**/actions.ts  — Server Actions (mutations) — une par modèle Prisma
  2. app/**/page.tsx    — Server Components (lecture directe Prisma)
  3. app/api/**/route.ts — routes conservées uniquement pour : webhooks + toute route
                           explicitement marquée comme non-mutation (GET public)

Règle Level 1 :
  - Mutations (POST, PUT, PATCH, DELETE) → Server Actions
  - Lecture → Server Component lit Prisma directement (pas de GET route)
  - Webhooks (/api/webhooks/*) → route.ts (obligatoire pour Svix/Stripe)
"""
from __future__ import annotations

import re as _re
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from agents.project_spec import ProjectSpec


def _pascal_to_kebab(name: str) -> str:
    """Convertit PascalCase en kebab-case. Ex: LeaveRequest → leave-request, Task → task."""
    return _re.sub(r"(?<!^)(?=[A-Z])", "-", name).lower()


def _pascal_to_camel(name: str) -> str:
    return name[0].lower() + name[1:] if name else name


def _route_model_segment(path: str) -> str:
    """
    Extrait le segment de modèle depuis un chemin d'API.
    '/api/projects/[id]' → 'projects'
    '/api/leave-requests' → 'leave-requests'
    """
    clean = path.lstrip("/")
    if clean.startswith("api/"):
        clean = clean[4:]
    parts = clean.split("/")
    return parts[0] if parts else "unknown"


def _is_webhook_route(path: str) -> bool:
    return "webhook" in path.lower() or "svix" in path.lower() or "stripe" in path.lower()


def _is_mutation_method(method: str) -> bool:
    return method.upper() in ("POST", "PUT", "PATCH", "DELETE")


class FilePlanEntry(BaseModel):
    path: str
    role: str        # "actions" | "route" | "page"
    context_hint: str = ""


def make_deterministic_plan(
    spec: "ProjectSpec",
    template_files: list[str],
) -> list[FilePlanEntry]:
    """
    Retourne la liste ordonnée des fichiers que l'executor doit générer.
    Les fichiers déjà écrits par les templates sont exclus.

    Ordre :
      1. app/**/actions.ts   (Server Actions — mutations Prisma via service)
      2. app/**/page.tsx     (Server Components — lecture directe Prisma)
      3. app/api/**/route.ts (webhooks uniquement)
    """
    template_set = set(template_files)
    entries: list[FilePlanEntry] = []

    # ── 1. Server Actions — une par segment de modèle avec des mutations ──────
    # On groupe les routes de mutation par segment de modèle (ex: 'projects').
    # Les GET routes sont ignorées : les Server Components lisent Prisma directement.
    _actions_segments: dict[str, list[str]] = {}

    for route in spec.routes:
        if _is_webhook_route(route.path):
            continue
        if not _is_mutation_method(route.method):
            continue
        seg = _route_model_segment(route.path)
        _actions_segments.setdefault(seg, []).append(
            f"{route.method.upper()} {route.path}"
        )

    for seg, mutations in _actions_segments.items():
        file_path = f"app/{seg}/actions.ts"
        mutations_str = ", ".join(mutations)

        # Trouver le service associé depuis la spec
        # Le segment ressemble à 'projects' ou 'leave-requests'
        service_hint = ""
        for model in spec.models:
            if _pascal_to_kebab(model.name) == seg or _pascal_to_kebab(model.name) + "s" == seg:
                camel = _pascal_to_camel(model.name)
                owner = model.owner_field or "userId"
                service_hint = (
                    f"Service : import {{ {camel}Service }} from '@/lib/services/{_pascal_to_kebab(model.name)}.service' — "
                    f"Schema : import {{ Create{model.name}Schema, Update{model.name}Schema }} from '@/lib/schemas' — "
                    f"owner field : {owner}."
                )
                break

        entries.append(FilePlanEntry(
            path=file_path,
            role="actions",
            context_hint=(
                f"'use server' — Server Actions pour : {mutations_str}. "
                "CHAQUE action DOIT : (1) const { userId } = await auth() — if (!userId) throw new Error('Unauthorized'); "
                "(2) valider avec le schéma Zod .safeParse(data); "
                "(3) appeler le service (jamais prisma directement dans les actions). "
                + service_hint
            ),
        ))

    # ── 2. Webhooks routes ─────────────────────────────────────────────────────
    _webhook_files: set[str] = set()
    for route in spec.routes:
        if not _is_webhook_route(route.path):
            continue
        rpath = route.path
        if rpath.startswith("/api"):
            rpath = rpath[4:]
        file_path = f"app/api{rpath.rstrip('/')}/route.ts"
        if file_path in _webhook_files:
            continue
        _webhook_files.add(file_path)
        entries.append(FilePlanEntry(
            path=file_path,
            role="route",
            context_hint=(
                "Webhook handler — POST uniquement. "
                "Vérifier la signature Svix/Stripe avant de traiter. "
                "Retourner NextResponse.json({}, {status:200}) si OK."
            ),
        ))

    # ── 3. Pages ───────────────────────────────────────────────────────────────
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
            "Récupérer les données DIRECTEMENT avec prisma (pas de fetch vers /api). "
            "Sérialiser les dates avant Client Components : .toISOString()."
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

    # Services (pré-générés → dans template_set)
    for model in spec.models:
        svc = f"lib/services/{_pascal_to_kebab(model.name)}.service.ts"
        if svc not in plan_paths:
            missing.append(svc)

    # Actions ou routes
    for route in spec.routes:
        if _is_webhook_route(route.path):
            rpath = route.path
            if rpath.startswith("/api"):
                rpath = rpath[4:]
            rf = f"app/api{rpath.rstrip('/')}/route.ts"
            if rf not in plan_paths:
                missing.append(rf)
        elif _is_mutation_method(route.method):
            seg = _route_model_segment(route.path)
            af = f"app/{seg}/actions.ts"
            if af not in plan_paths:
                missing.append(af)

    for page in spec.pages:
        ppath = page.path.strip("/")
        pf = "app/page.tsx" if not ppath else f"app/{ppath}/page.tsx"
        if pf not in plan_paths:
            missing.append(pf)

    return list(dict.fromkeys(missing))  # dédupliqué, ordre préservé
