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
      0. lib/services/*.ts   (DAL — générés par le LLM avec contrat d'interface)
      1. app/**/actions.ts   (Server Actions — mutations via service)
      2. app/api/**/route.ts (webhooks uniquement)
      3. app/**/page.tsx     (Server Components — lecture via service)
    """
    template_set = set(template_files)
    entries: list[FilePlanEntry] = []

    # ── 0. Services lib/services/{model}.service.ts ────────────────────────────
    # Générés par le LLM AVANT les actions (les actions importent depuis les services).
    # Chaque service expose : getAll, getById, create, update, delete + méthodes enrichies.
    for model in spec.models:
        kebab = _pascal_to_kebab(model.name)
        camel = _pascal_to_camel(model.name)
        file_path = f"lib/services/{kebab}.service.ts"
        if file_path in template_set:
            continue

        owner = model.resolved_owner()

        # Champs DateTime non auto (nécessitent new Date() côté service)
        _datetime_fields = [
            f.name for f in model.fields
            if f.type.rstrip("?").rstrip("[]") == "DateTime"
            and "@default(now())" not in (f.attributes or "").lower()
            and "@updatedat" not in (f.attributes or "").lower().replace(" ", "")
            and f.name.lower() not in {"id", "createdat", "updatedat", "deletedat"}
            and f.name.lower() != owner.lower()
        ]

        # Relations disponibles pour include
        _relation_names = [
            f.name for f in model.fields
            if "@relation" in (f.attributes or "")
        ]

        _dt_hint = (
            f" Champs DateTime : {', '.join(_datetime_fields)} — déjà Date (z.coerce.date()) — passer directement à Prisma."
            if _datetime_fields else ""
        )
        _rel_hint = (
            f" Relations disponibles pour include : {', '.join(_relation_names)}."
            if _relation_names else ""
        )

        entries.append(FilePlanEntry(
            path=file_path,
            role="service",
            context_hint=(
                f"Service DAL pour {model.name}. owner_field='{owner}'. "
                f"INTERFACE OBLIGATOIRE : "
                f"export const {camel}Service = {{ "
                f"getAll({owner}), getById({owner}, id), "
                f"create({owner}, data: Create{model.name}Input), "
                f"update(id, data: Update{model.name}Input), "
                f"delete({owner}, id) }}. "
                f"Imports : import prisma from '@/lib/prisma' — "
                f"import type {{ {model.name} }} from '@prisma/client' — "
                f"import type {{ Create{model.name}Input, Update{model.name}Input }} from '@/lib/types'."
                f"{_dt_hint}{_rel_hint}"
            ),
        ))

    # F-04: index stable segment→modèle (évite rstrip("s") fragile sur "address", "news"...)
    # Couvre : "project" → Project, "projects" → Project, "leave-requests" → LeaveRequest
    _model_by_seg: dict[str, object] = {}
    for _bm in spec.models:
        _bk = _pascal_to_kebab(_bm.name)
        _model_by_seg[_bk] = _bm
        _model_by_seg[_bk + "s"] = _bm

    # ── 1. Server Actions — une par modèle (chemin via _find_list_page, même logique que dev_actions_generator)
    # Dériver le path depuis la page liste garantit l'alignement avec les fichiers pré-générés.
    # Si le fichier est dans template_set (pré-généré), il est sauté → LLM ne le réécrit pas.
    # Si le générateur a échoué (non-bloquant), le planner le planifie avec le bon chemin.
    try:
        from agents.stacks.nextjs_clerk_prisma.dev_actions_generator import _find_list_page as _flp
        _actions_by_page: dict[str, list] = {}
        for _bm in spec.models:
            _lp = _flp(_bm.name, spec)
            _route_dir = _lp.lstrip("/")
            _actions_by_page.setdefault(_route_dir, []).append(_bm)
    except Exception:
        # Fallback route-based si dev_actions_generator non disponible
        _actions_by_page = {}
        for route in spec.routes:
            if _is_webhook_route(route.path) or not _is_mutation_method(route.method):
                continue
            seg = _route_model_segment(route.path)
            _m = _model_by_seg.get(seg)
            if _m:
                _actions_by_page.setdefault(seg, []).append(_m)

    for seg, _seg_models in _actions_by_page.items():
        file_path = f"app/{seg}/actions.ts"
        if file_path in template_set:
            continue  # pré-généré par dev_actions_generator — ne pas replanifier
        mutations = [
            f"{r.method.upper()} {r.path}"
            for r in spec.routes
            if not _is_webhook_route(r.path) and _is_mutation_method(r.method)
            and _route_model_segment(r.path) == seg
        ]
        mutations_str = ", ".join(mutations) if mutations else "create / update / delete"
        mutations_str = ", ".join(mutations)

        # Modèles impliqués : ceux du groupe (déjà déterminés par _find_list_page)
        # + modèles imbriqués détectés dans les routes (ex: /api/tasks/[id]/comments → Comment)
        _relevant_models = list(_seg_models)
        for route_str in mutations:
            route_path = route_str.split(" ", 1)[1] if " " in route_str else route_str
            nested_parts = route_path.lstrip("/").split("/")
            for ns in nested_parts[2:]:
                if not ns.startswith("[") and ns:
                    _secondary = _model_by_seg.get(ns)
                    if _secondary and _secondary not in _relevant_models:
                        _relevant_models.append(_secondary)

        service_hint = ""
        if _relevant_models:
            svc_parts = []
            for _rm in _relevant_models:
                _rc = _pascal_to_camel(_rm.name)
                _rk = _pascal_to_kebab(_rm.name)
                _ro = _rm.resolved_owner()
                svc_parts.append(
                    f"import {{ {_rc}Service }} from '@/lib/services/{_rk}.service' (owner: {_ro})"
                )
            service_hint = "Services : " + " | ".join(svc_parts) + "."
            # Schemas de TOUS les modèles impliqués (primary + nested)
            _schema_imports = ", ".join(
                f"Create{_rm.name}Schema, Update{_rm.name}Schema"
                for _rm in _relevant_models
            )
            service_hint += (
                f" Schema : import {{ {_schema_imports} }}"
                f" from '@/lib/schemas'."
            )

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
    # Modèles ayant des @relation — pour le fallback page racine (/)
    _models_with_relations = [
        m for m in spec.models
        if any("@relation" in (f.attributes or "") for f in m.fields)
    ]

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
            "LECTURE SEULE — zéro mutation dans ce fichier : "
            "pas de prisma.create/update/delete, pas de Server Action appelée directement. "
            "Les mutations se font UNIQUEMENT depuis actions.ts."
        )
        hint_parts.append(
            "Récupérer les données VIA LE SERVICE : xxxService.getAll(userId) — JAMAIS prisma directement dans page.tsx. "
            "Le service retourne SerializedXxx (dates déjà string) — NE PAS appeler .toISOString() sur ces données."
        )

        # Hint params pour les pages dynamiques (ex: app/projects/[id]/page.tsx)
        _dynamic_segments = [seg[1:-1] for seg in ppath.split("/") if seg.startswith("[") and seg.endswith("]")]
        if _dynamic_segments:
            _params_type = ", ".join(f"{seg}: string" for seg in _dynamic_segments)
            _params_destructure = ", ".join(_dynamic_segments)
            hint_parts.append(
                f"PAGE DYNAMIQUE — TYPER params OBLIGATOIREMENT : "
                f"export default async function Page({{ params }}: {{ params: {{ {_params_type} }} }}) "
                f"{{ const {{ {_params_destructure} }} = params; — "
                f"NE PAS laisser params non typé (TS7031 fatal)."
            )

        # Hint getAllWithRelations : SPÉCIFIQUE au modèle primaire de la page
        # Dérivé des segments statiques du chemin via _model_by_seg — jamais générique
        _static_segs = [s for s in ppath.split("/") if s and not s.startswith("[")]
        _primary_model = _model_by_seg.get(_static_segs[0]) if _static_segs else None
        if _primary_model is not None:
            _prel = [f.name for f in _primary_model.fields if "@relation" in (f.attributes or "")]
            if _prel:
                _pcamel = _pascal_to_camel(_primary_model.name)
                _powner = _primary_model.resolved_owner()
                hint_parts.append(
                    f"Ce modèle ({_primary_model.name}) a des relations : {', '.join(_prel)}. "
                    f"Si la page affiche ces champs, utiliser {_pcamel}Service.getAllWithRelations({_powner}) "
                    f"au lieu de getAll() — Prisma ne retourne pas les relations sans include (TS2551 fatal). "
                    f"NE PAS appeler getAllWithRelations sur un service qui n'est pas {_pcamel}Service."
                )
            else:
                # Pas de @relation explicite — détecter les FK implicites (projectId → Project)
                _spec_names_lower = {m.name.lower(): m.name for m in spec.models}
                _implicit_fk = [
                    (f.name, _spec_names_lower[f.name[:-2].lower()])
                    for f in _primary_model.fields
                    if f.type.rstrip("?") == "String"
                    and f.name.endswith("Id")
                    and f.name[:-2].lower() in _spec_names_lower
                ]
                if _implicit_fk:
                    _fk_warn = " | ".join(
                        f"`{_primary_model.name.lower()}.{mn[0].lower() + mn[1:]}` N'EXISTE PAS"
                        f" — utiliser `{fk}` (ID scalaire uniquement, pas l'objet)"
                        for fk, mn in _implicit_fk
                    )
                    hint_parts.append(
                        f"ATTENTION FK IMPLICITES : {_primary_model.name} a "
                        f"{', '.join(fk for fk, _ in _implicit_fk)} sans @relation Prisma. "
                        f"Prisma retourne UNIQUEMENT les champs scalaires — NE PAS accéder aux objets reliés. "
                        f"{_fk_warn}."
                    )
        elif _models_with_relations:
            # Page racine (/) : segment non identifiable depuis le chemin
            _rel_calls = " | ".join(
                f"{_pascal_to_camel(m.name)}Service.getAllWithRelations({m.resolved_owner()})"
                for m in _models_with_relations
            )
            hint_parts.append(
                f"Si la page affiche des champs relationnels, utiliser getAllWithRelations : {_rel_calls} — "
                f"chaque service ne l'a que si son modèle Prisma a un champ @relation (TS2551 fatal sinon)."
            )

        # Page-client générée AVANT page.tsx (F3) :
        # page-client.tsx définit son interface de props → page.tsx peut ensuite
        # lire ce fichier (injecté par executor_node) et passer exactement les bonnes props.
        # Sans cet ordre, page.tsx est écrit en premier et ignore les props du client → TS2741.
        _pages_detail = getattr(spec, "pages_detail", {}) or {}
        _page_detail_str = str(_pages_detail.get(page.path, ""))
        if "[INTERACTIVE]" in _page_detail_str:
            client_file = "app/page-client.tsx" if not ppath else f"app/{ppath}/page-client.tsx"
            if client_file not in template_set:
                _comp_name = (ppath.replace("/", "-") or "home").title().replace("-", "")
                entries.append(FilePlanEntry(
                    path=client_file,
                    role="page_client",
                    context_hint=(
                        f"'use client' LIGNE 1 OBLIGATOIRE. Client Component pour {file_path}. "
                        f"export default function {_comp_name}Client(props: {_comp_name}ClientProps). "
                        f"PROPS INTERFACE : déclarer UNIQUEMENT les props que le Server Component "
                        f"parent peut concrètement passer (données chargées côté serveur). "
                        f"Pour un formulaire de création simple, les props sont vides ou minimales — "
                        f"NE PAS inventer de props required pour des données pré-chargées si le brief "
                        f"ne le demande pas explicitement. "
                        f"Champs nullable → string | null (JAMAIS string | undefined). "
                        f"Importé depuis {file_path} avec DEFAULT import : "
                        f"import {_comp_name}Client from './page-client'."
                    ),
                ))

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

    # Services (générés par le LLM → dans le plan, pas dans template_set)
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
