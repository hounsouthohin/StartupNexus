"""
brief_parser.py — Extraction déterministe du brief (sans LLM).

Principe : tout ce qui est écrit explicitement dans le brief est extrait par code.
Le LLM (Brief Normalizer) ne traite que ce qui n'est PAS trouvé ici.

Robustesse face à 3 types de briefs :
  - Vague    : "fais-moi une marketplace" → parser trouve rien → LLM fait tout
  - Partiel  : "avec Product et Order"   → parser trouve les noms → LLM complète structure
  - Explicite: Prisma models + pages + routes → parser trouve tout → LLM peut être skippé
"""

import re
from typing import TypedDict


class ParsedBrief(TypedDict):
    data_models: list    # ["Product { id String, name String, ... }"]
    pages: list          # ["app/page.tsx", "app/products/[id]/page.tsx"]
    api_routes: list     # ["app/api/products/route.ts"] (dédupliqués par fichier)
    api_methods: dict    # {"app/api/products/route.ts": ["GET", "POST"]}
    description: str     # Première ligne significative du brief
    has_explicit_models: bool
    has_explicit_pages: bool
    has_explicit_routes: bool


def parse_brief(phrase: str) -> ParsedBrief:
    """
    Parse déterministe du brief.
    Priorité 1 : blocs `Modèle Prisma : X { ... }` avec champs explicites
    Priorité 2 : listes de pages avec chemins `/xxx`
    Priorité 3 : routes API avec méthodes HTTP (GET, POST, PUT, PATCH, DELETE)
    """
    data_models = _extract_prisma_models(phrase)
    pages = _extract_pages(phrase)
    api_routes, api_methods = _extract_api_routes(phrase)
    description = _extract_description(phrase)

    return ParsedBrief(
        data_models=data_models,
        pages=pages,
        api_routes=api_routes,
        api_methods=api_methods,
        description=description,
        has_explicit_models=len(data_models) > 0,
        has_explicit_pages=len(pages) > 0,
        has_explicit_routes=len(api_routes) > 0,
    )


def _extract_prisma_models(text: str) -> list:
    """
    Extrait les blocs 'Modèle Prisma : X { ... }' avec tous leurs champs.
    Préserve les types exacts (String, Float, DateTime, @default, etc.).
    """
    models = []
    pattern = re.compile(
        r'Mod[eè]le?\s+Prisma\s*:?\s*(\w+)\s*\{([^}]+)\}',
        re.IGNORECASE | re.DOTALL,
    )
    for match in pattern.finditer(text):
        name = match.group(1).strip()
        fields_raw = match.group(2).strip()
        fields = [line.strip().rstrip(',') for line in fields_raw.splitlines() if line.strip()]
        model_str = f"{name} {{ {', '.join(fields)} }}"
        models.append(model_str)
    return models


def _extract_pages(text: str) -> list:
    """
    Extrait les chemins de pages depuis le brief.
    Reconnaît le format : '- /chemin : description'
    Convertit en chemins Next.js App Router (app/xxx/page.tsx).
    Ignore les chemins /api/.
    """
    pages = []
    seen = set()

    # Match: "- /path :" ou "- /path/[id] :" (avec ou sans colon)
    pattern = re.compile(r'[-*]\s+(\/[\w\/\[\]\-]*)\s*[:\u2014\u2013]', re.MULTILINE)

    for match in pattern.finditer(text):
        raw_path = match.group(1).strip()
        if '/api/' in raw_path:
            continue
        app_path = _path_to_app_route(raw_path)
        if app_path not in seen:
            seen.add(app_path)
            pages.append(app_path)

    return pages


def _extract_api_routes(text: str) -> tuple:
    """
    Extrait les routes API avec leurs méthodes HTTP.
    Retourne (routes_uniques, methods_par_route).
    Exemple : (["app/api/products/route.ts"], {"app/api/products/route.ts": ["GET", "POST"]})
    """
    route_file_map: dict = {}  # route_file → set of methods

    pattern = re.compile(
        r'\b(GET|POST|PUT|PATCH|DELETE)\s+(\/api\/[\w\/\[\]\-]+)',
        re.IGNORECASE,
    )
    for match in pattern.finditer(text):
        method = match.group(1).upper()
        api_path = match.group(2).strip()
        route_file = _api_path_to_route_file(api_path)
        if route_file not in route_file_map:
            route_file_map[route_file] = []
        if method not in route_file_map[route_file]:
            route_file_map[route_file].append(method)

    routes = list(route_file_map.keys())
    methods = {k: v for k, v in route_file_map.items()}
    return routes, methods


def _extract_description(text: str) -> str:
    """Extrait la première ligne significative comme description courte."""
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith('{') and not line.startswith('-') and not line.startswith('Modèle'):
            return line[:180]
    return "Application web"


def _path_to_app_route(raw_path: str) -> str:
    """
    Convertit un chemin URL en chemin fichier Next.js App Router.
    /           → app/page.tsx
    /dashboard  → app/dashboard/page.tsx
    /products/[id] → app/products/[id]/page.tsx
    """
    if raw_path == '/' or raw_path == '':
        return 'app/page.tsx'
    clean = raw_path.strip('/')
    return f'app/{clean}/page.tsx'


