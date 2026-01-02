import os
from typing import TypedDict, Annotated, List
import operator

# Assuming config.factory_config and utils.logger exist and are configured
# from config.factory_config import *
# from utils.logger import logger

# Import shared tools
from .shared_tools import write_file, validate_syntax, prisma_migrate, rag_search, run_build, read_files

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
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage, ToolMessage, AIMessage, trim_messages
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver


# --- Agent State Definition ---
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    files: dict
    iterations: int
    build_attempts: int

# --- New Helper Function for Summarization/Truncation ---
def summarize_text(text: str, max_tokens: int, llm: ChatOpenAI, description: str) -> str:
    """
    Summarizes or truncates text to fit within max_tokens.
    """
    try:
        current_tokens = llm.get_num_tokens(text)
    except Exception:
        current_tokens = len(text) // 2 # Fallback

    if current_tokens <= max_tokens:
        logger.info(f"Dev Agent: {description} is within token limit ({current_tokens} tokens).")
        return text

    logger.warning(f"Dev Agent: {description} ({current_tokens} tokens) exceeds limit of {max_tokens}. Attempting summarization.")
    
    try:
        summarization_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=f"Summarize the following '{description}' to be less than {max_tokens} tokens, focusing on the most critical details for a software developer."),
            HumanMessage(content="{input_text}")
        ])
        
        summarization_chain = summarization_prompt | llm
        summarized_content = summarization_chain.invoke({"input_text": text}).content
        
        summarized_tokens = llm.get_num_tokens(summarized_content)
        if summarized_tokens <= max_tokens:
            logger.info(f"Dev Agent: {description} successfully summarized to {summarized_tokens} tokens.")
            return summarized_content
        else:
            logger.warning(f"Dev Agent: Summarization of {description} still too long ({summarized_tokens} tokens). Truncating.")
            split_by_char = int(max_tokens * 3.5)
            truncated_text = text[:split_by_char]
            return f"TRUNCATED ({description} was too long):\n{truncated_text}..."

    except Exception as e:
        logger.error(f"Dev Agent: Summarization failed for {description}: {e}. Truncating instead.")
        split_by_char = int(max_tokens * 3.5)
        truncated_text = text[:split_by_char]
        return f"TRUNCATED ({description} was too long):\n{truncated_text}..."

# Initialize LLM for the main agent and summarization once
llm_main_agent = ChatOpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"), temperature=0.2)


# --- Node Functions ---

