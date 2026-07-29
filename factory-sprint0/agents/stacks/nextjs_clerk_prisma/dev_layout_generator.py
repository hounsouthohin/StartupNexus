"""
dev_layout_generator.py — Shell déterministe (Sprint A — Layout Diversification)

Génère depuis ProjectSpec + design_system.layout_type :
  layout_type="sidebar" (saas_dashboard, finance, education, default) :
    - app/components/layout/DashboardShell.tsx   sidebar nav active-aware
    - app/layout.tsx                             ClerkProvider + DashboardShell

  layout_type="topnav" (editorial, wellness, marketplace, community) :
    - app/components/layout/TopNavShell.tsx      sticky header + nav active-aware
    - app/layout.tsx                             ClerkProvider + TopNavShell

Le LLM ne touche jamais ces fichiers — ils sont dans template_written (protégés).
"""
from __future__ import annotations

import pathlib
from typing import Any, Dict, List

# ─────────────────────────────────────────────────────────────────────────────
# Template — DashboardShell (sidebar)
# ─────────────────────────────────────────────────────────────────────────────

_SIDEBAR_SHELL_TEMPLATE = '''\
"use client"
import React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { UserButton } from "@clerk/nextjs"

interface NavItem { href: string; label: string; exact?: boolean; priv?: boolean; base?: boolean }

// Rôle privilégié (vide = mono-acteur). Nav filtrée par la SURFACE de l'acteur (S2).
// Annoté `string` : sinon TS réduit au littéral et `!== ""` = comparaison sans overlap (TS2367).
const PRIVILEGED_ROLE: string = "__PRIVILEGED_ROLE__"

const NAV: NavItem[] = [
__NAV_LINES__
]

export function DashboardShell({ children, role }: { children: React.ReactNode; role?: string | null }) {
  const pathname = usePathname()
  const PUBLIC_PATHS: string[] = [__PUBLIC_PATHS__]
  const isAuthPage = pathname.startsWith("/sign-in") || pathname.startsWith("/sign-up") || PUBLIC_PATHS.some(p => pathname === p || pathname.startsWith(p + "/"))

  if (isAuthPage) return <>{children}</>

  const isPrivileged = PRIVILEGED_ROLE !== "" && role === PRIVILEGED_ROLE
  const navItems = NAV.filter((i) => (isPrivileged ? i.priv !== false : i.base !== false))

  return (
    <div className="flex h-screen overflow-hidden bg-__PAGE_BG__">
      <aside className="w-60 shrink-0 bg-__SIDEBAR_BG__ border-r border-__BORDER__ flex flex-col">
        <div className="h-14 flex items-center px-5 border-b border-__BORDER__">
          <span className="text-base font-semibold text-__BRAND_TEXT__ truncate">__APP_NAME__</span>
        </div>
        <nav className="flex-1 px-3 py-3 space-y-0.5 overflow-y-auto">
          {navItems.map((item) => {
            const active = item.exact
              ? pathname === item.href
              : pathname === item.href || pathname.startsWith(item.href + "/")
            return (
              <Link
                key={item.href}
                href={item.href}
                className={[
                  "flex items-center __NAV_PADDING__ rounded-lg text-sm font-medium __TRANSITION__",
                  active
                    ? "__ACTIVE_CLS__"
                    : "__INACTIVE_CLS__",
                ].join(" ")}
              >
                {item.label}
              </Link>
            )
          })}
        </nav>
        <div className="p-3 border-t border-__BORDER__">
          <UserButton />
        </div>
      </aside>
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  )
}
'''

_SIDEBAR_LAYOUT_TEMPLATE = '''\
import { ClerkProvider } from "@clerk/nextjs"
import { DashboardShell } from "@/app/components/layout/DashboardShell"
import "./globals.css"
import type { ReactNode } from "react"

export const metadata = { title: "__APP_NAME__" }

export default function RootLayout({ children }: { children: ReactNode }) {
  const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY

  const canUseClerk =
    typeof publishableKey === "string" &&
    publishableKey.startsWith("pk_") &&
    !publishableKey.includes("placeholder")

  if (!canUseClerk) {
    return (
      <html lang="fr">
        <body>{children}</body>
      </html>
    )
  }

  return (
    <ClerkProvider publishableKey={publishableKey}>
      <html lang="fr">
        <body>
          <DashboardShell>{children}</DashboardShell>
        </body>
      </html>
    </ClerkProvider>
  )
}
'''

# ─────────────────────────────────────────────────────────────────────────────
# Template — TopNavShell (header sticky)
# ─────────────────────────────────────────────────────────────────────────────

