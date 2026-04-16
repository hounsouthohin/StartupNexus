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
    brief: dict                  # Brief structuré : {"description", "models", "pages", "routes"}
    rag_context: str
    plan: dict
    specification: str
    mermaid_diagram: str
    architect_output: ArchitectOutput
    run_id: str
    stack_id: str
    project_name: str
    requirements: list
    user_flows: list
    spec_structured: dict        # Dual-output P2 — spec JSON sérialisé
    project_spec: dict           # Nouvelle Base — ProjectSpec.model_dump() (Phase 1)

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


def _load_sections_from_personas_dir() -> dict[str, str] | None:
    """
    Charge les sections depuis prompts/base/personas/ (Faille 5 fix — un fichier par persona).
    Retourne None si le dossier ou un fichier obligatoire est absent (fallback sur architect.md).
    """
    project_root = Path(__file__).resolve().parent.parent
    personas_dir = project_root / "prompts" / "base" / "personas"
    if not personas_dir.exists():
        return None

    _PERSONA_FILES = {
        "brief_normalizer": "brief_normalizer.md",
        "planner":          "planner.md",
        "spec_writer":      "spec_writer.md",
        "diagrammer":       "diagrammer.md",
    }
    sections: dict[str, str] = {}
    for key, filename in _PERSONA_FILES.items():
        path = personas_dir / filename
        if not path.exists():
            logger.warning("[load_prompts] persona manquant : %s — fallback monolithique", filename)
            return None
        sections[key] = path.read_text(encoding="utf-8").strip()
    return sections


