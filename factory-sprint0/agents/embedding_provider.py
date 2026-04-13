# agents/embedding_provider.py
"""
Provider Embeddings — OpenAI uniquement.
Fournit get_embeddings(), resolve_embedding_model(), detect_embedding_dimension(), get_embedding_provider().
"""
from __future__ import annotations

import os
from typing import Literal

EmbeddingProvider = Literal["openai"]

# Dimensions connues par modèle OpenAI
_MODEL_DIMENSIONS: dict[str, int] = {
    "text-embedding-3-large": 3072,
    "text-embedding-3-small": 1536,
    "text-embedding-ada-002": 1536,
}

_DEFAULT_MODEL = "text-embedding-3-large"


def get_embedding_provider() -> EmbeddingProvider:
    """Retourne le provider embeddings actif (toujours 'openai')."""
    return "openai"


def resolve_embedding_model(model: str | None = None) -> str:
    """
    Résout le nom du modèle d'embedding à utiliser.
    Priorité : argument > EMBEDDING_MODEL env var > défaut text-embedding-3-large.
    """
    if model and model.strip():
        return model.strip()
    env_model = os.getenv("EMBEDDING_MODEL", "").strip()
    if env_model:
        return env_model
    return _DEFAULT_MODEL


def detect_embedding_dimension(model: str | None = None) -> int:
    """
    Retourne la dimension vectorielle du modèle d'embedding.
    Utilise la table statique, puis tente une requête réelle si inconnu.
    """
    resolved = resolve_embedding_model(model)
    if resolved in _MODEL_DIMENSIONS:
        return _MODEL_DIMENSIONS[resolved]
    # Modèle inconnu : tente de détecter via une requête réelle
    try:
        embeddings_fn = get_embeddings(resolved)
        sample = embeddings_fn.embed_query("test")
        return len(sample)
    except Exception:
        return 1536  # fallback sécurisé


def get_embeddings(model: str | None = None):
    """
    Retourne une instance OpenAIEmbeddings configurée.
    model: identifiant du modèle (défaut: resolve_embedding_model())
    """
    try:
        from langchain_openai import OpenAIEmbeddings
    except ImportError as e:
        raise ImportError("langchain-openai requis : pip install langchain-openai") from e

    resolved_model = resolve_embedding_model(model)
    return OpenAIEmbeddings(
        model=resolved_model,
        api_key=os.getenv("OPENAI_API_KEY"),
    )
