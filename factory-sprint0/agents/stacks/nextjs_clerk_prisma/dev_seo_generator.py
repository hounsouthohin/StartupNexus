"""
agents/stacks/nextjs_clerk_prisma/dev_seo_generator.py
───────────────────────────────────────────────────────
Génération déterministe des fichiers SEO — Sprint 5 (Type D-complet).

Produit (uniquement si l'app a des pages publiques) :
  - app/sitemap.ts : routes publiques statiques + slugs dynamiques (getPublicAll)
  - app/robots.ts  : allow public, disallow préfixes des pages auth, lien sitemap

Le generateMetadata() des pages détail publiques n'est PAS ici — contrainte
Next.js : il doit être exporté depuis page.tsx → généré par _gen_page_full
(dev_pages_generator.py) via build_generate_metadata_block().

Base URL : process.env.NEXT_PUBLIC_APP_URL (fallback localhost:3000).
"""
from __future__ import annotations

import logging
import os

from .dev_naming import pascal_to_camel, pascal_to_kebab

logger = logging.getLogger(__name__)

# Champs candidats pour title / description dans generateMetadata
_TITLE_CANDIDATES = ("title", "name", "heading", "label", "subject")
_DESC_CANDIDATES = ("excerpt", "summary", "description", "content", "body", "instructions", "details", "text")


def _static_prefix(path: str) -> str:
    """Préfixe statique d'un chemin ('/blog/[slug]' → '/blog')."""
    parts = [p for p in path.strip("/").split("/") if not p.startswith("[")]
    return "/" + "/".join(parts) if parts else "/"


def _pick_field(model_obj, candidates: tuple[str, ...]) -> str | None:
    """Premier champ String du modèle dont le nom est dans candidates."""
    field_names = {f.name: f.type.rstrip("?").rstrip("[]") for f in model_obj.fields}
    for c in candidates:
        if field_names.get(c) == "String":
            return c
    return None


def build_generate_metadata_block(page, model_obj, camel: str) -> list[str]:
    """
    Lignes TS du bloc generateMetadata pour une page detail-slug PUBLIQUE.
    Inséré par _gen_page_full — le service est déjà importé par la page.
    getBySlug lève notFound() si absent : Next.js rend la 404 (comportement correct).
    """
    title_field = _pick_field(model_obj, _TITLE_CANDIDATES)
    desc_field = _pick_field(model_obj, _DESC_CANDIDATES)
    title_expr = (
        f"String(item.{title_field} ?? '{model_obj.name}')"
        if title_field else f"'{model_obj.name}'"
    )
    desc_expr = (
        f"String(item.{desc_field} ?? '').slice(0, 160)"
        if desc_field else "''"
    )
    return [
        "",
        "export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {",
        "  const { slug } = await params",
        f"  const item = await {camel}Service.getBySlug(slug)",
        f"  const title = {title_expr}",
        f"  const description = {desc_expr}",
        "  return {",
        "    title,",
        "    description,",
        "    openGraph: { title, description, type: 'article' },",
        "  }",
        "}",
    ]


def generate_seo_files(spec, contexts: dict, project_workdir: str) -> dict[str, str]:
    """
    Écrit app/sitemap.ts + app/robots.ts si l'app a au moins une page publique.
    Retourne {rel_path: content} pour intégration dans template_written.
    """
    pages = getattr(spec, "pages", []) or []
    public_pages = [p for p in pages if not p.auth_required]
    if not public_pages:
        logger.info("[seo_gen] aucune page publique → skip sitemap/robots")
        return {}

    written: dict[str, str] = {}

    # ── Modèles avec detail-slug public → entrées dynamiques du sitemap ──────
    # (model, camel, kebab, static_prefix) — le service a getPublicAll (page publique)
    slug_entries: list[tuple[str, str, str]] = []
    seen_models: set[str] = set()
    for p in public_pages:
        if p.page_type != "detail-slug" or not p.model or p.model in seen_models:
            continue
        ctx = (contexts or {}).get(p.model)
        if ctx is not None and not ctx.has_slug:
            continue
        seen_models.add(p.model)
        slug_entries.append((p.model, pascal_to_camel(p.model), _static_prefix(p.path)))

    # ── Routes publiques statiques (sans segment dynamique) ──────────────────
    static_paths: list[str] = []
    for p in public_pages:
        if "[" in p.path:
            continue
        if p.path not in static_paths:
            static_paths.append(p.path)

    # ── sitemap.ts ────────────────────────────────────────────────────────────
    lines: list[str] = [
        "// AUTO-GÉNÉRÉ PAR dev_seo_generator.py — NE PAS MODIFIER",
        "import type { MetadataRoute } from 'next'",
    ]
    for model_name, camel, _prefix in slug_entries:
        kebab = pascal_to_kebab(model_name)
        lines.append(f"import {{ {camel}Service }} from '@/lib/services/{kebab}.service'")
    lines += [
        "",
        "const BASE = process.env.NEXT_PUBLIC_APP_URL ?? 'http://localhost:3000'",
        "",
        "export const dynamic = 'force-dynamic'",
        "",
        "export default async function sitemap(): Promise<MetadataRoute.Sitemap> {",
        "  const entries: MetadataRoute.Sitemap = [",
    ]
    for path in static_paths:
        url = "BASE" if path == "/" else f"`${{BASE}}{path}`"
        lines.append(f"    {{ url: {url}, lastModified: new Date() }},")
    lines.append("  ]")
    for model_name, camel, prefix in slug_entries:
        lines += [
            f"  const {camel}s = await {camel}Service.getPublicAll()",
            f"  entries.push(...{camel}s.map(item => ({{",
            f"    url: `${{BASE}}{prefix}/${{item.slug}}`,",
            "    lastModified: item.updatedAt ? new Date(item.updatedAt) : new Date(),",
            "  })))",
        ]
    lines += [
        "  return entries",
        "}",
        "",
    ]
    written["app/sitemap.ts"] = "\n".join(lines)

    # ── robots.ts ─────────────────────────────────────────────────────────────
    # Disallow : préfixes statiques des pages auth + pages Clerk
    auth_prefixes: list[str] = []
    for p in pages:
        if not p.auth_required:
            continue
        prefix = _static_prefix(p.path)
        root = "/" + prefix.strip("/").split("/")[0] if prefix != "/" else "/"
        if root != "/" and root not in auth_prefixes:
            auth_prefixes.append(root)
    for clerk_route in ("/sign-in", "/sign-up"):
        if clerk_route not in auth_prefixes:
            auth_prefixes.append(clerk_route)
    disallow_ts = ", ".join(f"'{p}'" for p in auth_prefixes)

    robots = "\n".join([
        "// AUTO-GÉNÉRÉ PAR dev_seo_generator.py — NE PAS MODIFIER",
        "import type { MetadataRoute } from 'next'",
        "",
        "const BASE = process.env.NEXT_PUBLIC_APP_URL ?? 'http://localhost:3000'",
        "",
        "export default function robots(): MetadataRoute.Robots {",
        "  return {",
        "    rules: {",
        "      userAgent: '*',",
        "      allow: '/',",
        f"      disallow: [{disallow_ts}],",
        "    },",
        "    sitemap: `${BASE}/sitemap.xml`,",
        "  }",
        "}",
        "",
    ])
    written["app/robots.ts"] = robots

    # Écriture disque
    for rel, content in written.items():
        abs_path = os.path.join(project_workdir, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info("[seo_gen] ✓ %s", rel)

    return written
