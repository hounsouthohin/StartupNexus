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
from datetime import datetime
from typing import List, TypedDict, Annotated
import operator
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage
from config.factory_config import QDRANT_URL, QDRANT_COLLECTION_NAME, EMBEDDING_MODEL
from utils.prompt_loader import load_prompt

load_dotenv(override=True)
logger = logging.getLogger(__name__)

FORBIDDEN_AUTH_PATTERNS = [
    r"\bbcrypt\b",
    r"\bjwt\b",
    r"\bnextauth\b",
    r"\bnext-auth\b",
    r"\bpassword_hash\b",
    r"\bhashed_password\b",
    r"/api/auth/",
]


def _contains_forbidden_auth(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in FORBIDDEN_AUTH_PATTERNS)


def _append_architect_rag_event(query: str, docs: list, error: str | None = None) -> None:
    try:
        metrics_dir = Path("logs/metrics")
        metrics_dir.mkdir(parents=True, exist_ok=True)
        path = metrics_dir / "rag_usage.jsonl"
        payload_docs = []
        for idx, doc in enumerate(docs or [], start=1):
            metadata = getattr(doc, "metadata", {}) or {}
            payload_docs.append(
                {
                    "rank": idx,
                    "category": metadata.get("category"),
                    "source": metadata.get("source"),
                    "tech": metadata.get("tech"),
                    "snippet": str(getattr(doc, "page_content", ""))[:180],
                }
            )
        event = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "agent": "architect_retrieval",
            "query": query,
            "k": 10,
            "cache_hit": False,
            "result_count": len(payload_docs),
            "docs": payload_docs,
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
def load_prompts():
    """Reads and parses the architect.md file to get prompts for each node."""
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.messages import SystemMessage, HumanMessage
    try:
        content = load_prompt("architect")
        
        prompts = {}
        pattern = r'#\s*(.*?)\n(.*?)(?=\n#\s*|\Z)'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for match in matches:
            title = match[0].strip().lower().replace(' ', '_')
            prompt_content = match[1].strip()
            prompts[title] = ChatPromptTemplate.from_messages([
                SystemMessage(content=prompt_content),
                HumanMessage(content="{input}")
            ])
        return prompts
    except FileNotFoundError:
        raise FileNotFoundError("prompts/architect.md not found.")
    except Exception as e:
        raise RuntimeError(f"Failed to parse prompts/architect.md: {e}")

# ==================== CRÉATION DU GRAPH ====================
def create_architect_agent():
    # Imports moved inside the function to avoid Temporal sandbox issues
    from langgraph.graph import StateGraph, START, END
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    from langchain_qdrant import QdrantVectorStore
    from qdrant_client import QdrantClient

    prompts = load_prompts()
    
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    client = QdrantClient(url=QDRANT_URL)
    vectorstore = QdrantVectorStore(client=client, collection_name=QDRANT_COLLECTION_NAME, embedding=embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
    llm = ChatOpenAI(model="gpt-4o", temperature=0.1)

    # --- Nodes ---
    async def retrieval_node(state: AgentState):
        query = state["messages"][-1].content
        try:
            docs = await retriever.ainvoke(query)
            _append_architect_rag_event(query=query, docs=docs, error=None)
        except Exception as e:
            logger.warning(f"RAG indisponible: {e} - continuation sans contexte")
            docs = []
            _append_architect_rag_event(query=query, docs=[], error=str(e))
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

        if _contains_forbidden_auth(specification):
            logger.warning("Spec contains forbidden auth terms. Forcing one rewrite with strict Clerk constraints.")
            harden_input = (
                input_text
                + "\n\nMANDATORY REWRITE:\n"
                  "- Replace any JWT/bcrypt/NextAuth/password-based auth with Clerk-only auth.\n"
                  "- Prisma schema must not contain password or password_hash fields.\n"
                  "- Keep PostgreSQL + Prisma and Next.js architecture.\n"
                  "- Return only corrected markdown."
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


