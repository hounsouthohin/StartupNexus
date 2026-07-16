"""
dev_design_compiler.py — Design Compiler central.

SOURCE UNIQUE de traduction du Design Brief (produit par l'agent design, un vocabulaire
FERMÉ : icône / badges / highlights / layout) en morceaux TSX + classes Tailwind concrets
et STATIQUES.

Pourquoi central : au lieu de recopier de la logique de style dans chaque template, tous les
générateurs déterministes (form, hub, futurs) appellent CE module. Conséquences :
  - un nouveau template → il consomme le compiler, zéro style recopié ;
  - une nouvelle dimension de design → on l'ajoute ICI, une fois, pour tous.

Règle d'or : on n'émet JAMAIS de classe Tailwind construite dynamiquement (bg-${x}-100),
sinon le JIT Tailwind la purge au build (bug des badges détail). Toujours des chaînes
complètes et littérales.
"""
from __future__ import annotations

# ── Couleurs de badge → classes Tailwind STATIQUES ────────────────────────────
# Le vocabulaire de couleurs est celui que l'agent design peut choisir (dev_design_brief).
BADGE_COLOR_CLS: dict[str, str] = {
    "green":  "bg-green-100 text-green-700",
    "blue":   "bg-blue-100 text-blue-700",
    "orange": "bg-orange-100 text-orange-700",
    "red":    "bg-red-100 text-red-700",
    "purple": "bg-purple-100 text-purple-700",
    "gray":   "bg-gray-100 text-gray-600",
    "yellow": "bg-yellow-100 text-yellow-700",
    "teal":   "bg-teal-100 text-teal-700",
}
DEFAULT_BADGE_CLS = "bg-gray-100 text-gray-600"

# Layout de card → padding vertical des lignes.
_LAYOUT_ROW_PY = {"compact": "py-2", "hero": "py-4", "standard": "py-4"}


def badge_class(color: str) -> str:
    """« green » → « bg-green-100 text-green-700 » (statique, jamais purgé)."""
    return BADGE_COLOR_CLS.get((color or "").strip().lower(), DEFAULT_BADGE_CLS)


def _entity_brief(design_brief: dict | None, model_name: str) -> dict:
    if not isinstance(design_brief, dict):
        return {}
    return (design_brief.get("entities", {}) or {}).get(model_name, {}) or {}


def compile_entity_decor(
    design_brief: dict | None,
    model_name: str,
    value_labels: dict[str, dict[str, str]] | None = None,
) -> dict:
    """Décorations prêtes à injecter dans les templates, pour un modèle.

    value_labels : {champ: {valeur: libellé}} — libellés lisibles des valeurs d'enum,
    résolus en amont par le générateur (depuis enum_value_labels de l'architect).

    Retourne un dict consommé tel quel par les templates Jinja :
      icon        : nom d'icône lucide ("" si aucun)
      row_py      : "py-2" | "py-4"
      highlights  : set des champs à mettre en évidence (font-medium)
      badge_map   : {champ: {valeur: {"label": str, "cls": str_statique}}}
    """
    brief = _entity_brief(design_brief, model_name)
    value_labels = value_labels or {}

    badge_map: dict[str, dict[str, dict[str, str]]] = {}
    for field, colors in (brief.get("badge_fields", {}) or {}).items():
        if not isinstance(colors, dict):
            continue
        labels = value_labels.get(field, {}) or {}
        badge_map[field] = {
            str(value): {"label": labels.get(value, value), "cls": badge_class(color)}
            for value, color in colors.items()
        }

    layout = (brief.get("list_card_layout", "standard") or "standard").strip().lower()
    return {
        "icon": (brief.get("icon", "") or "").strip(),
        "row_py": _LAYOUT_ROW_PY.get(layout, "py-4"),
        "hero_layout": layout == "hero",
        "highlights": {str(f) for f in (brief.get("highlight_fields", []) or [])},
        "badge_map": badge_map,
    }
