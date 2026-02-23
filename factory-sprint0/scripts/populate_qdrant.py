"""
scripts/populate_qdrant.py
Peuplement initial de la collection factory_standards dans Qdrant.
Idempotent — utilise UUIDs, peut être relancé sans créer de doublons.
Usage: python scripts/populate_qdrant.py
"""

import asyncio
import os
import hashlib
from uuid import UUID
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct
from langchain_openai import OpenAIEmbeddings

load_dotenv(dotenv_path='.env')

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = "factory_standards"
EMBEDDINGS = OpenAIEmbeddings(model="text-embedding-3-large")


def text_to_uuid(text: str) -> str:
    """UUID déterministe basé sur le contenu — idempotent garanti."""
    hash_bytes = hashlib.md5(text.encode("utf-8")).digest()
    return str(UUID(bytes=hash_bytes))

# ─────────────────────────────────────────
# STANDARDS — 7 catégories, 3+ standards chacune
# ─────────────────────────────────────────

STANDARDS = [
    # ── NEXTJS ──────────────────────────────────────────────────────────
    {
        "text": "Next.js 14.2+ avec App Router est la version obligatoire pour tous les projets factory. Structure de dossiers : app/ pour les routes, components/ pour les composants réutilisables, lib/ pour les utilitaires. Le fichier next.config.js doit inclure les optimisations d'images et la configuration des variables d'environnement publiques.",
        "metadata": {"category": "nextjs", "tech": "next.js", "version": "14.2+", "source": "factory_standards_v1", "outcome": "validated"}
    },
    {
        "text": "Package.json pour projet Next.js 14 factory : next@14.2.25, react@18.3.0, react-dom@18.3.0. Scripts obligatoires : build (next build), dev (next dev), start (next start), lint (next lint), test (jest). La dépendance sharp doit être incluse pour l'optimisation des images en production sur Vercel.",
        "metadata": {"category": "nextjs", "tech": "next.js", "version": "14.2.25", "source": "factory_standards_v1", "outcome": "validated"}
    },
    {
        "text": "App Router Next.js 14 : utiliser des Server Components par défaut. Ajouter 'use client' uniquement pour les composants nécessitant des hooks React (useState, useEffect) ou des interactions browser. Les layouts (app/layout.tsx) doivent englober ClerkProvider. Les routes dynamiques utilisent des brackets : app/[id]/page.tsx.",
        "metadata": {"category": "nextjs", "tech": "next.js", "version": "14.2+", "source": "factory_standards_v1", "outcome": "validated"}
    },
    {
        "text": "Optimisation Next.js pour Vercel : ajouter next.config.js avec images.domains configuré, experimental.serverActions activé si besoin. Variables d'environnement publiques préfixées NEXT_PUBLIC_. Variables serveur sans préfixe. Ne jamais exposer OPENAI_API_KEY ou DATABASE_URL côté client.",
        "metadata": {"category": "nextjs", "tech": "next.js", "version": "14.2+", "source": "factory_standards_v1", "outcome": "validated"}
    },
    {
        "text": "Utiliser parallel routes (@folder) et intercepting routes pour les modals d'authentification et les flux complexes dans les applications SaaS factory.",
        "metadata": {"category": "nextjs", "tech": "next.js", "version": "14.2+", "source": "factory_standards_v1", "outcome": "validated"}
    },
    {
        "text": "Next.js 14 middleware matcher INTERDIT: '/protected/**'. Utilise UNIQUEMENT '/protected/(.*)'. Le pattern ** cause 'Unexpected MODIFIER' a la compilation.",
        "metadata": {
            "category": "nextjs",
            "tech": "next.js",
            "version": "14.2+",
            "source": "factory_standards_hotfix",
            "outcome": "failure_prevention",
            "tags": ["nextjs", "middleware", "routing", "critical"]
        }
    },
    {
        "text": "package.json doit etre du JSON pur valide. INTERDIT: commentaires, markdown, backticks, texte avant ou apres les accolades. Valide avec json.loads() avant ecriture.",
        "metadata": {
            "category": "nextjs",
            "tech": "json",
            "version": "n/a",
            "source": "factory_standards_hotfix",
            "outcome": "failure_prevention",
            "tags": ["nextjs", "json", "package", "critical"]
        }
    },

    # ── CLERK ───────────────────────────────────────────────────────────
    {
        "text": "Clerk authentication v5+ est le système d'auth exclusif pour tous les projets factory. Installation : @clerk/nextjs@^5.0.0. ClerkProvider doit envelopper l'application dans app/layout.tsx. Ne jamais implémenter d'authentification custom (bcrypt, JWT manuel, NextAuth). Variables requises : NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY et CLERK_SECRET_KEY.",
        "metadata": {"category": "clerk", "tech": "clerk", "version": "5.0+", "source": "factory_standards_v1", "outcome": "validated"}
    },
    {
        "text": "Middleware Clerk (middleware.ts à la racine) : utiliser clerkMiddleware() de @clerk/nextjs/server. Protéger toutes les routes par défaut avec createRouteMatcher. Routes publiques explicites : ['/', '/sign-in(.*)', '/sign-up(.*)'. Exemple : export default clerkMiddleware((auth, req) => { if (!isPublicRoute(req)) auth().protect(); });",
        "metadata": {"category": "clerk", "tech": "clerk", "version": "5.0+", "source": "factory_standards_v1", "outcome": "validated"}
    },
    {
        "text": "Pages Clerk obligatoires pour App Router : app/sign-in/[[...sign-in]]/page.tsx avec composant <SignIn /> de @clerk/nextjs. app/sign-up/[[...sign-up]]/page.tsx avec composant <SignUp />. Composants UI Clerk : <UserButton afterSignOutUrl='/' /> dans le header, <SignedIn> et <SignedOut> pour affichage conditionnel. Pas de champ password dans Prisma schema quand Clerk est utilisé.",
        "metadata": {"category": "clerk", "tech": "clerk", "version": "5.0+", "source": "factory_standards_v1", "outcome": "validated"}
    },
    {
        "text": "Récupération user Clerk côté serveur : import { auth, currentUser } from '@clerk/nextjs/server'. Dans un Server Component : const { userId } = auth(); const user = await currentUser(). Pour les API routes : const { userId } = auth(); if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });",
        "metadata": {"category": "clerk", "tech": "clerk", "version": "5.0+", "source": "factory_standards_v1", "outcome": "validated"}
    },

    # ── PRISMA ──────────────────────────────────────────────────────────
    {
        "text": "Prisma v5+ avec PostgreSQL pour tous les projets factory. schema.prisma : generator client (provider = 'prisma-client-js'), datasource db (provider = 'postgresql', url = env('DATABASE_URL')). Client singleton pattern : lib/prisma.ts avec const prisma = global.prisma ?? new PrismaClient(). En dev : global.prisma = prisma.",
        "metadata": {"category": "prisma", "tech": "prisma", "version": "5.0+", "source": "factory_standards_v1", "outcome": "validated"}
    },
    {
        "text": "Prisma schema conventions factory : champs id en cuid() ou uuid(). Champ createdAt DateTime @default(now()) et updatedAt DateTime @updatedAt sur tous les modèles. Pas de champ password quand Clerk est utilisé — stocker userId Clerk (String) pour la relation. Exemple User model : id String @id @default(cuid()), clerkId String @unique, email String @unique.",
        "metadata": {"category": "prisma", "tech": "prisma", "version": "5.0+", "source": "factory_standards_v1", "outcome": "validated"}
    },
    {
        "text": "Prisma migrations : npx prisma migrate dev --name init pour la première migration. npx prisma db push pour les environnements de développement sans migration formelle. npx prisma generate après chaque changement de schema. En production Vercel : npx prisma migrate deploy dans le build command. DATABASE_URL doit être une connection string PostgreSQL valide.",
        "metadata": {"category": "prisma", "tech": "prisma", "version": "5.0+", "source": "factory_standards_v1", "outcome": "validated"}
    },
    {
        "text": "Toujours utiliser select ou include de manière explicite dans les queries Prisma pour limiter les données retournées et éviter les fuites accidentelles de champs sensibles.",
        "metadata": {"category": "prisma", "tech": "prisma", "version": "5.0+", "source": "factory_standards_v1", "outcome": "validated"}
    },

    # ── SHADCN ──────────────────────────────────────────────────────────
    {
        "text": "ERREUR CRITIQUE / INTERDIT dans package.json: ne jamais ajouter shadcn/ui, @shadcn/ui, ni shadcn-ui dans dependencies ou devDependencies. Cela provoque npm EINVALIDPACKAGENAME. shadcn/ui n'est pas un package npm installable: c'est un CLI de génération de composants. CORRECT: utiliser npx shadcn@latest init (ou npx shadcn-ui@latest init selon la version du CLI) puis importer les composants copiés localement depuis '@/components/ui/*'. Dans package.json, utiliser uniquement de vraies dépendances npm compatibles shadcn: class-variance-authority, clsx, tailwind-merge, lucide-react.",
        "metadata": {"category": "shadcn", "tech": "shadcn-ui", "version": "latest", "source": "factory_standards_v1", "outcome": "validated"}
    },
    {
        "text": "shadcn/ui Form avec react-hook-form et Zod : import { useForm } from 'react-hook-form', import { zodResolver } from '@hookform/resolvers/zod'. Toujours utiliser le composant Form de shadcn qui encapsule FormField, FormItem, FormLabel, FormControl, FormMessage. Validation Zod côté client ET serveur (ne pas faire confiance au client seul).",
        "metadata": {"category": "shadcn", "tech": "shadcn-ui", "version": "latest", "source": "factory_standards_v1", "outcome": "validated"}
    },
    {
        "text": "Layout pattern shadcn/ui pour SaaS factory : Sidebar navigation avec Sheet pour mobile, Header avec UserButton Clerk, main content area avec padding. Utiliser cn() utility (clsx + tailwind-merge) pour les classes conditionnelles. Dark mode via next-themes avec ThemeProvider dans layout.tsx.",
        "metadata": {"category": "shadcn", "tech": "shadcn-ui", "version": "latest", "source": "factory_standards_v1", "outcome": "validated"}
    },

    # ── TESTING ─────────────────────────────────────────────────────────
    {
        "text": "Configuration Jest pour Next.js 14 factory : jest.config.js avec preset next/jest. Transformer babel-jest avec next/babel. testEnvironment jsdom. moduleNameMapper pour @/ alias. setupFilesAfterFramework pour @testing-library/jest-dom. Coverage threshold : branches 70%, functions 80%, lines 80%, statements 80%.",
        "metadata": {"category": "testing", "tech": "jest", "version": "29+", "source": "factory_standards_v1", "outcome": "validated"}
    },
    {
        "text": "Mock Clerk dans les tests unitaires Jest : jest.mock('@clerk/nextjs', () => ({ useAuth: () => ({ userId: 'test-user-id', isLoaded: true, isSignedIn: true }), useUser: () => ({ user: { id: 'test-user-id', emailAddresses: [{ emailAddress: 'test@test.com' }] } }), ClerkProvider: ({ children }) => children })). Essentiel pour tester les composants React qui utilisent Clerk.",
        "metadata": {"category": "testing", "tech": "jest", "version": "29+", "source": "factory_standards_v1", "outcome": "validated"}
    },
    {
        "text": "Tests API routes Next.js : utiliser jest.mock pour prisma client. Mock NextResponse et Request objects. Tester les status codes (200, 401, 404, 500). Pattern : import handler from '../app/api/tasks/route.ts'; const req = new Request('http://localhost/api/tasks', { method: 'POST', body: JSON.stringify({...}) }); const res = await handler(req); expect(res.status).toBe(200).",
        "metadata": {"category": "testing", "tech": "jest", "version": "29+", "source": "factory_standards_v1", "outcome": "validated"}
    },

    # ── DEPLOYMENT ──────────────────────────────────────────────────────
    {
        "text": "Déploiement Vercel pour projets factory : vercel.json minimal (framework: nextjs). Variables d'environnement à configurer sur Vercel : NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY, CLERK_SECRET_KEY, DATABASE_URL. Build command : npx prisma generate && npx prisma migrate deploy && next build. Node.js version : 18.x ou 20.x.",
        "metadata": {"category": "deployment", "tech": "vercel", "version": "latest", "source": "factory_standards_v1", "outcome": "validated"}
    },
    {
        "text": "Checklist pre-deploy factory : 1) next build réussit sans erreur ni warning TypeScript. 2) Variables env toutes définies. 3) DATABASE_URL pointe sur DB de production (pas localhost). 4) Prisma migrations à jour. 5) Tests Jest passent (coverage >80%). 6) Lighthouse score >85 mobile. 7) Pas de console.log restants en prod.",
        "metadata": {"category": "deployment", "tech": "vercel", "version": "latest", "source": "factory_standards_v1", "outcome": "validated"}
    },

    # ── SECURITY ────────────────────────────────────────────────────────
    {
        "text": "Sécurité OWASP pour projets Next.js factory : validation Zod obligatoire sur TOUS les inputs API (pas de trust client). Rate limiting sur les routes API publiques. Headers sécurité dans next.config.js : X-Frame-Options DENY, X-Content-Type-Options nosniff, Referrer-Policy strict-origin-when-cross-origin. Utiliser des paramétrisés Prisma queries (pas d'injection SQL possible avec ORM).",
        "metadata": {"category": "security", "tech": "nextjs", "version": "14.2+", "source": "factory_standards_v1", "outcome": "validated"}
    },
    {
        "text": "Validation input Zod côté serveur factory : créer des schemas Zod pour chaque endpoint API. Exemple : const CreateTaskSchema = z.object({ title: z.string().min(1).max(255), description: z.string().optional() }). Utiliser schema.safeParse() pour retourner des erreurs formatées. Ne jamais utiliser schema.parse() dans les API routes (crash non géré).",
        "metadata": {"category": "security", "tech": "zod", "version": "3.0+", "source": "factory_standards_v1", "outcome": "validated"}
    },
    {
        "text": "Protection CSRF et auth checks factory : vérifier userId Clerk sur chaque route API protégée. Pattern standard : const { userId } = auth(); if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 }). Vérifier que la ressource appartient bien à l'user : const task = await prisma.task.findFirst({ where: { id, userId } }). Si null → 404, pas 403 (évite l'énumération).",
        "metadata": {"category": "security", "tech": "clerk", "version": "5.0+", "source": "factory_standards_v1", "outcome": "validated"}
    },
    {
        "text": "Toujours sanitizer les entrées utilisateur affichées (sanitize-html ou DOMPurify côté client si besoin) pour prévenir les attaques XSS même avec un bon CSP.",
        "metadata": {"category": "security", "tech": "nextjs", "version": "14.2+", "source": "factory_standards_v1", "outcome": "validated"}
    },
    # Clerk Auth Patterns (Next.js 14)
    {"text": "Implémenter le composant <UserButton /> dans le header pour la gestion de session côté client avec redirection automatique après déconnexion.", "metadata": {"category": "clerk", "priority": "high"}},
    {"text": "Utiliser 'auth()' dans les Server Components pour récupérer le userId et protéger l'accès aux données au niveau du serveur.", "metadata": {"category": "clerk", "priority": "high"}},
    {"text": "Synchroniser les données utilisateur via Webhooks Clerk vers la base de données locale pour maintenir l'intégrité des relations Prisma.", "metadata": {"category": "clerk", "priority": "medium"}},
    {"text": "Préférer 'currentUser()' de @clerk/nextjs/server pour obtenir les détails complets de l'utilisateur (email, nom) dans les Server Components.", "metadata": {"category": "clerk", "priority": "medium"}},

    # Prisma Best Practices
    {"text": "Utiliser des index '@unique' sur le champ 'clerkId' pour optimiser les jointures entre le provider d'auth et la base de données.", "metadata": {"category": "prisma", "priority": "high"}},
    {"text": "Ajouter systématiquement les champs 'createdAt' et 'updatedAt' sur chaque modèle pour assurer la traçabilité des données.", "metadata": {"category": "prisma", "priority": "medium"}},

    # shadcn/ui Standards
    {"text": "Installer les composants via 'npx shadcn-ui@latest add' pour garantir la compatibilité avec les dernières versions de Tailwind CSS.", "metadata": {"category": "shadcn", "priority": "high"}},
    {"text": "Centraliser la gestion des thèmes (dark/light) via le package 'next-themes' injecté dans le RootLayout.", "metadata": {"category": "shadcn", "priority": "medium"}},
    {"text": "Accessibilité : s'assurer que tous les composants interactifs (Dialog, Popover) utilisent les primitives Radix UI intégrées à shadcn.", "metadata": {"category": "shadcn", "priority": "high"}},

    # Next.js 14 App Router
    {"text": "Structure de dossiers : utiliser des 'Route Groups' (folder) pour organiser logiquement l'auth du reste de l'application SaaS.", "metadata": {"category": "nextjs", "priority": "medium"}},
    {"text": "Utiliser 'loading.tsx' à la racine des segments pour fournir un feedback visuel immédiat (skeleton screens) pendant le streaming.", "metadata": {"category": "nextjs", "priority": "high"}},
    {"text": "Préférer les Server Actions pour les mutations de données (formulaires) afin de réduire le JavaScript envoyé au client.", "metadata": {"category": "nextjs", "priority": "high"}},
    {"text": "Optimisation : configurer 'next/image' avec des domaines autorisés et des placeholders de flou pour améliorer le LCP.", "metadata": {"category": "nextjs", "priority": "medium"}},

    # Zod Validation
    {"text": "Définir les schémas Zod dans un fichier partagé 'lib/validations' pour réutilisation côté client et côté serveur.", "metadata": {"category": "zod", "priority": "high"}},
    {"text": "Inférer les types TypeScript directement des schémas Zod via 'z.infer<typeof schema>' pour garantir une source unique de vérité.", "metadata": {"category": "zod", "priority": "high"}},

    # Tailwind CSS
    {"text": "Utiliser la configuration 'tailwind.config.ts' pour définir les variables de design system (couleurs, espacements) conformes à shadcn.", "metadata": {"category": "tailwind", "priority": "medium"}},
    {"text": "Privilégier les classes utilitaires 'flex' et 'grid' pour les mises en page responsives plutôt que des media queries custom.", "metadata": {"category": "tailwind", "priority": "high"}},
    {"text": "Appliquer 'hover:', 'focus:', et 'active:' sur tous les éléments interactifs pour améliorer l'affordance de l'interface.", "metadata": {"category": "tailwind", "priority": "medium"}},

    # E2E Playwright Patterns
    {"text": "BASE_URL : utiliser 'process.env.BASE_URL' pour permettre l'exécution des tests sur localhost ou en staging/production.", "metadata": {"category": "testing", "priority": "high"}},
    {"text": "Auth : implémenter un script global setup pour simuler le login Clerk et réutiliser l'état d'authentification entre les tests.", "metadata": {"category": "testing", "priority": "high"}},
    {"text": "Locators : utiliser 'page.getByRole' ou 'page.getByTestId' pour cibler les composants UI de manière sémantique et résiliente.", "metadata": {"category": "testing", "priority": "medium"}},
    {"text": "Cleanup : s'assurer que chaque test E2E supprime les données qu'il a créées pour éviter la pollution entre les runs.", "metadata": {"category": "testing", "priority": "high"}},
    {"text": "Flakiness : utiliser 'await page.waitForLoadState('networkidle')' avant de valider des mutations de données asynchrones.", "metadata": {"category": "testing", "priority": "medium"}},
    {"text": "Screenshots : configurer Playwright pour capturer des screenshots et vidéos uniquement lors des échecs en CI.", "metadata": {"category": "testing", "priority": "low"}},
    {"text": "Sélecteurs Clerk : cibler les éléments d'auth via '.cl-internal-ph606s' ou les data attributes spécifiques de Clerk.", "metadata": {"category": "testing", "priority": "high"}},
    {
    "text": "INTERDIT dans schema.prisma quand Clerk est utilisé : champs password, password_hash, passwordHash, sessionToken, session_token. Le modèle User ne doit contenir que clerkId String @unique comme lien d'authentification.",
    "metadata": {"category": "clerk", "tech": "prisma", "priority": "critical", "source": "run_learnings_v1", "outcome": "failure_prevention"}
},
{
    "text": "Les fichiers de tests E2E Playwright générés doivent être du TypeScript pur (.spec.ts). Ne jamais retourner du JSON ou du Markdown avec des backticks. Format obligatoire : import { test, expect } from '@playwright/test'; test('...', async ({ page }) => { ... });",
    "metadata": {"category": "testing", "tech": "playwright", "priority": "critical", "source": "run_learnings_v1", "outcome": "failure_prevention"}
},
{
    "text": "Routes d'authentification Clerk obligatoires : /sign-in et /sign-up uniquement. Routes interdites : /login, /register, /api/auth/login, /api/auth/register, /api/auth/logout. L'architecture Clerk ne nécessite aucune API route custom pour l'authentification.",
    "metadata": {"category": "clerk", "tech": "nextjs", "priority": "critical", "source": "run_learnings_v1", "outcome": "failure_prevention"}
},
{
    "category": "nextjs",
    "text": "shadcn/ui N'EST PAS un package npm. INTERDIT dans dependencies/devDependencies. "
            "shadcn/ui est un CLI : npx shadcn-ui@latest init puis npx shadcn-ui@latest add [component]. "
            "Les composants sont copiés dans le projet, pas installés via npm.",
    "tags": ["nextjs", "shadcn", "dependencies", "critical"],
    "priority": "HIGH"
},
# Dans la liste factory_standards, ajoute :

# 1. shadcn/ui invalide
{
    "category": "nextjs",
    "text": "INTERDIT dans package.json: 'shadcn/ui' ou '@shadcn/ui'. shadcn/ui n'est pas une dépendance npm installable. Utiliser le CLI `npx shadcn@latest init` et ajouter uniquement les vraies dépendances npm requises.",
    "tags": ["nextjs", "npm", "package-json", "shadcn", "critical"],
    "priority": "HIGH"
},

# 2. Prisma 7 breaking change
{
    "category": "prisma",
    "text": "Si Prisma CLI >=7 est utilisé, NE PAS générer `datasource { url = env(...) }` dans schema.prisma. Utiliser `prisma.config.ts` conforme Prisma 7, ou pinner Prisma 5.x de façon cohérente (CLI + client + schema conventions).",
    "tags": ["prisma", "migration", "versioning", "breaking-change"],
    "priority": "HIGH"
},

# 3. Versions Prisma cohérentes
{
    "category": "prisma",
    "text": "Toujours pinner explicitement les versions `prisma` et `@prisma/client` dans package.json avant tout `prisma migrate`. Interdit de laisser `npx prisma` installer une version implicite latest.",
    "tags": ["prisma", "dependency-management", "build-stability"],
    "priority": "HIGH"
},

# 4. Mermaid validation
{
    "category": "architecture",
    "text": "Les diagrammes Mermaid doivent rester compacts et validables en <30s. Si validation CLI timeout, marquer explicitement `mermaid_validated=false` dans metadata et propager ce signal en aval.",
    "tags": ["mermaid", "validation", "quality-signal"],
    "priority": "MEDIUM"
},

# 5. npm token warning
{
    "category": "deployment",
    "text": "En CI/container, exécuter npm sans dépendance à un token privé pour packages publics. Si `.npmrc` contient auth expirée, neutraliser ou isoler le registry privé pour éviter bruit et erreurs de résolution.",
    "tags": ["npm", "ci", "container", "registry"],
    "priority": "MEDIUM"
},
]

