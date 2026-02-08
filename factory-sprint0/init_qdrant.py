import asyncio
import os
from uuid import uuid4
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from langchain_openai import OpenAIEmbeddings

# Configuration
load_dotenv(dotenv_path='.env')
COLLECTION_NAME = "factory_standards"
EMBEDDINGS = OpenAIEmbeddings(model="text-embedding-3-large")
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")

# --- Fonctions Utilitaires ---

def get_qdrant_client():
    """Initialise et retourne un client Qdrant."""
    return QdrantClient(url=QDRANT_URL)

async def upsert_dynamic_standard(text: str, metadata: dict):
    """
    Embed un texte et l'ajoute (upsert) comme un nouveau standard dynamique dans Qdrant.
    Utilise un UUID pour garantir un identifiant unique.
    """
    client = get_qdrant_client()
    try:
        vector = EMBEDDINGS.embed_query(text)
        
        # Utiliser UUID pour un ID unique et robuste
        point_id = str(uuid4())
        
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={"text": text, "metadata": metadata}
                )
            ],
            wait=True
        )
        print(f"✅ Standard dynamique upserté avec succès. ID: {point_id}")
        return point_id
    except Exception as e:
        print(f"❌ Erreur lors de l'upsert du standard dynamique : {e}")
        return None

async def init_collection():
    """
    Initialise la connexion à Qdrant, crée la collection si elle n'existe pas,
    et vérifie si elle est prête pour l'ajout dynamique de standards.
    """
    client = get_qdrant_client()
    max_retries = 5
    wait_seconds = 5

    # 1. Connexion robuste à Qdrant
    for attempt in range(max_retries):
        try:
            client.get_collections()
            print("✅ Connexion à Qdrant réussie !")
            break
        except Exception as e:
            print(f"⚠️ Tentative {attempt + 1}/{max_retries} échouée: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(wait_seconds)
            else:
                print("❌ Échec de la connexion à Qdrant. Le script va s'arrêter.")
                raise

    # 2. Création/Vérification de la collection
    try:
        collections_response = client.get_collections()
        collection_names = [c.name for c in collections_response.collections]
        
        if COLLECTION_NAME not in collection_names:
            print(f"La collection '{COLLECTION_NAME}' n'existe pas. Création...")
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=3072, distance=Distance.COSINE),
            )
            print(f"Collection '{COLLECTION_NAME}' créée avec succès.")
        else:
            print(f"La collection '{COLLECTION_NAME}' existe déjà.")

        # 3. Vérification du contenu de la collection
        count_response = client.count(collection_name=COLLECTION_NAME, exact=True)
        if count_response.count == 0:
            print("텅텅 Standards vides – ready for Learner upsert. 텅텅")
        else:
            print(f"📊 La collection contient {count_response.count} standard(s).")

    except Exception as e:
        print(f"❌ Une erreur est survenue : {e}")
        raise

async def main_simulation():
    """
    Simule le workflow complet : initialisation puis ajout d'un standard.
    """
    print("--- Début de la simulation ---")
    
    # Étape 1: Assurer que la collection est prête
    await init_collection()
    
    print("\n--- Simulation de l'ajout par un 'Learner' ---")
    
    # Étape 2: Un agent 'Learner', après un build réussi, ajoute un nouveau standard.
    # Ceci est un exemple de comment la fonction `upsert_dynamic_standard` serait appelée.
    winning_pattern_text = "Winning pattern: Pour les projets Next.js 14.2+, la dépendance `sharp` est souvent nécessaire pour l'optimisation d'images. L'ajouter via `npm install sharp` résout les erreurs de build sur Vercel."
    winning_pattern_metadata = {
        "category": "build",
        "tech": "nextjs",
        "source": "learner_agent_run_123",
        "outcome": "success"
    }
    
    await upsert_dynamic_standard(winning_pattern_text, winning_pattern_metadata)
    
    # Vérification que le standard a bien été ajouté
    client = get_qdrant_client()
    count_response = client.count(collection_name=COLLECTION_NAME, exact=True)
    print(f"📊 Nombre de standards après upsert : {count_response.count}")

    print("\n--- Fin de la simulation ---")


if __name__ == "__main__":
    # Exécute la simulation complète pour démonstration
    asyncio.run(main_simulation())
