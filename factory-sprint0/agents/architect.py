# agents/architect.py
# ===============================================
# ARCHITECTE LOGICIEL IA - Refactored for Chained Prompts (décembre 2025)
# ===============================================

import os
import json
import re
import subprocess
import asyncio
import tempfile
import logging
import time
from datetime import datetime
from typing import List, TypedDict, Annotated
from temporalio.exceptions import ApplicationError
import operator
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage
from config.factory_config import QDRANT_URL, QDRANT_COLLECTION_NAME, EMBEDDING_MODEL, DEFAULT_VECTOR_SEARCH_LIMIT
from utils.prompt_loader import load_base_prompt, load_stack_rules_only
from agents.stack_config import _DEFAULT_STACK_ID

load_dotenv()
logger = logging.getLogger(__name__)

DEFAULT_FORBIDDEN_AUTH_PATTERNS = [
    r"\bbcrypt\b",
    r"\bjwt\b",
    r"\bjsonwebtoken\b",
    r"\boauth2?\b",
    r"\bpassport\b",
    r"\bexpress-session\b",
    r"\bcookie-session\b",
    r"\bnextauth\b",
    r"\bnext-auth\b",
    r"\bpassword_hash\b",
    r"\bhashed_password\b",
    r"/api/auth/register",
    r"/api/auth/login",
]


def _load_forbidden_auth_patterns(stack_id: str) -> list[str]:
    try:
        from agents.stack_config import load_stack_config
        stack_cfg = load_stack_config(stack_id) or {}
        patterns = stack_cfg.get("forbidden_auth_patterns", [])
        if isinstance(patterns, list) and patterns:
            return [str(p) for p in patterns]
    except Exception:
        pass
    return DEFAULT_FORBIDDEN_AUTH_PATTERNS


def _contains_forbidden_auth(text: str, stack_id: str = _DEFAULT_STACK_ID) -> bool:
    lowered = text.lower()
    patterns = _load_forbidden_auth_patterns(stack_id)
    return any(re.search(pattern, lowered) for pattern in patterns)


def _extract_brief_entities(phrase: str) -> str:
    """
    Parse déterministiquement le brief pour extraire les entités explicites.
    Injecté dans le planner input pour que le LLM ne puisse pas les ignorer.
    Retourne une chaîne "ENTITÉS OBLIGATOIRES" ou "" si rien de détectable.
    """
    lines = []

    # Modèles Prisma avec champs entre accolades
    model_blocks = re.findall(
        r'(?:Mod[eè]le?\s+Prisma|model)\s*:?\s*(\w+)\s*\{([^}]+)\}',
        phrase, re.IGNORECASE
    )
    if model_blocks:
        for name, fields in model_blocks:
            field_list = re.sub(r'\s+', ' ', fields.strip())
            lines.append(f"MODELE PRISMA: {name} {{ {field_list} }}")
    else:
        # Modèles sans champs détaillés
        model_names = re.findall(
            r'(?:Mod[eè]le?\s+Prisma|model)\s*:?\s*(\w+)', phrase, re.IGNORECASE
        )
        for name in model_names:
            lines.append(f"MODELE PRISMA: {name}")

    # Méthodes HTTP explicites (GET/POST/PUT/PATCH/DELETE + chemin)
    http_methods = re.findall(r'\b(GET|POST|PUT|PATCH|DELETE)\s+(/[\w/\[\]-]+)', phrase)
    for method, path in http_methods:
        lines.append(f"ENDPOINT API: {method} {path}")

    # Tous les chemins /... (pages + routes API)
    all_paths = re.findall(r'/[\w/\[\]-]{2,}', phrase)
    pages = [p for p in all_paths if '/api/' not in p]
    api_routes = [p for p in all_paths if '/api/' in p]
    # Exclut les paths déjà listés via http_methods
    already = {path for _, path in http_methods}
    api_routes = [p for p in api_routes if p not in already]

    if pages:
        lines.append(f"PAGES: {', '.join(dict.fromkeys(pages))}")
    if api_routes:
        lines.append(f"ROUTES API: {', '.join(dict.fromkeys(api_routes))}")

    if not lines:
        return ""
    return "ENTITÉS OBLIGATOIRES (extraites du brief — toutes DOIVENT apparaître dans le plan) :\n" + "\n".join(f"  - {l}" for l in lines)


