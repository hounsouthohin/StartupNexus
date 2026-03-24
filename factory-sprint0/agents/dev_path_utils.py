"""
dev_path_utils.py — Fonctions pures de gestion des chemins et priorités.

Extraites de dev.py pour réduire la taille de dev_agent() :
- Priorité de génération des fichiers (depuis stack config)
- Résolution max_iterations par policy
- Extraction chemins depuis requirements
- Filtrage des chemins autorisés selon le blocker actif
- Détection du répertoire racine du projet généré
"""

from __future__ import annotations

import re
from typing import Callable


# ── Priorité de génération ───────────────────────────────────────────────────

def make_priority_ranker(priority_paths: list[str]) -> Callable[[str], int]:
    """
    Retourne une fonction rank(path) → int.
    Un rang faible = priorité haute.
    Construit depuis la liste `generation_order.priority_paths` du JSON de stack.
    """
    normalized = [str(p).replace("\\", "/").strip() for p in (priority_paths or []) if str(p).strip()]

    def _rank(path: str) -> int:
        p = str(path or "").replace("\\", "/").strip().lower()
        if not normalized:
            return 10_000
        for idx, raw_pat in enumerate(normalized):
            pat = raw_pat.lower()
            if pat.endswith("/"):
                if p.startswith(pat):
                    return idx
            elif p == pat or p.endswith("/" + pat):
                return idx
        return 10_000 + len(normalized)

    return _rank


def sort_paths_by_priority(paths: list[str], ranker: Callable[[str], int]) -> list[str]:
    return sorted(
        [str(p) for p in (paths or [])],
        key=lambda p: (ranker(p), str(p).replace("\\", "/").lower()),
    )


# ── Résolution max_iterations ────────────────────────────────────────────────

def resolve_max_iterations(cfg: dict, reqs: list | None, default: int = 14) -> int:
    """
    Calcule le max_iterations depuis la section `iteration_policy` du JSON de stack.
    Applique les tiers (par nombre de requirements).
    """
    policy = cfg.get("iteration_policy", {}) if isinstance(cfg, dict) else {}
    if not isinstance(policy, dict):
        return default
    try:
        base = int(policy.get("base_max_iterations", default))
    except Exception:
        base = default
    try:
        cap = int(policy.get("max_cap_iterations", base))
    except Exception:
        cap = base
    if cap < 1:
        cap = base if base >= 1 else default

    req_count = len(reqs or [])
    target = base
    tiers = policy.get("tiers", [])

    def _safe_int(v: object, d: int = 0) -> int:
        try:
            return int(v)  # type: ignore[arg-type]
        except Exception:
            return d

    if isinstance(tiers, list):
        for tier in sorted(
            [t for t in tiers if isinstance(t, dict)],
            key=lambda t: _safe_int(t.get("min_requirements", 0), 0),
        ):
            try:
                min_req = int(tier.get("min_requirements", 0))
                iter_cap = int(tier.get("max_iterations", target))
            except Exception:
                continue
            if req_count >= min_req:
                target = iter_cap

    target = max(1, target)
    target = min(target, cap)
    return target


# ── Extraction chemin depuis requirement ─────────────────────────────────────

def extract_primary_path_from_requirement(req: str) -> str:
    """
    Déduit le chemin de fichier principal qu'un requirement implique.
    Ex: "API Route: GET /api/orders" → "app/api/orders/route.ts"
        "Page: /dashboard"           → "app/dashboard/page.tsx"
        "Modèle Prisma: Order"       → "prisma/schema.prisma"
    """
    req = req or ""
    req_lower = req.lower()
    route_match = re.search(r'(GET|POST|PUT|PATCH|DELETE)\s+(/[\w/\[\]-]+)', req, re.IGNORECASE)
    if route_match:
        return f"app/{route_match.group(2).strip('/')}/route.ts"
    if "page" in req_lower:
        page_match = re.search(r'/[\w\[\]/\-]+', req)
        if page_match:
            return f"app/{page_match.group(0).strip('/')}/page.tsx"
        if re.search(r'(^|[\s:(])/(?=$|[\s),.:;])', req):
            return "app/page.tsx"
    if "modèle prisma" in req_lower or "model prisma" in req_lower or "prisma:" in req_lower:
        return "prisma/schema.prisma"
    return ""


def sort_requirements_by_priority(reqs: list[str], ranker: Callable[[str], int]) -> list[str]:
    if not reqs:
        return []
    decorated: list[tuple[int, str, str]] = []
    for req in reqs:
        primary = extract_primary_path_from_requirement(req)
        decorated.append((ranker(primary), primary, req))
    decorated.sort(key=lambda t: (t[0], t[1].lower(), t[2].lower()))
    return [t[2] for t in decorated]


# ── Chemins autorisés selon le blocker actif ─────────────────────────────────

def allowed_paths_for_blocker(state: dict, scaffold_extends_paths: set[str]) -> list[str]:
    """
    Retourne la liste des chemins que le LLM est autorisé à écrire
    étant donné le blocker actif (depuis _build_run_state).

    Fix boucle schema.prisma : scaffold_extends_paths n'est plus injecté pour
    file_missing:: et structural:: — ces blockers ciblent un fichier précis et
    n'ont pas besoin que le schema soit réécrit.
    Seul requirements::Prisma autorise explicitement prisma/schema.prisma.
    """
    blocker = state.get("active_blocker", "")
    if blocker.startswith("file_missing::"):
        p = blocker.split("::", 1)[1].strip()
        return [p] if p else []
    if blocker.startswith("requirements::"):
        req = blocker.split("::", 1)[1]
        primary = extract_primary_path_from_requirement(req)
        allowed: list[str] = []
        if primary:
            allowed.append(primary)
        req_lower = req.lower()
        if "modèle prisma" in req_lower or "model prisma" in req_lower or "prisma:" in req_lower:
            allowed.extend(["prisma/schema.prisma", "lib/prisma.ts", "prisma.config.ts"])
        return allowed
    if blocker.startswith("structural::"):
        targets = state.get("structural_targets", []) or []
        return [str(t).replace("\\", "/") for t in targets]
    return []


