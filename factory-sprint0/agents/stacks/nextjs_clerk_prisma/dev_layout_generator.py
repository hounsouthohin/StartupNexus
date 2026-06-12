"""
dev_layout_generator.py — DashboardShell déterministe (Sprint 5.0)

Génère depuis ProjectSpec :
  - app/components/layout/DashboardShell.tsx   sidebar nav active-aware
  - app/layout.tsx                             ClerkProvider + DashboardShell

Appelé par frontend_activity._bootstrap_layout() AVANT le FrontendAgent LLM.
Le LLM ne touche jamais ces fichiers — ils sont dans les protections.
"""
from __future__ import annotations

import pathlib
from typing import Any, Dict, List

# ─────────────────────────────────────────────────────────────────────────────
# Templates raw (placeholders __UPPER_SNAKE__)
# ─────────────────────────────────────────────────────────────────────────────

_SHELL_TEMPLATE = '''\
"use client"
import React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { UserButton } from "@clerk/nextjs"

interface NavItem { href: string; label: string; exact?: boolean }

const NAV: NavItem[] = [
__NAV_LINES__
]

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const PUBLIC_PATHS: string[] = [__PUBLIC_PATHS__]
  const isAuthPage = pathname.startsWith("/sign-in") || pathname.startsWith("/sign-up") || PUBLIC_PATHS.some(p => pathname === p || pathname.startsWith(p + "/"))

  if (isAuthPage) return <>{children}</>

  return (
    <div className="flex h-screen overflow-hidden bg-__PAGE_BG__">
      <aside className="w-60 shrink-0 bg-__SIDEBAR_BG__ border-r border-__BORDER__ flex flex-col">
        <div className="h-14 flex items-center px-5 border-b border-__BORDER__">
          <span className="text-base font-semibold text-__BRAND_TEXT__ truncate">__APP_NAME__</span>
        </div>
        <nav className="flex-1 px-3 py-3 space-y-0.5 overflow-y-auto">
          {NAV.map((item) => {
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

_LAYOUT_TEMPLATE = '''\
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
    """Retourne True si la page est authentifiée.
    Convention fiable : tout chemin /dashboard/* est protégé par le middleware Clerk.
    AppPage Pydantic sérialise le champ en auth_required (pas auth).
    """
    path = _path_of(page)
    if path.startswith("/dashboard"):
        return True
    if isinstance(page, dict):
        return bool(page.get("auth_required"))
    # Pydantic AppPage object (spec_obj.pages)
    return bool(getattr(page, "auth_required", False))


def _label(segment: str) -> str:
    s = segment.lower()
    if s in _LABEL_OVERRIDES:
        return _LABEL_OVERRIDES[s]
    return s.replace("-", " ").title()


def _is_exact(path: str) -> bool:
    """dashboard root ou racine = exact match pour ne pas rester actif sur les sous-routes."""
    parts = path.strip("/").split("/")
    return parts[-1].lower() in ("dashboard", "") or path == "/"


def _nav_items(pages: List[Any]) -> List[Dict[str, str]]:
    """
    Filtre les pages du ProjectSpec → liens de navigation sidebar :
    - auth=True seulement
    - Exclut /new, /edit, segments dynamiques [id]
    - Trie par longueur de chemin
    """
    seen: set[str] = set()
    items: List[Dict[str, Any]] = []

    for page in pages:
        path = _path_of(page)
        if not path or not _auth_of(page):
            continue
        if any(seg in path for seg in ("/new", "/edit", "[", "{", "...")):
            continue

        # Déduplique les chemins identiques
        if path in seen:
            continue
        seen.add(path)

        parts = [p for p in path.strip("/").split("/") if p]
        if not parts:
            continue

        label = _label(parts[-1])
        exact = _is_exact(path)
        items.append({"href": path, "label": label, "exact": exact})

    # Tri : chemin le plus court d'abord → dashboard en haut
    items.sort(key=lambda x: (len(x["href"].split("/")), x["href"]))
    return items


def _app_display_name(project_name: str) -> str:
    """event-board → Event Board"""
    return project_name.replace("-", " ").title()


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────────

_DARK_SIDEBAR_BGS = {
    "slate-900", "slate-800", "slate-700",
    "gray-900", "gray-800", "gray-700",
    "zinc-900", "zinc-800", "neutral-900", "neutral-800",
    "indigo-900", "indigo-800",   # presets education
    "violet-900", "violet-800",   # presets marketplace sombre futur
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
    """Déduit les tokens CSS depuis design_system. Fallback vers valeurs neutres si absent."""
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

    page_bg    = "gray-50" if not is_dark_sidebar else "gray-100"
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


def generate_layout(
    project_workdir: str,
    project_name: str,
    project_spec: Dict[str, Any],
) -> Dict[str, str]:
    """
    Écrit DashboardShell.tsx et layout.tsx sur disque.
    Retourne {rel_path: content} pour traçabilité.
    Lit project_spec["design_system"] pour les couleurs — aucun LLM requis.
    """
    pages: List[Any] = project_spec.get("pages", [])
    design_system: Dict[str, Any] = project_spec.get("design_system", {}) or {}
    app_name = _app_display_name(project_name)
    nav = _nav_items(pages)
    tokens = _resolve_design(design_system, app_name)

    # Chemins publics (auth_required=False) → injectés dans DashboardShell
    # pour exclure ces routes du wrapper sidebar (visiteurs ne voient pas la sidebar)
    public_paths = [
        _path_of(p) for p in pages
        if not _auth_of(p) and _path_of(p) and not _path_of(p).startswith("/sign-")
    ]
    pub_paths_ts = ", ".join(f'"{p}"' for p in public_paths)

    nav_lines = "\n".join(
        f'  {{ href: "{item["href"]}", label: "{item["label"]}", exact: {str(item["exact"]).lower()} }},'
        for item in nav
    )

    shell_content = (
        _SHELL_TEMPLATE
        .replace("__APP_NAME__",    tokens["brand_name"])
        .replace("__NAV_LINES__",   nav_lines)
        .replace("__SIDEBAR_BG__",  tokens["sidebar_bg"])
        .replace("__PAGE_BG__",     tokens["page_bg"])
        .replace("__BORDER__",      tokens["border"])
        .replace("__BRAND_TEXT__",  tokens["brand_text"])
        .replace("__ACTIVE_CLS__",  tokens["active_cls"])
        .replace("__INACTIVE_CLS__", tokens["inactive_cls"])
        .replace("__PUBLIC_PATHS__", pub_paths_ts)
        .replace("__NAV_PADDING__", tokens["nav_padding"])
        .replace("__TRANSITION__",  tokens["transition"])
    )

    layout_content = _LAYOUT_TEMPLATE.replace("__APP_NAME__", tokens["brand_name"])

    base = pathlib.Path(project_workdir)
    written: Dict[str, str] = {}

    for rel, content in [
        ("app/components/layout/DashboardShell.tsx", shell_content),
        ("app/layout.tsx", layout_content),
    ]:
        abs_path = base / rel
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_text(content, encoding="utf-8")
        written[rel] = content

    return written
