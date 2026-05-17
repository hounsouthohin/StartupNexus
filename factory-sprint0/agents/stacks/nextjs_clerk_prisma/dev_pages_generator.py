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
                     Pour les pages sans `model` : stub auth-guard uniquement (LLM complète).
- page-client.tsx  : stub pré-scaffoldé avec interface props correcte.
                     PAS dans template_written → LLM complète le JSX body.
                     Garantit la cohérence entre page.tsx (locked) et page-client.tsx (stub).
"""
from __future__ import annotations

import logging
import os
import re

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


# ── Page stubs (R6) ──────────────────────────────────────────────────────────

def _gen_page_stub(page_path: str, auth_required: bool = True) -> str:
    """
    Génère un stub page.tsx pour un Server Component Next.js.
    - auth_required=True  → imports Clerk + guard auth() + redirect
    - auth_required=False → pas d'imports Clerk, page publique sans guard
    Le LLM lit ce fichier et complète la logique métier sans risquer d'altérer
    le régime d'authentification fixé ici de façon déterministe.
    """
    dynamic_params = re.findall(r"\[([^\]]+)\]", page_path)
    component = path_to_page_component(page_path)

    lines: list[str] = []

    if auth_required:
        lines.append("import { auth } from '@clerk/nextjs/server';")
        lines.append("import { redirect } from 'next/navigation';")
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

    if auth_required:
        lines.extend([
            "  const { userId } = await auth();",
            "  if (!userId) redirect('/sign-in');",
        ])

    lines.extend([
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
        fn_params = "{ params }: { params: { slug: string } }"
    elif is_detail:
        fn_params = "{ params }: { params: { id: string } }"
    else:
        fn_params = ""
    lines += [
        "",
        "export const dynamic = 'force-dynamic'",
        "",
        f"export default async function {component}({fn_params}) {{",
    ]

    if page.auth_required:
        lines += [
            "  const { userId } = await auth()",
            "  if (!userId) redirect('/sign-in')",
        ]

    if is_detail:
        if is_slug_detail:
            lines.append(f"  const item = await {camel}Service.getBySlug(params.slug)")
        elif page.auth_required:
            lines.append(f"  const item = await {camel}Service.getById(userId, params.id)")
        else:
            lines.append(f"  const item = await {camel}Service.getPublicById(params.id)")
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


def generate_page_stubs(spec: "ProjectSpec", project_workdir: str) -> dict[str, str]:  # type: ignore[name-defined]
    """
    Génère app/<path>/page.tsx pour chaque page du spec.

    Deux régimes :
    - Page avec `model` → page.tsx ENTIÈREMENT DÉTERMINISTE (retourné dans le dict
      pour ajout dans template_written par dev_graph → LLM ne peut pas écraser).
    - Page sans `model` → stub auth-guard minimal (LLM peut compléter librement,
      non retourné dans le dict template_written).

    Retourne {rel_path: content} pour les pages fully-deterministic uniquement.
    """
    written: dict[str, str] = {}

    for page in spec.pages:
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
            if not os.path.exists(page_abs):
                stub = _gen_page_stub(page.path, page.auth_required)
                with open(page_abs, "w", encoding="utf-8") as f:
                    f.write(stub)
                logger.info("[pages_gen] ✓ stub auth-guard : %s", page_rel)

    logger.info("[pages_gen] %d pages déterministes écrites", len(written))
    return written


# ── Helpers générateur stubs UI ──────────────────────────────────────────────

def _form_fields(model_obj, fk_to_exclude: "set[str] | None" = None) -> list:
    """
    Retourne (field_name, input_type, is_required) pour les champs du formulaire Create.
    Exclut : id, createdAt, updatedAt, owner_field, champs @relation, tableaux, champs FK (déjà rendus en <select>).
    """
    _TEXTAREA_NAMES = {"content", "description", "body", "notes", "message", "text", "bio", "about", "details"}
    owner = model_obj.resolved_owner()
    excluded = {"id", "createdAt", "updatedAt", owner} | (fk_to_exclude or set())
    result = []
    for field in model_obj.fields:
        name = field.name
        if name in excluded:
            continue
        if "@relation" in (field.attributes or ""):
            continue
        if field.type.endswith("[]"):
            continue
        is_required = not field.type.endswith("?")
        base_type = field.type.rstrip("?")
        if base_type == "Boolean":
            input_type = "checkbox"
        elif base_type in ("Int", "Float"):
            input_type = "number"
        elif base_type == "DateTime":
            input_type = "datetime-local"
        elif name.lower() in _TEXTAREA_NAMES:
            input_type = "textarea"
        else:
            input_type = "text"
        result.append((name, input_type, is_required))
    return result


def _fk_fields(model_obj, spec) -> list[tuple[str, str, str]]:
    """
    Retourne les champs FK du modèle sous la forme (field_name, related_model_name, related_camel).
    Heuristique : champ de type String dont le nom se termine par 'Id' et dont la base correspond
    à un modèle existant dans la spec (ex: categoryId → Category si Category ∈ spec.models).
    Ces champs doivent être rendus comme <select> dans les formulaires.
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
        base = name[:-2]  # "categoryId" → "category"
        related_model = base[0].upper() + base[1:]  # → "Category"
        if related_model in model_names:
            result.append((name, related_model, pascal_to_camel(related_model)))
    return result


