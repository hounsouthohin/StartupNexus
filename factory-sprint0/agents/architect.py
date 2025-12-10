# agents/architect.py
# ===============================================
# ARCHITECTE LOGICIEL IA - RAG Réel sur factory_standards (Qdrant Docker)
# Version finale – compatible avec ton init existant
# ===============================================

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from typing import TypedDict, Annotated, List
import operator
import os
from dotenv import load_dotenv

load_dotenv(override=True)

# ==================== ÉTAT ====================
class AgentState(TypedDict):
    messages: Annotated[List, operator.add]
    rag_context: str

# ==================== PROMPT ====================
prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content="""
Tu es l'Architecte Logiciel Senior de Factory Nexus, une startup 100% composée d'agents IA.

TU DOIS IMPÉRATIVEMENT t'appuyer sur le contexte RAG fourni (issu de la base factory_standards) 
pour toutes tes décisions d'architecture, choix technos, structure, sécurité et UI/UX.

Raisonne étape par étape, puis produis :
1. Une spécification technique complète en Markdown
2. Un diagramme d'architecture en Mermaid (syntaxe valide, lisible)

Respecte scrupuleusement les standards internes.
"""),
    MessagesPlaceholder(variable_name="messages"),
])

# ==================== OUTIL MERMAID ====================
@tool
def generate_mermaid_diagram(description: str) -> str:
    """Génère un diagramme Mermaid précis basé sur les standards factory."""
    return """
graph TD
    subgraph Frontend[Frontend - Next.js 15 App Router]
        A[Client Browser] --> B[Next.js Pages & Server Components]
        B --> C[shadcn/ui + Tailwind CSS]
    end
    subgraph Backend[Backend]
        D[API Routes / Route Handlers] --> E[Auth Middleware<br>Clerk ou NextAuth v5]
        E --> F[Prisma ORM]
        F --> G[PostgreSQL]
    end
    A -->|HTTPS + JWT httpOnly| D
    style Frontend fill:#e0f2fe
    style Backend fill:#f0e6fe
"""

tools = [generate_mermaid_diagram]

# ==================== CRÉATION DU GRAPH (lazy) ====================
def create_architect_agent():
    # Embeddings identiques à ton script d'init
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

    # Connexion Qdrant (exactement comme ton Docker)
    client = QdrantClient(url="http://localhost:6333")  # même host que ton script

    # VectorStore sur collection EXISTANTE (pas de recreate)
    vectorstore = QdrantVectorStore(
        client=client,
        collection_name="factory_standards",
        embedding=embeddings,
    )

    # Retriever : top 6 documents les plus pertinents
    retriever = vectorstore.as_retriever(search_kwargs={"k": 6})

    llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
    llm_with_tools = llm.bind_tools(tools)

    # ==================== NŒUDS ====================
    async def retrieval_node(state: AgentState):
        query = state["messages"][-1].content
        docs = await retriever.ainvoke(query)
        
        if not docs:
            rag_context = "Aucun standard pertinent trouvé dans factory_standards pour cette requête."
        else:
            rag_context = "\n\n".join([
                f"--- Standard {i+1} ---\n{doc.page_content}\n(Source: {doc.metadata.get('category', 'inconnu')})"
                for i, doc in enumerate(docs)
            ])
        
        return {"rag_context": rag_context}

    async def architect_agent_node(state: AgentState):
        messages = state["messages"]
        if state.get("rag_context"):
            messages = messages + [
                HumanMessage(content=f"Contexte RAG obligatoire (factory_standards) :\n{state['rag_context']}")
            ]
        
        chain = prompt | llm_with_tools
        result = await chain.ainvoke({"messages": messages})
        return {"messages": [result]}

    # Graph
    workflow = StateGraph(AgentState)
    workflow.add_node("retrieval", retrieval_node)
    workflow.add_node("architect_agent", architect_agent_node)
    workflow.add_node("tools", ToolNode(tools))

    workflow.add_edge(START, "retrieval")
    workflow.add_edge("retrieval", "architect_agent")
    workflow.add_conditional_edges("architect_agent", tools_condition, {"tools": "tools", END: END})
    workflow.add_edge("tools", "architect_agent")

    return workflow.compile()