# agents/architect.py
# ===============================================
# ARCHITECTE LOGICIEL IA - Refactored for Chained Prompts (décembre 2025)
# ===============================================

import os
import json
import re
import asyncio
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
from config.factory_config import QDRANT_URL, QDRANT_COLLECTION_NAME, EMBEDDING_MODEL, DEFAULT_VECTOR_SEARCH_LIMIT, ARCHITECT_RAG_SCORE_THRESHOLD
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


def _is_generic_plan(plan: dict, normalized_brief: str) -> tuple[bool, str]:
    """
    Détecte si le plan est générique (auth-only) alors que le brief demande des entités métier.
    Utilise normalized_brief (format Brief Normalizer : "- ModelName: ...") pour une détection fiable.
    Fallback regex sur raw brief si normalized_brief est absent.
    Retourne (is_generic, reason) — observation uniquement, non bloquant.
    """
    data_models_str = " ".join(str(m) for m in plan.get("data_models", [])).lower()
    pages_str = " ".join(str(p) for p in plan.get("pages", [])).lower()

    # Format Brief Normalizer : "- ModelName: champ1 (type), ..."
    model_names = re.findall(r'^-\s+(\w+):', normalized_brief, re.MULTILINE)
    if not model_names:
        # Fallback : format raw brief (regex legacy)
        model_names = re.findall(
            r'(?:Mod[eè]le?\s+Prisma|model)\s*:?\s*(\w+)', normalized_brief, re.IGNORECASE
        )

    for name in model_names:
        if name.lower() not in ("user", "") and name.lower() not in data_models_str:
            return True, f"Modèle '{name}' mentionné dans le brief mais absent du plan"

    # Chemins métier (fonctionnent dans les deux formats)
    business_paths = [
        p for p in re.findall(r'/[\w/\[\]-]{2,}', normalized_brief)
        if not any(auth in p for auth in ["sign-in", "sign-up", "login", "register"])
    ]
    for path in business_paths:
        path_key = re.sub(r'\[[\w-]+\]', '', path).strip("/")
        if path_key and path_key not in pages_str:
            return True, f"Page/route '{path}' mentionnée dans le brief mais absente du plan"

    return False, ""


def _extract_requirements_from_plan(plan: dict) -> list:
    """
    Dérive les requirements déterministiquement depuis data_models/pages/api_routes du plan.
    Ne lit jamais plan["requirements"] (LLM-généré, source de dérive documentée).
    """
    reqs = []
    for model in plan.get("data_models", []):
        reqs.append(f"Modèle Prisma: {model}")
    schema = plan.get("schema", "")
    if schema and not plan.get("data_models"):
        reqs.append(f"Modèle Prisma: {schema}")
    for page in plan.get("pages", []):
        reqs.append(f"Page: {page}")
    for route in plan.get("api_routes", []):
        reqs.append(f"API Route: {route}")
    return reqs if reqs else ["Page: /"]


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
class SpecOutput(BaseModel):
    """IR structuré de la spec — complément JSON du markdown brut (P2).
    Construit de façon déterministe dans formatter_node, sans appel LLM supplémentaire.
    specification: str reste le contrat garanti (≥500 chars markdown).
    """
    spec_summary: str = Field(default="", description="Premier paragraphe non-titre de la spec (≤300 chars).")
    entities_in_spec: list = Field(default_factory=list, description="Noms d'entités IR (models) confirmées dans la spec.")
    missing_entities: list = Field(default_factory=list, description="Entités IR absentes de la spec (drift spec_writer détecté).")
    pages_in_spec: list = Field(default_factory=list, description="Pages IR confirmées dans la spec (URL format).")
    routes_in_spec: list = Field(default_factory=list, description="Routes API IR confirmées dans la spec.")


