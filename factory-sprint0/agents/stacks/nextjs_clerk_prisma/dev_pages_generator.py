"""
agents/dev_pages_generator.py
──────────────────────────────
Génération déterministe des fichiers de scaffold.

Architecture (Mai 2026) :
- loading.tsx      : squelette UI trivial, jamais incorrect.
- error/not-found  : invariants de stack, jamais générés par le LLM.
- page.tsx         : ENTIÈREMENT DÉTERMINISTE pour les pages avec champ `model`.
                     Écrit dans template_written → LLM ne peut pas écraser.
                     Pattern : auth guard (si requis) + appel service + <XxxClient items={items} />
                     Pour les pages sans `model` : entièrement générées par le LLM.
                     Aucun stub n'est écrit sur disque — le data_contract est injecté
                     via context_hint dans le plan ; executor_node décide de générer.
"""
from __future__ import annotations

import logging
import os

from .dev_naming import (
    pascal_to_camel,
    pascal_to_kebab,
    path_to_client_component,
    path_to_page_component,
)

logger = logging.getLogger(__name__)


def _pluralize(name: str) -> str:
    """Pluriel anglais simple pour les noms de modèles PascalCase."""
    if name.endswith("y") and len(name) > 1 and name[-2].lower() not in "aeiou":
        return name[:-1] + "ies"   # Category → Categories
    if name.endswith(("s", "sh", "ch", "x", "z")):
        return name + "es"
    return name + "s"


def _model_has_status(model_obj) -> bool:
    return any(f.name.lower() == "status" for f in model_obj.fields)


def _model_has_relations(model_obj) -> bool:
    return any("@relation" in (f.attributes or "") for f in model_obj.fields)


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

    # Si la cible est une page auth-required : guard auth() obligatoire.
    # Utilisateurs authentifiés → redirect_target, non-authentifiés → /sign-in.
    # Sans ce guard, redirect('/dashboard') s'exécute AVANT l'auth check → TS review warning.
    target_page = next(
        (p for p in spec.pages if p.path == redirect_target and p.auth_required),
        None,
    )

    if target_page is not None:
        content = "\n".join([
            "import { auth } from '@clerk/nextjs/server'",
            "import { redirect } from 'next/navigation'",
            "",
            "export default async function Home() {",
            "  const { userId } = await auth()",
            f"  if (userId) redirect('{redirect_target}')",
            "  redirect('/sign-in')",
            "}",
            "",
        ])
    else:
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



def _fk_fields(model_obj, spec) -> list[tuple[str, str, str]]:
    """
    Retourne les champs FK du modèle : (field_name, related_model_name, related_camel).
    Utilisé par _gen_page_full pour fetcher les options FK côté serveur (create pages).
    """
    model_names = {m.name for m in spec.models}
    owner = model_obj.resolved_owner()
    result: list[tuple[str, str, str]] = []
    for field in model_obj.fields:
        name = field.name
        if name in {owner, "id"} or "@relation" in (field.attributes or ""):
            continue
        if not name.endswith("Id"):
            continue
        base = name[:-2]
        related_model = base[0].upper() + base[1:]
        if related_model not in model_names:
            suffix_matches = [mn for mn in model_names if mn.endswith(related_model)]
            if suffix_matches:
                related_model = suffix_matches[0]
        if related_model in model_names:
            result.append((name, related_model, pascal_to_camel(related_model)))
    return result

