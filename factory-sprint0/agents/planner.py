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


def _match_flows_to_page(page_path: str, user_flows: list) -> list[str]:
    """
    Retourne les user_flows qui concernent une page donnée.
    Match sur le chemin exact (/dashboard) ou le segment final (dashboard).
    """
    if not user_flows:
        return []
    path_lower = page_path.lower()
    segs = [s for s in path_lower.strip("/").split("/") if s and not s.startswith("[")]
    matched = []
    for flow in user_flows:
        flow_lower = str(flow).lower()
        if path_lower in flow_lower:
            matched.append(flow)
        elif segs and any(seg in flow_lower for seg in segs):
            matched.append(flow)
    return matched


def build_custom_page_contracts(
    spec: "ProjectSpec",
    contexts: "dict | None" = None,
) -> "dict[str, str]":
    """
    Génère des contrats pour les pages custom (page_type='custom', sans modèle lié).
    Source : user_flows de l'architect + signatures de services disponibles.

    Retourne {page_path: hint_str} à injecter dans context_hint de page.tsx.
    """
    user_flows = getattr(spec, "user_flows", []) or []
    contracts: dict[str, str] = {}

    for page in spec.pages:
        page_type = getattr(page, "page_type", "custom")
        if page_type != "custom":
            continue

        hint_parts: list[str] = []

        # 1. User flows matchés à cette page
        matched_flows = _match_flows_to_page(page.path, user_flows)
        if matched_flows:
            hint_parts.append(
                f"USER FLOWS à implémenter sur cette page : {' | '.join(matched_flows)}."
            )

        # 2. Services disponibles avec leurs appels pertinents
        svc_lines: list[str] = []
        for model in spec.models:
            camel = _pascal_to_camel(model.name)
            kebab = _pascal_to_kebab(model.name)
            owner = model.resolved_owner()
            ctx = contexts.get(model.name) if contexts else None
            has_public = bool(getattr(ctx, "has_public_pages", False)) if ctx else False
            has_status = bool(getattr(ctx, "has_status", False)) if ctx else False

            calls = [f"{camel}Service.getAll({owner})"]
            if has_status and has_public:
                calls.append(f"{camel}Service.getPublished() → uniquement publiés")
            elif has_status:
                # Pour dashboard : count par statut via getAll puis .filter()
                calls.append(f"(filtrer getAll par status pour comptage)")

            svc_lines.append(
                f"import {{ {camel}Service }} from '@/lib/services/{kebab}.service' "
                f"[appels : {', '.join(calls)}]"
            )

        if svc_lines:
            hint_parts.append(f"SERVICES DISPONIBLES : {' | '.join(svc_lines)}.")

        # 3. Hint spécifique dashboard / hub
        path_lower = page.path.lower()
        if any(kw in path_lower for kw in ("dashboard", "hub", "overview", "home", "accueil")):
            # Construire les appels de stats concrets depuis les modèles
            stat_calls: list[str] = []
            link_suggestions: list[str] = []
            for model in spec.models:
                camel = _pascal_to_camel(model.name)
                kebab = _pascal_to_kebab(model.name)
                owner = model.resolved_owner()
                ctx = contexts.get(model.name) if contexts else None
                has_public = bool(getattr(ctx, "has_public_pages", False)) if ctx else False
                has_status = bool(getattr(ctx, "has_status", False)) if ctx else False
                list_path = getattr(ctx, "list_page_path", f"/{kebab}s") if ctx else f"/{kebab}s"

                stat_calls.append(
                    f"const {camel}s = await {camel}Service.getAll({owner})"
                    f" → total={camel}s.length"
                )
                if has_status and has_public:
                    stat_calls.append(
                        f"const published{model.name}s = await {camel}Service.getPublished()"
                        f" → publishedCount=published{model.name}s.length"
                    )
                link_suggestions.append(f"'{list_path}/new' (créer {model.name})")
                link_suggestions.append(f"'{list_path}' (gérer {model.name}s)")

            if stat_calls:
                hint_parts.append(
                    f"STRUCTURE DASHBOARD : "
                    f"(1) Charger les données en haut du Server Component : {'; '.join(stat_calls[:4])}. "
                    f"(2) Retourner un <main> avec des cartes de statistiques affichant ces chiffres. "
                    f"(3) Inclure des <Link> vers : {', '.join(link_suggestions[:4])}. "
                    f"Tout le rendu est inline dans ce Server Component — aucun Client Component séparé."
                )

        if hint_parts:
            contracts[page.path] = " ".join(hint_parts)

    return contracts


