"""
dev_design_system_generator.py — shadcn/ui + CSS Variables (Sprint 4.9B)

Génère les fondations de design pour chaque projet généré :
  1. app/globals.css          — CSS variables HSL (primary depuis design_system)
  2. tailwind.config.js       — format shadcn (classes sémantiques : bg-primary, text-foreground…)
  3. postcss.config.js        — inchangé
  4. components/ui/*.tsx      — copie officielle depuis assets/shadcn/components/ui/
  5. lib/utils.ts             — copie depuis assets/shadcn/lib/utils.ts
  6. components/Empty.tsx     — composant custom (semantic classes)
  7. components/StatCard.tsx  — composant custom (semantic classes)

Tokens Tailwind disponibles après génération :
  bg-primary / text-primary / border-primary / ring-primary
  hover:bg-primary/85  (hover boutons)    hover:bg-primary/10  (fond léger)
  text-muted-foreground / text-foreground / bg-muted / bg-card / bg-background
"""
from __future__ import annotations

import logging
import pathlib
from typing import Dict

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# Table HSL — Tailwind v3 exact values
# ═══════════════════════════════════════════════════════════════════════════════

_TAILWIND_HSL: dict[str, str] = {
    # Blues
    "sky-400":    "199 89% 60%", "sky-500":    "199 89% 48%", "sky-600":    "201 96% 39%",
    "blue-400":   "213 94% 68%", "blue-500":   "217 91% 60%", "blue-600":   "221 83% 53%",
    "blue-700":   "224 76% 48%", "blue-800":   "226 71% 40%",
    # Indigos / Violets
    "indigo-400": "237 74% 72%", "indigo-500": "239 84% 67%", "indigo-600": "243 75% 59%",
    "indigo-700": "245 58% 51%", "indigo-800": "244 55% 41%",
    "violet-400": "263 80% 73%", "violet-500": "258 90% 66%", "violet-600": "262 83% 58%",
    "violet-700": "263 70% 50%",
    "purple-400": "271 76% 73%", "purple-500": "271 91% 65%", "purple-600": "272 81% 56%",
    "purple-700": "272 72% 47%",
    # Pinks / Roses
    "fuchsia-400": "292 80% 72%", "fuchsia-500": "292 84% 61%", "fuchsia-600": "293 69% 49%",
    "pink-400":   "330 81% 70%", "pink-500":   "330 81% 60%", "pink-600":   "333 71% 51%",
    "rose-400":   "351 83% 70%", "rose-500":   "351 83% 61%", "rose-600":   "347 77% 50%",
    # Greens / Teals
    "emerald-400": "152 76% 60%", "emerald-500": "152 76% 40%", "emerald-600": "153 66% 31%",
    "green-400":  "142 69% 58%", "green-500":  "142 71% 45%", "green-600":  "142 71% 36%",
    "green-700":  "142 72% 29%",
    "teal-400":   "174 72% 56%", "teal-500":   "173 80% 40%", "teal-600":   "173 80% 34%",
    "cyan-400":   "187 89% 61%", "cyan-500":   "192 90% 45%", "cyan-600":   "192 90% 37%",
    # Warm
    "lime-500":   "84 81% 44%",  "lime-600":   "85 85% 35%",
    "yellow-500": "48 96% 53%",  "yellow-600": "38 92% 40%",
    "amber-500":  "38 92% 50%",  "amber-600":  "32 95% 44%",
    "orange-500": "25 95% 53%",  "orange-600": "21 90% 48%",
    # Reds
    "red-400":    "0 91% 71%",   "red-500":    "0 84% 60%",   "red-600":    "0 72% 51%",
    # Neutral
    "slate-600":  "215 19% 35%", "slate-700":  "215 25% 27%",
    "gray-600":   "220 9% 46%",  "gray-700":   "215 14% 34%",
    "zinc-600":   "240 6% 35%",  "zinc-700":   "240 5% 26%",
    "stone-600":  "25 5% 45%",   "stone-700":  "28 6% 37%",
    "neutral-600": "0 0% 32%",   "neutral-700": "0 0% 25%",
}

_DEFAULT_PRIMARY_HSL = "221 83% 53%"  # blue-600

# Google Fonts URLs par famille (Inter = système, pas d'import nécessaire)
_FONT_IMPORTS: dict[str, str] = {
    "Playfair Display": (
        "@import url('https://fonts.googleapis.com/css2?"
        "family=Playfair+Display:wght@400;600;700&display=swap');"
    ),
    "DM Sans": (
        "@import url('https://fonts.googleapis.com/css2?"
        "family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600&display=swap');"
    ),
    "Plus Jakarta Sans": (
        "@import url('https://fonts.googleapis.com/css2?"
        "family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');"
    ),
}

_FONT_STACK: dict[str, str] = {
    "Playfair Display": '"Playfair Display", Georgia, serif',
    "DM Sans":          '"DM Sans", system-ui, sans-serif',
    "Plus Jakarta Sans": '"Plus Jakarta Sans", system-ui, sans-serif',
    "Inter":            '"Inter", system-ui, sans-serif',
}


