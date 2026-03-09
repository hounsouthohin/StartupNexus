import os
from typing import TypedDict, Annotated, List
import operator
from dotenv import load_dotenv

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from utils.prompt_loader import load_prompt, load_stack_prompt
from agents.shared_tools import get_stack_id

# Load environment variables from .env file
load_dotenv()

# --- Logger ---
class Logger:
    def info(self, message): print(f"[INFO] {message}")
    def error(self, message): print(f"[ERROR] {message}")
logger = Logger()

# --- Agent State ---
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]

# --- Agent Definition ---
def qa_agent_node(state: AgentState) -> dict:
    """
    The primary node for the QA agent that generates test scenarios.
    """
    try:
        system_prompt_content = load_stack_prompt("qa", get_stack_id())
    except FileNotFoundError:
        logger.error("prompts/qa.md not found.")
        system_prompt_content = "You are a QA Agent..."
    except Exception:
        system_prompt_content = load_prompt("qa")

    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=system_prompt_content),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    _llm_base = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.2,
        api_key=os.getenv("OPENAI_API_KEY"),
        max_retries=3
    )
    if os.getenv("LLM_FALLBACK_ENABLED", "0") == "1":
        llm = _llm_base.with_fallbacks(
            [ChatOpenAI(model="gpt-4o", temperature=0.2, max_retries=1)]
        )
    else:
        llm = _llm_base
    # QA est best-effort non-gating: génération de tests uniquement.
    chain = prompt | llm
    response = chain.invoke({"messages": state["messages"]})
    
    # In a real scenario, this response would be parsed to extract the test file content
    # and then written to a file. For this basic agent, we just return the content.
    return {"messages": state["messages"] + [response]}

def create_qa_agent():
    """
    Creates the graph for the QA Agent.
    """
    graph = StateGraph(AgentState)
    graph.add_node("qa_node", qa_agent_node)
    graph.set_entry_point("qa_node")
    graph.add_edge("qa_node", END)
    
    return graph.compile()

if __name__ == '__main__':
    # Example of how to run the agent
    from agents.stack_config import load_stack_config, _DEFAULT_STACK_ID
    _qa_cfg = load_stack_config(_DEFAULT_STACK_ID).get("prompt_rules", {}).get("qa_rules", [])
    _qa_context = " ".join(_qa_cfg) if _qa_cfg else "Generate E2E tests for the application."
    agent = create_qa_agent()
    initial_message = HumanMessage(content=_qa_context)
    
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set.")
    else:
        final_state = agent.invoke({"messages": [initial_message]})
        print("\n--- QA Agent Final Output ---")
        print(final_state['messages'][-1].content)