def build_page_contracts(
    spec: "ProjectSpec",
    contexts: "dict | None" = None,
) -> "dict[str, tuple[str, str]]":
    """
    Dérive les contrats techniques des pages custom [INTERACTIVE] depuis Level A.

    Utilise ModelGenerationContext (déjà calculé) pour déduire QUEL appel de service
    injecter par page : getAll vs getPublicAll, getById vs getPublicById, with/without relations.

    Retourne {page_path: (page_hint, client_hint)} où :
      - page_hint : injecté dans page.tsx context_hint — appel de service exact
      - client_hint : injecté dans page-client.tsx context_hint — type de props
    """
    if not contexts:
        return {}

    pages_detail = getattr(spec, "pages_detail", {}) or {}

    # Index modèle par segment de chemin (même logique que make_deterministic_plan)
    _mbseg: dict[str, object] = {}
    for m in spec.models:
        k = _pascal_to_kebab(m.name)
        _mbseg[k] = m
        _mbseg[k + "s"] = m

    contracts: dict[str, tuple[str, str]] = {}

    for page in spec.pages:
        _pd_val = pages_detail.get(page.path, "")
        _is_interactive = (
            isinstance(_pd_val, dict) and bool(_pd_val.get("interactive", False))
        ) or (isinstance(_pd_val, str) and "[INTERACTIVE]" in _pd_val)
        if not _is_interactive:
            continue
        page_detail_str = str(_pd_val)

        ppath = page.path.strip("/")
        segs = ppath.split("/") if ppath else []
        static_segs = [s for s in segs if s and not (s.startswith("[") and s.endswith("]"))]
        dyn_segs = [s[1:-1] for s in segs if s.startswith("[") and s.endswith("]")]
        has_dyn = bool(dyn_segs)

        # Match modèle primaire : chemin d'abord, description ensuite, puis list_page_path
        primary_model = _mbseg.get(static_segs[0]) if static_segs else None
        if primary_model is None:
            desc_lower = page_detail_str.lower()
            for m in spec.models:
                mk = _pascal_to_kebab(m.name)
                if mk in desc_lower or getattr(m, "name", "").lower() in desc_lower:
                    primary_model = m
                    break
        # Fallback list_page_path : si l'architect a déclaré "list_page_path=/blog" pour Post,
        # alors /blog/[id] et tout chemin dont le premier segment = "blog" → Post.
        if primary_model is None and contexts and static_segs:
            _seg0 = static_segs[0]
            for _m in spec.models:
                _ctx_cand = contexts.get(getattr(_m, "name", ""))
                _lpp = getattr(_ctx_cand, "list_page_path", "") if _ctx_cand else ""
                if _lpp and _lpp.strip("/").split("/")[0] == _seg0:
                    primary_model = _m
                    break

        if primary_model is None:
            continue

        model_name = getattr(primary_model, "name", "")
        ctx = contexts.get(model_name)
        if ctx is None:
            continue

        camel: str = getattr(ctx, "camel", _pascal_to_camel(model_name))
        kebab: str = getattr(ctx, "kebab", _pascal_to_kebab(model_name))
        serialized: str = getattr(ctx, "serialized_type", f"Serialized{model_name}")
        owner: str = primary_model.resolved_owner()
        has_relations: bool = bool(getattr(ctx, "has_relations", False))
        has_slug: bool = bool(getattr(ctx, "has_slug", False))

        svc_import = f"import {{ {camel}Service }} from '@/lib/services/{kebab}.service'"
        page_parts: list[str] = []
        client_parts: list[str] = []

        if has_dyn:
            dyn_param = dyn_segs[0]
            if page.auth_required:
                fetch_call = (
                    f"{camel}Service.getByIdWithRelations({owner}, {dyn_param})"
                    if has_relations else
                    f"{camel}Service.getById({owner}, {dyn_param})"
                )
                page_parts += [
                    f"CONTRAT TECHNIQUE — page détail privée.",
                    f"Charger via : `const item = await {fetch_call}`.",
                    f"Type retour : {serialized}.",
                    f"Passer `<ClientComponent item={{item}} />` au Client Component.",
                ]
                client_parts += [
                    f"Props : `{{ item: {serialized} }}`.",
                    f"Import type : `import type {{ {serialized} }} from '@/lib/types'`.",
                ]
            else:
                if has_slug and "slug" in ppath:
                    fetch_call = f"{camel}Service.getBySlug({dyn_param})"
                elif has_relations:
                    fetch_call = f"{camel}Service.getPublicByIdWithRelations({dyn_param})"
                else:
                    fetch_call = f"{camel}Service.getPublicById({dyn_param})"
                page_parts += [
                    f"CONTRAT TECHNIQUE — page détail PUBLIQUE (sans auth).",
                    f"Charger via : `const item = await {fetch_call}`.",
                    f"Type retour : {serialized}. NE PAS appeler auth() ni redirect.",
                    f"Passer `<ClientComponent item={{item}} />` au Client Component.",
                ]
                client_parts += [
                    f"Props : `{{ item: {serialized} }}`.",
                    f"Import type : `import type {{ {serialized} }} from '@/lib/types'`.",
                    "Page publique — NE PAS importer ni appeler Clerk.",
                ]
        else:
            if page.auth_required:
                fetch_call = (
                    f"{camel}Service.getAllWithRelations({owner})"
                    if has_relations else
                    f"{camel}Service.getAll({owner})"
                )
                page_parts += [
                    f"CONTRAT TECHNIQUE — page liste/dashboard privée.",
                    f"Charger via : `const items = await {fetch_call}`.",
                    f"Type retour : {serialized}[].",
                    f"Passer `<ClientComponent items={{items}} />` au Client Component.",
                ]
                client_parts += [
                    f"Props : `{{ items: {serialized}[] }}`.",
                    f"Import type : `import type {{ {serialized} }} from '@/lib/types'`.",
                ]
            else:
                fetch_call = f"{camel}Service.getPublicAll()"
                page_parts += [
                    f"CONTRAT TECHNIQUE — page liste PUBLIQUE (sans auth).",
                    f"Charger via : `const items = await {fetch_call}`.",
                    f"Type retour : {serialized}[]. NE PAS appeler auth() ni redirect.",
                    f"Passer `<ClientComponent items={{items}} />` au Client Component.",
                ]
                client_parts += [
                    f"Props : `{{ items: {serialized}[] }}`.",
                    f"Import type : `import type {{ {serialized} }} from '@/lib/types'`.",
                    "Page publique — NE PAS importer ni appeler Clerk.",
                ]

        page_parts.append(f"Import service : `{svc_import}`.")

        # Secondary fetches from [CROSS_ENTITY: X] tags in pages_detail
        _ce_matches = _re.findall(r'\[CROSS_ENTITY:\s*(\w+)\]', page_detail_str)
        for _sec_name in _ce_matches:
            _sec_ctx = contexts.get(_sec_name)
            if _sec_ctx is None:
                continue
            _sec_camel = getattr(_sec_ctx, "camel", _pascal_to_camel(_sec_name))
            _sec_kebab = getattr(_sec_ctx, "kebab", _pascal_to_kebab(_sec_name))
            _sec_serialized = getattr(_sec_ctx, "serialized_type", f"Serialized{_sec_name}")
            _param_ref = dyn_segs[0] if has_dyn else "id"
            _parent_cap = model_name[0].upper() + model_name[1:]
            _dedicated_method = f"getBy{_parent_cap}Id"

            # Validation ServiceSpec — la méthode doit exister dans le service enfant
            try:
                from agents.stacks.nextjs_clerk_prisma.dev_service_spec import build_service_spec as _bss
                _sec_svc = _bss(_sec_ctx)
                if not _sec_svc.has(_dedicated_method):
                    import logging as _log
                    _log.getLogger(__name__).warning(
                        "[planner] CROSS_ENTITY : méthode '%s' absente de ServiceSpec(%s) — skip",
                        _dedicated_method, _sec_name,
                    )
                    continue
            except Exception:
                pass  # validation non bloquante

            page_parts.append(
                f"DONNÉES SECONDAIRES [{_sec_name}] : "
                f"`import {{ {_sec_camel}Service }} from '@/lib/services/{_sec_kebab}.service'` — "
                f"`const {_sec_camel}s = await {_sec_camel}Service.{_dedicated_method}(userId, params.{_param_ref})` "
                f"(méthode pré-générée dans le service — NE PAS recréer). "
                f"Type : {_sec_serialized}[]. Passer au Client Component via props additionnels."
            )
            client_parts.append(
                f"Props [{_sec_name}] : `{_sec_camel}s: {_sec_serialized}[]`. "
                f"Pour les mutations sur {_sec_name} (delete/update) : "
                f"importer depuis `@/app/{_sec_kebab}s/actions` — "
                f"JAMAIS depuis `../actions` (qui est le service du modèle parent, pas de l'enfant)."
            )

        contracts[page.path] = (" ".join(page_parts), " ".join(client_parts))

    return contracts