def path_is_allowed_for_objective(
    path: str,
    allowed_paths: list[str],
    blocker: str,
    scaffold_extends_paths: set[str],
) -> bool:
    """
    Vérifie si le LLM est autorisé à écrire ce chemin étant donné le blocker actif.
    Les fichiers scaffold_extends et les commons sont toujours autorisés.
    """
    if not allowed_paths:
        return True
    p = (path or "").replace("\\", "/").strip()
    p_lower = p.lower()
    # scaffold_extends : autorisés UNIQUEMENT si aucun blocker actif (ready_for_build),
    # si le blocker est requirements::Prisma,
    # ou si le blocker est file_missing:: et que le fichier est exactement la cible demandée.
    # Pour structural:: et autres file_missing:: non-cibles, le schema ne doit PAS être réécrit —
    # c'est la cause racine de la boucle prisma/schema.prisma.
    if p_lower in {s.replace("\\", "/").lower() for s in scaffold_extends_paths}:
        if not blocker or blocker == "ready_for_build":
            return True
        if blocker.startswith("file_missing::") or blocker.startswith("structural::"):
            # Autoriser si c'est exactement le fichier scaffold_extends demandé par le blocker
            # (file_missing = création initiale, structural = correction superviseur)
            return any(p_lower == a.replace("\\", "/").lower() for a in allowed_paths)
        if blocker.startswith("requirements::"):
            req_part = blocker.split("::", 1)[1].lower()
            if "modèle prisma" in req_part or "model prisma" in req_part or "prisma:" in req_part:
                return True
        return False
    # Blockers stricts : uniquement le fichier demandé
    if blocker.startswith("file_missing::"):
        return any(p_lower == a.replace("\\", "/").lower() for a in allowed_paths)
    if blocker.startswith("structural::"):
        return any(p_lower == a.replace("\\", "/").lower() for a in allowed_paths)
    # Fichiers fondamentaux toujours autorisés
    commons = {
        "package.json",
        ".env.local",
        "next.config.js",
        "tsconfig.json",
        "app/layout.tsx",
        "middleware.ts",
    }
    if p_lower in commons:
        return True
    allowed_norm = [a.replace("\\", "/").lower() for a in allowed_paths]
    return any(p_lower == a or p_lower.startswith(a.rsplit("/", 1)[0] + "/") for a in allowed_norm)


# ── Détection répertoire racine du projet ────────────────────────────────────

def find_project_dir(files_dict: dict, stack_id: str) -> str:
    """
    Déduit le répertoire racine du projet depuis les fichiers écrits.
    Utilise le root_file de la stack config (package.json par défaut).
    Retourne '.' si le projet est à la racine, sinon le sous-répertoire.
    """
    try:
        from agents.stack_config import get_root_file
        root_file = get_root_file(stack_id)
    except Exception:
        root_file = "package.json"
    root_filename = root_file.split("/")[-1]
    for p in files_dict.keys():
        normalized = p.replace("\\", "/")
        if normalized == root_file or normalized.endswith("/" + root_filename):
            parent = normalized.rsplit("/", 1)[0] if "/" in normalized else ""
            return parent if parent else "."
    return "."


# ── Violations d'imports interdits ──────────────────────────────────────────

def collect_forbidden_import_violations(
    files_dict: dict,
    forbidden_tokens: list[str],
    templated_names: set[str] | None = None,
) -> list[tuple[str, str]]:
    """Retourne les violations (path, token) pour les imports/patterns interdits."""
    templated = templated_names or set()
    tokens = [str(t).strip() for t in (forbidden_tokens or []) if str(t).strip()]
    if not tokens:
        return []
    violations: list[tuple[str, str]] = []
    for fp, fc in files_dict.items():
        fp_norm = fp.replace("\\", "/")
        if fp_norm in templated:
            continue
        if not fp_norm.endswith((".ts", ".tsx", ".js", ".jsx")):
            continue
        content_lower = (fc or "").lower()
        for tok in tokens:
            if tok.lower() in content_lower:
                violations.append((fp_norm, tok))
                break
    return violations


# ── Première directive d'un fichier ─────────────────────────────────────────

def first_directive_line(content: str, ignore_leading_comments: bool = False) -> str:
    """
    Retourne la première ligne sémantique d'un fichier.
    Utilisée pour détecter 'use client' / 'use server' en tête de fichier.
    Si ignore_leading_comments=True, saute les blocs // et /* */.
    """
    if not content:
        return ""
    if not ignore_leading_comments:
        return next((ln.strip() for ln in content.splitlines() if ln.strip()), "")

    in_block_comment = False
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if in_block_comment:
            if "*/" in line:
                in_block_comment = False
            continue
        if line.startswith("/*"):
            if "*/" not in line:
                in_block_comment = True
            continue
        if line.startswith("//"):
            continue
        return line
    return ""
