"""
dev_shell_enricher.py — Nav Icons Enricher (Phase 4.1)

Lit DESIGN_BRIEF.json (nav_icons) et enrichit DashboardShell.tsx ou TopNavShell.tsx
avec des icônes Lucide devant les labels de navigation.

Position dans dev_graph.py : APRÈS generate_design_brief, AVANT enrich_page_clients.

Garanties :
- TSC guard : si TypeScript échoue après enrichissement → rollback déterministe
- Non bloquant : si DESIGN_BRIEF absent ou TSC fail → shell original intact
- template_written mis à jour in-place si succès → shell protégé contre réécriture LLM
"""
from __future__ import annotations

import logging
import os
import pathlib
import re
import subprocess

logger = logging.getLogger(__name__)

# Icônes Lucide disponibles dans les templates shells (déjà importées via lucide-react)
_LUCIDE_VALID = {
    "LayoutDashboard", "Home", "Settings", "Bell", "Inbox",
    "FileText", "BookOpen", "PenLine", "Newspaper", "ScrollText",
    "CheckSquare", "ListTodo", "ClipboardList", "FolderOpen", "Layers",
    "Users", "UserCircle", "Contact", "UserPlus", "UserCheck",
    "DollarSign", "Receipt", "CreditCard", "Wallet", "TrendingUp",
    "Calendar", "CalendarDays", "Clock", "Timer", "CalendarCheck",
    "Package", "ShoppingBag", "Tag", "Barcode", "ShoppingCart",
    "GraduationCap", "Award", "Trophy", "Star",
    "MessageCircle", "Heart", "ThumbsUp", "Share2", "Globe",
    "Bookmark", "Hash", "FolderTree", "Folders",
    "ChefHat", "Utensils", "Coffee", "Apple",
}

_FALLBACK_ICON = "LayoutDashboard"


def _sanitize_icon(icon: str | None) -> str:
    """Retourne l'icône si valide, sinon un fallback neutre."""
    if icon and isinstance(icon, str) and icon in _LUCIDE_VALID:
        return icon
    return _FALLBACK_ICON


def _shell_path_for(design_system: dict, project_workdir: str) -> tuple[str, str] | None:
    """Retourne (rel_path, abs_path) du shell actif selon layout_type."""
    layout_type = design_system.get("layout_type", "sidebar")
    if layout_type == "topnav":
        rel = "app/components/layout/TopNavShell.tsx"
    else:
        rel = "app/components/layout/DashboardShell.tsx"
    abs_p = os.path.join(project_workdir, rel.replace("/", os.sep))
    return (rel, abs_p) if os.path.exists(abs_p) else None


def _patch_shell_with_icons(shell_content: str, nav_icons: dict[str, str]) -> str | None:
    """
    Injecte les icônes Lucide dans le shell TSX.

    Stratégie :
    1. Ajoute `import { Icon1, Icon2, ... } from "lucide-react"` après les imports existants
    2. Pour chaque NavItem dans NAV/AUTH_NAV/PUBLIC_NAV, remplace `label: "X"` par un
       composant inline — non applicable car NAV est un tableau d'objets JS, pas du JSX.

    Approche réaliste : on remplace le rendu du label dans le JSX.
    Le template génère : `{item.label}`
    On remplace par : un helper qui rend <Icon /> + label via un map icon_href→component.

    Implementation : injection d'un objet NAV_ICONS en tête du composant + rendu conditionnel.
    """
    if not nav_icons:
        return None

    icons_used: set[str] = set()
    icon_map_entries: list[str] = []

    for route, icon in nav_icons.items():
        safe_icon = _sanitize_icon(icon)
        icons_used.add(safe_icon)
        icon_map_entries.append(f'  "{route}": {safe_icon}')

    if not icons_used:
        return None

    icons_import = f'import {{ {", ".join(sorted(icons_used))} }} from "lucide-react"'
    nav_icons_obj = "const NAV_ICONS: Record<string, React.ElementType> = {\n" + ",\n".join(icon_map_entries) + "\n}"

    # ── 1. Ajouter l'import lucide-react (après les imports existants) ────────
    import_block_end = shell_content.rfind("\nimport ")
    if import_block_end == -1:
        return None
    # Trouver la fin de la ligne d'import
    line_end = shell_content.find("\n", import_block_end + 1)
    if line_end == -1:
        line_end = len(shell_content)
    patched = shell_content[:line_end + 1] + icons_import + "\n" + shell_content[line_end + 1:]

    # ── 2. Ajouter l'objet NAV_ICONS après le dernier const NAV/AUTH_NAV ─────
    nav_const_end = patched.rfind("\n]")
    if nav_const_end == -1:
        return None
    line_after_nav = patched.find("\n", nav_const_end + 1)
    if line_after_nav == -1:
        line_after_nav = len(patched)
    patched = patched[:line_after_nav + 1] + "\n" + nav_icons_obj + "\n" + patched[line_after_nav + 1:]

    # ── 3. Remplacer le rendu {item.label} par icône + label ─────────────────
    # Le template utilise `>{item.label}</Link>` — on le remplace par le rendu avec icône
    def _replace_label(m: re.Match) -> str:
        indent = m.group(1)
        return (
            f"{indent}>{{(() => {{"
            f" const Icon = NAV_ICONS[item.href]; "
            f"return Icon ? <><Icon className=\"w-4 h-4 mr-2 inline-block shrink-0\" />{{item.label}}</> : item.label; "
            f"}})()"
            f"}}</Link>"
        )

    patched, n = re.subn(
        r"(\s+)>\s*\n\s*\{item\.label\}\s*\n\s*</Link>",
        _replace_label,
        patched,
    )
    if n == 0:
        return None

    return patched


