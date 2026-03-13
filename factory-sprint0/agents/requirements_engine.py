"""
T002 — Requirements Engine Unifié
Source de vérité unique pour le mapping et la validation des requirements.

`_requirements_gate()` dans dev.py et `compute_spec_coverage()` dans
spec_coverage.py appellent ce module. Plus de logique dupliquée.

Règles de mapping (A→D) :
  A — Modèle Prisma → schema.prisma
  B — Route API (METHOD /path) → app/path/route.ts (exact)
  C — Page /path → app/path/page.tsx (exact)
  D — Chemin explicite dans le texte du requirement → existence fichier

Non-mappables : requirements sans marqueur connu → assumés satisfaits
(on ne peut pas les vérifier de façon déterministe).
"""
from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------------------
# Normalisation contenu fichier (T000-B intégré)
# ---------------------------------------------------------------------------

_NORMALIZABLE_SUFFIXES = (
    ".prisma", ".ts", ".tsx", ".js", ".jsx", ".py", ".md", ".yaml", ".yml"
)
_DOUBLE_N_RATIO_THRESHOLD = 0.01


def normalize_file_content(path: str, content: str) -> str:
    """
    Normalisation ciblée : si le contenu est stocké avec des \\n littéraux
    (double-encodage LLM) au lieu de vrais sauts de ligne (U+000A), les garde
    regex échouent silencieusement.

    Conditions pour normaliser :
    - Le fichier est d'un type texte courant (suffixe dans _NORMALIZABLE_SUFFIXES)
    - Le contenu ne contient aucun vrai \\n (U+000A)
    - Le ratio \\\\n littéraux / longueur > seuil (évite les faux positifs sur JSON)

    Les fichiers .json ne sont JAMAIS normalisés : risque de corruption légitime.
    """
    if not content:
        return content
    path_lower = path.lower().replace("\\", "/")
    if path_lower.endswith(".json"):
        return content
    if not any(path_lower.endswith(s) for s in _NORMALIZABLE_SUFFIXES):
        return content
    has_real_newline = "\n" in content
    has_literal_n = "\\n" in content
    if has_real_newline or not has_literal_n:
        return content
    ratio = content.count("\\n") * 2 / max(len(content), 1)
    if ratio < _DOUBLE_N_RATIO_THRESHOLD:
        return content
    return content.replace("\\n", "\n").replace("\\t", "\t")


# ---------------------------------------------------------------------------
# Utilitaires internes
# ---------------------------------------------------------------------------

def _norm_path(p: str) -> str:
    """Normalise un chemin : séparateurs Unix + lower-case."""
    return p.replace("\\", "/").lower()


def _build_file_set(files_dict: dict) -> set[str]:
    """Retourne l'ensemble des chemins normalisés présents dans files_dict."""
    return {_norm_path(fp) for fp in files_dict.keys()}


def _model_in_schema(model_name: str, schema_content: str) -> bool:
    """
    Vérifie qu'un modèle Prisma existe dans le schema.
    Applique la normalisation ciblée avant le regex.
    """
    schema_content = normalize_file_content("schema.prisma", schema_content)
    return bool(re.search(
        rf'\bmodel\s+{re.escape(model_name)}\s*\{{',
        schema_content,
        re.IGNORECASE,
    ))


def _extract_model_block(model_name: str, schema_content: str) -> str:
    """Retourne le bloc `model <Name> { ... }` (sans accolades) ou chaîne vide."""
    schema_content = normalize_file_content("schema.prisma", schema_content)
    m = re.search(
        rf"\bmodel\s+{re.escape(model_name)}\s*\{{(.*?)\}}",
        schema_content,
        re.IGNORECASE | re.DOTALL,
    )
    if not m:
        return ""
    return m.group(1)


def _schema_has_postgres_datasource(schema_content: str) -> bool:
    """
    Vérifie la présence d'un bloc datasource Prisma PostgreSQL.
    Exigence structurelle minimale pour cette stack.
    """
    schema_content = normalize_file_content("schema.prisma", schema_content)
    has_datasource = bool(
        re.search(r"\bdatasource\s+\w+\s*\{", schema_content, re.IGNORECASE)
    )
    has_pg_provider = bool(
        re.search(r"provider\s*=\s*['\"]postgresql['\"]", schema_content, re.IGNORECASE)
    )
    return has_datasource and has_pg_provider


def _extract_required_model_fields(req: str, model_name: str) -> tuple[set[str], set[str]]:
    """
    Extrait les champs requis d'un requirement Prisma et les champs marqués @unique.
    Retourne (required_fields, unique_required_fields).
    """
    req_lower = req.lower()
    m = re.search(r"avec\s+champs?\s+(.+)$", req_lower)
    if not m:
        return set(), set()

    raw_fields = m.group(1)
    chunks = re.split(r",|\bet\b", raw_fields)
    stopwords = {
        "avec", "champ", "champs", "model", "modèle", "prisma", "string",
        "boolean", "datetime", "int", "float", "json", "optional", "required",
        "unique", "slug", "id", "default", "now", "updatedat", "createdat",
    }
    # slug/id doivent rester autorisés comme noms de champs, on ne les retire pas ici.
    stopwords.discard("slug")
    stopwords.discard("id")
    stopwords.discard("createdat")
    stopwords.discard("updatedat")

    required_fields: set[str] = set()
    unique_required_fields: set[str] = set()
    for chunk in chunks:
        part = chunk.strip()
        if not part:
            continue
        tokens = re.findall(r"\b[a-z_][a-z0-9_]*\b", part)
        if not tokens:
            continue
        # Premier token non-stopword = nom de champ attendu.
        field = ""
        for t in tokens:
            if t not in stopwords and t != model_name.lower():
                field = t
                break
        if not field:
            continue
        required_fields.add(field)
        if "@unique" in part or " unique" in part:
            unique_required_fields.add(field)

    return required_fields, unique_required_fields


