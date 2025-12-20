import os
from typing import TypedDict, Annotated, List, Tuple
import operator
import json # For parsing tool calls if necessary

from langgraph.graph import StateGraph, END
from langchain_core.tools import Tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
# from langchain_community.chat_models import ChatOllama
from langchain_core.messages import BaseMessage, ToolMessage, HumanMessage, SystemMessage, AIMessage

# Assuming config.factory_config and utils.logger exist and are configured
# from config.factory_config import *
# from utils.logger import logger

# Import shared tools
from .shared_tools import write_file, validate_syntax, prisma_migrate

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Setup basic logger (replace with actual logger if available)
class Logger:
    def info(self, message):
        print(f"[INFO] {message}")
    def error(self, message):
        print(f"[ERROR] {message}")
logger = Logger() # Placeholder

# Define Agent State
class AgentState(TypedDict):
    """
    Represents the state of the Dev Agent.
    messages: A list of messages in the conversation.
    files: A dictionary to store generated files {path: content}.
    iterations: Counter for ReAct loop iterations.
    """
    messages: Annotated[List[BaseMessage], operator.add]
    files: dict
    iterations: int

# Initialize LLMs
llm_openai = ChatOpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"), temperature=0.2)
# llm_ollama = ChatOllama(model="qwen2:7b", temperature=0.2, base_url="http://ollama:11434") # Assuming Ollama server is running and qwen2:7b is pulled

# Bind tools to LLMs
tools = [
    Tool(name="write_file", func=write_file, description="Writes content to a specified file path."),
    Tool(name="validate_syntax", func=validate_syntax, description="Validates the syntax of .tsx (ESLint) and .prisma (Prisma Validate) files."),
    Tool(name="prisma_migrate", func=prisma_migrate, description="Executes a Prisma migration.")
]

llm_openai_with_tools = llm_openai.bind_tools(tools)
# llm_ollama_with_tools = llm_ollama.bind_tools(tools)


# Agent node function
def call_llm(state: AgentState) -> dict:
    """
    Invokes the LLM with the current messages and returns the response.
    Handles tool calls and updates the state.
    """
    logger.info(f"Dev Agent: Starting iteration {state['iterations'] + 1}")
    
    # Read the system prompt from prompts/dev.md
    try:
        with open("prompts/dev.md", "r") as f:
            system_prompt_content = f.read()
    except FileNotFoundError:
        logger.error("prompts/dev.md not found. Using fallback system prompt.")
        system_prompt_content = "You are Dev Agent. Generate full-stack code. You have access to write_file, validate_syntax, and prisma_migrate tools. Use them to implement the user's request. Correct errors using ReAct approach (max 3 iterations)."

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=system_prompt_content),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    
    # TODO: Implement RAG score based LLM fallback here
    # For now, default to OpenAI
    response = llm_openai_with_tools.invoke({"messages": state["messages"]})
    
    # Increment iteration count
    current_iterations = state["iterations"] + 1
    
    # Update files dictionary if write_file was called.
    # LangGraph will execute the tool call and return a ToolMessage.
    # We need to parse this for file updates.
    updated_files = state.get("files", {}).copy()
    if response.tool_calls:
        for tool_call in response.tool_calls:
            if tool_call.name == "write_file":
                # Assuming the content will be in the arguments
                path = tool_call.args.get("path")
                content = tool_call.args.get("content")
                if path and content:
                    updated_files[path] = content
                    logger.info(f"Dev Agent: Proposed writing file: {path}")

    return {"messages": [response], "files": updated_files, "iterations": current_iterations}

# Conditional edge for ReAct loop
def should_continue(state: AgentState) -> str:
    """
    Determines if the agent should continue iterating.
    Checks for tool calls, explicit termination, and iteration limit.
    """
    last_message = state["messages"][-1]
    
    # If the last message contains tool calls, the graph needs to continue to process their output.
    if last_message.tool_calls:
        logger.info(f"Dev Agent: Continuing for tool calls.")
        return "continue"
    
    # Check for explicit errors or if the agent indicates it needs to re-evaluate
    # This is a very basic check; a more sophisticated agent would parse tool_messages for errors
    # or have a specific "think" step.
    has_error_message = any("error" in str(msg.content).lower() for msg in state["messages"] if isinstance(msg, ToolMessage))
    
    if has_error_message and state["iterations"] < 3:
        logger.info(f"Dev Agent: Continuing due to error and remaining iterations ({state['iterations']}/3).")
        return "continue"
    
    # If no tool calls and no explicit error in tool messages, and iterations limit reached, or success
    if state["iterations"] >= 3:
        logger.info(f"Dev Agent: Max iterations ({state['iterations']}/3) reached. Ending.")
        return "end"

    # If the agent's last message is not a tool call and no clear error, it's likely done.
    logger.info(f"Dev Agent: No tool calls or unhandled errors. Ending.")
    return "end"


# Graph definition
graph = StateGraph(AgentState)

graph.add_node("dev", call_llm)

# Define the entry point
graph.set_entry_point("dev")

graph.add_conditional_edges(
    "dev", # From the 'dev' node
    should_continue,
    {
        "continue": "dev", # Loop back to 'dev' node
        "end": END # End the graph
    }
)

# Compile the graph
app = graph.compile()


def dev_agent(spec: str, mermaid: str) -> dict:
    """
    Main function to run the Dev Agent.
    Takes architectural specification and Mermaid diagram as input.
    """
    logger.info("Starting Dev Agent process.")
    initial_message = HumanMessage(content=f"Architectural Specification:\n{spec}\n\nMermaid Diagram:\n{mermaid}")
    
    # Initialize the state with the initial message
    final_state = app.invoke(
        {"messages": [initial_message], "files": {}, "iterations": 0},
        config={"recursion_limit": 100} # Set a recursion limit for safety
    )
    
    generated_files = final_state.get("files", {})
    final_message_content = final_state["messages"][-1].content if final_state["messages"] else "No final message."
    
    logger.info("Dev Agent process completed.")
    return {
        "files": generated_files,
        "final_message": final_message_content
    }
