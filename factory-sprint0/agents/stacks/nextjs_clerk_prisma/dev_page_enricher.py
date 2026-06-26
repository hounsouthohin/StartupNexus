"""
dev_page_enricher.py — Page Enricher (Sprint C)

Applique le Design Brief aux page-client.tsx déterministes.

Algorithme :
  1. Identifier les pages-client éligibles dans template_written (list + detail, pas create/edit)
  2. Pour chaque page : 1 appel LLM guidé par l'entité du Design Brief
  3. Écrire tous les fichiers enrichis sur disque
  4. npx tsc --noEmit sur l'ensemble (un seul appel)
  5. TSC OK  → template_written mis à jour (enrichis protégés)
  6. TSC FAIL → restauration déterministe, template_written inchangé

Appelé APRÈS pre_run_commands (npm install + prisma generate déjà exécutés).
"""
from __future__ import annotations

import json
import logging
import os
import pathlib
import subprocess

logger = logging.getLogger(__name__)

# ─── Couleurs badge → classes Tailwind ───────────────────────────────────────

_BADGE_COLOR_CLS: dict[str, str] = {
    "green":  "bg-green-100 text-green-700",
    "blue":   "bg-blue-100 text-blue-700",
    "orange": "bg-orange-100 text-orange-700",
    "red":    "bg-red-100 text-red-700",
    "purple": "bg-purple-100 text-purple-700",
    "gray":   "bg-gray-100 text-gray-600",
    "yellow": "bg-yellow-100 text-yellow-700",
    "teal":   "bg-teal-100 text-teal-700",
}

# ─── Contexte structurel par page (auth, boolean fields, textarea fields) ────

_STRUCTURAL_RULES_SECTION = """\
## CONTEXTE STRUCTUREL DE LA PAGE
- auth_required  : {auth_required}
- page_type      : {page_type}
- boolean_fields : {boolean_fields}
- textarea_fields: {textarea_fields}

## RÈGLES STRUCTURELLES (priorité absolue sur toute règle visuelle)

### [A] Pages publiques (auth_required = false)
Si auth_required est false :
  ❌ Ne jamais importer createXxx, updateXxx, deleteXxx
  ❌ Ne jamais ajouter de formulaire de création ou de modification
  ❌ Ne jamais afficher de bouton "Supprimer" ou "Modifier"
  ❌ Ne jamais appeler useActionState ni useFormState
  ✅ Affichage READ-ONLY uniquement : titres, textes, liens de navigation

### [B] Champs boolean (boolean_fields)
Pour chaque champ dont le nom est dans boolean_fields :
  ❌ Interdit : {{String(item.champ ?? '—')}} — texte brut pour un boolean
  ✅ Remplacer par un badge inline. Exemples :
     "published" :
       item.published
         ? <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">Publié</span>
         : <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-500">Brouillon</span>
     "isPaid" :
       item.isPaid
         ? <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">Payé</span>
         : <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-600">En attente</span>
     Cas général : utiliser le libellé métier du champ (label UI), jamais les valeurs "true"/"false".

### [C] Champs textarea en liste publique
Si auth_required = false ET page_type = list :
  Les champs dans textarea_fields ne doivent PAS apparaître dans les cards de liste.
  Un texte long dans une card publique est une mauvaise UX pour les visiteurs.

"""

# ─── System prompt d'enrichissement ─────────────────────────────────────────