def _model_fields_satisfied(req: str, model_name: str, schema_content: str) -> bool:
    """
    Vérifie les champs critiques explicitement demandés dans le requirement.
    Si aucun champ n'est extractible, on se limite à l'existence du modèle.
    """
    model_block = _extract_model_block(model_name, schema_content)
    if not model_block:
        return False

    required_fields, unique_required_fields = _extract_required_model_fields(req, model_name)
    if not required_fields and not unique_required_fields:
        return True

    block_lower = model_block.lower()
    for field in required_fields:
        if not re.search(rf"\b{re.escape(field)}\b", block_lower):
            return False
    for field in unique_required_fields:
        line_match = re.search(
            rf"^\s*{re.escape(field)}\b[^\n]*$",
            model_block,
            re.IGNORECASE | re.MULTILINE,
        )
        if not line_match:
            return False
        if "@unique" not in line_match.group(0).lower():
            return False
    return True


def _model_fields_diff(req: str, model_name: str, schema_content: str) -> dict[str, Any]:
    """
    Retourne un diff déterministe pour expliquer les écarts Prisma:
    - model_present
    - missing_fields
    - missing_unique
    """
    model_block = _extract_model_block(model_name, schema_content)
    if not model_block:
        return {
            "model_present": False,
            "missing_fields": [],
            "missing_unique": [],
        }

    required_fields, unique_required_fields = _extract_required_model_fields(req, model_name)
    block_lower = model_block.lower()

    missing_fields: list[str] = []
    for field in sorted(required_fields):
        if not re.search(rf"\b{re.escape(field)}\b", block_lower):
            missing_fields.append(field)

    missing_unique: list[str] = []
    for field in sorted(unique_required_fields):
        line_match = re.search(
            rf"^\s*{re.escape(field)}\b[^\n]*$",
            model_block,
            re.IGNORECASE | re.MULTILINE,
        )
        if not line_match:
            missing_unique.append(field)
            continue
        if "@unique" not in line_match.group(0).lower():
            missing_unique.append(field)

    return {
        "model_present": True,
        "missing_fields": missing_fields,
        "missing_unique": missing_unique,
    }


# ---------------------------------------------------------------------------
# Moteur de mapping (règles A→D)
# ---------------------------------------------------------------------------

def check_requirement_verbose(req: str, files_dict: dict) -> tuple[bool, bool, str]:
    """
    Variante explicative de check_requirement.
    Retourne (is_mappable, satisfied, reason).
    """
    req_lower = req.lower()
    file_set = _build_file_set(files_dict)

    # -- Règle A : modèle Prisma ------------------------------------------
    if (
        "modèle prisma" in req_lower
        or "model prisma" in req_lower
        or "prisma:" in req_lower
    ):
        model_match = re.search(r':\s*(\w+)', req)
        if not model_match:
            return True, False, "Nom de modèle Prisma introuvable dans le requirement."
        model_name = model_match.group(1).lower()
        schema_content = next(
            (v for k, v in files_dict.items() if "schema.prisma" in _norm_path(k)),
            "",
        )
        if not _model_in_schema(model_name, schema_content):
            return True, False, f"Modèle '{model_name}' absent de prisma/schema.prisma."
        if not _schema_has_postgres_datasource(schema_content):
            return True, False, (
                "Datasource Prisma manquante/invalide dans prisma/schema.prisma "
                "(attendu: datasource db avec provider = \"postgresql\")."
            )
        diff = _model_fields_diff(req, model_name, schema_content)
        missing_fields = diff.get("missing_fields", [])
        missing_unique = diff.get("missing_unique", [])
        if missing_fields or missing_unique:
            details = []
            if missing_fields:
                details.append("champs manquants: " + ", ".join(missing_fields))
            if missing_unique:
                details.append("contraintes @unique manquantes: " + ", ".join(missing_unique))
            return True, False, "; ".join(details)
        return True, True, "Modèle Prisma conforme."

    # -- Règle B : route API (METHOD /path) --------------------------------
    route_match = re.search(
        r'(GET|POST|PUT|PATCH|DELETE)\s+(/[\w/\[\]-]+)', req, re.IGNORECASE
    )
    if route_match:
        api_path = route_match.group(2).strip("/")
        expected = _norm_path("app/" + api_path + "/route.ts")
        ok = expected in file_set
        reason = "Route API présente." if ok else f"Route API manquante: {expected}"
        return True, ok, reason

    # -- Règle C : page mentionnée avec chemin (/path) ---------------------
    if "page" in req_lower:
        page_match = re.search(r'/[\w\[\]/\-]+', req)
        if page_match:
            raw = page_match.group(0)
            page_path = _norm_path(raw.strip("/"))
            expected = _norm_path(f"app/{page_path}/page.tsx")
            ok = expected in file_set
            reason = "Page présente." if ok else f"Page manquante: {expected}"
            return True, ok, reason
        if re.search(r'(^|[\s:(])/(?=$|[\s),.:;])', req):
            ok = "app/page.tsx" in file_set
            reason = "Page racine présente." if ok else "Page racine manquante: app/page.tsx"
            return True, ok, reason

    # -- Règle D : chemin explicite dans le texte du requirement -----------
    path_match = re.search(
        r'(app/[\w/\[\].]+\.(tsx?|js|jsx)|[\w-]+\.(ts|tsx|js|prisma|json))',
        req, re.IGNORECASE
    )
    if path_match:
        req_path = _norm_path(path_match.group(1))
        ok = any(req_path in fp or fp.endswith(req_path) for fp in file_set)
        reason = "Fichier explicite présent." if ok else f"Fichier explicite manquant: {req_path}"
        return True, ok, reason

    # Requirement non mappable — assumé satisfait, non bloquant
    return False, True, "Requirement non mappable (non bloquant)."


