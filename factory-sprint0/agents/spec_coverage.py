"""
agents/spec_coverage.py
Calcul déterministe de la couverture spec (requirements vs fichiers générés).

Module isolé sans dépendances lourdes (uniquement stdlib `re`) —
importable depuis les tests sans déclencher langchain_openai / temporalio.
"""

import re


def _model_in_schema(model_name: str, schema_content: str) -> bool:
    """
    Vérifie qu'un modèle Prisma existe dans le schema avec sa déclaration exacte.
    Évite le faux positif "post" ∈ "postgresql".
    Syntaxe Prisma : 'model Post {' (insensible à la casse).
    """
    return bool(re.search(
        rf'\bmodel\s+{re.escape(model_name)}\s*\{{',
        schema_content,
        re.IGNORECASE,
    ))


def compute_spec_coverage(requirements: list, combined_files: dict) -> dict:
    """
    Compare requirements[] (Architect) vs combined_files (DevAgent).
    Retourne spec_coverage en pourcentage + liste des requirements non couverts.
    Algorithme déterministe — aucun LLM.
    """
    if not requirements:
        return {"spec_coverage": 0.0, "requirements_met": 0, "requirements_total": 0, "unmet": []}

    # Normaliser les paths une seule fois : séparateurs Unix + lower-case
    def _norm(p: str) -> str:
        return p.replace("\\", "/").lower()

    file_paths_norm = {_norm(fp) for fp in combined_files.keys()}

    met, unmet = [], []
    for req in requirements:
        req_lower = req.lower()
        satisfied = False

        # Règle 1 : path explicite dans le requirement (app/..., *.ts, schema.prisma...)
        path_match = re.search(
            r'(app/[\w/\[\].]+\.(tsx?|js|jsx)|[\w-]+\.(ts|tsx|js|prisma|json))',
            req, re.IGNORECASE
        )
        if path_match:
            req_path = _norm(path_match.group(1))
            if any(req_path in fp or fp.endswith(req_path) for fp in file_paths_norm):
                satisfied = True

        # Règle 2 : mention d'un modèle Prisma → vérifier schema.prisma
        if not satisfied and ("modèle prisma" in req_lower or "model prisma" in req_lower or "prisma:" in req_lower):
            model_match = re.search(r':\s*(\w+)', req)
            if model_match:
                model_name = model_match.group(1).lower()
                schema_content = next(
                    (v for k, v in combined_files.items() if "schema.prisma" in _norm(k)), ""
                )
                if _model_in_schema(model_name, schema_content):
                    satisfied = True

        # Règle 3 : route API (GET/POST/PUT/PATCH/DELETE /path)
        if not satisfied:
            route_match = re.search(
                r'(GET|POST|PUT|PATCH|DELETE)\s+(/[\w/\[\]-]+)', req, re.IGNORECASE
            )
            if route_match:
                # group(2) = "/api/posts/[id]" → strip('/') = "api/posts/[id]"
                # On préfixe avec "app/" seulement pour éviter le double "api/"
                api_path = route_match.group(2).strip('/')
                expected = _norm('app/' + api_path + '/route.ts')
                if any(expected in fp for fp in file_paths_norm):
                    satisfied = True

        # Règle 4 : page mentionnée (Page: /path ou page publique/protégée)
        # Le regex capture aussi la racine "/" (ex : "Page: /")
        if not satisfied and ("page" in req_lower):
            page_match = re.search(r'/(?:[\w\[\]/-]+)?', req)
            if page_match:
                raw = page_match.group(0)
                if raw == "/":
                    # Racine → app/page.tsx
                    if "app/page.tsx" in file_paths_norm:
                        satisfied = True
                else:
                    page_path = _norm(raw.strip('/'))
                    if any(page_path in fp for fp in file_paths_norm):
                        satisfied = True

        (met if satisfied else unmet).append(req)

    coverage = round(len(met) / len(requirements), 3) if requirements else 0.0
    return {
        "spec_coverage": coverage,
        "requirements_met": len(met),
        "requirements_total": len(requirements),
        "unmet": unmet,
    }