def _api_path_to_route_file(api_path: str) -> str:
    """
    Convertit un chemin API en fichier route Next.js.
    /api/products      → app/api/products/route.ts
    /api/products/[id] → app/api/products/[id]/route.ts
    """
    clean = api_path.strip('/')  # "api/products" ou "api/products/[id]"
    return f'app/{clean}/route.ts'


def _strip_prisma_decorators(model_str: str) -> str:
    """
    Retire les décorateurs Prisma (@id, @default(...), @relation(...), etc.)
    des champs d'un modèle.
    Avant : Product { id String @id @default(cuid()), stock Int @default(0) }
    Après  : Product { id String, stock Int }
    """
    return re.sub(r'\s+@\w+(?:\([^)]*\))?', '', model_str)


def _route_file_to_url(route_file: str) -> str:
    """
    Convertit un chemin fichier route Next.js en chemin URL API.
    app/api/products/route.ts      → /api/products
    app/api/products/[id]/route.ts → /api/products/[id]
    """
    without_app = route_file.removeprefix('app/')          # api/products/route.ts
    without_suffix = without_app.removesuffix('/route.ts') # api/products
    return '/' + without_suffix                            # /api/products


def requirements_from_parsed(parsed: ParsedBrief) -> list:
    """
    Dérive requirements[] depuis le résultat du parser déterministe.
    C'est LA source de vérité — jamais dérivée d'un LLM.

    Format aligné sur ce que spec_validator.validate_spec_requirements() sait lire :
      - Modèles  → "Modèle Prisma: Product { id String, name String, ... }"  (sans @décorateurs)
      - Pages    → "Page: /products/[id]"                                     (URL, pas fichier)
      - Routes   → "API Route: GET /api/products"                             (méthode + URL)

    Règle A spec_validator : extrait le nom après ":"  → vérifie \bProduct\b dans spec
    Règle C spec_validator : extrait le path /xxx     → vérifie /products/[id] dans spec
    Règle B spec_validator : extrait path après méthode → vérifie /api/products dans spec
    """
    reqs = []

    # Modèles Prisma — sans décorateurs pour matching fiable
    for model in parsed['data_models']:
        clean_model = _strip_prisma_decorators(model)
        reqs.append(f"Modèle Prisma: {clean_model}")

    # Pages — format URL (/products/[id]) pas fichier (app/products/[id]/page.tsx)
    for page in parsed['pages']:
        url = _app_route_to_url(page)
        reqs.append(f"Page: {url}")

    # Routes API — format méthode + URL pour que Règle B spec_validator matche
    methods_map = parsed.get('api_methods', {})
    seen_urls = set()
    for route_file in parsed['api_routes']:
        url = _route_file_to_url(route_file)
        methods = methods_map.get(route_file, [])
        if methods:
            for method in methods:
                key = f"{method}:{url}"
                if key not in seen_urls:
                    seen_urls.add(key)
                    reqs.append(f"API Route: {method} {url}")
        else:
            if url not in seen_urls:
                seen_urls.add(url)
                reqs.append(f"API Route: {url}")

    return reqs if reqs else ["Page: /"]


def build_normalized_brief_from_parsed(parsed: ParsedBrief, raw_phrase: str) -> str:
    """
    Construit un normalized_brief structuré depuis le parser (sans LLM).
    Utilisé quand le brief est complet — le LLM ne re-dérive pas ce qui est déjà exact.
    Format lisible par le planner et les logs.
    """
    lines = [f"APPLICATION: {parsed['description']}", ""]

    if parsed['data_models']:
        lines.append("MODÈLES MÉTIER (extraits verbatim du brief) :")
        for model in parsed['data_models']:
            lines.append(f"- {model}")
        lines.append("")

    if parsed['pages']:
        lines.append("PAGES DEMANDÉES :")
        for page in parsed['pages']:
            # Reconstruire le path URL depuis le fichier app router pour la lisibilité
            url = _app_route_to_url(page)
            lines.append(f"- {url} → {page}")
        lines.append("")

    if parsed['api_routes']:
        lines.append("ROUTES API :")
        methods_map = parsed.get('api_methods', {})
        for route in parsed['api_routes']:
            methods = methods_map.get(route, [])
            method_str = ', '.join(methods) if methods else '?'
            lines.append(f"- {method_str} → {route}")
        lines.append("")

    return "\n".join(lines).strip()


def _app_route_to_url(app_path: str) -> str:
    """Inverse de _path_to_app_route : app/products/[id]/page.tsx → /products/[id]"""
    if app_path == 'app/page.tsx':
        return '/'
    # app/dashboard/page.tsx → /dashboard
    without_prefix = app_path.removeprefix('app/')
    without_suffix = without_prefix.removesuffix('/page.tsx')
    return '/' + without_suffix


def describe_parsed(parsed: ParsedBrief) -> str:
    """Résumé lisible pour les logs."""
    parts = []
    if parsed['has_explicit_models']:
        parts.append(f"{len(parsed['data_models'])} modèle(s)")
    if parsed['has_explicit_pages']:
        parts.append(f"{len(parsed['pages'])} page(s)")
    if parsed['has_explicit_routes']:
        parts.append(f"{len(parsed['api_routes'])} route(s) API")
    if not parts:
        return "brief vague — aucune entité parsée"
    return "brief explicite : " + ", ".join(parts)
