# agents/web_search.py
"""
Outil web_search — LangChain @tool appelé directement par le LLM (gpt-4o).

Le LLM formule lui-même la requête quand il est bloqué sur une erreur TypeScript/Next.js.
Python n'injecte plus les résultats : c'est le modèle qui décide quand chercher.

Moteurs supportés (par ordre de priorité) :
  1. Tavily   — TAVILY_API_KEY  (gratuit 1000 req/mois, résultats AI-optimisés)
  2. SearXNG  — SEARXNG_URL     (auto-hébergé Docker, illimité, zéro coût)
  3. DuckDuckGo — aucune clé    (pip install ddgs, toujours disponible)
"""
from __future__ import annotations

import logging
import os
from typing import Optional

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

_TAVILY_KEY = os.getenv("TAVILY_API_KEY", "").strip()
_SEARXNG_URL = os.getenv("SEARXNG_URL", "").strip()
_MAX_RESULTS = 3
_SNIPPET_MAX_CHARS = 600


# ── Moteur 1 : Tavily ─────────────────────────────────────────────────────────

def _try_tavily(query: str, n: int) -> Optional[str]:
    if not _TAVILY_KEY:
        return None
    try:
        import httpx  # type: ignore
        resp = httpx.post(
            "https://api.tavily.com/search",
            json={
                "api_key": _TAVILY_KEY,
                "query": query,
                "max_results": n,
                "search_depth": "basic",
                "include_answer": True,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        parts: list[str] = []
        if data.get("answer"):
            parts.append(f"SYNTHÈSE : {data['answer'][:600]}")
        for r in data.get("results", [])[:n]:
            snippet = (r.get("content") or r.get("snippet") or "")[:_SNIPPET_MAX_CHARS]
            title = r.get("title", "")
            if snippet:
                parts.append(f"[{title}]\n{snippet}")
        return "\n\n".join(parts) if parts else None
    except Exception as exc:
        logger.warning("[web_search:tavily] %s", exc)
        return None


# ── Moteur 2 : SearXNG (auto-hébergé) ────────────────────────────────────────

def _try_searxng(query: str, n: int) -> Optional[str]:
    if not _SEARXNG_URL:
        return None
    try:
        import httpx  # type: ignore
        resp = httpx.get(
            f"{_SEARXNG_URL.rstrip('/')}/search",
            params={"q": query, "format": "json", "pageno": 1},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        parts: list[str] = []
        for r in data.get("results", [])[:n]:
            snippet = (r.get("content") or "")[:_SNIPPET_MAX_CHARS]
            if snippet:
                parts.append(f"[{r.get('title', '')}]\n{snippet}")
        return "\n\n".join(parts) if parts else None
    except Exception as exc:
        logger.warning("[web_search:searxng] %s", exc)
        return None


# ── Moteur 3 : DuckDuckGo (fallback sans clé) ────────────────────────────────

def _try_duckduckgo(query: str, n: int) -> Optional[str]:
    try:
        from ddgs import DDGS  # type: ignore
    except ImportError:
        logger.debug("[web_search] ddgs non installé — pip install ddgs")
        return None
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=n))
        if not results:
            return None
        parts: list[str] = []
        for r in results:
            snippet = (r.get("body") or "")[:_SNIPPET_MAX_CHARS]
            if snippet:
                parts.append(f"[{r.get('title', '')}]\n{snippet}")
        return "\n\n".join(parts) if parts else None
    except Exception as exc:
        logger.warning("[web_search:ddg] %s", exc)
        return None


# ── Outil LLM ────────────────────────────────────────────────────────────────

@tool
def web_search(query: str) -> str:
    """Search the web for TypeScript/Next.js documentation or error fixes.

    Use this tool ONLY when you are blocked on a TypeScript or Next.js error after
    1-2 failed correction attempts and do not have the solution in context.

    Write a focused query — include the TS error code, the error message, and the stack:
      Good: "TypeScript TS2322 null not assignable undefined interface props fix Next.js 14"
      Good: "Next.js 14 Server Action auth import @clerk/nextjs/server fix"
      Bad:  pasting the full raw error

    Returns concatenated documentation snippets, or "[WEB_SEARCH_UNAVAILABLE]" if
    no search engine is reachable.
    """
    logger.info("[web_search] query=%r", query[:80])

    result = _try_tavily(query, _MAX_RESULTS)
    if result:
        logger.info("[web_search] via=tavily chars=%d", len(result))
        return result

    result = _try_searxng(query, _MAX_RESULTS)
    if result:
        logger.info("[web_search] via=searxng chars=%d", len(result))
        return result

    result = _try_duckduckgo(query, _MAX_RESULTS)
    if result:
        logger.info("[web_search] via=duckduckgo chars=%d", len(result))
        return result

    logger.warning(
        "[web_search] aucun moteur disponible — "
        "définir TAVILY_API_KEY, SEARXNG_URL, ou installer ddgs"
    )
    return "[WEB_SEARCH_UNAVAILABLE]"
