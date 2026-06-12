"""
Journey Validator — Sprint 4.5
Validateur déterministe (0 tokens) qui vérifie que chaque user_flow extrait par l'Architect
a une route ou une page correspondante dans les fichiers générés.

user_flow format attendu (flexible) :
  "L'utilisateur crée une tâche → POST /api/tasks"
  "L'utilisateur voit son dashboard → /dashboard"
  "L'utilisateur supprime une tâche → DELETE /api/tasks/[id]"

Algorithme :
  1. Extraire le segment de chemin de chaque flow (après →, ou premier /...)
  2. Normaliser en chemin de fichier attendu (app/api/.../route.ts ou app/.../page.tsx)
  3. Vérifier présence dans combined_files (exact ou fuzzy par segments)
  4. Retourner user_flows_coverage + liste covered/uncovered
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Seuil "app utile" : 60% des user_flows couverts par des fichiers générés
USER_FLOWS_USEFUL_THRESHOLD = 0.60


def _llm_judge_enabled() -> bool:
    return (
        os.getenv("JOURNEY_LLM_FALLBACK", "0") == "1"
        and bool(os.getenv("OPENAI_API_KEY"))
    )


def _llm_judge_flow_coverage(flow: str, file_keys: list[str]) -> tuple[bool | None, str]:
    """
    Fallback sémantique (optionnel) pour flows non résolus déterministiquement.
    Retourne (covered|None, reason). None = impossible de juger.
    """
    if not _llm_judge_enabled():
        return None, "llm_disabled"

    try:
        from pydantic import BaseModel
        from langchain_openai import ChatOpenAI

        class CoverageCheck(BaseModel):
            covered: bool
            reason: str

        model_name = os.getenv("JOURNEY_LLM_MODEL", "gpt-4o-mini")
        llm = ChatOpenAI(model=model_name, temperature=0).with_structured_output(CoverageCheck)
        file_list = "\n".join(f"- {k}" for k in file_keys[:120])
        prompt = (
            "Tu es un juge strict de couverture de flow utilisateur.\n"
            "Réponds uniquement sur la base des fichiers listés.\n"
            f"Flow: {flow}\n\n"
            "Fichiers générés:\n"
            f"{file_list}\n\n"
            "Covered=true seulement si une route/page implémentant clairement ce flow existe."
        )
        resp = llm.invoke(prompt)
        return bool(resp.covered), str(resp.reason)[:220]
    except Exception as e:
        return None, f"llm_error:{str(e)[:120]}"


def _extract_path_from_flow(flow: str) -> str | None:
    """
    Extrait le chemin URL d'un user_flow string.
    Gère : "description → /path", "description -> /path", "description > /path", "/path seul"
    """
    # Cherche après → ou -> ou >
    arrow_split = re.split(r"→|->|>", flow, maxsplit=1)
    search_in = arrow_split[-1].strip() if len(arrow_split) > 1 else flow.strip()

    # Supprime le verbe HTTP si présent (POST, GET, PUT, DELETE, PATCH)
    search_in = re.sub(r"^\s*(GET|POST|PUT|PATCH|DELETE)\s+", "", search_in, flags=re.IGNORECASE).strip()

    # Extrait le premier segment /...
    match = re.search(r"/[\w/\[\].-]+", search_in)
    return match.group(0) if match else None


def _path_to_candidates(path: str) -> list[str]:
    """
    Convertit un chemin URL en liste de fichiers candidats.
      /api/tasks        → app/api/tasks/route.ts
      /api/tasks/[id]   → app/api/tasks/[id]/route.ts
      /dashboard        → app/dashboard/page.tsx
      /tasks/[id]       → app/tasks/[id]/page.tsx
    """
    normalized = path.strip("/")
    if not normalized:
        return ["app/page.tsx"]

    if normalized.startswith("api/") or "/api/" in normalized:
        return [f"app/{normalized}/route.ts"]
    else:
        return [
            f"app/{normalized}/page.tsx",
            f"app/{normalized}.tsx",
        ]


def _file_path_to_route(file_path: str) -> str | None:
    """
    Convertit un chemin de fichier Next.js App Router en route URL.
    Ne retourne rien pour les non-pages (route.ts, layout.tsx, etc.).
    Route groups (x) et parallel routes @slot sont ignorés.
    """
    p = Path(file_path)
    if p.name not in ("page.tsx", "page.ts", "page.jsx", "page.js"):
        return None

    parts = list(p.parent.parts)
    while parts and parts[0] in ("app", "src"):
        parts.pop(0)

    route_parts: list[str] = []
    for part in parts:
        if re.match(r"^\(.*\)$", part):       # route group (auth) → ignoré
            continue
        if part.startswith("@"):               # parallel route slot → ignoré
            continue
        if re.match(r"^\[\.\.\..*\]$", part):  # catch-all [...slug]
            route_parts.append("*")
        elif re.match(r"^\[.*\]$", part):      # dynamic segment [id] → :id
            route_parts.append(":" + part[1:-1])
        else:
            route_parts.append(part)

    return "/" + "/".join(route_parts) if route_parts else "/"


def build_route_table(file_keys: "set[str] | list[str]") -> dict[str, str]:
    """
    Construit {route_url: file_path} depuis la liste des fichiers générés.
    Exporté pour spec_validator.py.
    """
    table: dict[str, str] = {}
    for f in file_keys:
        route = _file_path_to_route(f)
        if route:
            table[route] = f
    return table


def _spec_path_to_pattern(spec_path: str) -> re.Pattern:
    """
    Convertit un chemin spec (/users/[id] ou /users/:id) en regex
    matchant la route table (qui stocke :param).
    """
    parts = spec_path.strip("/").split("/")
    regex_parts: list[str] = []
    for p in parts:
        if (p.startswith("[") and p.endswith("]")) or p.startswith(":") or p == "*":
            regex_parts.append("[^/]+")
        else:
            regex_parts.append(re.escape(p.lower()))
    if not regex_parts:
        return re.compile(r"^/$")
    return re.compile("^/" + "/".join(regex_parts) + "$", re.IGNORECASE)


def _is_covered(path: str, combined_files: dict, _route_table: "dict | None" = None) -> bool:
    """
    Vérifie si un chemin URL est couvert dans les fichiers générés.
    Stratégie :
      1. Exact match sur les candidats directs (page.tsx, route.ts)
      2. Route table déterministe — remplace le fuzzy matching par segments
         (évite les faux positifs type /companies → app/contacts/companies/page.tsx)
    _route_table : pré-construit par validate_user_flows pour ne pas reconstruire à chaque flow.
    """
    file_keys = set(combined_files.keys())
    candidates = _path_to_candidates(path)

    for c in candidates:
        if c in file_keys:
            return True

    # API routes : route.ts introuvable → fallback Server Actions (Option A).
    # Option A place les mutations dans app/{list_page}/actions.ts (pas app/api/).
    # Le chemin du list_page peut différer du segment API (ex: /api/posts → app/blog/actions.ts).
    # Stratégie :
    #   1. Match direct par segment (app/{segment}/actions.ts)
    #   2. Match par contenu : scanner tous les actions.ts pour trouver createXxx/deleteXxx
    #      correspondant au modèle inféré depuis le segment API ("posts" → "Post")
    normalized = path.strip("/")
    if normalized.startswith("api/") or "/api/" in normalized:
        rest = normalized[4:] if normalized.startswith("api/") else normalized
        segs = rest.split("/")
        first_static = next((s for s in segs if s and not s.startswith("[")), None)
        if first_static:
            # 1. Match direct
            if f"app/{first_static}/actions.ts" in file_keys:
                return True
            # 2. Match par contenu — "posts" → model "Post", cherche createPost/deletePost
            model_keyword = first_static.rstrip("s").capitalize()
            for af in file_keys:
                if not af.endswith("/actions.ts"):
                    continue
                content = combined_files.get(af, "")
                if f"create{model_keyword}" in content or f"delete{model_keyword}" in content:
                    return True
        return False

    # Route table déterministe — segment exact, pas de substring matching
    table = _route_table if _route_table is not None else build_route_table(file_keys)
    if not table:
        return False

    pattern = _spec_path_to_pattern(path)
    return any(pattern.match(route) for route in table)


def validate_author_flows(spec, user_flows: list) -> Dict[str, Any]:
    """
    Vérifie que les pages liste authentifiées (auth=True, page_type="list")
    ont un user_flow correspondant dans la spec.
    Utile pour détecter les oublis de flows auteur (ex: /dashboard/posts sans flow).

    Args:
        spec : ProjectSpec (Pydantic) ou dict avec clé "pages"
        user_flows : liste de strings (même format que validate_user_flows)

    Returns:
        {
          "has_auth_list_pages": bool,
          "author_flows_total": int,       # nb de pages liste auth
          "author_flows_covered": int,     # nb de pages liste auth avec flow
          "missing_author_flows": [str],   # chemins sans flow
        }
    """
    if isinstance(spec, dict):
        pages = spec.get("pages", [])
    else:
        pages = list(getattr(spec, "pages", None) or [])

    # Collecte les pages liste authentifiées
    auth_list_paths: list[str] = []
    for page in pages:
        path = _path_of(page)
        if not path:
            continue
        if not _auth_of(page):
            continue
        ptype = page.get("page_type") if isinstance(page, dict) else getattr(page, "page_type", "")
        if ptype == "list":
            auth_list_paths.append(path)

    if not auth_list_paths:
        return {
            "has_auth_list_pages": False,
            "author_flows_total": 0,
            "author_flows_covered": 0,
            "missing_author_flows": [],
        }

    # Extrait les chemins couverts par les user_flows
    flow_paths = {_extract_path_from_flow(str(f)) for f in user_flows if f}
    flow_paths.discard(None)

    missing = [p for p in auth_list_paths if p not in flow_paths]
    covered = len(auth_list_paths) - len(missing)

    logger.info(
        "[journey_validator] author_flows: %d/%d pages liste auth couvertes (missing: %s)",
        covered, len(auth_list_paths), missing or "aucune",
    )

    return {
        "has_auth_list_pages": True,
        "author_flows_total": len(auth_list_paths),
        "author_flows_covered": covered,
        "missing_author_flows": missing,
    }


def validate_user_flows(user_flows: list, combined_files: dict) -> Dict[str, Any]:
    """
    Point d'entrée principal.

    Args:
        user_flows    : liste de strings décrivant les flux utilisateur
        combined_files: dict {filepath: content} des fichiers générés

    Returns:
        {
          "user_flows_total": int,
          "user_flows_covered": int,
          "user_flows_coverage": float,     # 0.0 → 1.0
          "is_useful_app": bool,            # coverage >= USER_FLOWS_USEFUL_THRESHOLD
          "covered": [str, ...],
          "uncovered": [str, ...],
          "unresolvable": [str, ...],       # flows sans chemin extractible
        }
    """
    if not user_flows:
        logger.info("[journey_validator] Aucun user_flow fourni — skip")
        return {
            "user_flows_total": 0,
            "user_flows_covered": 0,
            "user_flows_coverage": 1.0,
            "is_useful_app": True,
            "covered": [],
            "uncovered": [],
            "unresolvable": [],
        }

    covered = []
    uncovered = []
    unresolvable = []
    llm_promoted = []
    llm_checked = 0

    # Pré-construit une seule fois pour tous les flows (R7 — route table déterministe)
    _route_table = build_route_table(set(combined_files.keys()))

    for flow in user_flows:
        path = _extract_path_from_flow(str(flow))
        if not path:
            unresolvable.append(flow)
            logger.debug(f"[journey_validator] Pas de chemin extractible : '{flow}'")
            continue

        if _is_covered(path, combined_files, _route_table=_route_table):
            covered.append(flow)
            logger.debug(f"[journey_validator] ✓ '{flow}' → {path}")
        else:
            uncovered.append(flow)
            logger.debug(f"[journey_validator] ✗ '{flow}' → {path} (absent)")

    # Fallback LLM uniquement pour flows non résolus déterministiquement.
    # Il n'est activé que par env var (JOURNEY_LLM_FALLBACK=1).
    if _llm_judge_enabled() and (uncovered or unresolvable):
        unresolved = list(uncovered) + list(unresolvable)
        file_keys = list(combined_files.keys())
        for flow in unresolved:
            llm_checked += 1
            judged, reason = _llm_judge_flow_coverage(str(flow), file_keys)
            if judged is True:
                if flow in uncovered:
                    uncovered.remove(flow)
                if flow in unresolvable:
                    unresolvable.remove(flow)
                covered.append(flow)
                llm_promoted.append({"flow": flow, "reason": reason})
                logger.info(f"[journey_validator][llm] promoted flow='{flow}' reason='{reason}'")
            elif judged is False:
                logger.debug(f"[journey_validator][llm] not covered flow='{flow}' reason='{reason}'")
            else:
                logger.debug(f"[journey_validator][llm] skipped flow='{flow}' reason='{reason}'")

    # Dénominateur = total flows (unresolvable comptent comme non-couverts).
    # Utiliser resolvable_total seulement gonflait le ratio : 2 couverts / 2 résolvables = 1.0
    # alors que 3 flows sur 5 étaient non-résolvables (et donc non-vérifiés).
    total_flows = len(user_flows)
    coverage = len(covered) / total_flows if total_flows > 0 else 1.0
    is_useful = coverage >= USER_FLOWS_USEFUL_THRESHOLD

    logger.info(
        f"[journey_validator] {len(covered)}/{total_flows} flows couverts "
        f"({coverage:.0%}) — is_useful_app={is_useful} "
        f"(seuil={USER_FLOWS_USEFUL_THRESHOLD:.0%}, unresolvable={len(unresolvable)})"
    )
    if uncovered:
        logger.warning(f"[journey_validator] Flows non couverts : {uncovered}")

    return {
        "user_flows_total": len(user_flows),
        "user_flows_covered": len(covered),
        "user_flows_coverage": round(coverage, 3),
        "is_useful_app": is_useful,
        "covered": covered,
        "uncovered": uncovered,
        "unresolvable": unresolvable,
        "llm_checked": llm_checked,
        "llm_promoted": llm_promoted,
    }
