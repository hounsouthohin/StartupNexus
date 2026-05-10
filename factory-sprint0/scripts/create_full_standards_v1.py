"""
scripts/create_full_standards_v1.py

Standards COMPLETS — stack nextjs-clerk-prisma — SOURCE UNIQUE (v3).
Zones 1-30 + hard rules. Ce fichier est l'unique source de vérité pour Qdrant.

Ce fichier REMPLACE :
  - populate_qdrant.py                       (standards descriptifs, buggués)
  - create_sprint2_prescriptive_standards.py (5 standards Sprint 2 seulement)
  - migrate_zones_17_18.py                   (ZONE_17B stack patterns + ZONE_18 tsc correctifs)
  - migrate_zone_19_saas_senior.py           (ZONE_19 SaaS senior patterns)
  - migrate_zone_20_dal_service.py           (ZONE_20 DAL service pattern)
  - migrate_zone_21_pagination.py            (ZONE_21 pagination skip/take)
  - migrate_zone_22_prisma_errors.py         (ZONE_22 codes Prisma P2002/P2025)
  - migrate_zone_23_create_input.py          (ZONE_23 CreateInput sans userId)
  - migrate_zone_24_n1_prevention.py         (ZONE_24 N+1 include)
  - migrate_zone_25_select_minimal.py        (ZONE_25 — NON INCLUS : 2 standards RECOMMANDÉ, hors scope actuel)
  - migrate_zone_26_transactions.py          (ZONE_26 $transaction)
  - migrate_zone_27_logging.py               (ZONE_27 Pino logging)
  - migrate_zone_28_connection_pooling.py    (ZONE_28 globalThis singleton)
  - migrate_zone_29_soft_delete.py           (ZONE_29 — non inclus, hors scope MVP)
  - migrate_zone_30_healthcheck.py           (ZONE_30 healthcheck)
  - enrich_qdrant.py                         (ZONE_HARD_RULES: Clerk, Prisma7, auth guard, etc.)

OPTION A — FORMAT PRESCRIPTIF SEMANTIQUE :
  Chaque standard commence par RULE: (alias TECHNOLOGIE:) — identifiant technique distinctif.
  ACTION:/STACK:/STATUS:/VERSION: retirés du page_content → metadata uniquement.
  Objectif : scores cosinus 0.7-0.9 au lieu de 0.3-0.5 (préfixes génériques uniformes supprimés).

PROCÉDURE D'INJECTION (ordre obligatoire) :
  1. python scripts/reset_qdrant.py               (purge totale)
  2. python scripts/create_full_standards_v1.py   (injection complète)

FORMAT PRESCRIPTIF pour chaque standard :
  ACTION: INTERDIT | OBLIGATOIRE | PRÉFÉRÉ
  STACK: nextjs-clerk-prisma
  TECHNOLOGIE: <package ou pattern exact>
  RAISON: <impact concret si violé>
  DETECTION_REGEX: <pattern de détection>
  ALTERNATIVE: <quoi utiliser à la place>
  EXEMPLE_INVALIDE: <code exact qui échoue>
  EXEMPLE_VALIDE: <code correct>
  ERREUR_ATTENDUE: <message d'erreur exact ou comportement>
  STATUS: active | draft
  VERSION: 1.0

SOURCES :
  - Perplexity 2026-03-01 (5 requêtes sur Next.js 14, Jest 29, Clerk v6, Prisma 7)
  - Runs factory empiriques (Sprints 1-2)
  - Doc officielle Next.js, Clerk, Prisma, Jest

ZONES :
  Zone 1  — Fichiers obligatoires + structure canonique
  Zone 2  — Package configuration
  Zone 3  — TypeScript configuration
  Zone 4  — Next.js configuration (next.config.js + middleware)
  Zone 5  — App Router layout (Clerk + html/body)
  Zone 6  — Authentification Clerk v6 (breaking changes v5→v6)
  Zone 7  — Base de données Prisma 7
  Zone 8  — Tests Jest 29 (next/jest + setupFilesAfterEnv)
  Zone 9  — Sécurité (auth checks + Zod + env vars)
  Zone 10 — Sécurité avancée
  Zone 11 — Gestion d'erreurs
  Zone 12 — Tests avancés
  Zone 13 — Logique métier
  Zone 14 — Anti-patterns
  Zone 15 — Conformité : coverage requirements + cohérence brief↔entités + page stubs (Sprint 4.6 + Sprint 4.8)
  Zone 16 — Sécurité applicative : Route Handlers + Server Actions + Service DAL ownership (Sprint 4.6 + Sprint 4.8)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from dotenv import load_dotenv
try:
    from agents.embedding_provider import (
        get_embedding_provider,
        get_embeddings,
        resolve_embedding_model,
    )
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from agents.embedding_provider import (
        get_embedding_provider,
        get_embeddings,
        resolve_embedding_model,
    )
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct

load_dotenv(dotenv_path=".env")

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "factory_standards")
EMBEDDING_MODEL = resolve_embedding_model(os.getenv("EMBEDDING_MODEL", "text-embedding-3-large"))
EMBEDDING_PROVIDER = get_embedding_provider()
try:
    EMBEDDINGS = get_embeddings(EMBEDDING_MODEL)
    _EMBEDDING_INIT_ERROR: Exception | None = None
except Exception as exc:
    EMBEDDINGS = None
    _EMBEDDING_INIT_ERROR = exc

# =============================================================================
# PHASE D — SANITIZATION DES ENTITES METIER
# =============================================================================

ENTITY_BASE_TERMS = (
    "Product",
    "Order",
    "User",
    "Booking",
    "Invoice",
    "Post",
    "Book",
    "Review",
    "Todo",
    "Category",
    "Article",
    "Item",
    "Cart",
    "Payment",
)

# Pluriels explicites pour garantir une substitution stable.
ENTITY_PLURAL_SEGMENTS = {
    "product": "products",
    "order": "orders",
    "user": "users",
    "booking": "bookings",
    "invoice": "invoices",
    "post": "posts",
    "book": "books",
    "review": "reviews",
    "todo": "todos",
    "category": "categories",
    "article": "articles",
    "item": "items",
    "cart": "carts",
    "payment": "payments",
}

_ENTITY_MODEL_TERMS_LOWER = tuple(sorted((t.lower() for t in ENTITY_BASE_TERMS), key=len, reverse=True))
_ENTITY_ROUTE_SEGMENTS = tuple(
    sorted(set(_ENTITY_MODEL_TERMS_LOWER + tuple(ENTITY_PLURAL_SEGMENTS.values())), key=len, reverse=True)
)
_ENTITY_ROUTE_API_SEGMENTS_PATTERN = "|".join(re.escape(s) for s in _ENTITY_ROUTE_SEGMENTS)
_ENTITY_MODEL_PATTERN = re.compile(
    r"\bmodel\s+(" + "|".join(re.escape(s) for s in _ENTITY_MODEL_TERMS_LOWER) + r")\b"
)
_ENTITY_REQUIREMENT_MODEL_PATTERN = re.compile(
    r"(Modèle Prisma:\s*)(" + "|".join(re.escape(s) for s in _ENTITY_MODEL_TERMS_LOWER) + r")\b",
    re.IGNORECASE,
)
_ENTITY_PRISMA_ACCESSOR_PATTERN = re.compile(
    r"\bprisma\.(" + "|".join(re.escape(s) for s in _ENTITY_MODEL_TERMS_LOWER) + r")\b"
)
_ENTITY_API_ROUTE_PATTERN = re.compile(
    r"/api/(" + _ENTITY_ROUTE_API_SEGMENTS_PATTERN + r")(?=(?:/|$|[^A-Za-z0-9_]))"
)
_ENTITY_GENERIC_ROUTE_PATTERN = re.compile(
    r"/(" + _ENTITY_ROUTE_API_SEGMENTS_PATTERN + r")(?=(?:/|$|[^A-Za-z0-9_]))"
)

# User est traité uniquement dans les contextes structurels (model / prisma / route)
# pour préserver la lisibilité des règles auth (userId, utilisateur, etc.).
_ENTITY_NOUN_TERMS = tuple(t for t in ENTITY_BASE_TERMS if t.lower() != "user")
_ENTITY_NOUN_VARIANTS: set[str] = set()
for _term in _ENTITY_NOUN_TERMS:
    _lower = _term.lower()
    _ENTITY_NOUN_VARIANTS.add(_term)
    _ENTITY_NOUN_VARIANTS.add(_lower)
    _plural = ENTITY_PLURAL_SEGMENTS.get(_lower, f"{_lower}s")
    _ENTITY_NOUN_VARIANTS.add(_plural)
    _ENTITY_NOUN_VARIANTS.add(_plural.capitalize())
_ENTITY_NOUN_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(v) for v in sorted(_ENTITY_NOUN_VARIANTS, key=len, reverse=True)) + r")\b"
)

_ENTITY_AUDIT_VARIANTS: set[str] = set()
for _term in ENTITY_BASE_TERMS:
    _lower = _term.lower()
    _ENTITY_AUDIT_VARIANTS.add(_term)
    _ENTITY_AUDIT_VARIANTS.add(_lower)
    _plural = ENTITY_PLURAL_SEGMENTS.get(_lower, f"{_lower}s")
    _ENTITY_AUDIT_VARIANTS.add(_plural)
    _ENTITY_AUDIT_VARIANTS.add(_plural.capitalize())
_ENTITY_AUDIT_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(v) for v in sorted(_ENTITY_AUDIT_VARIANTS, key=len, reverse=True)) + r")\b"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Injecte les standards complets dans Qdrant avec sanitization optionnelle "
            "des entités métier (Phase D)."
        )
    )
    parser.add_argument(
        "--audit-only",
        action="store_true",
        help="Affiche le rapport de pollution d'entités sans injecter dans Qdrant.",
    )
    parser.add_argument(
        "--only-modified",
        action="store_true",
        help="Injecte uniquement les standards modifiés par la sanitization.",
    )
    parser.add_argument(
        "--no-sanitize",
        action="store_true",
        help="Désactive la sanitization des entités métier (comportement legacy).",
    )
    return parser.parse_args()


def _detect_domain_terms(text: str) -> list[str]:
    return sorted({m.group(0) for m in _ENTITY_AUDIT_PATTERN.finditer(text)})


def _sanitize_standard_text(text: str) -> str:
    sanitized = text
    sanitized = _ENTITY_REQUIREMENT_MODEL_PATTERN.sub(r"\1[MODEL_NAME]", sanitized)
    sanitized = _ENTITY_MODEL_PATTERN.sub("model [MODEL_NAME]", sanitized)
    sanitized = _ENTITY_PRISMA_ACCESSOR_PATTERN.sub("prisma.[entity]", sanitized)
    sanitized = _ENTITY_API_ROUTE_PATTERN.sub("/api/[entities]", sanitized)
    sanitized = _ENTITY_GENERIC_ROUTE_PATTERN.sub("/[entities]", sanitized)
    sanitized = _ENTITY_NOUN_PATTERN.sub("[ENTITY]", sanitized)
    return sanitized


def _sanitize_standards(
    indexed_standards: list[tuple[int, dict]],
) -> tuple[list[dict], list[dict]]:
    prepared: list[dict] = []
    report: list[dict] = []

    for idx, std in indexed_standards:
        text = str(std.get("text", ""))
        metadata = dict(std.get("metadata", {}))
        before_terms = _detect_domain_terms(text)
        sanitized_text = _sanitize_standard_text(text)
        after_terms = _detect_domain_terms(sanitized_text)
        changed = sanitized_text != text

        if before_terms or changed:
            report.append(
                {
                    "index": idx,
                    "zone": metadata.get("zone", "unknown"),
                    "category": metadata.get("category", "unknown"),
                    "changed": changed,
                    "terms_before": before_terms,
                    "terms_after": after_terms,
                    "excerpt": text.replace("\n", " ")[:180],
                }
            )

        prepared.append(
            {
                "index": idx,
                "text": sanitized_text,
                "original_text": text,
                "metadata": metadata,
                "changed": changed,
            }
        )

    return prepared, report


def _write_pollution_report(report_items: list[dict]) -> str:
    metrics_dir = os.path.join("logs", "metrics")
    os.makedirs(metrics_dir, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join(metrics_dir, f"qdrant_phase_d_entity_audit_{ts}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report_items, f, ensure_ascii=True, indent=2)
    return path


def text_to_uuid(text: str) -> str:
    """UUID déterministe basé sur MD5(text) — idempotence garantie."""
    hash_bytes = hashlib.md5(text.encode("utf-8")).digest()
    return str(UUID(bytes=hash_bytes))


# =============================================================================
# OPTION A — REFORMATAGE POUR EMBEDDINGS SEMANTIQUES
# Problème : ACTION:/STACK: identiques sur tous les standards → embeddings uniformes
#            → scores cosinus 0.3-0.5 au lieu de 0.7-0.9
# Solution : retirer les préfixes génériques, commencer par RULE: (contenu technique)
# =============================================================================

def _reformat_text(text: str) -> str:
    """Option A: retire les préfixes génériques ACTION:/STACK: du text avant embedding.

    Ces lignes sont identiques sur ~100% des standards et polluent les vecteurs.
    On les déplace dans metadata (déjà présent : status, stack). Le texte commence
    maintenant par RULE: (alias de TECHNOLOGIE:), qui est le contenu le plus distinctif.
    """
    result = re.sub(r"^ACTION:\s*\S+[^\n]*\n?", "", text, flags=re.MULTILINE)
    result = re.sub(r"^STACK:\s*\S+[^\n]*\n?", "", result, flags=re.MULTILINE)
    result = re.sub(r"\nSTATUS:\s*\S+\s*$", "", result.rstrip())
    result = re.sub(r"\nVERSION:\s*[\d.]+\s*$", "", result.rstrip())
    result = re.sub(r"^TECHNOLOGIE:", "RULE:", result, flags=re.MULTILINE)
    result = re.sub(r"^RAISON:", "WHY:", result, flags=re.MULTILINE)
    result = re.sub(r"^EXEMPLE_INVALIDE:", "BAD:", result, flags=re.MULTILINE)
    result = re.sub(r"^EXEMPLE_VALIDE:", "GOOD:", result, flags=re.MULTILINE)
    result = re.sub(r"^ERREUR_ATTENDUE:", "ERROR:", result, flags=re.MULTILINE)
    result = re.sub(r"^ALTERNATIVE:", "INSTEAD:", result, flags=re.MULTILINE)
    result = re.sub(r"^DETECTION_REGEX:", "DETECT:", result, flags=re.MULTILINE)
    return result.strip()


# =============================================================================
# ZONE 0 — SUPPRIMÉE (19 Mars 2026, Pré-Sprint 4.6)
# Les templates de domaine (Todo, Blog, Product, Contact, Item) causaient un planner drift
# documenté : marketplace-mvp → Project/Task, habit-tracker → Workout.
# Le LLM connaît nativement les domaines métier. Le Brief Normalizer remplace cette zone.
# Le RAG doit enseigner uniquement les patterns stack (Next.js, Clerk, Prisma), pas le domaine.
# =============================================================================


# =============================================================================
# ZONE 1 — FICHIERS OBLIGATOIRES + STRUCTURE CANONIQUE
# Source: runs factory empiriques + doc Next.js officielle
# =============================================================================

ZONE_1_REQUIRED_FILES = [
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Next.js 14 App Router — liste des fichiers critiques obligatoires
RAISON: L'absence d'un de ces fichiers cause des erreurs de build fatales ou un fonctionnement incorrect de l'authentification et des tests.
FICHIERS_OBLIGATOIRES:
  app/layout.tsx      — RootLayout (ClerkProvider + html + body obligatoires)
  app/page.tsx        — page d'accueil
  middleware.ts       — à la RACINE du projet (pas dans app/), gestion Clerk
  next.config.js      — configuration Next.js avec eslint.ignoreDuringBuilds
  tsconfig.json       — avec "tests/**" dans exclude
  jest.config.js      — avec next/jest + setupFilesAfterEnv
  jest.setup.js       — import '@testing-library/jest-dom'
  package.json        — JSON valide, versions épinglées
  prisma/schema.prisma — datasource + generator + modèles
  prisma.config.ts    — config Prisma 7 (defineConfig depuis prisma/config)
  .env.local          — NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY + CLERK_SECRET_KEY + DATABASE_URL
FICHIERS_INTERDITS:
  pages/              — conflit fatal avec App Router
  src/pages/          — conflit fatal avec App Router
DETECTION_REGEX: ^pages\/.*\.(tsx?|jsx?)$
ALTERNATIVE: Utiliser uniquement app/ pour les routes.
EXEMPLE_INVALIDE: pages/index.tsx + app/page.tsx coexistent
EXEMPLE_VALIDE: app/page.tsx uniquement, jamais pages/
ERREUR_ATTENDUE: Error: Conflicting app and page file was found
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "1-required-files",
            "status": "active",
            "version": "1.0",
            "category": "nextjs",
            "source": "factory_standards_v2",
            "agent_context": "dev",
        },
    },
]


# =============================================================================
# ZONE 2 — PACKAGE CONFIGURATION
# Source: runs factory + doc officielle + Perplexity
# =============================================================================

ZONE_2_PACKAGES = [
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: package.json — versions épinglées et scripts obligatoires
RAISON: Les versions non épinglées provoquent des incompatibilités entre next/clerk/prisma/ts-jest lors du npm install. ts-jest@29.2+ est incompatible avec ts-jest@29.1.2, d'où l'épinglage exact.
DEPENDENCIES_OBLIGATOIRES:
  "next": "14.2.25"
  "react": "^18.2.0"
  "react-dom": "^18.2.0"
  "@clerk/nextjs": "^6.0.0"
  "prisma": "^7.0.0"
  "@prisma/client": "^7.0.0"
  "typescript": "^5.3.3"
DEV_DEPENDENCIES_OBLIGATOIRES:
  "ts-jest": "29.1.2"         <- version EXACTE, pas de ^
  "jest": "^29.0.0"
  "jest-environment-jsdom": "^29.0.0"
  "@testing-library/jest-dom": "^6.0.0"
  "@testing-library/react": "^14.0.0"
  "node-mocks-http": "^1.14.0"
  "@types/react": "^18.2.0"
  "@types/node": "^20.0.0"
SCRIPTS_OBLIGATOIRES:
  "build": "next build"
  "dev": "next dev"
  "start": "next start"
  "lint": "next lint"
  "test": "jest"
DETECTION_REGEX: "ts-jest":\s*"\^29
ALTERNATIVE: Épingler ts-jest à "29.1.2" sans le préfixe ^
EXEMPLE_INVALIDE: "ts-jest": "^29.0.0"
EXEMPLE_VALIDE: "ts-jest": "29.1.2"
ERREUR_ATTENDUE: TypeError ou incompatibilité silencieuse ts-jest lors des tests
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "2-packages",
            "status": "active",
            "version": "1.0",
            "category": "nextjs",
            "source": "factory_standards_v2",
            "agent_context": "dev",
        },
    },
    {
        "text": """ACTION: INTERDIT
STACK: nextjs-clerk-prisma
TECHNOLOGIE: package.json — packages invalides ou incompatibles avec la stack
RAISON: Ces packages provoquent des erreurs npm, des conflits d'authentification ou violent l'architecture Clerk-exclusive.
PACKAGES_INTERDITS:
  shadcn/ui    — pas un package npm (EINVALIDPACKAGENAME). CLI seulement: npx shadcn@latest init
  @shadcn/ui   — même raison
  next-auth    — conflit direct avec Clerk (auth dupliquée)
  @clerk/clerk-sdk — package Clerk v3, déprécié
  bcrypt       — auth custom INTERDIT (Clerk est exclusif)
  jsonwebtoken — JWT custom INTERDIT (Clerk gère les tokens)
  passport     — auth custom INTERDIT
  express      — incompatible Next.js App Router
DETECTION_REGEX: "shadcn\/ui"|"@shadcn\/ui"|"next-auth"|"bcrypt"|"jsonwebtoken"|"passport"
ALTERNATIVE:
  shadcn/ui → Tailwind CSS pur pour le style
  next-auth → @clerk/nextjs
  bcrypt/jwt/passport → Clerk (zéro auth custom)
