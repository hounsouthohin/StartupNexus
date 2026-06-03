# agents/llm_provider.py
"""
Provider LLM — OpenAI uniquement.
Fournit validate_llm_env(), get_llm_provider(), get_chat_llm().

Prompt caching :
  1. InMemoryCache LangChain (process-level) — évite les appels OpenAI redondants pour
     des prompts identiques dans le même processus (ex: même brief soumis deux fois
     dans un batch, même requête RAG dupliquée entre les agents).
  2. seed=42 sur tous les appels — combiné à temperature=0, rend les sorties
     déterministes. OpenAI peut ainsi retrouver un résultat en cache côté serveur
     (prompt caching automatique, 50% de réduction sur les input tokens répétés).
"""
from __future__ import annotations

import logging
import os
from typing import Literal

logger = logging.getLogger(__name__)

LLMProvider = Literal["openai"]

# ── Cache LangChain process-level ────────────────────────────────────────────
# Activé une fois à l'import — toutes les instances ChatOpenAI/get_chat_llm()
# dans ce processus bénéficient du cache automatiquement.
# Thread-safe (dict Python avec GIL). Lifetime : durée du processus worker.
try:
    from langchain_core.globals import set_llm_cache
    from langchain_core.caches import InMemoryCache
    set_llm_cache(InMemoryCache())
    logger.debug("[llm_provider] InMemoryCache LangChain activé")
except Exception as _cache_err:
    logger.warning("[llm_provider] InMemoryCache non disponible : %s", _cache_err)


def validate_llm_env() -> tuple[bool, str]:
    """
    Valide que les variables d'environnement OpenAI sont présentes.
    Retourne (True, "OK") ou (False, message d'erreur).
    """
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return False, "OPENAI_API_KEY manquante ou vide — vérifier le fichier .env"
    return True, "OK"


def _get_base_url() -> str | None:
    """Retourne OPENAI_BASE_URL si définie (ex: GitHub Models endpoint)."""
    return os.getenv("OPENAI_BASE_URL") or None


def get_llm_provider() -> LLMProvider:
    """Retourne le provider LLM actif (toujours 'openai')."""
    return "openai"


def get_chat_llm(model: str | None = None, temperature: float = 0.0, api_key: str | None = None):
    """
    Retourne une instance ChatOpenAI configurée.
    model: identifiant du modèle (défaut: OPENAI_MODEL env var ou 'gpt-4o-mini')
    api_key: clé API à utiliser (défaut: OPENAI_API_KEY env var)

    seed=42 : rend les sorties déterministes (temperature=0 + seed fixe).
    OpenAI utilise ce signal pour son prompt caching côté serveur.
    """
    try:
        from langchain_openai import ChatOpenAI
    except ImportError as e:
        raise ImportError("langchain-openai requis : pip install langchain-openai") from e

    resolved_model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    kwargs: dict = {
        "model": resolved_model,
        "temperature": temperature,
        "api_key": api_key or os.getenv("OPENAI_API_KEY"),
        "model_kwargs": {"seed": 42},
    }
    base_url = _get_base_url()
    if base_url:
        kwargs["base_url"] = base_url
    # return ChatOpenAI(
    #     model=resolved_model,
    #     temperature=temperature,
    #     api_key=os.getenv("OPENAI_API_KEY"),
    #     model_kwargs={"seed": 42},
    # )
    return ChatOpenAI(**kwargs)