_TOPNAV_SHELL_TEMPLATE = '''\
"use client"
import React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { UserButton, useUser } from "@clerk/nextjs"

interface NavItem { href: string; label: string; exact?: boolean; priv?: boolean; base?: boolean }

// Rôle privilégié (vide = mono-acteur). Les liens sont filtrés par la SURFACE de l'acteur (S2) :
// chacun ne voit dans sa nav que ce qui compose SON app. Annoté `string` (sinon TS réduit au
// type littéral et `!== ""` devient une comparaison « sans overlap » → TS2367).
const PRIVILEGED_ROLE: string = "__PRIVILEGED_ROLE__"

const AUTH_NAV: NavItem[] = [
__AUTH_NAV_LINES__
]

const PUBLIC_NAV: NavItem[] = [
__PUBLIC_NAV_LINES__
]

export function TopNavShell({ children, role }: { children: React.ReactNode; role?: string | null }) {
  const pathname = usePathname()
  const { isSignedIn } = useUser()
  const isAuthPage = pathname.startsWith("/sign-in") || pathname.startsWith("/sign-up")

  if (isAuthPage) return <>{children}</>

  const isPrivileged = PRIVILEGED_ROLE !== "" && role === PRIVILEGED_ROLE
  const authNav = AUTH_NAV.filter((i) => (isPrivileged ? i.priv !== false : i.base !== false))
  const nav = isSignedIn ? authNav : PUBLIC_NAV

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-50 w-full border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <span className="text-base font-semibold text-foreground">__APP_NAME__</span>
            <nav className="hidden md:flex items-center gap-1">
              {nav.map((item) => {
                const active = item.exact
                  ? pathname === item.href
                  : pathname === item.href || pathname.startsWith(item.href + "/")
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={[
                      "px-3 py-1.5 rounded-md text-sm font-medium __TRANSITION__",
                      active
                        ? "bg-primary/10 text-primary"
                        : "text-muted-foreground hover:text-foreground hover:bg-muted/50",
                    ].join(" ")}
                  >
                    {item.label}
                  </Link>
                )
              })}
            </nav>
          </div>
          <div className="flex items-center gap-2">
            {!isSignedIn && (
              <Link
                href="/sign-in"
                className="px-4 py-1.5 rounded-md text-sm font-medium bg-primary text-primary-foreground hover:bg-primary/90 __TRANSITION__"
              >
                Connexion
              </Link>
            )}
            <UserButton />
          </div>
        </div>
      </header>
      <main>{children}</main>
    </div>
  )
}
'''

_TOPNAV_LAYOUT_TEMPLATE = '''\
import { ClerkProvider } from "@clerk/nextjs"
import { TopNavShell } from "@/app/components/layout/TopNavShell"
import "./globals.css"
import type { ReactNode } from "react"

export const metadata = { title: "__APP_NAME__" }

export default function RootLayout({ children }: { children: ReactNode }) {
  const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY

  const canUseClerk =
    typeof publishableKey === "string" &&
    publishableKey.startsWith("pk_") &&
    !publishableKey.includes("placeholder")

  if (!canUseClerk) {
    return (
      <html lang="fr">
        <body>{children}</body>
      </html>
    )
  }

  return (
    <ClerkProvider publishableKey={publishableKey}>
      <html lang="fr">
        <body>
          <TopNavShell>{children}</TopNavShell>
        </body>
      </html>
    </ClerkProvider>
  )
}
'''

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

_LABEL_OVERRIDES: Dict[str, str] = {
    "dashboard": "Tableau de bord",
    "home":      "Accueil",
    "settings":  "Paramètres",
    "profile":   "Profil",
}


def _path_of(page: Any) -> str:
    if isinstance(page, str):
        return page
    if isinstance(page, dict):
        return page.get("path", "")
    return ""


def _auth_of(page: Any) -> bool:
    """Retourne True si la page est authentifiée."""
    path = _path_of(page)
    if path.startswith("/dashboard"):
        return True
    if isinstance(page, dict):
        return bool(page.get("auth_required"))
    return bool(getattr(page, "auth_required", False))


def _label(segment: str) -> str:
    s = segment.lower()
    if s in _LABEL_OVERRIDES:
        return _LABEL_OVERRIDES[s]
    return s.replace("-", " ").title()


def _is_exact(path: str) -> bool:
    parts = path.strip("/").split("/")
    return parts[-1].lower() in ("dashboard", "") or path == "/"


def _is_dynamic(path: str) -> bool:
    return any(seg in path for seg in ("/new", "/edit", "[", "{", "..."))