def _is_generic_plan(plan: dict, phrase: str) -> tuple[bool, str]:
    """
    Détecte si le plan est générique (auth-only) alors que le brief demande des entités métier.
    Retourne (is_generic, reason).
    """
    data_models_str = " ".join(str(m) for m in plan.get("data_models", [])).lower()
    pages_str = " ".join(str(p) for p in plan.get("pages", [])).lower()

    # Cherche les modèles métier non-User dans le brief
    model_names = re.findall(
        r'(?:Mod[eè]le?\s+Prisma|model)\s*:?\s*(\w+)', phrase, re.IGNORECASE
    )
    for name in model_names:
        if name.lower() not in ("user", "") and name.lower() not in data_models_str:
            return True, f"Modèle '{name}' mentionné dans le brief mais absent du plan"

    # Cherche les chemins métier dans le brief
    business_paths = [
        p for p in re.findall(r'/[\w/\[\]-]{2,}', phrase)
        if not any(auth in p for auth in ["sign-in", "sign-up", "login", "register"])
        and len(p) > 1
    ]
    for path in business_paths:
        # Normalise [slug] → matcher flexible
        path_key = re.sub(r'\[[\w-]+\]', '', path).strip("/")
        if path_key and path_key not in pages_str:
            return True, f"Page/route '{path}' mentionnée dans le brief mais absente du plan"

    return False, ""


def _extract_requirements_from_plan(plan: dict) -> list:
    """
    Extrait une liste plate de requirements depuis le plan Architect.
    Priorité : champ requirements[] du plan (LLM). Fallback : dérivé des autres champs.
    """
    if isinstance(plan.get("requirements"), list) and plan["requirements"]:
        return [str(r) for r in plan["requirements"] if r]
    # Fallback dérivé si le LLM n'a pas rempli requirements[]
    # Supporte nouveau format (data_models/pages/api_routes) et legacy (schema/auth_flow)
    reqs = []
    for model in plan.get("data_models", []):
        reqs.append(f"Modèle Prisma: {model}")
    # Clé "schema" = format legacy (ex: "User model with clerkId")
    schema = plan.get("schema", "")
    if schema and not plan.get("data_models"):
        reqs.append(f"Modèle Prisma: {schema}")
    for page in plan.get("pages", []):
        reqs.append(f"Page: {page}")
    for route in plan.get("api_routes", []):
        reqs.append(f"API Route: {route}")
    for feature in plan.get("key_features", []):
        reqs.append(f"Feature: {feature}")
    # "auth_flow" et "security_measures" ne sont pas mappables en fichier → ignorés
    return reqs


def _build_hard_rewrite_instructions(stack_id: str) -> str:
    """
    Construit un bloc de rewrite depuis les règles stack.
    Évite tout couplage Clerk/Next.js en dur.
    """
    try:
        from agents.stack_config import load_stack_config
        stack_cfg = load_stack_config(stack_id) or {}
    except Exception:
        stack_cfg = {}
    prompt_rules = stack_cfg.get("prompt_rules", {}) if isinstance(stack_cfg.get("prompt_rules"), dict) else {}
    auth_rules = prompt_rules.get("auth_rules", []) if isinstance(prompt_rules.get("auth_rules"), list) else []
    orm_rules = prompt_rules.get("orm_rules", []) if isinstance(prompt_rules.get("orm_rules"), list) else []
    security_rules = prompt_rules.get("security_rules", []) if isinstance(prompt_rules.get("security_rules"), list) else []

    lines = []
    for rule in [*auth_rules, *orm_rules, *security_rules]:
        if isinstance(rule, str) and rule.strip():
            lines.append(f"- {rule.strip()}")
    if not lines:
        lines = [
            "- Respect strict de l'auth définie par la stack.",
            "- Respect strict du schéma de données défini par la stack.",
            "- Retourner uniquement le markdown corrigé.",
        ]
    if not any("Retourner" in ln or "return" in ln.lower() for ln in lines):
        lines.append("- Retourner uniquement le markdown corrigé.")
    return "\n".join(lines)

def _resolve_architect_models(active_stack: str) -> tuple[str, str]:
    """
    Résout les modèles LLM Architect via env puis stack config.
    Priorité:
    1) ARCHITECT_BASE_MODEL / ARCHITECT_PLANNER_MODEL
    2) stack_cfg.llm_models.architect_base / architect_planner
    3) défauts sûrs
    """
    default_base = "gpt-4o-mini"
    default_planner = "gpt-4o"
    stack_base = ""
    stack_planner = ""
    try:
        from agents.stack_config import load_stack_config
        stack_cfg = load_stack_config(active_stack) or {}
        llm_models = stack_cfg.get("llm_models", {})
        if isinstance(llm_models, dict):
            stack_base = str(llm_models.get("architect_base", "")).strip()
            stack_planner = str(llm_models.get("architect_planner", "")).strip()
    except Exception:
        pass

    base_model = (
        os.getenv("ARCHITECT_BASE_MODEL", "").strip()
        or stack_base
        or default_base
    )
    planner_model = (
        os.getenv("ARCHITECT_PLANNER_MODEL", "").strip()
        or stack_planner
        or default_planner
    )
    return base_model, planner_model

