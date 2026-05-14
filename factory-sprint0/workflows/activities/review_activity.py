"""
workflows/activities/review_activity.py
────────────────────────────────────────
Temporal Activity — Revue sémantique post-build.

Sélectionne les fichiers métier (services, actions, pages) parmi generated_files,
fetch les standards ZONE_15 + ZONE_16 depuis Qdrant (agent_context=reviewer),
puis délègue à agents.reviewer.run_reviewer.

Ne s'exécute que si build_status == "BUILD_SUCCESS".
"""
from __future__ import annotations

import os
import sys
from typing import Any, Dict, List

from temporalio import activity
from temporalio.exceptions import ApplicationError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# ── Sélection de fichiers ─────────────────────────────────────────────────────

_SERVICE_PATTERNS = ("lib/services/", "services/")
_ACTION_PATTERNS = ("actions.ts", "actions.tsx")
_PAGE_PATTERNS = ("page.tsx", "page.ts")
_MAX_FILES = 12


def _select_files_for_review(generated_files: Dict[str, str]) -> Dict[str, str]:
    """
    Choisit les fichiers les plus pertinents pour la revue sémantique.
    Priorité : services > actions > pages. Max _MAX_FILES fichiers.
    Exclut : node_modules, .env, config, jest, middleware, tsconfig.
    """
    _EXCLUDE = (
        "node_modules", ".env", "jest.", "tsconfig", "middleware.ts",
        "next.config", "tailwind", "postcss", ".d.ts",
    )

    def _is_excluded(path: str) -> bool:
        return any(ex in path for ex in _EXCLUDE)

    services: Dict[str, str] = {}
    actions: Dict[str, str] = {}
    pages: Dict[str, str] = {}

    for path, content in generated_files.items():
        if _is_excluded(path):
            continue
        if any(path.startswith(p) for p in _SERVICE_PATTERNS):
            services[path] = content
        elif any(path.endswith(p) for p in _ACTION_PATTERNS):
            actions[path] = content
        elif any(path.endswith(p) for p in _PAGE_PATTERNS):
            pages[path] = content

    selected: Dict[str, str] = {}
    for bucket in (services, actions, pages):
        for path, content in bucket.items():
            if len(selected) >= _MAX_FILES:
                break
            selected[path] = content
        if len(selected) >= _MAX_FILES:
            break

    return selected


# ── Fetch standards RAG (agent_context=reviewer) ──────────────────────────────

_REVIEWER_QUERIES = [
    "IDOR update delete userId where clause security",
    "cross-user data exposure findMany filter userId",
    "server action auth userId transmission service",
    "ghost success brief entities mismatch generated code",
    "page stub empty hardcoded data user flow",
]


def _fetch_reviewer_standards(stack_id: str) -> str:
    """
    Interroge Qdrant avec filtre agent_context=reviewer + status=active.
    Retourne le texte des standards concaténés.
    """
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.http.models import Filter, FieldCondition, MatchValue
        from langchain_openai import OpenAIEmbeddings
        from langchain_qdrant import QdrantVectorStore
        from config.factory_config import QDRANT_URL, QDRANT_COLLECTION_NAME, EMBEDDING_MODEL
    except ImportError as e:
        activity.logger.warning(f"[review_activity] Qdrant non disponible: {e}")
        return ""

    try:
        embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
        client = QdrantClient(url=QDRANT_URL)
        store = QdrantVectorStore(
            client=client,
            collection_name=QDRANT_COLLECTION_NAME,
            embedding=embeddings,
            content_payload_key="text",
        )

        reviewer_filter = Filter(must=[
            FieldCondition(key="metadata.agent_context", match=MatchValue(value="reviewer")),
            FieldCondition(key="metadata.status", match=MatchValue(value="active")),
        ])

        seen: set[str] = set()
        collected: List[str] = []

        for query in _REVIEWER_QUERIES:
            try:
                docs = store.similarity_search_with_score(query, k=3, filter=reviewer_filter)
                for doc, score in docs:
                    text = (doc.page_content or "").strip()
                    key = text[:80].lower()
                    if key and key not in seen:
                        seen.add(key)
                        zone = doc.metadata.get("zone", "?")
                        collected.append(f"[{zone} score={score:.3f}]\n{text}")
            except Exception as qe:
                activity.logger.warning(f"[review_activity] Query Qdrant failed ({query[:40]}): {qe}")

        activity.logger.info(f"[review_activity] {len(collected)} standards reviewer récupérés depuis Qdrant")
        return "\n\n---\n\n".join(collected)

    except Exception as e:
        activity.logger.warning(f"[review_activity] Erreur fetch standards reviewer: {e}")
        return ""


