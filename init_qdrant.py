import asyncio
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from langchain_openai import OpenAIEmbeddings
import os

load_dotenv(dotenv_path='factory-sprint0/.env')


# === CONFIG ===
client = QdrantClient("http://localhost:6333")  # ton Qdrant local
collection_name = "factory_standards"
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")  # ou ton modèle préféré

# === PREMIERS STANDARDS (on commence solide, on enrichira après) ===
standards = [
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
]

async def init_collection():
    # Créer collection si inexistante
    collections = client.get_collections()
    if collection_name not in [c.name for c in collections.collections]:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=3072, distance=Distance.COSINE),
        )
        print(f"Collection '{collection_name}' créée.")

    # Embedder et uploader
    points = []
    for i, item in enumerate(standards):
        vector = embeddings.embed_query(item["text"])
        points.append(
            PointStruct(
                id=i + 1,
                vector=vector,
                payload={
                    "text": item["text"],
                    "metadata": item["metadata"]
                }
            )
        )
    
    client.upsert(collection_name=collection_name, points=points)
    print(f"{len(standards)} standards injectés avec succès dans Qdrant ! 🚀")
    print("L'Agent Architecte va maintenant pouvoir faire du RAG et sortir des specs/diagrammes bien plus riches.")

if __name__ == "__main__":
    asyncio.run(init_collection())