def load_prompts():
    """
    Charge les prompts architecte + rules stack injectées par section.

    Priorité :
    1. prompts/base/personas/<persona>.md  — un fichier par persona (Faille 5)
    2. prompts/base/architect.md           — fichier monolithique (fallback legacy)
    """
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.messages import SystemMessage, HumanMessage
    try:
        try:
            from agents.shared_tools import get_stack_id
            active_stack = get_stack_id()
        except Exception:
            active_stack = _DEFAULT_STACK_ID

        stack_rules = load_stack_rules_only("architect", active_stack)

        # Préférer les fichiers persona individuels
        sections = _load_sections_from_personas_dir()
        if sections is None:
            logger.info("[load_prompts] personas/ absent ou incomplet — chargement architect.md")
            base_content = load_base_prompt("architect")
            sections = _parse_level1_sections(base_content)

        # brief_normalizer et planner restent stack-agnostic (voir commentaire original)
        _STACK_AGNOSTIC_SECTIONS = {"brief_normalizer", "planner"}

        prompts = {}
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
                f"Sections manquantes : {sorted(missing)}. Trouvées : {sorted(prompts.keys())}"
            )
        return prompts
    except FileNotFoundError:
        raise FileNotFoundError("Prompts architecte introuvables (personas/ et architect.md absents).")
    except Exception as e:
        raise RuntimeError(f"Échec chargement prompts architecte : {e}")

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
    # temperature=0.3 : brise le cache OpenAI (dérive identique kpi-01→09 documentée)
    # + project_name est injecté dans chaque HumanMessage → cache prefix différent par run
    # 0.1 était insuffisant (5 briefs différents → même output Book/Review en session suivante)
    _planner_llm_base = ChatOpenAI(model=planner_model, temperature=0.3, max_retries=3)
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

    async def retrieval_node(state: AgentState):
        # Utilise la description du brief comme query RAG
        brief = state.get("brief", {})
        rag_query = str(brief.get("description", "")) or state["messages"][-1].content
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
        """
        Planner — construit ProjectSpec directement depuis state["brief"] structuré.

        Le brief est un dict avec : description, models[], pages[], routes[].
        Aucun parsing regex — les données sont déjà structurées à l'entrée.
        Si le brief est incomplet ou absent, instructor + LLM produit le ProjectSpec.
        """
        stack_id = str(state.get("stack_id", _DEFAULT_STACK_ID))
        project_name = state.get("project_name", "")
        brief = state.get("brief", {})

        from agents.project_spec import ProjectSpec, PrismaModel, PrismaField, ApiRoute, AppPage

        def _split_fields(raw: str) -> list[str]:
            """Découpe les champs Prisma en respectant les virgules dans les parenthèses/crochets.
            Ex: '@default(uuid()), title String' → ['@default(uuid())', ' title String']
            Sans ça, '@relation(fields: [boardId], references: [id])' serait splitté en 2 tokens."""
            parts, current, depth = [], [], 0
            for ch in raw:
                if ch in "([":
                    depth += 1
                elif ch in ")]":
                    depth -= 1
                if ch == "," and depth == 0:
                    parts.append("".join(current))
                    current = []
                else:
                    current.append(ch)
            if current:
                parts.append("".join(current))
            return parts

        def _parse_model_str(model_str: str) -> PrismaModel:
            """Convertit une string Prisma DSL 'Name { field Type attrs, ... }' en PrismaModel."""
            blocks = re.findall(r'(\w+)\s*\{([^}]*)\}', model_str)
            if blocks:
                name, raw_fields = blocks[0]
                fields: list[PrismaField] = []
                for line in _split_fields(raw_fields.strip()):
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split()
                    if len(parts) >= 2:
                        fname, ftype = parts[0], parts[1]
                        fattrs = " ".join(parts[2:]) if len(parts) > 2 else ""
                        fields.append(PrismaField(name=fname, type=ftype, attributes=fattrs))
                if not fields:
                    fields = [PrismaField(name="id", type="String", attributes="@id @default(uuid())")]
                return PrismaModel(name=name.strip(), fields=fields)
            # Fallback : juste un nom sans champs
            name = (model_str or "").strip().split()[0] or "Model"
            return PrismaModel(
                name=name,
                fields=[PrismaField(name="id", type="String", attributes="@id @default(uuid())")],
            )

        # ── Chemin 1 : brief structuré → ProjectSpec déterministe (zéro LLM) ──
        brief_models = brief.get("models", [])
        brief_pages = brief.get("pages", [])
        brief_routes = brief.get("routes", [])

        if brief_models or brief_pages or brief_routes:
            models: list[PrismaModel] = []
            seen_names: set[str] = set()
            for mdl_str in brief_models:
                m = _parse_model_str(str(mdl_str))
                if m.name not in seen_names:
                    models.append(m)
                    seen_names.add(m.name)

            pages: list[AppPage] = []
            seen_paths: set[str] = set()
            for pg in brief_pages:
                if isinstance(pg, dict):
                    path = str(pg.get("path", "/"))
                    auth = bool(pg.get("auth", True))
                else:
                    path, auth = str(pg), True
                if path not in seen_paths:
                    pages.append(AppPage(path=path, auth_required=auth))
                    seen_paths.add(path)
            if not any(pg.path == "/" for pg in pages):
                pages.insert(0, AppPage(path="/", auth_required=False))
                logger.info("[planner] page '/' ajoutée automatiquement (requis Next.js — absent du brief)")

            routes: list[ApiRoute] = []
            seen_routes: set[str] = set()
            for rt in brief_routes:
                if isinstance(rt, dict):
                    method = str(rt.get("method", "GET")).upper()
                    path = str(rt.get("path", "/api/resource"))
                    key = f"{method}:{path}"
                    if key not in seen_routes and method in ("GET", "POST", "PUT", "PATCH", "DELETE"):
                        routes.append(ApiRoute(method=method, path=path))  # type: ignore[arg-type]
                        seen_routes.add(key)

            user_flows = (
                [f"L'utilisateur crée via {r.method} {r.path}" for r in routes]
                + [f"L'utilisateur visite {p.path}" for p in pages]
            )

            spec = ProjectSpec(
                project_name=project_name,
                stack_id=stack_id,
                models=models,
                routes=routes,
                pages=pages,
                user_flows=user_flows,
            ).with_fingerprint()

            logger.info(
                f"[planner] ProjectSpec déterministe — "
                f"{len(models)} modèles, {len(pages)} pages, {len(routes)} routes "
                f"| fingerprint={spec.spec_fingerprint}"
            )

        else:
            # Brief non structuré — les opérateurs sont responsables de fournir
            # models/pages/routes dans le brief avant de soumettre à la factory.
            # Chemin 2 (instructor + LLM) supprimé : source de spécifications incomplètes
            # (ex: task-manager → seulement PATCH+DELETE au lieu du CRUD complet).
            missing = []
            if not brief_models:  missing.append("models")
            if not brief_pages:   missing.append("pages")
            if not brief_routes:  missing.append("routes")
            logger.error(
                "[planner] Brief non structuré reçu — champs manquants : %s. "
                "Fournir un brief avec models[], pages[] et routes[] explicites.",
                missing,
            )
            raise ApplicationError(
                f"Brief insuffisant : {missing} absents. "
                "Structurer le brief (models/pages/routes) avant de soumettre à la factory.",
                non_retryable=True,
            )

        # ── RAG budget (Phase 5 Codex — appliqué ici aussi pour cohérence) ───
        # Le rag_context est déjà calculé dans retrieval_node (max 3 docs, max 600 chars/doc).

        # ── Compatibilité descendante : architect_output pour architect_activity ─
        spec_summary = (
            f"Projet {project_name} | Stack {stack_id}\n"
            f"Modèles : {', '.join(m.name for m in spec.models)}\n"
            f"Pages : {', '.join(p.path for p in spec.pages)}\n"
            f"Routes : {', '.join(r.method + ' ' + r.path for r in spec.routes)}"
        )
        architect_output = ArchitectOutput(
            specification=spec_summary,
            mermaid_diagram="",
            requirements=spec.to_requirements(),
            user_flows=spec.user_flows,
            ir_schema=[m.name for m in spec.models],
            ir_pages=[p.path for p in spec.pages],
            ir_routes=[f"{r.method} {r.path}" for r in spec.routes],
            spec_structured=SpecOutput(),
        )

        return {
            "plan": spec.model_dump(),
            "requirements": spec.to_requirements(),
            "user_flows": spec.user_flows,
            "project_spec": spec.model_dump(),
            "architect_output": architect_output,
        }

    async def spec_writer_node(state: AgentState):
        plan_json = json.dumps(state['plan'], indent=2)
        requirements = state.get("requirements", [])
        rag_context = state.get("rag_context", "")

        # Requirements en PREMIER — source de vérité du brief.
        # Ordre intentionnel : requirements → plan JSON → RAG.
        # Avant (bug) : plan JSON en tête → LLM suivait le plan et ignorait les requirements en bas.
        # Correction : requirements en tête → LLM les traite comme contrainte prioritaire.
        if requirements:
            reqs_block = "\n".join(f"  - {r}" for r in requirements)
            input_text = (
                f"REQUIREMENTS OBLIGATOIRES — source de vérité du brief (TOUS doivent apparaître dans la spec) :\n"
                f"{reqs_block}\n"
                f"Règle absolue : utilise le NOM EXACT de chaque modèle/route (pas de synonyme, pas de traduction). "
                f"Chaque modèle Prisma DOIT figurer dans ## Schéma Prisma avec ses champs.\n\n"
                f"High-Level Plan (JSON):\n{plan_json}"
            )
        else:
            input_text = f"High-Level Plan (JSON):\n{plan_json}"

        # RAG injecté après le plan — contexte d'implémentation stack (COMMENT implémenter)
        if rag_context:
            input_text += f"\n\nRAG Context (patterns d'implémentation stack) :\n{rag_context}"
        
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
        # formatter_node hors-graphe — conservé pour compatibilité imports tests uniquement.
        # Le planner_node produit directement architect_output depuis le brief structuré.
        spec_text = state.get('specification', '')
        spec_lower = spec_text.lower()

        # ── SpecOutput depuis project_spec (plus de parsed_brief / brief_parser) ─
        project_spec = state.get('project_spec') or {}
        models_raw = project_spec.get('models', [])
        pages_raw = project_spec.get('pages', [])
        routes_raw = project_spec.get('routes', [])

        spec_summary = ""
        for para in spec_text.split('\n\n'):
            stripped = para.strip()
            if stripped and not stripped.startswith('#'):
                spec_summary = stripped[:300]
                break

        entities_in_spec, missing_entities = [], []
        for m in models_raw:
            name = m.get('name', '') if isinstance(m, dict) else str(m).split()[0]
            (entities_in_spec if name.lower() in spec_lower else missing_entities).append(name)

        pages_in_spec = []
        for pg in pages_raw:
            url = pg.get('path', '') if isinstance(pg, dict) else str(pg)
            stripped = url.strip('/')
            if url in spec_text or (stripped and stripped in spec_lower):
                pages_in_spec.append(url)

        routes_in_spec = []
        for rt in routes_raw:
            if isinstance(rt, dict):
                url = rt.get('path', '')
            else:
                url = str(rt)
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
                f"[formatter] SpecOutput — {len(missing_entities)} entité(s) absentes de la spec : {missing_entities}"
            )

        architect_output = ArchitectOutput(
            specification=spec_text,
            mermaid_diagram=state.get('mermaid_diagram', ''),
            requirements=state.get('requirements', []),
            user_flows=state.get('user_flows', []),
            ir_schema=[m.get('name', '') if isinstance(m, dict) else str(m) for m in models_raw],
            ir_pages=[p.get('path', '') if isinstance(p, dict) else str(p) for p in pages_raw],
            ir_routes=[f"{r.get('method','')} {r.get('path','')}" if isinstance(r, dict) else str(r) for r in routes_raw],
            spec_structured=spec_output,
        )
        return {"architect_output": architect_output}

    # --- Graph Definition ---
    # Pipeline (Phase 2 — 28 Mars 2026) :
    # retrieval → planner
    #
    # retrieval : RAG Qdrant (max 3 docs, budgeté)
    # planner   : lit state["brief"] structuré → ProjectSpec déterministe (zéro LLM si brief complet)
    #
    # Supprimés : brief_normalizer (brief_parser éliminé), spec_writer_node, formatter_node (hors-graphe)
    workflow = StateGraph(AgentState)
    workflow.add_node("retrieval", retrieval_node)
    workflow.add_node("planner", planner_node)

    workflow.add_edge(START, "retrieval")
    workflow.add_edge("retrieval", "planner")
    workflow.add_edge("planner", END)

    return workflow.compile()