# ── Auth contract (contrainte ferme pour le reviewer) ─────────────────────────

def _build_page_auth_contract(spec: dict) -> str:
    """
    Table compacte {path → auth | type | model} construite depuis project_spec.pages.
    Injectée dans le reviewer comme contrainte non-négociable pour éviter l'oscillation
    add-auth / remove-auth sur des pages dont le régime est fixé par le brief.
    """
    pages = spec.get("pages") or []
    if not pages:
        return ""
    lines = [
        "### PAGE AUTH CONTRACT (source de vérité — CONTRAINTE NON NÉGOCIABLE)",
        "NE PAS flagguer ces pages pour leur régime d'auth — il est fixé par le brief.\n",
    ]
    for page in pages:
        if isinstance(page, dict):
            path   = page.get("path", "?")
            auth   = page.get("auth_required", True)
            p_type = page.get("page_type", "custom")
            model  = page.get("model") or ""
        else:
            path   = getattr(page, "path", "?")
            auth   = getattr(page, "auth_required", True)
            p_type = getattr(page, "page_type", "custom")
            model  = getattr(page, "model", None) or ""
        auth_str  = "auth_required" if auth else "public"
        model_str = f" | model: {model}" if model else ""
        lines.append(f"{path} → {auth_str} | type: {p_type}{model_str}")
    return "\n".join(lines)


# ── Temporal Activity ─────────────────────────────────────────────────────────

@activity.defn(name="review_activity")
async def review_activity(input_data: Dict[str, Any], run_id: str = "") -> Dict[str, Any]:
    """
    Revue sémantique post-build.

    Input attendu :
        project_name    : str
        stack_id        : str
        brief           : str
        spec            : dict  (output architect: entités, routes)
        user_flows      : list
        generated_files : dict[str, str]
        build_status    : str

    Output :
        review_report   : dict  (ReviewReport complet)
        review_verdict  : str   ("COHERENT" | "DEGRADED" | "INCOHERENT" | "SKIPPED")
        review_skipped  : bool
    """
    project_name = input_data.get("project_name", "projet-sans-nom")
    stack_id = str(input_data.get("stack_id", "nextjs-clerk-prisma"))
    build_status = str(input_data.get("build_status", ""))

    # Ne pas reviewer si le build a échoué
    if build_status != "BUILD_SUCCESS":
        activity.logger.info(
            f"[review_activity] Revue ignorée — build_status={build_status!r}"
        )
        return {
            "review_report": {},
            "review_verdict": "SKIPPED",
            "review_skipped": True,
        }

    try:
        from agents.shared_tools import set_run_id, set_stack_id
        set_run_id(run_id)
        set_stack_id(stack_id)
    except Exception:
        pass

    brief = str(input_data.get("brief", ""))
    spec = input_data.get("spec", {}) or {}
    user_flows = input_data.get("user_flows", []) or []
    page_auth_contract = _build_page_auth_contract(spec)
    generated_files = input_data.get("generated_files", {}) or {}

    activity.logger.info(
        f"[review_activity] Démarrage — projet={project_name} "
        f"fichiers_totaux={len(generated_files)}"
    )

    # 1. Sélection fichiers métier
    selected_files = _select_files_for_review(generated_files)
    activity.logger.info(
        f"[review_activity] {len(selected_files)} fichier(s) sélectionnés pour la revue: "
        + ", ".join(selected_files.keys())
    )

    if not selected_files:
        activity.logger.warning("[review_activity] Aucun fichier métier trouvé — revue ignorée")
        return {
            "review_report": {},
            "review_verdict": "SKIPPED",
            "review_skipped": True,
        }

    # 2. Fetch standards reviewer depuis Qdrant
    rag_standards = _fetch_reviewer_standards(stack_id)

    # 3. Appel reviewer
    try:
        from agents.reviewer import run_reviewer
        report = await run_reviewer(
            brief=brief,
            spec=spec,
            user_flows=user_flows,
            selected_files=selected_files,
            rag_standards=rag_standards,
            run_id=run_id,
            stack_id=stack_id,
            page_auth_contract=page_auth_contract,
        )
    except Exception as e:
        activity.logger.error(f"[review_activity] run_reviewer échoué: {e}", exc_info=True)
        raise ApplicationError("REVIEW_EXECUTION_FAILED", str(e))

    verdict = report.get("verdict", "COHERENT")
    activity.logger.info(
        f"[review_activity] Revue terminée — verdict={verdict} "
        f"sec={report.get('security_score')} coh={report.get('coherence_score')} "
        f"findings={len(report.get('findings', []))}"
    )

    return {
        "review_report": report,
        "review_verdict": verdict,
        "review_skipped": False,
    }