_ENRICHMENT_PROMPT = """\
Tu enrichis visuellement un fichier page-client.tsx Next.js déjà fonctionnel.
Ce fichier compile correctement — ton seul rôle est d'améliorer son apparence visuelle.

## DESIGN BRIEF DE L'ENTITÉ
{entity_brief_json}

## ANIMATION STYLE : {animation_style}

## RÈGLES ABSOLUES — violations = build cassé
1. Conserver EXACTEMENT la signature du composant (props, interface, types TypeScript)
2. Conserver TOUS les handlers (handleDelete, handleSubmit, redirections)
3. Conserver TOUS les imports existants (en ajouter de nouveaux est autorisé)
4. Seuls nouveaux packages autorisés : lucide-react (déjà installé){motion_rule}
5. Tokens Tailwind sémantiques UNIQUEMENT : bg-primary, text-primary, bg-primary/10,
   bg-primary/85, bg-muted, text-muted-foreground, border-border, bg-card,
   text-foreground, text-primary-foreground, bg-destructive, text-destructive
6. INTERDITS : valeurs hex (#...), classes arbitraires (bg-[...]), nouveaux packages npm

## ENRICHISSEMENTS À APPLIQUER

### Icône d'entité
L'import {{ {icon} }} from "lucide-react" est déjà présent dans le fichier.
Placer <{icon} className="w-5 h-5 text-primary inline-block mr-2" /> immédiatement avant le texte du premier h1 ou h2 visible.

### Badges pour badge_fields
Pour chaque champ dans badge_fields, remplacer l'affichage texte brut par un badge coloré.
Exemple — si badge_fields.status = {{"published": "green", "draft": "gray"}} :
  Avant  : {{String(item.status ?? '—')}}
  Après  : {{item.status === 'published' ? <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">Publié</span> : item.status === 'draft' ? <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">Brouillon</span> : <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">{{String(item.status ?? '—')}}</span>}}

### Highlight fields
Pour les champs dans highlight_fields : ajouter className="font-medium" à leur valeur d'affichage.

### Layout card
- list_card_layout="hero"    : dans une liste, agrandir le premier champ texte affiché (text-base font-semibold)
- list_card_layout="compact" : réduire les espacements des lignes (py-2 au lieu de py-4)
- list_card_layout="standard": aucun changement de layout requis{motion_instructions}

## SORTIE
Retourner UNIQUEMENT le code TypeScript complet du fichier, sans bloc markdown, sans commentaire.
"""

_MOTION_RULE = " + framer-motion si animation_style=spring (déjà installé)"

_MOTION_INSTRUCTIONS = """

### Animations (animation_style="spring" uniquement)
Importer : import {{ motion }} from "framer-motion"
Wrapper le contenu principal dans <motion.div initial={{{{ opacity: 0, y: 8 }}}} animate={{{{ opacity: 1, y: 0 }}}} transition={{{{ type: "spring", duration: 0.4 }}}}>
"""


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _should_enrich(path: str) -> bool:
    """Retourne True si le fichier est éligible à l'enrichissement."""
    if not path.endswith("page-client.tsx"):
        return False
    parts = path.replace("\\", "/").split("/")
    # Exclure create et edit — logique métier trop fragile à modifier
    return "new" not in parts and "edit" not in parts


def _build_page_context(path: str, spec_obj, model_contexts: dict) -> dict:
    """Contexte structurel injecté dans le prompt pour chaque page enrichie.

    Retourne un dict avec :
      - auth_required   : bool  — la page est-elle protégée par Clerk ?
      - page_type       : str   — "list" | "detail" | "detail-slug" | …
      - boolean_fields  : list  — champs de type Boolean du modèle (pour badges)
      - textarea_fields : list  — champs textarea (à exclure des cards publiques)
    """
    # Reconstruire le path spec depuis le chemin template_written
    # ex: "app/dashboard/articles/page-client.tsx" → "/dashboard/articles"
    #     "app/articles/[slug]/page-client.tsx"    → "/articles/[slug]"
    norm = path.replace("\\", "/")
    norm = norm.removeprefix("app/").removesuffix("/page-client.tsx").strip("/")
    spec_path = "/" + norm if norm else "/"

    page = next(
        (p for p in (getattr(spec_obj, "pages", []) or [])
         if getattr(p, "path", "") == spec_path),
        None,
    )

    auth_required = getattr(page, "auth_required", True) if page else True
    page_type     = getattr(page, "page_type",     "list") if page else "list"
    model_name    = getattr(page, "model",          None)  if page else None

    boolean_fields:  list[str] = []
    textarea_fields: list[str] = []

    if model_name:
        ctx = model_contexts.get(model_name)
        if ctx:
            boolean_fields  = [f.name for f in ctx.editable_fields if f.base_type == "Boolean"]
            textarea_fields = [f.name for f in ctx.editable_fields if f.input_type == "textarea"]

    return {
        "auth_required":   auth_required,
        "page_type":       page_type,
        "boolean_fields":  boolean_fields,
        "textarea_fields": textarea_fields,
    }


def _build_path_to_model(spec_obj) -> dict[str, str]:
    """Construit {path_prefix_lower: model_name} depuis spec_obj.pages."""
    mapping: dict[str, str] = {}
    for page in getattr(spec_obj, "pages", []) or []:
        model = getattr(page, "model", None)
        path  = getattr(page, "path", "") or ""
        if not model or not path:
            continue
        # Garde uniquement le préfixe statique (avant le premier segment dynamique)
        prefix = path.split("[")[0].rstrip("/").lower()
        if prefix:
            mapping[prefix] = model
    return mapping


