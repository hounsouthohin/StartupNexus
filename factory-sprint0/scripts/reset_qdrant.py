# scripts/reset_qdrant.py — à lancer UNE FOIS
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

client = QdrantClient(url="http://localhost:6333")

# Supprime et recrée la collection proprement
client.delete_collection("factory_standards")
client.create_collection(
    collection_name="factory_standards",
    vectors_config=VectorParams(size=3072, distance=Distance.COSINE)
)
print("Collection réinitialisée — 0 points")