def _primary_hsl(primary_color: str) -> str:
    """Convertit 'indigo-600' → '243 75% 59%'. Fallback sur blue-600."""
    return _TAILWIND_HSL.get(primary_color, _DEFAULT_PRIMARY_HSL)


def _radius_from_density(density: str | None) -> str:
    if density == "compact":
        return "0.25rem"
    if density == "spacious":
        return "0.75rem"
    return "0.5rem"


def _collect_font_imports(font_heading: str, font_body: str) -> str:
    """Construit les @import Google Fonts uniques nécessaires."""
    imports, seen = [], set()
    for font in (font_heading, font_body):
        if font != "Inter" and font in _FONT_IMPORTS and font not in seen:
            imports.append(_FONT_IMPORTS[font])
            seen.add(font)
    return "\n".join(imports)


# ═══════════════════════════════════════════════════════════════════════════════
# globals.css — CSS variables HSL + typographie par preset
# ═══════════════════════════════════════════════════════════════════════════════

def _build_globals_css(design_system: dict) -> str:
    primary      = design_system.get("primary_color", "blue-600")
    density      = design_system.get("density", None)
    font_heading = design_system.get("font_heading", "Inter")
    font_body    = design_system.get("font_body", "Inter")
    p_hsl        = _primary_hsl(primary)
    radius       = _radius_from_density(density)
    font_imports = _collect_font_imports(font_heading, font_body)
    body_stack   = _FONT_STACK.get(font_body, '"Inter", system-ui, sans-serif')
    head_stack   = _FONT_STACK.get(font_heading, '"Inter", system-ui, sans-serif')
    imports_block = f"{font_imports}\n\n" if font_imports else ""

    return f"""\
{imports_block}@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {{
  :root {{
    --background: 0 0% 100%;
    --foreground: 222 84% 5%;

    --card: 0 0% 100%;
    --card-foreground: 222 84% 5%;

    --popover: 0 0% 100%;
    --popover-foreground: 222 84% 5%;

    --primary: {p_hsl};
    --primary-foreground: 0 0% 100%;

    --secondary: 210 40% 96%;
    --secondary-foreground: 222 47% 11%;

    --muted: 210 40% 96%;
    --muted-foreground: 215 16% 47%;

    --accent: 210 40% 96%;
    --accent-foreground: 222 47% 11%;

    --destructive: 0 84% 60%;
    --destructive-foreground: 0 0% 100%;

    --border: 214 32% 91%;
    --input: 214 32% 91%;
    --ring: {p_hsl};

    --radius: {radius};

    --font-heading: {head_stack};
    --font-body:    {body_stack};
  }}

  * {{
    @apply border-border;
  }}
  body {{
    @apply bg-background text-foreground;
    font-family: var(--font-body);
  }}
  h1, h2, h3, h4, h5, h6 {{
    font-family: var(--font-heading);
  }}
}}

@layer utilities {{
  .text-balance {{
    text-wrap: balance;
  }}
}}
"""


# ═══════════════════════════════════════════════════════════════════════════════
# tailwind.config.js — format shadcn (CSS variables)
# ═══════════════════════════════════════════════════════════════════════════════

_TAILWIND_CONFIG = '''\
/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background:  "hsl(var(--background))",
        foreground:  "hsl(var(--foreground))",
        card: {
          DEFAULT:    "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        popover: {
          DEFAULT:    "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        primary: {
          DEFAULT:    "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT:    "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        muted: {
          DEFAULT:    "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT:    "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        destructive: {
          DEFAULT:    "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        border: "hsl(var(--border))",
        input:  "hsl(var(--input))",
        ring:   "hsl(var(--ring))",
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
'''

_POSTCSS_CONFIG = '''\
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
'''

# ═══════════════════════════════════════════════════════════════════════════════
# Composants custom (non-shadcn) — classes sémantiques
# ═══════════════════════════════════════════════════════════════════════════════

_EMPTY_TSX = '''\
import React from "react";

interface EmptyProps {
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export function Empty({ title, description, action, className = "" }: EmptyProps) {
  return (
    <div className={["flex flex-col items-center justify-center py-16 text-center", className].join(" ")}>
      <div className="mb-4 rounded-full bg-muted p-4">
        <svg
          className="h-8 w-8 text-muted-foreground"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={1.5}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0
               01-2.247-2.118L3.75 7.5m8.25 3v6.75m0 0l-3-3m3 3 3-3M3.75 7.5h16.5"
          />
        </svg>
      </div>
      <h3 className="text-sm font-semibold text-foreground">{title}</h3>
      {description && <p className="mt-1 text-sm text-muted-foreground">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
'''