def _entity_from_path(path: str, model_contexts: dict, path_to_model: dict | None = None) -> str | None:
    """Détecte le nom d'entité depuis le chemin du page-client.tsx.

    Stratégie 1 (préférentielle) : correspondance directe via spec_obj.pages.
    Stratégie 2 (fallback)        : heuristique kebab avec pluriels anglais.
    """
    norm = path.replace("\\", "/").lower()
    # Strip leading app/ prefix for matching
    norm_stripped = norm.removeprefix("app/")

    # ── Stratégie 1 : correspondance spec_obj.pages ───────────────────────
    if path_to_model:
        for prefix, model_name in path_to_model.items():
            prefix_stripped = prefix.lstrip("/")
            if norm_stripped.startswith(prefix_stripped + "/") or norm_stripped == prefix_stripped + "/page-client.tsx":
                if model_name in model_contexts:
                    return model_name

    # ── Stratégie 2 : heuristique pluriel anglais ─────────────────────────
    for model_name, ctx in model_contexts.items():
        kebab = getattr(ctx, "kebab", model_name.lower())
        candidates = [
            f"/{kebab}s/",
            f"/{kebab}es/",
            # y → ies (category → categories, story → stories)
            f"/{kebab[:-1]}ies/" if kebab.endswith("y") else None,
            f"/{kebab}/",
        ]
        for c in candidates:
            if c and (c in norm or norm.endswith(c.rstrip("/") + "/page-client.tsx")):
                return model_name
    return None


def _build_enrichment_prompt(entity_brief: dict, animation_style: str, page_context: dict | None = None) -> str:
    """Construit le prompt complet : règles structurelles (auth, booleans) + règles visuelles (design brief)."""
    ctx = page_context or {}

    structural = _STRUCTURAL_RULES_SECTION.format(
        auth_required=ctx.get("auth_required", True),
        page_type=ctx.get("page_type", "list"),
        boolean_fields=", ".join(ctx.get("boolean_fields", [])) or "(aucun)",
        textarea_fields=", ".join(ctx.get("textarea_fields", [])) or "(aucun)",
    )

    use_motion = animation_style == "spring"
    visual = _ENRICHMENT_PROMPT.format(
        entity_brief_json=json.dumps(entity_brief, ensure_ascii=False, indent=2),
        animation_style=animation_style,
        icon=entity_brief.get("icon", "Layers"),
        motion_rule=_MOTION_RULE if use_motion else "",
        motion_instructions=_MOTION_INSTRUCTIONS if use_motion else "",
    )

    return structural + visual


# ─── Injection déterministe de l'import Lucide ───────────────────────────────

def _inject_icon_import(code: str, icon: str) -> str:
    """Ajoute `import { Icon } from "lucide-react"` après le dernier import existant.
    No-op si lucide-react est déjà importé."""
    if "lucide-react" in code:
        return code
    idx = code.rfind("\nimport ")
    if idx == -1:
        return code
    line_end = code.find("\n", idx + 1)
    if line_end == -1:
        line_end = len(code)
    return code[:line_end + 1] + f'import {{ {icon} }} from "lucide-react"\n' + code[line_end + 1:]


# ─── LLM enrichissement (1 fichier) ─────────────────────────────────────────

async def _enrich_single(
    original_code: str,
    entity_brief: dict,
    animation_style: str,
    llm,
    page_context: dict | None = None,
) -> str | None:
    """Injecte l'import Lucide déterministiquement, puis appelle le LLM pour le reste."""
    from langchain_core.messages import SystemMessage, HumanMessage

    icon = entity_brief.get("icon", "Layers")
    code_with_import = _inject_icon_import(original_code, icon)

    system = _build_enrichment_prompt(entity_brief, animation_style, page_context)
    human  = f"Fichier à enrichir :\n\n```typescript\n{code_with_import}\n```"

    try:
        response = await llm.ainvoke([
            SystemMessage(content=system),
            HumanMessage(content=human),
        ])
        content = str(response.content or "").strip()
        # Nettoyer les blocs markdown si le LLM les ajoute malgré l'instruction
        if content.startswith("```"):
            lines = content.splitlines()
            content = "\n".join(
                l for l in lines
                if not l.startswith("```")
            ).strip()
        return content if content else code_with_import
    except Exception as _e:
        logger.warning("[page_enricher] LLM enrichissement échoué : %s — retour avec import injecté", _e)
        return code_with_import


# ─── Point d'entrée ──────────────────────────────────────────────────────────