def _gen_page_full(page, model_obj, spec=None) -> str:
    """
    Génère un page.tsx ENTIÈREMENT DÉTERMINISTE pour une page avec champ `model`.
    Le fichier résultant est ajouté à template_written → le LLM ne peut pas l'écraser.

    Patterns générés :
    - Liste privée  : auth() + getAll(userId) → <XxxClient items={items} />
    - Liste publique: getPublished() / getPublicAll() sans auth → <XxxClient items={items} />
    - Création      : auth() + fetch FK options → <XxxClient fkOptions={...} />
    - Détail privé  : auth() + getById(userId, params.id) + notFound() → <XxxClient item={item} />
    - Détail public : prisma.model.findUnique(params.id) + notFound() → <XxxClient item={item} />
    """
    name = model_obj.name
    camel = pascal_to_camel(name)
    kebab = pascal_to_kebab(name)
    client = path_to_client_component(page.path)
    component = path_to_page_component(page.path)
    is_create = page.page_type == "create"
    is_detail = page.page_type in ("detail", "detail-slug")
    is_slug_detail = page.page_type == "detail-slug"
    has_relations = _model_has_relations(model_obj)
    has_status = _model_has_status(model_obj)

    # Champs FK pour pages create (Pilier 1 — form generator)
    fk_list: list[tuple[str, str, str]] = []
    if is_create and spec is not None:
        fk_list = _fk_fields(model_obj, spec)

    lines: list[str] = []

    # Auth import
    if page.auth_required:
        lines.append("import { auth } from '@clerk/nextjs/server'")

    # next/navigation : redirect + notFound combinés dans un seul import
    nav_imports: list[str] = []
    if page.auth_required:
        nav_imports.append("redirect")
    if is_detail:
        nav_imports.append("notFound")
    if nav_imports:
        lines.append(f"import {{ {', '.join(nav_imports)} }} from 'next/navigation'")

    lines.append(f"import {client} from './page-client'")

    # Service selon type de page — detail public : getPublicById (sans owner filter)
    if is_detail:
        lines.append(f"import {{ {camel}Service }} from '@/lib/services/{kebab}.service'")
    elif not is_create:
        lines.append(f"import {{ {camel}Service }} from '@/lib/services/{kebab}.service'")

    # Imports des services FK pour les selects du formulaire create
    for _fk_field, related_model, related_camel in fk_list:
        related_kebab = pascal_to_kebab(related_model)
        lines.append(
            f"import {{ {related_camel}Service }} from '@/lib/services/{related_kebab}.service'"
        )

    if is_slug_detail:
        fn_params = "{ params }: { params: Promise<{ slug: string }> }"
    elif is_detail:
        fn_params = "{ params }: { params: Promise<{ id: string }> }"
    else:
        fn_params = ""
    lines += [
        "",
        "export const dynamic = 'force-dynamic'",
        "",
        f"export default async function {component}({fn_params}) {{",
    ]

    # Next.js 15 : params is a Promise — must be awaited before use
    if is_slug_detail:
        lines.append("  const { slug } = await params")
    elif is_detail:
        lines.append("  const { id } = await params")

    if page.auth_required:
        lines += [
            "  const { userId } = await auth()",
            "  if (!userId) redirect('/sign-in')",
        ]

    if is_detail:
        if is_slug_detail:
            _has_slug_field = any(f.name.lower() == "slug" for f in model_obj.fields)
            if _has_slug_field:
                svc_method = f"getBySlugWithRelations(slug)" if has_relations else f"getBySlug(slug)"
            elif page.auth_required:
                logger.warning(
                    "[pages_gen] %s : detail-slug déclaré mais pas de champ 'slug' — fallback getByIdWithRelations(userId, slug). "
                    "L'architect doit ajouter `slug String @unique` au modèle.",
                    name,
                )
                svc_method = f"getByIdWithRelations(userId, slug)" if has_relations else f"getById(userId, slug)"
            else:
                logger.warning(
                    "[pages_gen] %s : detail-slug déclaré mais pas de champ 'slug' — fallback getPublicByIdWithRelations(slug). "
                    "L'architect doit ajouter `slug String @unique` au modèle.",
                    name,
                )
                svc_method = f"getPublicByIdWithRelations(slug)" if has_relations else f"getPublicById(slug)"
            lines.append(f"  const item = await {camel}Service.{svc_method}")
        elif page.auth_required:
            svc_method = f"getByIdWithRelations(userId, id)" if has_relations else f"getById(userId, id)"
            lines.append(f"  const item = await {camel}Service.{svc_method}")
        else:
            svc_method = f"getPublicByIdWithRelations(id)" if has_relations else f"getPublicById(id)"
            lines.append(f"  const item = await {camel}Service.{svc_method}")
        lines += [
            "  if (!item) notFound()",
            f"  return <{client} item={{item}} />",
        ]
    elif not is_create:
        if page.auth_required:
            service_call = (
                f"{camel}Service.getAllWithRelations(userId)"
                if has_relations else
                f"{camel}Service.getAll(userId)"
            )
        else:
            service_call = (
                f"{camel}Service.getPublished()"
                if has_status else
                f"{camel}Service.getPublicAll()"
            )
        lines += [
            f"  const items = await {service_call}",
            f"  return <{client} items={{items}} />",
        ]
    else:
        if fk_list:
            # Fetch des options pour chaque select FK
            for _fk_field, _related_model, related_camel in fk_list:
                if page.auth_required:
                    lines.append(f"  const {related_camel}Options = await {related_camel}Service.getAll(userId)")
                else:
                    lines.append(f"  const {related_camel}Options = await {related_camel}Service.getPublicAll()")
            fk_props = " ".join(
                f"{related_camel}Options={{{related_camel}Options}}"
                for _fk_field, _related_model, related_camel in fk_list
            )
            lines.append(f"  return <{client} {fk_props} />")
        else:
            lines.append(f"  return <{client} />")

    lines += ["}", ""]
    return "\n".join(lines)


