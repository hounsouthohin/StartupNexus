import os
import subprocess
from typing import TypedDict, Annotated, List
import operator
from pydantic import BaseModel, Field

# Imports for the new logic
from agents.shared_tools import run_tests, write_file
from langchain_core.messages import HumanMessage, BaseMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

# Import central configuration (Added)
from config.factory_config import SUBPROCESS_TIMEOUT_LONG

# --- Pydantic Models for Structured Output ---
class TestFile(BaseModel):
    file_path: str = Field(description="The full relative path for the test file, e.g., 'tests/components/Button.test.tsx'.")
    content: str = Field(description="The complete source code for the test file.")

class TestSuite(BaseModel):
    tests: List[TestFile]

# --- Agent State Definition ---
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    files: dict  # Source files
    tests: dict  # Generated test files content {path: content}
    iterations: int
    max_iterations: int

# --- Logger ---
class Logger:
    def info(self, message): print(f"[INFO] {message}")
    def error(self, message): print(f"[ERROR] {message}")
    def warning(self, message): print(f"[WARNING] {message}")
logger = Logger()

# --- Node Functions ---

def write_source_files_node(state: AgentState) -> dict:
    """Writes the application source files (received from Dev Agent) to disk and installs dependencies."""
    logger.info("Writing application source files to disk...")
    written_files = []
    for path, content in state["files"].items():
        write_file.invoke({"path": path, "content": content})
        written_files.append(path)
    
    logger.info(f"Source files written to disk: {written_files}")

    # Run npm install after writing files, if a package.json was written
    if "package.json" in state["files"]:
        package_json_path = os.path.join(os.getcwd(), "package.json")
        if os.path.exists(package_json_path): # Check if it actually exists after writing
            logger.info("package.json detected. Running npm install...")
            try:
                install_command = ['npm', 'install']
                subprocess.run(
                    install_command,
                    capture_output=True,
                    text=True,
                    check=True,
                    cwd=".", # Assuming current working directory is the project root
                    timeout=SUBPROCESS_TIMEOUT_LONG
                )
                logger.info("npm install completed successfully in write_source_files_node.")
            except subprocess.CalledProcessError as e:
                logger.error(f"npm install failed in write_source_files_node (code {e.returncode}):\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}")
                return {"messages": state["messages"] + [HumanMessage(content=f"Error: npm install failed during source file setup: {e.stderr}.")]}
            except Exception as e:
                logger.error(f"An unexpected error occurred during npm install in write_source_files_node: {e}")
                return {"messages": state["messages"] + [HumanMessage(content=f"Error: An unexpected error occurred during npm install: {e}.")]}
        else:
            logger.warning("package.json was in state['files'] but not found on disk after writing.")

    return {"messages": state["messages"] + [HumanMessage(content="Application source files written and dependencies installed.")]}


def generation_node(state: AgentState) -> dict:
    """Generates the test files' content based on source files and prior errors."""
    logger.info(f"TestCoverage Agent: Starting test generation iteration {state['iterations'] + 1}.")
    
    try:
        with open(os.path.join(os.path.dirname(__file__), '..', 'prompts', 'test_coverage.md'), "r", encoding='utf-8') as f:
            system_prompt_content = f.read()
    except FileNotFoundError:
        logger.error("prompts/test_coverage.md not found.")
        system_prompt_content = "You are a TestCoverage Agent..."

    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=system_prompt_content),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
    structured_llm = llm.with_structured_output(TestSuite)
    chain = prompt | structured_llm

    files_content_message = "Provided source code files:\n\n"
    for path, content in state["files"].items():
        files_content_message += f"File: {path}\n```\n{content}\n```\n\n"
    
    # Add the source files to the message history for the LLM
    messages = state["messages"] + [HumanMessage(content=files_content_message)]
    
    response_suite = chain.invoke({"messages": messages})
    generated_tests_dict = {test.file_path: test.content for test in response_suite.tests}
    
    logger.info(f"Generated {len(generated_tests_dict)} test files.")
    return {"tests": generated_tests_dict, "iterations": state["iterations"] + 1}

def writing_node(state: AgentState) -> dict:
    """Writes the generated test files to disk."""
    logger.info("Writing test files to disk...")
    for path, content in state["tests"].items():
        # Use the .invoke() method for LangChain tools
        write_file.invoke({"path": path, "content": content})
    return {}

def test_runner_node(state: AgentState) -> dict:
    """Runs the tests and returns the result."""
    logger.info("Running tests...")
    # Use the .invoke() method for LangChain tools
    test_results = run_tests.invoke({"project_dir": "."})
    
    if "Tests passed" in test_results:
        logger.info("All tests passed!")
        return {"messages": state["messages"] + [HumanMessage(content="All tests passed successfully.")]}
    else:
        logger.error(f"Tests failed. Result: {test_results}")
        # Add error message to state for the next generation iteration
        return {"messages": state["messages"] + [HumanMessage(content=f"The test run failed with the following error:\n{test_results}\nPlease analyze the error and fix the test files.")]}

def should_continue(state: AgentState) -> str:
    """Determines whether to continue the loop or end."""
    if state["iterations"] >= state["max_iterations"]:
        logger.warning("Max iterations reached. Ending test generation loop.")
        return "end"
    
    last_message = state["messages"][-1]
    if "All tests passed" in last_message.content:
        return "end"
    else:
        return "generate" # Loop back to generate new tests

# --- Main Agent Definition ---

def test_coverage_agent(files: dict) -> dict:
    """
    Main function to run the TestCoverage Agent with a generate-test-fix loop.
    """
    graph = StateGraph(AgentState)
    
    graph.add_node("write_source_files", write_source_files_node) # New node
    graph.add_node("generate", generation_node)
    graph.add_node("write_tests", writing_node)
    graph.add_node("run_tests", test_runner_node)
    
    graph.set_entry_point("write_source_files") # New entry point
    
    graph.add_edge("write_source_files", "generate") # New edge
    graph.add_edge("generate", "write_tests")
    graph.add_edge("write_tests", "run_tests")
    
    graph.add_conditional_edges(
        "run_tests",
        should_continue,
        {
            "generate": "generate",
            "end": END
        }
    )
    
    app = graph.compile()
    
    logger.info("Starting TestCoverage Agent process.")
    initial_message = HumanMessage(content="Generate unit tests for the provided source files. If the tests fail, analyze the error and correct them.")
    
    final_state = app.invoke(
        {
            "messages": [initial_message],
            "files": files,
            "tests": {},
            "iterations": 0,
            "max_iterations": 3 # Set max retries
        },
        config={"recursion_limit": 30}
    )
    
    logger.info("TestCoverage Agent process completed.")
    return {"tests": final_state.get("tests", {})}
