# agents/architect.py
# ===============================================
# ARCHITECTE LOGICIEL IA - Version blindée conformité standards (décembre 2025)
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

class AgentState(TypedDict):
    messages: Annotated[List, operator.add]
    rag_context: str

# ==================== PROMPT SYSTÈME BLINDÉ (la clé de la conformité) ====================
prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content="""
Tu es l'Architecte Logiciel Senior de Factory Nexus, startup 100% agents IA.

RÈGLES ABSOLUES ET NON NÉGOCIABLES :
- Tu DOIS baser TOUTES tes décisions exclusivement sur le contexte RAG fourni (collection factory_standards).
- Toute technologie, pattern ou pratique ABSENTE du contexte RAG est STRICTEMENT INTERDITE.
- Tu cites systématiquement les standards pertinents avec leur catégorie.

PILIERS IMMUABLES DE FACTORY NEXUS :
• Frontend full-stack : Next.js 15+ App Router uniquement
• UI/UX : shadcn/ui + Tailwind CSS obligatoire
• Authentification : Clerk ou NextAuth v5 (version App Router)
• ORM : Prisma avec PostgreSQL
• Sécurité : JWT httpOnly cookies, refresh tokens, middleware auth Next.js
• Structure : dossiers app/, components/, lib/, actions/, types/

LIVRABLES OBLIGATOIRES (à produire À CHAQUE FOIS, quelle que soit la requête) :
1. Une spécification technique complète et détaillée au format Markdown, incluant :
   - Description des pages/routes
   - Composants UI principaux (shadcn/ui)
   - Flux d'authentification
   - Schema Prisma
   - Mesures de sécurité
2. Un diagramme d'architecture professionnel en syntaxe Mermaid valide, incluant :
   - subgraphs Frontend et Backend/Database
   - flux HTTPS + JWT httpOnly
   - Server Components, Server Actions, middleware auth

Tu raisonnes étape par étape en citant les standards, PUIS tu fournis les deux livrables complets.
Tu NE TERMINE JAMAIS ta réponse avant d'avoir fourni la spécification Markdown complète ET le diagramme Mermaid.
Toute réponse incomplète = échec de mission.
"""),
    MessagesPlaceholder(variable_name="messages"),
])
# ==================== OUTIL MERMAID AMÉLIORÉ ====================
@tool
def generate_mermaid_diagram(description: str) -> str:
    """Génère un diagramme Mermaid conforme aux standards Factory Nexus."""
    return """
graph TD
    subgraph Frontend[Frontend - Next.js 15 App Router]
        A[Client Browser] --> B[Server Components + Client Components]
        B --> C[shadcn/ui + Tailwind CSS]
        C --> D[Server Actions / Route Handlers]
    end
    subgraph Backend[Backend - Prisma + PostgreSQL]
        E[Next.js Middleware] --> F[Auth Check<br>Clerk ou NextAuth v5]
        F --> G[Prisma ORM]
        G --> H[PostgreSQL<br>Row Level Security]
    end
    A -->|HTTPS + JWT httpOnly| E
    style Frontend fill:#dbeafe
    style Backend fill:#fce7f3
"""

tools = [generate_mermaid_diagram]

# ==================== CRÉATION DU GRAPH ====================
def create_architect_agent():
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    client = QdrantClient(url="http://localhost:6333")

    vectorstore = QdrantVectorStore(
        client=client,
        collection_name="factory_standards",
        embedding=embeddings,
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": 10})  # Plus de docs pour plus de poids

    llm = ChatOpenAI(model="gpt-4o", temperature=0.1)  # Température plus basse = plus déterministe
    llm_with_tools = llm.bind_tools(tools)

    async def retrieval_node(state: AgentState):
        query = state["messages"][-1].content
        docs = await retriever.ainvoke(query)
        
        if not docs:
            rag_context = "ATTENTION : Aucun standard pertinent trouvé. Refuse toute génération hors standards connus."
        else:
            rag_context = "\n\n".join([
                f"--- STANDARD OBLIGATOIRE {i+1} ({doc.metadata.get('category', 'général')}) ---\n{doc.page_content}"
                for i, doc in enumerate(docs)
            ])
        
        return {"rag_context": rag_context}

    async def architect_agent_node(state: AgentState):
        messages = state["messages"]
        if state.get("rag_context"):
            messages = messages + [
                HumanMessage(content=f"CONTEXTE RAG OBLIGATOIRE À RESPECTER IMPÉRATIVEMENT :\n{state['rag_context']}")
            ]
        
        chain = prompt | llm_with_tools
        result = await chain.ainvoke({"messages": messages})
        return {"messages": [result]}

    workflow = StateGraph(AgentState)
    workflow.add_node("retrieval", retrieval_node)
    workflow.add_node("architect_agent", architect_agent_node)
    workflow.add_node("tools", ToolNode(tools))

    workflow.add_edge(START, "retrieval")
    workflow.add_edge("retrieval", "architect_agent")
    workflow.add_conditional_edges("architect_agent", tools_condition, {"tools": "tools", END: END})
    workflow.add_edge("tools", "architect_agent")

    return workflow.compile()