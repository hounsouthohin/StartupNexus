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
import operator
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage
from config.factory_config import QDRANT_URL, QDRANT_COLLECTION_NAME, EMBEDDING_MODEL
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


def _append_architect_rag_event(query: str, docs: list, error: str | None = None, run_id: str = "") -> None:
    try:
        metrics_dir = Path("logs/metrics")
        metrics_dir.mkdir(parents=True, exist_ok=True)
        path = metrics_dir / "rag_usage.jsonl"
        doc_ids = [str(getattr(doc, "id", "")) for doc in (docs or [])]
        scores = [float(getattr(doc, "score", 0.0) or 0.0) for doc in (docs or [])]
        snippet = str(getattr(docs[0], "page_content", ""))[:180] if docs else ""
        event = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "agent": "architect_retrieval",
            "query": query,
            "k": 10,
            "cache_hit": False,
            "result_count": len(docs or []),
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

class AgentState(TypedDict):
    messages: Annotated[List, operator.add]
    rag_context: str
    plan: dict
    specification: str
    mermaid_diagram: str
    architect_output: ArchitectOutput 

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
    retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)

    # --- Nodes ---
    async def retrieval_node(state: AgentState):
        query = state["messages"][-1].content
        try:
            docs = await retriever.ainvoke(query)
            _append_architect_rag_event(query=query, docs=docs, error=None, run_id=str(state.get("run_id", "")))
        except Exception as e:
            logger.warning(f"RAG indisponible: {e} - continuation sans contexte")
            docs = []
            _append_architect_rag_event(query=query, docs=[], error=str(e), run_id=str(state.get("run_id", "")))
        rag_context = "\n\n".join([f"--- STANDARD {i+1} ({doc.metadata.get('category', 'général')}) ---\n{doc.page_content}" for i, doc in enumerate(docs)]) if docs else "No relevant standards found."
        print(f"RAG Context for Planner:\n{rag_context}\n--- END RAG CONTEXT ---")
        return {"rag_context": rag_context}
    async def planner_node(state: AgentState):
        input_text = f"User Request: {state['messages'][-1].content}\n\nRAG Context:\n{state['rag_context']}"
        chain = prompts['planner'] | llm
        llm_response = await chain.ainvoke({"input": input_text})
        
        match = re.search(r'```json\s*\n(.*?)\n\s*```', llm_response.content, re.DOTALL)
        json_content = match.group(1).strip() if match else llm_response.content.strip()

        try:
            plan = json.loads(json_content)
            return {"plan": plan}
        except json.JSONDecodeError as e:
            raise ValueError(f"Planner failed to produce a valid JSON plan. Raw LLM response: {llm_response.content}. Error: {e}")

    async def spec_writer_node(state: AgentState):
        original_request = state["messages"][0].content
        plan_json = json.dumps(state['plan'], indent=2)
        
        input_text = (
            f"Original User Request: \"{original_request}\"\n\n"
            f"High-Level Plan (JSON):\n{plan_json}"
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

        required_keywords = ["next.js", "clerk", "prisma"]
        forbidden_keywords = [
            "oauth 2.0",
            "oauth2",
            "express.js",
            "flask",
            "mongodb",
            "angular",
            "react.js or",
            "microservices",
        ]
        required_sections = [
            "## vue d'ensemble",
            "## stack technique",
            "## structure des pages",
            "## schéma prisma",
            "## authentification clerk",
            "## api routes",
            "## composants tailwind",
        ]

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
            mermaid_diagram=state['mermaid_diagram']
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


