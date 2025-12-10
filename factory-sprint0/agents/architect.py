from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import os
from dotenv import load_dotenv

load_dotenv()

# Charge ta clé (mets-la dans .env à la racine plus tard)
# os.environ["OPENAI_API_KEY"] = "sk-..."  # ← REMPLACE PAR TA CLÉ

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("La clé API OpenAI n'est pas configurée. Définissez la variable d'environnement OPENAI_API_KEY dans votre fichier .env.")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=api_key)  # gpt-4o-mini pour vitesse/coût en dev

# Prompt système de l'Agent Architecte
ARCHITECT_SYSTEM_PROMPT = """
Tu es l'Agent Architecte de la Software Agent Factory, une usine 100% autonome d'agents AI.
Ta mission : analyser une phrase humaine et produire des spécifications techniques complètes et professionnelles.

Pour toute demande, réponds EXACTEMENT dans ce format (rien d'autre) :

--- SPEC.md ---
[Ton SPEC.md complet ici : 
- Description du projet
- Fonctionnalités principales (liste)
- Stack technique recommandée (frontend, backend, DB, auth...)
- Modèle de données (entités et relations)
- Routes API principales
- Sécurité et bonnes pratiques]
--- FIN SPEC ---

--- DIAGRAMME MERMAID ---
```mermaid
graph TD
    [Ton diagramme d'architecture clair ici]

--- FIN DIAGRAMME ---
"""

class AgentState(dict):
    messages: list
    spec_md: str
    mermaid: str

async def architect_node(state):
    messages = [HumanMessage(content=ARCHITECT_SYSTEM_PROMPT)] + state["messages"]
    response = await llm.ainvoke(messages)
    return {
    "messages": state["messages"] + [response],
    "spec_md": response.content,
    "mermaid": response.content  # on extraira plus tard
    }
    
##Construction du graphe (un seul nœud pour l'instant)
graph = StateGraph(AgentState)
graph.add_node("architecte", architect_node)
graph.set_entry_point("architecte")
graph.add_edge("architecte", END)
architect_agent = graph.compile()