_STAT_CARD_TSX = '''\
import React from "react";

type TrendDirection = "up" | "down" | "flat";

interface StatCardProps {
  label: string;
  value: string | number;
  trend?: string;
  trendDirection?: TrendDirection;
  className?: string;
}

const TREND_CLASSES: Record<TrendDirection, string> = {
  up:   "text-green-600",
  down: "text-destructive",
  flat: "text-muted-foreground",
};

export function StatCard({ label, value, trend, trendDirection = "flat", className = "" }: StatCardProps) {
  return (
    <div className={["bg-card rounded-lg border border-border shadow-sm px-6 py-5", className].join(" ")}>
      <p className="text-sm font-medium text-muted-foreground truncate">{label}</p>
      <p className="mt-1 text-3xl font-bold tracking-tight text-foreground">{value}</p>
      {trend && (
        <p className={["mt-2 flex items-center gap-1 text-sm font-medium", TREND_CLASSES[trendDirection]].join(" ")}>
          {trendDirection === "up" ? "↑" : trendDirection === "down" ? "↓" : "→"}
          {trend}
        </p>
      )}
    </div>
  );
}
'''

# ═══════════════════════════════════════════════════════════════════════════════
# Chemin vers les assets shadcn pré-générés
# ═══════════════════════════════════════════════════════════════════════════════

_ASSETS_DIR = pathlib.Path(__file__).parent.parent.parent.parent / "assets" / "shadcn"


def _copy_shadcn_assets(project_workdir: str) -> Dict[str, str]:
    """
    Copie components/ui/*.tsx et lib/utils.ts depuis assets/shadcn/ vers le projet.
    Retourne {rel_path: content} des fichiers copiés.
    Si assets/shadcn/ est absent → warning non-bloquant, retourne {}.
    """
    if not _ASSETS_DIR.exists():
        logger.warning(
            "[design_sys] assets/shadcn/ introuvable — "
            "exécutez factory-sprint0/scripts/prebuild_shadcn.ps1 puis commitez les fichiers générés. "
            "Les composants shadcn NE seront PAS disponibles dans ce projet."
        )
        return {}

    base = pathlib.Path(project_workdir)
    written: Dict[str, str] = {}

    # components/ui/
    ui_src = _ASSETS_DIR / "components" / "ui"
    if ui_src.exists():
        ui_dst = base / "components" / "ui"
        ui_dst.mkdir(parents=True, exist_ok=True)
        for src_file in ui_src.glob("*.tsx"):
            dst_file = ui_dst / src_file.name
            content = src_file.read_text(encoding="utf-8")
            dst_file.write_text(content, encoding="utf-8")
            rel = f"components/ui/{src_file.name}"
            written[rel] = content
            logger.debug("[design_sys] ✓ %s", rel)
    else:
        logger.warning("[design_sys] assets/shadcn/components/ui/ introuvable")

    # lib/utils.ts
    utils_src = _ASSETS_DIR / "lib" / "utils.ts"
    if utils_src.exists():
        utils_dst = base / "lib" / "utils.ts"
        utils_dst.parent.mkdir(parents=True, exist_ok=True)
        content = utils_src.read_text(encoding="utf-8")
        utils_dst.write_text(content, encoding="utf-8")
        written["lib/utils.ts"] = content
        logger.debug("[design_sys] ✓ lib/utils.ts")

    if written:
        logger.info("[design_sys] %d fichiers shadcn copiés depuis assets/shadcn/", len(written))
    return written


# ═══════════════════════════════════════════════════════════════════════════════
# Point d'entrée public
# ═══════════════════════════════════════════════════════════════════════════════

def generate_design_system(project_workdir: str, design_system: Dict | None = None) -> Dict[str, str]:
    """
    Génère les fondations du design system dans project_workdir.
    Retourne {rel_path: content} de tous les fichiers écrits (pour template_written).
    design_system: dict depuis ProjectSpec (primary_color, density, animation_level…)
    """
    ds = design_system or {}
    base = pathlib.Path(project_workdir)
    written: Dict[str, str] = {}

    def _write(rel_path: str, content: str) -> None:
        abs_path = base / pathlib.Path(rel_path)
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_text(content, encoding="utf-8")
        written[rel_path] = content

    # 1 — globals.css (CSS variables dynamiques)
    _write("app/globals.css", _build_globals_css(ds))

    # 2 — tailwind.config.js (format shadcn)
    _write("tailwind.config.js", _TAILWIND_CONFIG)

    # 3 — postcss.config.js
    _write("postcss.config.js", _POSTCSS_CONFIG)

    # 4 — Composants shadcn officiels (copie depuis assets/shadcn/)
    shadcn_files = _copy_shadcn_assets(project_workdir)
    written.update(shadcn_files)

    # 5 — Composants custom sémantiques
    _write("components/Empty.tsx",    _EMPTY_TSX)
    _write("components/StatCard.tsx", _STAT_CARD_TSX)

    primary = ds.get("primary_color", "blue-600")
    logger.info(
        "[design_sys] %d fichiers générés (primary=%s → HSL %s, shadcn=%d fichiers)",
        len(written), primary, _primary_hsl(primary), len(shadcn_files),
    )
    return written
