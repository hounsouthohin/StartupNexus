"""
tsc_error_catalog.py — Catalogue déclaratif des classes d'erreurs TypeScript.

Chaque entrée mappe un code d'erreur tsc vers une liste de sous-cas (subcases).
Le moteur `lookup_error()` parcourt le catalogue en O(1) sur le code, puis
évalue les conditions par ordre jusqu'au premier match.

Structure d'une entrée :
  {
    "_pattern": regex pour extraire la valeur clé depuis la ligne d'erreur,
    "_extract": lambda match → extracted value (str ou tuple),
    "entries": [
      {
        "condition": lambda extracted → bool,
        "context_hint": lambda extracted → str  (instruction actionnable pour le LLM),
        "rag_query": str | None  (query RAG vers Qdrant pour standard correctif),
        "action": str           (code sémantique pour métriques/debug),
      },
      ...  # dernier entry = fallback (condition toujours True)
    ]
  }

Ajouter une nouvelle classe d'erreur = ajouter un bloc ici.
Aucune logique ne change dans file_validate_node ou _build_targeted_correction.
"""
from __future__ import annotations

import re as _re
from typing import Any


def _service_obj_name(module_path: str) -> str:
    """
    '@/lib/services/expense.service' → 'expenseService'
    '@/lib/services/invoice-item.service' → 'invoiceItemService'
    """
    name = module_path.split("/")[-1].replace(".service", "").replace(".ts", "")
    parts = name.split("-")
    return parts[0] + "".join(p.capitalize() for p in parts[1:]) + "Service"


# ─────────────────────────────────────────────────────────────────────────────
# CATALOGUE
# ─────────────────────────────────────────────────────────────────────────────