def _display_fields(model_obj) -> list:
    """Retourne les 2 premiers champs String/Int affichables (non-système)."""
    owner = model_obj.resolved_owner()
    excluded = {"id", "createdAt", "updatedAt", owner}
    result = []
    for field in model_obj.fields:
        if field.name in excluded:
            continue
        if "@relation" in (field.attributes or ""):
            continue
        if field.type.endswith("[]"):
            continue
        if field.type.rstrip("?") in ("String", "Int", "Float"):
            result.append(field.name)
        if len(result) >= 2:
            break
    return result or ["id"]


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


def _compute_relative_import(from_file: str, to_module: str) -> str:
    """
    Calcule l'import relatif TypeScript entre deux chemins posix.
    from_file : 'app/blog/new/page-client.tsx'
    to_module  : 'app/dashboard/actions'
    Retourne   : '../../dashboard/actions'
    """
    from_parts = from_file.replace("\\", "/").split("/")[:-1]
    to_parts = to_module.replace("\\", "/").split("/")
    common = 0
    for a, b in zip(from_parts, to_parts):
        if a == b:
            common += 1
        else:
            break
    up = len(from_parts) - common
    down = to_parts[common:]
    parts = [".."] * up + down
    rel = "/".join(parts) if parts else "."
    return rel if rel.startswith(".") else f"./{rel}"


def _gen_page_client_list(page, model_obj, spec=None) -> str:
    """
    page-client.tsx pour une list page — Level A complet :
    - Header avec titre + bouton "Nouveau" (si page create détectée dans la spec)
    - Chaque item : titre cliquable vers detail (si page detail dans la spec) + champs affichables
    - Bouton Supprimer via Server Action delete{Model}.bind(null, item.id)
    """
    name = model_obj.name
    client = path_to_client_component(page.path)
    serialized = f"Serialized{name}"
    display = _display_fields(model_obj)
    client_rel = f"app/{page.path.strip('/')}/page-client.tsx"

    # Résolution depuis la spec
    delete_fn = f"delete{name}"
    import_actions_path: str | None = None
    detail_href_ts: str | None = None   # template literal TS : `/blog/${item.id}`
    create_path: str | None = None

    if spec is not None:
        # Delete action : seulement sur les pages privées (auth:true).
        # Une page publique (/blog) lit sans droits de mutation — le bouton Supprimer ne doit pas apparaître.
        if page.auth_required:
            list_page = spec.get_list_page_for_model(name)
            actions_module = f"app/{list_page.lstrip('/')}/actions"
            import_actions_path = _compute_relative_import(client_rel, actions_module)

        detail_pages = [p for p in spec.pages if p.page_type == "detail" and p.model == name]
        if detail_pages:
            detail_href_ts = re.sub(r"\[(\w+)\]", r"${item.\1}", detail_pages[0].path)

        list_prefix = page.path.rstrip("/")
        create_pages = [p for p in spec.pages if p.page_type == "create" and p.path.startswith(list_prefix + "/")]
        if create_pages:
            create_path = create_pages[0].path

    lines = [
        "'use client'",
        "import Link from 'next/link'",
        f"import type {{ {serialized} }} from '@/lib/types'",
    ]
    if import_actions_path:
        lines.append(f"import {{ {delete_fn} }} from '{import_actions_path}'")

    lines += [
        "",
        f"interface {client}Props {{",
        f"  items: {serialized}[]",
        "}",
        "",
        f"export default function {client}({{ items }}: {client}Props) {{",
        "  return (",
        '    <main className="container mx-auto p-6">',
        '      <div className="flex justify-between items-center mb-6">',
        f'        <h1 className="text-2xl font-bold">{_pluralize(name)}</h1>',
    ]
    if create_path:
        lines += [
            f'        <Link href="{create_path}" className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">',
            f"          Nouveau {name}",
            "        </Link>",
        ]
    lines += [
        "      </div>",
        "      {items.length === 0 ? (",
        '        <p className="text-gray-500">Aucun élément.</p>',
        "      ) : (",
        '        <ul className="space-y-4">',
        "          {items.map((item) => (",
        '            <li key={item.id} className="border rounded p-4 bg-white shadow-sm flex justify-between items-start">',
        "              <div>",
    ]

    for i, field_name in enumerate(display):
        if i == 0 and detail_href_ts:
            href_attr = "href={`" + detail_href_ts + "`}"
            lines.append(f'                <Link {href_attr} className="font-medium hover:underline">{{item.{field_name}}}</Link>')
        else:
            cls = "font-medium" if i == 0 else "text-sm text-gray-600"
            lines.append(f'                <p className="{cls}">{{item.{field_name}}}</p>')

    lines += [
        '                <p className="text-xs text-gray-400">{item.createdAt}</p>',
        "              </div>",
    ]

    if import_actions_path:
        lines += [
            f"              <form action={{{delete_fn}.bind(null, item.id)}}>",
            '                <button type="submit" className="text-red-500 hover:text-red-700 text-sm">',
            "                  Supprimer",
            "                </button>",
            "              </form>",
        ]

    lines += [
        "            </li>",
        "          ))}",
        "        </ul>",
        "      )}",
        "    </main>",
        "  )",
        "}",
        "",
    ]
    return "\n".join(lines)