def check_requirement(req: str, files_dict: dict) -> tuple[bool, bool]:
    """
    Vérifie un requirement unique contre files_dict.

    Retourne (is_mappable: bool, satisfied: bool) :
    - is_mappable=False → requirement non vérifiable de façon déterministe
      (ex: "Authentification Clerk robuste") → assumé satisfait, non bloquant.
    - is_mappable=True, satisfied=True  → critère couvert.
    - is_mappable=True, satisfied=False → critère manquant → gate bloque.
    """
    is_mappable, satisfied, _ = check_requirement_verbose(req, files_dict)
    return is_mappable, satisfied


# ---------------------------------------------------------------------------
# API publique
# ---------------------------------------------------------------------------

def gate_check(requirements: list[str], files_dict: dict) -> tuple[bool, str]:
    """
    Remplace `_requirements_gate()` dans dev.py.
    Bloque si au moins un requirement mappable n'est pas couvert.
    Retourne (bloqué: bool, message: str).
    """
    if not requirements:
        return False, ""

    missing: list[tuple[str, str]] = []
    for req in requirements:
        is_mappable, satisfied, reason = check_requirement_verbose(req, files_dict)
        if is_mappable and not satisfied:
            missing.append((req, reason))

    if missing:
        details = "\n".join(f"  - {req}\n    ↳ {reason}" for req, reason in missing)
        return True, (
            "REQUIREMENTS GATE — BUILD BLOQUÉ\n"
            f"{len(missing)} requirement(s) métier mappable(s) non couverts :\n"
            + details
            + "\n\nGénère les fichiers manquants avant d'appeler run_build."
        )
    return False, ""


def compute_coverage(requirements: list[str], files_dict: dict) -> dict[str, Any]:
    """
    Remplace `compute_spec_coverage()` dans spec_coverage.py (via T003).
    Retourne spec_coverage + détails.

    Non-mappables assumés satisfaits (on ne peut pas les vérifier) :
    ils n'apparaissent pas dans unmet et n'impactent pas le taux négativement.
    """
    if not requirements:
        return {
            "spec_coverage": 0.0,
            "requirements_met": 0,
            "requirements_total": 0,
            "unmet": [],
        }

    met: list[str] = []
    unmet: list[str] = []
    for req in requirements:
        is_mappable, satisfied = check_requirement(req, files_dict)
        if satisfied:
            met.append(req)
        else:
            # satisfied=False → forcément is_mappable=True (non-mappables → True)
            unmet.append(req)

    coverage = round(len(met) / len(requirements), 3)
    return {
        "spec_coverage": coverage,
        "requirements_met": len(met),
        "requirements_total": len(requirements),
        "unmet": unmet,
    }


def compute_coverage_detailed(requirements: list[str], files_dict: dict) -> dict[str, Any]:
    """
    Même logique que compute_coverage, avec statut détaillé par requirement.
    """
    if not requirements:
        return {
            "spec_coverage": 0.0,
            "requirements_met": 0,
            "requirements_total": 0,
            "unmet": [],
            "statuses": [],
        }

    statuses: list[dict[str, Any]] = []
    met_count = 0
    unmet: list[str] = []

    for req in requirements:
        is_mappable, satisfied, reason = check_requirement_verbose(req, files_dict)
        if satisfied:
            met_count += 1
        else:
            unmet.append(req)
        statuses.append(
            {
                "requirement": req,
                "is_mappable": is_mappable,
                "satisfied": satisfied,
                "reason": reason,
            }
        )

    coverage = round(met_count / len(requirements), 3)
    return {
        "spec_coverage": coverage,
        "requirements_met": met_count,
        "requirements_total": len(requirements),
        "unmet": unmet,
        "statuses": statuses,
    }
