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
import re
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Seuil "app utile" : 60% des user_flows couverts par des fichiers générés
USER_FLOWS_USEFUL_THRESHOLD = 0.60


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


def _is_covered(path: str, combined_files: dict) -> bool:
    """
    Vérifie si un chemin URL est couvert dans les fichiers générés.
    Stratégie : exact d'abord, puis fuzzy par segments non-vides.
    """
    candidates = _path_to_candidates(path)
    file_keys = set(combined_files.keys())

    # Match exact
    for c in candidates:
        if c in file_keys:
            return True

    # Match fuzzy : tous les segments significatifs du path doivent apparaître dans le nom de fichier
    segments = [s for s in path.strip("/").split("/") if s and s not in ("api",) and not s.startswith("[")]
    if not segments:
        return False

    for f in file_keys:
        if all(seg.lower() in f.lower() for seg in segments):
            return True

    return False


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

    for flow in user_flows:
        path = _extract_path_from_flow(str(flow))
        if not path:
            unresolvable.append(flow)
            logger.debug(f"[journey_validator] Pas de chemin extractible : '{flow}'")
            continue

        if _is_covered(path, combined_files):
            covered.append(flow)
            logger.debug(f"[journey_validator] ✓ '{flow}' → {path}")
        else:
            uncovered.append(flow)
            logger.debug(f"[journey_validator] ✗ '{flow}' → {path} (absent)")

    resolvable_total = len(covered) + len(uncovered)
    coverage = len(covered) / resolvable_total if resolvable_total > 0 else 1.0
    is_useful = coverage >= USER_FLOWS_USEFUL_THRESHOLD

    logger.info(
        f"[journey_validator] {len(covered)}/{resolvable_total} flows couverts "
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
    }