EXEMPLE_INVALIDE: "dependencies": { "shadcn/ui": "latest", "bcrypt": "^5.0.0" }
EXEMPLE_VALIDE: Aucun de ces packages dans dependencies ou devDependencies
ERREUR_ATTENDUE: npm ERR! EINVALIDPACKAGENAME ou conflits d'authentification runtime
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "2-packages",
            "status": "active",
            "version": "1.0",
            "category": "nextjs",
            "source": "factory_standards_v2",
            "agent_context": "dev",
        },
    },
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: package.json — format JSON strict
RAISON: npm (EJSONPARSE) rejette tout JSON invalide : commentaires JS, backticks, virgules trailing, texte hors accolades.
DETECTION_REGEX: \/\/.*|`[^`]*`|,\s*\}|\s*,\s*\]
ALTERNATIVE: JSON pur, validé par json.loads() avant écriture
EXEMPLE_INVALIDE:
  {
    // commentaire interdit
    "name": "my-app",
    "version": "1.0.0",   <- virgule trailing
  }
EXEMPLE_VALIDE:
  {
    "name": "my-app",
    "version": "1.0.0"
  }
ERREUR_ATTENDUE: npm ERR! EJSONPARSE position 1
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "2-packages",
            "status": "active",
            "version": "1.0",
            "category": "nextjs",
            "source": "factory_standards_v2",
            "agent_context": "dev",
        },
    },
]


# =============================================================================
# ZONE 3 — TYPESCRIPT CONFIGURATION
# Source: runs factory (TS5070 casing Linux)
# =============================================================================

ZONE_3_TYPESCRIPT = [
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: tsconfig.json — "tests/**" dans exclude
RAISON: Sans "tests/**" dans exclude, Next.js compile les fichiers de test dans le build TypeScript. Sur filesystem Linux case-sensitive (Docker), deux fichiers de test différant uniquement par la casse coexistent → TS5070 fatal.
CONFIGURATION_MINIMALE:
  {
    "compilerOptions": {
      "target": "ES2017",
      "lib": ["dom", "dom.iterable", "esnext"],
      "allowJs": true,
      "skipLibCheck": true,
      "strict": true,
      "noEmit": true,
      "esModuleInterop": true,
      "module": "esnext",
      "moduleResolution": "bundler",
      "resolveJsonModule": true,
      "isolatedModules": true,
      "jsx": "preserve",
      "incremental": true,
      "plugins": [{ "name": "next" }],
      "paths": { "@/*": ["./*"] }
    },
    "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
    "exclude": ["node_modules", "tests/**"]
  }
DETECTION_REGEX: "exclude":\s*\["node_modules"\](?!\s*,\s*"tests)
ALTERNATIVE: Ajouter "tests/**" dans le tableau exclude
EXEMPLE_INVALIDE: "exclude": ["node_modules"]
EXEMPLE_VALIDE: "exclude": ["node_modules", "tests/**"]
ERREUR_ATTENDUE: TS5070 File name 'Layout.test.tsx' differs from already included file name 'layout.test.tsx' only in casing
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "3-typescript",
            "status": "active",
            "version": "1.0",
            "category": "typescript",
            "source": "factory_standards_v2",
            "agent_context": "dev",
        },
    },
]


# =============================================================================
# ZONE 4 — NEXT.JS CONFIGURATION (next.config.js + middleware)
# Source: Perplexity Requête 3 + doc officielle + runs factory
# =============================================================================

ZONE_4_NEXTCONFIG = [
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: next.config.js — eslint.ignoreDuringBuilds pour build en génération automatique
RAISON: Sans eslint.ignoreDuringBuilds: true, le build Next.js échoue sur les erreurs ESLint générées par le LLM. Dans un contexte de génération automatique, c'est obligatoire.
CONFIGURATION_OBLIGATOIRE:
  /** @type {import('next').NextConfig} */
  const nextConfig = {
    reactStrictMode: true,
    eslint: { ignoreDuringBuilds: true },
    typescript: { ignoreBuildErrors: false },
  };
  module.exports = nextConfig;
DETECTION_REGEX: ignoreDuringBuilds
ALTERNATIVE: Ajouter eslint: { ignoreDuringBuilds: true } dans nextConfig
EXEMPLE_INVALIDE:
  const nextConfig = { reactStrictMode: true };
  module.exports = nextConfig;
EXEMPLE_VALIDE:
  const nextConfig = {
    reactStrictMode: true,
    eslint: { ignoreDuringBuilds: true },
  };
  module.exports = nextConfig;
ERREUR_ATTENDUE: Build failed due to ESLint errors (erreurs ESLint bloquant next build)
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "4-nextconfig",
            "status": "active",
            "version": "1.0",
            "category": "nextjs",
            "source": "factory_standards_v2",
            "agent_context": "dev",
        },
    },
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: next.config.js — format correct de la fonction headers()
RAISON: (Perplexity confirmé) Next.js exige que chaque objet dans le tableau retourné par headers() possède un champ `source`. Un tableau plat [{key, value}] sans `source` est invalide.
PATTERN_SOURCE_OFFICIEL: '/:path*' (doc officielle Next.js)
DETECTION_REGEX: headers\s*\(\s*\)\s*\{[\s\S]{0,300}\{\s*key:(?![\s\S]{0,100}source\s*:)
ALTERNATIVE: Wrapper chaque groupe de headers dans un objet { source: '/:path*', headers: [...] }
EXEMPLE_INVALIDE:
  async headers() {
    return [
      { key: 'X-Frame-Options', value: 'DENY' },
    ];
  }
EXEMPLE_VALIDE:
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
        ],
      },
    ];
  }
ERREUR_ATTENDUE: Error: Route headers[0] is missing the 'source' field
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "4-nextconfig",
            "status": "active",
            "version": "1.0",
            "category": "nextjs",
            "source": "factory_standards_v2",
            "agent_context": "dev",
        },
    },
    {
        "text": """ACTION: INTERDIT
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Next.js 14 — pages/ directory avec App Router
RAISON: La coexistence de pages/ et app/ provoque une erreur de build fatale. Next.js 14 App Router utilise exclusivement app/.
DETECTION_REGEX: ^pages\/.*\.(tsx?|jsx?)$
ALTERNATIVE: app/ uniquement pour toutes les routes
EXEMPLE_INVALIDE: pages/index.tsx coexiste avec app/page.tsx
EXEMPLE_VALIDE: app/page.tsx uniquement — aucun fichier dans pages/
ERREUR_ATTENDUE: Error: Conflicting app and page file was found
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "4-nextconfig",
            "status": "active",
            "version": "1.0",
            "category": "nextjs",
            "source": "factory_standards_v2",
            "agent_context": "dev",
        },
    },
    {
        "text": """ACTION: INTERDIT
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Next.js 14 middleware matcher — pattern glob **
RAISON: Le pattern ** dans le matcher cause 'Unexpected MODIFIER'. Next.js middleware utilise la syntaxe regex, pas glob.
DETECTION_REGEX: matcher.*\/\w+\/\*\*
ALTERNATIVE: '/protected/(.*)' au lieu de '/protected/**'
EXEMPLE_INVALIDE:
  export const config = { matcher: ['/protected/**'] }
EXEMPLE_VALIDE:
  export const config = { matcher: ['/protected/(.*)'] }
ERREUR_ATTENDUE: SyntaxError: Unexpected MODIFIER at position X
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "4-nextconfig",
            "status": "active",
            "version": "1.0",
            "category": "nextjs",
            "source": "factory_standards_v2",
            "agent_context": "dev",
        },
    },
]


# =============================================================================
# ZONE 5 — APP ROUTER LAYOUT
# Source: Perplexity Requête 1 + runs factory empiriques
# =============================================================================

ZONE_5_LAYOUT = [
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: app/layout.tsx — structure canonique App Router avec Clerk v6
RAISON: (Perplexity + doc Next.js) Le Root Layout DOIT retourner un arbre HTML complet. ClerkProvider DOIT wrapper l'extérieur de <html> pour couvrir toutes les routes. Sans html+body, comportements inattendus (styles, metadata, scripts). Sans ClerkProvider au root, les composants Clerk lancent des erreurs runtime sur les routes non couvertes.
PLACEMENT_CLERKPROVIDER: À l'extérieur de <html> (wrapping tout le document)
DETECTION_REGEX: export default function.*Layout(?![\s\S]{0,500}<ClerkProvider)
ALTERNATIVE: ClerkProvider → html lang="en" → body → {children}
EXEMPLE_INVALIDE:
  export default function RootLayout({ children }) {
    return (
      <html lang="en">
        <body>{children}</body>
      </html>
    );
    // Manque ClerkProvider → useUser/useAuth échouent
  }
EXEMPLE_VALIDE:
  import { ClerkProvider } from '@clerk/nextjs';
  export const dynamic = "force-dynamic";

  export default function RootLayout({ children }: { children: React.ReactNode }) {
    return (
      <ClerkProvider>
        <html lang="en">
          <body>{children}</body>
        </html>
      </ClerkProvider>
    );
  }
ERREUR_ATTENDUE: Error: <Clerk> is not a valid component or ClerkProvider missing
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "5-layout",
            "status": "active",
            "version": "1.0",
            "category": "nextjs",
            "type": "policy",
            "source": "factory_standards_v2",
            "agent_context": "dev",
        },
    },
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: app/layout.tsx — export const dynamic = 'force-dynamic'
RAISON: Next.js 14 pré-rend statiquement toutes les pages au build. ClerkProvider s'initialise pendant ce prerender et lève une exception si NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY est un placeholder (valeur de dev). force-dynamic désactive la génération statique — Clerk n'est initialisé qu'à runtime avec de vraies credentials.
DETECTION_REGEX: ClerkProvider(?![\s\S]{0,400}export const dynamic)
ALTERNATIVE: Ajouter 'export const dynamic = "force-dynamic"' après les imports
EXEMPLE_INVALIDE:
  import { ClerkProvider } from '@clerk/nextjs';
  export default function RootLayout({ children }) {
    return (<ClerkProvider><html lang="en"><body>{children}</body></html></ClerkProvider>);
  }
  // Manque force-dynamic → ClerkProvider crash au build avec placeholder key
EXEMPLE_VALIDE:
  import { ClerkProvider } from '@clerk/nextjs';
  export const dynamic = "force-dynamic";
  export default function RootLayout({ children }) {
    return (<ClerkProvider><html lang="en"><body>{children}</body></html></ClerkProvider>);
  }
ERREUR_ATTENDUE: Error: @clerk/nextjs: Missing or invalid publishableKey during static prerender
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "5-layout",
            "status": "active",
            "version": "1.0",
            "category": "nextjs",
            "type": "policy",
            "source": "factory_standards_v2",
            "agent_context": "dev",
        },
    },
]


# =============================================================================
# ZONE 6 — AUTHENTIFICATION CLERK v6 (breaking changes v5→v6)
# Source: Perplexity Requête 4 + create_sprint2 validés empiriquement
# =============================================================================

ZONE_6_CLERK = [
    {
        "text": """ACTION: INTERDIT
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Clerk v6 — authMiddleware déprécié
RAISON: (Perplexity confirmé) authMiddleware importé de @clerk/nextjs est supprimé en v6. Cause Module Not Found ou comportement incorrect au runtime.
DETECTION_REGEX: authMiddleware|from\s+['"]@clerk\/nextjs['"].*authMiddleware
ALTERNATIVE: clerkMiddleware + createRouteMatcher depuis @clerk/nextjs/server
EXEMPLE_INVALIDE:
  import { authMiddleware } from '@clerk/nextjs';
  export default authMiddleware({
    publicRoutes: ['/', '/sign-in', '/sign-up'],
  });
EXEMPLE_VALIDE:
  import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server';
  const isPublicRoute = createRouteMatcher(['/', '/sign-in(.*)', '/sign-up(.*)']);
  export default clerkMiddleware(async (auth, request) => {
    if (!isPublicRoute(request)) await auth.protect();
  });
ERREUR_ATTENDUE: Error: authMiddleware is not exported from @clerk/nextjs (v6)
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "6-clerk",
            "status": "active",
            "version": "1.0",
            "category": "clerk",
            "source": "factory_standards_v2",
            "agent_context": "dev",
        },
    },
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Clerk v6 middleware.ts — clerkMiddleware async + auth.protect()
RAISON: (Perplexity confirmé) Clerk v6 : dans clerkMiddleware, auth est un OBJET injecté (pas une fonction). auth().protect() est invalide. Le callback DOIT être async pour utiliser await auth.protect().
DETECTION_REGEX: auth\(\)\.protect\(\)|clerkMiddleware\(\s*\(auth,\s*req\)\s*=>(?!\s*async)
ALTERNATIVE: clerkMiddleware(async (auth, request) => { await auth.protect(); })
EXEMPLE_INVALIDE:
  export default clerkMiddleware((auth, req) => {
    if (!isPublicRoute(req)) auth().protect();  // DOUBLE erreur: sync + auth()
  });
EXEMPLE_VALIDE:
  import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server';
  const isPublicRoute = createRouteMatcher(['/sign-in(.*)', '/sign-up(.*)']);
  export default clerkMiddleware(async (auth, request) => {
    if (!isPublicRoute(request)) await auth.protect();
  });
ERREUR_ATTENDUE: TypeError: auth is not a function | SyntaxError: await only valid in async
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "6-clerk",
            "status": "active",
            "version": "1.0",
            "category": "clerk",
            "source": "factory_standards_v2",
            "agent_context": "dev",
        },
    },
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Clerk v6 — auth() async dans Server Components et API Routes
RAISON: (Perplexity confirmé) Clerk v6 : auth() retourne une Promise. Un appel synchrone cause TypeError ou retourne undefined silencieusement, exposant des données sans auth.
DETECTION_REGEX: const\s*\{.*userId.*\}\s*=\s*auth\(\)(?!\s*;.*await|.*\.then)
ALTERNATIVE: const { userId } = await auth(); dans une fonction async
EXEMPLE_INVALIDE:
  export default function Page() {
    const { userId } = auth();  // sync → INTERDIT Clerk v6
    return <div>{userId}</div>;
  }
EXEMPLE_VALIDE:
  import { auth } from '@clerk/nextjs/server';
  export default async function Page() {
    const { userId } = await auth();  // async → correct Clerk v6
    return <div>{userId}</div>;
  }
ERREUR_ATTENDUE: TypeError: Cannot destructure property 'userId' of undefined
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "6-clerk",
            "status": "active",
            "version": "1.0",
            "category": "clerk",
            "source": "factory_standards_v2",
            "agent_context": "dev",
        },
    },
    {
        "text": """ACTION: INTERDIT
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Clerk v6 — imports server depuis @clerk/nextjs (sans /server)
RAISON: (Perplexity confirmé) Clerk v6 sépare clairement : @clerk/nextjs pour les client components (UserButton, SignIn, useUser), @clerk/nextjs/server pour le code serveur (auth, currentUser, clerkMiddleware). Mélanger cause des erreurs de module ou des fuites server→client.
DETECTION_REGEX: import\s*\{.*\b(auth|currentUser|clerkMiddleware|createRouteMatcher)\b.*\}\s*from\s*['"]@clerk\/nextjs['"](?!\/server)
ALTERNATIVE:
  Client: import { useUser, UserButton, ClerkProvider } from '@clerk/nextjs'
  Serveur: import { auth, currentUser, clerkMiddleware } from '@clerk/nextjs/server'
EXEMPLE_INVALIDE: import { auth } from '@clerk/nextjs'  // server fn depuis le mauvais path
EXEMPLE_VALIDE: import { auth } from '@clerk/nextjs/server'
ERREUR_ATTENDUE: Module not found ou erreur "server-only" boundary violation
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "6-clerk",
            "status": "active",
            "version": "1.0",
            "category": "clerk",
            "source": "factory_standards_v2",
            "agent_context": "dev",
        },
    },
    {
        "text": """ACTION: INTERDIT
STACK: nextjs-clerk-prisma
TECHNOLOGIE: @clerk/nextjs/api — sous-path supprimé
RAISON: Le sous-path @clerk/nextjs/api est supprimé depuis Clerk v5. Tous les imports serveur doivent venir de @clerk/nextjs/server.
DETECTION_REGEX: from\s+['"]@clerk\/nextjs\/api['"]
ALTERNATIVE: import { auth, currentUser } from '@clerk/nextjs/server'
EXEMPLE_INVALIDE: import { auth } from '@clerk/nextjs/api'
EXEMPLE_VALIDE: import { auth } from '@clerk/nextjs/server'
ERREUR_ATTENDUE: Module not found: Can't resolve '@clerk/nextjs/api'
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "6-clerk",
            "status": "active",
            "version": "1.0",
            "category": "clerk",
            "source": "factory_standards_v2",
            "agent_context": "dev",
        },
    },
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Clerk v6 — distinction auth() selon le contexte d'exécution
RAISON: (Perplexity confirmé) auth() est utilisé DIFFÉREMMENT selon le contexte. Dans middleware.ts, auth est un OBJET injecté par clerkMiddleware — appeler auth() est INTERDIT. Dans les Server Components et Route Handlers, auth() est une FONCTION async à appeler avec await. Confondre les deux contextes provoque TypeError runtime.
CONTEXTE_MIDDLEWARE:
  auth = OBJET injecté par clerkMiddleware
  CORRECT: await auth.protect()
  INTERDIT: auth().protect() → TypeError: auth is not a function
CONTEXTE_SERVER_COMPONENTS_ET_ROUTE_HANDLERS:
  auth() = FONCTION async importée depuis @clerk/nextjs/server
  CORRECT: const { userId } = await auth()
  INCORRECT: const { userId } = auth() → retourne Promise non résolue
DETECTION_REGEX: auth\(\)\.protect\(\)
ALTERNATIVE:
  middleware.ts → await auth.protect()
  server components/routes → const { userId } = await auth()
EXEMPLE_INVALIDE:
  // Dans middleware.ts (auth est un objet, pas une fonction)
  export default clerkMiddleware((auth, req) => {
    auth().protect();  // ERREUR: auth is not a function
  });
EXEMPLE_VALIDE:
  // Dans middleware.ts
  export default clerkMiddleware(async (auth, req) => {
    await auth.protect();  // CORRECT
  });
  // Dans un Server Component ou Route Handler
  import { auth } from '@clerk/nextjs/server';
  export async function GET() {
    const { userId } = await auth();  // CORRECT
    if (!userId) return new Response('Unauthorized', { status: 401 });
  }
ERREUR_ATTENDUE: TypeError: auth is not a function (middleware) | Promise<...> retourné au lieu de userId (server)
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "6-clerk",
            "status": "active",
            "version": "1.0",
            "category": "clerk",
            "type": "technical",
            "source": "factory_standards_v2",
            "agent_context": "dev",
        },
    },
]


# =============================================================================
# ZONE 7 — BASE DE DONNÉES PRISMA 7
# Source: Perplexity Requête 5 (prisma.config.ts + schema.prisma)
# =============================================================================

ZONE_7_PRISMA = [
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Prisma 7 — générer schema.prisma ET prisma.config.ts
RAISON: (Perplexity confirmé) Prisma 7 introduit prisma.config.ts. La datasource URL doit être portée par prisma.config.ts ; `url = env("DATABASE_URL")` dans schema.prisma doit être évité/retiré pour rester aligné avec la config moderne de la stack.
FICHIERS_OBLIGATOIRES:
  prisma/schema.prisma  — datasource + generator + modèles
  prisma.config.ts      — defineConfig depuis 'prisma/config'
CONFIGURATION_SCHEMA_PRISMA:
  datasource db {
    provider = "postgresql"
  }
  generator client {
    provider = "prisma-client-js"
  }
CONFIGURATION_PRISMA_CONFIG_TS:
  import 'dotenv/config';
  import { defineConfig, env } from 'prisma/config';
  export default defineConfig({
    schema: 'prisma/schema.prisma',
    datasource: { url: env('DATABASE_URL') },
  });
DETECTION_REGEX: prisma\.config\.ts
ALTERNATIVE: Générer les deux fichiers systématiquement
EXEMPLE_INVALIDE: schema.prisma seul sans prisma.config.ts
EXEMPLE_VALIDE: prisma/schema.prisma + prisma.config.ts à la racine
ERREUR_ATTENDUE: Écart de configuration Prisma 7 (datasource URL au mauvais endroit)
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "7-prisma",
            "status": "active",
            "version": "1.0",
            "category": "prisma",
            "source": "factory_standards_v2",
            "agent_context": "dev",
        },
    },
    {
        "text": """ACTION: INTERDIT
STACK: nextjs-clerk-prisma
TECHNOLOGIE: schema.prisma — champ password avec Clerk
RAISON: Clerk gère l'authentification entièrement. Un champ password dans Prisma est redondant, dangereux, et architecturalement incorrect avec Clerk.
DETECTION_REGEX: \bpassword\s+String|\bpassword_hash\s+String|\bpasswordHash\s+String
ALTERNATIVE: clerkId String @unique comme seul lien d'auth
EXEMPLE_INVALIDE:
  model User {
    id       String @id @default(cuid())
    password String                        <- INTERDIT avec Clerk
    clerkId  String @unique
  }
EXEMPLE_VALIDE:
  model User {
    id        String   @id @default(cuid())
    clerkId   String   @unique
    email     String   @unique
    createdAt DateTime @default(now())
    updatedAt DateTime @updatedAt
  }
ERREUR_ATTENDUE: Faille sécurité — champ password inutilisé ou non chiffré
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "7-prisma",
            "status": "active",
            "version": "1.0",
            "category": "prisma",
            "source": "factory_standards_v2",
            "agent_context": "dev",
        },
    },
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: schema.prisma — champs createdAt/updatedAt sur chaque modèle
RAISON: Sans createdAt/updatedAt, il est impossible de trier, auditer ou paginer les données. Convention obligatoire dans tous les projets factory.
DETECTION_REGEX: ^model \w+ \{(?![\s\S]{0,400}createdAt)
ALTERNATIVE: Ajouter createdAt DateTime @default(now()) et updatedAt DateTime @updatedAt
EXEMPLE_INVALIDE:
  model Task {
    id    String @id @default(cuid())
    title String
  }
EXEMPLE_VALIDE:
  model Task {
    id        String   @id @default(cuid())
    title     String
    authorId  String
    createdAt DateTime @default(now())
    updatedAt DateTime @updatedAt
  }
ERREUR_ATTENDUE: Données sans traçabilité temporelle (pas d'erreur de build, mais violation architecture)
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "7-prisma",
            "status": "active",
            "version": "1.0",
            "category": "prisma",
            "source": "factory_standards_v2",
            "agent_context": "dev",
        },
    },
]


# =============================================================================
# ZONE 8 — TESTS JEST 29
# Source: Perplexity Requête 2 (next/jest officiel + setupFilesAfterEnv)
# =============================================================================

ZONE_8_TESTING = [
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: jest.config.js — preset next/jest (officiel Next.js 14)
RAISON: (Perplexity + doc Next.js officielle) Le preset recommandé pour Next.js 14 est next/jest via createJestConfig, pas ts-jest directement comme preset. next/jest supporte nativement App Router, aliases @/, et la résolution des imports Next.
FORMAT_OBLIGATOIRE:
  const nextJest = require('next/jest');
  const createJestConfig = nextJest({ dir: './' });
  const config = {
    testEnvironment: 'jsdom',
    setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
    moduleNameMapper: { '^@/(.*)$': '<rootDir>/$1' },
  };
  module.exports = createJestConfig(config);
DETECTION_REGEX: preset:\s*['"]ts-jest['"](?![\s\S]{0,200}createJestConfig)
ALTERNATIVE: Utiliser next/jest comme wrapper, ts-jest reste en devDependency mais pas comme preset
EXEMPLE_INVALIDE:
  module.exports = {
    preset: 'ts-jest',
    testEnvironment: 'jsdom',
  };
EXEMPLE_VALIDE:
  const nextJest = require('next/jest');
  const createJestConfig = nextJest({ dir: './' });
  module.exports = createJestConfig({
    testEnvironment: 'jsdom',
    setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
    moduleNameMapper: { '^@/(.*)$': '<rootDir>/$1' },
  });
ERREUR_ATTENDUE: Cannot find module '@/' ou erreurs de résolution App Router
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "8-testing",
            "status": "active",
            "version": "1.0",
            "category": "testing",
            "source": "factory_standards_v2",
            "agent_context": "dev",
        },
    },
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: jest.config.js — setupFilesAfterEnv (clé correcte)
RAISON: (Perplexity confirmé) setupFilesAfterEnv est la clé correcte Jest 29 pour charger @testing-library/jest-dom après l'environnement de test. setupFiles (sans AfterEnv) s'exécute avant l'environnement → matchers non disponibles. setupFilesAfterFramework n'existe pas dans Jest 29.
DETECTION_REGEX: setupFiles(?!AfterEnv)|setupFilesAfterFramework
ALTERNATIVE: setupFilesAfterEnv: ['<rootDir>/jest.setup.js']
EXEMPLE_INVALIDE:
  setupFiles: ['<rootDir>/jest.setup.js']           // trop tôt
  setupFilesAfterFramework: ['<rootDir>/jest.setup.js'] // clé inexistante
EXEMPLE_VALIDE:
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js']
ERREUR_ATTENDUE: TypeError: expect(...).toBeInTheDocument is not a function
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "8-testing",
            "status": "active",
            "version": "1.0",
            "category": "testing",
            "source": "factory_standards_v2",
            "agent_context": "dev",
        },
    },
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: jest.setup.js — import @testing-library/jest-dom
RAISON: (Perplexity confirmé) jest.setup.js doit importer @testing-library/jest-dom pour enregistrer les matchers (toBeInTheDocument, toHaveTextContent, etc.) avant chaque test.
DETECTION_REGEX: ^(?!.*@testing-library\/jest-dom)
ALTERNATIVE: Créer jest.setup.js avec une seule ligne d'import
EXEMPLE_INVALIDE: jest.setup.js vide ou absent
EXEMPLE_VALIDE:
  import '@testing-library/jest-dom';
ERREUR_ATTENDUE: TypeError: expect(...).toBeInTheDocument is not a function
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "8-testing",
            "status": "active",
            "version": "1.0",
            "category": "testing",
            "source": "factory_standards_v2",
            "agent_context": "dev",
        },
    },
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Tests React — mock @clerk/nextjs obligatoire
RAISON: Les composants utilisant useAuth, useUser, ClerkProvider échouent sans mock car Clerk tente de s'initialiser avec de vraies credentials absentes en test.
DETECTION_REGEX: (useAuth|useUser|ClerkProvider)(?![\s\S]{0,500}jest\.mock.*@clerk)
ALTERNATIVE: jest.mock('@clerk/nextjs', ...) au début de chaque fichier de test React
EXEMPLE_INVALIDE:
  import { useAuth } from '@clerk/nextjs';
  // Pas de jest.mock → Error: Missing publishableKey
EXEMPLE_VALIDE:
  jest.mock('@clerk/nextjs', () => ({
    useAuth: () => ({ userId: 'test-user-id', isLoaded: true, isSignedIn: true }),
    useUser: () => ({ user: { id: 'test-user-id', emailAddresses: [{ emailAddress: 'test@test.com' }] } }),
    ClerkProvider: ({ children }: any) => children,
  }));
ERREUR_ATTENDUE: Error: @clerk/nextjs: Missing publishableKey
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "8-testing",
            "status": "active",
            "version": "1.0",
            "category": "testing",
            "source": "factory_standards_v2",
            "agent_context": "dev",
        },
    },
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Tests API Routes — node-mocks-http dans devDependencies
RAISON: Tester les Route Handlers Next.js nécessite des objets Request/Response mockés. node-mocks-http fournit ces mocks compatibles.
DETECTION_REGEX: devDependencies(?![\s\S]{0,800}node-mocks-http)
ALTERNATIVE: "node-mocks-http": "^1.14.0" dans devDependencies
EXEMPLE_INVALIDE: package.json sans node-mocks-http
EXEMPLE_VALIDE: "node-mocks-http": "^1.14.0" dans devDependencies
ERREUR_ATTENDUE: ReferenceError: Request is not defined dans les tests API
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "8-testing",
            "status": "active",
            "version": "1.0",
            "category": "testing",
            "source": "factory_standards_v2",
            "agent_context": "dev",
        },
    },
]


# =============================================================================
# ZONE 9 — SÉCURITÉ
# Source: OWASP + runs factory + doc Clerk
# =============================================================================

ZONE_9_SECURITY = [
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: API Routes — null check userId obligatoire avant toute opération Prisma avec authorId
RAISON_TYPESCRIPT: Clerk V6 auth() retourne { userId: string | null } — breaking change depuis Clerk V5 où userId était string. Prisma schema : authorId String (non-nullable). Passer string | null à un champ String Prisma = ERREUR TypeScript à la compilation, pas au runtime. Le null check if (!userId) effectue un TypeScript type narrowing : string | null devient string garanti — Prisma accepte. SANS ce narrowing, TypeScript refuse de compiler.
RAISON_SECURITE: Sans vérification userId, les routes API sont accessibles sans authentification.
ERREUR_TYPESCRIPT_EXACTE: Type 'string | null' is not assignable to type 'string'. Type 'null' is not assignable to type 'string'.
NULL_CHECK_VALIDES:
  if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  if (userId === null) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
PATTERN_AUTHORID_CORRECT:
  GET/DELETE : where: { authorId: userId }   — userId narrowé = string garanti
  POST/PUT   : data: { authorId: userId, ... } — userId narrowé = string garanti
  INTERDIT   : where: { userId }              — champ userId n'existe pas dans le modèle Prisma
EXEMPLE_INVALIDE:
  export async function POST(req: Request) {
    const { userId } = await auth();
    // userId est string | null ici — pas de narrowing
    const body = await req.json();
    await prisma.task.create({ data: { ...body, authorId: userId } });
    // ERREUR TypeScript: string | null n'est pas assignable à String (Prisma)
  }
EXEMPLE_VALIDE:
  import { auth } from '@clerk/nextjs/server';
  export async function GET(req: Request) {
    const { userId } = await auth();
    if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    // userId est string ici (narrowé) — Prisma accepte authorId: userId
    const data = await prisma.task.findMany({ where: { authorId: userId } });
    return NextResponse.json(data);
  }
  export async function POST(req: Request) {
    const { userId } = await auth();
    if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    const body = await req.json();
    await prisma.task.create({ data: { ...body, authorId: userId } });
    return NextResponse.json({ success: true }, { status: 201 });
  }
ERREUR_ATTENDUE: Type error: Type 'string | null' is not assignable to type 'string' (compilation Next.js build)
STATUS: active
VERSION: 2.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "9-security",
            "status": "active",
            "version": "1.0",
            "category": "security",
            "source": "factory_standards_v2",
            "agent_context": "dev",
        },
    },
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: API Routes POST/PUT/PATCH — validation Zod obligatoire
RAISON: Sans validation Zod, les entrées non validées provoquent des erreurs Prisma, des injections ou des crashs non gérés.
DETECTION_REGEX: export async function (POST|PUT|PATCH)(?![\s\S]{0,600}z\.(object|string|number|array))
ALTERNATIVE: Définir un schema Zod et utiliser .safeParse() avant toute opération Prisma
EXEMPLE_INVALIDE:
  export async function POST(req: Request) {
    const body = await req.json();
    await prisma.task.create({ data: body });  // Non validé
  }
EXEMPLE_VALIDE:
  const CreateTaskSchema = z.object({ title: z.string().min(1).max(255) });
  export async function POST(req: Request) {
    const body = await req.json();
    const result = CreateTaskSchema.safeParse(body);
    if (!result.success) return NextResponse.json({ error: result.error }, { status: 400 });
    await prisma.task.create({ data: result.data });
  }
ERREUR_ATTENDUE: PrismaClientValidationError ou données corrompues
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "9-security",
            "status": "active",
            "version": "1.0",
            "category": "security",
            "source": "factory_standards_v2",
            "agent_context": "dev",
        },
    },
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: .env.local — contenu obligatoire (Clerk + Database)
RAISON: Sans NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY, ClerkProvider crash au runtime (Missing publishableKey). Sans CLERK_SECRET_KEY, tous les appels serveur Clerk échouent (401 Unauthorized). Sans DATABASE_URL, Prisma ne peut pas se connecter à la base.
CONTENU_OBLIGATOIRE:
  NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_placeholder
  CLERK_SECRET_KEY=sk_test_placeholder
  DATABASE_URL="postgresql://user:password@localhost:5432/todo-batch-alpha"
DETECTION_REGEX: ^NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=
ALTERNATIVE: Créer .env.local à la RACINE du projet avec les 3 variables exactes
EXEMPLE_INVALIDE:
  DATABASE_URL="postgresql://..."
  # Manque NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY → ClerkProvider crash runtime
  # Manque CLERK_SECRET_KEY → auth() serveur → 401
EXEMPLE_VALIDE:
  NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_placeholder
  CLERK_SECRET_KEY=sk_test_placeholder
  DATABASE_URL="postgresql://user:password@localhost:5432/todo-batch-alpha"
ERREUR_ATTENDUE: Error: @clerk/nextjs: Missing publishableKey
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "9-security",
            "status": "active",
            "version": "1.0",
            "category": "security",
            "source": "factory_standards_v2",
            "agent_context": "dev",
        },
    },
    {
        "text": """ACTION: INTERDIT
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Variables d'environnement — secrets avec préfixe NEXT_PUBLIC_
RAISON: Les variables avec NEXT_PUBLIC_ sont exposées dans le bundle JavaScript client. CLERK_SECRET_KEY et DATABASE_URL exposés = faille critique.
DETECTION_REGEX: NEXT_PUBLIC_CLERK_SECRET_KEY|NEXT_PUBLIC_DATABASE_URL
ALTERNATIVE: CLERK_SECRET_KEY et DATABASE_URL sans préfixe (serveur uniquement)
EXEMPLE_INVALIDE:
  NEXT_PUBLIC_CLERK_SECRET_KEY=sk_test_xxx    <- exposé au client
  NEXT_PUBLIC_DATABASE_URL=postgresql://...   <- exposé au client
EXEMPLE_VALIDE:
  NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_xxx  <- public OK
  CLERK_SECRET_KEY=sk_test_xxx                   <- privé OK
  DATABASE_URL=postgresql://...                  <- privé OK
ERREUR_ATTENDUE: Fuite de secrets dans le bundle JavaScript client
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "9-security",
            "status": "active",
            "version": "1.0",
            "category": "security",
            "source": "factory_standards_v2",
            "agent_context": "dev",
        },
    },
]


# =============================================================================
# ZONE 10 — SÉCURITÉ AVANCÉE (Session 1 — AI-generated, validé Claude)
# Source: AI-generated 2026-03-05, validé par Claude Code
# Couvre: auth patterns avancés, IDOR, userId spoofing, force-dynamic
# =============================================================================

ZONE_10_SECURITY_ADVANCED = [
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: @clerk/nextjs/server — auth() dans Route Handlers
RAISON: Sans vérification auth(), n'importe quel client non authentifié peut appeler la route et accéder aux données — fuite de données garantie.
DETECTION_REGEX: export async function (GET|POST|PUT|DELETE|PATCH)\s*\([^)]*\)\s*\{(?![^}]*auth\(\))
ALTERNATIVE: Appeler auth() en premier et vérifier userId avant tout accès Prisma
EXEMPLE_INVALIDE:
  // app/api/posts/route.ts
  import prisma from '@/lib/prisma';
  import { NextResponse } from 'next/server';

  export async function GET() {
    const posts = await prisma.post.findMany();
    return NextResponse.json(posts);
  }
EXEMPLE_VALIDE:
  // app/api/posts/route.ts
  import { auth } from '@clerk/nextjs/server';
  import prisma from '@/lib/prisma';
  import { NextResponse } from 'next/server';

  export async function GET() {
    const { userId } = await auth();
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    const posts = await prisma.post.findMany({ where: { authorId: userId } });
    return NextResponse.json(posts);
  }
ERREUR_ATTENDUE: N/A (pas d'erreur build — faille silencieuse à l'exécution)
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "10-security-advanced",
            "status": "active",
            "version": "1.0",
            "category": "security",
            "source": "session1-ai-validated",
            "agent_context": "dev",
        },
    },
    {
        "text": """ACTION: INTERDIT
STACK: nextjs-clerk-prisma
TECHNOLOGIE: @clerk/nextjs — useAuth() dans Route Handlers
RAISON: useAuth() est un hook React Client-side — l'appeler dans un Route Handler (contexte serveur) lève une exception et crashe la route entière.
DETECTION_REGEX: import\s*\{[^}]*useAuth[^}]*\}\s*from\s*['"]@clerk/nextjs['"]
ALTERNATIVE: Utiliser auth() depuis @clerk/nextjs/server dans les Route Handlers
EXEMPLE_INVALIDE:
  // app/api/profile/route.ts
  import { useAuth } from '@clerk/nextjs';
  import { NextResponse } from 'next/server';

  export async function GET() {
    const { userId } = useAuth(); // hook dans contexte serveur
    return NextResponse.json({ userId });
  }
EXEMPLE_VALIDE:
  // app/api/profile/route.ts
  import { auth } from '@clerk/nextjs/server';
  import { NextResponse } from 'next/server';

  export async function GET() {
    const { userId } = await auth();
    if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    return NextResponse.json({ userId });
  }
ERREUR_ATTENDUE: Error: (0 , _clerk_nextjs__WEBPACK_IMPORTED_MODULE_0__.useAuth) is not a function — ou — Invalid hook call. Hooks can only be called inside of the body of a function component.
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "10-security-advanced",
            "status": "active",
            "version": "1.0",
            "category": "security",
            "source": "session1-ai-validated",
            "agent_context": "dev",
        },
    },
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Next.js App Router — Route Handlers dynamiques avec auth
RAISON: Un Route Handler avec auth() qui n'est pas marqué dynamic peut être statiquement prérendu par Next.js, rendant auth() inaccessible au build.
DETECTION_REGEX: ^(?!.*export const dynamic).*export async function (GET|POST|PUT|DELETE).*auth\(\)
ALTERNATIVE: Ajouter export const dynamic = "force-dynamic" dans tout Route Handler qui appelle auth()
EXEMPLE_INVALIDE:
  // app/api/user/route.ts
  import { auth } from '@clerk/nextjs/server';
  import { NextResponse } from 'next/server';

  // pas de export const dynamic
  export async function GET() {
    const { userId } = await auth();
    return NextResponse.json({ userId });
  }
EXEMPLE_VALIDE:
  // app/api/user/route.ts
  import { auth } from '@clerk/nextjs/server';
  import { NextResponse } from 'next/server';

  export const dynamic = 'force-dynamic';

  export async function GET() {
    const { userId } = await auth();
    if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    return NextResponse.json({ userId });
  }
ERREUR_ATTENDUE: Error: Route /api/user with dynamic = "auto" couldn't be rendered statically because it used `headers`.
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "10-security-advanced",
            "status": "active",
            "version": "1.0",
            "category": "security",
            "source": "session1-ai-validated",
            "agent_context": "dev",
        },
    },
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Next.js App Router — ownership check Prisma (IDOR prevention)
RAISON: Vérifier uniquement userId !== null ne suffit pas — un utilisateur authentifié peut modifier les ressources d'un autre utilisateur en passant un ID arbitraire dans l'URL (IDOR — Insecure Direct Object Reference).
DETECTION_REGEX: prisma\.\w+\.(update|delete|findUnique)\(\s*\{[^}]*where[^}]*id[^}]*\}
ALTERNATIVE: Toujours inclure { id: params.id, authorId: userId } dans le where de toute mutation Prisma sur ressource utilisateur
EXEMPLE_INVALIDE:
  // app/api/posts/[id]/route.ts
  export async function DELETE(req: Request, { params }: { params: { id: string } }) {
    const { userId } = await auth();
    if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

    // n'importe quel user authentifié peut supprimer n'importe quel post
    await prisma.post.delete({ where: { id: params.id } });
    return NextResponse.json({ success: true });
  }
EXEMPLE_VALIDE:
  // app/api/posts/[id]/route.ts
  export async function DELETE(req: Request, { params }: { params: { id: string } }) {
    const { userId } = await auth();
    if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

    // double contrainte : id ET propriétaire
    const deleted = await prisma.post.deleteMany({
      where: { id: params.id, authorId: userId },
    });
    if (deleted.count === 0) {
      return NextResponse.json({ error: 'Not found or forbidden' }, { status: 404 });
    }
    return NextResponse.json({ success: true });
  }
ERREUR_ATTENDUE: N/A (faille silencieuse — pas d'erreur build ni runtime)
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "10-security-advanced",
            "status": "active",
            "version": "1.0",
            "category": "security",
            "source": "session1-ai-validated",
            "agent_context": "dev",
        },
    },
    {
        "text": """ACTION: INTERDIT
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Next.js App Router — lecture userId depuis le body/query params
RAISON: Faire confiance à un userId envoyé par le client permet à n'importe qui d'usurper l'identité d'un autre utilisateur en falsifiant le paramètre.
DETECTION_REGEX: (body|params|searchParams)\.(userId|user_id|clerkId)
ALTERNATIVE: Toujours extraire userId depuis await auth() côté serveur, jamais depuis req.body ou les query params
EXEMPLE_INVALIDE:
  // app/api/profile/route.ts
  export async function PUT(req: Request) {
    const { userId, name } = await req.json(); // userId vient du client
    await prisma.user.update({
      where: { clerkId: userId },
      data: { name },
    });
    return NextResponse.json({ success: true });
  }
EXEMPLE_VALIDE:
  // app/api/profile/route.ts
  export async function PUT(req: Request) {
    const { userId } = await auth(); // userId depuis Clerk, pas le client
    if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

    const { name } = await req.json(); // seules les données métier viennent du body
    await prisma.user.update({
      where: { clerkId: userId },
      data: { name },
    });
    return NextResponse.json({ success: true });
  }
ERREUR_ATTENDUE: N/A (faille silencieuse de sécurité)
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "10-security-advanced",
            "status": "active",
            "version": "1.0",
            "category": "security",
            "source": "session1-ai-validated",
            "agent_context": "dev",
        },
    },
]


# =============================================================================
# AGRÉGATION COMPLÈTE
# =============================================================================

# =============================================================================
# ZONE 11 — GESTION D'ERREURS PRISMA + API (Session 2 — AI-generated, validé Claude)
# Source: AI-generated 2026-03-05, validé par Claude Code
# Couvre: PrismaClientKnownRequestError, exposition erreurs, null check, validation Zod
# =============================================================================

ZONE_11_ERROR_HANDLING = [
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Prisma — gestion PrismaClientKnownRequestError
RAISON: Sans catch Prisma typé, une violation de contrainte unique (email déjà pris) retourne une 500 non informative au lieu d'une 409 Conflict — et expose le stack trace interne au client.
DETECTION_REGEX: prisma\.\w+\.(create|update|upsert)\((?![\s\S]*catch[\s\S]*PrismaClientKnownRequestError)
ALTERNATIVE: Importer PrismaClientKnownRequestError et distinguer P2002 (unique constraint) des autres erreurs
EXEMPLE_INVALIDE:
  // app/api/users/route.ts
  export async function POST(req: Request) {
    const { email, clerkId } = await req.json();
    const user = await prisma.user.create({ // pas de gestion d'erreur Prisma
      data: { email, clerkId },
    });
    return NextResponse.json(user);
  }
EXEMPLE_VALIDE:
  // app/api/users/route.ts
  import { Prisma } from '@prisma/client';

  export async function POST(req: Request) {
    const { email, clerkId } = await req.json();
    try {
      const user = await prisma.user.create({ data: { email, clerkId } });
      return NextResponse.json(user, { status: 201 });
    } catch (error) {
      if (error instanceof Prisma.PrismaClientKnownRequestError) {
        if (error.code === 'P2002') {
          return NextResponse.json({ error: 'Email already exists' }, { status: 409 });
        }
      }
      console.error('[POST /api/users]', error);
      return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
    }
  }
ERREUR_ATTENDUE: PrismaClientKnownRequestError: Unique constraint failed on the fields: (`email`)
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "11-error-handling",
            "status": "active",
            "version": "1.0",
            "category": "error-handling",
            "source": "session2-ai-validated",
            "agent_context": "dev",
        },
    },
    {
        "text": """ACTION: INTERDIT
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Next.js App Router — exposition du message d'erreur Prisma brut
RAISON: Retourner error.message directement expose le schéma de base de données, les noms de tables et les contraintes — vecteur d'attaque par énumération.
DETECTION_REGEX: NextResponse\.json\(\{\s*error:\s*(?:error|err|e)\.message
ALTERNATIVE: Logger l'erreur côté serveur (console.error), retourner un message générique au client
EXEMPLE_INVALIDE:
  } catch (error) {
    return NextResponse.json({ error: (error as Error).message }, { status: 500 });
  }
EXEMPLE_VALIDE:
  } catch (error) {
    console.error('[POST /api/posts]', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
ERREUR_ATTENDUE: N/A (faille silencieuse — le client reçoit le schéma DB)
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "11-error-handling",
            "status": "active",
            "version": "1.0",
            "category": "error-handling",
            "source": "session2-ai-validated",
            "agent_context": "dev",
        },
    },
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Prisma — findUnique avec résultat null non géré
RAISON: findUnique retourne null si l'enregistrement n'existe pas. Accéder à une propriété sur null crashe le Route Handler avec une 500 au lieu d'une 404 sémantique.
DETECTION_REGEX: const \w+ = await prisma\.\w+\.findUnique\(
ALTERNATIVE: Vérifier le résultat de findUnique avant tout accès aux propriétés, retourner 404 si null
EXEMPLE_INVALIDE:
  // app/api/posts/[id]/route.ts
  export async function GET(_: Request, { params }: { params: { id: string } }) {
    const post = await prisma.post.findUnique({ where: { id: params.id } });
    return NextResponse.json({ title: post.title, content: post.content }); // crash si null
  }
EXEMPLE_VALIDE:
  // app/api/posts/[id]/route.ts
  export async function GET(_: Request, { params }: { params: { id: string } }) {
    const post = await prisma.post.findUnique({ where: { id: params.id } });
    if (!post) {
      return NextResponse.json({ error: 'Post not found' }, { status: 404 });
    }
    return NextResponse.json({ title: post.title, content: post.content });
  }
ERREUR_ATTENDUE: TypeError: Cannot read properties of null (reading 'title')
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "11-error-handling",
            "status": "active",
            "version": "1.0",
            "category": "error-handling",
            "source": "session2-ai-validated",
            "agent_context": "dev",
        },
    },
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Next.js App Router — validation body avec Zod avant opération Prisma
RAISON: Passer des champs undefined ou de mauvais type à Prisma lève une PrismaClientValidationError qui expose le schéma interne si non catchée.
DETECTION_REGEX: const \{[^}]+\} = await req\.json\(\);
ALTERNATIVE: Définir un schema Zod et utiliser .safeParse() avant tout appel Prisma — retourner 400 si invalide
EXEMPLE_INVALIDE:
  export async function POST(req: Request) {
    const { title, content } = await req.json();
    // title peut être undefined → PrismaClientValidationError
    const post = await prisma.post.create({ data: { title, content, authorId: userId } });
    return NextResponse.json(post);
  }
EXEMPLE_VALIDE:
  import { z } from 'zod';
  const CreatePostSchema = z.object({
    title: z.string().min(1).max(255),
    content: z.string().min(1),
  });

  export async function POST(req: Request) {
    const { userId } = await auth();
    if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

    const body = await req.json();
    const result = CreatePostSchema.safeParse(body);
    if (!result.success) {
      return NextResponse.json({ error: result.error.flatten() }, { status: 400 });
    }
    const post = await prisma.post.create({ data: { ...result.data, authorId: userId } });
    return NextResponse.json(post, { status: 201 });
  }
ERREUR_ATTENDUE: PrismaClientValidationError: Argument `title` is missing.
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "11-error-handling",
            "status": "active",
            "version": "1.0",
            "category": "error-handling",
            "source": "session2-ai-validated",
            "agent_context": "dev",
        },
    },
]


# =============================================================================
# ZONE 12 — TESTS AVANCÉS (Session 3 — AI-generated, validé Claude)
# Source: AI-generated 2026-03-05, validé par Claude Code
# Couvre: mock Clerk/server, mock Prisma, NextRequest jsdom, P2002 test, hoisting ESM
# =============================================================================

ZONE_12_TESTING_ADVANCED = [
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Jest — mock @clerk/nextjs/server dans les tests Route Handlers
RAISON: Sans mock, auth() tente une vraie requête Clerk depuis l'environnement Jest, échoue silencieusement et retourne { userId: null }, rendant les tests d'auth non déterministes.
DETECTION_REGEX: import.*auth.*from.*@clerk/nextjs/server
ALTERNATIVE: Toujours jest.mock('@clerk/nextjs/server') en début de test et contrôler la valeur retournée par userId
EXEMPLE_INVALIDE:
  import { GET } from '@/app/api/posts/route';
  // auth() non mocké → userId toujours null en Jest
  test('GET /api/posts retourne 200', async () => {
    const res = await GET();
    expect(res.status).toBe(200); // échoue : retourne 401
  });
EXEMPLE_VALIDE:
  jest.mock('@clerk/nextjs/server', () => ({
    auth: jest.fn().mockResolvedValue({ userId: 'user_test_123' }),
  }));
  import { GET } from '@/app/api/posts/route';
  test('GET /api/posts retourne 200 pour user authentifié', async () => {
    const res = await GET();
    expect(res.status).toBe(200);
  });
  test('GET /api/posts retourne 401 si non authentifié', async () => {
    const { auth } = require('@clerk/nextjs/server');
    auth.mockResolvedValueOnce({ userId: null });
    const res = await GET();
    expect(res.status).toBe(401);
  });
ERREUR_ATTENDUE: N/A (test passe toujours faussement ou échoue toujours selon l'env)
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "12-testing-advanced",
            "status": "active",
            "version": "1.0",
            "category": "testing",
            "source": "session3-ai-validated",
            "agent_context": "dev",
        },
    },
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Jest — mock PrismaClient (éviter les vraies requêtes DB)
RAISON: Sans mock Prisma, les tests unitaires tentent de se connecter à la base de données, échouent en CI (pas de DB), et sont des tests d'intégration déguisés en tests unitaires.
DETECTION_REGEX: import.*prisma.*from.*@/lib/prisma
ALTERNATIVE: Mocker inline via jest.mock('@/lib/prisma') avec les méthodes utilisées
EXEMPLE_INVALIDE:
  import prisma from '@/lib/prisma'; // import direct → vraie DB
  import { POST } from '@/app/api/users/route';
  test('crée un utilisateur', async () => {
    const res = await POST(req); // crash si DB absente
    expect(res.status).toBe(201);
  });
EXEMPLE_VALIDE:
  jest.mock('@clerk/nextjs/server', () => ({
    auth: jest.fn().mockResolvedValue({ userId: 'user_test_123' }),
  }));
  jest.mock('@/lib/prisma', () => ({
    prisma: {
      user: {
        create: jest.fn().mockResolvedValue({ id: 1, email: 'test@test.com', clerkId: 'user_test_123' }),
      },
    },
  }));
  import { POST } from '@/app/api/users/route';
  test('POST /api/users crée un utilisateur', async () => {
    const req = new Request('http://localhost/api/users', {
      method: 'POST',
      body: JSON.stringify({ email: 'test@test.com' }),
      headers: { 'Content-Type': 'application/json' },
    });
    const res = await POST(req);
    expect(res.status).toBe(201);
  });
ERREUR_ATTENDUE: PrismaClientInitializationError: Can't reach database server at `localhost:5432`
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "12-testing-advanced",
            "status": "active",
            "version": "1.0",
            "category": "testing",
            "source": "session3-ai-validated",
            "agent_context": "dev",
        },
    },
    {
        "text": """ACTION: INTERDIT
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Jest — import de NextRequest/NextResponse dans tests jsdom
RAISON: NextRequest et NextResponse utilisent l'API Web Fetch qui n'existe pas dans l'environnement jsdom Jest — les tests crashent immédiatement à l'import.
DETECTION_REGEX: import.*NextRequest|import.*NextResponse
ALTERNATIVE: Utiliser le constructeur natif Request/Response Web API dans les tests (disponible dans Node 18+)
EXEMPLE_INVALIDE:
  import { NextRequest } from 'next/server'; // crash jsdom
  test('GET posts', async () => {
    const req = new NextRequest('http://localhost/api/posts'); // ReferenceError
    const res = await GET(req);
  });
EXEMPLE_VALIDE:
  test('GET posts', async () => {
    const req = new Request('http://localhost/api/posts', { method: 'GET' });
    const res = await GET(req);
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(Array.isArray(data)).toBe(true);
  });
ERREUR_ATTENDUE: ReferenceError: NextRequest is not defined — ou — TypeError: (0 , next_server__WEBPACK_IMPORTED_MODULE_0__.NextRequest) is not a constructor
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "12-testing-advanced",
            "status": "active",
            "version": "1.0",
            "category": "testing",
            "source": "session3-ai-validated",
            "agent_context": "dev",
        },
    },
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Jest — test des erreurs Prisma avec simulation P2002
RAISON: Un test qui vérifie uniquement le happy path ne valide pas le comportement en cas de conflit DB — les erreurs Prisma non testées restent des 500 non diagnostiquées en production.
DETECTION_REGEX: prisma\.\w+\.create.*mockResolvedValue
ALTERNATIVE: Toujours ajouter un test cas d'erreur avec mockRejectedValue + PrismaClientKnownRequestError P2002
EXEMPLE_INVALIDE:
  test('crée un user', async () => {
    prismaMock.user.create.mockResolvedValue({ id: 1, email: 'a@b.com' });
    const res = await POST(req);
    expect(res.status).toBe(201);
    // aucun test d'erreur → le catch P2002 n'est jamais validé
  });
EXEMPLE_VALIDE:
  import { Prisma } from '@prisma/client';
  test('crée un user — succès', async () => {
    prismaMock.user.create.mockResolvedValue({ id: 1, email: 'a@b.com', clerkId: 'u_1' });
    const res = await POST(req);
    expect(res.status).toBe(201);
  });
  test('retourne 409 si email déjà existant', async () => {
    prismaMock.user.create.mockRejectedValue(
      new Prisma.PrismaClientKnownRequestError('Unique constraint failed', {
        code: 'P2002', clientVersion: '7.0.0', meta: { target: ['email'] },
      })
    );
    const res = await POST(req);
    expect(res.status).toBe(409);
    const body = await res.json();
    expect(body.error).toBe('Email already exists');
  });
ERREUR_ATTENDUE: N/A (test manquant — la route renvoie 500 en prod)
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "12-testing-advanced",
            "status": "active",
            "version": "1.0",
            "category": "testing",
            "source": "session3-ai-validated",
            "agent_context": "dev",
        },
    },
    {
        "text": """ACTION: INTERDIT
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Jest — jest.mock placé après les imports ES modules
RAISON: jest.mock() est hoisté avant les imports uniquement avec Babel/ts-jest CommonJS. Avec ESM natif ou mauvaise config ts-jest, le mock n'est pas appliqué et l'import réel est utilisé.
DETECTION_REGEX: import\\s+\\{[^}]+\\}\\s+from\\s+['"][^'"]+['"];\\s*[\\s\\S]*?jest\\.mock\\(
ALTERNATIVE: Placer jest.mock() avant tout import, ou utiliser require() pour les mocks dynamiques
EXEMPLE_INVALIDE:
  import { clerkMiddleware } from '@clerk/nextjs/server'; // import AVANT mock
  jest.mock('@clerk/nextjs/server', () => ({ clerkMiddleware: jest.fn() })); // trop tard
EXEMPLE_VALIDE:
  // jest.mock est hoisté avant les imports par le transform Babel/ts-jest.
  jest.mock('@clerk/nextjs/server', () => ({
    clerkMiddleware: jest.fn((handler) => jest.fn()),
    createRouteMatcher: jest.fn(() => jest.fn(() => false)),
  }));
  const mod = require('../middleware'); // require() pour éviter l'ambiguïté ESM
ERREUR_ATTENDUE: Cannot access 'clerkMiddleware' before initialization — ou — The module factory of jest.mock() is not allowed to reference any out-of-scope variables.
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "12-testing-advanced",
            "status": "active",
            "version": "1.0",
            "category": "testing",
            "source": "session3-ai-validated",
            "agent_context": "dev",
        },
    },
]


ZONE_13_BUSINESS_LOGIC = [
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Prisma — lier les entités utilisateur à authorId (String Clerk), pas à l'id interne
RAISON: Stocker l'id Prisma interne (Int) comme référence d'ownership crée une désynchronisation quand Clerk supprime ou recrée un utilisateur — les données orphelines ne peuvent plus être réclamées.
DETECTION_REGEX: (authorId|userId|ownerId)\\s+Int\\s+(?!.*@relation.*User)
ALTERNATIVE: Utiliser `authorId String` dans chaque modèle lié à un utilisateur — ce champ stocke le userId Clerk (String). Ne pas créer un modèle User séparé ni utiliser une clé étrangère vers un id interne.
EXEMPLE_INVALIDE:
  // schema.prisma ❌
  model Post {
    id       String @id @default(cuid())
    title    String
    authorId Int    // ❌ id interne Prisma — cassé si user recréé dans Clerk
    author   User   @relation(fields: [authorId], references: [id])
  }
EXEMPLE_VALIDE:
  // schema.prisma ✅
  model Post {
    id        String   @id @default(cuid())
    title     String
    content   String
    published Boolean  @default(false)
    authorId  String   // ✅ userId Clerk stocké directement — stable et sans jointure User
    createdAt DateTime @default(now())
    updatedAt DateTime @updatedAt
  }
  // Dans la route : where: { authorId: userId } où userId vient de await auth()
ERREUR_ATTENDUE: N/A (désynchronisation silencieuse à l'exécution)
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "13-business-logic",
            "status": "active",
            "version": "1.0",
            "category": "business-logic",
            "source": "session4-ai-validated",
            "agent_context": "dev",
        },
    },
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Prisma — champs obligatoires depuis le brief dans le schéma
RAISON: Générer un modèle Prisma incomplet (champs manquants du brief) produit un build qui passe mais une application qui ne satisfait pas la spécification — les routes API échouent à l'exécution sur les champs inexistants.
DETECTION_REGEX: N/A (détection sémantique — vérifier que chaque entité mentionnée dans le brief a un modèle Prisma correspondant)
ALTERNATIVE: Extraire exhaustivement toutes les entités et leurs champs du brief avant de générer le schéma, créer un modèle par entité mentionnée
EXEMPLE_INVALIDE:
  // Brief : "Post avec title, content, slug unique, published Boolean"
  // schema.prisma généré ❌
  model Post {
    id      String @id @default(cuid())
    title   String
    // ❌ content manquant, slug manquant, published manquant
  }
EXEMPLE_VALIDE:
  // Brief : "Post avec title, content, slug unique, published Boolean"
  // schema.prisma généré ✅
  model Post {
    id        String   @id @default(cuid())
    title     String
    content   String
    slug      String   @unique
    published Boolean  @default(false)
    authorId  String
    createdAt DateTime @default(now())
    updatedAt DateTime @updatedAt
  }
ERREUR_ATTENDUE: TypeError: Cannot read properties of undefined (reading 'slug') — ou — PrismaClientValidationError: Unknown field `slug` for model `Post`.
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "13-business-logic",
            "status": "active",
            "version": "1.0",
            "category": "business-logic",
            "source": "session4-ai-validated",
            "agent_context": "dev",
        },
    },
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Next.js App Router — slug unique dans les routes dynamiques
RAISON: Utiliser l'id interne Prisma dans l'URL au lieu du slug expose l'implémentation interne et empêche les URLs lisibles SEO-friendly exigées par le brief.
DETECTION_REGEX: prisma\\.\\w+\\.findUnique\\(\\s*\\{\\s*where:\\s*\\{\\s*id:\\s*params\\.id
ALTERNATIVE: Utiliser findUnique({ where: { slug: params.slug } }) pour les routes publiques quand le modèle a un champ slug @unique
EXEMPLE_INVALIDE:
  // app/api/posts/[id]/route.ts — quand le brief dit "URL par slug"
  export async function GET(_: Request, { params }: { params: { id: string } }) {
    const post = await prisma.post.findUnique({
      where: { id: params.id }, // ❌ expose l'id interne, pas le slug
    });
  }
EXEMPLE_VALIDE:
  // app/blog/[slug]/page.tsx — route publique par slug
  export default async function PostPage({ params }: { params: { slug: string } }) {
    const post = await prisma.post.findUnique({
      where: { slug: params.slug }, // ✅ slug depuis l'URL
    });
    if (!post || !post.published) notFound();
    return <article>{post.content}</article>;
  }
ERREUR_ATTENDUE: N/A (build passe — URL incorrecte à l'exécution)
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "13-business-logic",
            "status": "active",
            "version": "1.0",
            "category": "business-logic",
            "source": "session4-ai-validated",
            "agent_context": "dev",
        },
    },
    {
        "text": """ACTION: PRÉFÉRÉ
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Next.js App Router — toggle boolean via PATCH, pas PUT complet
RAISON: Un PUT sur une ressource remplace tous ses champs — utiliser PUT pour un toggle "published" écrase les données non fournies dans le body (title, content perdus si non renvoyés). PATCH est sémantiquement correct pour une mise à jour partielle. Note: si le brief spécifie explicitement PUT, respecter la spécification.
DETECTION_REGEX: export async function PUT.*toggle|published.*PUT
ALTERNATIVE: Utiliser PATCH pour les mises à jour partielles (toggle de champ), réserver PUT aux remplacements complets de ressource
EXEMPLE_INVALIDE:
  // app/api/posts/[id]/route.ts ❌
  export async function PUT(req: Request, { params }: { params: { id: string } }) {
    const { userId } = await auth();
    if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    // ❌ PUT complet pour un simple toggle — écrase title/content si non fournis
    await prisma.post.update({
      where: { id: params.id, authorId: userId },
      data: { published: true },
    });
    return NextResponse.json({ success: true });
  }
EXEMPLE_VALIDE:
  // app/api/posts/[id]/route.ts ✅
  export async function PATCH(req: Request, { params }: { params: { id: string } }) {
    const { userId } = await auth();
    if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    const post = await prisma.post.findUnique({
      where: { id: params.id, authorId: userId },
      select: { published: true },
    });
    if (!post) return NextResponse.json({ error: 'Not found' }, { status: 404 });
    const updated = await prisma.post.update({
      where: { id: params.id },
      data: { published: !post.published }, // ✅ toggle réel
    });
    return NextResponse.json({ published: updated.published });
  }
ERREUR_ATTENDUE: N/A (sémantique incorrecte — données perdues en production)
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "13-business-logic",
            "status": "active",
            "version": "1.0",
            "category": "business-logic",
            "source": "session4-ai-validated",
            "agent_context": "dev",
        },
    },
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Next.js App Router — sélection des champs retournés par Prisma
RAISON: Retourner l'entité Prisma complète depuis une API publique expose des champs internes (authorId, clerkId, metadata) qui ne doivent pas être visibles côté client.
DETECTION_REGEX: return NextResponse\\.json\\(\\s*\\w+\\s*\\)(?!.*select|.*omit)
ALTERNATIVE: Utiliser select ou omit dans la requête Prisma, ou destructurer explicitement les champs à exposer
EXEMPLE_INVALIDE:
  // app/api/posts/[id]/route.ts
  const post = await prisma.post.findUnique({ where: { slug: params.slug } });
  // ❌ retourne authorId (clerkId interne), tous les champs internes
  return NextResponse.json(post);
EXEMPLE_VALIDE:
  // app/api/posts/[id]/route.ts
  const post = await prisma.post.findUnique({
    where: { slug: params.slug, published: true },
    select: {   // ✅ uniquement les champs publics
      id: true,
      title: true,
      content: true,
      slug: true,
      createdAt: true,
    },
  });
  if (!post) return NextResponse.json({ error: 'Not found' }, { status: 404 });
  return NextResponse.json(post);
ERREUR_ATTENDUE: N/A (fuite de données silencieuse)
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "13-business-logic",
            "status": "active",
            "version": "1.0",
            "category": "business-logic",
            "source": "session4-ai-validated",
            "agent_context": "dev",
        },
    },
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Prisma — slug généré déterministement côté serveur
RAISON: Laisser le client envoyer un slug ou le générer côté LLM sans normalisation produit des slugs avec espaces, accents ou majuscules qui cassent les URLs et violent la contrainte @unique Prisma.
DETECTION_REGEX: slug:\\s*(body\\.slug|req\\.body\\.slug|data\\.slug)(?!.*\\.toLowerCase\\(\\)|.*\\.replace\\(|.*slugify)
ALTERNATIVE: Générer le slug côté serveur depuis le titre avec normalisation (toLowerCase + replace espaces/accents)
EXEMPLE_INVALIDE:
  // app/api/posts/route.ts
  const { title, content, slug } = await req.json();
  // ❌ slug vient du client — peut contenir "Mon Article !" →
  //    contrainte @unique Prisma viole avec espaces/accents
  await prisma.post.create({ data: { title, content, slug, authorId: userId } });
EXEMPLE_VALIDE:
  // app/api/posts/route.ts
  const { title, content } = await req.json();
  // ✅ slug généré et normalisé côté serveur
  const baseSlug = title
    .toLowerCase()
    .normalize('NFD').replace(/[\\u0300-\\u036f]/g, '') // supprime accents
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
  // Unicité : ajouter suffix si conflit
  const slug = `${baseSlug}-${Date.now()}`;
  await prisma.post.create({ data: { title, content, slug, authorId: userId } });
ERREUR_ATTENDUE: PrismaClientKnownRequestError: Unique constraint failed on the fields: (`slug`)
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "13-business-logic",
            "status": "active",
            "version": "1.0",
            "category": "business-logic",
            "source": "session4-ai-validated",
            "agent_context": "dev",
        },
    },
]


ZONE_14_ANTIPATTERNS = [
    {
        "text": """ACTION: INTERDIT
STACK: nextjs-clerk-prisma
TECHNOLOGIE: @clerk/nextjs — SignIn/SignUp components sans routes Catch-All
RAISON: Créer manuellement des pages /sign-in et /sign-up sans les routes Catch-All fait que Clerk ne peut pas gérer ses propres redirections internes (/sign-in/factor-one, /sign-in/sso-callback...) — les utilisateurs se retrouvent sur une page 404 pendant l'auth.
DETECTION_REGEX: app/sign-in/page\\.tsx|app/sign-up/page\\.tsx(?!.*\\[\\[\\.\\.\\.sign)
ALTERNATIVE: Utiliser les routes Catch-All [[...sign-in]] et [[...sign-up]] pour que Clerk gère toutes ses sous-routes internes
EXEMPLE_INVALIDE:
  // app/sign-in/page.tsx ❌
  import { SignIn } from '@clerk/nextjs';
  export default function SignInPage() {
    return <SignIn />;
    // ❌ /sign-in/factor-one → 404, SSO callback → 404
  }
EXEMPLE_VALIDE:
  // app/sign-in/[[...sign-in]]/page.tsx ✅
  import { SignIn } from '@clerk/nextjs';
  export default function SignInPage() {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <SignIn />
      </div>
    );
  }
ERREUR_ATTENDUE: 404 sur /sign-in/factor-one — ou — Clerk: signInUrl must be set to the path of your sign-in page.
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "14-antipatterns",
            "status": "active",
            "version": "1.0",
            "category": "antipatterns",
            "source": "session5-ai-validated",
            "agent_context": "dev",
        },
    },
    {
        "text": """ACTION: INTERDIT
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Next.js App Router — Server Components avec useState/useEffect
RAISON: Les Server Components Next.js App Router n'ont pas accès au runtime React côté client — utiliser des hooks React crashe immédiatement le build avec une erreur TypeScript/Next.js non ambiguë.
DETECTION_REGEX: (useState|useEffect|useCallback|useRef)\\s*\\((dans un fichier app/**/*.tsx qui n'a pas 'use client' en première ligne)
ALTERNATIVE: Ajouter 'use client' en première ligne si des hooks sont nécessaires, ou extraire la logique dans un sous-composant Client
EXEMPLE_INVALIDE:
  // app/dashboard/page.tsx ❌ (Server Component par défaut)
  import { useState } from 'react';
  export default function DashboardPage() {
    const [count, setCount] = useState(0); // ❌ hook dans Server Component
    return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
  }
EXEMPLE_VALIDE:
  // app/dashboard/page.tsx ✅ — Server Component pour les données
  import DashboardClient from './page-client';
  import { auth } from '@clerk/nextjs/server';
  import { postService } from '@/lib/services/post.service';
  export default async function DashboardPage() {
    const { userId } = await auth();
    if (!userId) redirect('/sign-in');
    const posts = await postService.getAll(userId); // ✅ SerializedPost[] — dates déjà string
    return <DashboardClient posts={posts} />;  // ✅ pas de .toISOString() — déjà fait par le service
  }
  // app/dashboard/page-client.tsx
  'use client';
  import { useState } from 'react';
  import type { SerializedPost } from '@/lib/types';
  interface DashboardClientProps { posts: SerializedPost[] }
  export default function DashboardClient({ posts }: DashboardClientProps) {
    const [filter, setFilter] = useState('all');
  }
ERREUR_ATTENDUE: Error: useState only works in Client Components. Add the "use client" directive at the top of the file to use it.
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "14-antipatterns",
            "status": "active",
            "version": "1.0",
            "category": "antipatterns",
            "source": "session5-ai-validated",
            "agent_context": "dev",
        },
    },
    {
        "text": """ACTION: INTERDIT
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Next.js App Router — redirect() dans un try/catch
RAISON: La fonction redirect() de Next.js fonctionne en lançant une exception interne (NEXT_REDIRECT). Si elle est appelée dans un try/catch, l'exception est catchée et la redirection n'a jamais lieu — l'utilisateur reste sur la page sans redirection ni erreur visible.
DETECTION_REGEX: try\\s*\\{[\\s\\S]*?redirect\\([\\s\\S]*?\\}\\s*catch
ALTERNATIVE: Appeler redirect() en dehors des blocs try/catch, ou utiliser notFound() pour les 404 qui ne nécessitent pas de try/catch
EXEMPLE_INVALIDE:
  // app/dashboard/page.tsx
  export default async function DashboardPage() {
    try {
      const { userId } = await auth();
      if (!userId) redirect('/sign-in'); // ❌ exception catchée → redirect silencieux
      const data = await prisma.post.findMany();
      return <div>{data.length} posts</div>;
    } catch (error) {
      console.error(error); // redirect() est catchée ici → jamais exécutée
      return <div>Erreur</div>;
    }
  }
EXEMPLE_VALIDE:
  // app/dashboard/page.tsx
  export default async function DashboardPage() {
    const { userId } = await auth(); // ✅ auth() en dehors du try/catch
    if (!userId) redirect('/sign-in');
    try {
      const data = await prisma.post.findMany({ where: { authorId: userId } });
      return <div>{data.length} posts</div>;
    } catch (error) {
      console.error('[DashboardPage]', error);
      return <div>Une erreur est survenue</div>;
    }
  }
ERREUR_ATTENDUE: N/A (redirection silencieusement ignorée — l'utilisateur reste sur la page)
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "14-antipatterns",
            "status": "active",
            "version": "1.0",
            "category": "antipatterns",
            "source": "session5-ai-validated",
            "agent_context": "dev",
        },
    },
    {
        "text": """ACTION: INTERDIT
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Next.js App Router — appel Prisma direct dans un Client Component
RAISON: Les Client Components s'exécutent dans le navigateur — Prisma est une bibliothèque Node.js avec des modules natifs (pg, fs...) qui n'existent pas dans le browser. Le build échoue avec une erreur de module non trouvé.
DETECTION_REGEX: 'use client'[\\s\\S]*?import.*@prisma/client|import.*@prisma/client[\\s\\S]*?'use client'
ALTERNATIVE: Les appels Prisma restent dans les Server Components (page.tsx sans 'use client') ou les Route Handlers (app/api/**/route.ts)
EXEMPLE_INVALIDE:
  // app/dashboard/DashboardPage.tsx ❌
  'use client';
  import prisma from '@/lib/prisma'; // ❌ Prisma dans Client Component
  import { useEffect, useState } from 'react';
  export default function DashboardPage() {
    const [posts, setPosts] = useState([]);
    useEffect(() => {
      prisma.post.findMany().then(setPosts); // ❌ crash build + runtime
    }, []);
    return <div>{posts.length}</div>;
  }
EXEMPLE_VALIDE:
  // app/dashboard/page.tsx ✅ — Server Component
  import { DashboardClient } from './DashboardClient';
  export default async function DashboardPage() {
    const { userId } = await auth();
    if (!userId) redirect('/sign-in');
    // ✅ Prisma dans Server Component — Node.js env
    const posts = await prisma.post.findMany({ where: { authorId: userId } });
    return <DashboardClient initialPosts={posts} />;
  }
ERREUR_ATTENDUE: Module not found: Can't resolve 'pg-native' — ou — Module not found: Can't resolve 'fs' in '.../node_modules/@prisma/client/runtime'
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "14-antipatterns",
            "status": "active",
            "version": "1.0",
            "category": "antipatterns",
            "source": "session5-ai-validated",
            "agent_context": "dev",
        },
    },
]


# =============================================================================
# ZONE 15 — CONFORMITÉ : exemples de requirements bien/mal couverts
# Source: Sprint 4.6 — Agent Critique (AgentConformité)
# agent_context: conformity — utilisé par l'AgentConformité via RAG
# =============================================================================

ZONE_15_CONFORMITY = [
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Agent Conformité — coverage d'un modèle Prisma
RAISON: Un requirement "Modèle Prisma: Post" est couvert si et seulement si model Post existe dans prisma/schema.prisma avec au moins les champs id, authorId et un champ métier. Un modèle vide ou absent = requirement MISSING.
DETECTION_REGEX: model\\s+Post\\s*\\{[\\s\\S]*?id\\s+String[\\s\\S]*?\\}
EXEMPLE_INVALIDE:
  // requirement : "Modèle Prisma: Post" → MISSING
  // schema.prisma ne contient pas "model Post"
  model Book {
    id       String @id @default(cuid())
    title    String
    authorId String
  }
EXEMPLE_VALIDE:
  // requirement : "Modèle Prisma: Post" → IMPLEMENTED
  model Post {
    id        String   @id @default(cuid())
    title     String
    content   String
    authorId  String
    createdAt DateTime @default(now())
  }
VERDICT: implemented si model + ≥2 champs | partial si model vide ou <2 champs | missing si absent
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "15-conformity",
            "status": "active",
            "version": "1.0",
            "category": "conformity",
            "source": "sprint46",
            "agent_context": "conformity",
        },
    },
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Agent Conformité — coverage d'une page dynamique
RAISON: Un requirement "Page: /posts/[id]" est couvert si app/posts/[id]/page.tsx existe ET contient une fonction export default. Un fichier stub avec <10 lignes = PARTIAL. Absent = MISSING.
DETECTION_REGEX: export\\s+default\\s+(async\\s+)?function\\s+\\w+
EXEMPLE_INVALIDE:
  // requirement : "Page: /posts/[id]" → MISSING
  // app/posts/[id]/page.tsx absent du projet généré
EXEMPLE_PARTIEL:
  // requirement : "Page: /posts/[id]" → PARTIAL
  // app/posts/[id]/page.tsx existe mais contient uniquement :
  export default function PostPage() {
    return <div>Post</div>; // stub sans data fetching
  }
EXEMPLE_VALIDE:
  // requirement : "Page: /posts/[id]" → IMPLEMENTED
  // app/posts/[id]/page.tsx
  export default async function PostPage({ params }: { params: { id: string } }) {
    const { userId } = await auth();
    const post = await prisma.post.findUnique({ where: { id: params.id } });
    if (!post) notFound();
    return <article><h1>{post.title}</h1><p>{post.content}</p></article>;
  }
VERDICT: implemented si fichier + export default + data fetching | partial si fichier + export default mais stub | missing si absent
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "15-conformity",
            "status": "active",
            "version": "1.0",
            "category": "conformity",
            "source": "sprint46",
            "agent_context": "conformity",
        },
    },
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Agent Conformité — coverage d'une route API avec méthode
RAISON: Un requirement "API Route: POST /api/posts" est couvert si app/api/posts/route.ts existe ET contient "export async function POST". Un handler vide retournant seulement NextResponse.json({}) = PARTIAL. Absent = MISSING.
DETECTION_REGEX: export\\s+async\\s+function\\s+POST
EXEMPLE_INVALIDE:
  // requirement : "API Route: POST /api/posts" → MISSING
  // app/api/posts/route.ts existe mais contient seulement GET
  export async function GET(req: Request) { ... }
  // Pas de POST handler → MISSING pour ce requirement
EXEMPLE_PARTIEL:
  // requirement : "API Route: POST /api/posts" → PARTIAL
  export async function POST(req: Request) {
    return NextResponse.json({}); // handler vide, sans logique Prisma
  }
EXEMPLE_VALIDE:
  // requirement : "API Route: POST /api/posts" → IMPLEMENTED
  export async function POST(req: Request) {
    const { userId } = await auth();
    if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    const { title, content } = await req.json();
    const post = await prisma.post.create({ data: { title, content, authorId: userId } });
    return NextResponse.json(post, { status: 201 });
  }
VERDICT: implemented si handler + logique Prisma | partial si handler + return vide | missing si handler absent
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "15-conformity",
            "status": "active",
            "version": "1.0",
            "category": "conformity",
            "source": "sprint46",
            "agent_context": "conformity",
        },
    },
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Agent Conformité — calcul du conformity_score
RAISON: Le conformity_score doit être calculé de manière déterministe. La formule est (implemented + 0.5 * partial) / total_requirements. Un score ≥ 0.7 = app conforme. Un score < 0.5 = déviation majeure du brief.
FORMULE: conformity_score = (count_implemented + 0.5 * count_partial) / total_requirements
EXEMPLE:
  requirements = ["Modèle Prisma: Post", "Page: /", "Page: /posts/[id]", "API Route: GET /api/posts", "API Route: POST /api/posts"]
  results = [implemented, implemented, partial, implemented, missing]
  score = (3 + 0.5 * 1) / 5 = 3.5 / 5 = 0.70
SEUILS:
  ≥ 0.9 → app très conforme au brief
  ≥ 0.7 → app conforme (signal de clôture Sprint 4.6)
  ≥ 0.5 → app partiellement conforme
  < 0.5 → déviation majeure — dev agent a généré une autre app
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "15-conformity",
            "status": "active",
            "version": "1.0",
            "category": "conformity",
            "source": "sprint46",
            "agent_context": "conformity",
        },
    },
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Agent Conformité — relation modèle ↔ route API
RAISON: Un modèle Prisma sans aucune route API CRUD correspondante = requirement partiellement couvert. La présence du modèle dans schema.prisma est nécessaire mais insuffisante si aucun handler ne l'utilise via prisma.X.
RÈGLE: Si requirement "Modèle Prisma: Product" → vérifier aussi qu'au moins une route app/api/products/* utilise prisma.product.
EXEMPLE_INVALIDE:
  // requirement "Modèle Prisma: Product" → PARTIAL
  // schema.prisma contient model Product { ... }
  // mais app/api/products/route.ts fait : prisma.item.findMany() // mauvais modèle
  // → le modèle existe mais n'est pas utilisé → PARTIAL
EXEMPLE_VALIDE:
  // requirement "Modèle Prisma: Product" → IMPLEMENTED
  // schema.prisma : model Product { id String... }
  // app/api/products/route.ts : prisma.product.findMany({ where: { authorId: userId } })
  // → modèle déclaré ET utilisé → IMPLEMENTED
VERDICT: implemented si model déclaré + utilisé dans une route | partial si model déclaré mais non utilisé ou mauvais accesseur
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "15-conformity",
            "status": "active",
            "version": "1.0",
            "category": "conformity",
            "source": "sprint46",
            "agent_context": "conformity",
        },
    },

    # ── Reviewer-specific: cohérence brief ↔ production ──────────────────────
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Reviewer — cohérence entités brief vs entités générées (ghost success)
RAISON: Le reviewer doit vérifier que les entités Prisma générées correspondent aux entités du brief, pas à des entités génériques. Si le brief demande "Project + Task + Comment" et que schema.prisma contient "Post + Book", l'app compile mais n'implémente pas la demande. C'est un ghost success.
RÈGLE_REVIEWER:
  1. Extraire les noms de modèles du brief (des champs models[] du ProjectSpec)
  2. Extraire les noms de modèles de schema.prisma
  3. Si intersection < 80% des modèles du brief → verdict INCOHERENT
  4. Si intersection 50-80% → verdict DEGRADED
  5. Si intersection ≥ 80% → cohérence modèles OK
BAD:
  // brief : {"models": ["Project", "Task", "Comment"]}
  // schema.prisma généré :
  model Post { id String @id ... }     // ← mauvaise entité
  model Book { id String @id ... }     // ← mauvaise entité
  // verdict : INCOHERENT (0/3 entités du brief présentes)
GOOD:
  // brief : {"models": ["Project", "Task", "Comment"]}
  // schema.prisma généré :
  model Project { id String @id ... }  // ✅
  model Task    { id String @id ... }  // ✅
  model Comment { id String @id ... }  // ✅
  // verdict : COHERENT (3/3 entités du brief présentes)
ERREUR_ATTENDUE: App buildée avec de mauvaises entités — ghost success
SEVERITY: critical
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "15-conformity",
            "status": "active",
            "version": "1.0",
            "category": "conformity",
            "source": "reviewer_sprint48",
            "agent_context": "reviewer",
        },
    },
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Reviewer — page stub sans données réelles (app sans sens pour l'utilisateur)
RAISON: Une page qui existe dans app/ mais qui n'affiche pas les données du brief compile correctement mais n'a aucune valeur pour l'utilisateur. Si app/projects/page.tsx retourne un div vide ou un texte statique sans appel au service, la page est un stub.
RÈGLE_REVIEWER:
  Pour chaque page dans ir_pages du ProjectSpec, vérifier que page.tsx :
  1. Importe et appelle le service correspondant (ex: projectService.getAll)
  2. Passe les données à un composant (n'est pas un stub vide)
  Si page.tsx fait uniquement return <div>Projects</div> sans data → verdict DEGRADED
BAD:
  // app/projects/page.tsx — stub sans données ❌
  export default async function ProjectsPage() {
    return <div>Projects</div>  // ← aucune donnée — app inutilisable
  }
GOOD:
  // app/projects/page.tsx ✅
  export default async function ProjectsPage() {
    const { userId } = await auth()
    if (!userId) redirect('/sign-in')
    const projects = await projectService.getAll(userId)
    return <ProjectsClient projects={projects} />
  }
ERREUR_ATTENDUE: Page buildée sans données — l'utilisateur voit une page vide en production
SEVERITY: medium
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "15-conformity",
            "status": "active",
            "version": "1.0",
            "category": "conformity",
            "source": "reviewer_sprint48",
            "agent_context": "reviewer",
        },
    },
]


# =============================================================================
# ZONE 16 — SÉCURITÉ APPLICATIVE : patterns valides/invalides avec code
# Source: Sprint 4.6 — Agent Critique (AgentSécurité)
# agent_context: security — utilisé par l'AgentSécurité via RAG
# =============================================================================

ZONE_16_SECURITY_APPLICATIVE = [
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Route Handler Next.js App Router — auth check Clerk v6 obligatoire avant Prisma
RAISON: Un handler API qui accède à Prisma sans vérifier userId via auth() expose les données de TOUS les utilisateurs à n'importe qui. Severity HIGH.
DETECTION_REGEX: export\\s+async\\s+function\\s+(POST|PUT|DELETE|GET)[\\s\\S]*?prisma\\.[\\w]+\\.(?!.*auth\\()
ALTERNATIVE: Appeler auth() en premier dans chaque handler, vérifier userId non-null avant toute requête Prisma.
EXEMPLE_INVALIDE:
  // app/api/posts/route.ts — severity: HIGH ❌
  export async function POST(req: Request) {
    const { title } = await req.json();
    const post = await prisma.post.create({ data: { title } }); // ❌ pas de auth check
    return NextResponse.json(post);
  }
EXEMPLE_VALIDE:
  // app/api/posts/route.ts ✅
  export async function POST(req: Request) {
    const { userId } = await auth(); // ✅ auth check en premier
    if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    const { title } = await req.json();
    const post = await prisma.post.create({ data: { title, authorId: userId } });
    return NextResponse.json(post, { status: 201 });
  }
ERREUR_ATTENDUE: Fuite de données — n'importe quel utilisateur peut créer/lire/modifier des données sans être authentifié
SEVERITY: high
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "16-security-applicative",
            "status": "active",
            "version": "1.0",
            "category": "security",
            "source": "sprint46",
            "agent_context": "security",
        },
    },
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Route Handler GET liste — filtrage authorId obligatoire
RAISON: Un GET qui liste des ressources sans filtrer par authorId/userId expose les données de TOUS les utilisateurs. C'est une faille IDOR (Insecure Direct Object Reference). Severity MEDIUM.
DETECTION_REGEX: prisma\\.\\w+\\.findMany\\(\\s*\\)
ALTERNATIVE: Toujours passer { where: { authorId: userId } } dans findMany() après auth check.
EXEMPLE_INVALIDE:
  // app/api/posts/route.ts — severity: MEDIUM ❌
  export async function GET(req: Request) {
    const { userId } = await auth();
    if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    const posts = await prisma.post.findMany(); // ❌ retourne TOUS les posts de TOUS les users
    return NextResponse.json(posts);
  }
EXEMPLE_VALIDE:
  // app/api/posts/route.ts ✅
  export async function GET(req: Request) {
    const { userId } = await auth();
    if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    const posts = await prisma.post.findMany({ where: { authorId: userId } }); // ✅ filtré
    return NextResponse.json(posts);
  }
ERREUR_ATTENDUE: Un utilisateur A peut voir les données de l'utilisateur B — faille IDOR
SEVERITY: medium
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "16-security-applicative",
            "status": "active",
            "version": "1.0",
            "category": "security",
            "source": "sprint46",
            "agent_context": "security",
        },
    },
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Route Handler GET/PUT/DELETE par ID — vérification propriété obligatoire
RAISON: Accéder à une ressource par son ID sans vérifier que authorId === userId permet à un utilisateur d'accéder aux ressources d'un autre. Severity MEDIUM.
DETECTION_REGEX: prisma\\.\\w+\\.findUnique[\\s\\S]*?where[\\s\\S]*?id(?![\\s\\S]*?authorId\\s*!==\\s*userId)
ALTERNATIVE: Après findUnique, vérifier post.authorId !== userId et retourner 403 si vrai.
EXEMPLE_INVALIDE:
  // app/api/posts/[id]/route.ts — severity: MEDIUM ❌
  export async function DELETE(req: Request, { params }: { params: { id: string } }) {
    const { userId } = await auth();
    if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    await prisma.post.delete({ where: { id: params.id } }); // ❌ n'importe qui peut supprimer
    return NextResponse.json({ deleted: true });
  }
EXEMPLE_VALIDE:
  // app/api/posts/[id]/route.ts ✅
  export async function DELETE(req: Request, { params }: { params: { id: string } }) {
    const { userId } = await auth();
    if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    const post = await prisma.post.findUnique({ where: { id: params.id } });
    if (!post || post.authorId !== userId) { // ✅ vérif propriété
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
    }
    await prisma.post.delete({ where: { id: params.id } });
    return NextResponse.json({ deleted: true });
  }
ERREUR_ATTENDUE: Utilisateur B peut modifier/supprimer les ressources de l'utilisateur A
SEVERITY: medium
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "16-security-applicative",
            "status": "active",
            "version": "1.0",
            "category": "security",
            "source": "sprint46",
            "agent_context": "security",
        },
    },
    {
        "text": """ACTION: INTERDIT
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Route Handler — exposition de userId dans la réponse JSON
RAISON: Retourner userId (Clerk internal ID) dans la réponse HTTP expose un identifiant interne qui peut faciliter l'énumération des utilisateurs. Severity MEDIUM.
DETECTION_REGEX: NextResponse\\.json\\([\\s\\S]*?userId[\\s\\S]*?\\)
ALTERNATIVE: Retourner uniquement les champs métier nécessaires au client. Ne jamais inclure userId, sessionId ou tout identifiant Clerk dans la réponse.
EXEMPLE_INVALIDE:
  // severity: MEDIUM ❌
  export async function GET(req: Request) {
    const { userId } = await auth();
    if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    const profile = await prisma.user.findUnique({ where: { clerkId: userId } });
    return NextResponse.json({ ...profile, userId }); // ❌ userId exposé
  }
EXEMPLE_VALIDE:
  // ✅
  export async function GET(req: Request) {
    const { userId } = await auth();
    if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    const profile = await prisma.user.findUnique({ where: { clerkId: userId } });
    const { clerkId, ...safeProfile } = profile; // ✅ clerkId retiré de la réponse
    return NextResponse.json(safeProfile);
  }
ERREUR_ATTENDUE: Enumération d'utilisateurs facilité par exposition des IDs internes
SEVERITY: medium
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "16-security-applicative",
            "status": "active",
            "version": "1.0",
            "category": "security",
            "source": "sprint46",
            "agent_context": "security",
        },
    },
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Route Handler POST/PUT — validation du body avant écriture Prisma
RAISON: Passer le body non-validé directement à Prisma peut provoquer des erreurs runtime (champs inattendus, types incorrects) ou des injections de données. Severity LOW — non exploitable directement mais bonne pratique obligatoire.
DETECTION_REGEX: req\\.json\\(\\)[\\s\\S]*?prisma\\.\\w+\\.create\\(\\{\\s*data:\\s*\\.\\.\\.[\\s\\S]*?\\}\\)
ALTERNATIVE: Extraire les champs individuellement depuis req.json() et construire l'objet data explicitement. Ne jamais faire { data: ...body }.
EXEMPLE_INVALIDE:
  // severity: LOW ❌
  export async function POST(req: Request) {
    const { userId } = await auth();
    if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    const body = await req.json();
    const post = await prisma.post.create({ data: { ...body, authorId: userId } }); // ❌ body non validé
    return NextResponse.json(post);
  }
EXEMPLE_VALIDE:
  // ✅
  export async function POST(req: Request) {
    const { userId } = await auth();
    if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    const { title, content } = await req.json(); // ✅ extraction explicite
    if (!title || typeof title !== 'string') {
      return NextResponse.json({ error: 'title requis' }, { status: 400 });
    }
    const post = await prisma.post.create({ data: { title, content, authorId: userId } });
    return NextResponse.json(post, { status: 201 });
  }
ERREUR_ATTENDUE: Erreurs Prisma runtime si des champs inattendus sont passés au modèle
SEVERITY: low
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "16-security-applicative",
            "status": "active",
            "version": "1.0",
            "category": "security",
            "source": "sprint46",
            "agent_context": "security",
        },
    },

    # ── Reviewer-specific: Server Actions + Service layer ─────────────────────
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Service DAL update() — userId OBLIGATOIRE dans le where pour éviter IDOR
RAISON: La méthode update() du service DAL (lib/services/*.service.ts) DOIT filtrer par userId dans le where Prisma. Sans ce filtre, tout utilisateur authentifié peut écraser les données d'un autre utilisateur en connaissant l'UUID de la ressource. Ce bug est invisible au compilateur (TypeScript compile sans erreur) mais est une faille IDOR critique en production.
DETECTION_REGEX: prisma\\.\\w+\\.update\\(\\{\\s*where:\\s*\\{\\s*id[^}]*\\}(?![\\s\\S]{0,50}userId)
ALTERNATIVE: Toujours inclure userId dans le where de update() et delete().
BAD:
  // lib/services/project.service.ts — IDOR critique ❌
  update: async (id: string, data: UpdateProjectInput): Promise<Project> => {
    return prisma.project.update({
      where: { id },      // ← IDOR : n'importe qui peut écraser ce projet
      data: { ...(data as any) }
    })
  }
GOOD:
  // lib/services/project.service.ts ✅
  update: async (userId: string, id: string, data: UpdateProjectInput): Promise<Project> => {
    return prisma.project.update({
      where: { id, userId },  // ← filtre propriété obligatoire
      data: { ...(data as any) }
    })
  }
ERREUR_ATTENDUE: Utilisateur B modifie les données de l'utilisateur A sans erreur TypeScript ni build failure
SEVERITY: critical
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "16-security-applicative",
            "status": "active",
            "version": "1.0",
            "category": "security",
            "source": "reviewer_sprint48",
            "agent_context": "reviewer",
        },
    },
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Server Action — userId transmis au service pour update() et delete()
RAISON: Les Server Actions (app/*/actions.ts) appellent auth() et obtiennent userId. Ce userId DOIT être transmis au service DAL pour les opérations mutantes (update, delete). Si le service reçoit uniquement l'id de la ressource sans userId, il ne peut pas enforcer l'ownership — IDOR garanti.
DETECTION_REGEX: await\\s+\\w+Service\\.(?:update|delete)\\([^,)]*\\)(?![\\s\\S]{0,30}userId)
ALTERNATIVE: Passer userId comme premier argument de toute méthode service mutante.
BAD:
  // app/projects/actions.ts — IDOR ❌
  export async function updateProject(id: string, formData: FormData) {
    const { userId } = await auth()
    if (!userId) redirect('/sign-in')
    await projectService.update(id, validated)  // ← userId non transmis au service
  }
GOOD:
  // app/projects/actions.ts ✅
  export async function updateProject(id: string, formData: FormData) {
    const { userId } = await auth()
    if (!userId) redirect('/sign-in')
    await projectService.update(userId, id, validated)  // ← userId transmis
  }
ERREUR_ATTENDUE: Service update() sans userId dans where — IDOR silencieux
SEVERITY: critical
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "16-security-applicative",
            "status": "active",
            "version": "1.0",
            "category": "security",
            "source": "reviewer_sprint48",
            "agent_context": "reviewer",
        },
    },
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Service DAL getAll() — filtrage userId OBLIGATOIRE pour isolation des données
RAISON: La méthode getAll()/findMany() du service DAL DOIT filtrer par userId. Sans ce filtre, un utilisateur authentifié voit toutes les ressources de tous les utilisateurs. Ce bug est invisible au compilateur.
DETECTION_REGEX: prisma\\.\\w+\\.findMany\\(\\s*\\{(?![\\s\\S]{0,100}userId)
BAD:
  // lib/services/project.service.ts ❌
  getAll: async (): Promise<SerializedProject[]> => {
    return prisma.project.findMany()  // ← expose TOUS les projets de tous les users
  }
GOOD:
  // lib/services/project.service.ts ✅
  getAll: async (userId: string): Promise<SerializedProject[]> => {
    return prisma.project.findMany({ where: { userId } })  // ← isolé par user
  }
ERREUR_ATTENDUE: Utilisateur A voit les données de l'utilisateur B
SEVERITY: critical
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "16-security-applicative",
            "status": "active",
            "version": "1.0",
            "category": "security",
            "source": "reviewer_sprint48",
            "agent_context": "reviewer",
        },
    },
]


# =============================================================================
# ZONE_17 — COHERENCE ARCHITECTURALE INTER-FICHIERS
# agent_context: dev — consommé par le dev LLM via RAG (les superviseurs utilisent les fichiers prompts, pas Qdrant)
# Cohérence imports, patterns stack, conventions App Router, Prisma schema
# =============================================================================

ZONE_17_ARCHITECTURE = [
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Import Clerk — server vs client dans App Router
RAISON: '@clerk/nextjs/server' est SERVER ONLY. Importé depuis un Client Component ('use client'), il provoque une erreur de build Next.js : 'server-only cannot be imported from a Client Component module'. Ce pattern est architecturalement invalide.
RÈGLE:
  • Client Component ('use client') → importer useAuth(), useUser(), useClerk() depuis '@clerk/nextjs'
  • Server Component / Route Handler → importer auth(), currentUser() depuis '@clerk/nextjs/server'
EXEMPLE_INVALIDE:
  // ❌ Client Component avec import server
  'use client';
  import { auth } from '@clerk/nextjs/server'; // ← ERREUR BUILD
EXEMPLE_VALIDE:
  // ✅ Client Component
  'use client';
  import { useAuth } from '@clerk/nextjs';

  // ✅ Server Component / Route Handler
  import { auth } from '@clerk/nextjs/server';
ERREUR_ATTENDUE: Build error: 'server-only' cannot be imported from a Client Component module
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "17-architecture",
            "status": "active",
            "version": "1.0",
            "category": "architecture",
            "source": "sprint46",
            "agent_context": "dev",
        },
    },
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Prisma — singleton obligatoire, instanciation directe interdite
RAISON: Instancier PrismaClient directement (new PrismaClient()) crée une connexion DB à chaque requête. Avec le Hot Module Reloading de Next.js en dev, cela génère des dizaines de connexions simultanées et épuise le pool de connexions.
RÈGLE: Toujours importer le singleton depuis '@/lib/prisma'.
EXEMPLE_INVALIDE:
  // ❌ Instanciation directe — pool épuisé
  import { PrismaClient } from '@prisma/client';
  const prisma = new PrismaClient();
  export async function GET() {
    const posts = await prisma.post.findMany();
  }
EXEMPLE_VALIDE:
  // ✅ Import du singleton
  import prisma from '@/lib/prisma';
  export async function GET() {
    const posts = await prisma.post.findMany();
  }
ERREUR_ATTENDUE: Too many database connections — pool exhaustion après quelques requêtes
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "17-architecture",
            "status": "active",
            "version": "1.0",
            "category": "architecture",
            "source": "sprint46",
            "agent_context": "dev",
        },
    },
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: App Router — directive 'use client' et hooks React
RAISON: En App Router Next.js, les composants sont Server Components par défaut. Utiliser useState, useEffect ou tout autre hook React dans un Server Component provoque une erreur de build : "You're importing a component that needs useState/useEffect. It only works in a Client Component."
RÈGLE: Tout fichier app/**/*.tsx qui utilise des hooks React (useState, useEffect, useRef, useCallback, useMemo, useReducer) DOIT commencer par la directive exacte "use client" en première ligne.
EXEMPLE_INVALIDE:
  // ❌ Hook React dans Server Component
  import { useState } from 'react'; // ← ERREUR si pas de 'use client'
  export default function Page() {
    const [count, setCount] = useState(0);
  }
EXEMPLE_VALIDE:
  // ✅
  'use client';
  import { useState } from 'react';
  export default function Page() {
    const [count, setCount] = useState(0);
  }
  // OU : déplacer la logique state dans un composant client app/components/Counter.tsx
ERREUR_ATTENDUE: Error: You're importing a component that needs useState. It only works in a Client Component.
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "17-architecture",
            "status": "active",
            "version": "1.0",
            "category": "architecture",
            "source": "sprint46",
            "agent_context": "dev",
        },
    },
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Cohérence modèle Prisma — utilisation dans route handlers
RAISON: Un route handler API qui appelle prisma.X.findMany() alors que le modèle X n'existe pas dans prisma/schema.prisma provoque une erreur runtime Prisma : "Cannot read properties of undefined". Le modèle doit être déclaré AVANT d'être utilisé dans les routes API.
RÈGLE: Tout appel prisma.modelName.method() doit correspondre à un modèle déclaré dans prisma/schema.prisma avec les champs utilisés.
EXEMPLE_INVALIDE:
  // ❌ prisma.comment.create() si 'Comment' n'est pas dans schema.prisma
  await prisma.comment.create({ data: { content, authorId: userId } });
EXEMPLE_VALIDE:
  // ✅ Modèle déclaré dans schema.prisma
  // model Comment {
  //   id        String   @id @default(cuid())
  //   content   String
  //   authorId  String
  //   createdAt DateTime @default(now())
  // }
  await prisma.comment.create({ data: { content, authorId: userId } });
ERREUR_ATTENDUE: TypeError: Cannot read properties of undefined (reading 'create') — prisma.comment est undefined car le modèle n'existe pas
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "17-architecture",
            "status": "active",
            "version": "1.0",
            "category": "architecture",
            "source": "sprint46",
            "agent_context": "dev",
        },
    },
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Import chemin relatif Prisma — utiliser l'alias @/
RAISON: Les chemins relatifs (../../lib/prisma) sont fragiles : selon la profondeur du fichier dans l'arborescence, le chemin change. L'alias '@/*' dans tsconfig.json pointe toujours vers la racine du projet.
RÈGLE: Tout import de lib/prisma.ts doit utiliser l'alias canonique '@/lib/prisma'.
EXEMPLE_INVALIDE:
  import prisma from '../../lib/prisma'; // ❌ chemin relatif fragile
  import prisma from '../../../lib/prisma'; // ❌
EXEMPLE_VALIDE:
  import prisma from '@/lib/prisma'; // ✅ alias canonique, toujours résolu
ERREUR_ATTENDUE: Cannot find module '../../lib/prisma' — erreur selon la profondeur du fichier
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "17-architecture",
            "status": "active",
            "version": "1.0",
            "category": "architecture",
            "source": "sprint46",
            "agent_context": "dev",
        },
    },
]


# =============================================================================
# HELPER pour les nouvelles zones (17b-30)
# =============================================================================

def _s(zone: str, cat: str, text: str, **extra) -> dict:
    return {
        "text": text.strip(),
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": zone,
            "status": "active",
            "version": "1.0",
            "category": cat,
            "source": "factory_standards_v3",
            "agent_context": "dev",
            **extra,
        },
    }


# =============================================================================
# ZONE 17B — PATTERNS DE CODE STACK PRÉVENTIFS
# Source : migrate_zones_17_18.py (migrés depuis rules_dev.md)
# =============================================================================

ZONE_17B_STACK_PATTERNS = [
    _s("17b-stack-patterns", "nextjs", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: force-dynamic — ordre des déclarations dans un fichier Prisma
RAISON: export const dynamic doit être la première ligne avant les imports. TypeScript traite les exports de module avant les imports dans certains bundlers — un dynamic placé après les imports peut être ignoré en mode statique.
DETECTION_REGEX: ^import\\s+(?!.*force-dynamic)
ALTERNATIVE: Placer export const dynamic = 'force-dynamic' avant tout import
EXEMPLE_INVALIDE:
  import { NextResponse } from 'next/server';
  import prisma from '@/lib/prisma';
  export const dynamic = 'force-dynamic'; // ❌ trop tard
EXEMPLE_VALIDE:
  export const dynamic = 'force-dynamic'; // ✅ première ligne absolue
  import { NextResponse } from 'next/server';
  import { auth } from '@clerk/nextjs/server';
  import prisma from '@/lib/prisma';
ERREUR_ATTENDUE: PrismaClientInitializationError — ou build statique sans erreur mais crash runtime
STATUS: active
VERSION: 1.0"""),

    _s("17b-stack-patterns", "prisma", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Prisma singleton — import depuis @/lib/prisma uniquement
RAISON: Instancier PrismaClient directement crée N connexions pool en dev (HMR) et en prod. Le singleton lib/prisma.ts garantit une seule instance partagée via globalThis.
DETECTION_REGEX: new PrismaClient\\(\\)
ALTERNATIVE: import prisma from '@/lib/prisma'
EXEMPLE_INVALIDE:
  import { PrismaClient } from '@prisma/client';
  const prisma = new PrismaClient(); // ❌ nouvelle instance à chaque import
EXEMPLE_VALIDE:
  import prisma from '@/lib/prisma'; // ✅ singleton partagé
ERREUR_ATTENDUE: Too many connections — ou — PrismaClientKnownRequestError: connection pool exhausted
STATUS: active
VERSION: 1.0"""),

    _s("17b-stack-patterns", "auth", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Clerk v6 — auth() guard pattern complet dans route handlers et pages server
RAISON: auth() retourne { userId: string | null }. Prisma attend String (non-nullable). TypeScript refuse de compiler where: { authorId: userId } si le guard est absent. Le guard sert à la fois au narrowing TypeScript ET à la sécurité runtime.
DETECTION_REGEX: await auth\\(\\)(?![\\s\\S]{0,200}if.*!userId)
ALTERNATIVE: Guard immédiat après auth()
EXEMPLE_INVALIDE:
  const { userId } = await auth();
  const items = await prisma.item.findMany({ where: { authorId: userId } }); // ❌ userId peut être null
EXEMPLE_VALIDE:
  const { userId } = await auth();
  if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  // ✅ userId est maintenant string (non-nullable) — TypeScript et Prisma acceptent
  const items = await prisma.item.findMany({ where: { authorId: userId } });
ERREUR_ATTENDUE: TS2345 — Argument of type 'string | null' is not assignable to parameter of type 'string'
STATUS: active
VERSION: 1.0"""),

    _s("17b-stack-patterns", "auth", """ACTION: INTERDIT
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Clerk — authorId dans le body de la requête
RAISON: Accepter authorId depuis le body permet à un client malicieux d'associer une ressource à n'importe quel userId. L'authorId DOIT toujours venir de auth() côté serveur.
DETECTION_REGEX: body\\.authorId|req\\.json\\(\\)[\\s\\S]*authorId|authorId.*body
ALTERNATIVE: const { userId } = await auth(); puis data: { ...body, authorId: userId }
EXEMPLE_INVALIDE:
  const { title, authorId } = await req.json(); // ❌ authorId du client
  await prisma.post.create({ data: { title, authorId } });
EXEMPLE_VALIDE:
  const { userId } = await auth();
  if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const { title } = await req.json(); // ✅ pas d'authorId dans le body
  await prisma.post.create({ data: { title, authorId: userId } }); // ✅ userId de Clerk
ERREUR_ATTENDUE: Faille de sécurité — IDOR / privilege escalation
STATUS: active
VERSION: 1.0"""),

    _s("17b-stack-patterns", "typescript", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript strict — annotation explicite sur tableaux Prisma
RAISON: TypeScript infère never[] pour un tableau déclaré vide puis assigné dans un try/catch. La propriété 'id' n'existe pas sur type 'never' → TS2339 à la compilation. Pattern fetchAll avec .catch() résout le problème en une seule ligne.
DETECTION_REGEX: let \\w+ = \\[\\];[\\s\\S]{0,200}await prisma
ALTERNATIVE: const items: Model[] = await prisma.model.findMany().catch(() => [])
EXEMPLE_INVALIDE:
  let tasks = [];
  try {
    tasks = await prisma.task.findMany({ where: { userId } });
  } catch {
    tasks = [];
  }
  // ❌ TypeScript infère tasks: never[] — tasks[0].title → TS2339
EXEMPLE_VALIDE:
  const tasks: Task[] = await prisma.task.findMany({
    where: { userId },
  }).catch(() => []); // ✅ type explicite, gestion erreur en ligne
ERREUR_ATTENDUE: TS2339 — Property 'id' does not exist on type 'never'
STATUS: active
VERSION: 1.0"""),

    _s("17b-stack-patterns", "typescript", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript strict — types explicites sur callbacks React et destructurings
RAISON: TypeScript strict refuse les paramètres implicitement any (TS7006/TS7031). Les événements React et les destructurings de props doivent avoir des types explicites.
DETECTION_REGEX: onChange=\\{\\(e\\)\\s*=>|onSubmit=\\{\\(e\\)\\s*=>|function \\w+\\(\\{ \\w+ \\}\\)
ALTERNATIVE: Types explicites sur chaque paramètre de callback et destructuring
EXEMPLE_INVALIDE:
  onChange={(e) => setValue(e.target.value)}       // ❌ TS7006
  onSubmit={(e) => { e.preventDefault(); }}        // ❌ TS7006
  function Component({ id }) { ... }               // ❌ TS7031
EXEMPLE_VALIDE:
  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setValue(e.target.value)}   // ✅
  onSubmit={(e: React.FormEvent<HTMLFormElement>) => { e.preventDefault(); }}       // ✅
  function Component({ id }: { id: string }) { ... }                               // ✅
ERREUR_ATTENDUE: TS7006 — Parameter 'e' implicitly has an 'any' type
STATUS: active
VERSION: 1.0"""),

    _s("17b-stack-patterns", "nextjs", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Next.js App Router — imports obligatoires en tête de route handler
RAISON: L'absence d'un des trois imports dans un route handler provoque TS2552 (NextResponse non trouvé) ou TS2305 (auth non trouvé) à la compilation.
DETECTION_REGEX: export (async )?function (GET|POST|PUT|PATCH|DELETE)(?![\\s\\S]{0,300}import.*NextResponse)
ALTERNATIVE: Toujours présenter les trois imports en tête de fichier
EXEMPLE_INVALIDE:
  export const dynamic = 'force-dynamic';
  // ❌ import { NextResponse } manquant
  import { auth } from '@clerk/nextjs/server';
  import prisma from '@/lib/prisma';
  export async function GET() { return NextResponse.json({}) } // TS2552
EXEMPLE_VALIDE:
  export const dynamic = 'force-dynamic';
  import { NextResponse } from 'next/server';      // ✅
  import { auth } from '@clerk/nextjs/server';     // ✅
  import prisma from '@/lib/prisma';               // ✅
  export async function GET() { ... }
ERREUR_ATTENDUE: TS2552 — Cannot find name 'NextResponse'. Did you mean 'Response'?
STATUS: active
VERSION: 1.0"""),

    _s("17b-stack-patterns", "auth", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Zod + Prisma — validation body avec authorId depuis auth() uniquement
RAISON: Deux erreurs fréquentes combinées : (1) passer result.data directement à Prisma expose des champs inattendus et ignore authorId ; (2) accepter authorId depuis le body = faille IDOR. Le pattern correct dissocie les champs validés du body et injecte authorId depuis auth().
DETECTION_REGEX: prisma\\.\\w+\\.create\\(\\s*\\{\\s*data:\\s*result\\.data\\s*\\}
ALTERNATIVE: { data: { ...result.data, authorId: userId } } — authorId vient de auth(), jamais du body
EXEMPLE_INVALIDE:
  const result = CreateTaskSchema.safeParse(body);
  if (!result.success) return NextResponse.json({ error: result.error }, { status: 400 });
  await prisma.task.create({ data: result.data }); // ❌ authorId absent ou potentiellement dans body
EXEMPLE_VALIDE:
  const CreateTaskSchema = z.object({ title: z.string().min(1).max(255) });
  const { userId } = await auth();
  if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const body = await req.json();
  const result = CreateTaskSchema.safeParse(body);
  if (!result.success) return NextResponse.json({ error: result.error }, { status: 400 });
  await prisma.task.create({
    data: { ...result.data, authorId: userId }, // ✅ authorId de auth(), pas du body
  });
  return NextResponse.json(result.data, { status: 201 });
ERREUR_ATTENDUE: Faille IDOR si authorId du body / PrismaClientValidationError si authorId absent
STATUS: active
VERSION: 1.0"""),

    _s("17b-stack-patterns", "nextjs", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Next.js App Router — use client sur composants avec hooks React
RAISON: Les pages app/**page.tsx sont Server Components par défaut. useState/useEffect ne peuvent s'exécuter que côté client. Sans "use client", Next.js lève une erreur runtime "hooks can only be called inside a function component".
DETECTION_REGEX: (useState|useEffect|useRef|useCallback)(?![\\s\\S]{0,50}"use client")
ALTERNATIVE: Ajouter "use client" en première ligne absolue du fichier
EXEMPLE_INVALIDE:
  import { useState } from 'react'; // ❌ Server Component par défaut
  export default function Form() {
    const [value, setValue] = useState('');
    return <input value={value} onChange={e => setValue(e.target.value)} />;
  }
EXEMPLE_VALIDE:
  "use client"; // ✅ première ligne
  import { useState } from 'react';
  export default function Form() {
    const [value, setValue] = useState('');
    return <input value={value} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setValue(e.target.value)} />;
  }
ERREUR_ATTENDUE: Error — useState can only be called inside a Client Component. Add the "use client" directive.
STATUS: active
VERSION: 1.0"""),

    _s("17b-stack-patterns", "prisma", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Prisma — accès aux propriétés déclarées dans schema.prisma uniquement
RAISON: Accéder à un champ absent du schema Prisma provoque TS2339 à la compilation. TypeScript génère les types depuis le schema — tout champ absent est un type error.
DETECTION_REGEX: N/A (détection par tsc)
ALTERNATIVE: Lire prisma/schema.prisma avant d'écrire des accès de champs — n'utiliser que les champs déclarés
EXEMPLE_INVALIDE:
  const task = await prisma.task.findUnique({ where: { id } });
  return task.deadline; // ❌ si 'deadline' absent du schema Task → TS2339
EXEMPLE_VALIDE:
  // schema.prisma : Task { id, title, done, dueDate, userId, createdAt }
  const task = await prisma.task.findUnique({ where: { id } });
  if (!task) return NextResponse.json({ error: 'Not found' }, { status: 404 });
  return NextResponse.json({ id: task.id, title: task.title, dueDate: task.dueDate }); // ✅ champs déclarés
ERREUR_ATTENDUE: TS2339 — Property 'deadline' does not exist on type 'Task'
STATUS: active
VERSION: 1.0"""),
]


# =============================================================================
# ZONE 18 — STANDARDS CORRECTIFS PAR CODE D'ERREUR TYPESCRIPT
# Source : migrate_zones_17_18.py (catalogue tsc_error_catalog.py)
# =============================================================================

ZONE_18_TSC_CORRECTIVE = [
    _s("18-tsc-corrective", "typescript", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript TS2307 — fichier local manquant (module cannot be found)
CODE_ERREUR: TS2307
RAISON: TS2307 sur un chemin local (@/, ./, ../) signifie que le fichier importé n'existe pas sur le disque — pas un problème de npm. Modifier l'import serait une erreur : le chemin est correct, c'est le fichier cible qui manque.
DETECTION_REGEX: error TS2307: Cannot find module '@/|\\./|\\.\\./'
DIAGNOSTIC: Identifier le chemin du module → convertir en chemin fichier (@/components/X → components/X.tsx) → créer le fichier avec write_file
EXEMPLE_INVALIDE:
  // app/page.tsx importe '@/components/TaskList' mais TaskList.tsx n'existe pas
  // ❌ Mauvaise réaction : modifier l'import en '@/components/task-list'
  // ❌ Mauvaise réaction : npm install ...
EXEMPLE_VALIDE:
  // ✅ Bonne réaction : créer components/TaskList.tsx
  write_file('components/TaskList.tsx', `
  "use client";
  import { Task } from '@/lib/types';
  interface Props { tasks: Task[] }
  export default function TaskList({ tasks }: Props) {
    return <ul>{tasks.map(t => <li key={t.id}>{t.title}</li>)}</ul>;
  }
  `)
RÈGLE_EXTENSION: .tsx si composant React (nom en majuscule, dans components/ ou app/) | .ts sinon
ERREUR_ATTENDUE: TS2307 Cannot find module '@/components/TaskList' or its corresponding type declarations.
STATUS: active
VERSION: 1.0"""),

    _s("18-tsc-corrective", "typescript", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript TS2339 never — annotation de type sur tableau Prisma
CODE_ERREUR: TS2339
RAISON: TypeScript infère never[] pour un tableau déclaré vide (let arr = []) puis assigné dans un try/catch. Toute propriété accédée sur never[] provoque TS2339. La solution est d'annoter explicitement le type du tableau au point de déclaration.
DETECTION_REGEX: error TS2339.*type 'never'
DIAGNOSTIC: Trouver la déclaration du tableau → ajouter annotation de type Model[] → utiliser pattern .catch(() => [])
EXEMPLE_INVALIDE:
  let tasks = []; // ❌ TypeScript infère never[]
  try {
    tasks = await prisma.task.findMany({ where: { userId } });
  } catch {
    tasks = [];
  }
  return tasks[0].id; // ❌ TS2339 : Property 'id' does not exist on type 'never'
EXEMPLE_VALIDE:
  // ✅ Option 1 : annotation explicite + catch inline
  const tasks: Task[] = await prisma.task.findMany({ where: { userId } }).catch(() => []);

  // ✅ Option 2 : annotation + try/catch
  let tasks: Task[] = [];
  try {
    tasks = await prisma.task.findMany({ where: { userId } });
  } catch {
    tasks = [];
  }
ERREUR_ATTENDUE: TS2339 — Property 'id' does not exist on type 'never'
STATUS: active
VERSION: 1.0"""),

    _s("18-tsc-corrective", "typescript", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript TS2304 — nom introuvable dans lib/types.ts
CODE_ERREUR: TS2304
RAISON: TS2304 "Cannot find name X" signifie que le type/interface/classe X n'est pas importé ou exporté dans le scope courant. Dans la factory, cela vise souvent des types générés dans lib/types.ts qui ont un nom différent du nom attendu.
DETECTION_REGEX: error TS2304: Cannot find name '\\w+'
DIAGNOSTIC: Lire lib/types.ts → identifier les exports réels → corriger l'utilisation ou l'import
ÉTAPES:
  1. read_file('lib/types.ts') — liste les exports réels
  2. Comparer avec le nom utilisé — souvent typo (CreatePostInput au lieu de CreateTaskInput)
  3. Corriger l'import ou le nom dans le fichier fautif
EXEMPLE_INVALIDE:
  import { CreatePostInput } from '@/lib/types'; // ❌ si lib/types.ts exporte CreateTaskInput
  const body: CreatePostInput = await req.json(); // TS2304
EXEMPLE_VALIDE:
  import { CreateTaskInput } from '@/lib/types'; // ✅ nom exact depuis lib/types.ts
  const body: CreateTaskInput = await req.json();
ERREUR_ATTENDUE: TS2304 — Cannot find name 'CreatePostInput'
STATUS: active
VERSION: 1.0"""),

    _s("18-tsc-corrective", "typescript", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript TS7006/TS7031 — type explicite sur paramètre de callback React
CODE_ERREUR: TS7006
RAISON: TypeScript strict (noImplicitAny: true) refuse les paramètres de fonction sans type déclaré. Dans les composants React, les callbacks d'événements (onChange, onSubmit) et les destructurings de props doivent avoir des types explicites.
DETECTION_REGEX: error TS7006.*implicitly has an 'any' type|error TS7031.*implicitly has an 'any' type
DIAGNOSTIC: Identifier le paramètre non typé → ajouter le type React ou un type inline
TYPES_REACT_COURANTS:
  onChange input     → e: React.ChangeEvent<HTMLInputElement>
  onChange textarea  → e: React.ChangeEvent<HTMLTextAreaElement>
  onChange select    → e: React.ChangeEvent<HTMLSelectElement>
  onSubmit form      → e: React.FormEvent<HTMLFormElement>
  onClick button     → e: React.MouseEvent<HTMLButtonElement>
  destructuring prop → { id }: { id: string }
EXEMPLE_INVALIDE:
  onChange={(e) => setValue(e.target.value)}  // ❌ TS7006
  function Card({ id }) { ... }              // ❌ TS7031
EXEMPLE_VALIDE:
  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setValue(e.target.value)}  // ✅
  function Card({ id }: { id: string }) { ... }                                   // ✅
ERREUR_ATTENDUE: TS7006 — Parameter 'e' implicitly has an 'any' type
STATUS: active
VERSION: 1.0"""),

    _s("18-tsc-corrective", "typescript", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript TS2531 — null check avant accès sur résultat Prisma findUnique
CODE_ERREUR: TS2531
RAISON: prisma.model.findUnique() retourne Model | null. TypeScript refuse d'accéder à une propriété d'un objet potentiellement null sans guard préalable. Ce guard est aussi une bonne pratique API REST (404 si ressource introuvable).
DETECTION_REGEX: error TS2531: Object is possibly 'null'
DIAGNOSTIC: Ajouter un guard null après findUnique → retourner 404 si null
EXEMPLE_INVALIDE:
  const task = await prisma.task.findUnique({ where: { id } });
  return NextResponse.json({ id: task.id, title: task.title }); // ❌ TS2531 : task peut être null
EXEMPLE_VALIDE:
  const task = await prisma.task.findUnique({ where: { id } });
  if (!task) return NextResponse.json({ error: 'Not found' }, { status: 404 }); // ✅ guard null
  return NextResponse.json({ id: task.id, title: task.title }); // ✅ task est Task (non-null)
ERREUR_ATTENDUE: TS2531 — Object is possibly 'null'
STATUS: active
VERSION: 1.0"""),

    _s("18-tsc-corrective", "typescript", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript TS2345 — type 'string | null' non assignable à 'string' (auth guard)
CODE_ERREUR: TS2345
RAISON: auth() retourne { userId: string | null }. Prisma n'accepte pas string | null dans where: { authorId: userId }. Le narrowing TypeScript s'obtient uniquement avec un guard if (!userId) return 401 — après ce guard, userId est string.
DETECTION_REGEX: error TS2345.*'string \\| null'.*'string'
DIAGNOSTIC: Vérifier que le guard if (!userId) précède l'accès Prisma — si absent, l'ajouter
EXEMPLE_INVALIDE:
  const { userId } = await auth();
  const items = await prisma.item.findMany({
    where: { authorId: userId }, // ❌ TS2345 : string | null n'est pas string
  });
EXEMPLE_VALIDE:
  const { userId } = await auth();
  if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 }); // ✅ narrowing
  const items = await prisma.item.findMany({
    where: { authorId: userId }, // ✅ userId est string après le guard
  });
ERREUR_ATTENDUE: TS2345 — Argument of type 'string | null' is not assignable to parameter of type 'string'
STATUS: active
VERSION: 1.0"""),

    _s("18-tsc-corrective", "typescript", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript TS2339 — propriété absente du schema Prisma (champ inexistant)
CODE_ERREUR: TS2339
RAISON: Accéder à un champ non déclaré dans prisma/schema.prisma provoque TS2339. TypeScript génère les types Prisma depuis le schema — tout champ absent est une erreur de type. Ce n'est PAS une erreur never[] (cf. standard séparé) mais une vraie propriété manquante.
DETECTION_REGEX: error TS2339: Property '\\w+' does not exist on type '(?!never)\\w+'
DIAGNOSTIC: Lire prisma/schema.prisma → vérifier que le champ existe → corriger le nom ou ne pas y accéder
EXEMPLE_INVALIDE:
  // schema.prisma : Task { id, title, done, userId, createdAt }
  const task = await prisma.task.findUnique({ where: { id } });
  return task.deadline; // ❌ TS2339 : 'deadline' absent du schema
EXEMPLE_VALIDE:
  // schema.prisma : Task { id, title, done, dueDate, userId, createdAt }
  const task = await prisma.task.findUnique({ where: { id } });
  if (!task) return NextResponse.json({ error: 'Not found' }, { status: 404 });
  return NextResponse.json({ id: task.id, title: task.title, dueDate: task.dueDate }); // ✅ champs déclarés
ERREUR_ATTENDUE: TS2339 — Property 'deadline' does not exist on type 'Task'
STATUS: active
VERSION: 1.0"""),
]


# =============================================================================
# ZONE 19 — STANDARDS SAAS SENIOR
# Source : migrate_zone_19_saas_senior.py
# =============================================================================

ZONE_19_SAAS_SENIOR = [
    _s("19-saas-senior", "pages", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Next.js App Router — Server Component page liste
RAISON: Une page listant des entités doit afficher les données réelles depuis Prisma. Retourner un simple <h1> sans données est interdit — l'application serait inutilisable.
DETECT: return\\s+<h1>[^<]+</h1>
INSTEAD: Appeler prisma.model.findMany({ where: { userId } }) et mapper les résultats en JSX
EXEMPLE_INVALIDE:
  export const dynamic = 'force-dynamic';
  const InvoicesPage = () => {
    return <h1>Invoices List</h1>; // ❌ aucune donnée réelle
  };
EXEMPLE_VALIDE:
  export const dynamic = 'force-dynamic';
  import { auth } from '@clerk/nextjs/server';
  import { redirect } from 'next/navigation';
  import prisma from '@/lib/prisma';

  export default async function InvoicesPage() {
    const { userId } = await auth();
    if (!userId) redirect('/sign-in');
    const items = await prisma.invoice.findMany({
      where: { userId },
      orderBy: { createdAt: 'desc' },
    });
    return (
      <div>
        <h1>Mes factures</h1>
        {items.length === 0 ? (
          <p>Aucun enregistrement pour le moment.</p>
        ) : (
          <ul>{items.map((item) => <li key={item.id}>{item.id}</li>)}</ul>
        )}
      </div>
    );
  }
ERREUR_ATTENDUE: Page vide, utilisateur ne voit aucune donnée malgré les enregistrements en base
STATUS: active
VERSION: 1.0"""),

    _s("19-saas-senior", "pages", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Next.js App Router — Server Component page détail [id]
RAISON: Une page détail doit récupérer l'entité par son id, vérifier l'ownership, et afficher ses champs réels. notFound() si absent ou non autorisé.
DETECT: params\\.id
INSTEAD: findUnique + vérification userId + rendu des champs du modèle
EXEMPLE_INVALIDE:
  const Page = ({ params }: { params: { id: string } }) => {
    return <h1>Item {params.id}</h1>; // ❌ champ id affiché, pas le contenu
  };
EXEMPLE_VALIDE:
  export const dynamic = 'force-dynamic';
  import { auth } from '@clerk/nextjs/server';
  import { notFound, redirect } from 'next/navigation';
  import prisma from '@/lib/prisma';

  export default async function ItemPage({ params }: { params: { id: string } }) {
    const { userId } = await auth();
    if (!userId) redirect('/sign-in');
    const item = await prisma.item.findUnique({ where: { id: params.id } });
    if (!item || item.userId !== userId) notFound();
    return <article><h1>{item.title}</h1></article>;
  }
ERREUR_ATTENDUE: Page blanche ou données fictives au lieu du contenu réel
STATUS: active
VERSION: 1.0"""),

    _s("19-saas-senior", "forms", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Next.js App Router — Client Component formulaire de création
RAISON: Un formulaire doit soumettre les données à la route API correspondante via fetch, gérer les erreurs et rediriger après succès. "use client" DOIT être la ligne 1 absolue.
DETECT: useState.*handleSubmit
INSTEAD: "use client" ligne 1, useState pour les champs, fetch vers /api/resource, router.push après succès
EXEMPLE_INVALIDE:
  export const dynamic = 'force-dynamic';
  'use client'; // ❌ use client n'est pas en ligne 1 absolue
  const NewPage = () => {
    return <h1>Create New</h1>; // ❌ formulaire absent
  };
EXEMPLE_VALIDE:
  "use client";
  import { useState } from 'react';
  import { useRouter } from 'next/navigation';

  export default function NewItemPage() {
    const router = useRouter();
    const [title, setTitle] = useState('');
    const [error, setError] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
      e.preventDefault();
      const res = await fetch('/api/items', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title }),
      });
      if (!res.ok) { setError('Erreur lors de la création'); return; }
      router.push('/items');
    };

    return (
      <form onSubmit={handleSubmit}>
        {error && <p style={{ color: 'red' }}>{error}</p>}
        <input type="text" value={title} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setTitle(e.target.value)} required />
        <button type="submit">Créer</button>
      </form>
    );
  }
ERREUR_ATTENDUE: Formulaire non fonctionnel, données non envoyées à l'API, pas de redirection après succès
STATUS: active
VERSION: 1.0"""),

    _s("19-saas-senior", "security", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Next.js API Routes — sécurité ownership PATCH/PUT/DELETE
RAISON: Tout handler qui modifie ou supprime une ressource doit vérifier que l'enregistrement appartient à l'utilisateur authentifié. Sans ce check, n'importe quel utilisateur connecté peut modifier les données d'un autre (privilege escalation horizontal).
DETECT: prisma\\.\\w+\\.update|prisma\\.\\w+\\.delete
INSTEAD: findUnique → vérification userId === record.userId → 403 si différent → puis update/delete
EXEMPLE_INVALIDE:
  export async function PATCH(request: Request, { params }: { params: { id: string } }) {
    const { userId } = await auth();
    if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    // ❌ pas de vérification ownership
    const item = await prisma.item.update({ where: { id: params.id }, data: { status: 'done' } });
    return NextResponse.json(item);
  }
EXEMPLE_VALIDE:
  export async function PATCH(request: Request, { params }: { params: { id: string } }) {
    const { userId } = await auth();
    if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    const existing = await prisma.item.findUnique({ where: { id: params.id } });
    if (!existing || existing.userId !== userId) {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
    }
    const body = await request.json();
    const result = updateSchema.safeParse(body);
    if (!result.success) return NextResponse.json({ error: result.error.errors }, { status: 400 });
    const item = await prisma.item.update({ where: { id: params.id }, data: result.data });
    return NextResponse.json(item);
  }
ERREUR_ATTENDUE: Privilege escalation — utilisateur A peut modifier les données de l'utilisateur B
STATUS: active
VERSION: 1.0"""),

    _s("19-saas-senior", "architecture", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Next.js — Data Access Layer lib/services/
RAISON: Les pages ne doivent pas importer prisma directement. Encapsuler les requêtes Prisma dans lib/services/<model>.service.ts garantit la réutilisabilité, la testabilité et la cohérence de l'ownership check.
DETECT: import prisma from.*lib/prisma.*page\\.tsx
INSTEAD: Créer lib/services/<model>.service.ts avec findMany/findUnique/create/update/delete. Les pages importent le service, pas prisma.
EXEMPLE_INVALIDE:
  // app/items/page.tsx — ❌ Prisma directement dans la page
  import prisma from '@/lib/prisma';
  export default async function ItemsPage() {
    const items = await prisma.item.findMany({ where: { userId } });
  }
EXEMPLE_VALIDE:
  // lib/services/item.service.ts ✅
  import prisma from '@/lib/prisma';
  export const itemService = {
    findMany: (userId: string) => prisma.item.findMany({ where: { userId }, orderBy: { createdAt: 'desc' } }),
    findUnique: async (id: string, userId: string) => {
      const r = await prisma.item.findUnique({ where: { id } });
      if (!r || r.userId !== userId) return null;
      return r;
    },
    create: (data: { title: string }, userId: string) => prisma.item.create({ data: { ...data, userId } }),
  };
  // app/items/page.tsx ✅
  import { itemService } from '@/lib/services/item.service';
ERREUR_ATTENDUE: Code dupliqué, ownership check oublié dans certaines routes, pages non testables isolément
STATUS: active
VERSION: 1.0"""),

    _s("19-saas-senior", "database", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Prisma — relations @relation entre modèles liés
RAISON: Sans @relation explicite, Prisma ne connaît pas le lien entre les modèles. include: { client: true } est impossible, les cascades ne fonctionnent pas, et les requêtes jointes sont impossibles. Un champ clientId sans @relation est une foreign key "fantôme".
DETECT: \\w+Id\\s+String
INSTEAD: Déclarer @relation avec fields et references sur le modèle enfant, et le champ tableau sur le modèle parent
EXEMPLE_INVALIDE:
  model Invoice {
    id       String @id @default(uuid())
    clientId String // ❌ FK sans @relation — Prisma ignore le lien
  }
EXEMPLE_VALIDE:
  model Client {
    id       String    @id @default(uuid())
    invoices Invoice[] // ✅ relation inverse déclarée
  }
  model Invoice {
    id       String @id @default(uuid())
    client   Client @relation(fields: [clientId], references: [id]) // ✅
    clientId String
    @@index([userId])
    @@index([clientId])
  }
ERREUR_ATTENDUE: PrismaClientValidationError: Unknown field 'client' — ou jointures impossibles
STATUS: active
VERSION: 1.0"""),

    _s("19-saas-senior", "database", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Prisma — @@index sur les champs de filtrage fréquents
RAISON: Sans index, un findMany({ where: { userId } }) fait un full table scan. Avec 10k lignes, la requête prend plusieurs secondes. Tous les champs utilisés dans where, orderBy ou join doivent avoir un index.
DETECT: userId\\s+String(?!.*@@index)
INSTEAD: Ajouter @@index([userId]) sur tout modèle avec un champ userId ou filtré fréquemment
EXEMPLE_INVALIDE:
  model Task {
    id     String @id @default(uuid())
    userId String // ❌ pas d'index — full scan à chaque requête
  }
EXEMPLE_VALIDE:
  model Task {
    id        String   @id @default(uuid())
    userId    String
    createdAt DateTime @default(now())
    @@index([userId])
    @@index([userId, createdAt])
  }
ERREUR_ATTENDUE: Requêtes lentes en production, dégradation des performances avec la croissance des données
STATUS: active
VERSION: 1.0"""),

    _s("19-saas-senior", "auth", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Next.js App Router — redirect() dans les Server Components protégés
RAISON: Dans un Server Component, auth() peut retourner userId=null pour un visiteur non connecté. Retourner null ou un composant vide expose des erreurs Prisma en production. redirect('/sign-in') est la seule réponse correcte pour une page protégée.
DETECT: if\\s*\\(!userId\\)\\s*return\\s*null
INSTEAD: import { redirect } from 'next/navigation' — redirect('/sign-in') si !userId
EXEMPLE_INVALIDE:
  export default async function DashboardPage() {
    const { userId } = await auth();
    if (!userId) return null; // ❌ page blanche — pas de redirection
    const data = await prisma.invoice.findMany({ where: { userId } }); // crash si userId null
  }
EXEMPLE_VALIDE:
  import { redirect } from 'next/navigation';
  export default async function DashboardPage() {
    const { userId } = await auth();
    if (!userId) redirect('/sign-in'); // ✅ redirection propre
    const data = await prisma.invoice.findMany({ where: { userId } });
    return <div>...</div>;
  }
ERREUR_ATTENDUE: Page blanche pour utilisateur non connecté, ou crash Prisma avec userId=null
STATUS: active
VERSION: 1.0"""),
]


# =============================================================================
# ZONE 20 — SERVICE DAL PATTERN
# Source : migrate_zone_20_dal_service.py
# =============================================================================

ZONE_20_DAL_SERVICE = [
    _s("20-dal-service", "services", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript — lib/services/<model>.service.ts
RAISON: Centraliser tous les accès Prisma dans un objet service garantit l'ownership check systématique et fournit un contrat stable que les pages peuvent importer. Sans DAL, le LLM oublie les ownership checks dans certaines routes.
NOMMAGE: Modèle Post → fichier post.service.ts → objet postService. Modèle InvoiceItem → fichier invoice-item.service.ts → objet invoiceItemService (kebab pour le fichier, camelCase pour l'objet).
DETECT: export\\s+function\\s+get[A-Z]|export\\s+async\\s+function\\s+get[A-Z]
INSTEAD: Exporter un objet unique avec méthodes (findMany, findUnique, create, update, delete)
EXEMPLE_INVALIDE:
  export async function getExpenses(userId: string) { ... }
  export async function getExpenseById(id: string) { ... }
  export async function createExpense(data: any) { ... }
EXEMPLE_VALIDE:
  import prisma from '@/lib/prisma'

  export const expenseService = {
    findMany: (userId: string) =>
      prisma.expense.findMany({ where: { userId }, orderBy: { createdAt: 'desc' } }),

    findUnique: async (id: string, userId: string) => {
      const r = await prisma.expense.findUnique({ where: { id } })
      if (!r || r.userId !== userId) return null
      return r
    },

    create: (data: { amount: number; category: string; description: string }, userId: string) =>
      prisma.expense.create({ data: { ...data, userId } }),

    update: async (id: string, data: Partial<{ amount: number; category: string }>, userId: string) => {
      const r = await prisma.expense.findUnique({ where: { id } })
      if (!r || r.userId !== userId) throw new Error('Forbidden')
      return prisma.expense.update({ where: { id }, data })
    },

    delete: async (id: string, userId: string) => {
      const r = await prisma.expense.findUnique({ where: { id } })
      if (!r || r.userId !== userId) throw new Error('Forbidden')
      await prisma.expense.delete({ where: { id } })
    },
  }
STATUS: active
VERSION: 1.0"""),

    _s("20-dal-service", "services", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript — lib/services/ avec authorId (modèles Blog/CMS)
RAISON: Certains modèles (Post, Article) utilisent authorId au lieu de userId. Le service doit utiliser le nom de champ exact du schéma Prisma — sinon TS2339 sur r.userId inexistant.
DETECT: r\\.userId.*authorId|where.*userId.*authorId
INSTEAD: Utiliser le champ réel du modèle (authorId) dans tous les where et ownership checks
EXEMPLE_INVALIDE:
  findMany: (userId: string) => prisma.post.findMany({ where: { userId } })
  // Erreur : Post n'a pas de champ userId, il a authorId
EXEMPLE_VALIDE:
  export const postService = {
    findMany: (authorId: string) =>
      prisma.post.findMany({ where: { authorId }, orderBy: { createdAt: 'desc' } }),
    findUnique: async (id: string, userId: string) => {
      const r = await prisma.post.findUnique({ where: { id } })
      if (!r || r.authorId !== userId) return null
      return r
    },
    create: (data: { title: string; content: string; slug: string }, authorId: string) =>
      prisma.post.create({ data: { ...data, authorId } }),
  }
STATUS: active
VERSION: 1.0"""),

    _s("20-dal-service", "services", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript — import du service DAL dans une page (objet, pas fonctions nommées)
RAISON: Le service DAL exporte un objet unique (expenseService). Importer des fonctions nommées qui n'existent pas (getExpenses, getExpenseById) provoque TS2305 à la compilation. Toujours importer l'objet service et appeler sa méthode.
DETECT: import\\s+\\{\\s*get[A-Z][a-zA-Z]+\\s*\\}\\s+from\\s+'@/lib/services
INSTEAD: Importer l'objet service et appeler la méthode appropriée
EXEMPLE_INVALIDE:
  import { getExpenses, getExpenseById } from '@/lib/services/expense.service'
  // TS2305 : ces exports n'existent pas (le fichier exporte expenseService)
EXEMPLE_VALIDE:
  import { expenseService } from '@/lib/services/expense.service'

  export default async function ExpensesPage() {
    const { userId } = await auth()
    if (!userId) redirect('/sign-in')
    const expenses = await expenseService.findMany(userId)
    return (
      <ul>{expenses.map(e => <li key={e.id}>{e.id}</li>)}</ul>
    )
  }
ERREUR_ATTENDUE: TS2305 — Module '@/lib/services/expense.service' has no exported member 'getExpenses'
STATUS: active
VERSION: 1.0"""),

    _s("20-dal-service", "types", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript — lib/types.ts
RAISON: lib/types.ts centralise les types partagés entre pages, services et routes API. Le LLM doit le générer en premier pour pouvoir l'importer dans les services et pages. Sans ce fichier, les imports depuis '@/lib/types' échouent avec TS2307.
DETECT: import.*from\\s+'@/lib/types'
INSTEAD: Générer lib/types.ts en tout premier, avant les services et les pages
EXEMPLE_VALIDE:
  // lib/types.ts
  export type { Expense, Client, Invoice } from '@prisma/client'

  export type CreateExpenseInput = {
    amount: number
    category: string
    description: string
    date: string
  }
  export type UpdateExpenseInput = Partial<CreateExpenseInput>

  export type ApiResponse<T> = { data: T } | { error: string }
  export type PaginatedResponse<T> = { data: T[]; total: number }

  // Importer dans les services :
  // import type { CreateExpenseInput, UpdateExpenseInput } from '@/lib/types'
STATUS: active
VERSION: 1.0"""),
]


# =============================================================================
# ZONE 21 — PAGINATION
# Source : migrate_zone_21_pagination.py
# =============================================================================

ZONE_21_PAGINATION = [
    _s("21-pagination", "routes", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript — pagination findMany skip/take avec PaginatedResponse<T>
RAISON: Tout findMany() sans skip/take est un bottleneck de scalabilité. Même un MVP doit paginer ses listes dès le départ — corriger après coup casse l'API frontend.
DETECT: prisma\\.\\w+\\.findMany\\(\\{\\s*where
INSTEAD: Utiliser skip/take avec pageSize=20 par défaut, plafonné à 100. Toujours retourner { data, total, page, pageSize }.
EXEMPLE_INVALIDE:
  const items = await prisma.item.findMany({ where: { userId } })
  return NextResponse.json(items)
EXEMPLE_VALIDE:
  // lib/types.ts
  export type PaginatedResponse<T> = { data: T[]; total: number; page: number; pageSize: number }

  // app/api/items/route.ts
  export async function GET(req: Request) {
    const { userId } = await auth()
    if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    const url = new URL(req.url)
    const page = Math.max(1, parseInt(url.searchParams.get('page') ?? '1'))
    const pageSize = Math.min(100, parseInt(url.searchParams.get('pageSize') ?? '20'))
    const skip = (page - 1) * pageSize
    const [data, total] = await prisma.$transaction([
      prisma.item.findMany({ where: { userId }, skip, take: pageSize, orderBy: { createdAt: 'desc' } }),
      prisma.item.count({ where: { userId } }),
    ])
    return NextResponse.json({ data, total, page, pageSize } satisfies PaginatedResponse<typeof data[0]>)
  }
STATUS: active
VERSION: 1.0"""),
]


# =============================================================================
# ZONE 22 — GESTION DES ERREURS PRISMA
# Source : migrate_zone_22_prisma_errors.py
# =============================================================================

ZONE_22_PRISMA_ERRORS = [
    _s("22-prisma-errors", "error-handling", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript — handlePrismaError() dans les routes API
RAISON: Sans catch des erreurs Prisma connues, un conflit P2002 retourne une 500 générique au lieu d'un 409 clair. Le client ne peut pas distinguer "doublon" de "panne serveur". lib/prisma-errors.ts est pré-généré par le pipeline — toujours l'importer.
DETECT: catch.*error.*500|catch.*e.*Internal.server
INSTEAD: Importer handlePrismaError et déléguer le catch Prisma
EXEMPLE_INVALIDE:
  } catch (e) {
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
EXEMPLE_VALIDE:
  import { handlePrismaError } from '@/lib/prisma-errors'

  } catch (error) {
    const { status, message } = handlePrismaError(error)
    return NextResponse.json({ error: message }, { status })
  }
STATUS: active
VERSION: 1.0"""),

    _s("22-prisma-errors", "error-handling", """ACTION: INFORMATIF
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript — mapping codes Prisma P2002/P2025/P2003 → HTTP
RAISON: Référence des codes Prisma fréquents dans les apps SaaS — à utiliser dans les catch.
MAPPING:
  P2002 → 409 Conflict (unique constraint violated — ex: email déjà utilisé)
  P2025 → 404 Not Found (record to update/delete does not exist)
  P2003 → 400 Bad Request (foreign key constraint failed — parent introuvable)
  P2014 → 400 Bad Request (required relation violation)
  autres → 500 Internal Server Error
EXEMPLE_VALIDE:
  switch (error.code) {
    case 'P2002': return { status: 409, message: 'A record with this value already exists' }
    case 'P2025': return { status: 404, message: 'Record not found' }
    case 'P2003': return { status: 400, message: 'Foreign key constraint failed' }
    default:      return { status: 500, message: 'Internal server error' }
  }
STATUS: active
VERSION: 1.0"""),
]


# =============================================================================
# ZONE 23 — CreateInput SANS userId (lib/types.ts)
# Source : migrate_zone_23_create_input.py
# =============================================================================

ZONE_23_CREATE_INPUT = [
    _s("23-create-input", "types", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript — CreateXxxInput sans userId dans lib/types.ts
RAISON: CreateXxxInput ne doit jamais contenir userId/authorId — c'est une faille de sécurité (le client contrôlerait l'ownership) et une erreur TS2322 au build (type incompatible avec Prisma input). Le champ owner vient toujours de auth() et est passé séparément au service.
DETECT: CreateInput.*userId|type Create.*\\{[^}]*userId
INSTEAD: Déclarer CreateXxxInput avec seulement les champs métier, passer ownerId séparément
EXEMPLE_INVALIDE:
  export type CreateExpenseInput = {
    amount: number
    category: string
    userId: string  // ← INTERDIT : TS2322 + faille sécurité
  }
EXEMPLE_VALIDE:
  export type CreateExpenseInput = {
    amount: number
    category: string
    description: string
    date: string
  }
  // Dans le service : prisma.expense.create({ data: { ...data, userId: ownerId } })
STATUS: active
VERSION: 1.0"""),
]


# =============================================================================
# ZONE 24 — PRÉVENTION N+1
# Source : migrate_zone_24_n1_prevention.py
# =============================================================================

ZONE_24_N1_PREVENTION = [
    _s("24-n1-prevention", "services", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Prisma include — prévention N+1 avec include au lieu de boucle findUnique
RAISON: Une boucle findUnique dans un findMany = N+1 requêtes. Avec 100 factures, ça fait 101 requêtes au lieu de 1. Exemple réel production : 1 848 requêtes → 8,9s latence. Après fix include : 2 requêtes → 38ms.
DETECT: findMany.*\\.map.*findUnique|Promise\\.all.*findUnique
INSTEAD: Utiliser include pour charger les relations en une seule requête
EXEMPLE_INVALIDE:
  const invoices = await prisma.invoice.findMany({ where: { userId } })
  const enriched = await Promise.all(
    invoices.map(inv => prisma.client.findUnique({ where: { id: inv.clientId } }))
  )  // ← N+1 : 1 + N requêtes
EXEMPLE_VALIDE:
  const invoices = await prisma.invoice.findMany({
    where: { userId },
    include: {
      client: { select: { id: true, name: true, email: true } },
    },
    orderBy: { createdAt: 'desc' },
  })  // ← 1 requête avec JOIN
STATUS: active
VERSION: 1.0"""),

    _s("24-n1-prevention", "services", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Prisma include vs select — règle de combinaison
RAISON: include et select ne peuvent pas être utilisés au même niveau simultanément — Prisma retourne une erreur. Pour sélectionner des champs spécifiques dans une relation, utiliser select imbriqué dans include.
DETECT: include.*select.*\\{|select.*include.*\\{
INSTEAD: select imbriqué dans include pour les champs de relation — jamais les deux au niveau racine
EXEMPLE_INVALIDE:
  prisma.invoice.findMany({
    select: { id: true, title: true },
    include: { client: true },  // ← Erreur Prisma : cannot use both
  })
EXEMPLE_VALIDE:
  prisma.invoice.findMany({
    where: { userId },
    include: {
      client: { select: { id: true, name: true } },
    },
  })
STATUS: active
VERSION: 1.0"""),
]


# =============================================================================
# ZONE 26 — TRANSACTIONS PRISMA
# Source : migrate_zone_26_transactions.py
# =============================================================================

ZONE_26_TRANSACTIONS = [
    _s("26-transactions", "services", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Prisma $transaction — mutations multi-tables atomiques
RAISON: Les opérations multi-tables sans transaction laissent la base dans un état incohérent si une étape échoue (ex: Invoice créée mais InvoiceItems non créés). $transaction garantit le rollback automatique si une opération échoue.
DETECT: prisma\\.\\w+\\.create.*prisma\\.\\w+\\.create|prisma\\.\\w+\\.update.*prisma\\.\\w+
INSTEAD: $transaction([]) pour les opérations indépendantes, $transaction(async tx =>) pour les opérations conditionnelles
EXEMPLE_INVALIDE:
  // Sans transaction : si createMany échoue, l'invoice existe sans items
  const invoice = await prisma.invoice.create({ data: { userId, title, amount } })
  await prisma.invoiceItem.createMany({ data: items.map(i => ({ ...i, invoiceId: invoice.id })) })
EXEMPLE_VALIDE:
  // Interactive : quand une étape dépend du résultat de la précédente
  const invoice = await prisma.$transaction(async (tx) => {
    const inv = await tx.invoice.create({ data: { userId, title, amount } })
    await tx.invoiceItem.createMany({
      data: items.map(item => ({ ...item, invoiceId: inv.id })),
    })
    return inv
  })
STATUS: active
VERSION: 1.0"""),

    _s("26-transactions", "services", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Prisma $transaction interactive — règle absolue tx vs prisma dans le callback
RAISON: Dans une transaction interactive, utiliser l'instance globale prisma au lieu de tx crée un deadlock : la connexion est déjà occupée par la transaction et la requête externe attend indéfiniment jusqu'au timeout. En serverless, ce deadlock est silencieux et difficile à déboguer.
DETECT: \\$transaction.*async.*tx.*prisma\\.(?!\\$)
INSTEAD: Toujours remplacer prisma par tx à l'intérieur du callback de $transaction
EXEMPLE_INVALIDE:
  await prisma.$transaction(async (tx) => {
    const inv = await tx.invoice.create({ data })
    await prisma.invoiceItem.createMany({ data: items })  // ← prisma au lieu de tx → DEADLOCK
  })
EXEMPLE_VALIDE:
  await prisma.$transaction(async (tx) => {
    const inv = await tx.invoice.create({ data })
    await tx.invoiceItem.createMany({ data: items })  // ← tx partout dans le callback
  })
STATUS: active
VERSION: 1.0"""),
]


# =============================================================================
# ZONE 27 — LOGGING STRUCTURÉ (PINO)
# Source : migrate_zone_27_logging.py
# =============================================================================

ZONE_27_LOGGING = [
    _s("27-logging", "routes", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Pino — logging structuré dans les routes API (lib/logger.ts)
RAISON: console.log en production ne porte aucun contexte (userId, route, durée). Sans logging structuré, déboguer une erreur en production revient à chercher une aiguille dans une botte de foin. lib/logger.ts est pré-généré — toujours l'importer.
DETECT: console\\.log|console\\.error|console\\.warn
INSTEAD: Importer logger depuis @/lib/logger et utiliser child logger par route
EXEMPLE_INVALIDE:
  } catch (error) {
    console.error('Erreur:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
EXEMPLE_VALIDE:
  import logger from '@/lib/logger'

  const log = logger.child({ route: 'POST /api/invoices' })

  export async function POST(req: Request) {
    const { userId } = await auth()
    if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    try {
      const body = await req.json()
      const result = CreateInvoiceBodySchema.safeParse(body)
      if (!result.success) {
        log.warn({ userId, issues: result.error.issues }, 'Validation failed')
        return NextResponse.json({ error: 'Validation error' }, { status: 400 })
      }
      const invoice = await invoiceService.create(result.data, userId)
      log.info({ userId, invoiceId: invoice.id }, 'Invoice created')
      return NextResponse.json(invoice, { status: 201 })
    } catch (error) {
      const { status, message } = handlePrismaError(error)
      log.error({ userId, error }, 'Unexpected error')
      return NextResponse.json({ error: message }, { status })
    }
  }
STATUS: active
VERSION: 1.0"""),
]


# =============================================================================
# ZONE 28 — CONNECTION POOLING PRISMA (SERVERLESS)
# Source : migrate_zone_28_connection_pooling.py
# =============================================================================

ZONE_28_CONNECTION_POOLING = [
    _s("28-connection-pooling", "infrastructure", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Prisma serverless — connection_limit=1 dans DATABASE_URL
RAISON: Sans connection_limit=1, chaque instance serverless crée son propre pool. Avec 10 instances × pool par défaut ≈ 10 connexions = 100 connexions simultanées → épuisement PostgreSQL. connection_limit=1 + pool_timeout=20 est le minimum viable pour Vercel/serverless.
DETECT: DATABASE_URL.*postgresql://(?!.*connection_limit)
INSTEAD: Ajouter ?connection_limit=1&pool_timeout=20 à la fin de DATABASE_URL
EXEMPLE_INVALIDE:
  DATABASE_URL=postgresql://user:password@localhost:5432/mydb
EXEMPLE_VALIDE:
  DATABASE_URL=postgresql://user:password@localhost:5432/mydb?connection_limit=1&pool_timeout=20
STATUS: active
VERSION: 1.0"""),

    _s("28-connection-pooling", "infrastructure", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Prisma — pattern globalThis singleton dans lib/prisma.ts
RAISON: Le hot reload Next.js en dev crée une nouvelle instance PrismaClient à chaque modification de fichier. Sans globalThis singleton, on accumule des connexions jusqu'à "too many clients" en dev.
DETECT: new PrismaClient\\(\\)|globalForPrisma
INSTEAD: Pattern globalThis pour dev hot reload — lib/prisma.ts est pré-généré, ne pas le réécrire
EXEMPLE_INVALIDE:
  // Chaque import crée une nouvelle instance en dev
  export const prisma = new PrismaClient()
EXEMPLE_VALIDE:
  const globalForPrisma = globalThis as unknown as { prisma?: PrismaClient }
  export const prisma = globalForPrisma.prisma ?? new PrismaClient({ log: ['error'] })
  if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = prisma
  // Ne JAMAIS appeler prisma.$disconnect() après chaque requête — détruit la connexion réutilisable
STATUS: active
VERSION: 1.0"""),
]


# =============================================================================
# ZONE 30 — HEALTHCHECK ENDPOINT
# Source : migrate_zone_30_healthcheck.py
# =============================================================================

ZONE_30_HEALTHCHECK = [
    _s("30-healthcheck", "routes", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Next.js — app/api/health/route.ts pré-généré (ne pas réécrire)
RAISON: app/api/health/route.ts est pré-généré par le pipeline — ne pas le réécrire. Il implémente : force-dynamic, $queryRaw SELECT 1 avec Promise.race timeout 3s, retour { status: 'ok', db: 'ok' } en 200 ou { status: 'degraded', db: 'unreachable' } en 503.
DETECT: app/api/health|healthcheck|health.route
INSTEAD: Ne PAS écrire app/api/health/route.ts avec write_file — ce fichier est déjà présent dans les fichiers pré-générés
EXEMPLE_VALIDE:
  export const dynamic = 'force-dynamic'
  export async function GET() {
    try {
      await Promise.race([
        prisma.$queryRaw`SELECT 1`,
        new Promise((_, reject) => setTimeout(() => reject(new Error('DB timeout')), 3000)),
      ])
      return NextResponse.json({ status: 'ok', db: 'ok' })
    } catch {
      return NextResponse.json({ status: 'degraded', db: 'unreachable' }, { status: 503 })
    }
  }
STATUS: active
VERSION: 1.0"""),
]


# =============================================================================
# ZONE HARD RULES — Standards issus de enrich_qdrant.py
# =============================================================================

ZONE_HARD_RULES = [
    _s("hard-rules", "clerk", """RULE: Clerk @clerk/nextjs v6 — seul package npm valide, imports server/client
WHY: Les packages @clerk/clerk-sdk, @clerk/clerk-js, @clerk/sdk, @clerk/react n'existent pas ou sont obsolètes et ne doivent jamais apparaître dans package.json. Clerk v6 — auth() retourne une Promise, toujours await. Dans clerkMiddleware, auth est un OBJET (pas une fonction) : await auth.protect() (INTERDIT: auth().protect()).
GOOD:
  "@clerk/nextjs": "^6.0.0"  // dans package.json
  import { auth, currentUser } from '@clerk/nextjs/server'  // server-side
  import { useUser, useClerk } from '@clerk/nextjs'  // client-side
  const { userId } = await auth()  // toujours await
BAD:
  "@clerk/clerk-sdk": "..."  // package inexistant
  import { auth } from '@clerk/nextjs'  // ❌ doit être /server pour server-side
  auth().protect()  // ❌ auth() retourne une Promise en v6"""),

    _s("hard-rules", "prisma", """RULE: Prisma 7 — prisma.config.ts obligatoire, url INTERDIT dans schema.prisma
WHY: Prisma 7 breaking change : la propriété url dans datasource de schema.prisma est supprimée. La connexion DATABASE_URL doit être dans prisma.config.ts. Schema.prisma ne contient plus url. Créer prisma.config.ts avec defineConfig({ datasource: { url: process.env.DATABASE_URL } }). Ne jamais écrire url = env('DATABASE_URL') dans schema.prisma avec Prisma 7+.
BAD:
  datasource db {
    provider = "postgresql"
    url      = env("DATABASE_URL")  // ← INTERDIT PRISMA 7
  }
GOOD:
  // prisma/schema.prisma
  datasource db { provider = "postgresql" }
  generator client { provider = "prisma-client-js" }

  // prisma.config.ts
  import 'dotenv/config';
  import { defineConfig, env } from 'prisma/config';
  export default defineConfig({
    schema: 'prisma/schema.prisma',
    datasource: { url: env('DATABASE_URL') },
  });
ERROR: GateBlocked: NOT_BUILT_BY_GATE (prisma_schema_datasource_url)"""),

    _s("hard-rules", "auth", """RULE: auth() userId null guard — OBLIGATOIRE avant tout appel Prisma avec userId
WHY: Pattern mandatory dans tout route handler app/api/**/route.ts qui utilise userId dans une opération Prisma. Ce guard est OBLIGATOIRE pour TOUS les modèles avec ownership (authorId, userId, ownerId, createdBy). TypeScript strict : userId peut être null si l'utilisateur n'est pas authentifié. Sans ce guard, TypeScript lève TS2345 : 'Argument of type string | null is not assignable to parameter of type string'.
BAD:
  const { userId } = await auth();
  await prisma.item.create({ data: { title, userId } }); // ❌ TS2345 si userId null
GOOD:
  const { userId } = await auth();
  if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  await prisma.item.create({ data: { title, userId } }); // ✅ userId est string après guard
ERROR: TS2345 — Argument of type 'string | null' is not assignable to parameter of type 'string'"""),

    _s("hard-rules", "typescript", """RULE: TypeScript strict — tableau non typé INTERDIT (let data = [] pattern)
WHY: Le pattern `let data = []` suivi d'une réassignation dans try/catch est invalide en TypeScript strict : le compilateur infère `any[]` et rejette le build avec 'implicitly has type any[]'. Toujours typer explicitement si une variable tableau est déclarée avant son assignation Prisma.
BAD:
  let books = [];  // ← TypeScript strict refuse — any[] implicite
  try { books = await prisma.book.findMany(...) } catch { }
GOOD:
  // Forme 1 (préférée)
  const data = await prisma.model.findMany({...}).catch(() => []);

  // Forme 2 (si try/catch explicite requis)
  import type { Book } from '@prisma/client';
  let books: Book[] = [];
  try { books = await prisma.book.findMany({...}); } catch { books = []; }
ERROR: TS7034 — Variable 'data' implicitly has type 'any[]' in some locations"""),

    _s("hard-rules", "nextjs", """RULE: Next.js App Router — Server Component vs Client Component split pour pages interactives
WHY: Un Server Component (sans 'use client') NE PEUT PAS contenir onClick, onChange, useState, useEffect, useRouter, ni aucun handler d'événement. Ces éléments sont silencieusement non-fonctionnels en Server Component — pas d'erreur build, mais l'application est cassée à l'exécution. Si le brief décrit des boutons (Modifier, Supprimer, Ajouter, Valider, Annuler) sur une page qui affiche des données, le pattern Server+Client est OBLIGATOIRE.
BAD:
  // app/tasks/page.tsx — ❌ Server Component avec onClick
  export default async function TasksPage() {
    const tasks = await prisma.task.findMany({ where: { userId } });
    return tasks.map(t => <button onClick={() => handleDelete(t.id)}>Supprimer</button>); // ❌ silently broken
  }
GOOD:
  // Fichier 1 — Server Component (app/tasks/page.tsx, sans 'use client')
  export default async function TasksPage() {
    const tasks = await taskService.findMany(userId);
    return <TasksClient tasks={tasks} />;
  }
  // Fichier 2 — Client Component (app/tasks/tasks-client.tsx, avec 'use client')
  'use client';
  export function TasksClient({ tasks }: { tasks: Task[] }) {
    return tasks.map(t => <button onClick={() => handleDelete(t.id)}>Supprimer</button>);
  }"""),

    _s("hard-rules", "nextjs", """RULE: Next.js 14 App Router — routing URL vers fichier (convention stricte)
WHY: Chaque segment d'URL correspond à un dossier dans app/, la page est page.tsx dans ce dossier. app/page.tsx EST OBLIGATOIRE — c'est la page racine du projet. app/page.tsx doit être un Server Component et doit afficher la liste des entités principales du projet via prisma.<modèle>.findMany.
GOOD:
  route '/' → app/page.tsx (OBLIGATOIRE pour tout projet)
  route '/dashboard' → app/dashboard/page.tsx
  route '/[slug]' → app/[slug]/page.tsx
  route '/api/posts/[id]' → app/api/posts/[id]/route.ts
  app/page.tsx — Server Component, liste les vraies données du brief
  app/page.tsx — export const dynamic = 'force-dynamic' + try/catch avec fallback []
BAD:
  pages/index.tsx  // ❌ conflit fatal avec App Router
  app/page.tsx vide sans données  // ❌ page inutilisable"""),

    _s("hard-rules", "prisma", """RULE: Prisma schema — structure canonique datasource/generator multi-lignes
WHY: Dans prisma/schema.prisma, les blocs datasource et generator doivent être explicites et multi-lignes. Eviter les variantes ambiguës/compactées qui déclenchent P1012. Ne pas mettre datasource.url dans schema.prisma avec Prisma 7. Si Prisma retourne 'This line is not a valid definition within a datasource', reconstruire les deux blocs exactement au format canonique.
GOOD:
  datasource db {
    provider = "postgresql"
  }
  generator client {
    provider = "prisma-client-js"
  }
ERROR: Prisma P1012 — This line is not a valid definition within a datasource"""),
]


ALL_STANDARDS = (
    # ZONE_0_PLANNING retiré : les templates de domaine (Todo, Blog, Product, Contact, Item)
    # overridaient le brief utilisateur → planner drift confirmé (marketplace→Book, habit→Workout).
    # Le LLM connaît les domaines métier. Le RAG doit enseigner uniquement les patterns stack.
    ZONE_1_REQUIRED_FILES
    + ZONE_2_PACKAGES
    + ZONE_3_TYPESCRIPT
    + ZONE_4_NEXTCONFIG
    + ZONE_5_LAYOUT
    + ZONE_6_CLERK
    + ZONE_7_PRISMA
    + ZONE_8_TESTING
    + ZONE_9_SECURITY
    + ZONE_10_SECURITY_ADVANCED
    + ZONE_11_ERROR_HANDLING
    + ZONE_12_TESTING_ADVANCED
    + ZONE_13_BUSINESS_LOGIC
    + ZONE_14_ANTIPATTERNS
    + ZONE_15_CONFORMITY
    + ZONE_16_SECURITY_APPLICATIVE
    + ZONE_17_ARCHITECTURE   # Sprint 4.6 — cohérence architecturale inter-fichiers
    + ZONE_17B_STACK_PATTERNS  # patterns de code préventifs (ex-migrate_zones_17_18)
    + ZONE_18_TSC_CORRECTIVE   # correctifs tsc par code d'erreur
    + ZONE_19_SAAS_SENIOR      # pages réelles, DAL, ownership, relations
    + ZONE_20_DAL_SERVICE      # lib/services/<model>.service.ts pattern
    + ZONE_21_PAGINATION       # skip/take + PaginatedResponse<T>
    + ZONE_22_PRISMA_ERRORS    # handlePrismaError, codes P2002/P2025
    + ZONE_23_CREATE_INPUT     # CreateXxxInput sans userId
    + ZONE_24_N1_PREVENTION    # include vs boucle findUnique
    + ZONE_26_TRANSACTIONS     # $transaction séquentielle et interactive
    + ZONE_27_LOGGING          # Pino logging structuré
    + ZONE_28_CONNECTION_POOLING  # globalThis singleton + connection_limit
    + ZONE_30_HEALTHCHECK      # /api/health pré-généré
    + ZONE_HARD_RULES          # ex-enrich_qdrant.py : Clerk, Prisma7, auth guard, etc.
)


# =============================================================================
# INJECTION QDRANT
# =============================================================================

def upsert_standard(client: QdrantClient, text: str, metadata: dict) -> str:
    """Embed et upsert — Option A: applique _reformat_text() avant embedding.

    UUID basé sur le texte reformaté pour idempotence entre runs post-reset.
    """
    if EMBEDDINGS is None:
        raise RuntimeError(
            f"Embedding backend indisponible (provider={EMBEDDING_PROVIDER}, model={EMBEDDING_MODEL})"
        ) from _EMBEDDING_INIT_ERROR
    formatted = _reformat_text(text)
    vector = EMBEDDINGS.embed_query(formatted)
    point_id = text_to_uuid(formatted)
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[PointStruct(
            id=point_id,
            vector=vector,
            payload={"text": formatted, "metadata": metadata},
        )],
        wait=True,
    )
    return point_id


def main() -> int:
    args = _parse_args()

    print("\n" + "=" * 70)
    print("📚 STANDARDS COMPLETS v3 — Stack nextjs-clerk-prisma (Zones 1-30 + hard rules)")
    print("   Option A active : RULE: format, ACTION:/STACK: retirés du texte → metadata")
    print("   Sources: Perplexity 2026-03-01 + runs empiriques + doc officielle")
    print("=" * 70 + "\n")

    client = QdrantClient(url=QDRANT_URL)

    # Vérification connexion
    try:
        collections = client.get_collections()
        names = [c.name for c in collections.collections]
        if COLLECTION_NAME not in names:
            print(f"❌ Collection '{COLLECTION_NAME}' introuvable.")
            print("   → Exécutez d'abord: python scripts/reset_qdrant.py")
            return 1
        print(f"✅ Qdrant OK — '{COLLECTION_NAME}' trouvée")
    except Exception as e:
        print(f"❌ Connexion Qdrant: {e}")
        return 1

    count_before = client.count(collection_name=COLLECTION_NAME, exact=True).count
    print(f"📊 Standards avant injection: {count_before}\n")

    indexed_all = list(enumerate(ALL_STANDARDS, start=1))
    indexed_ready = [(idx, s) for idx, s in indexed_all if s["metadata"].get("status") != "draft"]
    drafts = [s for _, s in indexed_all if s["metadata"].get("status") == "draft"]

    sanitize_enabled = not args.no_sanitize
    if sanitize_enabled:
        prepared_ready, pollution_report = _sanitize_standards(indexed_ready)
    else:
        prepared_ready = [
            {
                "index": idx,
                "text": std["text"],
                "original_text": std["text"],
                "metadata": std["metadata"],
                "changed": False,
            }
            for idx, std in indexed_ready
        ]
        pollution_report = []

    report_path = _write_pollution_report(pollution_report)
    changed_count = sum(1 for x in prepared_ready if x["changed"])
    polluted_count = len(pollution_report)

    print("🧪 Audit entités métier (Phase D)")
    print(f"  - Sanitization active         : {sanitize_enabled}")
    print(f"  - Standards audités (actifs)  : {len(prepared_ready)}")
    print(f"  - Standards pollués détectés  : {polluted_count}")
    print(f"  - Standards modifiés          : {changed_count}")
    print(f"  - Rapport JSON                : {report_path}")
    if args.audit_only:
        print("\nℹ️ Mode audit-only: aucune injection Qdrant effectuée.")
        return 0

    if args.only_modified:
        targets = [x for x in prepared_ready if x["changed"]]
    else:
        targets = prepared_ready

    print(f"  ✅ Prêts à injecter : {len(targets)}")
    print(f"  ⏳ Draft (non injectés) : {len(drafts)}\n")

    zones: dict[str, list] = {}
    for std in targets:
        zone = std["metadata"].get("zone", "unknown")
        zones.setdefault(zone, []).append(std)

    total_ok = 0
    total_err = 0
    total_deleted = 0

    for zone, items in sorted(zones.items()):
        print(f"📁 {zone:<28} — {len(items)} standards")
        for std in items:
            preview = std["text"].replace("\n", " ")[:65]
            try:
                old_id = None
                new_id = None
                if std["changed"]:
                    old_id = text_to_uuid(std["original_text"])
                    new_id = text_to_uuid(std["text"])
                upsert_standard(client, std["text"], std["metadata"])
                if std["changed"] and old_id and new_id and old_id != new_id:
                    try:
                        client.delete(collection_name=COLLECTION_NAME, points_selector=[old_id])
                        total_deleted += 1
                    except Exception:
                        # Tolérance: l'ancien ID peut ne pas exister (première injection ou reset).
                        pass
                print(f"   ✅  {preview}...")
                total_ok += 1
            except Exception as e:
                print(f"   ❌  {preview}...")
                print(f"       → {e}")
                total_err += 1
        print()

    count_after = client.count(collection_name=COLLECTION_NAME, exact=True).count
    print("=" * 70)
    print("🎯 RÉSULTAT")
    print(f"   Avant     : {count_before}")
    print(f"   Injectés  : {total_ok}")
    print(f"   Supprimés : {total_deleted}")
    print(f"   Erreurs   : {total_err}")
    print(f"   Total     : {count_after}")
    print("=" * 70 + "\n")
    return 0 if total_err == 0 else 1


if __name__ == "__main__":
    if EMBEDDINGS is None:
        print(
            "❌ Backend embeddings indisponible "
            f"(provider={EMBEDDING_PROVIDER}, model={EMBEDDING_MODEL})"
        )
        if _EMBEDDING_INIT_ERROR is not None:
            print(f"   Détail: {_EMBEDDING_INIT_ERROR}")
        if EMBEDDING_PROVIDER == "openai":
            print("   Vérifie OPENAI_API_KEY ou active OPENAI_FROZEN=1 pour basculer sur Ollama.")
        raise SystemExit(1)
    raise SystemExit(main())
