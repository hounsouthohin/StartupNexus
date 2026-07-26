"""
dev_design_brief.py — Design Brief Generator (Sprint B)

1 appel LLM → JSON de décisions visuelles par entité pour toute l'app.
Placé APRÈS pre_run_commands (npm install + prisma generate) dans dev_graph.py.

Input  : ProjectSpec + enriched_spec.field_annotations + design_system
Output : dict brief + DESIGN_BRIEF.json écrit sur disque
"""
from __future__ import annotations

import json
import logging
import os
import pathlib

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
Tu es un moteur de décisions visuelles UI. Tu reçois la spec d'une application Next.js
et tu produis un JSON compact de décisions visuelles concrètes.

## CE QUE TU PRODUIS

### entities
Pour chaque modèle Prisma reçu, décide :

**icon** : nom d'icône Lucide qui représente ce modèle sémantiquement.
Référence par domaine :
- Articles/posts/contenu : FileText, Newspaper, BookOpen, PenLine, ScrollText
- Recettes/food/santé : ChefHat, Utensils, Coffee, Apple, Salad
- Tâches/todo/projets : CheckSquare, ListTodo, ClipboardList, FolderOpen, Layers
- Contacts/users : Users, UserCircle, Contact, UserPlus, UserCheck
- Finances/paiements : DollarSign, Receipt, CreditCard, Wallet, TrendingUp
- Événements/dates : Calendar, CalendarDays, Clock, Timer, CalendarCheck
- Produits/stock/boutique : Package, ShoppingBag, Tag, Barcode, ShoppingCart
- Cours/formations : GraduationCap, BookOpen, Award, Trophy, Star
- Communauté/social : MessageCircle, Heart, ThumbsUp, Share2, Globe
- Catégories/tags/labels : Tag, Bookmark, Hash, FolderTree, Folders
- Générique/navigation : LayoutDashboard, Home, Settings, Bell, Inbox

**badge_fields** : champs méritant un badge coloré.
S'applique UNIQUEMENT si field_annotations contient "status-enum" ou "priority-enum".
Format : {"fieldName": {"valeur1": "green", "valeur2": "orange", "valeur3": "red"}}
Couleurs disponibles : "green", "blue", "orange", "red", "purple", "gray", "yellow", "teal"
Conventions : published/active/done/completed → "green" | draft/pending/todo → "gray" | error/cancelled/rejected → "red" | in_progress/review → "orange" | high/urgent → "red" | low → "green" | medium → "orange"
Si aucun champ status-enum ou priority-enum → badge_fields: {}

**highlight_fields** : max 3 champs à afficher en évidence dans les cards/listes.
Choisir les champs les plus utiles au premier coup d'oeil (durée, prix, statut, date, score).
S'appuyer sur field_annotations : "currency", "date", "status-enum", "priority-enum" sont prioritaires.
Exclure absolument : id, userId, authorId, createdAt, updatedAt, slug, xxxId (FKs).
Si moins de 3 champs pertinents, laisser la liste courte.

**list_card_layout** : style visuel des listes.
- "hero"     : titre proéminent, pour contenu riche (articles, recettes, produits, événements)
- "compact"  : lignes denses, pour données opérationnelles (tâches, factures, contacts, logs)
- "standard" : card équilibrée (défaut pour tout le reste)

### nav_icons
Icône Lucide pour chaque route auth fournie dans pages_auth.
Couvrir TOUTES les routes reçues sans en inventer de nouvelles.

### animation_style
Déduit de design_system.animation_level :
- "enhanced" → "spring"
- "standard" → "ease"
- "none"     → "none"

## FORMAT — JSON uniquement, sans texte autour

