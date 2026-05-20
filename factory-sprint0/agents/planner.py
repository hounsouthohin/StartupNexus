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
  1. app/**/actions.ts       — Server Actions (mutations) — une par modèle Prisma
  2. app/**/page.tsx         — Server Components (lecture directe Prisma)
  3. app/api/**/route.ts     — routes conservées uniquement pour : webhooks
  4. app/**/page-client.tsx  — Client Components UI (Level B) — list/create/detail/edit

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
    contexts: "dict | None" = None,
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
    # Pré-générés par dev_service_generator AVANT le LLM (dans template_written).
    # Skippés ici via `if file_path in template_set`. Listés pour validate_plan uniquement.
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

    # ── 1. Server Actions — une par modèle (chemin via spec.get_list_page_for_model, source de vérité unique)
    # Même logique que dev_actions_generator → alignement garanti avec template_written.
    # Si le fichier est dans template_set (pré-généré), il est sauté → LLM ne le réécrit pas.
    _actions_by_page: dict[str, list] = {}
    for _bm in spec.models:
        _lp = spec.get_list_page_for_model(_bm.name)
        if not _lp:
            continue
        _route_dir = _lp.lstrip("/")
        _actions_by_page.setdefault(_route_dir, []).append(_bm)

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

        # ── page-client.tsx (Level B) — générée AVANT page.tsx ──────────────────
        # Pages avec model (list/create/detail/detail-slug) : le LLM génère le UI.
        # Pages custom [INTERACTIVE] : comportement inchangé.
        _model_name = getattr(page, "model", None)
        _page_type = getattr(page, "page_type", None)
        _pages_detail = getattr(spec, "pages_detail", {}) or {}
        _page_detail_str = str(_pages_detail.get(page.path, ""))
        _client_file = "app/page-client.tsx" if not ppath else f"app/{ppath}/page-client.tsx"
        _client_hint = ""

        if _model_name and _page_type in ("list", "create", "detail", "detail-slug"):
            _serialized = f"Serialized{_model_name}"
            if _page_type == "list":
                # Bug 1 fix : pages publiques n'ont pas d'actions.ts → pas de delete button
                if page.auth_required:
                    _list_actions_hint = (
                        f"Bouton 'Supprimer' via delete{_model_name}.bind(null, item.id) "
                        f"(import depuis ./actions). "
                    )
                else:
                    _list_actions_hint = (
                        "PAGE PUBLIQUE — PAS de bouton Supprimer, "
                        "PAS d'import depuis './actions' (fichier inexistant ici). "
                    )
                _client_hint = (
                    f"'use client' LIGNE 1 OBLIGATOIRE. Client Component liste pour {_model_name}. "
                    f"export default function {_model_name}Client({{ items }}: {{ items: {_serialized}[] }}). "
                    f"Afficher la liste avec items.map(item => ...). "
                    f"{_list_actions_hint}"
                    f"Lien 'Nouveau' vers la page create si elle existe. "
                    "Champs nullable → string | null dans les types props. "
                    f"Importé depuis {file_path} : import {_model_name}Client from './page-client'."
                )
            elif _page_type == "create":
                # FK et enum via ModelGenerationContext (Canal A→B) si disponible, sinon fallback
                _fk_info: list[tuple[str, str]] = []
                _enum_cast_hint = ""
                if contexts and _model_name in contexts:
                    _ctx_m = contexts[_model_name]
                    _fk_info = [(fk.related_camel, fk.related_model) for fk in _ctx_m.fk_fields]
                    _enum_fields_c = [f for f in _ctx_m.editable_fields if f.input_type == "enum-select"]
                    if _enum_fields_c:
                        _spec_enums_c = getattr(spec, "enums", {}) or {}
                        _cast_parts_c = []
                        for _ef in _enum_fields_c:
                            _vals = _spec_enums_c.get(_ef.base_type, [])
                            if _vals:
                                _vals_str = " | ".join(f"'{v}'" for v in _vals)
                                _cast_parts_c.append(f"{_ef.name}: e.target.value as {_vals_str}")
                        if _cast_parts_c:
                            _opts_hints_c = []
                            for _ef in _enum_fields_c:
                                _vals = _spec_enums_c.get(_ef.base_type, [])
                                if _vals:
                                    _opts = "".join(f'<option value="{v}">{v}</option>' for v in _vals)
                                    _opts_hints_c.append(
                                        f'{_ef.name}: <select name="{_ef.name}">{_opts}</select>'
                                    )
                            _enum_cast_hint = (
                                "Champs enum — FORMULAIRE SERVER ACTION"
                                " (PAS de onChange, PAS de formData.set, PAS de useState) : "
                                + " | ".join(_opts_hints_c) + ". "
                            )
                else:
                    _spec_names_lower = {m.name.lower(): m.name for m in spec.models}
                    for _m in spec.models:
                        if _m.name == _model_name:
                            for _f in _m.fields:
                                if (
                                    _f.name.endswith("Id")
                                    and _f.type.rstrip("?") == "String"
                                    and _f.name[:-2].lower() in _spec_names_lower
                                ):
                                    _fk_target = _spec_names_lower[_f.name[:-2].lower()]
                                    _fk_info.append((_f.name[:-2], _fk_target))
                            break

                if _fk_info:
                    _fk_params = ", ".join(f"{n}Options" for n, _ in _fk_info)
                    _fk_types = ", ".join(f"{n}Options: Serialized{m}[]" for n, m in _fk_info)
                    _create_signature = (
                        f"export default function {_model_name}CreateClient"
                        f"({{ {_fk_params} }}: {{ {_fk_types} }}). "
                    )
                    _fk_props_hint = (
                        f"Props FK reçues depuis page.tsx : {_fk_types} — "
                        f"OBLIGATOIRES (TS2322 fatal si absentes). "
                    )
                else:
                    _create_signature = f"export default function {_model_name}CreateClient(). "
                    _fk_props_hint = ""

                _client_hint = (
                    f"'use client' LIGNE 1 OBLIGATOIRE. Client Component formulaire création pour {_model_name}. "
                    f"{_create_signature}"
                    f"{_fk_props_hint}"
                    f"{_enum_cast_hint}"
                    f"Formulaire <form action={{create{_model_name}}}> avec Server Action importée depuis ./actions. "
                    "NE PAS inclure userId dans formData — auth côté serveur. "
                    "Champs nullable → string | null dans les types props. "
                    f"Importé depuis {file_path} : import {_model_name}CreateClient from './page-client'."
                )
            else:  # detail, detail-slug
                _client_hint = (
                    f"'use client' LIGNE 1 OBLIGATOIRE. Client Component detail pour {_model_name}. "
                    f"export default function {_model_name}DetailClient({{ item }}: {{ item: {_serialized} }}). "
                    f"Afficher les champs scalaires de l'item. "
                    "Champs nullable → string | null dans les types props. "
                    f"Importé depuis {file_path} : import {_model_name}DetailClient from './page-client'."
                )
        elif "[INTERACTIVE]" in _page_detail_str:
            _comp_name = (ppath.replace("/", "-") or "home").title().replace("-", "")
            _client_hint = (
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
            )

        if _client_hint and _client_file not in template_set:
            entries.append(FilePlanEntry(
                path=_client_file,
                role="page_client",
                context_hint=_client_hint,
            ))

        entries.append(FilePlanEntry(
            path=file_path,
            role="page",
            context_hint=" ".join(hint_parts),
        ))

    # ── 4. Edit page-client.tsx (Level B) ─────────────────────────────────────
    # page.tsx est pré-généré (generate_edit_page_stubs) → dans template_set → exclu.
    # page-client.tsx n'est plus pré-généré → doit être dans le plan.
    _crud_list: set[str] = {
        getattr(p, "model", None)
        for p in spec.pages
        if getattr(p, "page_type", None) == "list"
        and getattr(p, "model", None)
        and p.auth_required
    }
    _crud_create: set[str] = {
        getattr(p, "model", None)
        for p in spec.pages
        if getattr(p, "page_type", None) == "create"
        and getattr(p, "model", None)
    }
    for model in spec.models:
        if model.name not in (_crud_list & _crud_create):
            continue
        list_page = spec.get_list_page_for_model(model.name)
        if not list_page:
            continue
        route_dir = list_page.lstrip("/")
        edit_client = f"app/{route_dir}/[id]/edit/page-client.tsx"
        if edit_client not in template_set:
            _serialized = f"Serialized{model.name}"
            _edit_enum_hint = ""
            _nullable_hint = ""
            if contexts and model.name in contexts:
                _edit_ctx = contexts[model.name]
                _edit_enum_fields = [f for f in _edit_ctx.editable_fields if f.input_type == "enum-select"]
                if _edit_enum_fields:
                    _spec_enums_e = getattr(spec, "enums", {}) or {}
                    _cast_parts_e = []
                    for _ef in _edit_enum_fields:
                        _vals = _spec_enums_e.get(_ef.base_type, [])
                        if _vals:
                            _vals_str = " | ".join(f"'{v}'" for v in _vals)
                            _cast_parts_e.append(f"{_ef.name}: e.target.value as {_vals_str}")
                    if _cast_parts_e:
                        _opts_hints_e = []
                        for _ef in _edit_enum_fields:
                            _vals = _spec_enums_e.get(_ef.base_type, [])
                            if _vals:
                                _opts = "".join(f'<option value="{v}">{v}</option>' for v in _vals)
                                _opts_hints_e.append(
                                    f'{_ef.name}: <select name="{_ef.name}"'
                                    f' defaultValue={{item.{_ef.name}}}>{_opts}</select>'
                                )
                        _edit_enum_hint = (
                            "Champs enum — FORMULAIRE SERVER ACTION"
                            " (PAS de onChange, PAS de formData.set, PAS de useState) : "
                            + " | ".join(_opts_hints_e) + ". "
                        )
                _nullable_fields = [f.name for f in _edit_ctx.editable_fields if f.is_optional]
                if _nullable_fields:
                    _null_examples = " | ".join(
                        f"defaultValue={{item.{fn} ?? ''}}" for fn in _nullable_fields
                    )
                    _nullable_hint = (
                        f"Champs nullable (string | null) — RÈGLE ABSOLUE : {_null_examples}. "
                    )
            entries.append(FilePlanEntry(
                path=edit_client,
                role="page_client",
                context_hint=(
                    f"'use client' LIGNE 1 OBLIGATOIRE. Client Component formulaire edit pour {model.name}. "
                    f"export default function {model.name}EditClient({{ item }}: {{ item: {_serialized} }}). "
                    f"Server Action update{model.name}(id: string, formData: FormData) depuis ./actions. "
                    f"PATTERN BIND : <form action={{update{model.name}.bind(null, item.id)}}> "
                    f"— OU appel direct : await update{model.name}(item.id, formData) (2 args, id en 1er). "
                    f"Chaque champ avec defaultValue={{item.fieldName}}. "
                    f"{_edit_enum_hint}"
                    f"{_nullable_hint}"
                    f"Importé depuis app/{route_dir}/[id]/edit/page.tsx : import {model.name}EditClient from './page-client'."
                ),
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

    # Webhooks — seuls vrais fichiers route.ts attendus dans le plan
    for route in spec.routes:
        if _is_webhook_route(route.path):
            rpath = route.path
            if rpath.startswith("/api"):
                rpath = rpath[4:]
            rf = f"app/api{rpath.rstrip('/')}/route.ts"
            if rf not in plan_paths:
                missing.append(rf)

    # Actions — dérivées des pages list (correspondance réelle avec dev_actions_generator)
    _seen_action_dirs: set[str] = set()
    for page in spec.pages:
        if getattr(page, "page_type", "custom") == "list":
            seg = page.path.lstrip("/")
            if seg and seg not in _seen_action_dirs:
                _seen_action_dirs.add(seg)
                af = f"app/{seg}/actions.ts"
                if af not in plan_paths:
                    missing.append(af)

    for page in spec.pages:
        ppath = page.path.strip("/")
        pf = "app/page.tsx" if not ppath else f"app/{ppath}/page.tsx"
        if pf not in plan_paths:
            missing.append(pf)

    return list(dict.fromkeys(missing))  # dédupliqué, ordre préservé