def call_llm(state: AgentState) -> dict:
    """
    Invokes the LLM with the current state, handling both the main development
    path and error correction (ReAct logic).
    """
    logger.info(f"Dev Agent: Starting iteration {state['iterations'] + 1}")
    
    messages_to_process = state['messages']
    last_message = messages_to_process[-1]
    
    if isinstance(last_message, ToolMessage):
        if "Error:" in last_message.content or "failed" in last_message.content.lower():
            logger.warning("Dev Agent: A tool error occurred. Entering error correction loop.")
            error_feedback = HumanMessage(
                content=f"An error occurred during the last tool execution: '{last_message.content}'. Please analyze this error, determine the cause, and provide a corrected plan by calling the necessary tools to fix the issue."
            )
            messages_to_process.append(error_feedback)
        else:
            logger.info("Dev Agent: Tool executed successfully. Prompting to continue.")
            proceed_feedback = HumanMessage(
                content="Tool execution was successful. Please proceed to the next step based on the original plan."
            )
            messages_to_process.append(proceed_feedback)

    # --- Token-based Truncation (best practice) ---
    logger.info(f"Avant trim : {len(messages_to_process)} messages")
    trimmed_messages = trim_messages(
        messages=messages_to_process,
        token_counter=llm_main_agent,
        strategy="last",
        max_tokens=100_000,
        start_on="human",
        end_on=("human", "tool"),
        include_system=True,
    )
    logger.info(f"Après trim : {len(trimmed_messages)} messages")
    messages_to_process = trimmed_messages


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
    
    tools = [write_file, validate_syntax, prisma_migrate, rag_search, read_files, run_build]
    llm_with_tools = llm_main_agent.bind_tools(tools)
    
    chain = prompt | llm_with_tools
    response = chain.invoke({"messages": messages_to_process})
    
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
    
    # Define max tokens for spec and mermaid
    MAX_SPEC_TOKENS = 50000
    MAX_MERMAID_TOKENS = 10000

    # Summarize/truncate spec and mermaid
    summarized_spec = summarize_text(spec, MAX_SPEC_TOKENS, llm_main_agent, "Architectural Specification")
    summarized_mermaid = summarize_text(mermaid, MAX_MERMAID_TOKENS, llm_main_agent, "Mermaid Diagram")

    tools = [write_file, validate_syntax, prisma_migrate, rag_search, read_files, run_build]
    tool_node = ToolNode(tools)

    # This new node will call the run_build tool
    def build_node(state: AgentState) -> dict:
        build_attempts = state.get("build_attempts", 0) + 1
        if build_attempts > 5:
            logger.error("Too many consecutive build failures. Forcing process to end.")
            return {"messages": state["messages"] + [HumanMessage(content="Trop d'échecs build consécutifs. Arrêt forcé.")], "build_attempts": build_attempts}
        
        logger.info(f"Build Node: Attempting to build the project (Attempt {build_attempts}/5).")
        result = run_build(project_dir='.') # Assumes the agent runs in the project root
        
        if "Build successful" in result:
            logger.info("Build successful. Ending process.")
            return {"messages": state["messages"] + [HumanMessage(content="Build was successful.")], "build_attempts": 0}
        else:
            logger.error(f"Build failed (tentative {build_attempts}/5). Looping back for corrections. Error: {result}")
            # Add the build failure message to the state to inform the ReAct loop
            return {
                "messages": state["messages"] + [HumanMessage(content=f"Build failed (tentative {build_attempts}/5): {result}. Corrige précisément.")],
                "build_attempts": build_attempts
            }
    def clerk_compliance_check_node(state: AgentState) -> dict:
        logger.info("Dev Agent: Running Clerk compliance check.")
        violations = []
        forbidden_paths = ['app/api/auth/', 'app/api/login/', 'app/api/register/', 'app/api/logout/', 'app/api/password-reset/', 'app/api/password-update/']
        forbidden_packages = ['bcrypt', 'jsonwebtoken', 'bcryptjs']

        # Check generated files for forbidden paths and packages
        for path, content in state["files"].items():
            if any(fp in path for fp in forbidden_paths):
                violations.append(f"Forbidden path detected: {path}. Use Clerk for all authentication purposes.")
            
            for pkg in forbidden_packages:
                if pkg in content:
                    violations.append(f"Forbidden package '{pkg}' detected in file: {path}. Use Clerk exclusively.")

        # Check for required Clerk pages
        required_pages = ['app/sign-in/[[...sign-in]]/page.tsx', 'app/sign-up/[[...sign-up]]/page.tsx']
        missing_pages = [page for page in required_pages if not any(path.endswith(page) for path in state["files"].keys())]
        if missing_pages:
            violations.append(f"Required Clerk page(s) missing: {', '.join(missing_pages)}. You must generate these pages.")

        if violations:
            logger.warning(f"Dev Agent: Clerk compliance violations detected: {violations}")
            correction_prompt = (
                "CORRECTION REQUISE (ne régénère QUE les fichiers problématiques) :\n"
                "Violations Clerk :\n" + "\n".join(f"- {v}" for v in violations) + "\n\n"
                "Corrige UNIQUEMENT les fichiers concernés en appelant write_file dessus.\n"
                "Garde tous les autres fichiers existants intacts."
            )
            return {
                "messages": state["messages"] + [HumanMessage(content=correction_prompt)],
                "files": state["files"],  # Garde les fichiers existants !
            }

        logger.info("Dev Agent: Clerk compliance check passed.")
        return state # No violations, return original state

    # --- Conditional Edges ---
    def should_continue(state: AgentState) -> str:
        # Increased max iterations for more complex projects
        if state["iterations"] >= 50: 
            logger.warning("Max iterations reached. Ending process.")
            return "end"
        
        last_message = state["messages"][-1]
        
        # If the last message was a build failure, go back to dev
        if "Build failed" in last_message.content:
            return "dev"
            
        # If the last message was a successful build, end
        if any("Build successful" in m.content for m in state["messages"][-3:]):
            return "end"

        # If a tool was called, proceed to Clerk compliance check
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            # After tools run, always check for compliance
            return "clerk_compliance_check"
        
        # If the agent is in a correction loop from compliance check, go back to dev
        if "CRITICAL VIOLATION" in last_message.content:
            return "dev"
            
        return "dev"

    # --- Graph Definition ---
    graph = StateGraph(AgentState)
    graph.add_node("dev", call_llm)
    graph.add_node("tools", tool_node)
    graph.add_node("build", build_node)
    graph.add_node("clerk_compliance_check", clerk_compliance_check_node)

    graph.set_entry_point("dev")
    
    # After dev's turn (calling LLM), always go to tools to execute them
    graph.add_edge("dev", "tools") 
    
    # After tools are executed, go to compliance check
    graph.add_edge("tools", "clerk_compliance_check") 
    
    # After compliance check, decide where to go next
    graph.add_conditional_edges(
        "clerk_compliance_check",
        should_continue,
        {
            "build": "build", # Should be triggered by a specific condition, not directly
            "dev": "dev",    # If compliance fails or needs more work
            "end": END
        }
    )

    # After a build attempt, decide the next step
    graph.add_conditional_edges(
        "build",
        should_continue,
        {
            "dev": "dev",
            "end": END
        }
    )

    checkpointer = MemorySaver()
    app = graph.compile(checkpointer=checkpointer)
    
    logger.info("Starting Dev Agent process.")
    initial_message = HumanMessage(content=f"Project Name: {project_name}\n\nArchitectural Specification:\n{summarized_spec}\n\nMermaid Diagram:\n{summarized_mermaid}")
    
    final_state = app.invoke(
        {"messages": [initial_message], "files": {}, "iterations": 0, "build_attempts": 0},
        config={"configurable": {"thread_id": project_name}, "recursion_limit": 300} # Increased recursion limit
    )
    
    generated_files = final_state.get("files", {})
    final_message_content = final_state["messages"][-1].content if final_state["messages"] else "No final message."
    
    logger.info("Dev Agent process completed.")
    return {
        "files": generated_files,
        "final_message": final_message_content
    }