def _build_minimal_plan_from_phrase(phrase: str, stack_id: str = _DEFAULT_STACK_ID) -> dict:
    """
    Fallback déterministe sans LLM:
    construit un plan JSON minimal valide à partir du brief.
    """
    model_blocks = re.findall(
        r'(?:Mod[eè]le?\s+Prisma|model)\s*:?\s*(\w+)\s*\{([^}]+)\}',
        phrase,
        re.IGNORECASE,
    )
    model_names = []
    data_models = []
    for name, fields in model_blocks:
        model_names.append(name)
        field_list = re.sub(r"\s+", " ", fields.strip())
        data_models.append(f"{name} {{ {field_list} }}")
    if not data_models:
        for name in re.findall(r'(?:Mod[eè]le?\s+Prisma|model)\s*:?\s*(\w+)', phrase, re.IGNORECASE):
            if name not in model_names:
                model_names.append(name)
                data_models.append(name)

    http_methods = re.findall(r'\b(GET|POST|PUT|PATCH|DELETE)\s+(/[\w/\[\]-]+)', phrase)
    api_paths = [p for _, p in http_methods]
    api_routes = [f"app/{p.strip('/')}/route.ts" for p in dict.fromkeys(api_paths)]

    all_paths = re.findall(r'/[\w/\[\]-]{1,}', phrase)
    page_paths = [p for p in all_paths if "/api/" not in p]
    pages = []
    for p in dict.fromkeys(page_paths):
        if p == "/":
            pages.append("app/page.tsx")
        else:
            pages.append(f"app/{p.strip('/')}/page.tsx")
    if not pages:
        pages = ["app/page.tsx"]

    description = phrase.strip().splitlines()[0][:180] if phrase.strip() else "Web app"
    key_features = []
    if "/dashboard" in phrase:
        key_features.append("dashboard protégé")
    if http_methods:
        key_features.append("API routes")
    if not key_features:
        key_features = ["fonctionnalités métier"]

    requirements = []
    for model in data_models:
        requirements.append(f"Modèle Prisma: {model}")
    for p in dict.fromkeys(page_paths):
        requirements.append(f"Page: {p}")
    for method, path in http_methods:
        requirements.append(f"API Route: {method} {path}")
    if not requirements:
        requirements.append("Page: /")

    return {
        "app_type": "web_app",
        "router_type": "app",
        "stack": stack_id or _DEFAULT_STACK_ID,
        "description": description,
        "pages": pages,
        "data_models": data_models,
        "auth_required": True,
        "api_routes": api_routes,
        "key_features": key_features,
        "requirements": requirements,
    }


def _build_minimal_spec_from_requirements(plan: dict, requirements: list[str]) -> str:
    """
    Fallback déterministe pour éviter un blocage Architect sur SPEC_INVALID.
    Génère une spec markdown minimale, structurée, couvrant explicitement les requirements.
    """
    reqs = [str(r).strip() for r in (requirements or []) if str(r).strip()]
    pages: list[str] = []
    api_routes: list[str] = []
    prisma_models: list[str] = []
    other: list[str] = []
    for r in reqs:
        rl = r.lower()
        if "modèle prisma" in rl or "model prisma" in rl:
            prisma_models.append(r)
        elif rl.startswith("page"):
            pages.append(r)
        elif rl.startswith("api route"):
            api_routes.append(r)
        else:
            other.append(r)

    stack = str((plan or {}).get("stack", _DEFAULT_STACK_ID))
    description = str((plan or {}).get("description", "Spécification minimale déterministe"))
    lines = [
        "## Vue d'ensemble",
        description,
        "",
        "## Stack technique",
        f"- Stack: {stack}",
        "- Next.js App Router",
        "- Clerk",
        "- Prisma + PostgreSQL",
        "",
        "## Structure des pages",
    ]
    if pages:
        lines.extend([f"- {p}" for p in pages])
    else:
        lines.append("- Page: /")

    lines.extend(["", "## Schéma Prisma"])
    if prisma_models:
        lines.extend([f"- {m}" for m in prisma_models])
    else:
        lines.append("- Modèle Prisma: à compléter selon requirements")

    lines.extend(["", "## Authentification Clerk", "- Accès protégé via Clerk sur les routes privées"])
    lines.extend(["", "## API Routes"])
    if api_routes:
        lines.extend([f"- {a}" for a in api_routes])
    else:
        lines.append("- Aucune route API explicite dans les requirements")

    lines.extend(["", "## Composants Tailwind", "- Composants UI basés sur Tailwind CSS"])
    if other:
        lines.extend(["", "## Requirements complémentaires"])
        lines.extend([f"- {o}" for o in other])

    return "\n".join(lines).strip() + "\n"