TSC_ERROR_CATALOG: dict[str, dict[str, Any]] = {

    # ── TS2307 : Cannot find module 'X' ──────────────────────────────────────
    "TS2307": {
        "_pattern": r"error TS2307: Cannot find module '([^']+)'",
        "_extract": lambda m: m.group(1),
        "entries": [
            {
                "condition": lambda mod: (
                    mod.startswith("@/") or mod.startswith("./") or mod.startswith("../")
                ),
                "context_hint": lambda mod: (
                    f"⚠️  FICHIER MANQUANT (TS2307) : '{mod}' n'existe pas sur le disque.\n"
                    f"  ACTION OBLIGATOIRE : crée '{_mod_to_path(mod)}' avec write_file(...).\n"
                    f"  NE modifie PAS l'import — le chemin est correct, c'est le fichier qui manque."
                ),
                "rag_query": "créer composant React fichier manquant Next.js TypeScript",
                "action": "CREATE_FILE",
            },
            {
                "condition": lambda mod: True,  # fallback : module npm
                "context_hint": lambda mod: (
                    f"⚠️  MODULE NPM MANQUANT (TS2307) : '{mod}' n'est pas installé.\n"
                    f"  ACTION : ajoute '{mod}' dans package.json dependencies et réinstalle."
                ),
                "rag_query": None,
                "action": "NPM_INSTALL",
            },
        ],
    },

    # ── TS2339 : Property 'X' does not exist on type 'Y' ─────────────────────
    # Pattern : capture jusqu'au dernier ' avant le . final de la ligne.
    # Gère les types complexes : '{ id: string; }', 'string | null', 'never'.
    # ([^']+) échouerait si le type contient des ' (ex: '"a" | "b"' — rare en TS strict).
    "TS2339": {
        "_pattern": r"error TS2339: Property '([^']+)' does not exist on type '(.+?)'\.",
        "_extract": lambda m: (m.group(1), m.group(2)),
        "entries": [
            {
                # never[] : tableau non typé (let items = []; try { items = await ... })
                "condition": lambda prop, typ: "never" in typ,
                "context_hint": lambda prop, typ: (
                    f"⚠️  TYPE NEVER (TS2339) : la variable contenant '{prop}' est inférée `never[]`.\n"
                    f"  CAUSE : tableau déclaré sans type puis assigné dans un try/catch.\n"
                    f"  FIX : `const items: ModelType[] = await prisma.model.findMany().catch(() => []);`\n"
                    f"  INTERDIT : `let items = []; try {{ items = await ...; }} catch {{ items = []; }}`"
                ),
                "rag_query": "TypeScript never tableau non typé annotation Prisma findMany",
                "action": "ADD_TYPE_ANNOTATION",
            },
            {
                # Propriété absente du schema Prisma
                "condition": lambda prop, typ: True,
                "context_hint": lambda prop, typ: (
                    f"⚠️  PROPRIÉTÉ ABSENTE (TS2339) : '{prop}' n'existe pas sur le type '{typ}'.\n"
                    f"  CAUSE : champ absent de prisma/schema.prisma ou typo dans le nom.\n"
                    f"  FIX : vérifie prisma/schema.prisma — utilise uniquement les champs déclarés."
                ),
                "rag_query": "TypeScript propriété Prisma inexistante schéma champs déclarés",
                "action": "CHECK_SCHEMA",
            },
        ],
    },

    # ── TS2304 : Cannot find name 'X' ────────────────────────────────────────
    "TS2304": {
        "_pattern": r"error TS2304: Cannot find name '([^']+)'",
        "_extract": lambda m: m.group(1),
        "entries": [
            # Entrée prioritaire : composants/hooks Next.js sans import explicite
            {
                "condition": lambda name: name in (
                    "Link", "Image", "useRouter", "usePathname",
                    "useSearchParams", "useParams", "redirect",
                    "notFound", "permanentRedirect",
                ),
                "context_hint": lambda name: (
                    f"⚠️  IMPORT NEXT.JS MANQUANT (TS2304) : '{name}' utilisé sans import.\n"
                    f"  FIX — ajoute l'import correspondant en tête de fichier :\n"
                    + {
                        "Link":             "  import Link from 'next/link'",
                        "Image":            "  import Image from 'next/image'",
                        "useRouter":        "  import {{ useRouter }} from 'next/navigation'",
                        "usePathname":      "  import {{ usePathname }} from 'next/navigation'",
                        "useSearchParams":  "  import {{ useSearchParams }} from 'next/navigation'",
                        "useParams":        "  import {{ useParams }} from 'next/navigation'",
                        "redirect":         "  import {{ redirect }} from 'next/navigation'",
                        "notFound":         "  import {{ notFound }} from 'next/navigation'",
                        "permanentRedirect":"  import {{ permanentRedirect }} from 'next/navigation'",
                    }.get(name, f"  import {{ {name} }} from 'next/navigation'")
                ),
                "rag_query": "Next.js import Link Image useRouter usePathname next/link next/navigation",
                "action": "FIX_NEXTJS_IMPORT",
            },
            # Fallback générique : type/interface absent de lib/types.ts
            {
                "condition": lambda name: True,
                "context_hint": lambda name: (
                    f"⚠️  NOM INTROUVABLE (TS2304) : '{name}' n'est pas défini dans ce scope.\n"
                    f"  CAUSE : type ou interface absent de lib/types.ts, ou import manquant.\n"
                    f"  FIX : vérifie lib/types.ts — utilise uniquement les noms exportés."
                ),
                "rag_query": "TypeScript types lib exportés Prisma modèles noms introuvables",
                "action": "CHECK_TYPES_FILE",
            },
        ],
    },

    # ── TS2724 : Module X has no exported member Y ───────────────────────────
    "TS2724": {
        "_pattern": r"error TS2724: '([^']+)' has no exported member named '([^']+)'",
        "_extract": lambda m: (m.group(1), m.group(2)),
        "entries": [
            {
                "condition": lambda mod, name: True,
                "context_hint": lambda mod, name: (
                    f"⚠️  EXPORT INEXISTANT (TS2724) : '{mod}' n'exporte pas '{name}'.\n"
                    f"  FIX : vérifie lib/types.ts — les noms exportés sont ceux définis dans la spec."
                ),
                "rag_query": "TypeScript types lib exportés Prisma modèles noms introuvables",
                "action": "CHECK_TYPES_FILE",
            },
        ],
    },

    # ── TS7006 : Parameter 'X' implicitly has an 'any' type ──────────────────
    "TS7006": {
        "_pattern": r"error TS7006: Parameter '([^']+)' implicitly has an 'any' type",
        "_extract": lambda m: m.group(1),
        "entries": [
            {
                "condition": lambda name: True,
                "context_hint": lambda name: (
                    f"⚠️  TYPE IMPLICITE (TS7006) : le paramètre '{name}' n'a pas de type déclaré.\n"
                    f"  FIX : ajoute un type explicite :\n"
                    f"    callback React → {name}: React.ChangeEvent<HTMLInputElement>\n"
                    f"    destructuring  → {{ {name} }}: {{ {name}: string }}"
                ),
                "rag_query": "TypeScript paramètre type explicite React event handler callback",
                "action": "ADD_EXPLICIT_TYPE",
            },
        ],
    },

    # ── TS7031 : Binding element 'X' implicitly has an 'any' type ────────────
    "TS7031": {
        "_pattern": r"error TS7031: Binding element '([^']+)' implicitly has an 'any' type",
        "_extract": lambda m: m.group(1),
        "entries": [
            {
                "condition": lambda name: True,
                "context_hint": lambda name: (
                    f"⚠️  DESTRUCTURING NON TYPÉ (TS7031) : '{name}' n'a pas de type déclaré.\n"
                    f"  FIX : `function Component({{ {name} }}: {{ {name}: string }}) {{ ... }}`"
                ),
                "rag_query": "TypeScript destructuring paramètre type explicite composant Next.js",
                "action": "ADD_EXPLICIT_TYPE",
            },
        ],
    },

    # ── TS2531 : Object is possibly 'null' ────────────────────────────────────
    "TS2531": {
        "_pattern": r"error TS2531: Object is possibly '(null)'",
        "_extract": lambda m: m.group(1),
        "entries": [
            {
                "condition": lambda _: True,
                "context_hint": lambda _: (
                    "⚠️  POSSIBLY NULL (TS2531) : l'objet peut être null avant l'accès.\n"
                    "  FIX : ajoute un guard nul :\n"
                    "    `const item = await prisma.model.findUnique({ where: { id } });`\n"
                    "    `if (!item) return NextResponse.json({ error: 'Not found' }, { status: 404 });`"
                ),
                "rag_query": "TypeScript null check guard Prisma findUnique NextResponse 404",
                "action": "ADD_NULL_CHECK",
            },
        ],
    },

    # ── TS2322 : Type X is not assignable to type Y (assignment / property) ────
    # Distinct de TS2345 (argument de fonction) — même cause racine possible.
    "TS2322": {
        "_pattern": r"error TS2322: Type '([^']+)' is not assignable to type '([^']+)'",
        "_extract": lambda m: (m.group(1), m.group(2)),
        "entries": [
            {
                # string | null passé à Prisma where/create : auth guard absent
                "condition": lambda got, expected: "null" in got and "string" in got,
                "context_hint": lambda got, expected: (
                    f"⚠️  AUTH GUARD MANQUANT (TS2322) : '{got}' ne peut pas être passé à Prisma.\n"
                    f"  CAUSE : auth() retourne userId: string | null — il faut le narrower avant Prisma.\n"
                    f"  FIX OBLIGATOIRE dans le handler :\n"
                    f"    const {{ userId }} = await auth();\n"
                    f"    if (!userId) return NextResponse.json({{ error: 'Unauthorized' }}, {{ status: 401 }});\n"
                    f"  Après ce guard, userId est string (non-nullable) — Prisma accepte."
                ),
                "rag_query": "Clerk auth userId null guard NextResponse Prisma TypeScript",
                "action": "FIX_AUTH_GUARD",
            },
            {
                # CreateXxxInput contenant userId/authorId → type incompatible avec Prisma input
                "condition": lambda got, expected: (
                    "userId" in expected or "authorId" in expected
                    or "userId" in got or "authorId" in got
                ),
                "context_hint": lambda got, expected: (
                    f"⚠️  CREATEINPUT AVEC USERID (TS2322) : le type d'entrée contient un champ owner.\n"
                    f"  CAUSE : CreateXxxInput ne doit JAMAIS inclure userId/authorId — ces champs viennent de auth().\n"
                    f"  FIX dans lib/types.ts : retire userId/authorId du type CreateXxxInput.\n"
                    f"  Dans le service : ajouter le champ owner séparément lors du create :\n"
                    f"    prisma.model.create({{ data: {{ ...data, <owner_field>: ownerId }} }})"
                ),
                "rag_query": "CreateInput sans userId authorId auth() Prisma service TypeScript",
                "action": "FIX_CREATEINPUT_OWNER",
            },
            {
                "condition": lambda got, expected: True,
                "context_hint": lambda got, expected: (
                    f"⚠️  TYPE INCOMPATIBLE (TS2322) : '{got}' n'est pas assignable à '{expected}'.\n"
                    f"  FIX : aligne le type de la valeur assignée avec le type attendu."
                ),
                "rag_query": "TypeScript type incompatible assignable propriété Next.js Prisma",
                "action": "FIX_TYPE_MISMATCH",
            },
        ],
    },

    # ── TS2305 : Module X has no exported member Y ───────────────────────────
    # Déclenché quand le LLM importe une fonction nommée inexistante depuis un service.
    # Ex: import { getExpenses } from '@/lib/services/expense.service'
    # → le service exporte un objet (expenseService.findMany), pas des fonctions nommées.
    "TS2305": {
        "_pattern": r"error TS2305: Module '([^']+)' has no exported member '([^']+)'",
        "_extract": lambda m: (m.group(1), m.group(2)),
        "entries": [
            {
                # Clerk V4 → V6 : auth/currentUser doivent venir de @clerk/nextjs/server
                "condition": lambda mod, name: "@clerk/nextjs" in mod and "server" not in mod and name in ("auth", "currentUser", "clerkClient"),
                "context_hint": lambda mod, name: (
                    f"⚠️  IMPORT CLERK INCORRECT (TS2305) : '{name}' n'existe pas dans '@clerk/nextjs'.\n"
                    f"  CAUSE : syntaxe Clerk V4 détectée. La stack utilise Clerk V5/V6.\n"
                    f"  FIX OBLIGATOIRE dans TOUS les fichiers qui ont cette erreur :\n"
                    f"    INTERDIT  → import {{ {name} }} from '@clerk/nextjs'\n"
                    f"    CORRECT   → import {{ {name} }} from '@clerk/nextjs/server'\n"
                    f"  S'applique à : app/api/**/route.ts et tous les Server Components."
                ),
                "rag_query": "clerk auth currentUser server import nextjs/server API route",
                "action": "FIX_CLERK_SERVER_IMPORT",
            },
            {
                # Import depuis lib/services : mauvais pattern (fonctions nommées vs objet service)
                "condition": lambda mod, name: "services" in mod,
                "context_hint": lambda mod, name: (
                    f"⚠️  EXPORT INEXISTANT (TS2305) : '{mod}' n'exporte pas '{name}'.\n"
                    f"  CAUSE : les services exportent un OBJET, pas des fonctions nommées.\n"
                    f"  PATTERN CORRECT :\n"
                    f"    import {{ {_service_obj_name(mod)} }} from '{mod}'\n"
                    f"    const data = await {_service_obj_name(mod)}.findMany(userId)\n"
                    f"  JAMAIS : import {{ getAll, getById }} from '{mod}' — ces exports n'existent pas."
                ),
                "rag_query": "service DAL objet TypeScript Prisma findMany export nommé",
                "action": "FIX_SERVICE_IMPORT",
            },
            {
                "condition": lambda mod, name: True,
                "context_hint": lambda mod, name: (
                    f"⚠️  EXPORT INEXISTANT (TS2305) : '{mod}' n'exporte pas '{name}'.\n"
                    f"  FIX : vérifie les exports du module — utilise uniquement les noms déclarés."
                ),
                "rag_query": "TypeScript export inexistant module import nommé",
                "action": "CHECK_EXPORTS",
            },
        ],
    },

    # ── TS2345 : Argument of type X is not assignable to Y ───────────────────
    "TS2345": {
        "_pattern": r"error TS2345: Argument of type '([^']+)' is not assignable to parameter of type '([^']+)'",
        "_extract": lambda m: (m.group(1), m.group(2)),
        "entries": [
            {
                # string | null vers string : auth guard manquant
                "condition": lambda got, expected: "null" in got and "null" not in expected,
                "context_hint": lambda got, expected: (
                    f"⚠️  TYPE INCOMPATIBLE (TS2345) : valeur nullable '{got}' passée à '{expected}'.\n"
                    f"  CAUSE PROBABLE : userId non-narrowé après auth().\n"
                    f"  FIX : `const {{ userId }} = await auth(); if (!userId) return 401;` AVANT l'accès Prisma."
                ),
                "rag_query": "TypeScript auth guard userId null check Clerk Prisma",
                "action": "FIX_AUTH_GUARD",
            },
            {
                "condition": lambda got, expected: True,
                "context_hint": lambda got, expected: (
                    f"⚠️  TYPE INCOMPATIBLE (TS2345) : reçu '{got}', attendu '{expected}'.\n"
                    f"  FIX : corrige le type de la valeur passée ou du paramètre attendu."
                ),
                "rag_query": "TypeScript type mismatch incompatible assignable Prisma",
                "action": "FIX_TYPE_MISMATCH",
            },
        ],
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS INTERNES
# ─────────────────────────────────────────────────────────────────────────────

def _mod_to_path(mod: str) -> str:
    """Converts '@/components/TaskForm' → 'components/TaskForm.tsx' (heuristique)."""
    clean = mod.lstrip("@").lstrip("/")
    basename = clean.rsplit("/", 1)[-1]
    is_component = (
        basename[:1].isupper()
        or "component" in clean.lower()
        or clean.startswith("components/")
        or clean.startswith("app/")
    )
    ext = ".tsx" if is_component else ".ts"
    # Si le module a déjà une extension, ne pas en ajouter
    if "." in basename:
        return clean
    return clean + ext


# ─────────────────────────────────────────────────────────────────────────────
# API PUBLIQUE
# ─────────────────────────────────────────────────────────────────────────────

class CatalogMatch:
    """Résultat d'un lookup dans le catalogue."""
    __slots__ = ("code", "action", "context_hint", "rag_query")

    def __init__(self, code: str, action: str, context_hint: str, rag_query: str | None) -> None:
        self.code = code
        self.action = action
        self.context_hint = context_hint
        self.rag_query = rag_query


def lookup_error(err_line: str) -> CatalogMatch | None:
    """
    Cherche err_line dans le catalogue TSC_ERROR_CATALOG.

    Retourne un CatalogMatch (context_hint + rag_query + action) si un pattern
    correspond, None si l'erreur n'est pas cataloguée.

    Complexité : O(nb_codes) sur le code d'erreur, O(nb_entries) sur les sous-cas.
    En pratique < 10 codes → O(1) pour les erreurs fréquentes.
    """
    for code, spec in TSC_ERROR_CATALOG.items():
        if f"error {code}" not in err_line:
            continue
        m = _re.search(spec["_pattern"], err_line)
        if not m:
            continue
        extracted = spec["_extract"](m)
        for entry in spec["entries"]:
            try:
                if isinstance(extracted, tuple):
                    matched = entry["condition"](*extracted)
                else:
                    matched = entry["condition"](extracted)
            except Exception:
                continue
            if matched:
                try:
                    if isinstance(extracted, tuple):
                        hint = entry["context_hint"](*extracted)
                    else:
                        hint = entry["context_hint"](extracted)
                except Exception:
                    hint = f"[catalog error: hint generation failed for {code}]"
                return CatalogMatch(
                    code=code,
                    action=entry["action"],
                    context_hint=hint,
                    rag_query=entry.get("rag_query"),
                )
        break  # code trouvé mais aucune condition matchée → stop
    return None