class ArchitectOutput(BaseModel):
    specification: str = Field(description="The full technical specification in Markdown format.")
    mermaid_diagram: str = Field(description="The complete and valid Mermaid diagram syntax.")
    requirements: list = Field(default_factory=list, description="Flat list of all business requirements extracted from the brief.")
    user_flows: list = Field(default_factory=list, description="List of user interaction flows mapping actions to routes/pages.")
    # IR canonique — source de vérité typée issue du parser déterministe.
    # Coexiste avec requirements: list[str] jusqu'en P4.
    ir_schema: list = Field(default_factory=list, description="Prisma model strings verbatim from parsed_brief.")
    ir_pages: list = Field(default_factory=list, description="Next.js app-router page paths from parsed_brief.")
    ir_routes: list = Field(default_factory=list, description="API route files from parsed_brief.")
    # Dual-output P2 — spec structurée (JSON) en complément du markdown.
    # specification: str reste le contrat garanti (≥500 chars, non-breaking).
    spec_structured: SpecOutput = Field(default_factory=SpecOutput, description="Version JSON structurée de la spec (P2).")

class AgentState(TypedDict):
    messages: Annotated[List, operator.add]
    normalized_brief: str        # Brief Normalizer output (Pré-Sprint 4.6)
    parsed_brief: dict           # Sortie du brief_parser déterministe (source de vérité)
    rag_context: str
    plan: dict
    specification: str
    mermaid_diagram: str
    architect_output: ArchitectOutput
    run_id: str
    stack_id: str
    requirements: list
    user_flows: list
    ir_schema: list              # IR canonique — Prisma models (source: parsed_brief)
    ir_pages: list               # IR canonique — pages (source: parsed_brief)
    ir_routes: list              # IR canonique — API routes (source: parsed_brief)
    spec_structured: dict  # Dual-output P2 — spec JSON sérialisé (construit dans formatter_node, None en initial_state)

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
        # Sections stack-agnostic : ne jamais leur injecter de règles stack
        # brief_normalizer : doit rester 100% domaine métier — les règles Clerk/Prisma/Next.js
        #   pollueraient son output et casseraient son rôle de filtre entités pures.
        # planner : extrait les entités métier (QUOI construire) — les stack rules contiennent
        #   des mappings domaine ("liste" → Task, "blog" → Post) qui se déclenchent sur des mots
        #   présents dans le brief normalisé et causent la dérive documentée.
        #   Le base prompt du planner (architect.md #Planner) a les règles anti-dérive suffisantes.
        _STACK_AGNOSTIC_SECTIONS = {"brief_normalizer", "planner"}

        for title, section_content in sections.items():
            prompt_content = section_content
            if stack_rules and title not in _STACK_AGNOSTIC_SECTIONS:
                prompt_content = (
                    f"{section_content}\n\n---\n\n"
                    "## REGLES STACK OBLIGATOIRES\n\n"
                    f"{stack_rules}"
                )
            prompts[title] = ChatPromptTemplate.from_messages([
                SystemMessage(content=prompt_content),
                HumanMessage(content="{input}")
            ])

        required_sections = {"brief_normalizer", "planner", "spec_writer"}
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
    Depuis Pré-Sprint 4.6 : architect_qdrant_filter a "must": [] (Zone 0 supprimée).
    → tombe directement dans le fallback qdrant_filter (stack + status=active + agent_context=dev).
    L'architect et le DevAgent partagent les mêmes standards Zone 1-14.
    """
    try:
        from agents.stack_config import load_stack_config, get_qdrant_filter_cfg
        from qdrant_client.http.models import Filter, FieldCondition, MatchValue

        def _parse(cond: dict):
            if "key" in cond:
                return FieldCondition(key=cond["key"], match=MatchValue(value=cond["match"]["value"]))
            if "must" in cond:
                return Filter(must=[c for c in (_parse(m) for m in cond["must"]) if c])
            if "should" in cond:
                return Filter(should=[c for c in (_parse(m) for m in cond["should"]) if c])
            return None

        # Priorité 1 : architect_qdrant_filter (agent_context=architect)
        cfg = load_stack_config(stack_id)
        architect_filter_cfg = cfg.get("architect_qdrant_filter", {}).get("filter", {})
        if architect_filter_cfg:
            must_raw = architect_filter_cfg.get("must", [])
            conditions = [c for c in (_parse(m) for m in must_raw) if c]
            if conditions:
                return Filter(must=conditions)

        # Fallback : qdrant_filter général + status=active forcé
        status_condition = FieldCondition(
            key="metadata.status",
            match=MatchValue(value="active"),
        )
        filter_cfg = get_qdrant_filter_cfg(stack_id).get("filter", {})
        must_raw = filter_cfg.get("must", [])
        extra_conditions = [c for c in (_parse(m) for m in must_raw) if c]
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
    # temperature=0.0 : le planner fait de l'extraction/mapping (pas de créativité)
    # 0.4 causait une dérive de domaine documentée (marketplace → Finance/Task)
    _planner_llm_base = ChatOpenAI(model=planner_model, temperature=0.0, max_retries=3)
    if os.getenv("LLM_FALLBACK_ENABLED", "0") == "1":
        llm = _llm_base.with_fallbacks(
            [ChatOpenAI(model="gpt-4o", temperature=0.1, max_retries=1)]
        )
        planner_llm = _planner_llm_base.with_fallbacks(
            [ChatOpenAI(model="gpt-4o-mini", temperature=0.4, max_retries=1)]
        )
    else:
        llm = _llm_base
        planner_llm = _planner_llm_base

    # --- Nodes ---
    async def brief_normalizer_node(state: AgentState):
        """
        Brief Normalizer (refactorisé Pré-Sprint 4.6) — Architecture "Brief as Ground Truth".

        Étape 1 — Parser déterministe (TOUJOURS) :
          Extrait par code les Modèles Prisma, pages, routes API explicitement présents.
          Résultat stocké dans parsed_brief → source de vérité pour requirements[].

        Étape 2 — LLM compléteur de lacunes (SEULEMENT si le brief est vague/partiel) :
          Si le parser a tout trouvé → LLM skippé, normalized_brief construit depuis parser.
          Si le parser a trouvé partiellement → LLM reçoit le parsé + brief pour compléter.
          Si le parser n'a rien trouvé (brief vague) → LLM fait tout le travail.

        Ce design garantit qu'une information explicite dans le brief ne peut jamais
        être perdue, inventée ou altérée par un LLM.
        """
        from agents.brief_parser import (
            parse_brief, requirements_from_parsed,
            build_normalized_brief_from_parsed, describe_parsed
        )

        raw_phrase = state["messages"][-1].content

        # ── Étape 1 : Parser déterministe ────────────────────────────────────
        parsed = parse_brief(raw_phrase)
        logger.info(f"[brief_parser] {describe_parsed(parsed)}")

        # ── Étape 2 : Décision LLM ───────────────────────────────────────────
        is_complete = (
            parsed["has_explicit_models"]
            and parsed["has_explicit_pages"]
            and parsed["has_explicit_routes"]
        )

        if is_complete:
            # Brief explicite : tout est parsé déterministiquement — LLM inutile
            normalized = build_normalized_brief_from_parsed(parsed, raw_phrase)
            logger.info(
                f"[brief_normalizer] Brief complet parsé sans LLM "
                f"({len(parsed['data_models'])} modèles, "
                f"{len(parsed['pages'])} pages, "
                f"{len(parsed['api_routes'])} routes)"
            )
        else:
            # Brief partiel ou vague : LLM complète ce que le parser n'a pas trouvé
            normalizer_llm = ChatOpenAI(model=base_model, temperature=0.0, max_retries=2)
            chain = prompts["brief_normalizer"] | normalizer_llm

            # Si le parser a trouvé quelque chose → l'injecter pour que le LLM
            # ne le réinvente pas (il complète uniquement les lacunes)
            if parsed["has_explicit_models"] or parsed["has_explicit_pages"] or parsed["has_explicit_routes"]:
                pre_parsed_block = "DONNÉES DÉJÀ EXTRAITES (source de vérité — copier verbatim, ne pas modifier) :\n"
                if parsed["data_models"]:
                    pre_parsed_block += "MODÈLES PRISMA :\n" + "\n".join(f"  - {m}" for m in parsed["data_models"]) + "\n"
                if parsed["pages"]:
                    pre_parsed_block += "PAGES :\n" + "\n".join(f"  - {p}" for p in parsed["pages"]) + "\n"
                if parsed["api_routes"]:
                    methods_map = parsed.get("api_methods", {})
                    pre_parsed_block += "ROUTES API :\n" + "\n".join(
                        f"  - {', '.join(methods_map.get(r, []))} → {r}" for r in parsed["api_routes"]
                    ) + "\n"
                pre_parsed_block += "\nBRIEF ORIGINAL :\n" + raw_phrase
                llm_input = pre_parsed_block
                logger.info(f"[brief_normalizer] Brief partiel — LLM complète les lacunes (données parsées injectées)")
            else:
                llm_input = raw_phrase
                logger.info(f"[brief_normalizer] Brief vague — LLM extrait tout")

            try:
                response = await chain.ainvoke({"input": llm_input})
                normalized = response.content.strip()
                if not normalized:
                    normalized = build_normalized_brief_from_parsed(parsed, raw_phrase) if (
                        parsed["has_explicit_models"] or parsed["has_explicit_pages"]
                    ) else raw_phrase
            except Exception as e:
                logger.warning(f"[brief_normalizer] LLM échoué ({e}) — fallback parser/raw")
                normalized = build_normalized_brief_from_parsed(parsed, raw_phrase) if (
                    parsed["has_explicit_models"] or parsed["has_explicit_pages"]
                ) else raw_phrase

        logger.info(f"[brief_normalizer] normalized_brief ({len(normalized)} chars):\n{normalized[:400]}")
        return {"normalized_brief": normalized, "parsed_brief": dict(parsed)}

    async def retrieval_node(state: AgentState):
        # Utilise le brief normalisé comme query RAG — plus fiable que le query rewriting LLM
        normalized_brief = state.get("normalized_brief", "")
        raw_query = state["messages"][-1].content
        rag_query = normalized_brief if normalized_brief else raw_query
        run_id = str(state.get("run_id", ""))
        stack_id = str(state.get("stack_id", _DEFAULT_STACK_ID))
        scored_docs = []  # List[Tuple[Document, float]]

        try:
            qdrant_filter = _build_architect_rag_filter(stack_id)
            if qdrant_filter is not None:
                scored_docs = await vectorstore.asimilarity_search_with_score(rag_query, k=DEFAULT_VECTOR_SEARCH_LIMIT, filter=qdrant_filter)
            else:
                plain_docs = await retriever.ainvoke(rag_query)
                scored_docs = [(d, 0.0) for d in plain_docs]
            # ── Score threshold : exclut les standards peu pertinents ─────────
            before_count = len(scored_docs)
            scored_docs = [(d, s) for d, s in scored_docs if s >= ARCHITECT_RAG_SCORE_THRESHOLD]
            if len(scored_docs) < before_count:
                logger.info(
                    f"[retrieval] Score threshold {ARCHITECT_RAG_SCORE_THRESHOLD}: "
                    f"{before_count} → {len(scored_docs)} standards retenus"
                )
            _append_architect_rag_event(query=rag_query, scored_docs=scored_docs, error=None, run_id=run_id)
        except Exception as e:
            logger.warning(f"RAG indisponible: {e} - continuation sans contexte")
            _append_architect_rag_event(query=rag_query, scored_docs=[], error=str(e), run_id=run_id)
        docs = [d for d, _ in scored_docs]
        rag_context = "\n\n".join([f"--- STANDARD {i+1} ({doc.metadata.get('category', 'général')}) ---\n{doc.page_content}" for i, doc in enumerate(docs)]) if docs else "No relevant standards found."
        logger.info(f"[retrieval] RAG: {len(docs)} standards retenus (query: '{rag_query[:80]}')")
        return {"rag_context": rag_context}
    
    async def planner_node(state: AgentState):
        phrase = state['messages'][-1].content
        stack_id = str(state.get("stack_id", _DEFAULT_STACK_ID))
        normalized_brief = state.get("normalized_brief", "")
        parsed_brief = state.get("parsed_brief", {})

        # ── Planner = domaine pur (QUOI construire) — sans RAG ───────────────
        # Séparation architecturale : planner = brief normalisé + connaissance LLM native.
        #                             spec_writer = plan + RAG (patterns d'implémentation).
        if normalized_brief and normalized_brief != phrase:
            input_text = (
                f"BRIEF NORMALISÉ (source de vérité des entités) :\n"
                f"{normalized_brief}\n\n"
                f"BRIEF ORIGINAL : {phrase}"
            )
        else:
            input_text = f"User Request: {phrase}"

        # Temperature 0.0 : le planner fait de l'extraction (mapping), pas de la créativité.
        # Réduit la dérive de domaine documentée (marketplace → Finance/Task).
        json_planner_llm = planner_llm.bind(response_format={"type": "json_object"})
        chain = prompts['planner'] | json_planner_llm
        llm_response = await chain.ainvoke({"input": input_text})

        match = re.search(r'```json\s*\n(.*?)\n\s*```', llm_response.content, re.DOTALL)
        json_content = match.group(1).strip() if match else llm_response.content.strip()

        try:
            plan = json.loads(json_content)
        except json.JSONDecodeError:
            strict_input = (
                "Return ONLY valid JSON matching this schema keys exactly: "
                "app_type, router_type, stack, description, pages, data_models, auth_required, api_routes, key_features.\n"
                f"BRIEF NORMALISÉ :\n{normalized_brief}\n\n"
                f"User Request: {phrase}\n"
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
        is_generic, reason = _is_generic_plan(plan, normalized_brief if normalized_brief else phrase)
        if is_generic:
            logger.warning(f"[planner] Plan possiblement générique — non bloquant (raison: {reason})")

        # ── Requirements : source de vérité = parser déterministe ────────────
        # Si le parser a extrait des données → requirements depuis le parser (jamais un LLM).
        # Fallback sur le plan LLM uniquement si le brief était 100% vague (parser vide).
        from agents.brief_parser import requirements_from_parsed, user_flows_from_parsed, ParsedBrief
        has_parser_data = (
            parsed_brief.get("has_explicit_models")
            or parsed_brief.get("has_explicit_pages")
            or parsed_brief.get("has_explicit_routes")
        )
        if has_parser_data:
            requirements = requirements_from_parsed(parsed_brief)  # type: ignore[arg-type]
            # user_flows déterministes : mêmes entités/routes que requirements[]
            # Évite la dérive LLM (ex: "POST /api/books" pour un brief Product/Order)
            user_flows = user_flows_from_parsed(parsed_brief)  # type: ignore[arg-type]
            logger.info(
                f"[planner] requirements + user_flows depuis parser déterministe "
                f"({len(requirements)} requirements, {len(user_flows)} flows)"
            )
        else:
            requirements = _extract_requirements_from_plan(plan)
            user_flows = [str(f) for f in plan.get("user_flows", []) if f]
            logger.info(
                f"[planner] brief vague — requirements + user_flows depuis plan LLM "
                f"({len(requirements)} requirements, {len(user_flows)} flows)"
            )
        return {"plan": plan, "requirements": requirements, "user_flows": user_flows}

    async def spec_writer_node(state: AgentState):
        plan_json = json.dumps(state['plan'], indent=2)
        requirements = state.get("requirements", [])
        rag_context = state.get("rag_context", "")

        # RAG injecté ici (spec_writer = COMMENT implémenter) — pas dans le planner
        # Le planner ne voit pas le RAG pour éviter la contamination des noms d'entités.
        input_text = f"High-Level Plan (JSON):\n{plan_json}"
        if rag_context:
            input_text += f"\n\nRAG Context (patterns d'implémentation stack) :\n{rag_context}"

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

        # ── SPEC REQUIREMENTS GATE — observation pure (Pré-Sprint 4.6) ──────────
        # La correction loop (3 appels LLM) est supprimée : elle validait un contrat
        # requirements[] LLM-généré potentiellement faux → amplifiait l'erreur.
        # Avec le Brief Normalizer (Pré-Sprint 4.6), requirements[] sera déterministe
        # et ce gate servira de vérification finale fiable, pas d'un correctif.
        # L'Agent Critique (Sprint 4.6) est le lieu approprié pour la correction.
        try:
            from agents.spec_validator import validate_spec_requirements
            sv_result = validate_spec_requirements(specification, requirements)
            if sv_result["status"] == "DEGRADED":
                logger.warning(
                    f"[spec_writer_node] Spec DEGRADED (observation) — "
                    f"{len(sv_result['unmatched_requirements'])} requirement(s) absents : "
                    f"{sv_result['unmatched_requirements']}"
                )
            else:
                logger.info(
                    f"[spec_writer_node] Spec OK — "
                    f"{sv_result.get('matched_count', '?')}/{sv_result.get('total_mappable', '?')} requirements couverts"
                )
        except Exception as sv_err:
            logger.warning(f"[spec_writer_node] Spec gate non bloquant : {sv_err}")

        return {"specification": specification}

    # diagrammer_node supprimé (Pré-Sprint 4.6) — Sprint 6 dashboard le réintégrera via agent dédié.

    def formatter_node(state: AgentState):
        parsed = state.get('parsed_brief') or {}
        spec_text = state['specification']
        spec_lower = spec_text.lower()

        # ── SpecOutput (P2) — déterministe, zéro LLM ─────────────────────────
        # Résumé : premier paragraphe non-titre
        spec_summary = ""
        for para in spec_text.split('\n\n'):
            stripped = para.strip()
            if stripped and not stripped.startswith('#'):
                spec_summary = stripped[:300]
                break

        # Entités IR vs spec
        models = parsed.get('data_models', [])
        entities_in_spec, missing_entities = [], []
        for model in models:
            name = model.split('{')[0].strip()
            (entities_in_spec if name.lower() in spec_lower else missing_entities).append(name)

        # Pages IR vs spec (format URL)
        from agents.brief_parser import _app_route_to_url
        pages_in_spec = []
        for page in parsed.get('pages', []):
            url = _app_route_to_url(page)
            stripped = url.strip('/')
            if url in spec_text or (stripped and stripped in spec_lower):
                pages_in_spec.append(url)

        # Routes API IR vs spec
        routes_in_spec = []
        from agents.brief_parser import _route_file_to_url
        for route in parsed.get('api_routes', []):
            url = _route_file_to_url(route)
            if url in spec_text:
                routes_in_spec.append(url)

        spec_output = SpecOutput(
            spec_summary=spec_summary,
            entities_in_spec=entities_in_spec,
            missing_entities=missing_entities,
            pages_in_spec=pages_in_spec,
            routes_in_spec=routes_in_spec,
        )
        if missing_entities:
            logger.warning(
                f"[formatter] SpecOutput — {len(missing_entities)} entité(s) IR absentes de la spec : {missing_entities}"
            )

        architect_output = ArchitectOutput(
            specification=spec_text,
            mermaid_diagram=state.get('mermaid_diagram', ''),
            requirements=state.get('requirements', []),
            user_flows=state.get('user_flows', []),
            ir_schema=parsed.get('data_models', []),
            ir_pages=parsed.get('pages', []),
            ir_routes=parsed.get('api_routes', []),
            spec_structured=spec_output,
        )
        return {"architect_output": architect_output}

    # --- Graph Definition ---
    # Pipeline Pré-Sprint 4.6 :
    # brief_normalizer → retrieval → planner → spec_writer → formatter
    #
    # brief_normalizer : zéro RAG, zéro stack — extrait les entités métier du brief brut
    # retrieval        : utilise normalized_brief comme query RAG (plus fiable que query rewriting)
    # planner          : zéro stack rules (stack-agnostic) — reçoit uniquement normalized_brief
    # spec_writer      : reçoit plan + RAG (patterns d'implémentation stack)
    # diagrammer_node  : supprimé (Pré-Sprint 4.6) — réintégré Sprint 6 via agent dédié
    workflow = StateGraph(AgentState)
    workflow.add_node("brief_normalizer", brief_normalizer_node)
    workflow.add_node("retrieval", retrieval_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("spec_writer", spec_writer_node)
    workflow.add_node("formatter", formatter_node)

    workflow.add_edge(START, "brief_normalizer")
    workflow.add_edge("brief_normalizer", "retrieval")
    workflow.add_edge("retrieval", "planner")
    workflow.add_edge("planner", "spec_writer")
    workflow.add_edge("spec_writer", "formatter")
    workflow.add_edge("formatter", END)

    return workflow.compile()
