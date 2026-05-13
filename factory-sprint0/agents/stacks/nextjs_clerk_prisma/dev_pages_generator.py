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


def _gen_page_full(page, model_obj) -> str:
    """
    Génère un page.tsx ENTIÈREMENT DÉTERMINISTE pour une page avec champ `model`.
    Le fichier résultant est ajouté à template_written → le LLM ne peut pas l'écraser.

    Patterns générés :
    - Liste privée  : auth() + getAll(userId) ou getAllWithRelations(userId) → <XxxClient items={items} />
    - Liste publique: getPublished() sans userId                             → <XxxClient items={items} />
    - Création (auth=True) : auth() + <XxxClient />  (sans données)
    - Création (auth=False): <XxxClient />            (sans données ni auth)
    """
    name = model_obj.name
    camel = pascal_to_camel(name)
    kebab = pascal_to_kebab(name)
    client = path_to_client_component(page.path)
    component = path_to_page_component(page.path)
    is_create = page.page_type == "create"
    has_relations = _model_has_relations(model_obj)
    has_status = _model_has_status(model_obj)

    lines: list[str] = []

    if page.auth_required:
        lines += [
            "import { auth } from '@clerk/nextjs/server'",
            "import { redirect } from 'next/navigation'",
        ]

    lines += [
        f"import {client} from './page-client'",
    ]

    if not is_create:
        lines.append(f"import {{ {camel}Service }} from '@/lib/services/{kebab}.service'")

    lines += [
        "",
        "export const dynamic = 'force-dynamic'",
        "",
        f"export default async function {component}() {{",
    ]

    if page.auth_required:
        lines += [
            "  const { userId } = await auth()",
            "  if (!userId) redirect('/sign-in')",
        ]

    if not is_create:
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
                f"{camel}Service.getAll()"
            )
        lines += [
            f"  const items = await {service_call}",
            f"  return <{client} items={{items}} />",
        ]
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

        if model_obj is not None:
            content = _gen_page_full(page, model_obj)
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


def generate_page_client_stubs(spec: "ProjectSpec", project_workdir: str) -> dict[str, str]:  # type: ignore[name-defined]
    """
    Génère app/<path>/page-client.tsx avec l'interface props correcte pour chaque
    page ayant un champ `model`. Le fichier N'EST PAS dans template_written — le LLM
    complète le JSX body tout en conservant l'interface déjà définie.

    Garantit la cohérence avec page.tsx (locked) :
    page.tsx passe   <XxxClient items={items} />
    page-client.tsx  interface XxxClientProps { items: SerializedXxx[] }

    Retourne {rel_path: content} pour traçabilité.
    """
    written: dict[str, str] = {}

    for page in spec.pages:
        model_name = getattr(page, "model", None)
        model_obj = spec.get_model_by_name(model_name) if model_name else None
        is_create = page.page_type == "create"

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

        if model_obj is not None and not is_create:
            serialized = f"Serialized{model_obj.name}"
            content = "\n".join([
                "'use client'",
                f"import type {{ {serialized} }} from '@/lib/types'",
                "",
                f"interface {client}Props {{",
                f"  items: {serialized}[]",
                "}",
                "",
                f"export default function {client}({{ items }}: {client}Props) {{",
                "  return <div />",
                "}",
                "",
            ])
        else:
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
        logger.info("[pages_gen] ✓ page-client stub : %s", client_rel)

    logger.info("[pages_gen] %d page-client stubs écrits", len(written))
    return written