def make_deterministic_plan(
    spec: "ProjectSpec",
    template_files: list[str],
    manifest: "object | None" = None,
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
    # Contract Generator : contrats techniques par page custom [INTERACTIVE].
    # Si manifest disponible : lire page_contracts déjà calculés (évite double calcul).
    # Sinon : calculer depuis contexts (rétrocompatibilité).
    if manifest is not None and getattr(manifest, "page_contracts", None) is not None:
        _contracts = manifest.page_contracts
    else:
        _contracts = build_page_contracts(spec, contexts)

    # Contrats pour pages custom (page_type="custom") — user_flows → directives LLM
    _custom_contracts = build_custom_page_contracts(spec, contexts)

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

        # ── page-client.tsx custom [INTERACTIVE] ─────────────────────────────────
        # Pages CRUD standard (list/create/detail/edit) : page-client.tsx généré
        # déterministiquement par dev_form_generator → présents dans template_set →
        # le filtre final (e.path not in template_set) les exclut automatiquement.
        # Seules les pages custom [INTERACTIVE] restent à la charge du LLM.
        _pages_detail = getattr(spec, "pages_detail", {}) or {}
        _page_detail_str = str(_pages_detail.get(page.path, ""))

        # Contrat Level A : appel de service exact pour les pages custom [INTERACTIVE]
        if "[INTERACTIVE]" in _page_detail_str:
            _page_contract, _ = _contracts.get(page.path, ("", ""))
            if _page_contract:
                hint_parts.append(_page_contract)

        # Contrat pages custom (page_type="custom") — user_flows + services disponibles
        _page_type = getattr(page, "page_type", "custom")
        if _page_type == "custom":
            _custom_contract = _custom_contracts.get(page.path, "")
            if _custom_contract:
                hint_parts.append(_custom_contract)
        _client_file = "app/page-client.tsx" if not ppath else f"app/{ppath}/page-client.tsx"
        _client_hint = ""

        if "[INTERACTIVE]" in _page_detail_str:
            _comp_name = (ppath.replace("/", "-") or "home").title().replace("-", "")
            _client_hint = (
                f"'use client' LIGNE 1 OBLIGATOIRE. Client Component pour {file_path}. "
                f"export default function {_comp_name}Client(props: {_comp_name}ClientProps). "
                f"PROPS INTERFACE : déclarer UNIQUEMENT les props que le Server Component "
                f"parent peut concrètement passer (données chargées côté serveur). "
                f"Champs nullable → string | null (JAMAIS string | undefined). "
                f"Importé depuis {file_path} avec DEFAULT import : "
                f"import {_comp_name}Client from './page-client'."
            )
            _, _client_contract = _contracts.get(page.path, ("", ""))
            if _client_contract:
                _client_hint += f" {_client_contract}"

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
