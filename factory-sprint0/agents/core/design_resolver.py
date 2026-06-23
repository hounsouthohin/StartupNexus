"""
agents/core/design_resolver.py
───────────────────────────────
Résolveur déterministe de preset design — 0 token, 0 LLM, 0 regex.

Lit le texte du brief (langage naturel écrit par l'opérateur) et retourne
un dict design_system complet depuis config/design_presets.json.

Algorithme (deux passes) :
  1. Score = intersection de mots entre le brief et les keywords de chaque domaine.
     Le domaine avec le score le plus élevé gagne.
     En cas d'égalité → premier domaine par ordre alphabétique.
     Aucun match → "default".
  2. Override couleur : si le brief contient un mot-couleur explicite (ex: "orange"),
     primary_color du preset est remplacé par la couleur correspondante.
     Source de mapping : _TAILWIND_HSL depuis dev_design_system_generator.
"""
from __future__ import annotations

import json
import logging
import pathlib

logger = logging.getLogger(__name__)

_PRESETS_PATH = (
    pathlib.Path(__file__).parent.parent.parent / "config" / "design_presets.json"
)

# Mots-clés par domaine — ensembles Python (set membership, pas de regex)
# saas_* : 4 sous-domaines pour éviter que tout le B2B atterrisse sur blue-700
_DOMAIN_KEYWORDS: dict[str, set[str]] = {
    "editorial": {
        "blog", "article", "post", "publication", "rédaction", "éditorial",
        "news", "journal", "media", "magazine", "editorial", "auteur", "author",
        "chronique", "billet", "contenu", "content",
    },
    "saas_project": {
        "sprint", "board", "kanban", "backlog", "milestone", "roadmap",
        "task", "ticket", "issue", "agile", "scrum", "story", "epic",
        "project", "projet", "tâche",
    },
    "saas_crm": {
        "crm", "leads", "contacts", "sales", "deal", "pipeline", "prospect",
        "client", "customer", "opportunity", "account", "commercial",
    },
    "saas_analytics": {
        "analytics", "kpi", "reporting", "metrics", "rapport", "indicateur",
        "dashboard", "tableau de bord", "statistiques", "stats", "chart",
        "graph", "performance", "insight",
    },
    "saas_dashboard": {
        "saas", "admin", "management", "tracker", "workspace",
        "backoffice", "gestion", "internal", "intern", "tool", "platform",
        "équipe", "team", "hub", "office",
    },
    "marketplace": {
        "marketplace", "boutique", "shop", "vendor", "produit", "catalogue",
        "annonce", "listing", "vente", "sell", "achat", "buy", "commerce",
        "product", "offre", "offer", "store", "seller", "buyer",
    },
    "wellness": {
        "santé", "sport", "fitness", "yoga", "nutrition", "habit", "bien-être",
        "wellness", "health", "meal", "repas", "recette", "recipe", "workout",
        "exercise", "exercice", "régime", "diet", "meditation", "méditation",
    },
    "finance": {
        "finance", "comptabilité", "dépense", "budget", "facture", "paiement",
        "expense", "salary", "salaire", "invoice", "payroll", "accounting",
        "tax", "impôt", "trésorerie", "treasury", "remboursement", "refund",
    },
    "education": {
        "formation", "cours", "quiz", "étudiant", "apprentissage", "knowledge",
        "learn", "training", "lesson", "leçon", "school", "école", "university",
        "student", "teacher", "enseignant", "module", "certification",
    },
    "community": {
        "communauté", "forum", "événement", "réseau", "meetup", "social",
        "event", "member", "membre", "community", "network", "groupe", "group",
        "club", "association", "rencontre", "discussion",
    },
}

# Mapping couleur-mot → clé Tailwind (poids 500 = couleur vive, lisible)
# Utilisé pour override primary_color si le brief contient un mot-couleur explicite.
_COLOR_WORD_TO_TAILWIND: dict[str, str] = {
    "orange":   "orange-500",
    "amber":    "amber-600",
    "yellow":   "yellow-500",
    "red":      "red-600",
    "rose":     "rose-500",
    "pink":     "pink-500",
    "violet":   "violet-600",
    "purple":   "purple-600",
    "indigo":   "indigo-600",
    "blue":     "blue-600",
    "sky":      "sky-500",
    "cyan":     "cyan-500",
    "teal":     "teal-500",
    "green":    "green-600",
    "emerald":  "emerald-500",
    "lime":     "lime-600",
    "slate":    "slate-700",
    "gray":     "gray-600",
    "noir":     "slate-900",
    "bleu":     "blue-600",
    "rouge":    "red-600",
    "vert":     "green-600",
    "jaune":    "yellow-500",
    "violet_fr":"violet-600",  # alias français déjà couvert par "violet"
}


def _load_presets() -> dict:
    if _PRESETS_PATH.exists():
        return json.loads(_PRESETS_PATH.read_text(encoding="utf-8"))
    logger.warning(
        "[design_resolver] %s introuvable — preset 'default' vide utilisé", _PRESETS_PATH
    )
    return {}


def resolve_preset(brief: str) -> dict:
    """
    Résout le preset design depuis le texte du brief (deux passes).

    Passe 1 — domaine : score = intersection mots/keywords → preset gagnant.
    Passe 2 — couleur : si un mot-couleur explicite est trouvé dans le brief,
               override primary_color du preset (intent opérateur > défaut domaine).

    Args:
        brief: texte libre décrivant l'application (brief opérateur, pas output LLM)

    Returns:
        dict design_system complet + "preset_name" en metadata.
        Ex : {"preset_name": "saas_project", "primary_color": "orange-500", ...}
    """
    # Tokenisation minimale — pas de regex, juste split sur ponctuation courante
    cleaned = brief.lower().replace(",", " ").replace(".", " ").replace(";", " ").replace("_", " ")
    words = set(cleaned.split())

    presets = _load_presets()

    # ── Passe 1 : résolution du domaine ──────────────────────────────────────
    scores: dict[str, int] = {
        domain: len(words & keywords)
        for domain, keywords in _DOMAIN_KEYWORDS.items()
        if words & keywords
    }

    winner = max(scores, key=lambda d: (scores[d], d)) if scores else "default"
    preset = dict(presets.get(winner) or presets.get("default") or {})

    logger.info(
        "[design_resolver] preset=%s scores=%s",
        winner,
        dict(sorted(scores.items(), key=lambda x: -x[1])[:3]),
    )

    # ── Passe 2 : override couleur explicite du brief ─────────────────────────
    # Priorité : intent couleur opérateur > couleur par défaut du domaine.
    # Scan dans l'ordre du dict → premier mot-couleur trouvé gagne.
    color_override: str | None = None
    for color_word, tailwind_color in _COLOR_WORD_TO_TAILWIND.items():
        if color_word in words:
            color_override = tailwind_color
            break

    if color_override and color_override != preset.get("primary_color"):
        logger.info(
            "[design_resolver] color override : '%s' → primary_color=%s (était %s)",
            color_word, color_override, preset.get("primary_color"),
        )
        preset["primary_color"] = color_override

    return {"preset_name": winner, **preset}
