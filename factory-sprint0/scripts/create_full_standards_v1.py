"""
scripts/create_full_standards_v1.py

Standards COMPLETS et PRESCRIPTIFS — stack nextjs-clerk-prisma.
Couvre les 9 zones critiques d'une app Next.js 14 + Clerk v6 + Prisma 7.

Ce fichier REMPLACE :
  - populate_qdrant.py                        (standards descriptifs, buggués)
  - create_sprint2_prescriptive_standards.py  (5 standards Sprint 2 seulement)

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
  Zone 1 — Fichiers obligatoires + structure canonique
  Zone 2 — Package configuration
  Zone 3 — TypeScript configuration
  Zone 4 — Next.js configuration (next.config.js + middleware)
  Zone 5 — App Router layout (Clerk + html/body)
  Zone 6 — Authentification Clerk v6 (breaking changes v5→v6)
  Zone 7 — Base de données Prisma 7
  Zone 8 — Tests Jest 29 (next/jest + setupFilesAfterEnv)
  Zone 9 — Sécurité (auth checks + Zod + env vars)
"""

from __future__ import annotations

import hashlib
import os
from uuid import UUID

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct

load_dotenv(dotenv_path=".env")

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "factory_standards")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
EMBEDDINGS = OpenAIEmbeddings(model=EMBEDDING_MODEL)


def text_to_uuid(text: str) -> str:
    """UUID déterministe basé sur MD5(text) — idempotence garantie."""
    hash_bytes = hashlib.md5(text.encode("utf-8")).digest()
    return str(UUID(bytes=hash_bytes))


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
RAISON: (Perplexity confirmé) Prisma 7 introduit prisma.config.ts. Générer les deux garantit la compatibilité ascendante et la conformité à la voie officielle Prisma 7. url = env("DATABASE_URL") dans schema.prisma reste valide mais prisma.config.ts est désormais recommandé.
FICHIERS_OBLIGATOIRES:
  prisma/schema.prisma  — datasource + generator + modèles
  prisma.config.ts      — defineConfig depuis 'prisma/config'
CONFIGURATION_SCHEMA_PRISMA:
  datasource db {
    provider = "postgresql"
    url      = env("DATABASE_URL")
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
ERREUR_ATTENDUE: Warning Prisma 7 ou comportement déprécié
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "7-prisma",
            "status": "active",
            "version": "1.0",
            "category": "prisma",
            "source": "factory_standards_v2",
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
    userId    String
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
TECHNOLOGIE: API Routes — vérification userId Clerk sur chaque route protégée
RAISON: Sans vérification userId, les routes API sont accessibles sans authentification.
DETECTION_REGEX: export async function (GET|POST|PUT|DELETE|PATCH)(?![\s\S]{0,400}await auth\(\))
ALTERNATIVE: const { userId } = await auth(); if (!userId) return 401; au début de chaque handler
EXEMPLE_INVALIDE:
  export async function GET(req: Request) {
    const data = await prisma.task.findMany();
    return NextResponse.json(data);  // Pas d'auth check
  }
EXEMPLE_VALIDE:
  export async function GET(req: Request) {
    const { userId } = await auth();
    if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    const data = await prisma.task.findMany({ where: { userId } });
    return NextResponse.json(data);
  }
ERREUR_ATTENDUE: Données exposées sans authentification
STATUS: active
VERSION: 1.0""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "9-security",
            "status": "active",
            "version": "1.0",
            "category": "security",
            "source": "factory_standards_v2",
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
        },
    },
]


# =============================================================================
# AGRÉGATION COMPLÈTE
# =============================================================================

ALL_STANDARDS = (
    ZONE_1_REQUIRED_FILES
    + ZONE_2_PACKAGES
    + ZONE_3_TYPESCRIPT
    + ZONE_4_NEXTCONFIG
    + ZONE_5_LAYOUT
    + ZONE_6_CLERK
    + ZONE_7_PRISMA
    + ZONE_8_TESTING
    + ZONE_9_SECURITY
)


# =============================================================================
# INJECTION QDRANT
# =============================================================================

def upsert_standard(client: QdrantClient, text: str, metadata: dict) -> str:
    """Embed et upsert — idempotent via UUID déterministe MD5(text)."""
    vector = EMBEDDINGS.embed_query(text)
    point_id = text_to_uuid(text)
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[PointStruct(
            id=point_id,
            vector=vector,
            payload={"text": text, "metadata": metadata},
        )],
        wait=True,
    )
    return point_id


def main() -> int:
    print("\n" + "=" * 70)
    print("📚 STANDARDS COMPLETS v1 — Stack nextjs-clerk-prisma (9 zones)")
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

    # Séparer active vs draft
    ready = [s for s in ALL_STANDARDS if s["metadata"].get("status") != "draft"]
    drafts = [s for s in ALL_STANDARDS if s["metadata"].get("status") == "draft"]

    print(f"  ✅ Prêts à injecter : {len(ready)}")
    print(f"  ⏳ Draft (non injectés) : {len(drafts)}\n")

    zones: dict[str, list] = {}
    for std in ready:
        zone = std["metadata"].get("zone", "unknown")
        zones.setdefault(zone, []).append(std)

    total_ok = 0
    total_err = 0

    for zone, items in sorted(zones.items()):
        print(f"📁 {zone:<28} — {len(items)} standards")
        for std in items:
            preview = std["text"].replace("\n", " ")[:65]
            try:
                upsert_standard(client, std["text"], std["metadata"])
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
    print(f"   Erreurs   : {total_err}")
    print(f"   Total     : {count_after}")
    print("=" * 70 + "\n")
    return 0 if total_err == 0 else 1


if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY manquant dans .env")
        raise SystemExit(1)
    raise SystemExit(main())
