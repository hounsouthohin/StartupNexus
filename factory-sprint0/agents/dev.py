import os
from typing import TypedDict, Annotated, List
import operator

# Assuming config.factory_config and utils.logger exist and are configured
# from config.factory_config import *
# from utils.logger import logger

# Import shared tools
from .shared_tools import write_file, validate_syntax, prisma_migrate, rag_search

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Setup basic logger (replace with actual logger if available)
class Logger:
    def info(self, message):
        print(f"[INFO] {message}")
    def warning(self, message): # Added warning method
        print(f"[WARNING] {message}")
    def error(self, message):
        print(f"[ERROR] {message}")
logger = Logger() # Placeholder

# --- Pydantic and Langchain Core Imports for nodes ---
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage, ToolMessage
from langchain_openai import ChatOpenAI

# --- Agent State Definition ---
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    files: dict
    iterations: int

# --- Node Functions ---

def call_llm(state: AgentState) -> dict:
    """
    Invokes the LLM with the current state, handling both the main development
    path and error correction (ReAct logic).
    """
    logger.info(f"Dev Agent: Starting iteration {state['iterations'] + 1}")
    
    # Check for tool errors in the last message and prepare ReAct prompt
    messages_to_process = state['messages']
    last_message = messages_to_process[-1]
    if isinstance(last_message, ToolMessage) and "Error:" in last_message.content:
        logger.warning("Dev Agent: An error occurred. Entering error correction loop.")
        error_feedback = HumanMessage(
            content=f"An error occurred during the last tool execution: '{last_message.content}'. Please analyze this error, determine the cause, and provide a corrected plan by calling the necessary tools to fix the issue."
        )
        messages_to_process = messages_to_process + [error_feedback]

    # Read the system prompt from prompts/dev.md
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        prompts_path = os.path.join(current_dir, '..', 'prompts', 'dev.md')
        with open(prompts_path, "r", encoding='utf-8') as f:
            system_prompt_content = f.read()
    except FileNotFoundError:
        logger.error("prompts/dev.md not found. Using fallback system prompt.")
        system_prompt_content = "You are Dev Agent..."

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=system_prompt_content),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    
    llm = ChatOpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"), temperature=0.2)
    tools = [write_file, validate_syntax, prisma_migrate, rag_search]
    llm_with_tools = llm.bind_tools(tools)
    
    chain = prompt | llm_with_tools
    # Pass the potentially augmented message list
    response = chain.invoke({"messages": messages_to_process})
    
    # Update files dictionary if write_file was proposed
    updated_files = state.get("files", {}).copy()
    if response.tool_calls:
        for tool_call in response.tool_calls:
            if tool_call['name'] == "write_file":
                path = tool_call['args'].get("path")
                content = tool_call['args'].get("content")
                if path and content:
                    updated_files[path] = content
                    logger.info(f"Dev Agent: Proposed writing file: {path}")

    return {"messages": [response], "files": updated_files, "iterations": state["iterations"] + 1}

# --- Main Agent Definition ---

def dev_agent(spec: str, mermaid: str, project_name: str) -> dict:
    """
    Main function to run the Dev Agent.
    """
    from langgraph.graph import StateGraph, END
    from langgraph.prebuilt import ToolNode
    
    tools = [write_file, validate_syntax, prisma_migrate, rag_search]
    tool_node = ToolNode(tools)

    # --- Conditional Edges ---
    def should_continue(state: AgentState) -> str:
        if state["iterations"] >= 15:
            logger.warning("Max iterations reached. Ending process.")
            return "end"
        
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        
        required_files = ["package.json", "prisma/schema.prisma", "app/layout.tsx"]
        if all(file in state.get("files", {}) for file in required_files):
            logger.info("Core files generated. Ending.")
            return "end"
        
        return "dev"

    # --- Graph Definition ---
    graph = StateGraph(AgentState)
    graph.add_node("dev", call_llm)
    graph.add_node("tools", tool_node)

    graph.set_entry_point("dev")
    graph.add_conditional_edges("dev", should_continue, {"tools": "tools", "end": END, "dev": "dev"})
    graph.add_edge("tools", "dev") # Simple loop back to dev node after tools run

    app = graph.compile()
    
    logger.info("Starting Dev Agent process.")
    initial_message = HumanMessage(content=f"Project Name: {project_name}\n\nArchitectural Specification:\n{spec}\n\nMermaid Diagram:\n{mermaid}")
    
    final_state = app.invoke(
        {"messages": [initial_message], "files": {}, "iterations": 0},
        config={"recursion_limit": 150} # Increased recursion limit for error loops
    )
    
    generated_files = final_state.get("files", {})
    final_message_content = final_state["messages"][-1].content if final_state["messages"] else "No final message."
    
    logger.info("Dev Agent process completed.")
    return {
        "files": generated_files,
        "final_message": final_message_content
    }