async def enrich_page_clients(
    spec_obj,
    design_brief: dict,
    model_contexts: dict,
    project_workdir: str,
    template_written: dict,
) -> dict:
    """
    Enrichit les page-client.tsx list/detail avec le Design Brief.

    Écrit les fichiers enrichis sur disque, lance TSC une seule fois :
    - TSC OK  → template_written mis à jour in-place (enrichis protégés)
    - TSC FAIL → rollback déterministe, template_written inchangé

    Retourne {path: enriched_content} des fichiers effectivement enrichis.
    """
    from agents.llm_provider import get_chat_llm

    entities      = design_brief.get("entities", {})
    animation_style = design_brief.get("animation_style", "ease")

    if not entities:
        logger.info("[page_enricher] brief vide → skip")
        return {}

    _api_key = os.getenv("OPENAI_API_KEY")
    llm = get_chat_llm(model="gpt-4o-mini", temperature=0.0, api_key=_api_key)

    # ── 1. Identifier les candidats ──────────────────────────────────────────
    candidates: dict[str, dict] = {}  # path → {original, entity_name, entity_brief}
    _path_to_model = _build_path_to_model(spec_obj)

    for path in list(template_written.keys()):
        if not _should_enrich(path):
            continue
        entity_name = _entity_from_path(path, model_contexts, _path_to_model)
        if not entity_name:
            continue
        entity_brief = entities.get(entity_name)
        if not entity_brief:
            continue
        page_ctx = _build_page_context(path, spec_obj, model_contexts)
        candidates[path] = {
            "original":     template_written[path],
            "entity_name":  entity_name,
            "entity_brief": entity_brief,
            "page_context": page_ctx,
        }

    if not candidates:
        logger.info("[page_enricher] aucun candidat éligible → skip")
        return {}

    logger.info("[page_enricher] %d fichier(s) candidat(s) à l'enrichissement", len(candidates))

    # ── 2. Enrichir chaque fichier (LLM séquentiel) ─────────────────────────
    enriched: dict[str, str] = {}  # path → enriched_content

    for path, info in candidates.items():
        enriched_code = await _enrich_single(
            info["original"],
            info["entity_brief"],
            animation_style,
            llm,
            page_context=info.get("page_context"),
        )
        if enriched_code and enriched_code != info["original"]:
            enriched[path] = enriched_code
            logger.debug("[page_enricher] enrichi : %s", path)
        else:
            logger.debug("[page_enricher] aucun changement : %s", path)

    if not enriched:
        logger.info("[page_enricher] aucun enrichissement produit → skip TSC")
        return {}

    # ── 3. Écrire les fichiers enrichis sur disque ───────────────────────────
    base = pathlib.Path(project_workdir)
    for path, content in enriched.items():
        abs_p = base / path.replace("/", os.sep)
        try:
            abs_p.write_text(content, encoding="utf-8")
        except Exception as _we:
            logger.warning("[page_enricher] écriture %s échouée : %s", path, _we)
            enriched.pop(path, None)

    # ── 4. TSC check — un seul appel sur tout le projet ─────────────────────
    _env = os.environ.copy()
    _env["CI"] = "true"
    _env.setdefault("DATABASE_URL", "postgresql://user:CHANGEME@localhost:5432/db_placeholder")

    logger.info("[page_enricher] TSC check en cours (%d fichiers enrichis)…", len(enriched))
    try:
        tsc = subprocess.run(
            "npx tsc --noEmit",
            shell=True,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=project_workdir,
            env=_env,
        )
    except subprocess.TimeoutExpired:
        logger.warning("[page_enricher] TSC TIMEOUT → rollback")
        tsc = None

    # ── 5a. TSC OK → protéger les fichiers enrichis ─────────────────────────
    if tsc is not None and tsc.returncode == 0:
        for path, content in enriched.items():
            template_written[path] = content  # mis à jour in-place → protégé
        logger.info("[page_enricher] ✓ TSC OK — %d fichier(s) enrichis et protégés", len(enriched))
        return enriched

    # ── 5b. TSC FAIL → restauration déterministe ────────────────────────────
    err_excerpt = ""
    if tsc is not None:
        _lines = (tsc.stdout + tsc.stderr).splitlines()
        err_excerpt = "\n".join(_lines[:8])

    logger.warning(
        "[page_enricher] TSC FAILED — rollback vers déterministe.\n%s",
        err_excerpt,
    )

    for path, info in candidates.items():
        if path not in enriched:
            continue
        abs_p = base / path.replace("/", os.sep)
        try:
            abs_p.write_text(info["original"], encoding="utf-8")
        except Exception as _re:
            logger.error("[page_enricher] restauration %s échouée : %s", path, _re)

    # template_written inchangé (déterministe toujours en place)
    return {}