def _field_label(field_name: str) -> str:
    """Convertit un nom camelCase en label lisible. Ex: categoryId → Category, firstName → First Name."""
    # Retirer le suffixe Id si c'est un FK
    display = field_name[:-2] if field_name.endswith("Id") else field_name
    # camelCase → mots séparés
    import re as _re
    words = _re.sub(r"(?<!^)(?=[A-Z])", " ", display)
    return words.title()


def _gen_page_client_create(page, model_obj, spec, client_rel: str) -> str:
    """
    page-client.tsx pour une create page — formulaire déterministe avec :
    - Champs scalaires : input typé (text, number, datetime-local, checkbox, textarea)
    - Champs FK (xxxId) : <select> alimenté par les options passées en props depuis le Server Component
    - Champ status : <select> avec options draft/published si détecté
    """
    name = model_obj.name
    client = path_to_client_component(page.path)
    create_fn = f"create{name}"

    list_page = spec.get_list_page_for_model(name)
    route_dir = list_page.lstrip("/")
    actions_module = f"app/{route_dir}/actions"
    import_path = _compute_relative_import(client_rel, actions_module)

    fk_list = _fk_fields(model_obj, spec)
    fk_names = {fk_field for fk_field, _, _ in fk_list}
    fields = _form_fields(model_obj, fk_to_exclude=fk_names)

    # Props interface : une prop xxxOptions par FK
    fk_prop_lines: list[str] = []
    fk_prop_args: list[str] = []
    for _fk_field, related_model, related_camel in fk_list:
        serialized = f"Serialized{related_model}"
        fk_prop_lines.append(f"  {related_camel}Options: {serialized}[]")
        fk_prop_args.append(f"{related_camel}Options")

    # Imports types FK si nécessaire
    fk_type_imports = ""
    if fk_list:
        type_names = ", ".join(f"Serialized{rm}" for _, rm, _ in fk_list)
        fk_type_imports = f"import type {{ {type_names} }} from '@/lib/types'\n"

    has_props = bool(fk_list)
    props_interface = ""
    if has_props:
        props_body = "\n".join(fk_prop_lines)
        props_interface = f"\ninterface {client}Props {{\n{props_body}\n}}\n"
    props_arg = f"{{ {', '.join(fk_prop_args)} }}: {client}Props" if has_props else ""

    lines = [
        "'use client'",
        f"import {{ {create_fn} }} from '{import_path}'",
    ]
    if fk_type_imports:
        lines.append(fk_type_imports.rstrip())
    if props_interface:
        lines.append(props_interface.rstrip())
    lines += [
        "",
        f"export default function {client}({props_arg}) {{",
        "  return (",
        '    <main className="container mx-auto p-6 max-w-lg">',
        f'      <h1 className="text-2xl font-bold mb-6">Nouveau {name}</h1>',
        f'      <form action={{{create_fn}}} className="space-y-4">',
    ]

    # Champs FK en premier (selects)
    for fk_field_name, related_model, related_camel in fk_list:
        label = _field_label(fk_field_name)
        display_field = _display_fields(
            next((m for m in spec.models if m.name == related_model), None) or model_obj
        )[0]
        lines += [
            "        <div>",
            f'          <label className="block text-sm font-medium mb-1">{label}</label>',
            f'          <select name="{fk_field_name}" className="w-full border rounded px-3 py-2" required>',
            f'            <option value="">Sélectionner un(e) {label.lower()}</option>',
            f"            {{{related_camel}Options.map((opt) => (",
            f'              <option key={{opt.id}} value={{opt.id}}>{{opt.{display_field}}}</option>',
            "            ))}",
            "          </select>",
            "        </div>",
        ]

    # Champs scalaires
    for field_name, input_type, required in fields:
        req_attr = " required" if required else ""
        label = _field_label(field_name)
        if field_name.lower() == "status":
            lines += [
                "        <div>",
                f'          <label className="block text-sm font-medium mb-1">{label}</label>',
                f'          <select name="{field_name}" className="w-full border rounded px-3 py-2">',
                '            <option value="draft">Brouillon</option>',
                '            <option value="published">Publié</option>',
                "          </select>",
                "        </div>",
            ]
        elif input_type == "textarea":
            lines += [
                "        <div>",
                f'          <label className="block text-sm font-medium mb-1">{label}</label>',
                f'          <textarea name="{field_name}" rows={{4}} className="w-full border rounded px-3 py-2"{req_attr} />',
                "        </div>",
            ]
        elif input_type == "checkbox":
            lines += [
                '        <div className="flex items-center gap-2">',
                f'          <input name="{field_name}" type="checkbox" />',
                f'          <label className="text-sm font-medium">{label}</label>',
                "        </div>",
            ]
        else:
            lines += [
                "        <div>",
                f'          <label className="block text-sm font-medium mb-1">{label}</label>',
                f'          <input name="{field_name}" type="{input_type}" className="w-full border rounded px-3 py-2"{req_attr} />',
                "        </div>",
            ]

    lines += [
        '        <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">',
        "          Créer",
        "        </button>",
        "      </form>",
        "    </main>",
        "  )",
        "}",
        "",
    ]
    return "\n".join(lines)