async def upsert_standard(client: QdrantClient, text: str, metadata: dict) -> str:
    """Embed et upsert un standard dans Qdrant."""
    try:
        vector = EMBEDDINGS.embed_query(text)
        point_id = text_to_uuid(text)
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[PointStruct(
                id=point_id,
                vector=vector,
                payload={"text": text, "metadata": metadata}
            )],
            wait=True
        )
        return point_id
    except Exception as e:
        raise RuntimeError(f"Échec upsert du standard: {text[:60]}... → {str(e)}")


def _normalize_standard(standard: dict) -> dict:
    """
    Supporte deux formats d'entrée:
    - Nouveau format: {"text": "...", "metadata": {...}}
    - Format simplifié: {"category": "...", "text": "...", "tags": [...], "priority": "..."}
    """
    text = str(standard.get("text", "")).strip()
    metadata = standard.get("metadata")

    if not isinstance(metadata, dict):
        metadata = {
            "category": standard.get("category", "uncategorized"),
            "source": "factory_standards_v1",
            "outcome": "validated",
        }
        if "priority" in standard:
            metadata["priority"] = standard["priority"]
        tags = standard.get("tags")
        if isinstance(tags, list):
            metadata["tags"] = tags

    metadata.setdefault("category", "uncategorized")
    return {"text": text, "metadata": metadata}


