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


# ---------------------------------------------------------------------------
# Moteur de mapping (règles A→D)
# ---------------------------------------------------------------------------

def check_requirement(req: str, files_dict: dict) -> tuple[bool, bool]:
    """
    Vérifie un requirement unique contre files_dict.

    Retourne (is_mappable: bool, satisfied: bool) :
    - is_mappable=False → requirement non vérifiable de façon déterministe
      (ex: "Authentification Clerk robuste") → assumé satisfait, non bloquant.
    - is_mappable=True, satisfied=True  → critère couvert.
    - is_mappable=True, satisfied=False → critère manquant → gate bloque.
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
        if model_match:
            model_name = model_match.group(1).lower()
            schema_content = next(
                (v for k, v in files_dict.items() if "schema.prisma" in _norm_path(k)),
                "",
            )
            if not _model_in_schema(model_name, schema_content):
                return True, False
            return True, _model_fields_satisfied(req, model_name, schema_content)

    # -- Règle B : route API (METHOD /path) --------------------------------
    route_match = re.search(
        r'(GET|POST|PUT|PATCH|DELETE)\s+(/[\w/\[\]-]+)', req, re.IGNORECASE
    )
    if route_match:
        api_path = route_match.group(2).strip("/")
        expected = _norm_path("app/" + api_path + "/route.ts")
        return True, (expected in file_set)

    # -- Règle C : page mentionnée avec chemin (/path) ---------------------
    if "page" in req_lower:
        # Exige au moins un caractère après "/" pour éviter de matcher
        # systématiquement la racine quand le requirement vise /dashboard, /blog/[slug], etc.
        page_match = re.search(r'/[\w\[\]/\-]+', req)
        if page_match:
            raw = page_match.group(0)
            page_path = _norm_path(raw.strip("/"))
            expected = _norm_path(f"app/{page_path}/page.tsx")
            return True, (expected in file_set)
        # Cas racine explicite: "Page: /"
        if re.search(r'(^|[\s:(])/(?=$|[\s),.:;])', req):
            return True, ("app/page.tsx" in file_set)

    # -- Règle D : chemin explicite dans le texte du requirement -----------
    path_match = re.search(
        r'(app/[\w/\[\].]+\.(tsx?|js|jsx)|[\w-]+\.(ts|tsx|js|prisma|json))',
        req, re.IGNORECASE
    )
    if path_match:
        req_path = _norm_path(path_match.group(1))
        return True, any(
            req_path in fp or fp.endswith(req_path) for fp in file_set
        )

    # Requirement non mappable — assumé satisfait, non bloquant
    return False, True


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

    missing: list[str] = []
    for req in requirements:
        is_mappable, satisfied = check_requirement(req, files_dict)
        if is_mappable and not satisfied:
            missing.append(req)

    if missing:
        return True, (
            "REQUIREMENTS GATE — BUILD BLOQUÉ\n"
            f"{len(missing)} requirement(s) métier mappable(s) non couverts :\n"
            + "\n".join(f"  - {r}" for r in missing)
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
