# agents/architect.py
# ===============================================
# ARCHITECTE LOGICIEL IA - Refactored for Chained Prompts (décembre 2025)
# ===============================================

import os
import json
import re
import subprocess
import tempfile
from typing import List, TypedDict, Annotated
import operator
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv(override=True)

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
        current_dir = os.path.dirname(os.path.abspath(__file__))
        prompts_path = os.path.join(current_dir, '..', 'prompts', 'architect.md')
        with open(prompts_path, "r", encoding='utf-8') as f:
            content = f.read()
        
        prompts = {}
        # Find all sections starting with a '#' heading
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
    
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    client = QdrantClient(url="http://qdrant:6333")
    vectorstore = QdrantVectorStore(client=client, collection_name="factory_standards", embedding=embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
    llm = ChatOpenAI(model="gpt-4o", temperature=0.1)

    # --- Nodes ---
    async def retrieval_node(state: AgentState):
        query = state["messages"][-1].content
        docs = await retriever.ainvoke(query)
        rag_context = "\n\n".join([f"--- STANDARD {i+1} ({doc.metadata.get('category', 'général')}) ---\n{doc.page_content}" for i, doc in enumerate(docs)]) if docs else "No relevant standards found."
        print(f"RAG Context for Planner:\n{rag_context}\n--- END RAG CONTEXT ---")
        return {"rag_context": rag_context}

    async def planner_node(state: AgentState):
        input_text = f"User Request: {state['messages'][-1].content}\n\nRAG Context:\n{state['rag_context']}"
        chain = prompts['planner'] | llm
        llm_response = await chain.ainvoke({"input": input_text})
        
        # Robustly extract JSON from LLM response
        match = re.search(r'```json\s*\n(.*?)\n\s*```', llm_response.content, re.DOTALL)
        json_content = match.group(1).strip() if match else llm_response.content.strip()

        try:
            plan = json.loads(json_content)
            return {"plan": plan}
        except json.JSONDecodeError as e:
            raise ValueError(f"Planner failed to produce a valid JSON plan. Raw LLM response: {llm_response.content}. Error: {e}")

    async def spec_writer_node(state: AgentState):
        # Provide more context to the LLM by including the original request
        original_request = state["messages"][0].content
        plan_json = json.dumps(state['plan'], indent=2)
        
        input_text = (
            f"Original User Request: \"{original_request}\"\n\n"
            f"High-Level Plan (JSON):\n{plan_json}"
        )
        
        chain = prompts['spec_writer'] | llm
        llm_response = await chain.ainvoke({"input": input_text})
        return {"specification": llm_response.content}

    async def diagrammer_node(state: AgentState):
        from langchain_core.messages import HumanMessage
        
        max_attempts = 3
        attempts = 0
        input_text = f"Technical Specification:\n{state['specification']}"
        
        while attempts < max_attempts:
            attempts += 1
            chain = prompts['diagrammer'] | llm
            llm_response = await chain.ainvoke({"input": input_text})
            
            match = re.search(r'```(?:mermaid)?\s*\n(.*?)\n\s*```', llm_response.content, re.DOTALL)
            mermaid_code = match.group(1).strip() if match else llm_response.content.strip()

            # Validate the Mermaid syntax using minlag/mermaid-cli Docker image
            try:
                # Force tempfile to create in /tmp so it's accessible by the Docker volume mount
                with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.mmd', dir='/tmp') as tmp_file:
                    tmp_file.write(mermaid_code)
                    tmp_file_path = tmp_file.name
                
                input_filename = os.path.basename(tmp_file_path)
                output_filename = f"{input_filename}.png"

                host_dir = '/tmp' # Add this line

                container_input_path = f"/data/{input_filename}"
                container_output_path = f"/data/{output_filename}"

                subprocess.run(
                    [
                        'docker', 'run', '--rm',
                        '--user', f"{os.getuid()}:{os.getgid()}",
                        '-v', f"{host_dir}:/data",
                        'minlag/mermaid-cli:latest',
                        '-i', f"/data/{input_filename}",
                        '-o', f"/data/{output_filename}"
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                # If validation is successful, clean up and return
                os.remove(tmp_file_path)
                os.remove(os.path.join('/tmp', output_filename)) # Output file is also in /tmp now
                return {"mermaid_diagram": mermaid_code}

            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                # Ensure temp file is cleaned up on error
                if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
                    os.remove(tmp_file_path)
                
                error_message = f"Mermaid syntax validation failed (Attempt {attempts}/{max_attempts}). Error: {e.stderr or e.stdout}"
                print(error_message) # Or use a proper logger
                if attempts >= max_attempts:
                    raise ValueError(f"Failed to generate a valid Mermaid diagram after {max_attempts} attempts. Last error: {error_message}")
                
                # Prepare for retry
                input_text += f"\n\nPrevious attempt failed. The generated diagram was invalid. Please correct the syntax based on this error: {error_message}"
                # The HumanMessage here simulates the ReAct feedback loop for the LLM
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
