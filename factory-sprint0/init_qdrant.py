import asyncio
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from langchain_openai import OpenAIEmbeddings
import os

load_dotenv(dotenv_path='.env')


collection_name = "factory_standards"
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")  # ou ton modèle préféré

# === PREMIERS STANDARDS (on commence solide, on enrichira après) ===
standards = [
    {
        "text": "CLERK EXCLUSIF - INTERDIRE CUSTOM AUTH\nProjet SaaS : utiliser UNIQUEMENT Clerk. Supprimer bcrypt, JWT, routes /api/auth, champ password. Générer pages Clerk standards, UserButton, Tailwind + shadcn/ui.",
        "metadata": {"category": "authentication", "priority": "critical", "priority_score": 100}
    },
    {
        "text": "Dans tout projet Next.js impliquant de l'authentification : utiliser EXCLUSIVEMENT Clerk (@clerk/nextjs). Interdire bcrypt, stockage de passwords, JWT custom, table Session séparée. Utiliser les pages/routes Clerk standards : app/sign-in/[[...sign-in]]/page.tsx et app/sign-up/[[...sign-up]]/page.tsx. Toute implémentation manuelle d'auth est une violation critique des standards.",
        "metadata": {"category": "authentication", "tech": "clerk", "priority": "critical", "priority_score": 100}
    },
    {
        "text": "UI/UX : Toujours utiliser shadcn/ui + Tailwind CSS. Composants accessibles, dark mode natif. Mobile-first obligatoire. Utiliser la fonction cn() de tailwind-merge pour les className conditionnelles.",
        "metadata": {"category": "ui", "tech": "tailwind", "priority": "high"}
    },
    {
        "text": "Frontend : Next.js 14+ avec App Router obligatoire. Server Components par défaut. Route handlers dans app/api/. Fetch data côté serveur. Utiliser React Server Components pour performances.",
        "metadata": {"category": "frontend", "tech": "nextjs", "priority": "high"}
    },
    {
        "text": "Backend : Prisma ORM avec PostgreSQL ou MongoDB. Schema strict dans prisma/schema.prisma. Toujours définir relations explicites. Migrations avec prisma migrate dev.",
        "metadata": {"category": "backend", "tech": "prisma", "priority": "high"}
    },
    {
        "text": "Authentification : Prioriser Clerk ou NextAuth v5 (app router). Sinon JWT + httpOnly cookies sécurisés. Jamais stocker JWT en localStorage. Refresh tokens obligatoires. Blacklist ou expiry court.",
        "metadata": {"category": "security", "tech": "auth", "priority": "critical"}
    },
    {
        "text": "Architecture Mermaid : Toujours séparer Frontend / Backend / Database avec subgraphs. Montrer flux JWT (génération → stockage → header → middleware). Mettre en évidence parties sécurisées (bcrypt, middleware auth).",
        "metadata": {"category": "architecture", "tech": "mermaid", "priority": "high"}
    },
    {
        "text": "Sécurité : HTTPS obligatoire, validation inputs (zod), rate limiting, CORS strict, protection CSRF, headers security (helmet). Hachage bcrypt + sel.",
        "metadata": {"category": "security", "tech": "general", "priority": "critical"}
    },
    {
        "text": "Structure projet Next.js : app/ pour pages et API routes, components/, lib/, actions/, types/. Toujours séparer server-only et client components.",
        "metadata": {"category": "structure", "tech": "nextjs", "priority": "high"}
    },
    # Ajoutes-en autant que tu veux ici plus tard
    {
        "text": "Pinned Dependencies: All `package.json` dependencies must be pinned to exact versions to ensure reproducible builds. Example: `\"next\": \"14.2.3\"`, not `\"^14.2.3\"`.",
        "metadata": {"category": "build", "tech": "npm", "priority": "high"}
    },
    {
        "text": "Password Hashing (bcrypt): User passwords must always be hashed before being stored in the database. Use the `bcrypt` library with a salt factor of at least 10.",
        "metadata": {"category": "security", "tech": "bcrypt", "priority": "critical"}
    },
    {
        "text": "Input Validation (Zod): All API route inputs and form submissions must be validated server-side using Zod to prevent invalid data and common vulnerabilities like injection.",
        "metadata": {"category": "security", "tech": "zod", "priority": "high"}
    },
    {
        "text": "Authentication Middleware (Clerk): Protect all application routes by default using Clerk's `middleware.ts`. Only explicitly public pages (e.g., `/sign-in`) should be exempted.",
        "metadata": {"category": "security", "tech": "clerk", "priority": "critical"}
    },
    {
        "text": "OWASP Top 10 - Injection: Prevent injection flaws by using Prisma's parameterized queries. Never concatenate strings to build database queries.",
        "metadata": {"category": "security", "tech": "prisma", "priority": "critical"}
    },
    {
        "text": "OWASP Top 10 - Broken Authentication: Manage sessions securely using Clerk's built-in session management. Do not implement custom session logic.",
        "metadata": {"category": "security", "tech": "clerk", "priority": "critical"}
    },
    {
        "text": "Mocking Authentication in Tests: When testing components that use Clerk, mock the `@clerk/nextjs` library using `jest.mock('@clerk/nextjs')` to provide a controlled test environment.",
        "metadata": {"category": "testing", "tech": "jest", "priority": "high"}
    },
    {
        "text": "Test Coverage Standard: All new components, hooks, and API routes must have a corresponding Jest test file with a target of >80% test coverage.",
        "metadata": {"category": "testing", "tech": "jest", "priority": "medium"}
    },
    {
        "text": "State Management: For simple global state, use React Context. For complex state, consider using Zustand, but consult RAG for project approval first.",
        "metadata": {"category": "frontend", "tech": "react", "priority": "medium"}
    },
    {
        "text": "UI Components (shadcn/ui): All UI components should be built using `shadcn/ui` and Tailwind CSS for consistency. Do not introduce other UI libraries without architectural approval.",
        "metadata": {"category": "ui", "tech": "shadcn", "priority": "high"}
    },
    {
        "text": "Error Handling in APIs: API routes should handle errors gracefully, return appropriate HTTP status codes (e.g., 400 for bad request, 500 for server error), and log errors server-side.",
        "metadata": {"category": "backend", "tech": "api", "priority": "high"}
    },
    {
        "text": "Environment Variables: Sensitive information like API keys and database URLs must be loaded from environment variables (`.env`) and never be hardcoded in the source code.",
        "metadata": {"category": "security", "tech": "general", "priority": "critical"}
    },
    {
        "text": "Tests Jest : Toujours créer un fichier jest.config.js à la racine avec preset ts-jest, testEnvironment jsdom, setupFilesAfterEnv @testing-library/jest-dom, et moduleNameMapper pour CSS avec identity-obj-proxy.",
        "metadata": {"category": "testing", "tech": "jest", "priority": "high"}
    },
]

