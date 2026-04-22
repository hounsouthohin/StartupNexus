"""
rag_client.py — Client RAG centralisé (Qdrant).

Responsabilité unique : fournir rag_search @tool au dev agent.
Extraits de shared_tools.py pour isoler la dépendance Qdrant.

Règle : ce module ne dépend que de stack_config, context, observability.
"""
from __future__ import annotations

import logging
import os
import re

from langchain_core.tools import tool

from agents.context import get_run_id, get_stack_id
from agents.observability import logger as _obs_logger, _append_rag_usage_event
from config.factory_config import (
    QDRANT_URL,
    QDRANT_COLLECTION_NAME,
    EMBEDDING_MODEL,
    DEFAULT_VECTOR_SEARCH_LIMIT,
)

logger = logging.getLogger(__name__)

# ── Singleton Qdrant (lazy init, module-level) ────────────────────────────────
_qdrant_store = None
_qdrant_embeddings = None


def _get_qdrant_store():
    global _qdrant_store, _qdrant_embeddings
    if _qdrant_store is not None:
        try:
            _qdrant_store.client.get_collections()
            return _qdrant_store
        except Exception:
            logger.warning("[qdrant] Store stale — reconnexion forcée")
            _qdrant_store = None
    try:
        from qdrant_client import QdrantClient
        from langchain_openai import OpenAIEmbeddings
        from langchain_qdrant import QdrantVectorStore

        _qdrant_embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
        client = QdrantClient(url=QDRANT_URL)
        _qdrant_store = QdrantVectorStore(
            client=client,
            collection_name=QDRANT_COLLECTION_NAME,
            embedding=_qdrant_embeddings,
            content_payload_key="text",
        )
        logger.info(f"[qdrant] Store initialisé: {QDRANT_URL}/{QDRANT_COLLECTION_NAME}")
        return _qdrant_store
    except Exception as e:
        logger.warning(f"[qdrant] Init failed: {e}")
        return None


# ── Filtre Qdrant depuis stack config ────────────────────────────────────────

def _json_filter_to_qdrant(filter_dict: dict):
    from qdrant_client.http.models import Filter, FieldCondition, MatchValue

    def _parse(cond: dict):
        if "should" in cond:
            return Filter(should=[_parse(c) for c in cond["should"]])
        if "must" in cond:
            return Filter(must=[_parse(c) for c in cond["must"]])
        if "key" in cond:
            return FieldCondition(key=cond["key"], match=MatchValue(value=cond["match"]["value"]))
        raise ValueError(f"[rag_client] Condition non reconnue: {cond}")

    must_raw = filter_dict.get("must", [])
    if not must_raw:
        return None
    return Filter(must=[_parse(c) for c in must_raw])


def _build_rag_filter(stack_id: str):
    try:
        from agents.stack_config import get_qdrant_filter_cfg, StackConfigError
        filter_cfg = get_qdrant_filter_cfg(stack_id).get("filter", {})
        if not filter_cfg:
            raise StackConfigError(
                f"[rag_client] qdrant_filter.filter absent pour stack '{stack_id}'"
            )
        return _json_filter_to_qdrant(filter_cfg)
    except Exception as e:
        logger.warning(f"[rag_client] Filtre RAG non disponible: {e}")
        return None


# ── rag_search @tool ──────────────────────────────────────────────────────────

@tool
def rag_search(query: str, k: int = DEFAULT_VECTOR_SEARCH_LIMIT) -> str:
    """
    Recherche les standards techniques pertinents dans la base RAG (Qdrant).
    Retourne le texte des documents trouvés avec leurs scores et catégories.
    """
    run_id = get_run_id()
    store = _get_qdrant_store()

    if store is None:
        _append_rag_usage_event(query=query, k=k, cache_hit=False, run_id=run_id, error="Qdrant unavailable")
        return "[RAG] Qdrant indisponible — continuer sans contexte RAG."

    try:
        max_docs = max(1, min(k, int(os.getenv("RAG_MAX_RETURN_DOCS", "4"))))
        max_doc_chars = max(120, int(os.getenv("RAG_DOC_MAX_CHARS", "700")))
        qdrant_filter = _build_rag_filter(get_stack_id())
        docs = store.similarity_search_with_score(query, k=k, filter=qdrant_filter)

        if not docs and qdrant_filter is not None:
            logger.warning("[rag_search] Aucun résultat avec filtre stack — vérifier reset_qdrant.py")

        if not docs:
            _append_rag_usage_event(query=query, k=k, cache_hit=False, run_id=run_id, doc_ids=[], scores=[], snippet="")
            return f"[RAG] Aucun résultat pour: {query}"

        deduped = []
        seen_keys: set[str] = set()
        for doc, score in docs:
            key = re.sub(r"\s+", " ", (doc.page_content or "").strip().lower())
            if not key or key in seen_keys:
                continue
            seen_keys.add(key)
            deduped.append((doc, score))
            if len(deduped) >= max_docs:
                break

        doc_ids = [str(getattr(d, "id", "") or "") for d, _ in deduped]
        scores = [float(s) for _, s in deduped]
        results = [
            f"[{d.metadata.get('category', 'general')}] score={s:.3f}\n{(d.page_content or '')[:max_doc_chars]}"
            for d, s in deduped
        ]
        snippet = deduped[0][0].page_content[:180] if deduped else ""
        _append_rag_usage_event(query=query, k=k, cache_hit=False, run_id=run_id, doc_ids=doc_ids, scores=scores, snippet=snippet)
        return "\n\n---\n\n".join(results)

    except Exception as e:
        _append_rag_usage_event(query=query, k=k, cache_hit=False, run_id=run_id, error=str(e))
        logger.error(f"[rag_search] Error: {e}")
        return ""