def generate_page_stubs(spec: "ProjectSpec", project_workdir: str, contexts: "dict | None" = None) -> dict[str, str]:  # type: ignore[name-defined]
    """
    Génère app/<path>/page.tsx pour chaque page du spec.

    Deux régimes :
    - Page avec `model` → page.tsx ENTIÈREMENT DÉTERMINISTE (retourné dans le dict
      pour ajout dans template_written par dev_graph → LLM ne peut pas écraser).
    - Page sans `model` → stub auth-guard minimal (LLM peut compléter librement,
      non retourné dans le dict template_written).
    - Page [CROSS_ENTITY] → SKIP total : ni écriture disque ni template_written.
      Le LLM la génère depuis le context_hint du planner (fetch primaire + secondaires).

    Retourne {rel_path: content} pour les pages fully-deterministic uniquement.
    """
    written: dict[str, str] = {}

    # Chemins des pages [CROSS_ENTITY] — délégués entièrement au LLM
    _pages_detail = getattr(spec, "pages_detail", {}) or {}
    _cross_entity_paths: set[str] = {
        path for path, desc in _pages_detail.items()
        if "[CROSS_ENTITY:" in str(desc or "")
    }
    if _cross_entity_paths:
        logger.info("[pages_gen] %d page(s) [CROSS_ENTITY] → LLM : %s", len(_cross_entity_paths), sorted(_cross_entity_paths))

    for page in spec.pages:
        if page.path in _cross_entity_paths:
            # page.tsx est généré déterministiquement (auth + fetch entité primaire)
            # Seul page-client.tsx reste LLM (géré par dev_form_generator via CROSS_ENTITY)
            page_rel = f"app/{page.path.strip('/')}/page.tsx"
            page_abs = os.path.join(project_workdir, page_rel.replace("/", os.sep))
            os.makedirs(os.path.dirname(page_abs), exist_ok=True)
            model_obj = spec.get_model_by_name(getattr(page, "model", None)) if getattr(page, "model", None) else None
            if model_obj is None:
                model_obj = _find_detail_model(page, spec)
            if model_obj is not None:
                content = _gen_page_full(page, model_obj, spec=spec)
                with open(page_abs, "w", encoding="utf-8") as f:
                    f.write(content)
                written[page_rel] = content
                logger.info("[pages_gen] ✓ [CROSS_ENTITY] page.tsx déterministe : %s (model=%s)", page_rel, model_obj.name)
            else:
                logger.info("[pages_gen] [CROSS_ENTITY] page.tsx → LLM (model introuvable) : %s", page_rel)
            continue
        page_rel = f"app/{page.path.strip('/')}/page.tsx" if page.path.strip("/") else "app/page.tsx"
        page_abs = os.path.join(project_workdir, page_rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(page_abs), exist_ok=True)

        model_name = getattr(page, "model", None)
        model_obj = spec.get_model_by_name(model_name) if model_name else None

        # Pour les pages create sans model explicite, résoudre via le chemin parent
        if model_obj is None and getattr(page, "page_type", None) == "create":
            model_obj = _find_create_model(page, spec)

        # Pour les pages detail/detail-slug sans model explicite, résoudre via le chemin parent
        if model_obj is None and getattr(page, "page_type", None) in ("detail", "detail-slug"):
            model_obj = _find_detail_model(page, spec)

        if model_obj is not None:
            content = _gen_page_full(page, model_obj, spec=spec)
            with open(page_abs, "w", encoding="utf-8") as f:
                f.write(content)
            written[page_rel] = content
            logger.info("[pages_gen] ✓ page déterministe : %s (model=%s)", page_rel, model_name)
        else:
            # Page custom sans modèle → laissée au LLM.
            # NE PAS écrire de stub sur le disque : l'executor_node vérifie os.path.exists()
            # pour décider si un fichier doit être généré. Un stub pré-écrit bloquerait le LLM
            # et le contrat data_contract injecté dans context_hint ne serait jamais reçu.
            logger.info("[pages_gen] page custom (LLM) : %s", page_rel)

    logger.info("[pages_gen] %d pages déterministes écrites", len(written))
    return written