async def init_collection():
    # --- CONFIGURATION AMÉLIORÉE ---
    # L'URL est maintenant lue depuis une variable d'environnement pour la flexibilité en production.
    # Fallback sur localhost si la variable n'est pas définie.
    qdrant_url = os.getenv("QDRANT_URL", "http://qdrant:6333")
    client = QdrantClient(url=qdrant_url)
    
    # --- LOGIQUE DE CONNEXION ROBUSTE AVEC RETRY ---
    max_retries = 10
    wait_seconds = 5
    for attempt in range(max_retries):
        try:
            # La méthode la plus simple pour vérifier la connexion est de faire un appel léger.
            client.get_collections() 
            print("✅ Connexion à Qdrant réussie !")
            break # Sort de la boucle si la connexion est OK
        except Exception as e:
            print(f"⚠️ Tentative {attempt + 1}/{max_retries} échouée. Impossible de se connecter à Qdrant à l'adresse {qdrant_url}. Erreur : {e}")
            if attempt < max_retries - 1:
                print(f"   Prochaine tentative dans {wait_seconds} secondes...")
                await asyncio.sleep(wait_seconds)
            else:
                print("❌ Échec de la connexion à Qdrant après plusieurs tentatives. Le script va s'arrêter.")
                raise # Propage l'exception pour faire échouer le script si Qdrant n'est pas dispo

    # --- CRÉATION DE LA COLLECTION ---
    try:
        collections_response = client.get_collections()
        collection_names = [c.name for c in collections_response.collections]
        
        if collection_name not in collection_names:
            print(f"La collection '{collection_name}' n'existe pas. Création...")
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=3072, distance=Distance.COSINE), # 3072 pour text-embedding-3-large
            )
            print(f"Collection '{collection_name}' créée avec succès.")
        else:
            print(f"La collection '{collection_name}' existe déjà.")

        # --- EMBEDDING ET UPLOAD DES STANDARDS ---
        print("Début de l'embedding et de l'upload des standards...")
        points_to_upsert = []
        for i, item in enumerate(standards):
            # L'embedding est une opération qui peut prendre du temps.
            vector = embeddings.embed_query(item["text"])
            points_to_upsert.append(
                PointStruct(
                    id=i + 1, # Les IDs doivent être uniques
                    vector=vector,
                    payload={
                        "text": item["text"],
                        "metadata": item["metadata"]
                    }
                )
            )
        
        # Upsert en batch pour plus d'efficacité
        client.upsert(
            collection_name=collection_name,
            points=points_to_upsert,
            wait=True # Attendre que l'opération soit terminée
        )
        
        print(f"✅ {len(standards)} standards ont été injectés/mis à jour dans Qdrant ! 🚀")
        print("   L'Agent Architecte peut maintenant utiliser le RAG pour des specs et diagrammes de haute qualité.")

    except Exception as e:
        print(f"❌ Une erreur est survenue pendant la création de la collection ou l'upload des points : {e}")
        raise

if __name__ == "__main__":
    asyncio.run(init_collection())