def _gen_page_client_detail(page, model_obj, spec=None) -> str:
    """
    page-client.tsx pour une detail page — Level A complet :
    - Lien retour vers la page liste du modèle
    - Titre h1 (premier champ String)
    - dl avec tous les champs scalaires affichables
    """
    name = model_obj.name
    client = path_to_client_component(page.path)
    serialized = f"Serialized{name}"

    owner = model_obj.resolved_owner()
    excluded = {"id", "updatedAt", owner}

    # FK fields (xxxId → modèle connu) : UUIDs bruts, pas utiles en détail Level A
    fk_field_names: set[str] = set()
    if spec is not None:
        model_names = {m.name for m in spec.models}
        for field in model_obj.fields:
            fn = field.name
            if fn not in excluded and fn.endswith("Id") and "@relation" not in (field.attributes or ""):
                related = fn[:-2]
                if (related[0].upper() + related[1:]) in model_names:
                    fk_field_names.add(fn)

    all_display: list[str] = []
    for field in model_obj.fields:
        if field.name in excluded or field.name in fk_field_names:
            continue
        if "@relation" in (field.attributes or ""):
            continue
        if field.type.endswith("[]"):
            continue
        all_display.append(field.name)

    # Premier champ String → titre h1
    title_field = next(
        (f.name for f in model_obj.fields
         if f.name not in excluded
         and f.type.rstrip("?") == "String"
         and "@relation" not in (f.attributes or "")),
        None,
    )
    detail_fields = [f for f in all_display if f != title_field]

    # Lien retour : préférer la liste avec le même régime auth que la page détail
    back_href = "/"
    if spec is not None:
        list_pages = [p for p in spec.pages if p.page_type == "list" and getattr(p, "model", None) == name]
        if list_pages:
            same_auth = [p for p in list_pages if p.auth_required == page.auth_required]
            back_href = (same_auth[0] if same_auth else list_pages[0]).path

    lines = [
        "'use client'",
        "import Link from 'next/link'",
        f"import type {{ {serialized} }} from '@/lib/types'",
        "",
        f"interface {client}Props {{",
        f"  item: {serialized}",
        "}",
        "",
        f"export default function {client}({{ item }}: {client}Props) {{",
        "  return (",
        '    <main className="container mx-auto p-6 max-w-2xl">',
        f'      <Link href="{back_href}" className="text-blue-600 hover:underline text-sm mb-6 inline-block">',
        "        ← Retour",
        "      </Link>",
    ]

    if title_field:
        lines.append(f'      <h1 className="text-2xl font-bold mb-4">{{item.{title_field}}}</h1>')
    else:
        lines.append(f'      <h1 className="text-2xl font-bold mb-4">{name}</h1>')

    if detail_fields:
        lines.append('      <dl className="space-y-4">')
        for field_name in detail_fields:
            label = _field_label(field_name)
            lines += [
                "        <div>",
                f'          <dt className="text-sm font-medium text-gray-500">{label}</dt>',
                f'          <dd className="mt-1 text-sm text-gray-900">{{String(item.{field_name} ?? "—")}}</dd>',
                "        </div>",
            ]
        lines.append("      </dl>")

    lines += [
        "    </main>",
        "  )",
        "}",
        "",
    ]
    return "\n".join(lines)


