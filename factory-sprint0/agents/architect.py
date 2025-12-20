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
import json # Added for parsing LLM output
from dotenv import load_dotenv

load_dotenv(override=True)

class AgentState(TypedDict):
    messages: Annotated[List, operator.add]
    rag_context: str
    architect_output: dict # New field for structured output

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

Output UNIQUEMENT un JSON valide : { 'specification': 'texte Markdown complet de la spec', 'mermaid_diagram': 'code Mermaid valide (classDiagram ou flowChart) entre ```mermaid et ```' }. Pas de texte supplémentaire.
"""),   
    MessagesPlaceholder(variable_name="messages"),
])

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
        
        chain = prompt | llm
        llm_response = await chain.ainvoke({"messages": messages})
        
        # Try to parse the LLM's content as JSON
        try:
            # The response can be enclosed in ```json ... ```, let's strip that.
            clean_response = llm_response.content.strip()
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:-3].strip()

            json_output = json.loads(clean_response)
            # Store the structured output and also keep the message in state
            return {"messages": [llm_response], "architect_output": json_output}
        except json.JSONDecodeError:
            # Handle cases where LLM doesn't output valid JSON
            error_message = "LLM did not produce valid JSON output. Raw response: " + llm_response.content
            # Store an error in architect_output and the raw response in messages
            return {"messages": [llm_response, HumanMessage(content=error_message)], "architect_output": {"error": error_message}}

    workflow = StateGraph(AgentState)
    workflow.add_node("retrieval", retrieval_node)
    workflow.add_node("architect_agent", architect_agent_node)

    workflow.add_edge(START, "retrieval")
    workflow.add_edge("retrieval", "architect_agent")
    workflow.add_edge("architect_agent", END)

    return workflow.compile()