# agents/llm_provider.py
"""
Provider LLM — OpenAI uniquement.
Fournit validate_llm_env(), get_llm_provider(), get_chat_llm().
"""
from __future__ import annotations

import os
from typing import Literal

LLMProvider = Literal["openai"]


def validate_llm_env() -> tuple[bool, str]:
    """
    Valide que les variables d'environnement OpenAI sont présentes.
    Retourne (True, "OK") ou (False, message d'erreur).
    """
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return False, "OPENAI_API_KEY manquante ou vide — vérifier le fichier .env"
    return True, "OK"


def get_llm_provider() -> LLMProvider:
    """Retourne le provider LLM actif (toujours 'openai')."""
    return "openai"


def get_chat_llm(model: str | None = None, temperature: float = 0.0):
    """
    Retourne une instance ChatOpenAI configurée.
    model: identifiant du modèle (défaut: OPENAI_MODEL env var ou 'gpt-4o-mini')
    """
    try:
        from langchain_openai import ChatOpenAI
    except ImportError as e:
        raise ImportError("langchain-openai requis : pip install langchain-openai") from e

    resolved_model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    return ChatOpenAI(
        model=resolved_model,
        temperature=temperature,
        api_key=os.getenv("OPENAI_API_KEY"),
    )
