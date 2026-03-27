"""
agents/spec_validator.py
Validation déterministe de la cohérence requirements[] ↔ spec générée.

Module isolé — stdlib uniquement (re).
Importable depuis tests et architect_activity sans déclencher langchain_openai.

Problème ciblé : spec_writer drift — le LLM renomme les entités (Post→Article,
/blog→/articles) malgré l'EXTRACTION RULE, rendant les requirements[] inutiles
côté DevAgent car la spec qu'il reçoit ne les reflète pas.

Ce validator détecte la dérive AVANT que la spec dégradée atteigne le DevAgent.
"""

import re
from typing import List, Dict


def _extract_key_terms(req: str) -> List[str]:
    """
    Extrait les termes "stables" d'un requirement — les termes qu'on attend
    dans la spec générée : nom d'entité, chemin de route, chemin de page.

    Retourne [] si aucun terme mappable détecté (requirement non vérifiable).
    """
    req_lower = req.lower()
    terms = []

    # Règle A — Modèle Prisma : "Modèle Prisma: Post" ou "modèle prisma: post" → "Post"/"post"
    # Insensible à la casse pour accepter minuscule (post, article) et PascalCase (Post, Article).
    if "prisma" in req_lower or "modèle" in req_lower or "model " in req_lower:
        m = re.search(r':\s*([A-Za-z][a-zA-Z0-9_]*)', req)
        if m:
            terms.append(m.group(1))

    # Règle B — Route API : "POST /api/posts/[id]" → "/api/posts/[id]"
    m = re.search(r'(?:GET|POST|PUT|PATCH|DELETE)\s+(/[\w/\[\]-]+)', req, re.IGNORECASE)
    if m:
        terms.append(m.group(1))

    # Règle C — Page : "Page: /dashboard" → "/dashboard"
    if "page" in req_lower:
        m = re.search(r'(/[\w/\[\]-]+)', req)
        if m:
            # Éviter de doubler si déjà capturé par Règle B
            path = m.group(1)
            if path not in terms:
                terms.append(path)

    return terms


def validate_spec_requirements(
    spec: str,
    requirements: List[str],
    threshold: float = 1.0,
) -> Dict:
    """
    Vérifie que chaque terme-clé des requirements[] est présent dans la spec.

    Retourne:
        {
            "status": "OK" | "DEGRADED",
            "unmatched_requirements": [...],  # requirements dont ≥1 terme absent
            "matched_count": int,
            "total_mappable": int,           # requirements avec au moins 1 terme détecté
        }

    Un requirement est "mappable" s'il contient au moins un terme extractible.
    Un requirement non-mappable (ex: "Authentification Clerk robuste") est ignoré
    — pas de terme stable à chercher dans la spec.

    threshold (0.0–1.0) : fraction minimale de requirements mappables devant être
    présents dans la spec pour obtenir "OK". Défaut = 1.0 (tous obligatoires).
    Exemple : threshold=0.9 → 1 manquant sur 10 toléré.

    status = "DEGRADED" si matched_count / total_mappable < threshold.
    """
    spec = spec or ""
    requirements = requirements or []
    threshold = max(0.0, min(1.0, float(threshold)))

    unmatched = []
    matched_count = 0
    total_mappable = 0

    for req in requirements:
        terms = _extract_key_terms(req)
        if not terms:
            # Non mappable — on skip sans pénaliser le score
            continue

        total_mappable += 1
        req_satisfied = all(
            re.search(rf'\b{re.escape(t)}\b' if not t.startswith('/') else re.escape(t), spec, re.IGNORECASE)
            for t in terms
        )

        if req_satisfied:
            matched_count += 1
        else:
            unmatched.append(req)

    if total_mappable == 0:
        status = "OK"
    elif (matched_count / total_mappable) >= threshold:
        status = "OK"
    else:
        status = "DEGRADED"

    return {
        "status": status,
        "unmatched_requirements": unmatched,
        "matched_count": matched_count,
        "total_mappable": total_mappable,
    }