def _append_architect_rag_event(query: str, scored_docs: list, error: str | None = None, run_id: str = "") -> None:
    """
    scored_docs : List[Tuple[Document, float]] — retourné par asimilarity_search_with_score.
    """
    try:
        _log_root = Path(os.getenv("FACTORY_LOG_DIR", "/app/logs"))
        metrics_dir = _log_root / "metrics"
        metrics_dir.mkdir(parents=True, exist_ok=True)
        path = metrics_dir / "rag_usage.jsonl"
        doc_ids = [str(getattr(d, "id", None) or "") for d, _ in (scored_docs or [])]
        scores = [float(s) for _, s in (scored_docs or [])]
        snippet = str(getattr(scored_docs[0][0], "page_content", ""))[:180] if scored_docs else ""
        event = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "agent": "architect_retrieval",
            "query": query,
            "k": DEFAULT_VECTOR_SEARCH_LIMIT,
            "cache_hit": False,
            "result_count": len(scored_docs or []),
            "doc_ids": doc_ids,
            "scores": scores,
            "snippet": snippet,
            "run_id": run_id,
            "error": error,
        }
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception as log_err:
        logger.warning(f"Architect RAG metrics logging failed: {log_err}")

# --- Pydantic Models for State ---
class ArchitectOutput(BaseModel):
    specification: str = Field(description="The full technical specification in Markdown format.")
    mermaid_diagram: str = Field(description="The complete and valid Mermaid diagram syntax.")
    requirements: list = Field(default_factory=list, description="Flat list of all business requirements extracted from the brief.")

class AgentState(TypedDict):
    messages: Annotated[List, operator.add]
    rag_context: str
    plan: dict
    specification: str
    mermaid_diagram: str
    architect_output: ArchitectOutput
    run_id: str
    stack_id: str
    requirements: list

# --- Prompt Loading ---
def _parse_level1_sections(content: str) -> dict[str, str]:
    """
    Parse uniquement les sections de niveau 1 (# Titre).
    Ignore les sections ## pour éviter les captures parasites.
    """
    sections: dict[str, str] = {}
    current_title = None
    current_lines: list[str] = []

    for line in content.split("\n"):
        if line.startswith("# ") and not line.startswith("## "):
            if current_title is not None:
                sections[current_title] = "\n".join(current_lines).strip()
            current_title = line[2:].strip().lower().replace(" ", "_")
            current_lines = []
            continue
        current_lines.append(line)

    if current_title is not None:
        sections[current_title] = "\n".join(current_lines).strip()

    return sections


def load_prompts():
    """Charge les prompts architecte base + rules stack injectées par section."""
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.messages import SystemMessage, HumanMessage
    try:
        try:
            from agents.shared_tools import get_stack_id
            active_stack = get_stack_id()
        except Exception:
            active_stack = _DEFAULT_STACK_ID

        base_content = load_base_prompt("architect")
        stack_rules = load_stack_rules_only("architect", active_stack)
        sections = _parse_level1_sections(base_content)

        prompts = {}
        for title, section_content in sections.items():
            prompt_content = section_content
            if stack_rules:
                prompt_content = (
                    f"{section_content}\n\n---\n\n"
                    "## REGLES STACK OBLIGATOIRES\n\n"
                    f"{stack_rules}"
                )
            prompts[title] = ChatPromptTemplate.from_messages([
                SystemMessage(content=prompt_content),
                HumanMessage(content="{input}")
            ])

        required_sections = {"planner", "spec_writer", "diagrammer"}
        if not required_sections.issubset(set(prompts.keys())):
            missing = required_sections - set(prompts.keys())
            raise RuntimeError(
                f"Sections manquantes dans prompts/base/architect.md: {sorted(missing)}. "
                f"Trouvees: {sorted(prompts.keys())}"
            )
        return prompts
    except FileNotFoundError:
        raise FileNotFoundError("prompts/base/architect.md not found.")
    except Exception as e:
        raise RuntimeError(f"Failed to parse prompts/base/architect.md: {e}")

