"""
agents/core/design_resolver.py
───────────────────────────────
Résolveur déterministe de preset design — 0 token, 0 LLM, 0 regex.

Lit le texte du brief (langage naturel écrit par l'opérateur) et retourne
un dict design_system complet depuis config/design_presets.json.

Algorithme : score = intersection de mots entre le brief et les keywords
de chaque domaine. Le domaine avec le score le plus élevé gagne.
En cas d'égalité → premier domaine par ordre alphabétique.
Aucun match → "default".
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
_DOMAIN_KEYWORDS: dict[str, set[str]] = {
    "editorial": {
        "blog", "article", "post", "publication", "rédaction", "éditorial",
        "news", "journal", "media", "magazine", "editorial", "auteur", "author",
        "chronique", "billet", "contenu", "content",
    },
    "saas_dashboard": {
        "saas", "crm", "admin", "management", "tracker", "workspace",
        "backoffice", "gestion", "kpi", "analytics", "reporting",
        "internal", "intern", "tool", "platform", "dashboard", "tableau",
        "pipeline", "leads", "clients", "équipe", "team",
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


def _load_presets() -> dict:
    if _PRESETS_PATH.exists():
        return json.loads(_PRESETS_PATH.read_text(encoding="utf-8"))
    logger.warning(
        "[design_resolver] %s introuvable — preset 'default' vide utilisé", _PRESETS_PATH
    )
    return {}


def resolve_preset(brief: str) -> dict:
    """
    Résout le preset design depuis le texte du brief.

    Args:
        brief: texte libre décrivant l'application (brief opérateur, pas output LLM)

    Returns:
        dict design_system complet + "preset_name" en metadata.
        Ex : {"preset_name": "editorial", "primary_color": "amber-600", ...}
    """
    # Tokenisation minimale — pas de regex, juste split sur ponctuation courante
    cleaned = brief.lower().replace(",", " ").replace(".", " ").replace(";", " ")
    words = set(cleaned.split())

    presets = _load_presets()

    scores: dict[str, int] = {
        domain: len(words & keywords)
        for domain, keywords in _DOMAIN_KEYWORDS.items()
        if words & keywords
    }

    winner = max(scores, key=lambda d: (scores[d], d)) if scores else "default"
    preset = presets.get(winner) or presets.get("default") or {}

    logger.info(
        "[design_resolver] preset=%s scores=%s",
        winner,
        dict(sorted(scores.items(), key=lambda x: -x[1])[:3]),
    )
    return {"preset_name": winner, **preset}