def _nav_items(pages: List[Any], extra_labels: Dict[str, str] | None = None) -> List[Dict[str, Any]]:
    """Pages authentifiées → liens sidebar / AUTH_NAV topnav."""
    extra_labels = extra_labels or {}
    seen: set[str] = set()
    items: List[Dict[str, Any]] = []
    for page in pages:
        path = _path_of(page)
        if not path or not _auth_of(page) or _is_dynamic(path):
            continue
        if path in seen:
            continue
        seen.add(path)
        parts = [p for p in path.strip("/").split("/") if p]
        if not parts:
            label = _LABEL_OVERRIDES.get("dashboard", "Tableau de bord")
            items.append({"href": "/", "label": label, "exact": True})
            continue
        label = extra_labels.get(path) or _label(parts[-1])
        items.append({"href": path, "label": label, "exact": _is_exact(path)})
    items.sort(key=lambda x: (len(x["href"].split("/")), x["href"]))
    return items


def _public_nav_items(pages: List[Any], extra_labels: Dict[str, str] | None = None) -> List[Dict[str, Any]]:
    """Pages publiques → PUBLIC_NAV topnav (visible non-authentifiés)."""
    extra_labels = extra_labels or {}
    seen: set[str] = set()
    items: List[Dict[str, Any]] = []
    for page in pages:
        path = _path_of(page)
        if not path or _auth_of(page) or _is_dynamic(path):
            continue
        if path.startswith("/sign-"):
            continue
        if path in seen:
            continue
        seen.add(path)
        parts = [p for p in path.strip("/").split("/") if p]
        label = extra_labels.get(path) or (_label(parts[-1]) if parts else "Accueil")
        items.append({"href": path, "label": label, "exact": True if not parts else _is_exact(path)})
    items.sort(key=lambda x: (len(x["href"].split("/")), x["href"]))
    return items


def _app_display_name(project_name: str) -> str:
    return project_name.replace("-", " ").title()


# ─────────────────────────────────────────────────────────────────────────────
# Tokens design
# ─────────────────────────────────────────────────────────────────────────────

_DARK_SIDEBAR_BGS = {
    "slate-900", "slate-800", "slate-700",
    "gray-900", "gray-800", "gray-700",
    "zinc-900", "zinc-800", "neutral-900", "neutral-800",
    "indigo-900", "indigo-800",
    "violet-900", "violet-800",
}

_NAV_PADDING: Dict[str, str] = {
    "compact":  "px-2 py-1.5",
    "normal":   "px-3 py-2",
    "spacious": "px-4 py-3",
}

_TRANSITION_CLS: Dict[str, str] = {
    "none":     "transition-none",
    "standard": "transition-colors duration-150",
    "enhanced": "transition-all duration-300 ease-out",
}