async def populate():
    """Peuple factory_standards avec tous les standards définis."""
    print("\n" + "="*70)
    print("📚 POPULATION QDRANT — factory_standards  (version enrichie Sprint 1)")
    print("="*70 + "\n")
    
    client = QdrantClient(url=QDRANT_URL)
    
    # Vérification connexion + collection
    try:
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]
        if COLLECTION_NAME not in collection_names:
            print(f"❌ Collection '{COLLECTION_NAME}' introuvable.")
            print("   → Exécutez d'abord le script d'initialisation Qdrant.")
            return
        print(f"✅ Connexion Qdrant OK — Collection '{COLLECTION_NAME}' trouvée\n")
    except Exception as e:
        print(f"❌ Connexion Qdrant échouée: {e}")
        print("   → Vérifiez que le container Qdrant est lancé (docker-compose up -d)")
        return
    
    # État initial
    count_before = client.count(collection_name=COLLECTION_NAME, exact=True).count
    print(f"📊 Standards existants avant : {count_before}\n")
    
    # Groupement par catégorie pour un affichage clair
    categories = {}
    normalized_standards = []
    for std in STANDARDS:
        normalized = _normalize_standard(std)
        if not normalized["text"]:
            continue
        normalized_standards.append(normalized)
        cat = normalized["metadata"].get("category", "uncategorized")
        categories.setdefault(cat, []).append(normalized)
    
    total_added = 0
    
    for category, items in sorted(categories.items()):
        print(f"📁 {category.upper():<12} — {len(items)} standards")
        for i, standard in enumerate(items, 1):
            try:
                await upsert_standard(client, standard["text"], standard["metadata"])
                print(f"   {i:2d}/{len(items):2d}  ✅  {standard['text'][:68]}...")
                total_added += 1
            except Exception as e:
                print(f"   {i:2d}/{len(items):2d}  ❌  {standard['text'][:68]}...")
                print(f"       → {str(e)}")
        print()
    
    # Bilan final
    count_after = client.count(collection_name=COLLECTION_NAME, exact=True).count
    
    print("="*70)
    print("🎯 RÉSULTAT FINAL")
    print(f"   Avant     : {count_before} standards")
    print(f"   Ajoutés   : {total_added} standards")
    print(f"   Total     : {count_after} standards")
    print("="*70 + "\n")

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY manquant dans le fichier .env")
        exit(1)
    
    asyncio.run(populate())