# ── Stubs page-client (déterministes) ────────────────────────────────────────

def generate_page_client_stubs(spec: "ProjectSpec", project_workdir: str) -> dict[str, str]:  # type: ignore[name-defined]
    """
    Génère app/<path>/page-client.tsx pour chaque page du spec.

    Régimes :
    - list  + model  → list UI (cards) avec SerializedXxx[] props
    - create + model trouvable → form avec champs + import Server Action
    - create sans model         → form générique vide (mieux que <div />)
    - autres                    → stub minimal

    Retourne {rel_path: content} — ajouté à template_written dans dev_graph.py
    pour que le planner exclue ces fichiers et que write_file les protège.
    """
    written: dict[str, str] = {}

    for page in spec.pages:
        model_name = getattr(page, "model", None)
        model_obj  = spec.get_model_by_name(model_name) if model_name else None

        client_rel = (
            f"app/{page.path.strip('/')}/page-client.tsx"
            if page.path.strip("/") else
            "app/page-client.tsx"
        )
        client_abs = os.path.join(project_workdir, client_rel.replace("/", os.sep))

        if os.path.exists(client_abs):
            continue

        os.makedirs(os.path.dirname(client_abs), exist_ok=True)
        client = path_to_client_component(page.path)

        if page.page_type == "list" and model_obj is not None:
            content = _gen_page_client_list(page, model_obj, spec=spec)

        elif page.page_type == "create":
            create_model = model_obj or _find_create_model(page, spec)
            if create_model is not None:
                content = _gen_page_client_create(page, create_model, spec, client_rel)
            else:
                # Formulaire générique sans champs (pas de model détecté)
                content = "\n".join([
                    "'use client'",
                    "",
                    f"export default function {client}() {{",
                    "  return (",
                    '    <main className="container mx-auto p-6 max-w-lg">',
                    '      <h1 className="text-2xl font-bold mb-6">Nouveau</h1>',
                    '      <form className="space-y-4">',
                    '        <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">',
                    "          Créer",
                    "        </button>",
                    "      </form>",
                    "    </main>",
                    "  )",
                    "}",
                    "",
                ])

        elif page.page_type in ("detail", "detail-slug"):
            detail_model = model_obj or _find_detail_model(page, spec)
            if detail_model is not None:
                content = _gen_page_client_detail(page, detail_model, spec=spec)
            else:
                content = "\n".join([
                    "'use client'",
                    "",
                    f"export default function {client}() {{",
                    "  return <div />",
                    "}",
                    "",
                ])

        else:
            # custom — stub minimal
            content = "\n".join([
                "'use client'",
                "",
                f"export default function {client}() {{",
                "  return <div />",
                "}",
                "",
            ])

        with open(client_abs, "w", encoding="utf-8") as f:
            f.write(content)
        written[client_rel] = content
        logger.info("[pages_gen] ✓ page-client : %s (%s)", client_rel, page.page_type)

    logger.info("[pages_gen] %d page-client générés de manière déterministe", len(written))
    return written