def _find_create_model(page, spec):
    """
    Trouve le PrismaModel pour une page create en remontant via le chemin parent.
    Ex: /blog/new → parent /blog → model Post.
    """
    if getattr(page, "model", None):
        return spec.get_model_by_name(page.model)
    parts = page.path.strip("/").split("/")
    if len(parts) >= 2:
        parent_path = "/" + "/".join(parts[:-1])
        parent = next((p for p in spec.pages if p.path == parent_path), None)
        if parent and getattr(parent, "model", None):
            return spec.get_model_by_name(parent.model)
    return None


def _find_detail_model(page, spec):
    """
    Trouve le PrismaModel pour une page detail en remontant via le chemin parent.
    Ex: /blog/[id] → parent /blog → model Post.
    """
    if getattr(page, "model", None):
        return spec.get_model_by_name(page.model)
    parts = page.path.strip("/").split("/")
    # Remonte vers les segments statiques (exclut les [id])
    static_parts = [p for p in parts if not p.startswith("[")]
    if static_parts:
        parent_path = "/" + "/".join(static_parts)
        parent = next((p for p in spec.pages if p.path == parent_path), None)
        if parent and getattr(parent, "model", None):
            return spec.get_model_by_name(parent.model)
    return None


# ── Edit pages (CRUD update form) ────────────────────────────────────────────

def _gen_page_full_edit(model_obj, fk_list: "list[tuple[str,str,str]]", has_slug: bool = False) -> str:
    """
    page.tsx déterministe pour la page edit d'un modèle :
    auth() + getById(userId, params.id/slug) + fetch FK options + <EditClient item={item} ...options />
    fk_list : liste de (field_name, related_model, related_camel) depuis ModelGenerationContext.fk_fields
    """
    name = model_obj.name
    camel = pascal_to_camel(name)
    kebab = pascal_to_kebab(name)
    client = f"{name}EditClient"
    component = f"{name}EditPage"
    param_key = "slug" if has_slug else "id"

    lines: list[str] = [
        "import { auth } from '@clerk/nextjs/server'",
        "import { redirect, notFound } from 'next/navigation'",
        f"import {{ {camel}Service }} from '@/lib/services/{kebab}.service'",
    ]

    # Imports services FK
    for _fk_field, related_model, related_camel in fk_list:
        related_kebab = pascal_to_kebab(related_model)
        lines.append(
            f"import {{ {related_camel}Service }} from '@/lib/services/{related_kebab}.service'"
        )

    lookup_method = "getBySlugOwned" if has_slug else "getById"
    lines += [
        f"import {client} from './page-client'",
        "",
        "export const dynamic = 'force-dynamic'",
        "",
        f"export default async function {component}({{ params }}: {{ params: Promise<{{ {param_key}: string }}> }}) {{",
        "  const { userId } = await auth()",
        "  if (!userId) redirect('/sign-in')",
        f"  const {{ {param_key} }} = await params",
        f"  const item = await {camel}Service.{lookup_method}(userId, {param_key})",
        "  if (!item) notFound()",
    ]

    # Fetch des options FK
    for _fk_field, _related_model, related_camel in fk_list:
        lines.append(f"  const {related_camel}Options = await {related_camel}Service.getAll(userId)")

    # JSX return avec item + fk options
    if fk_list:
        fk_props = " ".join(
            f"{related_camel}Options={{{related_camel}Options}}"
            for _fk_field, _related_model, related_camel in fk_list
        )
        lines.append(f"  return <{client} item={{item}} {fk_props} />")
    else:
        lines.append(f"  return <{client} item={{item}} />")

    lines += ["}", ""]
    return "\n".join(lines)