def _wait_for_qdrant(url: str, max_wait_seconds: int = 90, poll_interval: float = 5.0) -> None:
    """Attend que Qdrant accepte les connexions avant d'initialiser QdrantVectorStore."""
    from qdrant_client import QdrantClient as _QC
    deadline = time.monotonic() + max_wait_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            _QC(url=url).get_collections()
            return
        except Exception as exc:
            last_error = exc
            remaining = round(deadline - time.monotonic(), 1)
            logger.info(
                f"[wait_for_qdrant] Qdrant pas encore prêt ({exc}) "
                f"— retry dans {poll_interval}s (reste {remaining}s)"
            )
            time.sleep(poll_interval)
    raise RuntimeError(
        f"Qdrant non disponible après {max_wait_seconds}s "
        f"(url: {url}, dernière erreur: {last_error})"
    )


def _build_architect_rag_filter(stack_id: str):
    """
    Construit le filtre Qdrant pour le retriever architect.
    Governance v1 : injecte toujours metadata.status=active pour exclure
    les standards deprecated/archived, quelle que soit la config stack.
    """
    try:
        from agents.stack_config import get_qdrant_filter_cfg
        from qdrant_client.http.models import Filter, FieldCondition, MatchValue

        def _parse(cond: dict):
            if "key" in cond:
                return FieldCondition(key=cond["key"], match=MatchValue(value=cond["match"]["value"]))
            if "must" in cond:
                return Filter(must=[_parse(c) for c in cond["must"]])
            if "should" in cond:
                return Filter(should=[_parse(c) for c in cond["should"]])
            return None

        # Governance v1 — condition toujours présente
        status_condition = FieldCondition(
            key="metadata.status",
            match=MatchValue(value="active"),
        )

        filter_cfg = get_qdrant_filter_cfg(stack_id).get("filter", {})
        must_raw = filter_cfg.get("must", [])
        extra_conditions = [_parse(c) for c in must_raw if c]

        return Filter(must=[status_condition, *extra_conditions])
    except Exception:
        return None


