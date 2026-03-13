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
        },
    },
    {
        "text": """ACTION: INTERDIT
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Jest — jest.mock placé après les imports ES modules
RAISON: jest.mock() est hoisté avant les imports uniquement avec Babel/ts-jest CommonJS. Avec ESM natif ou mauvaise config ts-jest, le mock n'est pas appliqué et l'import réel est utilisé.
DETECTION_REGEX: import\s+\{[^}]+\}\s+from\s+['"][^'"]+['"];\s*[\s\S]*?jest\.mock\(
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
        },
    },
]


ZONE_13_BUSINESS_LOGIC = [
    {
        "text": """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Prisma — lier les entités utilisateur à clerkId, pas à l'id interne
RAISON: Stocker l'id Prisma interne comme référence d'ownership crée une désynchronisation quand Clerk supprime ou recrée un utilisateur — les données orphelines ne peuvent plus être réclamées.
DETECTION_REGEX: (authorId|userId|ownerId)\\s+Int\\s+(?!.*@relation.*User)
ALTERNATIVE: Utiliser clerkId String comme clé de relation owner, ou stocker clerkId dans chaque entité liée à un utilisateur
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
    authorId  String   // ✅ clerkId = identifiant Clerk stable
    createdAt DateTime @default(now())
    updatedAt DateTime @updatedAt
  }
  // Dans la route : where: { authorId: userId } où userId vient de auth()
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
  import { DashboardClient } from './DashboardClient';
  import { auth } from '@clerk/nextjs/server';
  export default async function DashboardPage() {
    const { userId } = await auth();
    if (!userId) redirect('/sign-in');
    const posts = await prisma.post.findMany({ where: { authorId: userId } });
    return <DashboardClient posts={posts} />;
  }
  // app/dashboard/DashboardClient.tsx
  'use client';
  import { useState } from 'react';
  export function DashboardClient({ posts }) {
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
        },
    },
]


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
    + ZONE_10_SECURITY_ADVANCED
    + ZONE_11_ERROR_HANDLING
    + ZONE_12_TESTING_ADVANCED
    + ZONE_13_BUSINESS_LOGIC
    + ZONE_14_ANTIPATTERNS
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
    print("📚 STANDARDS COMPLETS v1 — Stack nextjs-clerk-prisma (14 zones)")
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
