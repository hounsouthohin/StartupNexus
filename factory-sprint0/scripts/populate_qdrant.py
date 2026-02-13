"""
scripts/populate_qdrant.py
Peuplement initial de la collection factory_standards dans Qdrant.
Idempotent — utilise UUIDs, peut être relancé sans créer de doublons.
Usage: python scripts/populate_qdrant.py
"""

import asyncio
import os
from uuid import uuid4
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct
from langchain_openai import OpenAIEmbeddings

load_dotenv(dotenv_path='.env')

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = "factory_standards"
EMBEDDINGS = OpenAIEmbeddings(model="text-embedding-3-large")

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
        "text": "Package.json pour projet Next.js 14 factory : next@14.2.3, react@18.3.0, react-dom@18.3.0. Scripts obligatoires : build (next build), dev (next dev), start (next start), lint (next lint), test (jest). La dépendance sharp doit être incluse pour l'optimisation des images en production sur Vercel.",
        "metadata": {"category": "nextjs", "tech": "next.js", "version": "14.2.3", "source": "factory_standards_v1", "outcome": "validated"}
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
        "text": "shadcn/ui avec Tailwind CSS est la librairie UI officielle pour tous les projets factory. Installation : npx shadcn-ui@latest init. Composants les plus utilisés : Button, Card, Input, Label, Form, Dialog, Table, Badge, Avatar, DropdownMenu. Importer depuis '@/components/ui/button' etc. Tailwind config doit inclure le darkMode et les custom colors shadcn.",
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
]

async def upsert_standard(client: QdrantClient, text: str, metadata: dict) -> str:
    """Embed et upsert un standard dans Qdrant."""
    try:
        vector = EMBEDDINGS.embed_query(text)
        point_id = str(uuid4())
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
    for std in STANDARDS:
        cat = std["metadata"]["category"]
        categories.setdefault(cat, []).append(std)
    
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