Exemple pour un gestionnaire de recettes (wellness) :
{
  "entities": {
    "Recipe": {
      "icon": "ChefHat",
      "badge_fields": {
        "difficulty": {"easy": "green", "medium": "orange", "hard": "red"}
      },
      "highlight_fields": ["cookTime", "servings", "difficulty"],
      "list_card_layout": "hero"
    },
    "Category": {
      "icon": "Tag",
      "badge_fields": {},
      "highlight_fields": ["name"],
      "list_card_layout": "compact"
    }
  },
  "nav_icons": {
    "/dashboard": "LayoutDashboard",
    "/dashboard/recipes": "ChefHat",
    "/dashboard/categories": "Tag"
  },
  "animation_style": "spring"
}
"""


async def generate_design_brief(
    spec_obj,
    enriched_spec,
    design_system: dict,
    project_workdir: str,
) -> dict:
    """
    Génère DESIGN_BRIEF.json depuis ProjectSpec + enriched_spec + design_system.
    Retourne le dict brief (vide si échec LLM — non bloquant).
    """
    from agents.llm_provider import get_chat_llm
    from langchain_core.messages import SystemMessage, HumanMessage

    models = getattr(spec_obj, "models", []) or []
    pages  = getattr(spec_obj, "pages",  []) or []

    if not models:
        logger.warning("[design_brief] aucun modèle → skip")
        return {}

    # Routes auth pour nav_icons (sans segments dynamiques ni create/edit)
    pages_auth = [
        p.path for p in pages
        if getattr(p, "auth_required", True)
        and not any(seg in p.path for seg in ("[", "/new", "/edit", "/sign-"))
    ]

    # field_annotations depuis enriched_spec — source de vérité pour badges/highlights
    field_annotations: dict = {}
    if enriched_spec is not None:
        try:
            fa = getattr(enriched_spec, "field_annotations", {}) or {}
            for k, v in fa.items():
                field_annotations[k] = v.model_dump() if hasattr(v, "model_dump") else dict(v)
        except Exception as _fa_err:
            logger.debug("[design_brief] field_annotations parse : %s", _fa_err)

    context = {
        "description":       getattr(spec_obj, "description", "").strip(),
        "models":            [m.name for m in models],
        "field_annotations": field_annotations,
        "design_system":     {k: v for k, v in design_system.items() if k in (
            "animation_level", "list_style", "density", "preset_name"
        )},
        "pages_auth": pages_auth,
    }

    _api_key = os.getenv("OPENAI_API_KEY")
    try:
        llm = get_chat_llm(
            model="gpt-4o-mini",
            temperature=0.0,
            api_key=_api_key,
        ).bind(response_format={"type": "json_object"})

        messages = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=json.dumps(context, ensure_ascii=False)),
        ]
        response = await llm.ainvoke(messages)
        _usage = getattr(response, "usage_metadata", {}) or {}
        logger.info(
            "[design_brief] tokens — input=%s output=%s total=%s",
            _usage.get("input_tokens", "?"),
            _usage.get("output_tokens", "?"),
            _usage.get("total_tokens", "?"),
        )
        brief: dict = json.loads(response.content)
    except json.JSONDecodeError as _je:
        logger.error("[design_brief] réponse non-JSON : %s", _je)
        return {}
    except Exception as _e:
        logger.error("[design_brief] LLM FAILED : %s", _e)
        return {}

    if not isinstance(brief, dict):
        logger.warning("[design_brief] format inattendu → brief vide")
        return {}

    # Validation minimale : entities doit être un dict
    if not isinstance(brief.get("entities"), dict):
        brief["entities"] = {}

    # ── Filtre déterministe badge_fields ─────────────────────────────────────
    # Le LLM hallucine des badge_fields sur des champs Boolean ou inexistants →
    # comparaison `boolean === "string"` → TS2367 dans Page Enricher → TSC fail.
    _model_field_types: dict[str, dict[str, str]] = {}
    for _m in models:
        _model_field_types[_m.name] = {
            _f.name: _f.type.rstrip("?").rstrip("[]")
            for _f in getattr(_m, "fields", [])
        }
    _spec_enums: dict = getattr(spec_obj, "enums", None) or {}
    for _ent_name, _ent in brief.get("entities", {}).items():
        _ftypes = _model_field_types.get(_ent_name, {})
        # Filtre badge_fields : Boolean et champs inexistants → TS2367 / TS2339 dans Page Enricher
        if isinstance(_ent.get("badge_fields"), dict):
            for _fname in [f for f in list(_ent["badge_fields"]) if _ftypes.get(f, "MISSING") in ("Boolean", "MISSING")]:
                del _ent["badge_fields"][_fname]
                logger.debug("[design_brief] badge_field '%s.%s' retiré (Boolean/inexistant)", _ent_name, _fname)
            # Filtre des VALEURS : le LLM invente des états génériques (pending/rejected) au lieu
            # des vraies valeurs de l'enum → `status === 'pending'` sur ReservationStatus = TS2367.
            # On ne garde que les valeurs réellement présentes dans l'enum Prisma du champ.
            for _fname, _vmap in list(_ent["badge_fields"].items()):
                _enum_name = _ftypes.get(_fname, "")
                _real_vals = set(_spec_enums.get(_enum_name, []) or [])
                if _real_vals and isinstance(_vmap, dict):
                    _cleaned = {v: c for v, c in _vmap.items() if v in _real_vals}
                    if _cleaned != _vmap:
                        logger.debug("[design_brief] badge_field '%s.%s' : valeurs hors-enum retirées %s",
                                     _ent_name, _fname, set(_vmap) - _real_vals)
                    if _cleaned:
                        _ent["badge_fields"][_fname] = _cleaned
                    else:
                        del _ent["badge_fields"][_fname]
        # Filtre highlight_fields : champs inexistants → Page Enricher génère item.field → TS2339
        if isinstance(_ent.get("highlight_fields"), list):
            _before = _ent["highlight_fields"]
            _ent["highlight_fields"] = [f for f in _before if f in _ftypes]
            for _hf in _before:
                if _hf not in _ftypes:
                    logger.debug("[design_brief] highlight_field '%s.%s' retiré (inexistant)", _ent_name, _hf)

    # Écrire DESIGN_BRIEF.json sur disque — lu par le LLM executor via read_file
    try:
        brief_path = pathlib.Path(project_workdir) / "DESIGN_BRIEF.json"
        brief_path.write_text(json.dumps(brief, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as _we:
        logger.warning("[design_brief] écriture fichier échouée : %s", _we)

    entity_count = len(brief.get("entities", {}))
    anim         = brief.get("animation_style", "?")
    logger.info("[design_brief] ✓ %d entités | animation_style=%s | nav_icons=%d",
                entity_count, anim, len(brief.get("nav_icons", {})))
    return brief