def generate_edit_page_stubs(
    spec: "ProjectSpec",  # type: ignore[name-defined]
    project_workdir: str,
    contexts: "dict | None" = None,
) -> dict[str, str]:
    """
    Génère app/{list_path}/[id]/edit/page.tsx pour chaque modèle
    qui a à la fois une page list privée ET une page create dans le spec (intent CRUD).

    Ces pages permettent la mise à jour d'un item existant via le Server Action update{Model}.
    Retourne {rel_path: content} pour intégration dans template_written.
    """
    written: dict[str, str] = {}

    # Modèles avec intent CRUD explicite : list auth + create
    crud_models: set[str] = set()
    for page in spec.pages:
        if getattr(page, "page_type", None) == "list" and getattr(page, "model", None) and page.auth_required:
            crud_models.add(page.model)

    # Modèles ayant une page create — model explicite OU inféré via chemin parent
    create_model_names: set[str] = set()
    for p in spec.pages:
        if getattr(p, "page_type", None) != "create":
            continue
        m = getattr(p, "model", None) or (
            getattr(_find_create_model(p, spec), "name", None) if _find_create_model(p, spec) else None
        )
        if m:
            create_model_names.add(m)

    # Intersection : doit avoir list auth + create (intent CRUD complet)
    crud_models &= create_model_names

    for model in spec.models:
        if model.name not in crud_models:
            continue

        list_path = spec.get_list_page_for_model(model.name)
        if not list_path:
            logger.warning(
                "[pages_generator] edit page skipped for '%s' — aucune page list déclarée.",
                model.name,
            )
            continue
        route_dir = list_path.lstrip("/")
        ctx = (contexts or {}).get(model.name)
        has_slug = bool(ctx and ctx.has_slug)
        slug_or_id = "[slug]" if has_slug else "[id]"
        edit_dir = f"app/{route_dir}/{slug_or_id}/edit"

        page_rel = f"{edit_dir}/page.tsx"
        page_abs = os.path.join(project_workdir, page_rel.replace("/", os.sep))

        os.makedirs(os.path.dirname(page_abs), exist_ok=True)

        # Convertit FKFieldInfo → (field_name, related_model, related_camel) pour _gen_page_full_edit
        fk_list_for_edit: list[tuple[str, str, str]] = [
            (fk.field_name, fk.related_model, fk.related_camel)
            for fk in (ctx.fk_fields if ctx else [])
        ]

        if not os.path.exists(page_abs):
            page_content = _gen_page_full_edit(model, fk_list_for_edit, has_slug=has_slug)
            with open(page_abs, "w", encoding="utf-8") as f:
                f.write(page_content)
            written[page_rel] = page_content
            logger.info("[pages_gen] ✓ edit page.tsx : %s", page_rel)

    logger.info("[pages_gen] %d fichiers edit générés de manière déterministe", len(written))
    return written