# ==================== CRÉATION DU GRAPH ====================
def create_architect_agent():
    # Imports moved inside the function to avoid Temporal sandbox issues
    from langgraph.graph import StateGraph, START, END
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    from langchain_qdrant import QdrantVectorStore
    from qdrant_client import QdrantClient

    prompts = load_prompts()
    
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    _wait_for_qdrant(QDRANT_URL)
    client = QdrantClient(url=QDRANT_URL)
    vectorstore = QdrantVectorStore(
        client=client,
        collection_name=QDRANT_COLLECTION_NAME,
        embedding=embeddings,
        content_payload_key="text",
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": DEFAULT_VECTOR_SEARCH_LIMIT})
    try:
        from agents.shared_tools import get_stack_id
        active_stack = str(get_stack_id() or _DEFAULT_STACK_ID)
    except Exception:
        active_stack = _DEFAULT_STACK_ID
    base_model, planner_model = _resolve_architect_models(active_stack)

    _llm_base = ChatOpenAI(model=base_model, temperature=0.1, max_retries=3)
    _planner_llm_base = ChatOpenAI(model=planner_model, temperature=0.1, max_retries=3)
    if os.getenv("LLM_FALLBACK_ENABLED", "0") == "1":
        llm = _llm_base.with_fallbacks(
            [ChatOpenAI(model="gpt-4o", temperature=0.1, max_retries=1)]
        )
        planner_llm = _planner_llm_base.with_fallbacks(
            [ChatOpenAI(model="gpt-4o-mini", temperature=0.1, max_retries=1)]
        )
    else:
        llm = _llm_base
        planner_llm = _planner_llm_base

    # --- Nodes ---
    async def retrieval_node(state: AgentState):
        query = state["messages"][-1].content
        run_id = str(state.get("run_id", ""))
        stack_id = str(state.get("stack_id", _DEFAULT_STACK_ID))
        scored_docs = []  # List[Tuple[Document, float]]
        try:
            qdrant_filter = _build_architect_rag_filter(stack_id)
            if qdrant_filter is not None:
                scored_docs = await vectorstore.asimilarity_search_with_score(query, k=DEFAULT_VECTOR_SEARCH_LIMIT, filter=qdrant_filter)
            else:
                plain_docs = await retriever.ainvoke(query)
                scored_docs = [(d, 0.0) for d in plain_docs]
            _append_architect_rag_event(query=query, scored_docs=scored_docs, error=None, run_id=run_id)
        except Exception as e:
            logger.warning(f"RAG indisponible: {e} - continuation sans contexte")
            _append_architect_rag_event(query=query, scored_docs=[], error=str(e), run_id=run_id)
        docs = [d for d, _ in scored_docs]
        rag_context = "\n\n".join([f"--- STANDARD {i+1} ({doc.metadata.get('category', 'général')}) ---\n{doc.page_content}" for i, doc in enumerate(docs)]) if docs else "No relevant standards found."
        print(f"RAG Context for Planner:\n{rag_context}\n--- END RAG CONTEXT ---")
        return {"rag_context": rag_context}
    
    async def planner_node(state: AgentState):
        phrase = state['messages'][-1].content
        stack_id = str(state.get("stack_id", _DEFAULT_STACK_ID))

        # ── Extraction déterministe des entités du brief ──────────────────────
        brief_entities = _extract_brief_entities(phrase)
        input_text = f"User Request: {phrase}\n\nRAG Context:\n{state['rag_context']}"
        if brief_entities:
            input_text += f"\n\n{brief_entities}"

        chain = prompts['planner'] | planner_llm
        llm_response = await chain.ainvoke({"input": input_text})

        match = re.search(r'```json\s*\n(.*?)\n\s*```', llm_response.content, re.DOTALL)
        json_content = match.group(1).strip() if match else llm_response.content.strip()

        try:
            plan = json.loads(json_content)
        except json.JSONDecodeError:
            # Fallback dur: réduit le bruit (sans RAG) et force un JSON strict.
            strict_input = (
                "Return ONLY valid JSON matching this schema keys exactly: "
                "app_type, router_type, stack, description, pages, data_models, auth_required, api_routes, key_features, requirements.\n"
                f"User Request: {phrase}\n"
                f"{brief_entities}\n"
                "No prose. No markdown fences. JSON object only."
            )
            strict_response = await chain.ainvoke({"input": strict_input})
            strict_match = re.search(r'```json\s*\n(.*?)\n\s*```', strict_response.content, re.DOTALL)
            strict_content = strict_match.group(1).strip() if strict_match else strict_response.content.strip()
            try:
                plan = json.loads(strict_content)
            except json.JSONDecodeError as e:
                logger.warning(
                    "[planner] Non-JSON après 2 essais LLM — fallback déterministe activé "
                    f"(error={e})"
                )
                plan = _build_minimal_plan_from_phrase(phrase=phrase, stack_id=stack_id)

        # ── Validation post-plan : détection plan générique ──────────────────
        is_generic, reason = _is_generic_plan(plan, phrase)
        if is_generic and brief_entities:
            logger.warning(f"[planner] Plan générique détecté — retry forcé. Raison: {reason}")
            retry_input = (
                f"User Request: {phrase}\n\nRAG Context:\n{state['rag_context']}\n\n"
                f"{brief_entities}\n\n"
                f"ATTENTION — ton plan précédent était incomplet : {reason}\n"
                f"Génère un nouveau plan JSON qui inclut TOUTES les entités listées ci-dessus.\n"
                f"Aucune entité ne doit être omise."
            )
            llm_response = await chain.ainvoke({"input": retry_input})
            match = re.search(r'```json\s*\n(.*?)\n\s*```', llm_response.content, re.DOTALL)
            json_content = match.group(1).strip() if match else llm_response.content.strip()
            try:
                plan = json.loads(json_content)
                logger.info("[planner] Plan corrigé après retry générique")
            except json.JSONDecodeError:
                logger.warning("[planner] Retry plan invalide JSON — on garde le plan original")

        requirements = _extract_requirements_from_plan(plan)
        logger.info(f"[planner] {len(requirements)} requirements extraits du brief")
        return {"plan": plan, "requirements": requirements}

    async def spec_writer_node(state: AgentState):
        plan_json = json.dumps(state['plan'], indent=2)
        requirements = state.get("requirements", [])

        input_text = (
            f"High-Level Plan (JSON):\n{plan_json}"
        )

        # Injection explicite des requirements — le LLM DOIT les couvrir tous
        if requirements:
            reqs_block = "\n".join(f"  - {r}" for r in requirements)
            input_text += (
                f"\n\nREQUIREMENTS OBLIGATOIRES — tous doivent apparaître dans la spec :\n{reqs_block}\n"
                f"\nATTENTION : chaque modèle Prisma listé ci-dessus DOIT figurer dans ## Schéma Prisma "
                f"avec TOUS ses champs — utilise le NOM EXACT du requirement, sans synonyme ni traduction. "
                f"Ne génère PAS une spec auth-only si des requirements métier sont présents."
            )
        
        chain = prompts['spec_writer'] | llm
        llm_response = await chain.ainvoke({"input": input_text})
        specification = llm_response.content

        active_stack = str(state.get("stack_id", _DEFAULT_STACK_ID))
        if _contains_forbidden_auth(specification, active_stack):
            logger.warning("Spec contains forbidden auth terms. Forcing one rewrite with strict stack constraints.")
            rewrite_rules = _build_hard_rewrite_instructions(active_stack)
            harden_input = (
                input_text
                + "\n\nMANDATORY REWRITE — Règles auth stack obligatoires:\n"
                + rewrite_rules
                + "\n- Return only corrected markdown."
            )
            llm_response = await chain.ainvoke({"input": harden_input})
            specification = llm_response.content

        try:
            from agents.stack_config import load_stack_config
            _spec_val = load_stack_config(active_stack).get("spec_validation", {})
        except Exception:
            _spec_val = {}
        required_keywords = _spec_val.get("required_keywords", [])
        forbidden_keywords = _spec_val.get("forbidden_keywords", [])
        required_sections = _spec_val.get("required_sections", [])

        spec_lower = specification.lower()
        missing_keywords = [kw for kw in required_keywords if kw not in spec_lower]
        found_forbidden = [kw for kw in forbidden_keywords if kw in spec_lower]
        missing_sections = [sec for sec in required_sections if sec not in spec_lower]

        if missing_keywords or found_forbidden or missing_sections:
            logger.warning(
                "Spec invalid for stack. Missing keywords=%s, forbidden=%s, missing sections=%s",
                missing_keywords,
                found_forbidden,
                missing_sections,
            )
            rewrite_rules = _build_hard_rewrite_instructions(active_stack)
            harden_input = (
                input_text
                + "\n\nMANDATORY REWRITE — Stack semantic corrections required:\n"
                + (f"- Missing stack keywords: {missing_keywords}\n" if missing_keywords else "")
                + (f"- Forbidden technologies found: {found_forbidden}\n" if found_forbidden else "")
                + (f"- Missing markdown sections: {missing_sections}\n" if missing_sections else "")
                + rewrite_rules
                + "\n- Return only corrected markdown."
            )
            llm_response = await chain.ainvoke({"input": harden_input})
            specification = llm_response.content

        # ── SPEC REQUIREMENTS GATE (Sprint 5) ────────────────────────────────
        # Détecte les dérives de noms (Post→Article, /blog→/articles) DANS le node,
        # avant que la spec dégradée ne se propage au DevAgent.
        # Un seul retry ciblé sur les requirements absents — non-bloquant si encore DEGRADED.
        try:
            from agents.spec_validator import validate_spec_requirements
            sv_result = validate_spec_requirements(specification, requirements)
            if sv_result["status"] == "DEGRADED" and sv_result["unmatched_requirements"]:
                logger.warning(
                    f"[spec_writer_node] Spec DEGRADED — "
                    f"{len(sv_result['unmatched_requirements'])} requirement(s) absents : "
                    f"{sv_result['unmatched_requirements']}"
                )
                unmatched_list = "\n".join(f"  - {r}" for r in sv_result["unmatched_requirements"])
                correction_input = (
                    input_text
                    + "\n\nCORRECTION OBLIGATOIRE — les requirements suivants sont ABSENTS de ta spec :\n"
                    + unmatched_list
                    + "\n\nRÈGLE ABSOLUE : copie les noms des requirements MOT POUR MOT dans la spec. "
                    "Si un requirement dit 'MonModèle', écris 'MonModèle' dans ## Schéma Prisma — jamais un synonyme. "
                    "Si un requirement dit '/mon-chemin/[id]', cette route DOIT apparaître dans ## Pages ou ## API Routes. "
                    "Régénère uniquement la spec corrigée — retourne uniquement le markdown."
                )
                llm_response = await chain.ainvoke({"input": correction_input})
                specification = llm_response.content
                sv_final = validate_spec_requirements(specification, requirements)
                if sv_final["status"] == "DEGRADED":
                    logger.critical(
                        f"[spec_writer_node] Spec encore DEGRADED après correction — "
                        f"unmatched: {sv_final['unmatched_requirements']}"
                    )
                    # Fallback déterministe: spec minimale couvrant mot pour mot les requirements.
                    specification = _build_minimal_spec_from_requirements(state.get("plan", {}), requirements)
                    sv_after_fallback = validate_spec_requirements(specification, requirements)
                    if sv_after_fallback["status"] == "DEGRADED":
                        logger.critical(
                            f"[spec_writer_node] Fallback spec encore DEGRADED — "
                            f"unmatched: {sv_after_fallback['unmatched_requirements']}"
                        )
                    else:
                        logger.info(
                            f"[spec_writer_node] Fallback spec OK — "
                            f"{sv_after_fallback['matched_count']}/{sv_after_fallback['total_mappable']} requirements couverts"
                        )
                    # Enforce mode : bloquer si le gate l'exige (non-retryable)
                    try:
                        from scripts.sprint5_gate import load_gate as _load_gate
                        _gate = _load_gate()
                        if _gate.get("enforce", False):
                            from temporalio.exceptions import ApplicationError as _AE
                            raise _AE(
                                "SPEC_GATE_ENFORCE",
                                f"Spec DEGRADED après 2 tentatives — gate en mode enforce. "
                                f"Requirements manquants : {sv_final['unmatched_requirements']}",
                                non_retryable=True,
                            )
                    except (SystemExit, KeyboardInterrupt):
                        raise
                    except Exception as _ge:
                        if "SPEC_GATE_ENFORCE" in str(_ge):
                            raise
                        logger.warning(f"[spec_writer_node] Gate enforce check non bloquant : {_ge}")
                else:
                    logger.info(
                        f"[spec_writer_node] Spec corrigée — "
                        f"{sv_final['matched_count']}/{sv_final['total_mappable']} requirements couverts"
                    )
        except ApplicationError:
            raise  # ne jamais avaler un gate enforce non-retryable
        except Exception as sv_err:
            logger.warning(f"[spec_writer_node] Spec gate non bloquant : {sv_err}")

        return {"specification": specification}

    async def diagrammer_node(state: AgentState):
        max_attempts = 3
        attempts = 0
        input_text = f"Technical Specification:\n{state['specification']}"
        
        # Dossier temporaire cross-platform (Windows local / Linux Docker)
        default_mermaid_dir = r"C:\temp\mermaid" if os.name == "nt" else "/tmp/mermaid"
        host_dir = os.getenv("MERMAID_TMP_DIR", default_mermaid_dir)
        os.makedirs(host_dir, exist_ok=True)
        
        while attempts < max_attempts:
            attempts += 1
            chain = prompts['diagrammer'] | llm
            llm_response = await chain.ainvoke({"input": input_text})
            
            match = re.search(r'```(?:mermaid)?\s*\n(.*?)\n\s*```', llm_response.content, re.DOTALL)
            mermaid_code = match.group(1).strip() if match else llm_response.content.strip()

            try:
                # Création fichier temporaire dans dossier fixe
                with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.mmd', dir=host_dir) as tmp_file:
                    tmp_file.write(mermaid_code)
                    tmp_file_path = tmp_file.name
                
                input_filename = os.path.basename(tmp_file_path)
                output_filename = f"{input_filename}.png"

                validation_error = None
                try:
                    result = await asyncio.to_thread(
                        subprocess.run,
                        ['npx', '@mermaid-js/mermaid-cli', '-i', tmp_file_path, '-o', output_filename],
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    if result.returncode != 0:
                        raise ValueError(result.stderr or result.stdout or 'Unknown Mermaid CLI error')
                except Exception as e:
                    validation_error = str(e)
                    logger.warning(f"Validation Mermaid ignorée: {e}")

                # Nettoyage
                if os.path.exists(tmp_file_path):
                    os.remove(tmp_file_path)
                output_path = os.path.join(host_dir, output_filename)
                if os.path.exists(output_path):
                    os.remove(output_path)

                if validation_error:
                    logger.info(f"Mermaid retourné sans validation stricte (tentative {attempts}/{max_attempts})")
                else:
                    logger.info(f"Mermaid validé après {attempts} tentatives")
                return {"mermaid_diagram": mermaid_code}

            except Exception as e:
                if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
                    os.remove(tmp_file_path)
                error_message = f"Mermaid generation failed (Attempt {attempts}/{max_attempts}). Error: {e}"
                logger.error(error_message)

                if attempts >= max_attempts:
                    raise ValueError(f"Failed to generate Mermaid diagram after {max_attempts} attempts. Last error: {error_message}")

                input_text += f"\n\nPrevious attempt failed. Please correct the syntax based on this error: {error_message}"
                state["messages"].append(HumanMessage(content=f"Diagram generation failed with error: {error_message}. Please fix the Mermaid syntax."))

        raise ValueError(f"Failed to generate a valid Mermaid diagram after {max_attempts} attempts.")

    def formatter_node(state: AgentState):
        architect_output = ArchitectOutput(
            specification=state['specification'],
            mermaid_diagram=state['mermaid_diagram'],
            requirements=state.get('requirements', []),
        )
        return {"architect_output": architect_output}

    # --- Graph Definition ---
    workflow = StateGraph(AgentState)
    workflow.add_node("retrieval", retrieval_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("spec_writer", spec_writer_node)
    workflow.add_node("diagrammer", diagrammer_node)
    workflow.add_node("formatter", formatter_node)

    workflow.add_edge(START, "retrieval")
    workflow.add_edge("retrieval", "planner")
    workflow.add_edge("planner", "spec_writer")
    workflow.add_edge("spec_writer", "diagrammer")
    workflow.add_edge("diagrammer", "formatter")
    workflow.add_edge("formatter", END)

    return workflow.compile()