def _resolve_design(design_system: Dict[str, Any], app_name: str) -> Dict[str, str]:
    primary         = design_system.get("primary_color", "blue-700")
    sidebar         = design_system.get("sidebar_bg", "white")
    brand           = design_system.get("brand_name", app_name) or app_name
    density         = design_system.get("density", "normal")
    animation_level = design_system.get("animation_level", "standard")

    is_dark_sidebar = sidebar in _DARK_SIDEBAR_BGS

    if is_dark_sidebar:
        brand_text   = "white"
        active_cls   = "bg-primary text-primary-foreground"
        inactive_cls = "text-slate-300 hover:bg-slate-700 hover:text-white"
        border       = "slate-700"
    else:
        brand_text   = "gray-900"
        active_cls   = "bg-primary/10 text-primary"
        inactive_cls = "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
        border       = "gray-200"

    page_bg     = "gray-50" if not is_dark_sidebar else "gray-100"
    nav_padding = _NAV_PADDING.get(density, "px-3 py-2")
    transition  = _TRANSITION_CLS.get(animation_level, "transition-colors duration-150")

    return {
        "sidebar_bg":   sidebar,
        "brand_text":   brand_text,
        "active_cls":   active_cls,
        "inactive_cls": inactive_cls,
        "border":       border,
        "page_bg":      page_bg,
        "brand_name":   brand,
        "nav_padding":  nav_padding,
        "transition":   transition,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Générateurs individuels
# ─────────────────────────────────────────────────────────────────────────────

def _generate_sidebar_layout(
    project_workdir: str,
    app_name: str,
    pages: List[Any],
    tokens: Dict[str, str],
    extra_labels: Dict[str, str] | None = None,
    multi_actor: bool = False,
    priv_role: str = "",
    vis=None,
) -> Dict[str, str]:
    """Génère DashboardShell.tsx + layout.tsx (sidebar)."""
    nav = _nav_items(pages, extra_labels)
    vis = vis or (lambda _p: (True, True))
    public_paths = [
        _path_of(p) for p in pages
        if not _auth_of(p) and _path_of(p) and not _path_of(p).startswith("/sign-")
    ]

    def _nav_line(item: Dict[str, Any]) -> str:
        _priv, _base = vis(item["href"])
        return (
            f'  {{ href: "{item["href"]}", label: "{item["label"]}", '
            f'exact: {str(item["exact"]).lower()}, priv: {str(_priv).lower()}, base: {str(_base).lower()} }},'
        )

    nav_lines = "\n".join(_nav_line(item) for item in nav)
    pub_paths_ts = ", ".join(f'"{p}"' for p in public_paths)

    shell_content = (
        _SIDEBAR_SHELL_TEMPLATE
        .replace("__APP_NAME__",     tokens["brand_name"])
        .replace("__PRIVILEGED_ROLE__", priv_role)
        .replace("__NAV_LINES__",    nav_lines)
        .replace("__SIDEBAR_BG__",   tokens["sidebar_bg"])
        .replace("__PAGE_BG__",      tokens["page_bg"])
        .replace("__BORDER__",       tokens["border"])
        .replace("__BRAND_TEXT__",   tokens["brand_text"])
        .replace("__ACTIVE_CLS__",   tokens["active_cls"])
        .replace("__INACTIVE_CLS__", tokens["inactive_cls"])
        .replace("__PUBLIC_PATHS__", pub_paths_ts)
        .replace("__NAV_PADDING__",  tokens["nav_padding"])
        .replace("__TRANSITION__",   tokens["transition"])
    )
    layout_content = _layout_content("DashboardShell", tokens["brand_name"], multi_actor)

    return _write_files(project_workdir, [
        ("app/components/layout/DashboardShell.tsx", shell_content),
        ("app/layout.tsx", layout_content),
    ])


def _generate_topnav_layout(
    project_workdir: str,
    app_name: str,
    pages: List[Any],
    tokens: Dict[str, str],
    extra_labels: Dict[str, str] | None = None,
    multi_actor: bool = False,
    priv_role: str = "",
    vis=None,
) -> Dict[str, str]:
    """Génère TopNavShell.tsx + layout.tsx (topnav)."""
    auth_nav    = _nav_items(pages, extra_labels)
    public_nav  = _public_nav_items(pages, extra_labels)
    transition  = tokens["transition"]
    vis = vis or (lambda _p: (True, True))

    def _nav_line(item: Dict[str, Any]) -> str:
        _priv, _base = vis(item["href"])
        return (
            f'  {{ href: "{item["href"]}", label: "{item["label"]}", '
            f'exact: {str(item["exact"]).lower()}, priv: {str(_priv).lower()}, base: {str(_base).lower()} }},'
        )

    auth_nav_lines   = "\n".join(_nav_line(i) for i in auth_nav)
    public_nav_lines = "\n".join(_nav_line(i) for i in public_nav)

    shell_content = (
        _TOPNAV_SHELL_TEMPLATE
        .replace("__APP_NAME__",        app_name)
        .replace("__PRIVILEGED_ROLE__", priv_role)
        .replace("__AUTH_NAV_LINES__",  auth_nav_lines)
        .replace("__PUBLIC_NAV_LINES__", public_nav_lines)
        .replace("__TRANSITION__",      transition)
    )
    layout_content = _layout_content("TopNavShell", app_name, multi_actor)

    return _write_files(project_workdir, [
        ("app/components/layout/TopNavShell.tsx", shell_content),
        ("app/layout.tsx", layout_content),
    ])


def _layout_content(shell_component: str, app_name: str, multi_actor: bool) -> str:
    """Construit app/layout.tsx. En MULTI-ACTEUR : layout serveur async qui lit le rôle
    (getCurrentRole) et le passe au shell → nav filtrée par acteur (S2). Sinon : layout
    classique (aucune dépendance à lib/auth-role, comportement historique mono-acteur)."""
    role_import = 'import { getCurrentRole } from "@/lib/auth-role"\n' if multi_actor else ""
    async_kw    = "async " if multi_actor else ""
    role_fetch  = "  const role = await getCurrentRole()\n" if multi_actor else ""
    role_prop   = " role={role}" if multi_actor else ""
    return (
        'import { ClerkProvider } from "@clerk/nextjs"\n'
        f'import {{ {shell_component} }} from "@/app/components/layout/{shell_component}"\n'
        f'{role_import}'
        'import "./globals.css"\n'
        'import type { ReactNode } from "react"\n'
        '\n'
        f'export const metadata = {{ title: "{app_name}" }}\n'
        '\n'
        f'export default {async_kw}function RootLayout({{ children }}: {{ children: ReactNode }}) {{\n'
        '  const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY\n'
        '\n'
        '  const canUseClerk =\n'
        '    typeof publishableKey === "string" &&\n'
        '    publishableKey.startsWith("pk_") &&\n'
        '    !publishableKey.includes("placeholder")\n'
        '\n'
        '  if (!canUseClerk) {\n'
        '    return (\n'
        '      <html lang="fr">\n'
        '        <body>{children}</body>\n'
        '      </html>\n'
        '    )\n'
        '  }\n'
        '\n'
        f'{role_fetch}'
        '  return (\n'
        '    <ClerkProvider publishableKey={publishableKey}>\n'
        '      <html lang="fr">\n'
        '        <body>\n'
        f'          <{shell_component}{role_prop}>{{children}}</{shell_component}>\n'
        '        </body>\n'
        '      </html>\n'
        '    </ClerkProvider>\n'
        '  )\n'
        '}\n'
    )


def _write_files(project_workdir: str, pairs: list) -> Dict[str, str]:
    base = pathlib.Path(project_workdir)
    written: Dict[str, str] = {}
    for rel, content in pairs:
        abs_path = base / rel
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_text(content, encoding="utf-8")
        written[rel] = content
    return written


# ─────────────────────────────────────────────────────────────────────────────
# Point d'entrée public
# ─────────────────────────────────────────────────────────────────────────────

def generate_layout(
    project_workdir: str,
    project_name: str,
    project_spec: Dict[str, Any],
    spec_obj: Any = None,
    enriched_spec: Any = None,
) -> Dict[str, str]:
    """
    Écrit le shell (sidebar ou topnav) + layout.tsx sur disque.
    Retourne {rel_path: content} pour intégration dans template_written.
    Lit project_spec["design_system"]["layout_type"] pour choisir le shell.
    spec_obj : ProjectSpec objet optionnel — source de title_plurals pour labels nav localisés.
    enriched_spec : porte la SURFACE par acteur (S2) → nav filtrée par rôle.
    """
    pages: List[Any]              = project_spec.get("pages", [])
    design_system: Dict[str, Any] = project_spec.get("design_system", {}) or {}
    app_name    = _app_display_name(project_name)
    layout_type = design_system.get("layout_type", "sidebar")
    tokens      = _resolve_design(design_system, app_name)

    # Mapping path → label localisé depuis title_plurals (ex: /invoices → "Factures")
    _title_plurals: Dict[str, str] = (
        getattr(spec_obj, "title_plurals", None) or project_spec.get("title_plurals", {})
    ) or {}
    extra_labels: Dict[str, str] = {}
    for page in pages:
        _model = page.get("model") if isinstance(page, dict) else getattr(page, "model", None)
        _path  = _path_of(page)
        if _model and _path and _model in _title_plurals:
            extra_labels[_path] = _title_plurals[_model]

    # ── S2 — surface par acteur : quelle nav chaque rôle voit ────────────────────
    _roles      = getattr(enriched_spec, "roles", None) if enriched_spec else None
    priv_role   = getattr(_roles, "privileged_role", "") if _roles else ""
    surface     = getattr(_roles, "surface", {}) if _roles else {}
    all_roles   = getattr(_roles, "roles", []) if _roles else []
    base_actor  = next((r for r in all_roles if r != priv_role), "")
    multi_actor = bool(priv_role and surface and len(all_roles) >= 2)
    _page_model: Dict[str, Any] = {}
    for page in pages:
        _m  = page.get("model") if isinstance(page, dict) else getattr(page, "model", None)
        _pa = _path_of(page)
        if _pa:
            _page_model[_pa] = _m
    _surface_models: set = set()
    for _v in (surface or {}).values():
        _surface_models.update(_v or [])

    def _vis(path: str):
        """(visible_privilégié, visible_base) pour une page. Défaut permissif : si pas de
        multi-acteur, ou page sans modèle, ou modèle dans AUCUNE surface → visible partout."""
        _m = _page_model.get(path)
        if not multi_actor or not _m or _m not in _surface_models:
            return (True, True)
        return (_m in surface.get(priv_role, []), _m in surface.get(base_actor, []))

    if layout_type == "topnav":
        return _generate_topnav_layout(project_workdir, app_name, pages, tokens, extra_labels,
                                       multi_actor=multi_actor, priv_role=priv_role, vis=_vis)
    else:
        return _generate_sidebar_layout(project_workdir, app_name, pages, tokens, extra_labels,
                                        multi_actor=multi_actor, priv_role=priv_role, vis=_vis)
