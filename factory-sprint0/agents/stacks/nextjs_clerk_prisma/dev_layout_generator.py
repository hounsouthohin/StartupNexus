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
  const isAuthPage = pathname.startsWith("/sign-in") || pathname.startsWith("/sign-up")

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
                  "flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors duration-150",
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
    L'architect n'a pas à setter auth: true explicitement.
    """
    path = _path_of(page)
    if path.startswith("/dashboard"):
        return True
    if isinstance(page, dict):
        return page.get("auth") is True
    return False


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
}


def _resolve_design(design_system: Dict[str, Any], app_name: str) -> Dict[str, str]:
    """Déduit les tokens CSS depuis design_system. Fallback vers valeurs neutres si absent."""
    primary   = design_system.get("primary_color", "blue-700")
    sidebar   = design_system.get("sidebar_bg", "white")
    brand     = design_system.get("brand_name", app_name) or app_name

    is_dark_sidebar = sidebar in _DARK_SIDEBAR_BGS

    if is_dark_sidebar:
        brand_text  = "white"
        active_cls  = f"bg-{primary.replace('-700', '-600').replace('-600', '-500')} text-white"
        inactive_cls = "text-slate-300 hover:bg-slate-700 hover:text-white"
        border       = "slate-700"
    else:
        brand_text  = "gray-900"
        primary_base = primary.split("-")[0] if "-" in primary else "blue"
        shade        = primary.split("-")[1] if "-" in primary else "700"
        light_shade  = "50"
        active_cls   = f"bg-{primary_base}-{light_shade} text-{primary_base}-{shade}"
        inactive_cls = "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
        border       = "gray-200"

    page_bg = "gray-50" if not is_dark_sidebar else "gray-100"

    return {
        "sidebar_bg":  sidebar,
        "brand_text":  brand_text,
        "active_cls":  active_cls,
        "inactive_cls": inactive_cls,
        "border":      border,
        "page_bg":     page_bg,
        "brand_name":  brand,
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

    nav_lines = "\n".join(
        f'  {{ href: "{item["href"]}", label: "{item["label"]}", exact: {str(item["exact"]).lower()} }},'
        for item in nav
    )

    shell_content = (
        _SHELL_TEMPLATE
        .replace("__APP_NAME__",   tokens["brand_name"])
        .replace("__NAV_LINES__",  nav_lines)
        .replace("__SIDEBAR_BG__", tokens["sidebar_bg"])
        .replace("__PAGE_BG__",    tokens["page_bg"])
        .replace("__BORDER__",     tokens["border"])
        .replace("__BRAND_TEXT__", tokens["brand_text"])
        .replace("__ACTIVE_CLS__", tokens["active_cls"])
        .replace("__INACTIVE_CLS__", tokens["inactive_cls"])
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