async def enrich_shell_with_nav_icons(
    design_brief: dict,
    design_system: dict,
    project_workdir: str,
    template_written: dict,
) -> bool:
    """
    Enrichit DashboardShell ou TopNavShell avec les icônes nav du design_brief.

    Retourne True si l'enrichissement a réussi et le shell a été mis à jour.
    """
    nav_icons: dict = design_brief.get("nav_icons") or {}
    if not nav_icons:
        logger.info("[shell_enricher] nav_icons absent du design_brief → skip")
        return False

    shell_paths = _shell_path_for(design_system, project_workdir)
    if not shell_paths:
        logger.warning("[shell_enricher] shell TSX introuvable sur disque → skip")
        return False

    rel_path, abs_path = shell_paths
    try:
        original = pathlib.Path(abs_path).read_text(encoding="utf-8")
    except Exception as e:
        logger.warning("[shell_enricher] lecture shell échouée : %s", e)
        return False

    patched = _patch_shell_with_icons(original, nav_icons)
    if not patched:
        logger.info("[shell_enricher] aucune modification applicable → skip")
        return False

    if patched == original:
        logger.info("[shell_enricher] patch identique à l'original → skip")
        return False

    # ── Écrire le shell patché sur disque ────────────────────────────────────
    try:
        pathlib.Path(abs_path).write_text(patched, encoding="utf-8")
    except Exception as e:
        logger.warning("[shell_enricher] écriture shell échouée : %s", e)
        return False

    # ── TSC guard ────────────────────────────────────────────────────────────
    _env = os.environ.copy()
    _env["CI"] = "true"
    _env.setdefault("DATABASE_URL", "postgresql://user:CHANGEME@localhost:5432/db_placeholder")

    try:
        tsc = subprocess.run(
            "npx tsc --noEmit",
            shell=True, capture_output=True, text=True,
            timeout=120, cwd=project_workdir, env=_env,
        )
    except subprocess.TimeoutExpired:
        logger.warning("[shell_enricher] TSC TIMEOUT → rollback shell")
        pathlib.Path(abs_path).write_text(original, encoding="utf-8")
        return False

    if tsc.returncode != 0:
        err = (tsc.stdout + tsc.stderr)[:300]
        logger.warning("[shell_enricher] TSC FAILED après enrichissement nav_icons → rollback\n%s", err)
        pathlib.Path(abs_path).write_text(original, encoding="utf-8")
        return False

    # ── Succès : mettre à jour template_written (shell protégé) ─────────────
    template_written[rel_path] = patched
    logger.info(
        "[shell_enricher] ✓ %s enrichi avec %d icônes nav | TSC OK",
        rel_path, len(nav_icons),
    )
    return True
